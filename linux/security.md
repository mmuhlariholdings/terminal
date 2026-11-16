# Terminal 1 security

Terminal 1 holds SSH keys and cloud sign-ins, so treat it like a laptop that is easier to lose.
This page covers the four rules from the prototype plan:

1. Encrypt the storage, with a passphrase entered at boot.
2. Lock the screen after a few minutes idle.
3. Protect SSH keys with a passphrase and load them into an agent per session.
4. Keep cloud sessions short-lived, and be able to revoke them remotely if the device is lost.

**Status:** the screen lock and SSH agent setup are installed by `install.sh`. Disk encryption is a
manual procedure, written from Debian's `cryptsetup` documentation and Raspberry Pi's CM4 flashing
documentation, and **not yet tested on a CM4**. Do it on the bench with nothing you can't lose, and
keep the board able to boot over `rpiboot` until it works.

---

## 1. Full-disk encryption (LUKS) on the CM4 eMMC

### What you get and what you don't

- The root filesystem (`/`, including `/home`, SSH keys, `~/.azure`, `~/.claude`) is encrypted with LUKS2.
  The initramfs asks for the passphrase on the screen at every boot.
- The boot partition (`/boot/firmware`: kernel, initramfs, `config.txt`) stays **unencrypted**. Someone
  with the device could replace the initramfs to capture the passphrase next time you type it (an
  "evil maid" attack). Closing that needs CM4 secure boot (signed boot images, Raspberry Pi's
  `rpi-sb-provisioner`), which is out of scope for v1.
- While the device is on, the key is in memory. Power off (long press), don't just blank the screen,
  when you leave it somewhere.

### Choosing the cipher

The CM4's Cortex-A72 cores have **no ARMv8 crypto extensions**, so AES runs in software and is slow.
Adiantum (`xchacha12,aes-adiantum-plain64`), designed by Google for exactly this kind of CPU, is
usually several times faster. Measure on your board before choosing:

```sh
sudo apt install cryptsetup
cryptsetup benchmark -c aes-xts-plain64 -s 512
cryptsetup benchmark -c xchacha12,aes-adiantum-plain64 -s 256
```

The steps below use Adiantum. If the benchmark shows AES-XTS is fine for you, use
`--cipher aes-xts-plain64 --key-size 512` instead and skip the Adiantum modules.

### Step 1: prepare the running system (on the CM4)

Do this on a working, up-to-date install (`sudo apt update && sudo apt full-upgrade`).

```sh
sudo apt install cryptsetup cryptsetup-initramfs

# 1a. Check the boot loader loads an initramfs (Bookworm and Trixie: auto_initramfs=1).
grep -n initramfs /boot/firmware/config.txt
ls -l /boot/firmware/initramfs*

# 1b. Note the root partition's PARTUUID (it does not change when the partition is encrypted).
findmnt -no SOURCE /          # e.g. /dev/mmcblk0p2
sudo blkid -s PARTUUID -o value /dev/mmcblk0p2    # e.g. 1a2b3c4d-02
```

Tell the initramfs to include cryptsetup and the modules for the keyboard and the cipher:

```sh
# Unlock "cryptroot" from the root partition at boot (replace the PARTUUID).
echo 'cryptroot PARTUUID=1a2b3c4d-02 none luks,discard,initramfs' | sudo tee -a /etc/crypttab

# Force cryptsetup into the initramfs even though root is not encrypted yet.
echo 'CRYPTSETUP=y' | sudo tee -a /etc/cryptsetup-initramfs/conf-hook

# USB keyboard (dwc2 host + HID) and Adiantum. A module that is built into the
# kernel just prints a warning, which is fine.
printf '%s\n' dm_crypt dwc2 usbhid hid_generic adiantum nhpoly1305 nhpoly1305_neon chacha_neon \
  | sudo tee -a /etc/initramfs-tools/modules
```

Point the system at the (future) encrypted root:

```sh
# /etc/fstab: the root line becomes /dev/mapper/cryptroot.
sudo sed -i 's|^PARTUUID=1a2b3c4d-02 |/dev/mapper/cryptroot |' /etc/fstab

# /boot/firmware/cmdline.txt (one line): root=PARTUUID=... becomes root=/dev/mapper/cryptroot.
# Keep "console=tty1" as the LAST console= entry so the passphrase prompt shows on the screen.
sudo cp /boot/firmware/cmdline.txt /boot/firmware/cmdline.txt.before-luks
sudo sed -i 's|root=PARTUUID=[^ ]*|root=/dev/mapper/cryptroot|' /boot/firmware/cmdline.txt
cat /boot/firmware/cmdline.txt
```

Rebuild the initramfs and check it has what it needs:

```sh
sudo update-initramfs -u
lsinitramfs /boot/firmware/initramfs8 | grep -E 'cryptsetup|crypttab|adiantum|usbhid|dwc2'
```

Raspberry Pi OS copies the new initramfs into `/boot/firmware` with its own hook; check the date
on `/boot/firmware/initramfs8` changed. **Do not reboot now**: the system would wait for an encrypted
root that doesn't exist yet. Power off: `sudo poweroff`.

### Step 2: encrypt the root partition in place (from a Linux computer, over rpiboot)

Put the CM4 in USB mass-storage mode the same way as for flashing (README, "Flash the eMMC"):
CM4 IO board jumper "disable eMMC boot" fitted, USB from the IO board's micro-USB port to your
computer, then `sudo ./rpiboot -d mass-storage-gadget64`. On the Terminal 1 device itself, use
service mode instead (hold `Fn` + `Back` while pressing power).

The eMMC appears as a disk, here `/dev/sdX` (check with `lsblk`; getting this wrong destroys the
wrong disk). Make sure nothing auto-mounted it.

```sh
sudo umount /dev/sdX1 /dev/sdX2 2>/dev/null
sudo e2fsck -f /dev/sdX2
sudo resize2fs -M /dev/sdX2                     # shrink to minimum, leaves room for the LUKS header

sudo cryptsetup reencrypt --encrypt --type luks2 \
  --cipher xchacha12,aes-adiantum-plain64 --key-size 256 \
  --reduce-device-size 32M /dev/sdX2            # asks for the new passphrase; takes a while

sudo cryptsetup open /dev/sdX2 cryptroot
sudo resize2fs /dev/mapper/cryptroot            # grow back to fill the partition
sudo e2fsck -f /dev/mapper/cryptroot
sudo cryptsetup luksHeaderBackup /dev/sdX2 --header-backup-file terminal-1-luks-header.img
sudo cryptsetup close cryptroot
```

Keep `terminal-1-luks-header.img` somewhere safe and off the device (it plus the passphrase can
unlock the disk; without it a damaged header means the data is gone). `reencrypt` can resume if it is
interrupted: run the same command again.

### Step 3: first encrypted boot

Remove the jumper (or leave service mode), power on. The initramfs shows
`Please unlock disk cryptroot:` on the screen and on the serial console. Type the passphrase.

Then, on the CM4:

```sh
lsblk -o NAME,TYPE,FSTYPE,MOUNTPOINT       # mmcblk0p2 -> crypt -> /
sudo cryptsetup status cryptroot
# Re-tune the key slot's Argon2id cost on the CM4 itself (step 2 measured your computer's speed).
sudo cryptsetup luksChangeKey --pbkdf argon2id --iter-time 2000 /dev/mmcblk0p2
swapon --show                               # swap must be zram or inside the encrypted root
```

### If it doesn't boot

- **No prompt / no keyboard at the prompt**: the screen or USB driver isn't in the initramfs. Use the
  serial console (UART on GPIO 14/15) to type the passphrase, then fix `/etc/initramfs-tools/modules`.
- **Wrong root**: put the CM4 back in rpiboot mode on your computer, `cryptsetup open` the partition,
  mount it and the boot partition, and fix `cmdline.txt`, `/etc/fstab` or `/etc/crypttab`.
- **Kernel updates**: `apt` rebuilds the initramfs on each kernel update. After an update, check again
  with `lsinitramfs ... | grep cryptsetup` before rebooting.

---

## 2. Screen lock

Installed by `install.sh`:

- tmux runs `vlock` after **5 minutes** without input (`lock-after-time 300` in `/etc/tmux.conf`), and on
  `Ctrl`-`b` then `Shift`-`L`. `vlock` asks for your **user password**, so the user must have one.
- `terminal-1-statusd` dims the screen after 60 s and switches the backlight off after 180 s (edit
  `/etc/default/terminal-1-statusd`). Any key brings it back. Dimming is not locking.
- The other consoles (`Ctrl`+`Alt`+`F2` …) have normal password logins.
- What the lock does **not** cover: anyone who can reach the device over SSH with a password. Use
  `sudo ./install.sh --ssh-keys-only` once your key is in `~/.ssh/authorized_keys`, or turn SSH off
  (`sudo systemctl disable --now ssh`) when you don't need it.

The cage + foot session logs in automatically on tty1. That is deliberate: the LUKS passphrase is the
boot-time gate. Without disk encryption, auto-login means anyone who powers the device on gets a shell
until the 5-minute lock, so **set up step 1 before the device leaves the bench.**

## 3. SSH keys with a passphrase, and the agent

Make one key per device, so losing the device means revoking one key:

```sh
ssh-keygen -t ed25519 -a 100 -C "terminal-1-$(date +%Y-%m)"
```

Give it a passphrase. `install.sh` sets up the rest:

- zsh starts one `ssh-agent` per login at `$XDG_RUNTIME_DIR/ssh-agent.socket`, with keys expiring after
  **4 hours** (`ssh-agent -t 4h`).
- `AddKeysToAgent yes` (`/etc/ssh/ssh_config.d/terminal-1.conf`): the first `ssh` asks for the passphrase
  and adds the key; later connections don't ask.
- `logout-cloud` empties the agent (`ssh-add -D`).

Put the public key (`~/.ssh/id_ed25519.pub`) on servers and on GitHub. The `terminal-1-` comment makes it
easy to find and remove later.

## 4. Short cloud sessions and remote revocation

### Azure CLI

- Sign in with the device code flow (no browser on the device): `az login --use-device-code`
  (alias `azlogin`). Open the URL on your phone and enter the code.
- The CLI caches refresh tokens in `~/.azure/` (protected at rest only by disk encryption). Sign out when
  you're done: `az logout` (or `logout-cloud`).
- Ask your Entra ID administrator for a Conditional Access **sign-in frequency** policy (for example 8 or
  12 hours) for this account or device, so a forgotten session ends on its own.
- Use an account with only the roles you need; activate higher roles with Privileged Identity Management
  when needed rather than keeping them.

### Claude Code

- Sign in by running `claude`. With no browser on the device, open the URL it prints on your phone or
  laptop and paste the code back. Credentials are stored under `~/.claude/` (again protected by disk encryption).
- Run `/logout` inside Claude Code when you hand the device to someone or put it away for a while.
- With an API key (Claude Console), use a key just for this device, so you can delete just that key.

### If the device is lost: revocation checklist

Do these from another computer, in this order:

1. **Azure / Entra ID**: revoke refresh tokens. Yourself: <https://myaccount.microsoft.com> → *Sign out
   everywhere* (work or school account). Administrator: Entra admin center → Users → the user → *Revoke sessions*, or
   `az rest --method post --url https://graph.microsoft.com/v1.0/users/<user-id>/revokeSignInSessions`.
   Access tokens already issued stay valid until they expire (about an hour, shorter with continuous
   access evaluation).
2. **SSH**: remove the device's key everywhere it is authorised. GitHub: Settings → SSH and GPG keys, or
   `gh ssh-key list` then `gh ssh-key delete <id>` from another machine. Servers: delete the line ending
   in `terminal-1-YYYY-MM` from `~/.ssh/authorized_keys`.
3. **GitHub CLI / tokens**: if you signed in with `gh auth login`, revoke the GitHub CLI authorisation
   (GitHub Settings → Applications → Authorized OAuth Apps) and any personal access tokens on the device.
4. **Claude**: Console API key: delete it at console.anthropic.com. Claude subscription login: sign the
   device out from your account's settings on claude.ai (look for active sessions or "log out of all
   devices"), or change your password. Team or Enterprise: ask an administrator.
5. **Wi-Fi**: the device stores Wi-Fi passwords (`/etc/NetworkManager/system-connections/`). Change
   them if they matter.

With disk encryption on and the device powered off, the data is safe even before you finish this list,
as long as the passphrase is strong. Revoke anyway.

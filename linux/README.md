# Terminal 1: Linux

The software side of Terminal 1: Raspberry Pi OS Lite (64-bit) on the CM4, set up to boot straight into
a full-screen terminal. No desktop: **cage** (a kiosk Wayland compositor) runs the **foot** terminal,
which runs **tmux** and **zsh**. A small daemon talks to the keyboard board for battery level and power
events. Shared numbers (pins, `config.txt` lines, the USB status protocol) come from
[system/plan/interfaces.md](../system/plan/interfaces.md); change them there first.

This project is openly "vibe coded": designed and written with an AI assistant, then checked by people.
The table below says honestly what has been run.

## What has been tested

| Part | Status |
|---|---|
| `terminal-1-statusd`, `terminal-1-ctl` | 21 host-side tests pass on macOS with Python 3 (fake keyboard on a pseudo-terminal). Not yet run against the real RP2040 firmware. |
| `install.sh` | `bash -n` and shellcheck 0.11 clean; `--dry-run` run on a development machine; config.txt block replacement tested for idempotency. **Not yet run on a CM4.** |
| Config files (foot, tmux, zsh, systemd, udev, logind, PAM) | Written from the tools' documentation; not yet run on a device. |
| `image/` + `.github/workflows/linux-image.yml` | Written; **never run**. Expect fixes on the first build. |
| Disk encryption ([security.md](security.md)) | Procedure written; **not yet tried on a CM4**. |

If you run any of this on hardware, please update this table in your pull request.

## What's here

```
linux/
├── README.md                    this file
├── install.sh                   idempotent installer for a fresh Raspberry Pi OS Lite 64-bit
├── security.md                  disk encryption, screen lock, SSH agent, cloud sessions, revocation
├── keyboard-cheat-sheet.md      user-facing key summary (firmware README is the authority)
├── bin/terminal-1-session       started by foot: attach tmux, fall back to a shell
├── config/
│   ├── config-txt-fragment.txt  appended to /boot/firmware/config.txt (interfaces.md section 5)
│   ├── foot.ini                 Terminus 16 px: 90 x 45 cells on 720 x 720
│   ├── tmux.conf                status line (battery, Wi-Fi, time) and 5-minute vlock
│   ├── zshrc                    history, completion, short prompt, ssh-agent, helpers
│   ├── terminal-1-statusd.env   daemon options (/etc/default/terminal-1-statusd)
│   ├── systemd/                 terminal-1-session.service (cage + foot on tty1), terminal-1-statusd.service
│   ├── pam/terminal-1-session   PAM stack for the kiosk session
│   ├── udev/99-terminal-1.rules /dev/terminal-1-status symlink; power key for logind
│   ├── logind/                  power key = clean poweroff, no suspend
│   └── ssh/                     sshd and ssh client drop-ins
├── status-daemon/
│   ├── terminal-1-statusd       Python 3, standard library only (pyserial optional)
│   ├── terminal-1-ctl           command-line control
│   └── tests/                   host-side tests with a fake serial port
└── image/                       pi-gen configuration and custom stage for a ready-made image
```

## How it fits together

```
RP2040 keyboard board ──USB──► CM4
   HID keyboard / mouse ─────────► cage ► foot ► tmux ► zsh
   HID System Power Down ────────► systemd-logind ► poweroff
   CDC "status" port ─udev─► /dev/terminal-1-status ► terminal-1-statusd
                                     ├─► /run/terminal-1/status       (key=value)
                                     ├─► /run/terminal-1/status.tmux  (tmux status line)
                                     ├─► systemctl poweroff on "PWR critical-battery"
                                     └─◄ /run/terminal-1/control.sock ◄ terminal-1-ctl
```

- **Battery level**: the keyboard board sends `BAT <percent> <mV> <state>` every 10 s; tmux shows
  `BAT 87% | wifi 72% home | 14:05`. `kbd --` means the status port isn't connected.
- **Power**: long press = the keyboard sends the power key, logind shuts down cleanly, GPIO26 tells the
  RP2040 it can cut power. Short press = screen off / on (proposal). `PWR critical-battery` = the daemon
  runs `systemctl poweroff`. The CM4 has no real sleep, so the device is either on or off.
- **Screen**: the daemon dims the backlight after 60 s without input and turns it off after 180 s.
  tmux locks with `vlock` after 5 minutes.
- **Commands**:

  ```sh
  terminal-1-ctl status                 # battery, firmware version, Wi-Fi, screen
  terminal-1-ctl version                # VER
  terminal-1-ctl keyboard-backlight 40  # BL 40
  terminal-1-ctl trackpad mouse         # MODE mouse (or arrows)
  terminal-1-ctl screen 60              # screen brightness, or on / off / toggle
  ```

  Members of the `terminal-1` group can use it (the installer adds your user; log in again).

## Phase 0: bench bring-up

The bench build is a CM4 on the official **CM4 IO board** with a Raspberry Pi DSI display, and the
keyboard on a **Raspberry Pi Pico** running the keyboard firmware (`firmware/keyboard-board`). Until the
keyboard firmware works, any USB keyboard will do; the status line then shows `kbd --`.

### You need

- CM4 4 GB RAM, 32 GB eMMC, Wi-Fi (plus the antenna, or comment out `dtparam=ant2` in
  `config/config-txt-fragment.txt` and use the on-board antenna)
- CM4 IO board and its 12 V supply
- A DSI display on DISP1 (for the 720 x 720 panel itself, see "Display" below)
- A Linux, macOS or Windows computer with Raspberry Pi Imager and `rpiboot`
- Micro-USB cable (computer to the IO board's USB slave port), a USB keyboard or the Pico

### 1. Flash Raspberry Pi OS Lite (64-bit) to the eMMC

The CM4's eMMC is flashed over USB with `rpiboot`, which makes the CM4 show up on your computer as a disk.

1. Install `rpiboot` (Raspberry Pi's `usbboot` repository). On Linux:

   ```sh
   sudo apt install git libusb-1.0-0-dev pkg-config build-essential
   git clone --depth=1 https://github.com/raspberrypi/usbboot && cd usbboot && make
   ```

   On Windows use the `rpiboot` installer; on macOS build it the same way with Homebrew's `libusb`.
2. On the IO board, fit the jumper on **J2** ("disable eMMC boot"). Connect the IO board's micro-USB port
   (J11) to your computer, then plug in the 12 V supply.
3. Run `sudo ./rpiboot -d mass-storage-gadget64` (or plain `sudo ./rpiboot` with older versions). The eMMC
   appears as a USB disk.
4. In **Raspberry Pi Imager**: device *Raspberry Pi 4* (covers the CM4), OS *Raspberry Pi OS (other) → Raspberry Pi
   OS Lite (64-bit)*, storage = the CM4 disk. In the customisation settings set a hostname
   (`terminal-1`), a **username and password**, your Wi-Fi, time zone and keyboard layout, and **enable SSH**.
   As of November 2026 the current image is Trixie (Debian 13), released 2026-10-06; Bookworm is the
   "Legacy" image and also works.
5. Write the image. When it's done: unplug the 12 V supply, remove the J2 jumper, unplug the micro-USB.

### 2. First boot

1. Connect the display and keyboard, power on. The first boot resizes the filesystem and reboots once.
2. Log in on the screen, or over SSH: `ssh <user>@terminal-1.local`.
3. Update: `sudo apt update && sudo apt full-upgrade -y && sudo reboot`.
4. Optional but useful: a USB-to-serial adapter on GPIO 14/15 gives a console at 115200 baud.

### 3. Run the installer

```sh
sudo apt install -y git
git clone https://github.com/<owner>/<repository>.git terminal-1
cd terminal-1/linux
sudo ./install.sh --dry-run      # read what it will do
sudo ./install.sh                # about 10-20 minutes, most of it Azure CLI and Node.js downloads
sudo reboot
```

Useful options: `--skip-claude`, `--skip-azure`, `--skip-node`, `--skip-session` (keep the normal
console on tty1, handy while debugging), `--skip-config-txt`, `--ssh-keys-only`, `--claude-method apt`.
Run `./install.sh --help` for all of them. Running it again only changes what differs.

After the reboot the screen goes straight to foot + tmux. Then:

```sh
nmtui                          # Wi-Fi networks (alias: wifi)
terminal-1-ctl status          # does the daemon see the keyboard?
ls -l /dev/terminal-1-status   # udev symlink, present when the keyboard firmware is running
journalctl -u terminal-1-statusd -u terminal-1-session -b
claude                         # sign in: open the printed URL on your phone, paste the code
az login --use-device-code     # alias: azlogin
```

Then read [security.md](security.md) and set up disk encryption before the device leaves the bench.

### Bench checklist

- [ ] foot shows 90 x 45 (`tput cols; tput lines` prints 90 and 44 inside tmux)
- [ ] `/dev/terminal-1-status` appears when the Pico is plugged in; `terminal-1-ctl ping` prints `OK`
- [ ] tmux status line shows the battery (the Pico firmware can send a fake `BAT` line)
- [ ] `terminal-1-ctl trackpad mouse` / `arrows` switches the trackpad mode
- [ ] Power key from the keyboard (or GPIO17 pulled low) shuts down cleanly; GPIO26 goes high after halt
- [ ] `sudo hwclock -r` reads the RTC
- [ ] Idle: screen dims after 60 s, turns off after 180 s, tmux locks after 5 minutes
- [ ] Boot time from power-on to the prompt: `systemd-analyze` (record it here)

### Display

The 720 x 720 panel is not chosen yet (`interfaces.md` section 2). The panel overlay line in
`config-txt-fragment.txt` is a placeholder; on the bench use the overlay for the display you have.
The screen dimming in `terminal-1-statusd` works with any panel that has a `/sys/class/backlight` device;
with none it simply does nothing.

## Building the image

`image/` turns the installer into a ready-to-flash image, so a new device needs no installer run.
It uses **pi-gen** (`RPi-Distro/pi-gen`, `arm64` branch), the tool Raspberry Pi builds Raspberry Pi OS
with. pi-gen builds Raspberry Pi OS Lite (stages 0 to 2), then our stage `stage-terminal-1` copies
`linux/` to `/opt/terminal-1/linux` in the image and runs `install.sh --image-build` in the chroot.
(Raspberry Pi's newer `rpi-image-gen` is aimed at custom images built from scratch with YAML layers;
pi-gen was chosen because it produces stock Raspberry Pi OS Lite, which is what the installer targets.)

### On GitHub

Actions → **Linux image** → *Run workflow*, give a release tag. The workflow
(`.github/workflows/linux-image.yml`) runs the tests, builds on GitHub's arm64 runner with
`build-docker.sh` and attaches `*.img.xz` to a new release. Set the repository secret
`IMAGE_FIRST_USER_PASSWORD` to choose the first password; otherwise it is `terminal-1` and the shell
reminds you to change it. SSH is off in the image.

### Locally

On an arm64 Debian or Raspberry Pi OS machine with Docker:

```sh
git clone https://github.com/RPi-Distro/pi-gen.git && cd pi-gen && git checkout arm64
cp -a ../terminal-1/linux/image/stage-terminal-1 .
mkdir -p stage-terminal-1/00-install/files
rsync -a --exclude image/ ../terminal-1/linux/ stage-terminal-1/00-install/files/linux/
touch stage2/SKIP_IMAGES
cp ../terminal-1/linux/image/config config
echo 'FIRST_USER_PASS=choose-a-password' >> config
./build-docker.sh
ls deploy/
```

Flash the result to the eMMC with rpiboot and Raspberry Pi Imager (*Use custom*). The image user is
`terminal`; don't rename it with Imager's customisation, because the session unit is set up for it.

## Software choices and versions (checked November 2026)

| What | How it is installed | Notes |
|---|---|---|
| Raspberry Pi OS Lite 64-bit | Imager | Trixie 2026-10-06 is current; Bookworm is "Legacy". Both keep the boot partition at `/boot/firmware`. |
| cage, foot, tmux, zsh, vlock, NetworkManager, OpenSSH, git | Debian packages | |
| Node.js 22 | NodeSource apt repository (`node_22.x`, `nodistro`, arm64) | Node 22 is in maintenance LTS until April 2027; `--node-major 24` moves to the current LTS. |
| Claude Code | native installer `curl -fsSL https://claude.ai/install.sh \| bash` (default, auto-updates); `--claude-method apt` uses Anthropic's signed apt repository | Needs 4 GB RAM and arm64, both met by the CM4. |
| Azure CLI | Microsoft apt repository, arm64 | Microsoft has no `trixie` suite yet, so the installer uses the `bookworm` suite, as Microsoft's docs advise for newer Debian; if apt refuses, it falls back to PyPI in `/opt/azure-cli`. |

## Open items

- Panel overlay and backlight control for the chosen 720 x 720 panel (`config-txt-fragment.txt`).
- `dtoverlay=dwc2,dr_mode=host` (from `interfaces.md`) versus the stock CM4 `otg_mode=1` (XHCI): the
  installer comments out `otg_mode=1`. Check on the bench which works better and update `interfaces.md`.
- RTC overlay parameters (`i2c_csi_dsi`, `i2c_vc`) need checking on the IO board.
- Agree with the firmware that a short power-button press means "screen off / on".
- USB VID/PID is the pid.codes test ID; update `config/udev/99-terminal-1.rules` when the real PID arrives.
- Disk encryption: try the procedure on the bench, then consider baking the initramfs parts into the image.

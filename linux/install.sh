#!/usr/bin/env bash
# install.sh: turn a fresh Raspberry Pi OS Lite (64-bit) into Terminal 1.
#
# Safe to run again: every step checks what is already there and only changes
# what differs. Run it as root on the device (or inside the image build chroot):
#
#   sudo ./install.sh                    # everything, for the user who ran sudo
#   sudo ./install.sh --dry-run          # print what would happen, change nothing
#   sudo ./install.sh --skip-claude --skip-azure
#
# Tested: `bash -n`, shellcheck (if available) and --dry-run on a development
# machine. NOT yet run end to end on a CM4; see linux/README.md for status.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$SCRIPT_DIR/config"

DRY_RUN=0
IMAGE_BUILD=0
SKIP_CLAUDE=0
SKIP_AZURE=0
SKIP_NODE=0
SKIP_CONFIG_TXT=0
SKIP_SESSION=0
SSH_KEYS_ONLY=0
NODE_MAJOR=22
CLAUDE_METHOD=native
TARGET_USER="${SUDO_USER:-}"

MARKER_BEGIN="# >>> terminal-1 >>>"
MARKER_END="# <<< terminal-1 <<<"
CHANGED=0

usage() {
    cat <<'EOF'
Usage: sudo ./install.sh [options]

  --user NAME            user who gets the kiosk session (default: the user who ran sudo)
  --dry-run              print every change, make none (runs without root)
  --skip-claude          do not install Claude Code
  --skip-azure           do not install the Azure CLI
  --skip-node            do not install Node.js
  --skip-config-txt      leave /boot/firmware/config.txt alone (for example on a Pi that is not a CM4)
  --skip-session         do not enable the cage + foot session on tty1 (keep the normal console login)
  --ssh-keys-only        turn off SSH password logins (add your public key first!)
  --node-major N         Node.js major version from NodeSource (default 22)
  --claude-method M      native (default, auto-updates), apt (signed repo) or npm
  --image-build          running inside the pi-gen chroot: no service starts, no udev reloads
  -h, --help             this help
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --user) TARGET_USER="${2:?--user needs a name}"; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        --skip-claude) SKIP_CLAUDE=1; shift ;;
        --skip-azure) SKIP_AZURE=1; shift ;;
        --skip-node) SKIP_NODE=1; shift ;;
        --skip-config-txt) SKIP_CONFIG_TXT=1; shift ;;
        --skip-session) SKIP_SESSION=1; shift ;;
        --ssh-keys-only) SSH_KEYS_ONLY=1; shift ;;
        --node-major) NODE_MAJOR="${2:?--node-major needs a number}"; shift 2 ;;
        --claude-method) CLAUDE_METHOD="${2:?--claude-method needs native, apt or npm}"; shift 2 ;;
        --image-build) IMAGE_BUILD=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "install.sh: unknown option $1" >&2; usage >&2; exit 2 ;;
    esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

say() { printf '\n==> %s\n' "$*"; }
note() { printf '    %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

# Run a command, or print it in dry-run mode.
run() {
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '    [dry-run]'
        printf ' %q' "$@"
        printf '\n'
    else
        "$@"
    fi
}

# Run a command as the target user with a login-like environment.
run_as_user() {
    run sudo -u "$TARGET_USER" -H env "HOME=$TARGET_HOME" "$@"
}

# install_file SOURCE DESTINATION MODE: copy only when the content differs.
install_file() {
    local source="$1" destination="$2" mode="$3"
    [ -f "$source" ] || die "missing file in the repository: $source"
    if [ -f "$destination" ] && cmp -s "$source" "$destination"; then
        return 0
    fi
    note "install $destination"
    run install -D -m "$mode" "$source" "$destination"
    CHANGED=1
}

# install_text DESTINATION MODE: like install_file, content from stdin.
install_text() {
    local destination="$1" mode="$2" temporary
    temporary="$(mktemp)"
    cat >"$temporary"
    install_file "$temporary" "$destination" "$mode"
    rm -f "$temporary"
}

# replace_block FILE BLOCK_FILE: put BLOCK_FILE between the terminal-1 markers at the end of FILE.
replace_block() {
    local file="$1" block="$2" temporary
    temporary="$(mktemp)"
    if [ -f "$file" ]; then
        awk -v begin="$MARKER_BEGIN" -v end="$MARKER_END" '
            $0 == begin { skipping = 1; next }
            $0 == end { skipping = 0; next }
            !skipping { print }
        ' "$file" >"$temporary"
    fi
    # Drop trailing blank lines left by an earlier block, then append the new block.
    awk 'NF { for (i = 0; i < blank; i++) print ""; blank = 0; print; next } { blank++ }' \
        "$temporary" >"$temporary.trimmed"
    {
        cat "$temporary.trimmed"
        printf '\n%s\n' "$MARKER_BEGIN"
        cat "$block"
        printf '%s\n' "$MARKER_END"
    } >"$temporary"
    rm -f "$temporary.trimmed"
    install_file "$temporary" "$file" 0644
    rm -f "$temporary"
}

apt_install() {
    local missing=() package
    for package in "$@"; do
        if ! dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q "install ok installed"; then
            missing+=("$package")
        fi
    done
    if [ "${#missing[@]}" -eq 0 ]; then
        return 0
    fi
    note "apt install ${missing[*]}"
    run env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${missing[@]}"
    CHANGED=1
}

have() { command -v "$1" >/dev/null 2>&1; }

# passwd_field USER FIELD: one field of the user's passwd entry (6 = home, 7 = shell).
passwd_field() {
    if have getent; then
        getent passwd "$1" 2>/dev/null | cut -d: -f"$2" || true
    fi
}

group_exists() { have getent && getent group "$1" >/dev/null 2>&1; }

# ---------------------------------------------------------------------------
# 1. Checks
# ---------------------------------------------------------------------------

say "Checking the system"

if [ "$DRY_RUN" -eq 0 ] && [ "$(id -u)" -ne 0 ]; then
    die "run as root: sudo $0 (or use --dry-run)"
fi

case "$CLAUDE_METHOD" in native|apt|npm) ;; *) die "--claude-method must be native, apt or npm" ;; esac

OS_CODENAME="unknown"
if [ -r /etc/os-release ]; then
    # shellcheck disable=SC1091
    OS_CODENAME="$(. /etc/os-release && printf '%s' "${VERSION_CODENAME:-unknown}")"
fi
case "$OS_CODENAME" in
    trixie) note "Raspberry Pi OS / Debian 13 trixie (current release, tested target)" ;;
    bookworm) note "Raspberry Pi OS / Debian 12 bookworm (legacy release, supported)" ;;
    *) warn "untested OS codename '$OS_CODENAME'; expected trixie or bookworm" ;;
esac

ARCHITECTURE="$(dpkg --print-architecture 2>/dev/null || uname -m)"
case "$ARCHITECTURE" in
    arm64|aarch64) ;;
    *)
        if [ "$DRY_RUN" -eq 1 ]; then
            warn "architecture is $ARCHITECTURE, not arm64 (fine for a dry run)"
        else
            die "Terminal 1 needs 64-bit Raspberry Pi OS (arm64); this is $ARCHITECTURE"
        fi
        ;;
esac

# Bookworm and Trixie mount the boot partition at /boot/firmware; Bullseye and older at /boot.
BOOT_DIR=/boot/firmware
if [ ! -f "$BOOT_DIR/config.txt" ] && [ -f /boot/config.txt ] && ! grep -q "DO NOT EDIT" /boot/config.txt 2>/dev/null; then
    BOOT_DIR=/boot
    warn "using /boot/config.txt (pre-Bookworm layout)"
fi
note "boot partition: $BOOT_DIR"

if [ -z "$TARGET_USER" ] || [ "$TARGET_USER" = root ]; then
    die "say which user gets the session: sudo ./install.sh --user NAME"
fi
if id "$TARGET_USER" >/dev/null 2>&1; then
    TARGET_HOME="$(passwd_field "$TARGET_USER" 6)"
    TARGET_HOME="${TARGET_HOME:-$(eval echo "~$TARGET_USER")}"
elif [ "$DRY_RUN" -eq 1 ]; then
    TARGET_HOME="/home/$TARGET_USER"
    warn "user $TARGET_USER does not exist (fine for a dry run)"
else
    die "user $TARGET_USER does not exist; create it first or pass --user"
fi
note "session user: $TARGET_USER ($TARGET_HOME)"

# ---------------------------------------------------------------------------
# 2. Packages from Raspberry Pi OS / Debian
# ---------------------------------------------------------------------------

say "Installing packages"
run apt-get update
apt_install \
    cage foot foot-terminfo \
    zsh tmux vlock \
    fonts-terminus fonts-terminus-otb fonts-dejavu-core console-setup \
    network-manager openssh-server openssh-client \
    git curl ca-certificates gnupg lsb-release \
    python3 python3-serial \
    less nano htop rsync cryptsetup

# ---------------------------------------------------------------------------
# 3. User and groups
# ---------------------------------------------------------------------------

say "Setting up user $TARGET_USER"
if ! group_exists terminal-1; then
    run groupadd --system terminal-1
    CHANGED=1
fi
for group in terminal-1 video render input dialout; do
    if group_exists "$group" || [ "$DRY_RUN" -eq 1 ]; then
        if ! id -nG "$TARGET_USER" 2>/dev/null | tr ' ' '\n' | grep -qx "$group"; then
            run usermod -aG "$group" "$TARGET_USER"
            CHANGED=1
        fi
    fi
done
if [ "$(passwd_field "$TARGET_USER" 7)" != /usr/bin/zsh ]; then
    run chsh -s /usr/bin/zsh "$TARGET_USER"
    CHANGED=1
fi

# ---------------------------------------------------------------------------
# 4. Terminal, shell and tmux configuration
# ---------------------------------------------------------------------------

say "Installing configuration"
install_file "$CONFIG_DIR/foot.ini" /etc/xdg/foot/foot.ini 0644
install_file "$CONFIG_DIR/tmux.conf" /etc/tmux.conf 0644
install_file "$CONFIG_DIR/zshrc" /etc/terminal-1/zshrc 0644
install_file "$SCRIPT_DIR/bin/terminal-1-session" /usr/local/bin/terminal-1-session 0755

# ~/.zshrc: create it, or add one line that sources the Terminal 1 settings. Never overwrite.
USER_ZSHRC="$TARGET_HOME/.zshrc"
SOURCE_LINE='[ -r /etc/terminal-1/zshrc ] && source /etc/terminal-1/zshrc  # Terminal 1'
if [ ! -f "$USER_ZSHRC" ] || ! grep -qF "/etc/terminal-1/zshrc" "$USER_ZSHRC"; then
    note "add Terminal 1 settings to $USER_ZSHRC"
    if [ "$DRY_RUN" -eq 0 ]; then
        printf '%s\n' "$SOURCE_LINE" >>"$USER_ZSHRC"
        chown "$TARGET_USER:" "$USER_ZSHRC"
    fi
    CHANGED=1
fi

# Text console fallback (Ctrl+Alt+F2, or if cage fails): Terminus 8x16 = 90 x 45 on 720 x 720.
if [ -f /etc/default/console-setup ] || [ "$DRY_RUN" -eq 1 ]; then
    if ! grep -q '^FONTFACE="Terminus"' /etc/default/console-setup 2>/dev/null \
        || ! grep -q '^FONTSIZE="8x16"' /etc/default/console-setup 2>/dev/null; then
        note "console font Terminus 8x16"
        run sed -i -e 's/^FONTFACE=.*/FONTFACE="Terminus"/' -e 's/^FONTSIZE=.*/FONTSIZE="8x16"/' \
            /etc/default/console-setup
        CHANGED=1
    fi
fi

# ---------------------------------------------------------------------------
# 5. Status daemon, udev, logind, SSH
# ---------------------------------------------------------------------------

say "Installing the status daemon and system integration"
install_file "$SCRIPT_DIR/status-daemon/terminal-1-statusd" /usr/local/bin/terminal-1-statusd 0755
install_file "$SCRIPT_DIR/status-daemon/terminal-1-ctl" /usr/local/bin/terminal-1-ctl 0755
install_file "$CONFIG_DIR/systemd/terminal-1-statusd.service" /etc/systemd/system/terminal-1-statusd.service 0644
if [ ! -f /etc/default/terminal-1-statusd ]; then
    install_file "$CONFIG_DIR/terminal-1-statusd.env" /etc/default/terminal-1-statusd 0644
fi
install_file "$CONFIG_DIR/udev/99-terminal-1.rules" /etc/udev/rules.d/99-terminal-1.rules 0644
install_file "$CONFIG_DIR/logind/terminal-1-power-key.conf" /etc/systemd/logind.conf.d/terminal-1-power-key.conf 0644
install_file "$CONFIG_DIR/ssh/sshd-terminal-1.conf" /etc/ssh/sshd_config.d/terminal-1.conf 0644
install_file "$CONFIG_DIR/ssh/ssh-client-terminal-1.conf" /etc/ssh/ssh_config.d/terminal-1.conf 0644
if [ "$SSH_KEYS_ONLY" -eq 1 ]; then
    if [ ! -s "$TARGET_HOME/.ssh/authorized_keys" ]; then
        warn "--ssh-keys-only but $TARGET_HOME/.ssh/authorized_keys is empty: you may lock yourself out of SSH"
    fi
    printf 'PasswordAuthentication no\n' | install_text /etc/ssh/sshd_config.d/terminal-1-keys-only.conf 0644
fi

# ---------------------------------------------------------------------------
# 6. Kiosk session: cage + foot on tty1
# ---------------------------------------------------------------------------

if [ "$SKIP_SESSION" -eq 0 ]; then
    say "Installing the cage + foot session on tty1"
    install_file "$CONFIG_DIR/pam/terminal-1-session" /etc/pam.d/terminal-1-session 0644
    install_file "$CONFIG_DIR/systemd/terminal-1-session.service" /etc/systemd/system/terminal-1-session.service 0644
    printf '[Service]\nUser=%s\nWorkingDirectory=%s\n' "$TARGET_USER" "$TARGET_HOME" \
        | install_text /etc/systemd/system/terminal-1-session.service.d/user.conf 0644
fi

# ---------------------------------------------------------------------------
# 7. Boot configuration (config.txt)
# ---------------------------------------------------------------------------

if [ "$SKIP_CONFIG_TXT" -eq 0 ]; then
    say "Updating $BOOT_DIR/config.txt"
    CONFIG_TXT="$BOOT_DIR/config.txt"
    if [ -f "$CONFIG_TXT" ] || [ "$DRY_RUN" -eq 1 ]; then
        if [ -f "$CONFIG_TXT" ] && [ ! -f "$CONFIG_TXT.before-terminal-1" ]; then
            run cp -p "$CONFIG_TXT" "$CONFIG_TXT.before-terminal-1"
        fi
        # The dwc2 overlay and the stock CM4 `otg_mode=1` (XHCI host) both claim the USB 2.0 port.
        if grep -q '^otg_mode=1' "$CONFIG_TXT" 2>/dev/null; then
            note "comment out otg_mode=1 (Terminal 1 uses dtoverlay=dwc2,dr_mode=host)"
            run sed -i 's/^otg_mode=1/#otg_mode=1  # disabled by Terminal 1 install.sh, see config-txt-fragment.txt/' "$CONFIG_TXT"
            CHANGED=1
        fi
        BLOCK="$(mktemp)"
        { printf '[all]\n'; cat "$CONFIG_DIR/config-txt-fragment.txt"; } >"$BLOCK"
        if [ -f "$CONFIG_TXT" ]; then
            replace_block "$CONFIG_TXT" "$BLOCK"
        else
            note "[dry-run] would add the Terminal 1 block to $CONFIG_TXT"
        fi
        rm -f "$BLOCK"
    else
        warn "$CONFIG_TXT not found; skipping"
    fi
fi

# ---------------------------------------------------------------------------
# 8. Node.js (NodeSource apt repository)
# ---------------------------------------------------------------------------

if [ "$SKIP_NODE" -eq 0 ]; then
    say "Installing Node.js $NODE_MAJOR"
    CURRENT_NODE_MAJOR=0
    if have node; then
        CURRENT_NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
    fi
    if [ "$CURRENT_NODE_MAJOR" -ge "$NODE_MAJOR" ] 2>/dev/null; then
        note "Node.js $(node --version) already installed"
    else
        # Same files NodeSource's setup_$NODE_MAJOR.x script writes, without piping a script to bash.
        if [ ! -s /usr/share/keyrings/nodesource.gpg ]; then
            note "add the NodeSource signing key"
            if [ "$DRY_RUN" -eq 0 ]; then
                curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
                    | gpg --dearmor --yes -o /usr/share/keyrings/nodesource.gpg
                chmod 0644 /usr/share/keyrings/nodesource.gpg
            fi
        fi
        install_text /etc/apt/sources.list.d/nodesource.sources 0644 <<EOF
Types: deb
URIs: https://deb.nodesource.com/node_$NODE_MAJOR.x
Suites: nodistro
Components: main
Architectures: arm64
Signed-By: /usr/share/keyrings/nodesource.gpg
EOF
        # Prefer NodeSource's nodejs over Debian's older one.
        install_text /etc/apt/preferences.d/nodejs 0644 <<'EOF'
Package: nodejs
Pin: origin deb.nodesource.com
Pin-Priority: 600
EOF
        run apt-get update
        run env DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs
        CHANGED=1
    fi
fi

# ---------------------------------------------------------------------------
# 9. Azure CLI (Microsoft apt repository, arm64 packages since CLI 2.46)
# ---------------------------------------------------------------------------

if [ "$SKIP_AZURE" -eq 0 ]; then
    say "Installing the Azure CLI"
    if have az; then
        note "Azure CLI already installed ($(az version --query '"azure-cli"' -o tsv 2>/dev/null || echo unknown))"
    else
        # Microsoft publishes bullseye and bookworm suites but (as of November 2026) no trixie
        # suite. Their docs say to use the bookworm suite on newer Debian; its arm64 package
        # bundles its own Python and only needs libc, libssl3, libffi8 and zlib.
        case "$OS_CODENAME" in
            bullseye|bookworm) AZURE_SUITE="$OS_CODENAME" ;;
            *) AZURE_SUITE=bookworm; note "no Microsoft suite for $OS_CODENAME; using bookworm" ;;
        esac
        if [ ! -s /etc/apt/keyrings/microsoft.gpg ]; then
            note "add the Microsoft signing key"
            run install -d -m 0755 /etc/apt/keyrings
            if [ "$DRY_RUN" -eq 0 ]; then
                curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
                    | gpg --dearmor --yes -o /etc/apt/keyrings/microsoft.gpg
                chmod 0644 /etc/apt/keyrings/microsoft.gpg
            fi
        fi
        install_text /etc/apt/sources.list.d/azure-cli.sources 0644 <<EOF
Types: deb
URIs: https://packages.microsoft.com/repos/azure-cli/
Suites: $AZURE_SUITE
Components: main
Architectures: arm64
Signed-By: /etc/apt/keyrings/microsoft.gpg
EOF
        if run apt-get update && run env DEBIAN_FRONTEND=noninteractive apt-get install -y azure-cli; then
            CHANGED=1
        else
            # Fallback: Microsoft's PyPI package in its own virtual environment.
            warn "apt install of azure-cli failed; installing from PyPI into /opt/azure-cli instead"
            run rm -f /etc/apt/sources.list.d/azure-cli.sources
            apt_install python3-venv
            run python3 -m venv /opt/azure-cli
            run /opt/azure-cli/bin/pip install --upgrade pip azure-cli
            run ln -sf /opt/azure-cli/bin/az /usr/local/bin/az
            CHANGED=1
        fi
    fi
fi

# ---------------------------------------------------------------------------
# 10. Claude Code
# ---------------------------------------------------------------------------

if [ "$SKIP_CLAUDE" -eq 0 ]; then
    say "Installing Claude Code ($CLAUDE_METHOD)"
    case "$CLAUDE_METHOD" in
        native)
            # Recommended by code.claude.com/docs/en/setup. Installs to ~/.local/bin and
            # updates itself in the background.
            if [ -x "$TARGET_HOME/.local/bin/claude" ]; then
                note "Claude Code already installed for $TARGET_USER (it updates itself)"
            else
                run_as_user bash -c 'curl -fsSL https://claude.ai/install.sh | bash'
                CHANGED=1
            fi
            ;;
        apt)
            # Signed apt repository (stable channel). Updated with apt, not by itself.
            if [ ! -s /etc/apt/keyrings/claude-code.asc ]; then
                run install -d -m 0755 /etc/apt/keyrings
                run curl -fsSL https://downloads.claude.ai/keys/claude-code.asc -o /etc/apt/keyrings/claude-code.asc
                if [ "$DRY_RUN" -eq 0 ] && ! gpg --show-keys /etc/apt/keyrings/claude-code.asc 2>/dev/null \
                    | tr -d ' ' | grep -q 31DDDE24DDFAB679F42D7BD2BAA929FF1A7ECACE; then
                    rm -f /etc/apt/keyrings/claude-code.asc
                    die "Claude Code signing key fingerprint did not match; not installing"
                fi
            fi
            printf 'deb [signed-by=/etc/apt/keyrings/claude-code.asc] https://downloads.claude.ai/claude-code/apt/stable stable main\n' \
                | install_text /etc/apt/sources.list.d/claude-code.list 0644
            run apt-get update
            apt_install claude-code
            ;;
        npm)
            # Global npm install into the user's own prefix (never sudo npm install -g).
            if [ -x "$TARGET_HOME/.npm-global/bin/claude" ]; then
                note "Claude Code already installed with npm"
            else
                run_as_user npm config set prefix "$TARGET_HOME/.npm-global"
                run_as_user npm install -g @anthropic-ai/claude-code@latest
                CHANGED=1
            fi
            ;;
    esac
fi

# ---------------------------------------------------------------------------
# 11. Services
# ---------------------------------------------------------------------------

say "Enabling services"
if [ "$IMAGE_BUILD" -eq 0 ]; then
    run systemctl daemon-reload
fi
run systemctl enable NetworkManager.service
if [ "$IMAGE_BUILD" -eq 0 ]; then
    # In the image build, pi-gen's ENABLE_SSH decides (off: the image has a known password).
    run systemctl enable ssh.service
fi
run systemctl enable terminal-1-statusd.service
run systemctl set-default multi-user.target
if [ "$SKIP_SESSION" -eq 0 ]; then
    run systemctl enable terminal-1-session.service
    # The session owns tty1; getty@tty1 stays available on the other consoles via autovt.
    run systemctl disable getty@tty1.service
fi
if [ "$IMAGE_BUILD" -eq 0 ]; then
    run udevadm control --reload-rules
    run udevadm trigger --subsystem-match=tty --subsystem-match=input
    run systemctl restart terminal-1-statusd.service
    run systemctl reload ssh.service
    # logind and the session are not restarted here: restarting logind can end the
    # console login you are running this from. They take effect after a reboot.
fi

say "Done"
if [ "$DRY_RUN" -eq 1 ]; then
    note "dry run: nothing was changed"
elif [ "$CHANGED" -eq 1 ]; then
    note "Reboot to start the Terminal 1 session on the screen: sudo reboot"
else
    note "Everything was already in place."
fi
note "Next: set up Wi-Fi with 'nmtui', then read linux/security.md (disk encryption, SSH keys)."

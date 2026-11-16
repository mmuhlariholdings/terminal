#!/bin/bash -e
# pi-gen step: copy linux/ from this repository into the image and run install.sh in the chroot.
# The workflow puts the repository's linux/ folder at files/linux before the build.

if [ ! -x files/linux/install.sh ]; then
	echo "files/linux/install.sh missing: copy the repository's linux/ folder here first" >&2
	exit 1
fi

install -d "${ROOTFS_DIR}/opt/terminal-1"
rm -rf "${ROOTFS_DIR}/opt/terminal-1/linux"
cp -a files/linux "${ROOTFS_DIR}/opt/terminal-1/linux"

# Claude Code from Anthropic's signed apt repository: reproducible in a chroot and
# updated with apt. (On a device, install.sh defaults to the self-updating native installer.)
on_chroot << CHROOT
/opt/terminal-1/linux/install.sh --image-build --user "${FIRST_USER_NAME}" --claude-method apt
CHROOT

# The image ships with a known password: remind the user until they change it.
install -d "${ROOTFS_DIR}/etc/terminal-1"
touch "${ROOTFS_DIR}/etc/terminal-1/default-password-in-use"

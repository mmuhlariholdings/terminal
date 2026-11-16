#!/bin/bash -e
# pi-gen: start this stage from a copy of stage2 (Raspberry Pi OS Lite).
if [ ! -d "${ROOTFS_DIR}" ]; then
	copy_previous
fi

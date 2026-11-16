/*
 * version.h: firmware version and board revision. The version is set in ONE place, the project() line of
 * firmware/keyboard-board/CMakeLists.txt, which passes it in as FIRMWARE_VERSION.
 */
#ifndef TERMINAL_VERSION_H
#define TERMINAL_VERSION_H

#include "board.h"

#ifndef FIRMWARE_VERSION
#define FIRMWARE_VERSION "0.0.0-unknown"
#endif

#if TERMINAL_BOARD_BENCH
#define BOARD_REVISION "bench"
#else
#define BOARD_REVISION BOARD_REVISION_LETTER
#endif

#endif

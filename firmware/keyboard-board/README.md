# Keyboard board firmware (RP2040)

Firmware for the Terminal 1 keyboard and power board, and for the **Phase 0 bench build** on a plain Raspberry Pi Pico.
C, [Raspberry Pi Pico SDK](https://github.com/raspberrypi/pico-sdk) + TinyUSB. **Not yet run on hardware**; the pure logic
(key map, debounce, sticky modifiers, trackpad, power state machine, status protocol) is covered by host tests that pass.

## What it does

- Scans the BlackBerry Q20 keyboard matrix (7 rows × 6 columns + one directly read nav key) with debounce.
- Applies the **terminal key map** ([`src/keymap_table.c`](src/keymap_table.c), the only place to edit it) with sticky Ctrl, Fn and Shift.
- Trackpad: arrow keys by default, mouse mode on request; trackpad click = Enter.
- Composite USB device (interfaces.md section 7): HID keyboard, HID mouse, HID system control (power key), CDC status port with
  the `BAT` / `PWR` / `VER` line protocol.
- Power manager: enables the 5 V boost and releases `CM4_GLOBAL_EN` on a short press; long press (2 s) sends the HID power key,
  waits for the CM4's `POWEROFF` signal (or 30 s), then cuts power; 10 s hold = hard off; low and critical battery events.
- Service mode: hold **Fn + Back** while pressing power to route the CM4's USB to the USB-C port and pull `nRPIBOOT` low.
- Drivers: BQ25895 charger, MAX17048 gauge, keyboard backlight PWM.

Pins: [`src/board.h`](src/board.h). It must match `hardware/keyboard-board/electronics/pin-map.md` (the keyboard board's
schematic generator owns the pin map and stops with an error if `board.h` disagrees with it).

## Key map (cheat sheet)

| Key above the keyboard | Terminal job |
|---|---|
| Call | **Ctrl** (sticky: tap once, or hold) |
| BlackBerry menu | **Esc** |
| Back | **Tab** |
| End | **Fn** (sticky) |
| sym | Linux Alt / Meta |
| alt | Printed symbols (next key) |
| Trackpad | Arrow keys (mouse mode: `terminal-1-ctl trackpad mouse`) · click = Enter |
| Fn + `0` (microphone key) | F10 |

Letters (plain = the lowercase letter; Shift = capital):

| Key | Alt (printed) | Fn (terminal layer) |
|---|---|---|
| A | `*` | `&` |
| B | `!` | `\` |
| C | `9` | F9 |
| D | `5` | F5 |
| E | `2` | F2 |
| F | `6` | F6 |
| G | `/` | `` ` `` |
| H | `:` | `^` |
| I | `-` | `}` |
| J | `;` | `[` |
| K | `'` | `]` |
| L | `"` |  |
| M | `.` | `>` |
| N | `,` | `<` |
| O | `+` |  |
| P | `@` | `\|` |
| Q | `#` | `%` |
| R | `3` | F3 |
| S | `4` | F4 |
| T | `(` | `~` |
| U | `_` | `{` |
| V | `?` |  |
| W | `1` | F1 |
| X | `8` | F8 |
| Y | `)` | `=` |
| Z | `7` | F7 |

Matrix positions and printed symbols come from Solder Party's [i2c_puppet](https://github.com/solderparty/i2c_puppet) firmware
(MIT, © 2022 Solder Party AB); the matrix wiring follows the [BBQ20KBD](https://github.com/solderparty/bbq20kbd_hw) board
(CERN-OHL-1.2). The Fn-layer symbol choices are a first draft to refine with use (product plan, section 7).

## Build

Needs CMake, an Arm GCC toolchain (`arm-none-eabi-gcc`) and the Pico SDK.

```sh
git clone --depth 1 https://github.com/raspberrypi/pico-sdk.git && (cd pico-sdk && git submodule update --init lib/tinyusb)
cmake -S firmware/keyboard-board -B build/keyboard-board -DPICO_SDK_PATH=$PWD/pico-sdk                        # our board
cmake -S firmware/keyboard-board -B build/bench          -DPICO_SDK_PATH=$PWD/pico-sdk -DTERMINAL_BOARD=bench # a Pico
cmake --build build/keyboard-board     # -> terminal-keyboard-board-firmware.uf2
```

Flash: hold BOOTSEL while plugging in USB, then copy the `.uf2` onto the `RPI-RP2` drive.

## Tests (no hardware needed)

```sh
cmake -S firmware/keyboard-board/test -B build/firmware-tests && cmake --build build/firmware-tests && (cd build/firmware-tests && ctest)
```

Last run 2026-11-17 on macOS: **5/5 test programs pass** (keymap, debounce, power state, status protocol, trackpad logic).
The full firmware has **not been cross-compiled locally** (no Arm toolchain on the design machine); `.github/workflows/firmware.yml` builds it on every pull request.

## Bench wiring (Phase 0)

Same GPIO numbers on a Pico. GPIO 23, 24, 25 and 29 aren't on the Pico header, so the bench build never drives GPIO 23 or
reads 24/29, and uses the Pico LED (GPIO 25) to show "the boost would be on". Wire the Q20 keyboard's FPC (through a breakout)
to the row and column pins in `src/board.h`.

## USB IDs

`1209:0001` is the [pid.codes](https://pid.codes) **test** ID. Apply for a free open-hardware PID before anything ships, then
update `src/usb_descriptors.c`, `system/plan/interfaces.md` and `linux/config/udev/99-terminal-1.rules`.

# 0005. Q20 keyboard on an RP2040 that also manages power

- **Status:** Accepted
- **Date:** 2026-11-16
- **Decided by:** Owner (prototype plan, "Electronics")

## Context

Real BlackBerry keys are the point of the device, and moulding our own is out of scope. Solder Party's open BBQ20KBD design runs
a BlackBerry Q20 (Classic) replacement keyboard and its trackpad from an RP2040. The device also needs something always awake to
watch the power button and battery, and to turn the CM4 on and off safely, since Linux on the CM4 has no phone-like sleep.

## Decision

A **BlackBerry Q20 replacement keyboard with trackpad, run by our own RP2040 board**, which is also the **power manager**: it
appears to Linux as a standard USB keyboard and mouse (no special driver), asks Linux to shut down cleanly before cutting power,
and reports battery state to Linux. The key map lives in the RP2040 firmware.

## Consequences

- Keyboards are old spare parts: buy several now, and keep the controller adaptable to another keyboard later.
- The terminal key remap (Ctrl, Esc, Tab, Fn on the four keys above the keyboard, Fn layers, sticky modifiers) changes without
  touching Linux.
- The firmware is adapted from, and credits, the open BBQ20KBD work (licence noted in `firmware/keyboard-board/README.md`).

## Alternatives considered

- **Off-the-shelf BBQ20KBD board over I2C:** less to design, but we want USB HID and the power manager on one board.
- **Custom moulded keyboard:** far beyond a prototype's budget.

## How we check it

Phase 1 gate: typing is reliable, charging is safe, and the power button shuts Linux down cleanly.

## Related

`system/plan/interfaces.md` (sections 6–8); `hardware/keyboard-board/`; `firmware/keyboard-board/`; 0004, 0006.

# 0006. USB service mode through the charging port

- **Status:** Proposed
- **Date:** 2026-11-16
- **Decided by:** Proposed by the AI assistant during the first design pass; awaiting owner approval

## Context

The CM4's eMMC is flashed over its USB port with `rpiboot` while `nRPIBOOT` is held low at power-up. In Terminal 1 the CM4's only
USB 2.0 port goes to the RP2040 (keyboard). With a single USB-C port used for charging, there would be no way to reflash the
device without opening it. The plan also leaves open whether to add a second USB-C port.

## Decision

Put a **USB 2.0 analogue switch (TS3USB221 class)** on the keyboard board. Normally the CM4's USB goes to the RP2040. In
**service mode** (hold `Fn` + `Back` while pressing power) the RP2040 routes the CM4's USB to the USB-C port and pulls
`CM4_nRPIBOOT` low, so a computer can flash the eMMC; the same path allows Linux USB gadget mode (for example Ethernet over USB).

## Consequences

- One small part and two control lines; no second port needed for v1.
- The keyboard does not work in service mode (expected: the computer is in control).
- The USB-C data lines are not used for charger detection; the charger's input current is set from the CC pins instead.

## Alternatives considered

- **Second USB-C port:** more space, cost and an extra opening; still an open decision for later.
- **Test pads only:** needs the back off every time; poor for contributors flashing images.

## How we check it

Phase 1 bench test: `rpiboot` sees the CM4 through the USB-C port in service mode; normal mode types into Linux.

## Related

`system/plan/interfaces.md` (sections 4 and 6); `hardware/keyboard-board/`; `firmware/keyboard-board/`; 0005.

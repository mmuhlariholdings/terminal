# 0003. Square 720 by 720 screen on MIPI DSI

- **Status:** Accepted
- **Date:** 2026-11-16
- **Decided by:** Owner (prototype plan, screen decision); DSI interface proposed in this record, plan open decision "Screen interface"

## Context

A terminal needs about 80 columns. A 4-inch 720 × 720 IPS panel with an 8 × 16 pixel font shows 90 × 45 characters, and the square
shape suits a candybar body. The plan left DSI or DPI open, depending on which panel can be sourced with good Linux drivers.
DPI uses most of the CM4's GPIO pins; DSI uses the CM4's dedicated display lanes.

## Decision

Use a **4-inch 720 × 720 IPS panel on MIPI DSI**, connected through a **Raspberry Pi standard 22-pin 0.5 mm FPC connector**
(as the CM4 IO board's DISP1, 4 lanes). Any panel with a Pi-compatible DSI cable or a small adapter fits without a new carrier.

## Consequences

- The carrier board routes DSI as 100 Ω differential pairs (see the carrier board's routing notes).
- GPIO pins stay free for the power-management signals.
- The exact panel and its device-tree overlay are still to be chosen and proven on the bench in Phase 0.

## Alternatives considered

- **DPI (parallel RGB), e.g. as on HyperPixel-style panels:** simple, well supported, but uses about 28 GPIO pins and more power.
- **Sharp memory display (400 × 240):** sunlight readable and frugal, but only about 66 × 20 characters.

## How we check it

Phase 0: the chosen panel shows a 90 × 45 terminal on the CM4 IO board's DSI connector with a stock or published overlay.

## Related

`system/plan/interfaces.md` (sections 2 and 5); `hardware/carrier-board/`; `linux/config/`.

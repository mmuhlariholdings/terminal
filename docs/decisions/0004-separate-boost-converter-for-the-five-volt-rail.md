# 0004. Separate boost converter for the five volt rail

- **Status:** Proposed
- **Date:** 2026-11-16
- **Decided by:** Proposed by the AI assistant during the first design pass; awaiting owner approval

## Context

The plan says the BQ25895 "charges the cell from USB-C and boosts the battery to 5 V for the CM4, and the device keeps running
while it charges". The BQ25895's boost (OTG) mode drives its VBUS pin and cannot run while it is charging from VBUS; while charging,
its power-path output (SYS) sits at about 3.5–4.4 V, not 5 V. The CM4 needs 5 V with peaks around 2 A or more, plus the screen.

## Decision

Keep the **BQ25895 as charger and power-path manager**, and power the CM4 from a **separate synchronous boost converter
(TPS61088 class) fed from SYS**, giving 5.1 V at up to 3 A. The RP2040 enables the boost (see 0005).

## Consequences

- The device runs from USB power and charges at the same time, as the plan requires.
- One more inductor and IC on the keyboard board, and boost losses (about 90 % efficient, an estimate) count against battery life.
- The boost must be sized for the CM4's peaks at the lowest battery voltage (hand calculation in
  `hardware/keyboard-board/electronics/circuit-notes.md`).

## Alternatives considered

- **BQ25895 boost only:** cannot charge and supply 5 V at the same time; the device would brown out or stop charging.
- **A 5 V USB power-bank chip (IP5306 class):** simple, but poor control and documentation, and fixed behaviours.
- **Power the CM4 from SYS directly:** the CM4 requires 5 V.

## How we check it

Phase 1 bench test: CM4 running a CPU stress test from the keyboard board while charging from USB-C, 5 V rail stays above 4.85 V.

## Related

`system/plan/interfaces.md` (section 6); `hardware/keyboard-board/`; 0005.

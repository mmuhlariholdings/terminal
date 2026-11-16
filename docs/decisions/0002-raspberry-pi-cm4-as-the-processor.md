# 0002. Raspberry Pi CM4 as the processor

- **Status:** Accepted
- **Date:** 2026-11-16
- **Decided by:** Owner (prototype plan, "Key decisions")

## Context

Terminal 1 must run 64-bit Linux comfortably enough for SSH, Azure CLI (a Python application) and Claude Code (which needs
Node.js 22 or newer and a 64-bit Arm build). It must also teach the team carrier-board design. Options weighed in the plan:
Raspberry Pi Zero 2 W (512 MB), Radxa Zero 3W (RK3566, 1–8 GB), Raspberry Pi CM4 (4 GB, 32 GB eMMC, Wi-Fi) and CM5.

## Decision

Use a **Raspberry Pi Compute Module 4 with 4 GB of memory, 32 GB of eMMC storage and Wi-Fi/Bluetooth** on our own carrier board.

## Consequences

- We must design a 4-layer, impedance-controlled carrier board (`hardware/carrier-board/`); that is the PCB skill we want.
- Higher power draw than a Zero: the power system must supply about 2 A or more at 5 V in peaks (see 0004).
- Best documentation and software support of the options; the official CM4 IO board design is published as KiCad files.
- The CM5 uses a similar board-to-board connector layout, so a later Terminal could move up (to verify before relying on it).

## Alternatives considered

- **Pi Zero 2 W:** 512 MB is tight for Azure CLI and Node.js, and slow; but small, cheap and proven (Beepy, Hackberry Pi).
- **Radxa Zero 3W:** more memory in a tiny board, but a smaller community and less polished software; no carrier-board learning.
- **CM5:** fastest, but hotter and drains the battery faster. Reconsidered for Terminal 2.

## How we check it

Phase 0 gate: SSH, `az login` and Claude Code run comfortably from the bench keyboard on a CM4 on its official IO board.

## Related

`system/plan/product-plan.md` ("Key decisions"); `hardware/carrier-board/`; 0004.

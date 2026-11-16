# 0007. Open-source licences

- **Status:** Proposed
- **Date:** 2026-11-16
- **Decided by:** Owner asked for an open-source, contributor-friendly project; the licence choice is proposed by the AI assistant

## Context

Terminal 1 is published for others to study, build and improve. Hardware, software and documentation are best served by
different licences. It builds on open work (Raspberry Pi's CM4 IO board design, Solder Party's BBQ20KBD) whose terms must be
respected. Some generator scripts in `tools/` came from the owner's earlier, private Finish Line project; the owner holds their
copyright and can release them.

## Decision

- **Hardware** (KiCad files, generators for them, FeatureScript CAD, fabrication files): **CERN-OHL-S-2.0** (strongly reciprocal).
- **Software** (firmware, Linux scripts, tools, website code): **MIT**.
- **Documentation and media** (plans, manuals, decision records, renders): **CC BY-SA 4.0**.
- Contributions are accepted under the same licences (inbound = outbound), with a Developer Certificate of Origin sign-off.

## Consequences

- Anyone may build and sell Terminal 1 hardware, but modified hardware designs they distribute must stay open.
- Third-party material keeps its own licence, recorded where it is used.
- `LICENSE` at the root explains the split; full texts are in `LICENSES/`.

## Alternatives considered

- **Everything MIT:** simple, but lets hardware forks close.
- **CERN-OHL-P (permissive) for hardware:** more permissive, weaker guarantee that improvements come back.
- **GPL for firmware:** stronger copyleft, but friction with mixing permissively licensed code (for example TinyUSB, MIT).

## How we check it

Reviewed before the repository is made public and whenever third-party design files are imported.

## Related

`LICENSE`; `LICENSES/`; `CONTRIBUTING.md`.

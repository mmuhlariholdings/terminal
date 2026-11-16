# Terminal 1: working context for Claude

Open-source pocket Linux terminal (BlackBerry Q20 keyboard, 4-inch 720 × 720 DSI screen, Raspberry Pi CM4). This repository is
the single home of the project: plan, CAD, electronics, firmware, Linux, docs and website. It is openly **vibe coded**
(record 0010): be explicit about what is verified and mark everything else `CHECK` / *verify*.

## The owner

- Product owner; **no CAD experience**. Explain CAD steps click by click; prefer approaches that need no CAD skill.
- Likes staged work and summaries; flag every assumption and simplification, never skip something silently.
- Engineering numbers are hand estimates unless tested: say so, and point to the test (phase gate) that confirms them.
- The owner commits; don't commit or push unless asked.

## Where things are

- `system/plan/product-plan.md`: the living plan (edit it; add a changelog line). `system/plan/interfaces.md`: **shared numbers**
  (envelope, stack-up, board outlines, inter-board cable, CM4 pins, USB protocol, RP2040 pins). Change numbers there first.
- `docs/decisions/`: decision records (never rewrite an accepted one; supersede). Check: `python3 tools/check_decisions.py`.
- `docs/conventions.md`: names, units, coordinates, generated files, versions, git workflow.
- `hardware/enclosure/terminal-1.fs`: the Onshape model (one custom feature "Terminal 1"); `terminal-1-check.fs` interference/mass test.
- `hardware/keyboard-board/`, `hardware/carrier-board/`: `electronics/generate_schematic.py` (uses `tools/kicadgen.py`, run with
  `--erc`: must be 0 errors / 0 warnings), `generate_pcb.py` (KiCad's Python, `tools/pcbgen.py`, Freerouting via
  `tools/fetch_tools.sh`). Edit the script, never the output.
- `firmware/keyboard-board/`: RP2040 (Pico SDK + TinyUSB); `src/board.h` must match `electronics/pin-map.md`.
- `linux/`: `install.sh`, `config/`, `status-daemon/` (tests: `python3 -m unittest discover -s linux/status-daemon/tests`), `image/` (pi-gen).
- `website/public/`: static launch page (GitHub Pages, `.github/workflows/website.yml`). Repo URL constant `REPO_URL` in `assets/js/site.js`.

## Onshape

- Document did `8bfe7e43f7d7ec8135f9a829`, wid `29c38cad0998e4a6472b08e0`, Part Studio eid `69201118ddf43601f28283ef`.
  Feature Studio **Terminal 1 FS**, eid `3bc3af66b798a4c48861a367`.
- Every MCP call uses the owner's **personal API allocation** (2,500 a year; 1,756 left on 2026-11-16 after the first model, which took about 100 calls). Mention it before
  heavy work; batch changes; don't iterate blindly.
- **Verify with a real regeneration (`create_geometry`) before `put_featurescript`**, and run `terminal-1-check.fs` (0 clashes).
- FeatureScript gotchas learned here:
  - `type` is a reserved word: use `c["type"]`.
  - Don't reuse standard-library names for your own functions (e.g. `hole`); prefix with `t1` / `T1_`.
  - Sub-operations of one id must be contiguous: create cutting tools before the part, under a sibling id.
  - A compile error only shows as "no features found" in `test_feature`: bisect with small snippets.
  - `test_feature` evaluates the **first** feature in the file; report results with `throw regenError(...)` (about 400 characters).
  - From the Finish Line project: dialog defaults come from the field bounds; adding fields means re-inserting the feature;
    `getProperty(NAME)` is unreliable inside a regeneration; `[a, b] * millimeter` fails.
- The MCP cannot export glTF or add a feature to the Part Studio: the owner does both (steps in `hardware/enclosure/README.md`).

## When a design decision changes

0. Decision record (status Proposed) for anything that shapes the device; the owner accepts it.
1. `system/plan/interfaces.md` (+ changelog) if a shared number changes.
2. Model (verify, then put), schematics/boards (regenerate, ERC/DRC), firmware and Linux as listed under "Used by".
3. Build sheets, `system/plan/product-plan.md` and its changelog.
4. The owner commits.

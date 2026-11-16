# Contributing to Terminal 1

Thank you for helping. Terminal 1 is an open-hardware pocket Linux terminal, built in the open and designed with an AI coding
assistant ("vibe coded", see [decision 0010](docs/decisions/0010-built-openly-with-an-ai-coding-assistant.md)). That makes
**human verification** the most valuable thing you can bring. You don't need to be an expert to help.

## Ways to help

| Skill | Good places to start |
|---|---|
| **Anyone** | Check a part number, pinout or price against its datasheet or shop page and fix what's marked `CHECK` / *verify*. Improve docs. Try the website on your phone and report what looks off |
| **Electronics** | Review a schematic (`hardware/*/electronics/*.pdf`), the power design (`hardware/keyboard-board/electronics/circuit-notes.md`), the carrier's high-speed routing (`hardware/carrier-board/electronics/routing-notes.md`) |
| **CAD** | The Onshape model is code: `hardware/enclosure/terminal-1.fs`. Measure real parts (Q20 keyboard, panels, cells) and update `system/plan/interfaces.md` |
| **Firmware** | `firmware/keyboard-board/`: the key map, trackpad, power state machine; host tests run without hardware |
| **Linux** | `linux/`: installer, configs, status daemon (has tests), the image build |
| **Bench builders** | Build the Phase 0 prototype and report results: they are the gates the whole roadmap hangs on |

Look for issues labelled **good first issue** or **help wanted**. Not sure? Open a Discussion and ask.

## How to contribute

1. **Fork and branch** from `main` (any branch name).
2. **Change the source, not the output.** Schematics, boards and the 3D model are generated (`docs/conventions.md`, "Generated
   files"). Edit the script, regenerate, and commit both.
3. **Run what your change affects:**
   | Changed | Run |
   |---|---|
   | A schematic | `python3 hardware/<board>/electronics/generate_schematic.py --erc` → 0 errors, 0 warnings |
   | A board layout | `<KiCad's python3> hardware/<board>/electronics/generate_pcb.py --all` → DRC clean |
   | The 3D model | A real regeneration in Onshape + `hardware/enclosure/terminal-1-check.fs` → 0 clashes |
   | Firmware | `firmware/keyboard-board/` host tests and build (see its README) |
   | Linux | `bash -n linux/install.sh`, shellcheck, `python3 -m unittest discover -s linux/status-daemon/tests` |
   | Decision records | `python3 tools/check_decisions.py` |
4. **Shared numbers** (sizes, pins, the inter-board cable, USB protocol) live in `system/plan/interfaces.md`; change them there
   first and update everything listed under "Used by".
5. **Big changes** (a different part, a new interface, a change of direction): write a decision record (`docs/decisions/template.md`,
   status Proposed) in your pull request.
6. **Open a pull request** using the template. Say what you verified and how. CI must pass.
7. **Sign off** your commits (`git commit -s`): you certify the [Developer Certificate of Origin](https://developercertificate.org/),
   i.e. you have the right to contribute it under the project's licences.

## If you use an AI assistant too

You're welcome to. Say so in the pull request, and **verify what it wrote** the same way we ask of our own AI output: datasheets,
tests, measurements. Never paste a part number, register value or pinout you haven't checked without marking it `CHECK`.

## Licences

By contributing you agree your contribution is licensed under the project's licences: hardware CERN-OHL-S-2.0, software MIT,
documentation CC BY-SA 4.0 ([`LICENSE`](LICENSE)). Don't add third-party material unless its licence allows it; credit it where used.

## Conventions in one breath

Millimetres; lowercase-hyphenated file names (Python scripts use underscores); full words, no abbreviations; every generated file
says which script made it; mark unverified values. Details: [`docs/conventions.md`](docs/conventions.md).

## Conduct

Be kind, assume good faith, and keep it about the work. See [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

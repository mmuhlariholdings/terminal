# 0010. Built openly with an AI coding assistant

- **Status:** Accepted
- **Date:** 2026-11-16
- **Decided by:** Owner

## Context

Terminal 1 is "vibe coded": the plan, FeatureScript CAD, schematic and board generators, firmware, Linux setup, documentation
and website are written largely by an AI coding assistant (Claude Code) directed and reviewed by the owner. That is fast, but AI
output can be confidently wrong (a part number, a pinout, a register value). People building or contributing must know this.

## Decision

Say so plainly, everywhere it matters: in the README, on the website and in `CONTRIBUTING.md`. Treat every AI-written number as
an estimate until a datasheet, a test or a measurement confirms it, and mark unconfirmed items (`CHECK`, *verify*) in the files.
Nothing goes to a fabricator without a human review and the automated checks (ERC, DRC, builds, tests).

## Consequences

- Contributors are especially welcome to verify: datasheet checks, bench measurements and reviews are first-class contributions.
- `CLAUDE.md` holds the assistant's working context so its output stays consistent across sessions.
- The project can move quickly while being honest about what is proven.

## Alternatives considered

- **Not mentioning it:** misleading, and risky for people who build hardware from these files.

## How we check it

Each phase gate (product plan, "Roadmap") is a real-world test; review checklists in the pull request template.

## Related

`README.md`; `CONTRIBUTING.md`; `CLAUDE.md`; `website/`.

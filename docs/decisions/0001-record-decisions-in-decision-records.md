# 0001. Record decisions in decision records

- **Status:** Accepted
- **Date:** 2026-11-16
- **Decided by:** Owner (practice carried over from the Finish Line project)

## Context

Terminal 1 is an open project: contributors arrive later and need to know not just what the device is, but why. The plan PDF
holds decisions in prose and tables; reasons get lost as a plan grows, and a reversed decision overwrites the old text.

## Decision

Every decision that shapes the device (architecture, interfaces between boards, major parts, how things are made, released or
hosted) gets a **decision record** in `docs/decisions/`, also known as an architecture decision record (ADR). The plan
(`system/plan/product-plan.md`) says *what* the device is; the records say *why*. An accepted record is never rewritten: a change
of mind is a new record that supersedes it.

## Consequences

- New decisions start as a record with status **Proposed** in a pull request, and become **Accepted** when the owner approves.
- Anyone can propose a record; this is the main way contributors argue for a change of direction.
- The Checks workflow validates the records on every pull request (`tools/check_decisions.py`).
- Small choices that constrain nothing else (a screw length, a colour) stay in build sheets.

## Alternatives considered

- **Decisions only in the plan:** no history of the reasons.
- **GitHub Discussions only:** good for debate, poor as a permanent, reviewable record next to the design files.

## How we check it

The Checks workflow fails a pull request whose records are malformed, misnumbered or missing from the index.

## Related

`docs/conventions.md` ("Decision records"); `docs/decisions/template.md`; `tools/check_decisions.py`.

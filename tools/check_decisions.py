#!/usr/bin/env python3
"""Check the decision records in docs/decisions/ (run by the Build workflow on every pull request).

Each record NNNN-title-in-full-words.md must: be numbered in sequence from 0001 with no gaps or repeats; start with the heading
"# NNNN. Title"; have a Status line (Proposed, Accepted, Retired, or Superseded by NNNN naming an existing record), a Date
(YYYY-MM-DD) and a Decided by line; have the sections Context, Decision, Consequences, Alternatives considered, How we check it
and Related; and appear in the index table in docs/decisions/README.md with the same status.
Usage: python3 tools/check_decisions.py    (exit code 1 on any problem)
"""
import os
import re
import sys

FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "decisions")
SECTIONS = ["Context", "Decision", "Consequences", "Alternatives considered", "How we check it", "Related"]
NAME = re.compile(r"^(\d{4})-[a-z0-9]+(-[a-z0-9]+)*\.md$")


def main():
    problems = []
    files = sorted(f for f in os.listdir(FOLDER) if f.endswith(".md") and f not in ("README.md", "template.md"))
    numbers = {}
    for f in files:
        m = NAME.match(f)
        if not m:
            problems.append(f"{f}: name must be NNNN-title-in-full-words.md (lowercase, hyphens)")
            continue
        numbers.setdefault(int(m.group(1)), []).append(f)
    for n, fs in numbers.items():
        if len(fs) > 1:
            problems.append(f"number {n:04d} used twice: {', '.join(fs)}")
    if numbers and sorted(numbers) != list(range(1, max(numbers) + 1)):
        problems.append(f"numbers must run 0001 to {max(numbers):04d} with no gaps")
    index = open(os.path.join(FOLDER, "README.md"), encoding="utf-8").read()
    for n, fs in sorted(numbers.items()):
        f = fs[0]
        text = open(os.path.join(FOLDER, f), encoding="utf-8").read()
        if not re.match(rf"# {n:04d}\. \S", text):
            problems.append(f"{f}: first line must be '# {n:04d}. Title'")
        status = re.search(r"^- \*\*Status:\*\* (.+)$", text, re.M)
        if not status:
            problems.append(f"{f}: missing '- **Status:** ...' line")
        else:
            s = status.group(1).strip()
            sup = re.fullmatch(r"Superseded by (\d{4})", s)
            if s not in ("Proposed", "Accepted", "Retired") and not sup:
                problems.append(f"{f}: status '{s}' must be Proposed, Accepted, Retired or 'Superseded by NNNN'")
            if sup and int(sup.group(1)) not in numbers:
                problems.append(f"{f}: superseded by {sup.group(1)}, which doesn't exist")
            row = re.search(rf"^\| \[{n:04d}\]\({re.escape(f)}\) \|[^|]+\| ([^|]+) \|", index, re.M)
            if not row:
                problems.append(f"{f}: not listed in docs/decisions/README.md (row '| [{n:04d}]({f}) | ... |')")
            elif row.group(1).strip() != s:
                problems.append(f"{f}: status '{s}' but the index says '{row.group(1).strip()}'")
        if not re.search(r"^- \*\*Date:\*\* \d{4}-\d{2}-\d{2}$", text, re.M):
            problems.append(f"{f}: missing '- **Date:** YYYY-MM-DD' line")
        if not re.search(r"^- \*\*Decided by:\*\* \S", text, re.M):
            problems.append(f"{f}: missing '- **Decided by:** ...' line")
        heads = re.findall(r"^## (.+)$", text, re.M)
        if heads != SECTIONS:
            problems.append(f"{f}: sections must be, in order: {', '.join(SECTIONS)}")
    if problems:
        print("Decision records: problems found\n  " + "\n  ".join(problems))
        sys.exit(1)
    print(f"Decision records: {len(numbers)} records, all well formed and indexed")


if __name__ == "__main__":
    main()

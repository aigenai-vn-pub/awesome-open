#!/usr/bin/env python3
"""Generate the awesome-open index tables in README.md from data.yaml.

data.yaml is the single source of truth. This script renders the category
tables (with live shields.io badges) and injects them into README.md between
the AUTOGEN markers, leaving all hand-written prose untouched.

Usage:
    python3 scripts/generate_readme.py           # rewrite README.md in place
    python3 scripts/generate_readme.py --check    # verify README is in sync (CI)

--check exits 0 if README already matches data.yaml, 1 otherwise. It never
writes. Use it in CI to prevent the tables from drifting out of sync.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data.yaml"
README = ROOT / "README.md"

START = "<!-- AUTOGEN:start -->"
END = "<!-- AUTOGEN:end -->"

STARS = "https://img.shields.io/github/stars/{repo}?style=flat-square"
LAST = "https://img.shields.io/github/last-commit/{repo}?style=flat-square"


def render_row(project: dict) -> str:
    repo = project["repo"]
    url = f"https://github.com/{repo}"
    stars = f"[![Stars]({STARS.format(repo=repo)})]({url})"
    last = f"[![Last commit]({LAST.format(repo=repo)})]({url})"
    return (
        f"| [{repo}]({url}) | {stars} | {last} | "
        f"{project['description']} | {project['language']} |"
    )


def render_category(cat: dict) -> str:
    label = cat.get("alternative_label")
    suffix = f" ({label})" if label else ""
    lines = [
        f"### {cat['emoji']} {cat['title']}{suffix}",
        "",
        f"**Commercial:** {cat['commercial']}",
        "",
        "| Project | Stars | Last Commit | Description | Language |",
        "|---------|-------|-------------|-------------|----------|",
    ]
    lines += [render_row(p) for p in cat["projects"]]
    return "\n".join(lines)


def render_index(data: dict) -> str:
    blocks = [render_category(c) for c in data["categories"]]
    return "\n\n---\n\n".join(blocks)


def build_readme(current: str, generated: str) -> str:
    if START not in current or END not in current:
        raise SystemExit(
            f"README.md is missing the AUTOGEN markers ({START} / {END})."
        )
    pre, rest = current.split(START, 1)
    _, post = rest.split(END, 1)
    return f"{pre}{START}\n\n{generated}\n\n{END}{post}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify README.md is in sync without writing (exit 1 on drift)",
    )
    args = parser.parse_args()

    data = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    generated = render_index(data)
    current = README.read_text(encoding="utf-8")
    updated = build_readme(current, generated)

    if args.check:
        if current != updated:
            print(
                "README.md is out of sync with data.yaml.\n"
                "Run: python3 scripts/generate_readme.py",
                file=sys.stderr,
            )
            return 1
        print("README.md is in sync with data.yaml.")
        return 0

    if current == updated:
        print("README.md already up to date.")
    else:
        README.write_text(updated, encoding="utf-8")
        print("README.md regenerated from data.yaml.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Enforce the awesome-open inclusion gate against live GitHub data.

For every repo listed in data.yaml, fetch stars, last push date, and archived
status from the GitHub API, then check them against the gate defined in
data.yaml (`gate.min_stars`, `gate.max_age_days`).

A repo PASSES when it EXCEEDS min_stars AND was pushed within max_age_days AND
is not archived. Anything else is a violation.

Usage:
    python3 scripts/check_gate.py                    # report only (exit 0)
    python3 scripts/check_gate.py --fail-on-violation # exit 1 if any violation

Auth: set GITHUB_TOKEN (or GH_TOKEN) to raise the API rate limit. In GitHub
Actions the built-in secrets.GITHUB_TOKEN is enough. Without a token the
public API allows only ~60 requests/hour.

Exit codes: 0 = all pass (or report-only) · 1 = gate violation(s) ·
            2 = could not fetch one or more repos (network / rate limit).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data.yaml"
API = "https://api.github.com/repos/{repo}"


def iter_repos(data: dict):
    for cat in data["categories"]:
        for project in cat["projects"]:
            yield project["repo"]


def fetch(repo: str) -> dict:
    req = urllib.request.Request(API.format(repo=repo))
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "awesome-open-gate-checker")
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def evaluate(repo: str, meta: dict, min_stars: int, max_age_days: int,
             activity_exempt_stars: int, now: dt.datetime):
    stars = meta.get("stargazers_count", 0)
    archived = meta.get("archived", False)
    pushed_at = meta.get("pushed_at")  # e.g. "2026-05-04T12:00:00Z"
    pushed = dt.datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    age_days = (now - pushed).days

    # Established projects (> activity_exempt_stars) skip the activity check.
    activity_exempt = stars > activity_exempt_stars

    reasons = []
    if stars <= min_stars:
        reasons.append(f"{stars} stars (needs > {min_stars})")
    if not activity_exempt and age_days > max_age_days:
        reasons.append(f"last push {age_days}d ago (needs <= {max_age_days}d)")
    if archived:
        reasons.append("archived")

    return {
        "repo": repo,
        "stars": stars,
        "age_days": age_days,
        "archived": archived,
        "passed": not reasons,
        "reasons": reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fail-on-violation", action="store_true",
                        help="exit 1 if any repo violates the gate")
    args = parser.parse_args()

    data = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    gate = data.get("gate", {})
    min_stars = int(gate.get("min_stars", 1000))
    max_age_days = int(gate.get("max_age_days", 90))
    activity_exempt_stars = int(gate.get("activity_exempt_stars", 5000))
    now = dt.datetime.now(dt.timezone.utc)

    print(f"Gate: > {activity_exempt_stars} stars, OR "
          f"(> {min_stars} stars AND pushed within {max_age_days} days)\n")

    results, fetch_errors = [], []
    for repo in iter_repos(data):
        try:
            meta = fetch(repo)
        except urllib.error.HTTPError as e:
            fetch_errors.append((repo, f"HTTP {e.code}"))
            continue
        except (urllib.error.URLError, TimeoutError) as e:
            fetch_errors.append((repo, str(e.reason if hasattr(e, "reason") else e)))
            continue
        results.append(evaluate(repo, meta, min_stars, max_age_days,
                                activity_exempt_stars, now))

    violations = [r for r in results if not r["passed"]]

    lines = ["| Repo | Stars | Last push | Verdict |", "|------|-------|-----------|---------|"]
    for r in sorted(results, key=lambda x: (x["passed"], x["repo"])):
        verdict = "✅ pass" if r["passed"] else "❌ " + "; ".join(r["reasons"])
        lines.append(f"| {r['repo']} | {r['stars']} | {r['age_days']}d ago | {verdict} |")
    table = "\n".join(lines)
    print(table)

    if fetch_errors:
        print("\nCould not fetch:")
        for repo, why in fetch_errors:
            print(f"  - {repo}: {why}")

    print(f"\n{len(results)} checked · {len(violations)} violation(s) · "
          f"{len(fetch_errors)} fetch error(s)")

    # Emit a report to the GitHub Actions step summary when available.
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write("## Inclusion gate audit\n\n" + table + "\n")
            if violations:
                fh.write(f"\n**{len(violations)} repo(s) below the gate — review needed.**\n")

    if fetch_errors:
        return 2
    if violations and args.fail_on_violation:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

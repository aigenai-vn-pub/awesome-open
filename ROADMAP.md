# 🤖 Automation Roadmap

> Planned design for automatically keeping the awesome-open index fresh and accurate.

> ⚠️ **Status: CONCEPT / ROADMAP — NOT YET IMPLEMENTED.**
> The index in [README.md](README.md) is **curated by hand today**. None of the scripts, GitHub Actions, data files, or agents described below exist yet. This document is a design target and an invitation to contributors — it is **not** a description of a running system. Everything below is written in the future/conditional tense on purpose.

---

## 📌 Concept & Vision

The goal is an index that stays **accurate and trustworthy without constant manual effort**. A future automation layer *would*:

- 🔄 Periodically check GitHub for new & updated AI / agentic projects
- 📊 Track open-source alternatives to commercial AI products
- 🎯 Suggest a category (Document Intelligence, Code Editors, Search, Chatbots, Frameworks, etc.)
- ⭐ Surface popularity/activity signals (stars, forks, last commit) — for review, not blind insertion
- 🚀 Regenerate the README tables from a single source of truth
- 📈 Flag stale or unmaintained entries for a human to confirm

Automation is a **means** to the end (a trustworthy, usable index) — not the product itself. A human stays in the loop for every addition.

---

## 🔧 Planned Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 GITHUB MONITOR (planned)                     │
├─────────────────────────────────────────────────────────────┤
│  1. DISCOVERY                                                │
│     ├─ Search: AI / agent / LLM open-source projects         │
│     └─ Monitor: trending repos                                │
│                                                              │
│  2. DATA COLLECTION                                          │
│     ├─ Fetch: repo metadata (stars, forks, last commit)      │
│     └─ Extract: description, topics, language, license       │
│                                                              │
│  3. CLASSIFICATION (human-reviewed)                          │
│     ├─ Suggest category & commercial alternative             │
│     └─ Check: AI is core (in scope) vs peripheral (out)      │
│                                                              │
│  4. SOURCE OF TRUTH                                          │
│     └─ Maintain: data.yaml (single structured source)        │
│                                                              │
│  5. GENERATION                                               │
│     └─ Regenerate README tables from data.yaml               │
└─────────────────────────────────────────────────────────────┘
```

The key architectural idea: **`data.yaml` is the single source of truth**, and `README.md` is *generated* from it. This is what prevents the manual-edit drift (stale stars, inconsistent totals) the project has today.

---

## 🚀 Planned Workflows

### Workflow 1 — Weekly data sync (planned)

```yaml
name: Weekly Data Sync
on:
  schedule:
    - cron: "0 0 * * 1"   # Every Monday 00:00 UTC

jobs:
  sync-data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Discover & collect
        run: python scripts/sync-github.py --query "ai agent open source" --min-stars 100 --output data/index.json
      - name: Classify (writes suggestions for human review)
        run: python scripts/classify.py --input data/index.json
      - name: Open PR for review
        run: |
          # Never push directly — open a PR so a human confirms scope & accuracy.
          echo "Create PR with proposed changes"
```

> Note: a real implementation should **open a pull request**, not commit straight to `main`. Every automated change gets human review before it lands — that is what keeps the index trustworthy.

### Workflow 2 — Staleness check (planned)

Periodically flag entries whose last commit is old, or whose repo has been archived/renamed/deleted, and open an issue listing them for a maintainer to confirm removal or update.

### Workflow 3 — Freshness of badges (already live)

Star counts and last-commit dates in the README already use **live shields.io badges**, so they never go stale — no automation required for those.

---

## 📂 Planned File Structure

```
awesome-open/
├── README.md              # Generated index (source of truth: data.yaml)
├── ROADMAP.md             # This file — automation design
├── LICENSE
├── data.yaml              # (planned) single structured source of truth
└── scripts/               # (planned) automation
    ├── sync-github.py      # Fetch metadata from GitHub
    ├── classify.py         # Suggest category / scope check
    └── generate-readme.py  # Render README tables from data.yaml
```

---

## 🧬 Planned Data Model

Each project *would* be stored in `data.yaml` roughly like this (illustrative — not live data):

```yaml
- repo: MODSetter/SurfSense
  category: document-intelligence
  alternative_to: [Google NotebookLM]
  language: Python
  license: Apache-2.0
  description: Privacy-focused alternative to NotebookLM for teams with no data limits
  # stars / forks / last_commit are NOT stored here — they are rendered as
  # live shields.io badges so they never go stale.
```

Deliberately **not** stored: star/fork counts and totals. Caching those is exactly how an index drifts out of date. Live badges are the source of truth for popularity signals.

---

## 🛠️ Reference: generation script (design sketch, not implemented)

A README generator would read `data.yaml`, render each category table (injecting live badges), and replace content between markers so it never clobbers hand-written prose:

```python
#!/usr/bin/env python3
"""Design sketch — render README tables from data.yaml. NOT yet implemented."""
import yaml

STARS = "https://img.shields.io/github/stars/{repo}?style=flat-square"
LAST  = "https://img.shields.io/github/last-commit/{repo}?style=flat-square"

def row(p):
    repo, url = p["repo"], f"https://github.com/{p['repo']}"
    stars = f"[![Stars]({STARS.format(repo=repo)})]({url})"
    last  = f"[![Last commit]({LAST.format(repo=repo)})]({url})"
    return f"| [{repo}]({url}) | {stars} | {last} | {p['description']} | {p['language']} |"

def render(data):
    # group by category, emit a table per category, insert between
    # <!-- AUTOGEN:start --> / <!-- AUTOGEN:end --> markers in README.md
    ...
```

> Prefer marker-based injection (`<!-- AUTOGEN:start -->` … `<!-- AUTOGEN:end -->`) over regex-replacing whole sections — it is far less fragile.

---

## 🚦 Roadmap

### Phase 1 — Foundation ✅ (current)
- [x] Manual curation of AI-focused projects
- [x] README with category organization & live star/last-commit badges
- [x] Commercial → open-source mapping
- [x] LICENSE
- [x] Honest scope (AI-core only) and trust conventions

### Phase 2 — Single source of truth 🔄 (next)
- [ ] Define `data.yaml` schema
- [ ] Migrate current README entries into `data.yaml`
- [ ] `generate-readme.py` to render tables from `data.yaml`
- [ ] CI check that README matches generated output

### Phase 3 — Assisted discovery 📅 (later)
- [ ] `sync-github.py` to propose new candidates
- [ ] Scope/quality classifier (AI-core check)
- [ ] Weekly PR of suggestions for human review
- [ ] Staleness / archived-repo detection

### Phase 4 — Comparisons 🌐 (later)
- [ ] Full per-category feature matrices (beyond the v1 positioning table)
- [ ] Migration notes between commercial products and alternatives

---

## 🤝 Contributing to Automation

The most valuable next step is **Phase 2** — a `data.yaml` source of truth plus a generator. If you'd like to help:

1. Fork the repo and create a feature branch
2. Propose a `data.yaml` schema (or improve the sketch above)
3. Open a PR — automation changes should always land via reviewed PRs, never direct pushes

---

## 📄 License

Released under the [MIT License](LICENSE).

---

*Status: concept / roadmap — not yet implemented.*
*Last updated: July 1, 2026*

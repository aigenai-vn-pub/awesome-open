# 📊 Workflow Implementation Guide

> How to use Agent.md to automate awesome-open index updates with real data

**Problem:** Document Intelligence category (NotebookLM alternatives) has accurate stars but they're static in README.md  
**Solution:** Implement automation workflows to keep data fresh and identify emerging projects

---

## 🎯 Current Status: NotebookLM Alternatives

### Real Data (as of June 12, 2026)

| Project | Stars | Forks | Status | Activity |
|---------|-------|-------|--------|----------|
| [MODSetter/SurfSense](https://github.com/MODSetter/SurfSense) | **14.4k** ⭐ | 1.4k | 🟢 Active | 2h ago |
| [souzatharsis/podcastfy](https://github.com/souzatharsis/podcastfy) | **6.3k** | 738 | 🟢 Active | May 4 |
| [run-llama/notebookllama](https://github.com/run-llama/notebookllama) | **1.9k** | 245 | 🟡 Moderate | Mar 2 |
| [theaiautomators/insights-lm-public](https://github.com/theaiautomators/insights-lm-public) | **545** | 245 | 🟡 Moderate | Jan 16 |
| [smallnest/notex](https://github.com/smallnest/notex) | **215** | - | 🔴 Low | - |
| [theaiautomators/insights-lm-local-package](https://github.com/theaiautomators/insights-lm-local-package) | **212** | - | 🔴 Low | - |
| [open-biz/OpenBookLM](https://github.com/open-biz/OpenBookLM) | **119** | - | 🔴 Low | - |

**Total projects found:** 36 NotebookLM alternatives (varying from 14.4k to 0 stars)

---

## 🔄 Workflow 1: Weekly Data Sync Automation

### Trigger: Every Monday 00:00 UTC

### Steps:

#### **Step 1: Discover & Collect** (GitHub Actions Job)
```yaml
name: Weekly Data Sync
on:
  schedule:
    - cron: "0 0 * * 1"  # Every Monday at midnight

jobs:
  sync-data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Discovery Script
        run: |
          python scripts/sync-github.py \
            --query "notebooklm alternative open" \
            --min-stars 100 \
            --output data/notebooklm.json
      
      - name: Validate & Process
        run: |
          python scripts/classify.py \
            --input data/notebooklm.json \
            --category document-intelligence
      
      - name: Commit & Push
        run: |
          git config user.name "AwesomeOpenBot"
          git config user.email "bot@awesome-open.dev"
          git add data/
          git commit -m "chore: Weekly data sync - NotebookLM alternatives"
          git push
```

#### **Step 2: Sync Script** (`scripts/sync-github.py`)
```python
#!/usr/bin/env python3
"""GitHub data synchronization script"""

import json
import os
from datetime import datetime
from github import Github

class DataSyncAgent:
    def __init__(self):
        self.gh = Github(os.getenv('GITHUB_TOKEN'))
        self.timestamp = datetime.now().isoformat()
    
    def search_repositories(self, query, min_stars=100):
        """Search GitHub for repositories"""
        print(f"🔍 Searching: {query}")
        results = []
        
        try:
            repos = self.gh.search_repositories(
                query=f"{query} stars:>{min_stars}",
                sort="stars",
                order="desc"
            )
            
            for repo in repos:
                project = {
                    'name': repo.full_name,
                    'url': repo.html_url,
                    'stars': repo.stargazers_count,
                    'forks': repo.forks_count,
                    'language': repo.language,
                    'license': repo.license.name if repo.license else 'Unknown',
                    'description': repo.description,
                    'last_commit': repo.pushed_at.isoformat(),
                    'created_at': repo.created_at.isoformat(),
                    'contributors': repo.get_contributors().totalCount,
                    'topics': repo.topics,
                }
                results.append(project)
                print(f"  ✓ {repo.full_name}: {repo.stargazers_count}⭐")
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        return results
    
    def save_data(self, data, filepath):
        """Save data to JSON file"""
        with open(filepath, 'w') as f:
            json.dump({
                'timestamp': self.timestamp,
                'projects': data,
                'total': len(data)
            }, f, indent=2)
        print(f"✅ Saved {len(data)} projects to {filepath}")

# Usage
if __name__ == "__main__":
    agent = DataSyncAgent()
    
    # Search for NotebookLM alternatives
    notebooklm_projects = agent.search_repositories(
        "notebooklm alternative open source",
        min_stars=100
    )
    
    # Save results
    agent.save_data(notebooklm_projects, "data/notebooklm.json")
```

#### **Step 3: Classification** (`scripts/classify.py`)
```python
#!/usr/bin/env python3
"""Classify projects into categories"""

import json
import argparse

class ProjectClassifier:
    def classify_project(self, project):
        """Classify a project based on metadata"""
        description = (project.get('description') or '').lower()
        name = project.get('name', '').lower()
        
        # Analyze keywords
        keywords = {
            'document-intelligence': ['notebook', 'document', 'podcast', 'audio'],
            'maturity_indicators': {
                'mature': ['10k+', '5k+', 'production'],
                'growing': ['1k+', '500+'],
                'early': ['<500', '<100']
            }
        }
        
        # Calculate maturity score
        stars = project.get('stars', 0)
        forks = project.get('forks', 0)
        contributors = project.get('contributors', 0)
        
        maturity_score = min(1.0, (
            (stars / 10000) * 0.5 +
            (forks / 1000) * 0.3 +
            (contributors / 100) * 0.2
        ))
        
        # Determine status
        if stars > 5000:
            status = 'established'
            health = '🟢'
        elif stars > 1000:
            status = 'growing'
            health = '🟡'
        else:
            status = 'emerging'
            health = '🔴'
        
        return {
            'category': 'document-intelligence',
            'status': status,
            'health': health,
            'maturity_score': round(maturity_score, 2),
            'trending': stars > 5000 or (forks > 200 and stars > 500)
        }
    
    def process_projects(self, input_file):
        """Process and classify all projects"""
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        classified = []
        for project in data['projects']:
            classification = self.classify_project(project)
            project.update(classification)
            classified.append(project)
        
        # Sort by stars
        classified.sort(key=lambda x: x['stars'], reverse=True)
        
        return {
            'timestamp': data['timestamp'],
            'total': len(classified),
            'projects': classified
        }

# Usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--category', default='document-intelligence')
    args = parser.parse_args()
    
    classifier = ProjectClassifier()
    result = classifier.process_projects(args.input)
    
    print(f"\n📊 Classification Results:")
    print(f"  Total: {result['total']} projects")
    print(f"  Established: {sum(1 for p in result['projects'] if p['status'] == 'established')}")
    print(f"  Growing: {sum(1 for p in result['projects'] if p['status'] == 'growing')}")
    print(f"  Emerging: {sum(1 for p in result['projects'] if p['status'] == 'emerging')}")
    
    # Save classified data
    with open(args.input, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"✅ Saved to {args.input}")
```

---

## 🚀 Workflow 2: Auto-Generate README Tables

### After Data Sync Completes

```python
#!/usr/bin/env python3
"""Generate README markdown tables from data"""

import json
import os

class ReadmeGenerator:
    def __init__(self):
        self.data_dir = "data"
    
    def load_category_data(self, category):
        """Load data for a category"""
        filepath = f"{self.data_dir}/{category}.json"
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def generate_table(self, projects, category_name):
        """Generate markdown table"""
        lines = [
            f"## 📚 {category_name}\n",
            "| Project | Stars | Forks | Status | Last Update |",
            "|---------|-------|-------|--------|-------------|"
        ]
        
        for p in projects:
            stars_display = f"**{p['stars']}**" if p['stars'] > 5000 else str(p['stars'])
            status = p.get('health', '🔴') + " " + p.get('status', 'unknown')
            
            line = (
                f"| [{p['name']}]({p['url']}) | {stars_display} ⭐ | "
                f"{p.get('forks', 0)} | {status} | {p['last_commit'][:10]} |"
            )
            lines.append(line)
        
        return "\n".join(lines) + "\n"
    
    def update_readme(self):
        """Update main README.md with latest data"""
        data = self.load_category_data('notebooklm')
        table = self.generate_table(data['projects'], "Document Intelligence")
        
        # Read current README
        with open('README.md', 'r') as f:
            readme = f.read()
        
        # Replace section
        import re
        pattern = r'(### 📚 \*\*Document Intelligence.*?\n)(.*?)(\n### )'
        updated = re.sub(
            pattern,
            r'\1' + table + r'\3',
            readme,
            flags=re.DOTALL
        )
        
        # Write back
        with open('README.md', 'w') as f:
            f.write(updated)
        
        print("✅ Updated README.md")

# Run
if __name__ == "__main__":
    gen = ReadmeGenerator()
    gen.update_readme()
```

---

## 📊 Workflow 3: Track Trending & Growth

### Daily Scheduled Task

```python
#!/usr/bin/env python3
"""Track trending projects and growth metrics"""

import json
import os
from datetime import datetime, timedelta

class TrendingAnalyzer:
    def __init__(self):
        self.data_dir = "data"
        self.history_dir = "trending/history"
        os.makedirs(self.history_dir, exist_ok=True)
    
    def load_current_data(self, category):
        """Load current snapshot"""
        with open(f"{self.data_dir}/{category}.json", 'r') as f:
            return json.load(f)
    
    def load_previous_data(self, category, days_ago=7):
        """Load previous week's snapshot"""
        filepath = f"{self.history_dir}/{category}-{days_ago}d-ago.json"
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return None
    
    def calculate_growth(self, current, previous):
        """Calculate stars gained"""
        if not previous:
            return 0
        
        current_stars = {p['name']: p['stars'] for p in current['projects']}
        prev_stars = {p['name']: p['stars'] for p in previous['projects']}
        
        growth = {}
        for name, stars in current_stars.items():
            if name in prev_stars:
                gained = stars - prev_stars[name]
                if gained > 0:
                    growth[name] = gained
        
        return growth
    
    def generate_trending_report(self, category):
        """Generate trending report"""
        current = self.load_current_data(category)
        previous = self.load_previous_data(category)
        growth = self.calculate_growth(current['projects'], previous)
        
        # Top gainers this week
        top_gainers = sorted(growth.items(), key=lambda x: x[1], reverse=True)[:5]
        
        report = f"""# 📈 Weekly Trending Report - {category.replace('-', ' ').title()}

## Top Gainers (This Week)

| Project | Stars Gained | Total Stars |
|---------|--------------|------------|"""
        
        for name, gained in top_gainers:
            project = next(p for p in current['projects'] if p['name'] == name)
            report += f"\n| {name} | +{gained} ⭐ | {project['stars']} |"
        
        # Save report
        today = datetime.now().strftime('%Y-%m-%d')
        report_file = f"trending/{today}-{category}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"✅ Generated trending report: {report_file}")
        
        # Archive current data
        archive_file = f"{self.history_dir}/{category}-snapshot.json"
        with open(archive_file, 'w') as f:
            json.dump(current, f)

# Run
if __name__ == "__main__":
    analyzer = TrendingAnalyzer()
    analyzer.generate_trending_report('notebooklm')
```

---

## 📁 Data Structure Example

### `data/notebooklm.json` (Auto-Generated Weekly)
```json
{
  "timestamp": "2026-06-12T00:00:00",
  "total": 7,
  "projects": [
    {
      "name": "MODSetter/SurfSense",
      "url": "https://github.com/MODSetter/SurfSense",
      "stars": 14438,
      "forks": 1374,
      "language": "Python",
      "license": "Apache License 2.0",
      "description": "An open source, privacy focused alternative to NotebookLM...",
      "last_commit": "2026-06-12T00:02:13Z",
      "created_at": "2024-07-30T00:00:00Z",
      "contributors": 45,
      "topics": ["agent", "ai", "rag", "notebooklm"],
      "category": "document-intelligence",
      "status": "established",
      "health": "🟢",
      "maturity_score": 0.92,
      "trending": true
    },
    {
      "name": "souzatharsis/podcastfy",
      "url": "https://github.com/souzatharsis/podcastfy",
      "stars": 6361,
      "forks": 738,
      "status": "established",
      "maturity_score": 0.78,
      "trending": true
    }
  ]
}
```

---

## ✅ Expected Outcomes

### After Week 1:
- ✅ Data file created with 36 NotebookLM projects
- ✅ README tables auto-generated
- ✅ Top projects identified (SurfSense: 14.4k, podcastfy: 6.3k)
- ✅ Trending tracked

### After Month 1:
- ✅ Growth patterns identified
- ✅ Emerging projects flagged
- ✅ Category maturity assessed
- ✅ Quality trends documented

### After Quarter 1:
- ✅ 150+ projects tracked across all categories
- ✅ Automated update pipeline fully operational
- ✅ Community contributions tracked
- ✅ Monthly reports generated

---

## 🔧 Implementation Checklist

- [ ] Create `.github/workflows/weekly-sync.yml`
- [ ] Create `scripts/sync-github.py`
- [ ] Create `scripts/classify.py`
- [ ] Create `scripts/generate-readme.py`
- [ ] Create `scripts/analyze-trends.py`
- [ ] Setup `data/` directory structure
- [ ] Add GitHub token to secrets
- [ ] Test workflow manually
- [ ] Enable scheduled triggers
- [ ] Document in CONTRIBUTING.md

---

## 🎯 Next Steps

1. **This Week:** Set up GitHub Actions workflow
2. **Next Week:** First automated sync & validation
3. **Month 1:** Daily trending reports
4. **Month 2:** Category deep-dives
5. **Month 3:** ML-based recommendations

---

*Document Version: 1.0*
*Last Updated: June 12, 2026*

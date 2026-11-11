#!/usr/bin/env python3
"""Pull the most-starred GitHub repositories for a list of topics as catalog links.

Uses the public search API (no token, 10 requests a minute), so it sleeps
between queries. Writes skill/oneskill/links/repos-<group>.json, one entry per
repository with its real description and star count. These are "resource"
links: Claude reads the README when routed to one.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINKS = os.path.join(REPO_ROOT, "skill", "oneskill", "links")
PER_TOPIC = 30

# category -> search queries (GitHub topics or free text)
GROUPS = {
    "frontend": ["topic:frontend topic:react", "topic:ui-components", "topic:design-system", "topic:tailwindcss", "topic:nextjs", "topic:css topic:animation", "topic:vue", "topic:svelte", "topic:web-components"],
    "design": ["topic:figma", "topic:icons", "topic:fonts topic:typography", "topic:ui-design", "topic:design-tools", "topic:color-palette", "topic:illustrations"],
    "video": ["topic:video-editing", "topic:ffmpeg", "topic:video-processing", "topic:subtitles", "topic:screen-recording"],
    "motion": ["topic:motion-graphics", "topic:animation-library", "topic:lottie", "topic:3d-animation", "topic:gsap"],
    "ai": ["topic:llm topic:agents", "topic:mcp-server", "topic:rag", "topic:prompt-engineering", "topic:ai-agents", "topic:claude-code", "topic:langchain", "topic:diffusion-models"],
    "coding": ["topic:developer-tools", "topic:code-quality", "topic:testing-tools", "topic:api-design", "topic:cli", "topic:best-practices", "topic:clean-code", "topic:system-design"],
    "backend": ["topic:backend topic:framework", "topic:database", "topic:graphql", "topic:authentication", "topic:microservices", "topic:serverless"],
    "mobile": ["topic:react-native", "topic:flutter", "topic:ios topic:swift", "topic:android topic:kotlin"],
    "devops": ["topic:devops", "topic:docker", "topic:kubernetes", "topic:ci-cd", "topic:infrastructure-as-code", "topic:monitoring"],
    "data": ["topic:data-science", "topic:data-visualization", "topic:charts", "topic:pandas", "topic:sql", "topic:data-engineering", "topic:jupyter"],
    "security": ["topic:pentesting", "topic:security-tools", "topic:bug-bounty", "topic:owasp", "topic:osint", "topic:malware-analysis", "topic:ctf"],
    "careers": ["topic:resume", "topic:job-search", "topic:interview-preparation", "topic:cv", "topic:portfolio-website", "topic:coding-interviews"],
    "outreach": ["topic:cold-email", "topic:linkedin", "topic:lead-generation", "topic:email-marketing", "topic:sales-automation"],
    "marketing": ["topic:seo", "topic:marketing-tools", "topic:growth-hacking", "topic:analytics", "topic:landing-page", "topic:social-media-automation"],
    "writing": ["topic:writing-tools", "topic:markdown-editor", "topic:copywriting", "topic:blog", "topic:documentation-tool", "topic:grammar"],
    "productivity": ["topic:productivity", "topic:note-taking", "topic:todo", "topic:automation", "topic:workflow-automation", "topic:knowledge-management"],
    "business": ["topic:startup", "topic:saas-boilerplate", "topic:invoice", "topic:crm", "topic:ecommerce", "topic:pricing"],
    "documents": ["topic:pdf", "topic:docx", "topic:spreadsheet", "topic:latex", "topic:presentation", "topic:ocr"],
    "media": ["topic:image-processing", "topic:audio-processing", "topic:text-to-speech", "topic:podcast", "topic:photography", "topic:music-generation"],
    "education": ["topic:awesome-list topic:learning", "topic:tutorial", "topic:roadmap", "topic:interview-questions", "topic:courses", "topic:books"],
    "games": ["topic:game-development", "topic:game-engine", "topic:unity", "topic:godot", "topic:pixel-art"],
    "research": ["topic:research-tool", "topic:papers", "topic:bioinformatics", "topic:scientific-computing", "topic:academic"],
    "finance": ["topic:finance", "topic:trading-bot", "topic:budgeting", "topic:accounting", "topic:fintech"],
}


def search(query):
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
        {"q": query + " stars:>50 archived:false", "sort": "stars", "order": "desc", "per_page": PER_TOPIC})
    req = urllib.request.Request(url, headers={"User-Agent": "oneskill-ingest", "Accept": "application/vnd.github+json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)["items"]
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429):
                time.sleep(65)
                continue
            raise
    return []


def slug(text):
    import re
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def main(groups):
    for group in groups:
        entries, seen = [], set()
        for q in GROUPS[group]:
            topic_words = [w.split(":", 1)[1] for w in q.split() if w.startswith("topic:")]
            for item in search(q):
                full = item["full_name"]
                if full.lower() in seen:
                    continue
                seen.add(full.lower())
                entries.append({
                    "id": slug(item["name"]),
                    "kind": "resource",
                    "category": group,
                    "description": (item.get("description") or "").strip()[:300] or ("GitHub repository %s." % full),
                    "tags": sorted(set(topic_words + [t for t in item.get("topics", [])[:10]])),
                    "repo": full,
                    "branch": item["default_branch"],
                    "path": "README.md",
                    "stars": item["stargazers_count"],
                    "license": (item.get("license") or {}).get("spdx_id") or "unspecified",
                    "language": item.get("language") or "",
                })
            print("%s %-40s %d so far" % (group, q, len(entries)), file=sys.stderr)
            time.sleep(6.5)
        # unique ids inside the file; build.py resolves clashes across files
        ids = set()
        for e in entries:
            base, n = e["id"], 2
            while e["id"] in ids:
                e["id"] = "%s-%d" % (base, n)
                n += 1
            ids.add(e["id"])
        with open(os.path.join(LINKS, "repos-%s.json" % group), "w", encoding="utf-8") as fh:
            json.dump(entries, fh, indent=1)
        print("wrote repos-%s.json (%d)" % (group, len(entries)), file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:] or list(GROUPS))

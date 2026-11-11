#!/usr/bin/env python3
"""Turn "awesome" lists of agent skills into catalog links.

Reads Markdown lists (one "- [name](github url) - description" per line under
section headings), works out where each SKILL.md lives, checks that it really
exists on GitHub, and writes skill/oneskill/links/skills-community.json.
Entries whose SKILL.md cannot be found are kept as "resource" links to the repo.
"""
import json
import os
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO_ROOT, "skill", "oneskill", "links", "skills-community.json")
# "- [name](url) - desc", "- **[name](url)** - desc" and "| [name](url) | desc |"
LINE = re.compile(r"^\s*(?:[-*]\s+|\|\s*)\*{0,2}\[([^\]]+)\]\((https://github\.com/[^)\s]+)\)\*{0,2}\s*(?:\||[-–—:])?\s*(.*?)\s*\|?\s*$")
URL = re.compile(r"https://github\.com/([^/\s]+)/([^/\s#?]+)(?:/(?:tree|blob)/([^/\s]+)/([^\s#?]*))?")

# section heading words -> catalog category
CATEGORY_RULES = [
    ("security", ["secur", "pentest", "web testing"]),
    ("documents", ["document"]),
    ("data", ["data", "analysis", "analytics"]),
    ("research", ["scientific", "research", "science", "health", "life sciences"]),
    ("writing", ["writing", "communication"]),
    ("education", ["learning", "knowledge", "education"]),
    ("media", ["media", "creative", "content", "video", "audio", "image"]),
    ("productivity", ["productivity", "organization", "collaboration", "project management", "utility", "automation"]),
    ("business", ["business", "marketing", "sales", "finance"]),
    ("coding", ["development", "code", "engineering", "programming", "devops", "testing", "official", "teams", "team"]),
    ("ai", ["ai", "llm", "agent", "prompt", "mcp"]),
    ("design", ["design", "ui", "ux", "frontend"]),
    ("collections", ["collection"]),
]
SKIP_SECTIONS = ["table of contents", "contribut", "contact", "license", "related lists", "articles", "blog", "how to", "what are", "skill structure", "template", "compatible", "getting started", "quickstart", "install the", "run setup", "restart", "join the", "official documentation", "inspiration"]


# words in a name or description that place an entry when its section does not
TEXT_RULES = [
    ("video", ["video", "ffmpeg", "remotion", "capcut", "youtube", "subtitle", "caption"]),
    ("motion", ["motion", "animation", "animate", "lottie", "gsap"]),
    ("security", ["security", "pentest", "vulnerab", "owasp", "exploit", "malware", "threat", "secrets"]),
    ("careers", ["resume", "cv ", "cover letter", "job search", "job application", "interview"]),
    ("outreach", ["outreach", "cold email", "linkedin", "prospect", "lead gen", "sales email"]),
    ("marketing", ["seo", "marketing", "landing page", "ads ", "campaign", "growth", "copywriting", "brand"]),
    ("design", ["design", "figma", "ui ", "ux", "typography", "color", "colour", "icon", "logo", "poster"]),
    ("frontend", ["react", "next.js", "nextjs", "vue", "svelte", "tailwind", "css", "frontend", "front-end", "component"]),
    ("data", ["data", "sql", "pandas", "spreadsheet", "excel", "chart", "analytics", "dashboard"]),
    ("documents", ["pdf", "docx", "word document", "pptx", "powerpoint", "slides", "latex"]),
    ("ai", ["llm", "agent", "prompt", "mcp", "rag", "model", "claude", "gpt", "embedding"]),
    ("devops", ["docker", "kubernetes", "k8s", "deploy", "ci/cd", "terraform", "aws", "cloud", "monitor"]),
    ("mobile", ["ios", "android", "swift", "kotlin", "flutter", "react native", "expo"]),
    ("research", ["research", "paper", "scientific", "bioinformatics", "clinical", "protein", "genom"]),
    ("writing", ["writing", "blog", "newsletter", "essay", "editing", "grammar", "story"]),
    ("productivity", ["notes", "todo", "calendar", "email", "meeting", "productivity", "workflow", "automation"]),
    ("business", ["business", "startup", "pitch", "pricing", "invoice", "finance", "crm", "customer"]),
    ("education", ["learn", "tutorial", "course", "teach", "study"]),
    ("games", ["game", "unity", "godot", "unreal"]),
    ("coding", ["code", "test", "debug", "refactor", "api", "git", "typescript", "python", "rust", "go ", "lint", "build"]),
]


def category_for(section, text=""):
    s = section.lower()
    for cat, words in CATEGORY_RULES:
        if any(w in s for w in words):
            return cat
    t = " " + text.lower() + " "
    for cat, words in TEXT_RULES:
        if any(w in t for w in words):
            return cat
    return "tools"


def slug(text):
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text[:60] or "skill"


def parse(path):
    entries, section = [], ""
    publisher_list = "VoltAgent" in path or "kodustech" in path
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                section = line.strip("# \n")
                continue
            if any(k in section.lower() for k in SKIP_SECTIONS):
                continue
            m = LINE.match(line)
            if not m:
                continue
            name, url, desc = m.group(1).strip(), m.group(2), m.group(3).strip()
            desc = re.sub(r"\*By \[.*?\]\(.*?\)\*", "", desc)  # drop "*By [@x](...)*"
            desc = re.sub(r"^by \[[^\]]+\]\([^)]+\)\s*[-–—:]?\s*", "", desc, flags=re.I)  # "by [author](...) - desc"
            desc = re.sub(r"\s*\|.*$", "", desc)  # trailing table cells
            desc = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", desc)  # unlink
            desc = re.sub(r"[`*_]", "", desc).strip(" .-") + "."
            u = URL.match(url)
            if not u:
                continue
            owner, repo, branch, sub = u.groups()
            if repo.endswith(".git"):
                repo = repo[:-4]
            if owner.lower() in ("topics", "search", "orgs", "settings", "features", "sponsors"):
                continue
            entries.append({"name": name, "repo": "%s/%s" % (owner, repo), "branch": branch, "sub": (sub or "").strip("/"),
                            "description": desc[:300], "section": "" if publisher_list else section, "list": os.path.basename(path)[:-3]})
    return entries


def exists(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "oneskill-ingest"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception:
        return False


def resolve(entry):
    """Find the SKILL.md for an entry. Returns (branch, path) or (branch, None)."""
    repo, branch, sub = entry["repo"], entry["branch"], entry["sub"]
    branches = [branch] if branch else ["main", "master"]
    candidates = []
    if sub.endswith("SKILL.md"):
        candidates.append(sub)
    elif sub:
        candidates.append(sub + "/SKILL.md")
    else:
        candidates += ["SKILL.md", "skills/%s/SKILL.md" % entry["repo"].split("/")[1], ".claude/skills/%s/SKILL.md" % entry["repo"].split("/")[1]]
    for b in branches:
        for c in candidates:
            if exists("https://raw.githubusercontent.com/%s/%s/%s" % (repo, b, c)):
                return b, c
    for b in branches:
        if exists("https://raw.githubusercontent.com/%s/%s/README.md" % (repo, b)):
            return b, None
    return None, None


def main(paths):
    raw = []
    for p in paths:
        raw.extend(parse(p))
    seen, entries = set(), []
    for e in raw:
        key = (e["repo"].lower(), e["sub"].lower())
        if key in seen:
            continue
        seen.add(key)
        entries.append(e)
    print("%d list lines, %d unique links; checking GitHub..." % (len(raw), len(entries)), file=sys.stderr)
    with ThreadPoolExecutor(max_workers=24) as pool:
        results = list(pool.map(resolve, entries))
    out, ids = [], set()
    for e, (branch, path) in zip(entries, results):
        if branch is None:
            continue
        base = slug(e["sub"].split("/")[-1] if e["sub"] else e["name"])
        sid = base
        n = 2
        while sid in ids:
            sid = "%s-%d" % (base, n)
            n += 1
        ids.add(sid)
        words = re.findall(r"[a-z0-9]+", (e["name"] + " " + e["sub"].replace("/", " ")).lower())
        out.append({
            "id": sid,
            "kind": "skill" if path else "resource",
            "category": category_for(e["section"], e["name"] + " " + e["sub"] + " " + e["description"]),
            "description": e["description"],
            "tags": sorted(set(w for w in words if len(w) > 2))[:12],
            "repo": e["repo"],
            "branch": branch,
            "path": path or "README.md",
            "section": e["section"],
            "list": e["list"],
        })
    out.sort(key=lambda x: (x["category"], x["id"]))
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    skills = len([o for o in out if o["kind"] == "skill"])
    print("%d entries written (%d with a SKILL.md, %d resources) -> %s" % (len(out), skills, len(out) - skills, os.path.relpath(OUT, REPO_ROOT)), file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])

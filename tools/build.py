#!/usr/bin/env python3
"""Build the registry from the skills folder, then package the skill.

Reads   skill/oneskill/skills/<category>/<id>/SKILL.md  and  registry/ratings.json
Writes  skill/oneskill/registry/index.json              (what route.py searches)
        skill/oneskill/registry/categories*.md          (no-script fallback)
        site/registry.js                                (what the website shows)
        dist/oneskill.zip                               (what users upload)

Run it after adding a skill or changing ratings:  python3 tools/build.py
"""
import json
import os
import re
import shutil
import sys
import zipfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_ROOT = os.path.join(REPO_ROOT, "skill", "oneskill")
SKILLS_DIR = os.path.join(SKILL_ROOT, "skills")
LINKS_DIR = os.path.join(SKILL_ROOT, "links")
RATINGS = os.path.join(REPO_ROOT, "registry", "ratings.json")
CONFIG = os.path.join(REPO_ROOT, "registry", "config.json")

sys.path.insert(0, os.path.join(SKILL_ROOT, "scripts"))
from route import quality  # noqa: E402  (one definition of the rating formula)

REQUIRED = ("name", "description", "tags")
LINK_REQUIRED = ("id", "description", "repo", "path")
ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def frontmatter(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise ValueError("missing frontmatter")
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta


def collect():
    with open(RATINGS, encoding="utf-8") as fh:
        ratings = json.load(fh)
    skills, errors = [], []
    for category in sorted(os.listdir(SKILLS_DIR)):
        cat_dir = os.path.join(SKILLS_DIR, category)
        if not os.path.isdir(cat_dir):
            continue
        for skill_id in sorted(os.listdir(cat_dir)):
            path = os.path.join(cat_dir, skill_id, "SKILL.md")
            if not os.path.isfile(path):
                continue
            where = "%s/%s" % (category, skill_id)
            try:
                meta = frontmatter(path)
            except ValueError as exc:
                errors.append("%s: %s" % (where, exc))
                continue
            missing = [k for k in REQUIRED if not meta.get(k)]
            if missing:
                errors.append("%s: missing %s" % (where, ", ".join(missing)))
                continue
            if meta["name"] != skill_id or not ID_RE.match(skill_id):
                errors.append("%s: name must equal the folder name, lowercase-with-hyphens" % where)
                continue
            if len(meta["description"]) > 300:
                errors.append("%s: description over 300 characters" % where)
                continue
            rating = ratings.get(skill_id, {})
            skills.append(
                {
                    "id": skill_id,
                    "name": skill_id,
                    "category": category,
                    "description": meta["description"],
                    "tags": [t.strip() for t in meta["tags"].split(",") if t.strip()],
                    "author": meta.get("author", ""),
                    "license": meta.get("license", ""),
                    "kind": "skill",
                    "source": "local",
                    "stars": 0,
                    "path": "skills/%s/%s/SKILL.md" % (category, skill_id),
                    "rating": {"votes": rating.get("votes", 0), "sum": rating.get("sum", 0)},
                }
            )
    ids = [s["id"] for s in skills]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append("%s: id used in more than one category" % dup)
    linked = collect_links(ratings, errors)
    taken = set(ids)
    for s in linked:  # a link may not shadow a built-in skill's id
        if s["id"] in taken:
            s["id"] = s["name"] = s["id"] + "-gh"
        taken.add(s["id"])
    skills.extend(linked)
    return skills, errors


def collect_links(ratings, errors):
    """Catalog entries that live in other GitHub repositories.

    links/*.json each hold a list of entries: where the file is (repo, branch,
    path), what it is (kind "skill" = a SKILL.md Claude can follow, "resource"
    = a repository whose README is the guide), plus name, description, tags
    and stars. Claude fetches the file at routing time, or hands over the link.
    """
    skills, ids, seen = [], set(), set()
    if not os.path.isdir(LINKS_DIR):
        return skills
    for name in sorted(os.listdir(LINKS_DIR)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(LINKS_DIR, name), encoding="utf-8") as fh:
            entries = json.load(fh)
        for e in entries:
            where = "%s:%s" % (name, e.get("id"))
            missing = [k for k in LINK_REQUIRED if not e.get(k)]
            if missing:
                errors.append("%s: missing %s" % (where, ", ".join(missing)))
                continue
            skill_id = e["id"]
            key = (e["repo"].lower(), e["path"].lower())
            if key in seen:  # the same file reached from two lists: keep the first (curated files sort first)
                continue
            seen.add(key)
            if not ID_RE.match(skill_id):
                errors.append("%s: id must be lowercase-with-hyphens" % where)
                continue
            base, n = skill_id, 2
            while skill_id in ids:  # same name in two lists: keep both, suffix the later one
                skill_id = "%s-%d" % (base, n)
                n += 1
            ids.add(skill_id)
            branch = e.get("branch", "main")
            rating = ratings.get(skill_id, {})
            skills.append(
                {
                    "id": skill_id,
                    "name": skill_id,
                    "kind": e.get("kind", "skill"),
                    "category": e.get("category", "tools"),
                    "description": e["description"][:300],
                    "tags": [t for t in e.get("tags", []) if t],
                    "author": e["repo"].split("/")[0],
                    "license": e.get("license", "unspecified"),
                    "source": "github",
                    "repo": e["repo"],
                    "stars": int(e.get("stars", 0) or 0),
                    "url": "https://github.com/%s/blob/%s/%s" % (e["repo"], branch, e["path"]),
                    "raw": "https://raw.githubusercontent.com/%s/%s/%s" % (e["repo"], branch, e["path"]),
                    "path": "links/%s#%s" % (name, skill_id),
                    "rating": {"votes": rating.get("votes", 0), "sum": rating.get("sum", 0)},
                }
            )
    return skills


def write_fallback(skills):
    reg = os.path.join(SKILL_ROOT, "registry")
    cat_dir = os.path.join(reg, "categories")
    os.makedirs(cat_dir, exist_ok=True)
    for name in os.listdir(cat_dir):
        os.remove(os.path.join(cat_dir, name))
    by_cat = {}
    for skill in skills:
        by_cat.setdefault(skill["category"], []).append(skill)
    with open(os.path.join(reg, "categories.md"), "w", encoding="utf-8") as fh:
        fh.write("# Categories\n\n")
        for cat in sorted(by_cat):
            fh.write("- `%s` (%d skills) - registry/categories/%s.md\n" % (cat, len(by_cat[cat]), cat))
    for cat, items in by_cat.items():
        items.sort(key=lambda s: (-quality(s["rating"], s.get("stars", 0)), s["id"]))
        with open(os.path.join(cat_dir, cat + ".md"), "w", encoding="utf-8") as fh:
            fh.write("# %s - best rated first\n\n" % cat)
            for s in items:
                where = s["url"] if s.get("source") == "github" else "`%s`" % s["path"]
                kind = " (repository)" if s.get("kind") == "resource" else ""
                fh.write("- **%s**%s - %s %s\n" % (s["id"], kind, s["description"], where))


def package():
    dist = os.path.join(REPO_ROOT, "dist")
    os.makedirs(dist, exist_ok=True)
    out = os.path.join(dist, "oneskill.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for base, dirs, files in os.walk(SKILL_ROOT):
            dirs[:] = sorted(d for d in dirs if d not in ("__pycache__", "cache"))
            for name in sorted(files):
                if name.startswith("."):
                    continue
                full = os.path.join(base, name)
                zf.write(full, os.path.join("oneskill", os.path.relpath(full, SKILL_ROOT)))
    return out


def main():
    skills, errors = collect()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        sys.exit(1)
    with open(CONFIG, encoding="utf-8") as fh:
        config = json.load(fh)
    index = {"version": 1, "repo": config.get("repo", ""), "skills": skills}
    with open(os.path.join(SKILL_ROOT, "registry", "index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, separators=(",", ":"))
        fh.write("\n")
    # the site gets a slimmer copy: it only needs what it shows and searches
    site_keys = ("id", "kind", "category", "description", "tags", "repo", "stars", "url", "source", "rating", "license")
    slim = {"version": 1, "repo": index["repo"], "skills": [{k: s[k] for k in site_keys if k in s} for s in skills]}
    with open(os.path.join(REPO_ROOT, "site", "registry.js"), "w", encoding="utf-8") as fh:
        fh.write("window.ONESKILL_REGISTRY = %s;\n" % json.dumps(slim, separators=(",", ":")))
    write_fallback(skills)
    out = package()
    shutil.copy(out, os.path.join(REPO_ROOT, "site", "oneskill.zip"))
    cats = len({s["category"] for s in skills})
    links = len([s for s in skills if s.get("source") == "github"])
    print("%d linked from GitHub" % links)
    print("%d skills in %d categories -> %s (%.0f KB)" % (len(skills), cats, os.path.relpath(out, REPO_ROOT), os.path.getsize(out) / 1024))


if __name__ == "__main__":
    main()

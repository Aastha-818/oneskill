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
RATINGS = os.path.join(REPO_ROOT, "registry", "ratings.json")
CONFIG = os.path.join(REPO_ROOT, "registry", "config.json")

sys.path.insert(0, os.path.join(SKILL_ROOT, "scripts"))
from route import quality  # noqa: E402  (one definition of the rating formula)

REQUIRED = ("name", "description", "tags")
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
                    "path": "skills/%s/%s/SKILL.md" % (category, skill_id),
                    "rating": {"votes": rating.get("votes", 0), "sum": rating.get("sum", 0)},
                }
            )
    ids = [s["id"] for s in skills]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append("%s: id used in more than one category" % dup)
    return skills, errors


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
        items.sort(key=lambda s: (-quality(s["rating"]), s["id"]))
        with open(os.path.join(cat_dir, cat + ".md"), "w", encoding="utf-8") as fh:
            fh.write("# %s - best rated first\n\n" % cat)
            for s in items:
                fh.write("- **%s** - %s `%s`\n" % (s["id"], s["description"], s["path"]))


def package():
    dist = os.path.join(REPO_ROOT, "dist")
    os.makedirs(dist, exist_ok=True)
    out = os.path.join(dist, "oneskill.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for base, dirs, files in os.walk(SKILL_ROOT):
            dirs[:] = sorted(d for d in dirs if d != "__pycache__")
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
        json.dump(index, fh, indent=1)
        fh.write("\n")
    with open(os.path.join(REPO_ROOT, "site", "registry.js"), "w", encoding="utf-8") as fh:
        fh.write("window.ONESKILL_REGISTRY = %s;\n" % json.dumps(index))
    write_fallback(skills)
    out = package()
    shutil.copy(out, os.path.join(REPO_ROOT, "site", "oneskill.zip"))
    cats = len({s["category"] for s in skills})
    print("%d skills in %d categories -> %s (%.0f KB)" % (len(skills), cats, os.path.relpath(out, REPO_ROOT), os.path.getsize(out) / 1024))


if __name__ == "__main__":
    main()

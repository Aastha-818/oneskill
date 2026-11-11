#!/usr/bin/env python3
"""Pick the best one or two skills in the catalog for a task.

score = relevance (BM25 over name, tags, description) x quality (rating prior)

Standard library only, so it runs anywhere a skill can run. The same ranking
is implemented in site/app.js for the website demo - keep the two in step.
"""
import argparse
import json
import math
import os
import re
import sys
import urllib.request
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "registry", "index.json")
CACHE = os.path.join(ROOT, "cache")

FIELD_WEIGHTS = {"name": 3.0, "tags": 2.5, "description": 1.0}
K1, B = 1.4, 0.6
# Bayesian rating prior: a skill with no votes sits at PRIOR_MEAN, and needs
# about PRIOR_VOTES real votes before its own average dominates.
PRIOR_MEAN, PRIOR_VOTES = 3.5, 8
# How far ratings can move a result. Relevance always matters most.
QUALITY_FLOOR = 0.5
SKILL_BONUS = 1.1
NAME_BONUS = 1.3  # query word equals the entry's first name word  # a ready-to-follow SKILL.md beats a repository README at equal relevance
SUPPORT_RATIO = 0.55  # second pick must score at least this share of the first
# Match strength counts query terms found in a skill's name or tags (anchors).
# Two anchors is a strong match, one is weak, description-only hits are none.
ANCHOR_FIELDS = ("name", "tags")

NAME_HITS = set()
STOPWORDS = set(
    "a an and are as at be but by can could do for from get give have help how i "
    "in into is it its just let like make me my need of on or our please should "
    "so some that the their them then this to up us use want we what when which "
    "will with would you your new good best create build".split()
)


def stem(word):
    for suffix in ("ations", "ation", "ings", "ing", "ers", "er", "ies", "es", "ed", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def tokens(text):
    """Stemmed tokens, plus the exact word when stemming changed it, so that
    "poster" still matches "poster" more strongly than it matches "post"."""
    out = []
    for w in re.findall(r"[a-z0-9+#]+", text.lower()):
        if len(w) <= 1 or w in STOPWORDS:
            continue
        s = stem(w)
        out.append(s)
        if s != w:
            out.append(w)
    return out


def quality(rating, stars=0):
    """Bayesian average rating, on a 0-1 scale.

    """
    # Until real votes arrive, GitHub stars set the prior: 100 stars ~3.6,
    # 10k ~4.2, 100k+ ~4.5. Entries without a star count stay at 3.5.
    prior = PRIOR_MEAN if not stars else 3.0 + min(1.5, 0.3 * math.log10(1 + stars))
    votes = rating.get("votes", 0)
    mean = (prior * PRIOR_VOTES + rating.get("sum", 0)) / (PRIOR_VOTES + votes)
    return mean / 5.0


def build_docs(skills):
    docs, anchors = [], []
    for skill in skills:
        tf, anchor = {}, set()
        for field, weight in FIELD_WEIGHTS.items():
            value = skill.get(field, "")
            if isinstance(value, list):
                value = " ".join(value)
            for tok in tokens(value.replace("-", " ")):
                tf[tok] = tf.get(tok, 0.0) + weight
                if field in ANCHOR_FIELDS:
                    anchor.add(tok)
        docs.append(tf)
        anchors.append(anchor)
    return docs, anchors


def rank(query, skills, category=None):
    docs, anchors = build_docs(skills)
    n = len(docs)
    avg_len = sum(sum(d.values()) for d in docs) / max(n, 1)
    df = {}
    for d in docs:
        for tok in d:
            df[tok] = df.get(tok, 0) + 1

    q = list(dict.fromkeys(tokens(query)))
    NAME_HITS.update(q)
    results = []
    for skill, d, anchor in zip(skills, docs, anchors):
        if category and skill["category"] != category:
            continue
        length = sum(d.values())
        relevance, matched = 0.0, []
        for tok in q:
            f = d.get(tok)
            if not f:
                continue
            idf = math.log(1 + (n - df[tok] + 0.5) / (df[tok] + 0.5))
            relevance += idf * f * (K1 + 1) / (f + K1 * (1 - B + B * length / avg_len))
            matched.append(tok)
        if not matched:
            continue
        qual = quality(skill.get("rating", {}), skill.get("stars", 0))
        score = relevance * (QUALITY_FLOOR + (1 - QUALITY_FLOOR) * qual)
        if skill.get("kind", "skill") == "skill":
            score *= SKILL_BONUS
        if any(t in NAME_HITS and t in q for t in tokens(skill["id"].replace("-", " "))[:1]):
            score *= NAME_BONUS  # the query names the thing itself (e.g. "shadcn", "remotion")
        results.append(
            {
                "skill": skill,
                "score": score,
                "anchors": len([t for t in matched if t in anchor]),
                "matched": matched,
            }
        )
    results.sort(key=lambda r: (-r["score"], r["skill"]["id"]))
    return results


def fetch(skill):
    """Download a linked skill's SKILL.md into cache/<id>/ and return its path."""
    folder = os.path.join(CACHE, skill["id"])
    target = os.path.join(folder, "SKILL.md" if skill.get("kind", "skill") == "skill" else "README.md")
    if os.path.isfile(target):
        return os.path.relpath(target, ROOT), None
    try:
        req = urllib.request.Request(skill["raw"], headers={"User-Agent": "oneskill-router"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read(60000)  # a README can be huge; the first part is the guide
        os.makedirs(folder, exist_ok=True)
        with open(target, "wb") as fh:
            fh.write(body)
        return os.path.relpath(target, ROOT), None
    except Exception as exc:  # no network, blocked, or the file moved
        return None, str(exc)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("task", nargs="*", help="the task, in the user's words")
    parser.add_argument("--category", help="only consider one category")
    parser.add_argument("--top", type=int, default=2, help="how many to return")
    parser.add_argument("--list-categories", action="store_true")
    parser.add_argument(
        "--fetch", action="store_true", help="download picks that live on GitHub into cache/ so they can be read"
    )
    args = parser.parse_args()

    with open(INDEX, encoding="utf-8") as fh:
        index = json.load(fh)
    skills = index["skills"]

    if args.list_categories:
        counts = {}
        for skill in skills:
            counts[skill["category"]] = counts.get(skill["category"], 0) + 1
        print(json.dumps(counts, indent=2, sort_keys=True))
        return

    query = " ".join(args.task).strip()
    if not query:
        parser.error("give the task as an argument")

    results = rank(query, skills, args.category)
    if not results:
        print(json.dumps({"match": "none", "picks": []}, indent=2))
        return

    top = results[0]
    match = "strong" if top["anchors"] >= 2 else "weak" if top["anchors"] == 1 else "none"
    if match == "none":
        print(json.dumps({"match": "none", "picks": []}, indent=2))
        return

    # --top above 2 is for browsing candidates, so it skips the support cutoff.
    keep = [top] + [
        r for r in results[1 : args.top] if args.top > 2 or r["score"] >= SUPPORT_RATIO * top["score"]
    ]
    repo = index.get("repo", "")
    picks = []
    for i, r in enumerate(keep):
        skill = r["skill"]
        pick = {
            "role": "primary" if i == 0 else "supporting",
            "id": skill["id"],
            "category": skill["category"],
            "path": skill["path"],
            "score": round(r["score"], 3),
            "rating": round(quality(skill.get("rating", {}), skill.get("stars", 0)) * 5, 2),
            "kind": skill.get("kind", "skill"),
            "stars": skill.get("stars", 0),
            "votes": skill.get("rating", {}).get("votes", 0),
            "why": r["matched"],
            "source": skill.get("source", "local"),
        }
        if skill.get("source") == "github":
            pick["repo"] = skill["repo"]
            pick["url"] = skill["url"]
            pick["raw"] = skill["raw"]
            pick["license"] = skill.get("license", "")
            pick["path"] = None  # nothing to read locally unless --fetch succeeds
            if args.fetch:
                pick["path"], pick["fetch_error"] = fetch(skill)
        if repo:
            pick["rate_url"] = (
                "https://github.com/%s/issues/new?template=rate-skill.yml&title=%s"
                % (repo, quote("Rate: " + skill["id"]))
            )
        picks.append(pick)
    json.dump({"match": match, "picks": picks}, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()

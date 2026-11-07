#!/usr/bin/env python3
"""Record one rating from a "Rate a skill" issue into registry/ratings.json.

Usage: apply_rating.py <issue-body-file> <github-login>
One vote per GitHub account per skill; voting again replaces the old vote.
"""
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RATINGS = os.path.join(REPO_ROOT, "registry", "ratings.json")
SKILLS_DIR = os.path.join(REPO_ROOT, "skill", "oneskill", "skills")


def field(body, label):
    match = re.search(r"###\s*%s\s*\n+([^\n]+)" % re.escape(label), body)
    return match.group(1).strip() if match else ""


def known_skills():
    return {s for cat in os.listdir(SKILLS_DIR) if os.path.isdir(os.path.join(SKILLS_DIR, cat))
            for s in os.listdir(os.path.join(SKILLS_DIR, cat))}


def main():
    body = open(sys.argv[1], encoding="utf-8").read()
    voter = sys.argv[2]
    skill = field(body, "Skill").strip("` ").lower()
    stars = field(body, "Rating")
    if skill not in known_skills():
        sys.exit("unknown skill: %r" % skill)
    if stars not in ("1", "2", "3", "4", "5"):
        sys.exit("rating must be 1-5")
    with open(RATINGS, encoding="utf-8") as fh:
        ratings = json.load(fh)
    entry = ratings.setdefault(skill, {"votes": 0, "sum": 0, "voters": {}})
    entry["voters"][voter] = int(stars)
    entry["votes"] = len(entry["voters"])
    entry["sum"] = sum(entry["voters"].values())
    with open(RATINGS, "w", encoding="utf-8") as fh:
        json.dump(ratings, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("%s: %d votes, average %.2f" % (skill, entry["votes"], entry["sum"] / entry["votes"]))


if __name__ == "__main__":
    main()

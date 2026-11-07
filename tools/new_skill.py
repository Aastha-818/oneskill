#!/usr/bin/env python3
"""Scaffold a catalog skill:  python3 tools/new_skill.py <category> <id>"""
import os
import sys

TEMPLATE = """---
name: {id}
description: One sentence on what this skill does and when to use it (under 300 characters).
tags: comma, separated, words, people, would, type
author: your-github-handle
license: MIT
---

# {title}

What good looks like, the steps to get there, and the mistakes to avoid.
Keep it under about 150 lines - it is loaded into context every time it wins.
"""


def write(category, skill_id, text=None):
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skill", "oneskill", "skills")
    folder = os.path.join(root, category, skill_id)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "SKILL.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text or TEMPLATE.format(id=skill_id, title=skill_id.replace("-", " ").title()))
    return path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    print(write(sys.argv[1], sys.argv[2]))

#!/usr/bin/env python3
"""Fill in GitHub star counts and licences for every linked repository.

Uses the public search API (no token), six repositories per query, with a
pause between queries to stay under the anonymous rate limit. Rewrites the
links/*.json files in place. Run occasionally: python3 tools/update_stars.py
"""
import glob
import json
import os
import sys
import time
import urllib.parse
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINKS = os.path.join(REPO_ROOT, "skill", "oneskill", "links")


def lookup(repos):
    q = " ".join("repo:" + r for r in repos)
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode({"q": q, "per_page": 50})
    req = urllib.request.Request(url, headers={"User-Agent": "oneskill-stars", "Accept": "application/vnd.github+json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return {i["full_name"].lower(): i for i in json.load(r)["items"]}
        except urllib.error.HTTPError as exc:
            if exc.code == 422:  # one of the repositories no longer exists; skip the batch
                return {}
            if exc.code in (403, 429):
                time.sleep(65)
                continue
            raise
        except (OSError, ConnectionError):  # flaky network: wait and retry
            time.sleep(10)
    return {}


def main():
    files = {f: json.load(open(f, encoding="utf-8")) for f in glob.glob(os.path.join(LINKS, "*.json"))}
    todo = sorted({e["repo"] for es in files.values() for e in es if not e.get("stars")}, key=str.lower)
    print("%d repositories to look up" % len(todo), file=sys.stderr)
    found = {}

    def save():
        for f, es in files.items():
            for e in es:
                m = found.get(e["repo"].lower())
                if m:
                    e["stars"] = m["stargazers_count"]
                    e["license"] = (m.get("license") or {}).get("spdx_id") or e.get("license") or "unspecified"
                    e["branch"] = e.get("branch") or m["default_branch"]
            json.dump(es, open(f, "w", encoding="utf-8"), indent=1)

    for i in range(0, len(todo), 6):
        found.update(lookup(todo[i:i + 6]))
        time.sleep(6.5)
        if i % 120 == 0:
            save()  # keep progress even if the network drops later
            print("%d/%d" % (i, len(todo)), file=sys.stderr)
    save()
    print("%d of %d found" % (len(found), len(todo)), file=sys.stderr)


if __name__ == "__main__":
    main()

# OneSkill

One skill for Claude with a whole rated catalog of specialist skills inside it.
Upload it once. For each task it finds the best one or two skills in the
catalog, Claude reads only those, and does the work their way.

## How it works

1. **Route** - Claude runs `scripts/route.py "<task>"`. The script searches
   `registry/index.json` and returns up to two skills: a primary and, when one
   scores close behind, a supporting skill. The catalog is searched, never read,
   so context cost is the same at 26 skills or 5,000 (5,200 skills rank in
   about 0.1s).
2. **Load** - Claude reads only the picked `SKILL.md` files.
3. **Work** - the primary skill leads; long tasks are re-routed per phase.
4. **Rate** - answers end with the skills used and a link to rate them.

Ranking: `score = relevance x (0.6 + 0.4 x rating / 5)`. Relevance is BM25 over
each skill's name, tags and description. Rating is a Bayesian average: every
skill starts at 3.5 and needs about eight votes before its own average takes
over. If no query word hits a skill's name or tags, the router returns no match.

## Layout

    skill/oneskill/            the skill users upload
      SKILL.md                 router instructions
      scripts/route.py         the ranking (standard library only)
      registry/                generated index and no-script fallback lists
      skills/<category>/<id>/  the catalog, one SKILL.md each
    registry/ratings.json      votes per skill (source of truth)
    registry/config.json       set "repo" to "owner/name" to switch on rating links
    tools/build.py             rebuild index, site data and dist/oneskill.zip
    tools/new_skill.py         scaffold a catalog skill
    tools/apply_rating.py      record a rating from a GitHub issue
    site/                      the website (static; GitHub Pages ready)

## Commands

    python3 tools/build.py                       # after any change
    python3 tools/new_skill.py design poster-design
    python3 skill/oneskill/scripts/route.py "design a landing page"
    python3 -m http.server 4173 --directory site # preview the site

## Ratings

"Rate a skill" issues (template in `.github/ISSUE_TEMPLATE`) are recorded by
the `Record rating` workflow: one vote per GitHub account per skill, written to
`registry/ratings.json`, then the index and site are rebuilt and republished.

## Adding skills

Run `tools/new_skill.py`, fill in the file, run `tools/build.py`, open a pull
request. Catalog skills are read by Claude as instructions, so review every
submission as you would review code: no hidden instructions, no network calls,
no attempts to override the user. Only add skills whose licence allows it.

Independent project, not made by Anthropic. MIT licensed.

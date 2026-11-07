---
name: prd-writing
description: Write a product requirements document or feature spec - problem, goals, scope, requirements and success metrics. Use for PRDs, feature specs, product briefs and user stories.
tags: prd, product requirements, spec, feature, requirements, user stories, product brief, scope, product management
author: oneskill
license: MIT
---

# Prd Writing

## Problem before solution
Half of a good PRD is the problem statement. Who has the problem, how often, what they do today, and what it costs them - with evidence (quotes, data, support tickets). If the evidence is thin, say so.

## Sections
1. **Summary** - three sentences: problem, proposed change, expected result.
2. **Goals and non-goals** - what success means, and what this deliberately will not do. Non-goals prevent more arguments than any other section.
3. **Users and scenarios** - two or three concrete situations, written as stories with a real person in them.
4. **Requirements** - numbered, each testable, each marked must / should / could. Describe behaviour, not implementation. Include empty, error and edge states.
5. **Success metrics** - the one metric that should move, by how much, by when, and the guardrail metrics that must not get worse.
6. **Open questions** - with an owner for each.
7. **Risks and dependencies** - technical, legal, other teams.
8. **Rollout** - phases, flags, who gets it first.

## Quality bar
- An engineer could estimate from it; a designer could start from it; a new teammate could understand why it exists.
- No requirement says "easy", "fast" or "intuitive" without a number or example.
- It fits in about two pages before appendices.

Mark assumptions you made so the user can correct them, rather than leaving gaps.

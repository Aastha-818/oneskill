---
name: code-review
description: Review code or a pull request for correctness bugs, security problems and maintainability, with prioritised findings. Use for code reviews, PR reviews and diff audits.
tags: code review, pull request, pr, diff, review, bugs, security, refactor, quality, code
author: oneskill
license: MIT
---

# Code Review

## Read for behaviour first
Understand what the change is meant to do before judging how. Read the description, then the tests, then the code. A review that only comments on style has missed the job.

## What to hunt for, in order
1. **Correctness** - off-by-one, null and empty inputs, error paths that swallow failures, wrong operator, state changed in the wrong order, concurrency and retries.
2. **Security** - unvalidated input reaching a query, shell, file path or HTML; secrets in code or logs; missing authorisation checks; unsafe deserialisation.
3. **Data** - migrations that lock or lose data, changes that break old clients, anything not reversible.
4. **Tests** - do they fail without the change? Do they cover the unhappy path?
5. **Design** - duplication of something that already exists, a function doing two jobs, names that mislead.

## Verify before you claim
For each suspected bug, trace it: which input, through which line, to which wrong result. If you can run the code, run it. Drop findings you cannot make concrete.

## Report
Most severe first. Each finding: file and line, what goes wrong with a concrete input, and the smallest fix. Separate "must fix" from "consider". Keep style remarks to what a linter would not catch, and say what is good about the change. If nothing is wrong, say so plainly.

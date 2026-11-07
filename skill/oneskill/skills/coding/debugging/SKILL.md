---
name: debugging
description: Find the root cause of a bug, error, crash or failing test systematically, then fix it and prove the fix. Use for debugging, stack traces, flaky tests and unexpected behaviour.
tags: debug, debugging, bug, error, fix, crash, stack trace, exception, failing test, flaky, broken, code
author: oneskill
license: MIT
---

# Debugging

## Method
Guessing is slow. Narrow instead.
1. **Reproduce** - get the failure to happen on demand with the smallest input. Write that down as a command or test. No reproduction, no fix.
2. **Read the evidence** - the whole error and stack trace, bottom to top. The first error in the log matters more than the last.
3. **State a hypothesis** - "X is null here because Y returned early." It must predict something you can check.
4. **Test it** - add a log, run in a debugger, or write a tiny script. One variable at a time.
5. **Bisect when stuck** - halve the search space: which commit, which half of the input, which half of the function.

## Common causes
What changed recently, wrong assumptions about input shape, stale cache or build, environment differences (versions, env vars, timezone), async ordering, and shared mutable state.

## Fix
- Fix the cause, not the symptom. A try/except around the crash is rarely the fix.
- Add the reproduction as a regression test; watch it fail before the fix and pass after.
- Look for the same mistake elsewhere in the codebase.

## Report
Say what was wrong, why it happened, what you changed and how you verified it. If you could not reproduce it, say that and give your best-supported hypothesis as a hypothesis.

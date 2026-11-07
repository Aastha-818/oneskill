---
name: test-writing
description: Write useful automated tests - unit, integration and edge cases - that catch real bugs and stay maintainable. Use for writing tests, improving coverage and test-driven development.
tags: test, tests, testing, unit test, integration, coverage, tdd, pytest, jest, mock, code
author: oneskill
license: MIT
---

# Test Writing

## What a good test is
It fails when the behaviour breaks, passes when it does not, and tells you what broke from its name alone. Test behaviour through the public interface, not the implementation - a refactor should not turn tests red.

## Choosing cases
For each unit of behaviour, cover:
- the normal case,
- boundaries (0, 1, many; empty; maximum; exactly on the limit),
- invalid input and the error it should raise,
- anything in the code that branches,
- any bug that has already happened once.

## Writing them
- Name as a sentence: `test_refund_fails_when_order_already_refunded`.
- Arrange, act, assert - one behaviour per test, visible at a glance.
- Use real objects where cheap; fake only what is slow, random or external (network, clock, payment provider). Over-mocking tests your mocks.
- No logic in tests - no loops or conditionals that could themselves be wrong. Use parameterised cases instead.
- Tests must not depend on each other, on order, or on the real time or network.

## Follow the project
Use the framework, fixtures, file layout and naming already in the repository. Read two existing tests before writing one.

## Prove it
Run the tests. Then break the code on purpose and confirm the test fails - a test that cannot fail is worth nothing. Report what is covered and what you deliberately left out.

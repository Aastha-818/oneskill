---
name: spreadsheet-modeling
description: Build a clear, auditable spreadsheet model - financial model, budget, forecast or calculator - with separated inputs, formulas and outputs. Use for Excel or Google Sheets models.
tags: spreadsheet, excel, google sheets, model, financial model, budget, forecast, formulas, calculator, projection
author: oneskill
license: MIT
---

# Spreadsheet Modeling

## Layout
Separate three things, ideally on separate sheets:
- **Inputs** - every assumption in one place, labelled with units and source, visibly marked as editable.
- **Calculations** - formulas only, no typed numbers.
- **Outputs** - the summary a reader looks at first.

Time runs left to right, one period per column, the same column for the same period on every sheet.

## Formula rules
- Never hard-code a number inside a formula. `=B4*1.18` hides an assumption; `=B4*(1+Inputs!tax_rate)` shows it.
- One formula per row, copied across. A row where the formula changes halfway is where errors hide.
- Prefer short formulas over clever ones; use helper rows.
- Use lookups that fail loudly (`XLOOKUP` with no default, or `INDEX/MATCH` exact) rather than returning a wrong match.
- Keep units consistent and stated (thousands, monthly versus annual).

## Checks
Add a checks section: totals that must match, balances that must be zero, percentages that must sum to 100. One cell reports whether all checks pass. Test with extreme inputs - zero, double, negative - and see if outputs move the right way.

## Deliver
A short note covering what the model answers, the key assumptions and which three inputs move the result most. Include scenarios (base, low, high) when the user is making a decision.

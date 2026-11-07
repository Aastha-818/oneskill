---
name: data-analysis
description: Analyse a dataset to answer a question - cleaning, exploration, statistics and clear findings. Use for data analysis, CSV or Excel exploration, metrics investigation and insight reports.
tags: data, analysis, analyse, analyze, dataset, csv, excel, statistics, insights, metrics, pandas, trends, report
author: oneskill
license: MIT
---

# Data Analysis

## Question first
Write down the decision this analysis feeds. "Explore the data" is not a question; "why did signups drop in March?" is. Agree what a useful answer would look like.

## Know the data before trusting it
- Shape, column types, date range, what one row represents.
- Missing values, duplicates, impossible values, sudden changes in volume (often a tracking change, not a real one).
- Say what you cleaned and how many rows it affected.

## Analyse
- Start with the simplest cut that could answer the question: a total over time, then split by the obvious dimensions.
- Compare like with like - same period length, same cohort, rates rather than counts when group sizes differ.
- Check a surprising result twice. Most surprises are bugs or definitions.
- Correlation is not cause; say which one you have. Look for a confounder before recommending action.
- Give a sense of uncertainty: sample sizes, and whether a difference is beyond normal variation.

## Report
Lead with the answer in one or two sentences, then the three or four pieces of evidence, each with one chart or table. Then caveats and what you would check next. Put method and code at the end. Round numbers to what is meaningful, and always give the denominator.

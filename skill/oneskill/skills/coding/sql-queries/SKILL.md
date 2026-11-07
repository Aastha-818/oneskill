---
name: sql-queries
description: Write, explain and optimise SQL queries - joins, aggregation, window functions and performance. Use for SQL, database queries, reporting queries and slow query tuning.
tags: sql, query, database, postgres, mysql, join, aggregate, window function, index, slow query, data
author: oneskill
license: MIT
---

# Sql Queries

## Before writing
Get the schema: tables, keys and row counts if performance matters. State the question as one sentence including the grain - "one row per customer per month". Most wrong queries have the wrong grain.

## Writing
- Build up with CTEs, one step each, named for what they hold.
- Select columns by name, never `*` in anything saved.
- Join on keys and know the cardinality: a one-to-many join before an aggregate double-counts. Check with a row count before and after.
- `LEFT JOIN` plus a filter on the right table in `WHERE` silently becomes an inner join - put the condition in `ON`.
- `NULL` is not equal to anything; `NOT IN` with a null returns nothing - use `NOT EXISTS`.
- Use window functions for running totals, ranks and "latest row per group" (`ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)`).
- Be explicit about time zones and whether date ranges are inclusive.

## Performance
Read the plan (`EXPLAIN ANALYZE`). Look for sequential scans on large tables, row estimates far from actual, and sorts spilling to disk. Fixes, in order: filter earlier, index the columns used in joins and filters, avoid functions on indexed columns, replace correlated subqueries with joins.

## Deliver
The query formatted with one clause per line, a line on what it returns and its grain, any assumptions about the schema, and the dialect it targets. Never run a write or delete without showing it first.

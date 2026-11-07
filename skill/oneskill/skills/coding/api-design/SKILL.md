---
name: api-design
description: Design a clean REST or HTTP API - resources, endpoints, request and response shapes, errors, pagination and versioning. Use for API design, endpoint specs, OpenAPI and backend contracts.
tags: api, rest, endpoint, http, backend, openapi, schema, json, design, versioning, pagination, code
author: oneskill
license: MIT
---

# Api Design

## Start from the client
List what the consumer needs to do, in their words. Design the calls they would wish existed, then check the backend can serve them. Do not mirror the database tables.

## Conventions
- **Resources are nouns, plural**: `/invoices`, `/invoices/{id}`, `/invoices/{id}/payments`. Verbs come from HTTP methods. For true actions, a sub-resource: `POST /invoices/{id}/send`.
- **Methods**: GET reads and is safe, POST creates, PATCH partially updates, PUT replaces, DELETE removes. PUT and DELETE must be idempotent.
- **Status codes**: 200, 201 with Location, 204, 400 validation, 401 not signed in, 403 not allowed, 404, 409 conflict, 422 semantic error, 429 rate limit.
- **Errors**: one shape everywhere - `{"error": {"code": "invoice_locked", "message": "...", "field": "..."}}`. Codes are stable strings clients can branch on.
- **Lists**: cursor pagination (`?limit=50&after=cursor`), return `next_cursor`. Filtering and sorting through query parameters.
- **Names**: one casing style throughout, ISO 8601 timestamps in UTC, money as integer minor units plus currency, ids as opaque strings.

## Safety and change
- Accept an `Idempotency-Key` on POSTs that create or charge.
- Adding fields is safe; removing or renaming is breaking. Version in the path or a header and say which.
- Authentication, rate limits and required scopes belong in the spec.

## Deliver
An endpoint table, then for each endpoint an example request and response, including one error. Offer an OpenAPI document if useful.

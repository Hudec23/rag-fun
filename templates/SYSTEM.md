# <System name> — System spec

## 1. Purpose
One paragraph. Who uses it, what it does.

## 1a. Requirements
One row per requirement. `Covered by`: `features` (listed by at least one feature in
plan/features.yaml) or `skeleton` (cross-cutting, proven by the walking skeleton's `baseline_tests`).

| ID | Requirement | Kind | Covered by |
|---|---|---|---|
| R-001 | Customer can place an order with at least one item | functional | features |
| R-002 | Placed orders are fulfilled asynchronously | functional | features |
| R-003 | Every error response uses the shared error shape | cross-cutting | skeleton |

## 2. Services
| Service | Language / version | Framework / version | Owns | Responsibility | Must NOT |
|---|---|---|---|---|---|
| api | TypeScript 5.6, Node 22 | Fastify 5.1 | orders DB | Public REST API | call payments DB directly |
| worker | Go 1.23 | stdlib + nats.go 1.37 | – | Processes order events | expose HTTP except /health |

## 3. Communication
| From → To | Style | Contract file | Notes |
|---|---|---|---|
| api → worker | event `order.created` | contracts/events/order.created.schema.json | at-least-once, idempotency key = order id |

## 4. Data
Per service: database, migration tool, location of schema file.

## 5. Cross-cutting decisions
| Topic | Decision |
|---|---|
| IDs | UUIDv7 strings |
| Time | UTC, ISO-8601 with `Z` |
| Errors | `{ "error": { "code": "ORDER_NOT_FOUND", "message": "..." } }`, codes in contracts/shared/errors.json |
| Logging | JSON lines: ts, level, service, msg, trace_id |
| Config | env vars only; full list in §6 |
| Auth | ... |

## 6. Environment variables
| Var | Service | Example | Required |
|---|---|---|---|

## 7. Repo layout
```
services/
  api/        src/, test/, package.json
  worker/     cmd/, internal/, go.mod
contracts/
tests/e2e/
plan/
```

## 8. Conventions per language
### TypeScript (api)
- Formatter / linter: ...  Test: vitest ...
- Module layout — copy this pattern:
```ts
// services/api/src/orders/get.ts  (example module, already in repo)
```

### Go (worker)
...

## 9. Allowed dependencies (executor may NOT add any)
| Service | Package | Version | Purpose |
|---|---|---|---|

## 10. Out of scope
-

## 11. Decisions log
| # | Decision | Reason | Alternatives rejected |
|---|---|---|---|

## 12. Open questions
(must be empty before phase 2)

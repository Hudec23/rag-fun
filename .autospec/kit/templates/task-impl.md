---
id: T-api-007
kind: impl                        # implementation: make locked tests pass, never touch tests
feature: F-orders-create          # must exist in .autospec/plan/features.yaml
title: Implement POST /orders handler
service: api                      # must match .autospec/plan/services/<service>.yaml, or "integration"
depends_on: [T-api-007t, T-api-004, T-api-006]   # T-api-007t = the test task that wrote the unit tests
edit:                             # the ONLY files the executor may create or change (max_edit_files, no tests)
  - services/api/src/orders/create.ts     # stub written by Claude in planning; executor fills it in
  - services/api/src/routes.ts
read:                             # files to open before coding (counted in max_read_tokens)
  - services/api/src/orders/get.ts          # example module to imitate
  - services/api/src/db/orders-repo.ts
locked:                           # tests that define "done"
  - services/api/test/orders/create.test.ts          # unit tests, written by test task T-api-007t
  - services/api/test/acceptance/orders-create.test.ts  # Claude-written acceptance test (last task of feature)
verify:                           # all must exit 0; service regression (build, lint, baseline + done tasks' tests) runs after
  - docker compose -f docker-compose.dev.yml run --rm api-dev npx vitest run test/orders/create.test.ts test/acceptance/orders-create.test.ts
max_attempts: 3
---

## Goal
Accept `POST /orders`, validate the body, persist the order, publish `order.created`, return 201.

## Context
Request/response (from contracts/api.openapi.yaml#/paths/~1orders/post):
```yaml
# paste the exact schema fragment here
```
Repository you must call (already implemented in T-api-004):
```ts
export async function insertOrder(db: Db, o: NewOrder): Promise<Order>
```
Publisher (T-api-006):
```ts
export async function publishOrderCreated(bus: Bus, o: Order): Promise<void>
```
Follow the structure of `services/api/src/orders/get.ts` exactly (validation with zod schema at top,
handler function exported as `createOrderHandler`, errors via `httpError(code)`).

## Steps
1. In `services/api/src/orders/create.ts` export `createOrderHandler(deps: Deps): RouteHandler`.
2. Validate body with zod schema `CreateOrderBody` (fields: ...). On failure → `httpError("VALIDATION_FAILED")`.
3. Call `insertOrder`, then `publishOrderCreated`. If publish throws, log it at `warn` and still return 201.
4. Register the route in `services/api/src/routes.ts`: `app.post("/orders", createOrderHandler(deps))`.

## Do not
- Do not edit any test file or anything under `contracts/` or `.autospec/plan/`.
- Do not add npm dependencies.
- Do not rename or change signatures of existing exported functions.
- Do not catch errors and return 500 yourself; use `httpError`.

## Done when
The verify command passes, and the service regression (build, lint, previously green tests)
still passes. Red tests of unfinished tasks are expected — ignore them.

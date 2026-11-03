---
id: T-api-007t
kind: test                        # test-writing: tests only, must end RED
feature: F-orders-create
title: Write unit tests for createOrderHandler
service: api
depends_on: [T-api-004]
edit:                             # new test file(s) only; existing test files are locked automatically
  - services/api/test/orders/create.test.ts
read:
  - services/api/test/orders/get.test.ts    # example test file to imitate (style, fixtures)
  - services/api/test/fakes/fake-repo.ts    # fakes the tests must use
verify:                           # must PASS: tests compile, are collected, lint clean (locked after this task)
  - docker compose -f docker-compose.dev.yml run --rm api-dev npx tsc --noEmit -p tsconfig.test.json
  - docker compose -f docker-compose.dev.yml run --rm api-dev npx vitest list test/orders/create.test.ts
  - docker compose -f docker-compose.dev.yml run --rm api-dev npx eslint test/orders/create.test.ts
expect_fail:                      # must FAIL: EVERY test is red against the stub, none may pass
  - docker compose -f docker-compose.dev.yml run --rm api-dev npx vitest run test/orders/create.test.ts
max_attempts: 3
---

## Goal
Write unit tests for `createOrderHandler` covering every case below. Do not implement it —
`services/api/src/orders/create.ts` is a stub that throws `NotImplemented`; T-api-007 implements it.

## Context
Interface under test (stub already in repo):
```ts
export function createOrderHandler(deps: { repo: OrdersRepo; bus: Bus }): RouteHandler
```
Use `makeFakeRepo()` and `makeFakeBus()` from `test/fakes/`. Call the handler with
`await inject(handler, { method: "POST", body })` exactly as `test/orders/get.test.ts` does.
Error body shape: `{ error: { code: string, message: string } }`.

## Test cases
1. valid body → 201, response body equals the stored order, `repo.insert` called once
2. valid body → `bus.published` contains one `order.created` event with the order id
3. missing `customerId` → 400, `error.code === "VALIDATION_FAILED"`, repo not called
4. `items` empty array → 400 `VALIDATION_FAILED`
5. item `quantity` 0 or negative → 400 `VALIDATION_FAILED`
6. bus publish throws → still 201, order stored
7. repo insert throws → 500 `INTERNAL`, nothing published

## Do not
- Do not write implementation code in `src/` (not even to make a test compile).
- Do not use `it.skip`, `it.todo`, empty test bodies, or assertions that are always true.
- Do not hit a real database or network.

## Done when
Tests compile, lint clean and are listed (verify passes), and every one of them fails against
the stub (expect_fail fails, zero tests pass).

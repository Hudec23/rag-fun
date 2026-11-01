# Planning step 2 — Freeze contracts

Read `plan/SYSTEM.md`. Write every interface that crosses a service boundary into `contracts/`.
These files are **protected**: the executor can read them but never change them.

## Produce

- REST: `contracts/<service>.openapi.yaml` (OpenAPI 3.1). Every endpoint: request/response
  schemas, all status codes, error shape, examples for success and each error.
- gRPC: `contracts/<service>.proto`.
- Events/messages: `contracts/events/<topic>.schema.json` (JSON Schema 2020-12) with an example
  payload, producer, consumers, delivery semantics (at-least-once? idempotency key?).
- Shared enums / error codes: `contracts/shared/*.json`.
- DB schemas are **not** contracts (they are private to a service) but write them now anyway in
  `plan/services/<name>.schema.sql` or equivalent, so tasks can reference them.

## Rules

- No `additionalProperties: true`, no untyped `object`, no "TBD".
- Every field: type, required or optional, format, constraints (min/max/pattern), description.
- Pagination, sorting, filtering: specify exactly, once, and reuse.
- Add a contract test plan: for each contract, which side gets a consumer test and which side a
  provider test. Step 3 turns these into locked tests.
- If you can generate code from a contract (openapi-generator, protoc, quicktype), decide that
  now. You run the generator yourself in the walking skeleton (step 3A) and commit the output;
  the executor never runs generators.

## Self-check

- [ ] Every arrow in the SYSTEM.md communication table has a contract file.
- [ ] Every example validates against its schema (run a validator if you can).
- [ ] Nothing in a contract contradicts SYSTEM.md.

Print the list of contract files and "CONTRACT GAPS: 0".

# Planner task generator

Regenerates `plan/tasks/*.md`, `plan/features.yaml` and `.autospec/state.json` from the unit specs
(`spec_api.py`, `spec_worker.py`, `spec_web.py`) and the stub files in `services/*/src` (each task's
Context pastes the current stub source). Planner tool only — the executor never runs it.

```sh
docker run --rm -v "$PWD":/w -w /w/scripts/plan python:3.12.16-slim sh -c \
  'pip install -q --root-user-action=ignore pyyaml==6.0.3 && python gen.py' \
  && docker run --rm -v "$PWD":/w -w /w python:3.12.16-slim sh -c \
  'pip install -q --root-user-action=ignore pyyaml==6.0.3 && python scripts/autospec-check.py'
```

Warning: regenerating resets every task in `.autospec/state.json` to `pending`.
`stubs_web_initial.py` is the one-off script that created the web stubs (kept for reference; do not rerun —
it overwrites implemented files).

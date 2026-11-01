"""F-live-progress (R-014): SSE relays worker events for a run."""

import json
import threading
import time

import httpx

from conftest import API, PLAIN, new_collection, upload


def test_sse_receives_stage_lifecycle(api: httpx.Client) -> None:
    f = upload(api, "handbook.md")["files"][0]
    run = api.post("/ingest-runs", json={"file_id": f["id"], "collection_id": new_collection(api)["id"]}).json()
    received: list[tuple[str, dict]] = []  # type: ignore[type-arg]
    ready = threading.Event()

    def listen() -> None:
        with httpx.Client(timeout=httpx.Timeout(60, read=60)) as c:
            with c.stream("GET", f"{API}/events", params={"run_id": run["id"]}) as r:
                assert r.headers["content-type"].startswith("text/event-stream")
                ready.set()
                event = None
                for line in r.iter_lines():
                    if line.startswith("event:"):
                        event = line.split(":", 1)[1].strip()
                    elif line.startswith("data:") and event:
                        received.append((event, json.loads(line.split(":", 1)[1])))
                        if event in ("stage.completed", "stage.failed"):
                            return

    t = threading.Thread(target=listen, daemon=True)
    t.start()
    assert ready.wait(20)
    time.sleep(0.5)
    sr = api.post(f"/ingest-runs/{run['id']}/stages/parse", json={"params": PLAIN}).json()
    t.join(120)
    types = [e for e, _ in received]
    assert "run.updated" in types
    assert "stage.started" in types and types[-1] == "stage.completed", types
    completed = received[-1][1]
    assert completed["stage_run_id"] == sr["id"] and completed["summary"]["stage"] == "parse"
    # completed is published after the callback: the stage run is already done
    assert api.get(f"/stage-runs/{sr['id']}").json()["status"] == "done"


def test_events_requires_run_id(api: httpx.Client) -> None:
    r = api.get("/events")
    assert r.status_code == 422

"""Integration tests for rag_api.services.pipeline_graphs: put_graph, get_graph, list_graphs.
Real postgres via the `session` fixture; the graph fixture is
tests/contract_fixtures/shared__pipeline-graph.json (stage chunk, variant fixed) and is
copied with a swapped stage/variant for the other stages.
The services are still stubs — every test here is red until T-api-025."""

import json
from copy import deepcopy
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import PipelineGraphRow
from rag_api.errors import AppError
from rag_api.services import pipeline_graphs
from tests.conftest import FIXTURES

GRAPH = json.loads((FIXTURES / "shared__pipeline-graph.json").read_text())


def graph(stage: str, variant: str) -> dict[str, Any]:
    """The fixture graph copied with a different stage/variant."""
    g = deepcopy(GRAPH)
    g["stage"] = stage
    g["variant"] = variant
    return g


async def test_put_graph_then_get_graph_returns_the_same_graph(session: AsyncSession) -> None:
    await pipeline_graphs.put_graph(session, "chunk", "fixed", deepcopy(GRAPH))

    out = await pipeline_graphs.get_graph(session, "chunk", "fixed")

    assert out == GRAPH
    rows = (await session.execute(select(PipelineGraphRow))).scalars().all()
    assert [(r.stage, r.variant) for r in rows] == [("chunk", "fixed")]


async def test_put_graph_twice_replaces_the_row(session: AsyncSession, frozen_now: object) -> None:
    second = graph("chunk", "fixed")
    second["nodes"][0]["init_params"][1]["value"] = "500"

    await pipeline_graphs.put_graph(session, "chunk", "fixed", deepcopy(GRAPH))
    await pipeline_graphs.put_graph(session, "chunk", "fixed", second)

    rows = (await session.execute(select(PipelineGraphRow))).scalars().all()
    assert len(rows) == 1
    assert (rows[0].stage, rows[0].variant) == ("chunk", "fixed")
    assert rows[0].graph == second
    assert rows[0].updated_at == frozen_now


async def test_put_graph_stage_mismatch_raises_validation_error_field_stage(
    session: AsyncSession,
) -> None:
    with pytest.raises(AppError) as exc:
        await pipeline_graphs.put_graph(session, "embed", "fixed", GRAPH)

    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details == {"field": "stage"}
    assert (await session.execute(select(PipelineGraphRow))).scalars().all() == []


async def test_put_graph_variant_mismatch_raises_validation_error_field_variant(
    session: AsyncSession,
) -> None:
    with pytest.raises(AppError) as exc:
        await pipeline_graphs.put_graph(session, "chunk", "semantic", GRAPH)

    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details == {"field": "variant"}
    assert (await session.execute(select(PipelineGraphRow))).scalars().all() == []


async def test_list_graphs_orders_by_pipeline_stage_then_variant(
    session: AsyncSession,
) -> None:
    g_generate = graph("generate", "default")
    g_chunk_semantic = graph("chunk", "semantic")
    g_chunk_fixed = graph("chunk", "fixed")
    g_parse = graph("parse", "plain_text")
    await pipeline_graphs.put_graph(session, "generate", "default", g_generate)
    await pipeline_graphs.put_graph(session, "chunk", "semantic", g_chunk_semantic)
    await pipeline_graphs.put_graph(session, "chunk", "fixed", g_chunk_fixed)
    await pipeline_graphs.put_graph(session, "parse", "plain_text", g_parse)

    out = await pipeline_graphs.list_graphs(session)

    assert [(g["stage"], g["variant"]) for g in out.items] == [
        ("parse", "plain_text"),
        ("chunk", "fixed"),
        ("chunk", "semantic"),
        ("generate", "default"),
    ]
    assert out.items == [g_parse, g_chunk_fixed, g_chunk_semantic, g_generate]


async def test_get_graph_unknown_raises_pipeline_graph_not_found(
    session: AsyncSession,
) -> None:
    with pytest.raises(AppError) as exc:
        await pipeline_graphs.get_graph(session, "rerank", "default")

    assert exc.value.code == "PIPELINE_GRAPH_NOT_FOUND"
    assert exc.value.details == {"stage": "rerank", "variant": "default"}

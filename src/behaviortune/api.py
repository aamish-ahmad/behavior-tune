"""Stateless FastAPI surface for deterministic BehaviorTune reviewer operations."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

from .engineering import aggregate_scores, render_record, score_record


ConditionName = Literal["BASE", "SYSTEM", "CONTEXT", "LONG-NEUTRAL", "QLORA"]


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RenderRequest(StrictRequest):
    scenario: dict[str, Any]
    condition: ConditionName


class ScoreRequest(RenderRequest):
    raw_output: str


class AggregateRequest(StrictRequest):
    rows: list[dict[str, Any]]


app = FastAPI(
    title="BehaviorTune Reviewer API",
    version="1.0.0",
    description="Model-free deterministic rendering, scoring, and aggregation for BehaviorTune R1.",
)


@app.get("/healthz")
def healthz() -> dict[str, object]:
    return {"status": "ok", "model_activity": False, "api_version": "v1"}


@app.post("/v1/render")
def render(request: RenderRequest) -> dict[str, Any]:
    return render_record(request.scenario, request.condition)


@app.post("/v1/score")
def score(request: ScoreRequest) -> dict[str, Any]:
    return score_record(request.scenario, request.condition, request.raw_output)


@app.post("/v1/aggregate")
def aggregate(request: AggregateRequest) -> dict[str, Any]:
    return aggregate_scores(request.rows)

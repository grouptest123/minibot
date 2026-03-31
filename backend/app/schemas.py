from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    name: str
    description: str
    permission_level: str
    supports_mock: bool = True


class SkillDefinition(BaseModel):
    name: str
    description: str
    trigger_condition: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    dependencies: list[str]
    supports_mock: bool
    fallback_strategy: str


class Evidence(BaseModel):
    source: str
    timestamp: str
    summary: str
    detail: dict[str, Any] = Field(default_factory=dict)


class ObservationWindow(BaseModel):
    window_start: str
    window_end: str
    modalities: list[str]
    key_features: list[str]
    risk_level: str
    evidences: list[Evidence]


class Anomaly(BaseModel):
    event_id: str
    title: str
    category: str
    severity: str
    confidence: float
    impact_scope: str
    trend: str
    evidence_ids: list[str]
    summary: str


class DecisionAdvice(BaseModel):
    advice_key: str
    level: str
    action: str
    evidence_summary: str
    rationale: str


class EventDetail(BaseModel):
    event_id: str
    title: str
    occurred_at: str
    anomaly: Anomaly
    observation: ObservationWindow
    advices: list[DecisionAdvice]
    audit_count: int
    video_summary: dict[str, Any] = Field(default_factory=dict)
    ai_insight: dict[str, Any] = Field(default_factory=dict)


class OverviewResponse(BaseModel):
    current_risk_level: str
    today_anomaly_count: int
    key_alerts: list[dict[str, Any]]
    advice_cards: list[DecisionAdvice]
    trend_points: list[dict[str, Any]]
    modality_health: dict[str, str]
    ai_highlights: list[dict[str, Any]] = Field(default_factory=list)
    video_digest: dict[str, Any] = Field(default_factory=dict)
    process_board: list[dict[str, Any]] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    intent: str
    summary: str
    steps: list[str]
    payload: dict[str, Any]


class ReportResponse(BaseModel):
    id: int | None = None
    report_type: str
    title: str
    created_at: datetime | None = None
    period_label: str
    format: str
    content: str

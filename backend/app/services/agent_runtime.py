from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import FeedbackRecord
from ..schemas import ChatResponse
from .anomaly_runtime import detect_anomalies
from .decision_runtime import generate_advices
from .fusion_runtime import build_observation_windows
from .reports_runtime import current_label, save_report
from .tooling import run_tool


def _classify_intent(message: str) -> str:
    if "\u65e5\u62a5" in message:
        return "generate_daily_report"
    if "\u5468\u62a5" in message:
        return "generate_weekly_report"
    if "\u7b80\u62a5" in message:
        return "generate_incident_brief"
    if "\u5efa\u8bae" in message or "\u5904\u7f6e" in message:
        return "decision_advice"
    if "\u544a\u8b66" in message or "\u5f02\u5e38" in message:
        return "alert_analysis"
    return "duty_overview"


def handle_chat(session: Session, message: str) -> ChatResponse:
    intent = _classify_intent(message)
    windows = build_observation_windows()
    anomalies = detect_anomalies(windows)
    advice_map = {item.event_id: generate_advices(item) for item in anomalies}
    steps = ["understand_task", "select_skill", "call_tools", "compose_result"]

    if intent == "generate_daily_report":
        run_tool(session, "generate_daily_report", "daily_report_skill", "report_export", {"format": "markdown"})
        report = save_report(
            session,
            "daily_report",
            current_label("daily_report"),
            anomalies,
            [advice for items in advice_map.values() for advice in items],
        )
        return ChatResponse(intent=intent, summary="\u5df2\u751f\u6210\u4eca\u65e5\u65e5\u62a5\u3002", steps=steps, payload=report.model_dump(mode="json"))

    if intent == "generate_weekly_report":
        run_tool(session, "generate_weekly_report", "weekly_report_skill", "report_export", {"format": "markdown"})
        report = save_report(
            session,
            "weekly_report",
            current_label("weekly_report"),
            anomalies,
            [advice for items in advice_map.values() for advice in items],
        )
        return ChatResponse(intent=intent, summary="\u5df2\u751f\u6210\u672c\u5468\u5468\u62a5\u3002", steps=steps, payload=report.model_dump(mode="json"))

    if intent == "generate_incident_brief":
        target = anomalies[0]
        run_tool(session, "generate_incident_brief", "incident_brief_skill", "report_export", {"format": "html"})
        report = save_report(session, "incident_brief", target.event_id, [target], advice_map[target.event_id])
        return ChatResponse(intent=intent, summary=f"\u5df2\u751f\u6210\u4e8b\u4ef6 {target.event_id} \u7b80\u62a5\u3002", steps=steps, payload=report.model_dump(mode="json"))

    if intent == "decision_advice":
        target = anomalies[0]
        run_tool(session, "generate_decision_advice", "decision_advice_skill", "case_retrieval")
        feedback_weight = session.scalar(
            select(func.coalesce(func.sum(FeedbackRecord.weight_delta), 0.0)).where(FeedbackRecord.event_id == target.event_id)
        )
        advices = advice_map[target.event_id]
        if feedback_weight > 0:
            advices = sorted(advices, key=lambda item: item.level == "escalate", reverse=True)
        return ChatResponse(
            intent=intent,
            summary=f"\u5df2\u8f93\u51fa {target.event_id} \u7684\u5904\u7f6e\u5efa\u8bae\u3002",
            steps=steps,
            payload={"event_id": target.event_id, "advices": [item.model_dump() for item in advices]},
        )

    run_tool(session, "duty_overview", "duty_overview_skill", "metric_query")
    run_tool(session, "duty_overview", "duty_overview_skill", "alert_query")
    risk_counts = defaultdict(int)
    for anomaly in anomalies:
        risk_counts[anomaly.severity] += 1
    return ChatResponse(
        intent=intent,
        summary="\u5df2\u6c47\u603b\u4eca\u65e5\u5f02\u5e38\u60c5\u51b5\u4e0e\u98ce\u9669\u6001\u52bf\u3002",
        steps=steps,
        payload={"anomaly_count": len(anomalies), "risk_counts": dict(risk_counts), "top_events": [item.model_dump() for item in anomalies[:3]]},
    )

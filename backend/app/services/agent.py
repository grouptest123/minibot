from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import FeedbackRecord
from ..schemas import ChatResponse
from .anomaly import detect_anomalies
from .decision import generate_advices
from .fusion import build_observation_windows
from .reports import current_label, save_report
from .tooling import run_tool


def _classify_intent(message: str) -> str:
    if "日报" in message:
        return "generate_daily_report"
    if "周报" in message:
        return "generate_weekly_report"
    if "简报" in message:
        return "generate_incident_brief"
    if "建议" in message or "处置" in message:
        return "decision_advice"
    if "告警" in message or "异常" in message:
        return "alert_analysis"
    return "duty_overview"


def handle_chat(session: Session, message: str) -> ChatResponse:
    intent = _classify_intent(message)
    windows = build_observation_windows()
    anomalies = detect_anomalies(windows)
    advice_map = {item.event_id: generate_advices(item) for item in anomalies}
    steps = ["理解任务", "选择技能", "调用工具", "形成输出"]

    if intent == "generate_daily_report":
        run_tool(session, "生成日报", "daily_report_skill", "report_export", {"format": "markdown"})
        report = save_report(session, "daily_report", current_label("daily_report"), anomalies, [a for items in advice_map.values() for a in items])
        return ChatResponse(intent=intent, summary="已生成今日日报。", steps=steps, payload=report.model_dump(mode="json"))
    if intent == "generate_weekly_report":
        run_tool(session, "生成周报", "weekly_report_skill", "report_export", {"format": "markdown"})
        report = save_report(session, "weekly_report", current_label("weekly_report"), anomalies, [a for items in advice_map.values() for a in items])
        return ChatResponse(intent=intent, summary="已生成本周周报。", steps=steps, payload=report.model_dump(mode="json"))
    if intent == "generate_incident_brief":
        target = anomalies[0]
        run_tool(session, "生成事件简报", "incident_brief_skill", "report_export", {"format": "html"})
        report = save_report(session, "incident_brief", target.event_id, [target], advice_map[target.event_id])
        return ChatResponse(intent=intent, summary=f"已生成事件 {target.event_id} 简报。", steps=steps, payload=report.model_dump(mode="json"))
    if intent == "decision_advice":
        target = anomalies[0]
        run_tool(session, "生成建议", "decision_advice_skill", "case_retrieval")
        feedback_weight = session.scalar(select(func.coalesce(func.sum(FeedbackRecord.weight_delta), 0.0)).where(FeedbackRecord.event_id == target.event_id))
        advices = advice_map[target.event_id]
        if feedback_weight > 0:
            advices = sorted(advices, key=lambda item: item.level == "escalate", reverse=True)
        return ChatResponse(intent=intent, summary=f"已输出 {target.event_id} 的处置建议。", steps=steps, payload={"event_id": target.event_id, "advices": [item.model_dump() for item in advices]})

    run_tool(session, "值班总览", "duty_overview_skill", "metric_query")
    run_tool(session, "值班总览", "duty_overview_skill", "alert_query")
    risk_counts = defaultdict(int)
    for anomaly in anomalies:
        risk_counts[anomaly.severity] += 1
    return ChatResponse(
        intent=intent,
        summary="已汇总今日异常情况与风险态势。",
        steps=steps,
        payload={"anomaly_count": len(anomalies), "risk_counts": dict(risk_counts), "top_events": [item.model_dump() for item in anomalies[:3]]},
    )


from collections import Counter
from datetime import datetime

from sqlalchemy.orm import Session

from ..db import ReportRecord
from ..schemas import Anomaly, DecisionAdvice, ReportResponse


def _render_markdown(report_type: str, period_label: str, anomalies: list[Anomaly], advices: list[DecisionAdvice]) -> str:
    level_counter = Counter(item.severity for item in anomalies)
    lines = [
        f"# {report_type.upper()} - {period_label}",
        "",
        f"- 异常总数: {len(anomalies)}",
        f"- 风险概览: critical {level_counter.get('critical', 0)}, high {level_counter.get('high', 0)}, medium {level_counter.get('medium', 0)}",
        "",
        "## 重点事件",
    ]
    for anomaly in anomalies[:5]:
        lines.append(f"- {anomaly.title}: {anomaly.summary}")
    lines.extend(["", "## 处置建议"])
    for advice in advices[:6]:
        lines.append(f"- [{advice.level}] {advice.action} | 证据: {advice.evidence_summary}")
    lines.extend(["", "## 待跟踪事项", "- 核对服务恢复时间", "- 复盘人员值守连续性", ""])
    return "\n".join(lines)


def save_report(session: Session, report_type: str, period_label: str, anomalies: list[Anomaly], advices: list[DecisionAdvice]) -> ReportResponse:
    title = f"{period_label}{report_type}"
    content = _render_markdown(report_type, period_label, anomalies, advices)
    record = ReportRecord(report_type=report_type, title=title, period_label=period_label, format="markdown", content=content)
    session.add(record)
    session.commit()
    session.refresh(record)
    return ReportResponse(
        id=record.id,
        report_type=record.report_type,
        title=record.title,
        created_at=record.created_at,
        period_label=record.period_label,
        format=record.format,
        content=record.content,
    )


def build_html_preview(report: ReportResponse) -> str:
    return "".join(
        [
            "<html><head><meta charset='utf-8'><title>Report</title></head><body>",
            f"<h1>{report.title}</h1>",
            f"<pre>{report.content}</pre>",
            "</body></html>",
        ]
    )


def current_label(report_type: str) -> str:
    now = datetime.now()
    if report_type == "weekly_report":
        return f"{now.year}-W{now.isocalendar().week}"
    return now.strftime("%Y-%m-%d")

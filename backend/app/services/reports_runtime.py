from collections import Counter
from datetime import datetime
from html import escape
from io import BytesIO
import re

from sqlalchemy.orm import Session

from ..db import ReportRecord
from ..schemas import Anomaly, DecisionAdvice, ReportResponse


REPORT_TYPE_LABELS = {
    "daily_report": "值班日报",
    "weekly_report": "值班周报",
    "incident_brief": "事件简报",
}

ADVICE_LEVEL_LABELS = {
    "observe": "观察",
    "investigate": "排查",
    "escalate": "上报",
    "urgent_action": "紧急处置",
}


def _report_title(report_type: str, period_label: str) -> str:
    return f"{period_label} {REPORT_TYPE_LABELS.get(report_type, report_type)}"


def _render_markdown(report_type: str, period_label: str, anomalies: list[Anomaly], advices: list[DecisionAdvice]) -> str:
    level_counter = Counter(item.severity for item in anomalies)
    lines = [
        f"# {_report_title(report_type, period_label)}",
        "",
        f"- 统计区间：{period_label}",
        f"- 异常总数：{len(anomalies)}",
        f"- 风险概览：严重 {level_counter.get('critical', 0)}，高 {level_counter.get('high', 0)}，中 {level_counter.get('medium', 0)}",
        "",
        "## 重点事件" if report_type != "incident_brief" else "## 事件概况",
    ]
    for anomaly in anomalies[:5]:
        lines.append(f"- {anomaly.title}：{anomaly.summary}")

    lines.extend(["", "## 处置建议"])
    for advice in advices[:6]:
        lines.append(f"- [{ADVICE_LEVEL_LABELS.get(advice.level, advice.level)}] {advice.action}；证据：{advice.evidence_summary}")

    lines.extend(
        [
            "",
            "## 待跟踪事项",
            "- 核对服务恢复时间与影响范围",
            "- 复盘值守过程中的处置动作",
            "- 将本次经验沉淀到案例库与知识库",
            "",
        ]
    )
    return "\n".join(lines)


def save_report(
    session: Session,
    report_type: str,
    period_label: str,
    anomalies: list[Anomaly],
    advices: list[DecisionAdvice],
    report_format: str = "markdown",
) -> ReportResponse:
    title = _report_title(report_type, period_label)
    content = _render_markdown(report_type, period_label, anomalies, advices)
    record = ReportRecord(report_type=report_type, title=title, period_label=period_label, format=report_format, content=content)
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
    content = escape(report.content)
    return (
        "<html><head><meta charset='utf-8'><title>报告预览</title>"
        "<style>body{font-family:'Microsoft YaHei',sans-serif;padding:32px;color:#0f172a}"
        "pre{white-space:pre-wrap;line-height:1.7;background:#f8fafc;border:1px solid #e2e8f0;padding:20px;border-radius:16px}</style>"
        "</head><body>"
        f"<h1>{escape(report.title)}</h1>"
        f"<pre>{content}</pre>"
        "</body></html>"
    )


def current_label(report_type: str, start_date: str | None = None, end_date: str | None = None) -> str:
    if start_date and end_date:
        return start_date if start_date == end_date else f"{start_date} 至 {end_date}"
    if start_date:
        return start_date
    now = datetime.now()
    if report_type == "weekly_report":
        return f"{now.year}-W{now.isocalendar().week}"
    return now.strftime("%Y-%m-%d")


def _markdown_to_plain_text(text: str) -> str:
    plain = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    plain = re.sub(r"^\-\s*", "• ", plain, flags=re.MULTILINE)
    return plain.replace("`", "")


def build_doc_bytes(report: ReportResponse) -> bytes:
    html = (
        "<html><head><meta charset='utf-8'><style>"
        "body{font-family:'Microsoft YaHei',sans-serif;padding:28px;color:#111827}"
        "h1{font-size:24px}pre{white-space:pre-wrap;line-height:1.7;font-size:12pt}"
        "</style></head><body>"
        f"<h1>{escape(report.title)}</h1>"
        f"<pre>{escape(report.content)}</pre>"
        "</body></html>"
    )
    return html.encode("utf-8")


def build_pdf_bytes(report: ReportResponse) -> bytes:
    lines = [report.title, f"统计区间：{report.period_label}", ""] + _markdown_to_plain_text(report.content).splitlines()
    lines = [line[:42] for line in lines[:28]]

    stream_lines = ["BT", "/F1 16 Tf", "48 780 Td"]
    first = True
    for line in lines:
        encoded = line.encode("utf-16-be").hex().upper()
        if not first:
            stream_lines.append("0 -24 Td")
        stream_lines.append(f"<{encoded}> Tj")
        first = False
    stream_lines.append("ET")
    stream = "\n".join(stream_lines).encode("ascii")

    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type0 /BaseFont /STSong-Light /Encoding /UniGB-UCS2-H /DescendantFonts [6 0 R] >>",
        b"<< /Type /Font /Subtype /CIDFontType0 /BaseFont /STSong-Light /CIDSystemInfo << /Registry (Adobe) /Ordering (GB1) /Supplement 4 >> /FontDescriptor 7 0 R >>",
        b"<< /Type /FontDescriptor /FontName /STSong-Light /Flags 4 /ItalicAngle 0 /Ascent 880 /Descent -120 /CapHeight 700 /StemV 80 /FontBBox [-25 -254 1000 880] >>",
    ]

    buffer = BytesIO()
    buffer.write(b"%PDF-1.4\n%\xe4\xf6\xd6\xa4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(buffer.tell())
        buffer.write(f"{index} 0 obj\n".encode("ascii"))
        buffer.write(obj)
        buffer.write(b"\nendobj\n")

    xref_start = buffer.tell()
    buffer.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    buffer.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        buffer.write(f"{offset:010d} 00000 n \n".encode("ascii"))
    buffer.write(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF"
        ).encode("ascii")
    )
    return buffer.getvalue()


def export_report(report: ReportResponse, target_format: str) -> tuple[bytes, str, str]:
    if target_format == "doc":
        return build_doc_bytes(report), "application/msword", "doc"
    if target_format == "pdf":
        return build_pdf_bytes(report), "application/pdf", "pdf"
    if target_format == "html":
        return build_html_preview(report).encode("utf-8"), "text/html; charset=utf-8", "html"
    return report.content.encode("utf-8"), "text/markdown; charset=utf-8", "md"

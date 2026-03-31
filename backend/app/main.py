from contextlib import asynccontextmanager
from datetime import date, datetime, time
from pathlib import Path
from urllib.parse import quote

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from .core.config import settings
from .db import AuditLog, Base, FeedbackRecord, ReportRecord, engine, get_session
from .schemas import ChatRequest, ChatResponse, EventDetail, OverviewResponse, ReportResponse
from .services.agent_runtime import handle_chat
from .services.anomaly_runtime import detect_anomalies
from .services.decision_runtime import generate_advices
from .services.fusion_runtime import build_observation_windows
from .services.insight_runtime import build_ai_insight, build_overview_highlights, build_process_board
from .services.video_analysis_runtime import analyze_video_status
from .services.reports_runtime import build_html_preview, current_label, export_report, save_report
from .services.skills import list_skills
from .services.tooling import list_tools
from .mock_data import get_input_videos

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"
GENERATED_DIR = ROOT_DIR / "data" / "generated"
INPUT_VIDEO_DIR = ROOT_DIR / "data" / "input" / "video"


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def db_session():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


def _event_bundle(session: Session):
    windows = build_observation_windows()
    anomalies = detect_anomalies(windows)
    details = []
    for anomaly in anomalies:
        evidence_timestamps = [item.split(":", 1)[1] for item in anomaly.evidence_ids if ":" in item]
        observation = next(
            (
                window
                for window in windows
                if any(evidence.timestamp in evidence_timestamps for evidence in window.evidences)
            ),
            windows[0],
        )
        audit_count = session.query(AuditLog).count()
        advices = generate_advices(anomaly)
        details.append(
            EventDetail(
                event_id=anomaly.event_id,
                title=anomaly.title,
                occurred_at=observation.window_start,
                anomaly=anomaly,
                observation=observation,
                advices=advices,
                audit_count=audit_count,
                video_summary=analyze_video_status(),
                ai_insight=build_ai_insight(anomaly, observation, advices),
            )
        )
    return details


def _parse_date(text: str | None, *, end_of_day: bool = False) -> datetime | None:
    if not text:
        return None
    base = date.fromisoformat(text)
    return datetime.combine(base, time.max if end_of_day else time.min)


def _filter_events_by_range(events: list[EventDetail], start_date: str | None, end_date: str | None) -> list[EventDetail]:
    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date, end_of_day=True)
    if not start_dt and not end_dt:
        return events

    filtered = []
    for item in events:
        occurred_at = datetime.fromisoformat(item.occurred_at)
        if start_dt and occurred_at < start_dt:
            continue
        if end_dt and occurred_at > end_dt:
            continue
        filtered.append(item)
    return filtered


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.app_name}


@app.get("/api/overview", response_model=OverviewResponse)
def get_overview(session: Session = Depends(db_session)):
    events = _event_bundle(session)
    top_event = events[0]
    video_digest = analyze_video_status()
    serialized_events = [item.model_dump() for item in events]
    return OverviewResponse(
        current_risk_level="高",
        today_anomaly_count=len(events),
        key_alerts=[{"title": item.title, "severity": item.anomaly.severity, "time": item.occurred_at} for item in events[:3]],
        advice_cards=top_event.advices,
        trend_points=[{"time": item.occurred_at[11:16], "risk": idx + 2, "anomalies": 1} for idx, item in enumerate(events[:6])],
        modality_health={"video": "mock_online", "metrics": "online", "alerts": "online", "logs": "online", "screenshots": "online"},
        ai_highlights=build_overview_highlights(serialized_events),
        video_digest=video_digest,
        process_board=build_process_board(video_digest, serialized_events[0]),
    )


@app.get("/api/video-streams")
def list_video_streams():
    videos = get_input_videos()
    if not videos:
        return [
            {
                "stream_id": "mock-primary",
                "name": "值守主画面",
                "url": "",
                "status": "模拟接入",
                "source": "未检测到真实视频，当前展示模拟模式",
            },
            {
                "stream_id": "mock-secondary",
                "name": "辅助回放画面",
                "url": "",
                "status": "模拟接入",
                "source": "可将真实视频放入 data/input/video 后重启服务",
            },
        ]

    streams = []
    for idx, video in enumerate(videos[:2], start=1):
        streams.append(
            {
                "stream_id": f"video-{idx}",
                "name": "值守主画面" if idx == 1 else "辅助回放画面",
                "url": f"/input-video/{video.name}",
                "status": "在线",
                "source": video.name,
            }
        )
    if len(streams) == 1:
        streams.append({**streams[0], "stream_id": "video-2", "name": "辅助回放画面"})
    return streams


@app.get("/api/events")
def list_events(session: Session = Depends(db_session)):
    return [item.model_dump() for item in _event_bundle(session)]


@app.get("/api/events/{event_id}", response_model=EventDetail)
def get_event(event_id: str, session: Session = Depends(db_session)):
    for item in _event_bundle(session):
        if item.event_id == event_id:
            return item
    raise HTTPException(status_code=404, detail="event not found")


@app.get("/api/reports")
def list_reports(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    session: Session = Depends(db_session),
):
    records = session.scalars(select(ReportRecord).order_by(desc(ReportRecord.created_at))).all()
    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date, end_of_day=True)
    if start_dt or end_dt:
        filtered = []
        for item in records:
            if start_dt and item.created_at < start_dt:
                continue
            if end_dt and item.created_at > end_dt:
                continue
            filtered.append(item)
        records = filtered
    return [ReportResponse(id=item.id, report_type=item.report_type, title=item.title, created_at=item.created_at, period_label=item.period_label, format=item.format, content=item.content).model_dump(mode="json") for item in records]


@app.post("/api/reports/generate/{report_type}")
def generate_report(
    report_type: str,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    session: Session = Depends(db_session),
):
    events = _filter_events_by_range(_event_bundle(session), start_date, end_date)
    anomalies = [item.anomaly for item in events]
    advices = [advice for item in events for advice in item.advices]
    report = save_report(session, report_type, current_label(report_type, start_date, end_date), anomalies, advices)
    return {"report": report.model_dump(mode="json"), "html_preview": build_html_preview(report)}


@app.get("/api/reports/export/{report_id}")
def download_report(report_id: int, format: str = Query(default="pdf"), session: Session = Depends(db_session)):
    record = session.get(ReportRecord, report_id)
    if not record:
        raise HTTPException(status_code=404, detail="report not found")
    report = ReportResponse(
        id=record.id,
        report_type=record.report_type,
        title=record.title,
        created_at=record.created_at,
        period_label=record.period_label,
        format=record.format,
        content=record.content,
    )
    content, media_type, extension = export_report(report, format)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(record.title)}.{extension}"},
    )


@app.get("/api/audit-logs")
def list_audit_logs(session: Session = Depends(db_session)):
    rows = session.scalars(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(50)).all()
    return [{"id": row.id, "created_at": row.created_at.isoformat(), "task_name": row.task_name, "skill_name": row.skill_name, "tool_name": row.tool_name, "permission_level": row.permission_level, "parameter_summary": row.parameter_summary, "result_summary": row.result_summary, "blocked": row.blocked, "is_mock": row.is_mock} for row in rows]


@app.get("/api/tools")
def get_tools():
    return [tool.model_dump() for tool in list_tools()]


@app.get("/api/skills")
def get_skills():
    return [skill.model_dump() for skill in list_skills()]


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, session: Session = Depends(db_session)):
    return handle_chat(session, payload.message)


@app.post("/api/feedback/{event_id}/{advice_key}")
def feedback(event_id: str, advice_key: str, accepted: bool, session: Session = Depends(db_session)):
    record = FeedbackRecord(event_id=event_id, advice_key=advice_key, accepted=accepted, weight_delta=0.2 if accepted else -0.1)
    session.add(record)
    session.commit()
    return {"status": "recorded"}


@app.get("/")
def serve_index():
    if FRONTEND_DIST.exists():
        return FileResponse(FRONTEND_DIST / "index.html")
    raise HTTPException(status_code=404, detail="frontend dist not found")


@app.get("/assets/{asset_path:path}")
def serve_assets(asset_path: str):
    asset = FRONTEND_DIST / "assets" / asset_path
    if asset.exists():
        return FileResponse(asset)
    raise HTTPException(status_code=404, detail="asset not found")


@app.get("/generated/{generated_path:path}")
def serve_generated(generated_path: str):
    asset = GENERATED_DIR / generated_path
    if asset.exists() and asset.is_file():
        return FileResponse(asset)
    raise HTTPException(status_code=404, detail="generated asset not found")


@app.get("/input-video/{video_name:path}")
def serve_input_video(video_name: str):
    asset = INPUT_VIDEO_DIR / video_name
    if asset.exists() and asset.is_file():
        return FileResponse(asset)
    raise HTTPException(status_code=404, detail="input video not found")


@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="not found")
    target = FRONTEND_DIST / full_path
    if target.exists() and target.is_file():
        return FileResponse(target)
    if FRONTEND_DIST.exists():
        return FileResponse(FRONTEND_DIST / "index.html")
    raise HTTPException(status_code=404, detail="frontend dist not found")

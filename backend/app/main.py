from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
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
from .services.insight import build_ai_insight, build_overview_highlights, build_process_board
from .services.video_analysis import analyze_video_status
from .services.reports import build_html_preview, current_label, save_report
from .services.skills import list_skills
from .services.tooling import list_tools

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"
GENERATED_DIR = ROOT_DIR / "data" / "generated"


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
        current_risk_level="high",
        today_anomaly_count=len(events),
        key_alerts=[{"title": item.title, "severity": item.anomaly.severity, "time": item.occurred_at} for item in events[:3]],
        advice_cards=top_event.advices,
        trend_points=[{"time": item.occurred_at[11:16], "risk": idx + 2, "anomalies": 1} for idx, item in enumerate(events[:6])],
        modality_health={"video": "mock_online", "metrics": "online", "alerts": "online", "logs": "online", "screenshots": "online"},
        ai_highlights=build_overview_highlights(serialized_events),
        video_digest=video_digest,
        process_board=build_process_board(video_digest, serialized_events[0]),
    )


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
def list_reports(session: Session = Depends(db_session)):
    records = session.scalars(select(ReportRecord).order_by(desc(ReportRecord.created_at))).all()
    return [ReportResponse(id=item.id, report_type=item.report_type, title=item.title, created_at=item.created_at, period_label=item.period_label, format=item.format, content=item.content).model_dump(mode="json") for item in records]


@app.post("/api/reports/generate/{report_type}")
def generate_report(report_type: str, session: Session = Depends(db_session)):
    events = _event_bundle(session)
    anomalies = [item.anomaly for item in events]
    advices = [advice for item in events for advice in item.advices]
    report = save_report(session, report_type, current_label(report_type), anomalies, advices)
    return {"report": report.model_dump(mode="json"), "html_preview": build_html_preview(report)}


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

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "mock"
KB_DIR = ROOT / "data" / "knowledge"
CASE_DIR = ROOT / "data" / "cases"
INPUT_VIDEO_DIR = ROOT / "data" / "input" / "video"
GENERATED_VIDEO_DIR = ROOT / "data" / "generated" / "video_frames"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def get_alerts() -> list[dict[str, Any]]:
    return load_json(DATA_DIR / "alerts" / "alerts.json")


def get_logs() -> list[dict[str, Any]]:
    return load_json(DATA_DIR / "logs" / "service_logs.json")


def get_metrics() -> list[dict[str, Any]]:
    return load_json(DATA_DIR / "metrics" / "metrics.json")


def get_screenshots() -> list[dict[str, Any]]:
    return load_json(DATA_DIR / "screenshots" / "screenshots.json")


def get_video_observations() -> list[dict[str, Any]]:
    return load_json(DATA_DIR / "video" / "staff_absence_mock.json")


def get_notes() -> list[dict[str, Any]]:
    return load_json(DATA_DIR / "notes" / "notes.json")


def get_cases() -> list[dict[str, Any]]:
    return load_json(CASE_DIR / "historical_cases.json")


def get_knowledge_docs() -> list[dict[str, str]]:
    docs = []
    for path in KB_DIR.glob("*.md"):
        docs.append({"name": path.stem, "content": load_text(path)})
    return docs


def get_input_videos() -> list[Path]:
    INPUT_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    return sorted([path for path in INPUT_VIDEO_DIR.iterdir() if path.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"}])

from datetime import datetime
from pathlib import Path
from statistics import mean

from ..mock_data import GENERATED_VIDEO_DIR, get_input_videos, get_video_observations

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - graceful fallback when deps are absent
    cv2 = None
    np = None


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


_VIDEO_CACHE: dict[str, dict] = {}


def _save_frame(image, output_path: Path, label: str):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame = image.copy()
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = int(w * 0.28), int(h * 0.2), int(w * 0.72), int(h * 0.9)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (20, 120, 240), 3)
    cv2.putText(frame, label, (x1, max(30, y1 - 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 120, 240), 2)
    cv2.imwrite(str(output_path), frame)


def _analyze_real_video(path: Path) -> dict:
    if cv2 is None or np is None:
        return {}

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {}

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    sample_gap = max(1, int(fps))

    frames: list[tuple[int, str, float, str, str]] = []
    baseline = None
    previous_roi = None
    flagged = []
    GENERATED_VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    index = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if index % sample_gap != 0:
            index += 1
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape[:2]
        x1, y1, x2, y2 = int(w * 0.28), int(h * 0.2), int(w * 0.72), int(h * 0.9)
        roi = gray[y1:y2, x1:x2]
        if baseline is None:
            baseline = roi.astype("float32")

        diff = cv2.absdiff(roi, baseline.astype("uint8"))
        occupancy_score = float(np.mean(diff)) / 255.0
        motion_score = 0.0 if previous_roi is None else float(np.mean(cv2.absdiff(roi, previous_roi))) / 255.0
        variance_score = float(np.std(gray)) / 255.0
        previous_roi = roi

        second = int(index / fps)
        timestamp = f"00:{second // 60:02d}:{second % 60:02d}"
        status = "在岗"
        note = "值守区域检测正常"
        confidence = 0.76

        if variance_score < 0.10:
            status = "画面轻度遮挡"
            note = "全画面纹理过低，疑似镜头遮挡或虚焦"
            confidence = 0.7
        elif occupancy_score < 0.055:
            status = "离岗"
            note = "值守区域与空岗基线接近，疑似人员离开工位"
            confidence = 0.84
        elif motion_score < 0.01 and occupancy_score > 0.08:
            status = "静止过久"
            note = "值守区域连续低运动，疑似静止过久"
            confidence = 0.74

        frames.append((second, status, round(confidence, 2), note, timestamp))
        if status != "在岗":
            image_name = f"{path.stem}_{second:04d}.jpg"
            output = GENERATED_VIDEO_DIR / image_name
            _save_frame(frame, output, status)
            flagged.append(
                {
                    "timestamp": timestamp,
                    "status": status,
                    "confidence": round(confidence, 2),
                    "note": note,
                    "image_url": f"/generated/video_frames/{image_name}",
                    "source_mode": "real_video",
                }
            )
        index += 1

    cap.release()
    if not frames:
        return {}

    latest_status = frames[-1][1]
    confidences = [item[2] for item in frames]
    absence_count = len([item for item in frames if item[1] == "离岗"])
    still_count = len([item for item in frames if item[1] == "静止过久"])
    blocked_count = len([item for item in frames if item[1] == "画面轻度遮挡"])

    return {
        "source": str(path.name),
        "source_mode": "real_video",
        "summary": f"已分析视频 {path.name}，抽取 {len(frames)} 个时间点，定位 {len(flagged)} 处异常片段。",
        "risk_level": "high" if absence_count or blocked_count else "medium" if still_count else "low",
        "average_confidence": round(mean(confidences), 2),
        "absence_count": absence_count,
        "still_count": still_count,
        "blocked_count": blocked_count,
        "latest_status": latest_status,
        "timeline": flagged or [
            {
                "timestamp": item[4],
                "status": item[1],
                "confidence": item[2],
                "note": item[3],
                "image_url": "",
                "source_mode": "real_video",
            }
            for item in frames[:4]
        ],
        "analysis_method": [
            "空岗基线差分",
            "值守区域运动检测",
            "画面纹理遮挡判定",
        ],
        "watch_area_hint": "建议固定摄像头并覆盖值守座位主体区域",
    }


def analyze_video_status() -> dict:
    videos = get_input_videos()
    if videos:
        video = videos[0]
        cache_key = f"{video.resolve()}::{video.stat().st_mtime_ns}"
        cached = _VIDEO_CACHE.get(cache_key)
        if cached:
            return cached

        real_result = _analyze_real_video(video)
        if real_result:
            _VIDEO_CACHE.clear()
            _VIDEO_CACHE[cache_key] = real_result
            return real_result

    observations = sorted(get_video_observations(), key=lambda item: item["timestamp"])
    statuses = [item["status"] for item in observations]
    confidences = [float(item.get("confidence", 0.0)) for item in observations]
    absence_events = [item for item in observations if "离岗" in item["status"]]
    still_events = [item for item in observations if "静止" in item["status"]]
    blocked_events = [item for item in observations if "遮挡" in item["status"] or "不可用" in item["status"]]

    timeline = []
    for item in observations:
        timeline.append(
            {
                "timestamp": item["timestamp"],
                "status": item["status"],
                "confidence": round(float(item.get("confidence", 0.0)), 2),
                "note": item.get("note", ""),
            }
        )

    risk_level = "low"
    if absence_events or blocked_events:
        risk_level = "high"
    elif still_events:
        risk_level = "medium"

    result = {
        "source": "offline_video_mock",
        "source_mode": "mock",
        "summary": "检测到人员短时离岗，随后恢复在岗。",
        "risk_level": risk_level,
        "average_confidence": round(mean(confidences), 2) if confidences else 0.0,
        "absence_count": len(absence_events),
        "still_count": len(still_events),
        "blocked_count": len(blocked_events),
        "latest_status": statuses[-1] if statuses else "unknown",
        "timeline": timeline,
        "analysis_method": [
            "值守区域存在性判断",
            "连续帧静止时长统计",
            "遮挡/不可用规则检测",
        ],
        "watch_area_hint": "当前为 mock 视频结果，请将真实视频放入 data/input/video 目录后重启服务",
    }
    _VIDEO_CACHE.clear()
    _VIDEO_CACHE["mock"] = result
    return result

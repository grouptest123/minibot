from datetime import datetime
from pathlib import Path
from statistics import mean

from ..mock_data import GENERATED_VIDEO_DIR, get_input_videos, get_video_observations

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None
    np = None


_VIDEO_CACHE: dict[str, dict] = {}


def _save_frame(image, output_path: Path, label: str):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame = image.copy()
    height, width = frame.shape[:2]
    x1, y1, x2, y2 = int(width * 0.28), int(height * 0.2), int(width * 0.72), int(height * 0.9)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (20, 120, 240), 3)
    cv2.putText(frame, label, (x1, max(30, y1 - 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 120, 240), 2)
    cv2.imwrite(str(output_path), frame)


def _format_clock(second: int) -> str:
    return f"00:{second // 60:02d}:{second % 60:02d}"


def _analyze_real_video(path: Path) -> dict:
    if cv2 is None or np is None:
        return {}

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {}

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    sample_gap = max(1, int(fps))
    baseline = None
    previous_roi = None
    frames: list[dict] = []
    flagged_frames: list[dict] = []
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
        height, width = gray.shape[:2]
        x1, y1, x2, y2 = int(width * 0.28), int(height * 0.2), int(width * 0.72), int(height * 0.9)
        roi = gray[y1:y2, x1:x2]
        if baseline is None:
            baseline = roi.astype("float32")

        diff = cv2.absdiff(roi, baseline.astype("uint8"))
        occupancy_score = float(np.mean(diff)) / 255.0
        motion_score = 0.0 if previous_roi is None else float(np.mean(cv2.absdiff(roi, previous_roi))) / 255.0
        variance_score = float(np.std(gray)) / 255.0
        previous_roi = roi

        second = int(index / fps)
        status = "在岗"
        note = "值守区域保持正常活动"
        confidence = 0.76

        if variance_score < 0.10:
            status = "画面轻度遮挡"
            note = "整帧纹理过低，疑似镜头被遮挡或画面失焦"
            confidence = 0.70
        elif occupancy_score < 0.055:
            status = "离岗"
            note = "值守区域与空岗基线接近，疑似人员离开工位"
            confidence = 0.84
        elif motion_score < 0.01 and occupancy_score > 0.08:
            status = "静止过久"
            note = "值守区域持续低活动，疑似长时间静止"
            confidence = 0.74

        item = {
            "timestamp": _format_clock(second),
            "status": status,
            "confidence": round(confidence, 2),
            "note": note,
            "source_mode": "真实视频",
        }
        frames.append(item)
        if status != "在岗":
            image_name = f"{path.stem}_{second:04d}.jpg"
            output = GENERATED_VIDEO_DIR / image_name
            _save_frame(frame, output, status)
            flagged_frames.append({**item, "image_url": f"/generated/video_frames/{image_name}"})
        index += 1

    cap.release()
    if not frames:
        return {}

    absence_count = sum(1 for item in frames if item["status"] == "离岗")
    still_count = sum(1 for item in frames if item["status"] == "静止过久")
    blocked_count = sum(1 for item in frames if item["status"] == "画面轻度遮挡")
    risk_level = "高" if absence_count or blocked_count else "中" if still_count else "低"

    return {
        "source": path.name,
        "source_mode": "真实视频",
        "summary": f"已分析视频 {path.name}，抽样 {len(frames)} 个时间点，定位 {len(flagged_frames)} 处异常片段。",
        "risk_level": risk_level,
        "average_confidence": round(mean(item["confidence"] for item in frames), 2),
        "absence_count": absence_count,
        "still_count": still_count,
        "blocked_count": blocked_count,
        "latest_status": frames[-1]["status"],
        "timeline": flagged_frames or frames[:4],
        "analysis_method": ["空岗基线差分", "值守区域运动检测", "画面纹理遮挡判定"],
        "watch_area_hint": "建议使用固定机位并覆盖值守座位主体区域",
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }


def analyze_video_status() -> dict:
    videos = get_input_videos()
    if videos:
        video = videos[0]
        cache_key = f"{video.resolve()}::{video.stat().st_mtime_ns}"
        cached = _VIDEO_CACHE.get(cache_key)
        if cached:
            return cached

        result = _analyze_real_video(video)
        if result:
            _VIDEO_CACHE.clear()
            _VIDEO_CACHE[cache_key] = result
            return result

    observations = sorted(get_video_observations(), key=lambda item: item["timestamp"])
    confidences = [float(item.get("confidence", 0.0)) for item in observations]
    timeline = [
        {
            "timestamp": item["timestamp"],
            "status": item["status"],
            "confidence": round(float(item.get("confidence", 0.0)), 2),
            "note": item.get("note", ""),
            "image_url": item.get("image_url", ""),
            "source_mode": "模拟数据",
        }
        for item in observations
    ]
    absence_count = sum(1 for item in observations if "离岗" in item["status"])
    still_count = sum(1 for item in observations if "静止" in item["status"])
    blocked_count = sum(1 for item in observations if "遮挡" in item["status"] or "不可用" in item["status"])
    risk_level = "高" if absence_count or blocked_count else "中" if still_count else "低"

    result = {
        "source": "离线视频样例",
        "source_mode": "模拟数据",
        "summary": "检测到值守人员短时离岗，随后恢复在岗。",
        "risk_level": risk_level,
        "average_confidence": round(mean(confidences), 2) if confidences else 0.0,
        "absence_count": absence_count,
        "still_count": still_count,
        "blocked_count": blocked_count,
        "latest_status": observations[-1]["status"] if observations else "未知",
        "timeline": timeline,
        "analysis_method": ["值守区域存在性判断", "连续静止时长统计", "遮挡或不可用规则检测"],
        "watch_area_hint": "当前为模拟检测结果，可将真实视频放入 data/input/video 目录后重启服务",
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    _VIDEO_CACHE.clear()
    _VIDEO_CACHE["mock"] = result
    return result

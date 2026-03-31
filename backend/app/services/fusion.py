from collections import defaultdict
from datetime import datetime, timedelta

from ..mock_data import get_alerts, get_logs, get_metrics, get_notes, get_screenshots, get_video_observations
from ..schemas import Evidence, ObservationWindow


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def build_observation_windows() -> list[ObservationWindow]:
    buckets: dict[datetime, list[Evidence]] = defaultdict(list)

    for alert in get_alerts():
        minute = _parse(alert["timestamp"]).replace(second=0)
        buckets[minute].append(Evidence(source="alert", timestamp=alert["timestamp"], summary=alert["summary"], detail=alert))
    for log in get_logs():
        minute = _parse(log["timestamp"]).replace(second=0)
        buckets[minute].append(Evidence(source="log", timestamp=log["timestamp"], summary=log["message"], detail=log))
    for metric in get_metrics():
        minute = _parse(metric["timestamp"]).replace(second=0)
        feature = f"cpu={metric['cpu']} memory={metric['memory']} latency={metric['latency_ms']}"
        buckets[minute].append(Evidence(source="metric", timestamp=metric["timestamp"], summary=feature, detail=metric))
    for shot in get_screenshots():
        minute = _parse(shot["timestamp"]).replace(second=0)
        buckets[minute].append(Evidence(source="screenshot", timestamp=shot["timestamp"], summary=shot["summary"], detail=shot))
    for video in get_video_observations():
        minute = _parse(video["timestamp"]).replace(second=0)
        buckets[minute].append(Evidence(source="video", timestamp=video["timestamp"], summary=video["status"], detail=video))
    for note in get_notes():
        minute = _parse(note["timestamp"]).replace(second=0)
        buckets[minute].append(Evidence(source="note", timestamp=note["timestamp"], summary=note["content"], detail=note))

    windows: list[ObservationWindow] = []
    for minute, evidences in sorted(buckets.items()):
        modalities = sorted({item.source for item in evidences})
        features = []
        if any(item.source == "video" and "离岗" in item.summary for item in evidences):
            features.append("人员离岗")
        if any(item.source == "metric" and ("cpu=92" in item.summary or "latency=1680" in item.summary) for item in evidences):
            features.append("指标越阈值")
        if any(item.source == "log" and ("timeout" in item.summary.lower() or "连接池耗尽" in item.summary) for item in evidences):
            features.append("日志异常")
        if any(item.source == "screenshot" and "异常弹窗" in item.summary for item in evidences):
            features.append("页面异常")
        if any(item.source == "alert" and item.detail.get("level") in {"high", "critical"} for item in evidences):
            features.append("高等级告警")

        risk_level = "low"
        if len(features) >= 4:
            risk_level = "high"
        elif len(features) >= 2:
            risk_level = "medium"

        windows.append(
            ObservationWindow(
                window_start=minute.isoformat(),
                window_end=(minute + timedelta(minutes=1)).isoformat(),
                modalities=modalities,
                key_features=features or ["状态平稳"],
                risk_level=risk_level,
                evidences=evidences,
            )
        )
    return windows


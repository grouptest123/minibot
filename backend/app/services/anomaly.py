from ..schemas import Anomaly, ObservationWindow


def detect_anomalies(windows: list[ObservationWindow]) -> list[Anomaly]:
    anomalies: list[Anomaly] = []
    for idx, window in enumerate(windows, start=1):
        features = set(window.key_features)
        if "状态平稳" in features:
            continue

        if "人员离岗" in features:
            anomalies.append(
                Anomaly(
                    event_id=f"EVT-{idx:03d}-P",
                    title="人员值守异常",
                    category="人员值守异常",
                    severity="high" if window.risk_level == "high" else "medium",
                    confidence=0.87,
                    impact_scope="值班岗",
                    trend="risk_up",
                    evidence_ids=[f"{ev.source}:{ev.timestamp}" for ev in window.evidences if ev.source == "video"],
                    summary="视频观测到值守位短时离岗，需结合其他模态确认是否影响处置时效。",
                )
            )

        if {"指标越阈值", "日志异常", "高等级告警"} & features:
            anomalies.append(
                Anomaly(
                    event_id=f"EVT-{idx:03d}-S",
                    title="服务运行异常",
                    category="设备/服务异常",
                    severity="critical" if len(features) >= 4 else "high",
                    confidence=0.91,
                    impact_scope="交易服务与监控页面",
                    trend="risk_up" if "高等级告警" in features else "stable",
                    evidence_ids=[f"{ev.source}:{ev.timestamp}" for ev in window.evidences if ev.source in {"metric", "log", "alert", "screenshot"}],
                    summary="CPU、延迟、日志和告警在同一窗口内共振，符合服务退化特征。",
                )
            )
    return anomalies


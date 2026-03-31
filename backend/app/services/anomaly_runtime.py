from ..schemas import Anomaly, ObservationWindow


def detect_anomalies(windows: list[ObservationWindow]) -> list[Anomaly]:
    anomalies: list[Anomaly] = []
    for idx, window in enumerate(windows, start=1):
        features = set(window.key_features)
        if "状态平稳" in features:
            continue

        if {"人员离岗", "人员静止过久", "视频不可用"} & features:
            severity = "high" if {"人员离岗", "视频不可用"} & features else "medium"
            anomalies.append(
                Anomaly(
                    event_id=f"EVT-{idx:03d}-P",
                    title="人员值守异常",
                    category="人员值守异常",
                    severity=severity,
                    confidence=0.88 if "人员离岗" in features else 0.74,
                    impact_scope="值班岗位",
                    trend="risk_up",
                    evidence_ids=[f"{ev.source}:{ev.timestamp}" for ev in window.evidences if ev.source in {"video", "note"}],
                    summary="视频分析显示值守区域存在短时离岗信号，需结合人工备注确认影响时长。",
                )
            )

        system_features = {"CPU越阈值", "延迟越阈值", "日志异常", "高等级告警", "页面异常"}
        if system_features & features:
            severity = "critical" if len(system_features & features) >= 4 else "high"
            anomalies.append(
                Anomaly(
                    event_id=f"EVT-{idx:03d}-S",
                    title="服务运行异常",
                    category="设备/服务异常",
                    severity=severity,
                    confidence=0.92,
                    impact_scope="交易服务与监控页面",
                    trend="risk_up",
                    evidence_ids=[f"{ev.source}:{ev.timestamp}" for ev in window.evidences if ev.source in {"metric", "log", "alert", "screenshot"}],
                    summary="指标、日志、告警和页面异常同窗共振，符合服务性能退化模式。",
                )
            )
    return anomalies


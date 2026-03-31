from ..schemas import Anomaly, DecisionAdvice, ObservationWindow
from .retrieval import retrieve_context
from .video_analysis_runtime import analyze_video_status


def _severity_label(value: str) -> str:
    mapping = {"critical": "严重", "high": "高", "medium": "中", "low": "低"}
    return mapping.get(value, value)


def build_ai_insight(anomaly: Anomaly, observation: ObservationWindow, advices: list[DecisionAdvice]) -> dict:
    query = f"{anomaly.title} {anomaly.summary} {' '.join(observation.key_features)}"
    context = retrieve_context(query)
    video = analyze_video_status()
    top_case = context["cases"][0]["title"] if context["cases"] else "未命中案例"
    top_rule = context["knowledge"][0]["title"] if context["knowledge"] else "未命中知识条目"

    hypothesis = (
        "数据库连接池与服务实例承压，导致延迟抬升和异常告警叠加"
        if anomaly.category == "设备/服务异常"
        else "值班人员短时离岗，但已恢复在岗"
    )
    return {
        "judgement": anomaly.title,
        "confidence": anomaly.confidence,
        "hypothesis": hypothesis,
        "reasoning": [
            f"任务理解：识别出 {anomaly.category}，需要形成可执行处置建议。",
            f"证据归并：当前窗口包含 {', '.join(observation.modalities)} 共 {len(observation.evidences)} 条证据。",
            f"知识对齐：命中知识库“{top_rule}”，命中案例“{top_case}”。",
            f"行动建议：优先执行“{advices[0].action}”。" if advices else "行动建议：继续观察。",
        ],
        "knowledge_hits": context["knowledge"],
        "case_hits": context["cases"],
        "process_flow": [
            {"stage": "任务理解", "status": "已完成", "detail": f"识别任务目标为 {anomaly.category} 分析与建议输出。"},
            {"stage": "多模态融合", "status": "已完成", "detail": f"融合 {', '.join(observation.modalities)} 共 {len(observation.evidences)} 条证据。"},
            {"stage": "视频检测", "status": "已完成", "detail": f"视频风险 {video['risk_level']}，最新状态为 {video['latest_status']}。"},
            {"stage": "知识检索", "status": "已完成", "detail": f"命中 {len(context['knowledge'])} 条知识、{len(context['cases'])} 条案例。"},
            {"stage": "决策生成", "status": "已完成", "detail": advices[0].action if advices else "继续观察"},
        ],
        "fusion_timeline": [
            {"time": evidence.timestamp[11:16], "source": evidence.source, "label": evidence.summary, "risk": observation.risk_level}
            for evidence in observation.evidences
        ],
        "signal_strength": [
            {"name": "视频信号", "value": 0.76 if "video" in observation.modalities else 0.2},
            {"name": "指标信号", "value": 0.91 if "metric" in observation.modalities else 0.2},
            {"name": "日志信号", "value": 0.84 if "log" in observation.modalities else 0.2},
            {"name": "告警信号", "value": 0.88 if "alert" in observation.modalities else 0.2},
            {"name": "知识支撑", "value": 0.72 if context["knowledge"] else 0.15},
        ],
        "video_signal": {
            "risk_level": video["risk_level"],
            "latest_status": video["latest_status"],
            "absence_count": video["absence_count"],
        },
    }


def build_overview_highlights(events: list[dict]) -> list[dict]:
    return [
        {
            "title": item["title"],
            "judgement": item["ai_insight"]["judgement"],
            "hypothesis": item["ai_insight"]["hypothesis"],
            "confidence": item["ai_insight"]["confidence"],
        }
        for item in events[:3]
    ]


def build_process_board(video_digest: dict, first_event: dict) -> list[dict]:
    insight = first_event["ai_insight"]
    return [
        {
            "title": "感知接入",
            "metric": "6 路",
            "detail": "视频、指标、日志、告警、截图、人工备注",
            "tone": "neutral",
        },
        {
            "title": "视频检测",
            "metric": f"{video_digest['absence_count']} 次离岗",
            "detail": f"最新状态：{video_digest['latest_status']}",
            "tone": "high" if video_digest["risk_level"] == "高" else "accent",
        },
        {
            "title": "融合研判",
            "metric": _severity_label(first_event["anomaly"]["severity"]),
            "detail": insight["hypothesis"],
            "tone": "high",
        },
        {
            "title": "决策输出",
            "metric": f"{len(first_event['advices'])} 条",
            "detail": first_event["advices"][0]["action"] if first_event["advices"] else "继续观察",
            "tone": "accent",
        },
    ]

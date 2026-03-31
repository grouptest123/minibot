from ..schemas import Anomaly, DecisionAdvice, ObservationWindow
from .retrieval import retrieve_context
from .video_analysis import analyze_video_status


def build_ai_insight(anomaly: Anomaly, observation: ObservationWindow, advices: list[DecisionAdvice]) -> dict:
    query = f"{anomaly.title} {anomaly.summary} {' '.join(observation.key_features)}"
    context = retrieve_context(query)
    video = analyze_video_status()
    top_case = context["cases"][0]["title"] if context["cases"] else "无匹配案例"
    top_rule = context["knowledge"][0]["title"] if context["knowledge"] else "无匹配知识"

    hypothesis = "数据库连接池和服务实例压力叠加" if anomaly.category == "设备/服务异常" else "值班人员短时离岗但已恢复"
    return {
        "judgement": anomaly.title,
        "confidence": anomaly.confidence,
        "hypothesis": hypothesis,
        "reasoning": [
            f"任务理解：识别 {anomaly.category} 并给出处置建议",
            f"证据归并：当前窗口包含 {', '.join(observation.modalities)} 共 {len(observation.evidences)} 条证据",
            f"知识对齐：命中知识库 {top_rule}，命中案例 {top_case}",
            f"行动建议：优先执行 {advices[0].action}" if advices else "行动建议：继续观察",
        ],
        "knowledge_hits": context["knowledge"],
        "case_hits": context["cases"],
        "process_flow": [
            {
                "stage": "任务理解",
                "status": "done",
                "detail": f"识别任务目标为 {anomaly.category} 分析与处置输出",
            },
            {
                "stage": "多模态融合",
                "status": "done",
                "detail": f"融合 {', '.join(observation.modalities)} 共 {len(observation.evidences)} 条证据",
            },
            {
                "stage": "视频检测",
                "status": "done",
                "detail": f"视频风险 {video['risk_level']}，最新状态 {video['latest_status']}",
            },
            {
                "stage": "知识检索",
                "status": "done",
                "detail": f"命中 {len(context['knowledge'])} 条知识、{len(context['cases'])} 条案例",
            },
            {
                "stage": "生成建议",
                "status": "done",
                "detail": advices[0].action if advices else "继续观察",
            },
        ],
        "fusion_timeline": [
            {
                "time": evidence.timestamp[11:16],
                "source": evidence.source,
                "label": evidence.summary,
                "risk": observation.risk_level,
            }
            for evidence in observation.evidences
        ],
        "signal_strength": [
            {"name": "video", "value": 0.76 if "video" in observation.modalities else 0.2},
            {"name": "metrics", "value": 0.91 if "metric" in observation.modalities else 0.2},
            {"name": "logs", "value": 0.84 if "log" in observation.modalities else 0.2},
            {"name": "alerts", "value": 0.88 if "alert" in observation.modalities else 0.2},
            {"name": "knowledge", "value": 0.72 if context["knowledge"] else 0.15},
        ],
        "video_signal": {
            "risk_level": video["risk_level"],
            "latest_status": video["latest_status"],
            "absence_count": video["absence_count"],
        },
    }


def build_overview_highlights(events: list[dict]) -> list[dict]:
    highlights = []
    for item in events[:3]:
        insight = item["ai_insight"]
        highlights.append(
            {
                "title": item["title"],
                "judgement": insight["judgement"],
                "hypothesis": insight["hypothesis"],
                "confidence": insight["confidence"],
            }
        )
    return highlights


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
            "detail": f"最新状态 {video_digest['latest_status']}",
            "tone": video_digest["risk_level"],
        },
        {
            "title": "融合研判",
            "metric": first_event["anomaly"]["severity"],
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

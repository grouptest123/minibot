from ..schemas import Anomaly, DecisionAdvice
from .retrieval import retrieve_context


def generate_advices(anomaly: Anomaly) -> list[DecisionAdvice]:
    context = retrieve_context(f"{anomaly.title} {anomaly.summary}")
    top_rule = context["knowledge"][0]["title"] if context["knowledge"] else "值班制度"
    top_case = context["cases"][0]["title"] if context["cases"] else "历史案例"

    if anomaly.category == "人员值守异常":
        return [
            DecisionAdvice(
                advice_key=f"{anomaly.event_id}-investigate",
                level="investigate",
                action="联系值班人员并复核当前在岗状态",
                evidence_summary="视频存在离岗信号，人工备注显示已在 14:03 返回座位。",
                rationale=f"依据知识条目《{top_rule}》，先人工复核并确认是否需要换岗补位。",
            ),
            DecisionAdvice(
                advice_key=f"{anomaly.event_id}-observe",
                level="observe",
                action="列入日报重点并持续观察 30 分钟",
                evidence_summary="本次异常时长较短，但会影响值守连续性考核。",
                rationale="当前已恢复在岗，可先观察是否再次出现离岗或静止过久信号。",
            ),
        ]

    return [
        DecisionAdvice(
            advice_key=f"{anomaly.event_id}-investigate",
            level="investigate",
            action="排查交易服务实例、连接池和慢查询",
            evidence_summary="CPU、延迟、超时日志和高等级告警同时出现。",
            rationale=f"相似案例《{top_case}》显示连接池和慢查询是首要排查点。",
        ),
        DecisionAdvice(
            advice_key=f"{anomaly.event_id}-escalate",
            level="escalate",
            action="通知班组长并生成事件简报",
            evidence_summary="异常已跨指标、日志、页面和告警多个模态。",
            rationale=f"依据《{top_rule}》中的升级流程，多模态共振异常应立即上报。",
        ),
    ]

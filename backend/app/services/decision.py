from ..mock_data import get_cases, get_knowledge_docs
from ..schemas import Anomaly, DecisionAdvice


def generate_advices(anomaly: Anomaly) -> list[DecisionAdvice]:
    kb = get_knowledge_docs()
    cases = get_cases()
    kb_hint = kb[0]["name"] if kb else "值班制度"
    case_hint = cases[0]["title"] if cases else "历史案例"

    advices: list[DecisionAdvice] = []
    if anomaly.category == "人员值守异常":
        advices.append(
            DecisionAdvice(
                advice_key=f"{anomaly.event_id}-observe",
                level="investigate",
                action="联系值班人员并核对当前岗位状态",
                evidence_summary="视频出现离岗状态，人工备注显示 14:03 有临时离席说明。",
                rationale=f"参考知识库《{kb_hint}》中的值守要求，先人工复核避免误报。",
            )
        )
        advices.append(
            DecisionAdvice(
                advice_key=f"{anomaly.event_id}-report",
                level="observe",
                action="列入日报重点跟踪",
                evidence_summary="事件持续时间短，但涉及值守连续性。",
                rationale="事件尚未升级为生产故障，建议纳入日报并保持观察。",
            )
        )
    else:
        advices.append(
            DecisionAdvice(
                advice_key=f"{anomaly.event_id}-investigate",
                level="investigate",
                action="排查交易服务实例与数据库连接池",
                evidence_summary="CPU、延迟、超时日志、页面异常弹窗和 critical 告警同时出现。",
                rationale=f"历史案例《{case_hint}》中出现过相似模式，首要检查连接池和慢查询。",
            )
        )
        advices.append(
            DecisionAdvice(
                advice_key=f"{anomaly.event_id}-escalate",
                level="escalate",
                action="通知班组长并生成事件简报",
                evidence_summary="异常已影响多个模态，风险处于上升态势。",
                rationale="多证据链收敛后应同步上报，便于协同处置与追踪。",
            )
        )
    return advices


import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from ..db import AuditLog
from ..mock_data import get_alerts, get_cases, get_logs, get_metrics, get_screenshots
from ..schemas import ToolDefinition


@dataclass
class ToolSpec:
    name: str
    description: str
    permission_level: str
    supports_mock: bool
    runner: Callable[[dict[str, Any]], Any]


def _read_metrics(_: dict[str, Any]) -> Any:
    return get_metrics()


def _read_alerts(_: dict[str, Any]) -> Any:
    return get_alerts()


def _read_logs(_: dict[str, Any]) -> Any:
    return get_logs()


def _read_screenshots(_: dict[str, Any]) -> Any:
    return get_screenshots()


def _retrieve_cases(_: dict[str, Any]) -> Any:
    return get_cases()


def _export_report(params: dict[str, Any]) -> Any:
    return {"status": "planned", "export_format": params.get("format", "html"), "note": "demo 模式仅展示执行计划"}


TOOL_REGISTRY: dict[str, ToolSpec] = {
    "metric_query": ToolSpec("metric_query", "查询指标数据", "read_only", True, _read_metrics),
    "alert_query": ToolSpec("alert_query", "查询告警数据", "read_only", True, _read_alerts),
    "log_search": ToolSpec("log_search", "检索日志文本", "read_only", True, _read_logs),
    "screenshot_reader": ToolSpec("screenshot_reader", "读取截图结果", "read_only", True, _read_screenshots),
    "case_retrieval": ToolSpec("case_retrieval", "检索历史案例", "read_only", True, _retrieve_cases),
    "report_export": ToolSpec("report_export", "导出报告", "controlled_exec", True, _export_report),
}


def list_tools() -> list[ToolDefinition]:
    return [
        ToolDefinition(name=tool.name, description=tool.description, permission_level=tool.permission_level, supports_mock=tool.supports_mock)
        for tool in TOOL_REGISTRY.values()
    ]


def run_tool(session: Session, task_name: str, skill_name: str, tool_name: str, params: dict[str, Any] | None = None, sandbox_mode: str = "mock_sandbox") -> Any:
    params = params or {}
    tool = TOOL_REGISTRY[tool_name]
    blocked = sandbox_mode == "mock_sandbox" and tool.permission_level == "admin_only"
    result = {"error": "tool blocked in sandbox"} if blocked else tool.runner(params)
    session.add(
        AuditLog(
            task_name=task_name,
            skill_name=skill_name,
            tool_name=tool_name,
            permission_level=tool.permission_level,
            parameter_summary=json.dumps(params, ensure_ascii=False),
            result_summary=json.dumps(result, ensure_ascii=False)[:1000],
            blocked=blocked,
            is_mock=True,
        )
    )
    session.commit()
    return result


"""第六步：LangGraph 中的纯工具节点——不使用 LLM。"""

import json
from typing import TypedDict

from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph


@tool
def calculate_pitch_change_time(
    project_id: str,
    start_pitch_deg: float,
    target_pitch_deg: float,
) -> dict:
    """计算调距桨从起始桨距角调到目标桨距角所需的时间。"""

    pitch_speed_database = {
        "CPP-001": 3.0,  # 单位：度/秒
    }
    pitch_speed = pitch_speed_database.get(project_id)
    if pitch_speed is None:
        return {"error": "项目不存在"}

    pitch_change = abs(target_pitch_deg - start_pitch_deg)
    return {
        "project_id": project_id,
        "pitch_change_deg": pitch_change,
        "change_time_seconds": pitch_change / pitch_speed,
    }


class PitchState(TypedDict):
    project_id: str
    start_pitch_deg: float
    target_pitch_deg: float
    tool_result: dict


def run_pitch_time_tool(state: PitchState) -> dict:
    """这是一个纯工具节点：State -> Tool.invoke() -> State patch。"""

    arguments = {
        "project_id": state["project_id"],
        "start_pitch_deg": state["start_pitch_deg"],
        "target_pitch_deg": state["target_pitch_deg"],
    }
    result = calculate_pitch_change_time.invoke(arguments)
    return {"tool_result": result}


builder = StateGraph(PitchState)
builder.add_node("run_pitch_time_tool_1", run_pitch_time_tool)
builder.add_node("run_pitch_time_tool_2", run_pitch_time_tool)
builder.add_edge(START, "run_pitch_time_tool_1")
builder.add_edge("run_pitch_time_tool_1","run_pitch_time_tool_2")
builder.add_edge("run_pitch_time_tool_2", END)
graph = builder.compile()

initial_state = {
    "project_id": "CPP-001",
    "start_pitch_deg": -6.0,
    "target_pitch_deg": 18.0,
}

final_state = graph.invoke(initial_state)

print("total state:")
print(json.dumps(final_state, ensure_ascii=False, indent=2))

print("输入 State:")
print(json.dumps(initial_state, ensure_ascii=False, indent=2))
print("\n最终 State 中由工具节点写入的结果:")
print(json.dumps(final_state["tool_result"], ensure_ascii=False, indent=2))

"""第十一步：使用 checkpoint、interrupt 和 Command 恢复暂停的工作流。"""

import json
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class PitchWorkflowState(TypedDict, total=False):
    raw_input: dict
    normalized_input: dict
    review: dict
    calculation: dict
    status: str


REQUIRED_FIELDS = (
    "project_id",
    "start_pitch_deg",
    "target_pitch_deg",
    "pitch_speed_deg_s",
)


def validate_input(state: PitchWorkflowState) -> dict:
    """缺失或非法输入时暂停；恢复后重新校验全部字段。"""

    raw_input = dict(state["raw_input"])
    while True:
        missing_fields = [
            name for name in REQUIRED_FIELDS if name not in raw_input
        ]
        problem: dict | None = None
        normalized_input: dict | None = None

        if missing_fields:
            problem = {
                "kind": "missing_input",
                "message": "请补充计算所需字段。",
                "missing_fields": missing_fields,
            }
        else:
            try:
                normalized_input = {
                    "project_id": str(raw_input["project_id"]),
                    "start_pitch_deg": float(raw_input["start_pitch_deg"]),
                    "target_pitch_deg": float(raw_input["target_pitch_deg"]),
                    "pitch_speed_deg_s": float(raw_input["pitch_speed_deg_s"]),
                }
            except (TypeError, ValueError):
                problem = {
                    "kind": "invalid_input",
                    "message": "角度和变距速度必须是可转换为数字的值。",
                }
            else:
                if normalized_input["pitch_speed_deg_s"] <= 0:
                    problem = {
                        "kind": "invalid_input",
                        "message": "pitch_speed_deg_s 必须大于 0。",
                    }

        if problem is None and normalized_input is not None:
            return {
                "raw_input": raw_input,
                "normalized_input": normalized_input,
                "status": "INPUT_VALID",
            }

        supplied_values = interrupt(
            {
                **problem,
                "current_input": raw_input,
            }
        )
        if isinstance(supplied_values, dict):
            raw_input.update(supplied_values)


def request_review(state: PitchWorkflowState) -> dict:
    review = interrupt(
        {
            "kind": "review_required",
            "message": "请确认是否允许使用演示变距速度继续计算。",
            "inputs_to_review": state["normalized_input"],
            "required_fields": ["approved", "actor_id", "basis_id"],
            "warning": "本例只演示暂停恢复，不代表真实工程授权。",
        }
    )

    review_is_valid = (
        isinstance(review, dict)
        and review.get("approved") is True
        and bool(review.get("actor_id"))
        and bool(review.get("basis_id"))
    )
    return {
        "review": review if isinstance(review, dict) else {"raw_value": review},
        "status": "REVIEW_APPROVED" if review_is_valid else "BLOCKED",
    }


def route_after_review(state: PitchWorkflowState) -> str:
    return "calculate" if state["status"] == "REVIEW_APPROVED" else "end"


def calculate_pitch_time(state: PitchWorkflowState) -> dict:
    inputs = state["normalized_input"]
    pitch_change_deg = abs(
        inputs["target_pitch_deg"] - inputs["start_pitch_deg"]
    )
    return {
        "calculation": {
            "project_id": inputs["project_id"],
            "pitch_change_deg": pitch_change_deg,
            "change_time_seconds": pitch_change_deg
            / inputs["pitch_speed_deg_s"],
            "basis_id": state["review"]["basis_id"],
            "maturity": "DRAFT",
        },
        "status": "DRAFT_COMPLETE",
    }


def build_graph():
    builder = StateGraph(PitchWorkflowState)
    builder.add_node("validate_input", validate_input)
    builder.add_node("request_review", request_review)
    builder.add_node("calculate", calculate_pitch_time)
    builder.add_edge(START, "validate_input")
    builder.add_edge("validate_input", "request_review")
    builder.add_conditional_edges(
        "request_review",
        route_after_review,
        {"calculate": "calculate", "end": END},
    )
    builder.add_edge("calculate", END)

    # InMemorySaver 只能在当前进程中恢复；生产环境应使用数据库 Checkpointer。
    return builder.compile(checkpointer=InMemorySaver())


def print_interrupt(stage: str, state: dict) -> None:
    print(f"\n{stage}")
    for item in state.get("__interrupt__", ()):
        print(json.dumps(item.value, ensure_ascii=False, indent=2))


def main() -> None:
    graph = build_graph()
    config = {
        "configurable": {"thread_id": "CPP-001-learning-session"}
    }
    print("流程图:")
    print(graph.get_graph().draw_mermaid())

    first_state = graph.invoke(
        {
            "raw_input": {
                "project_id": "CPP-001",
                "start_pitch_deg": -6.0,
            }
        },
        config=config,
    )
    print_interrupt("1. 第一次暂停：等待补充输入", first_state)

    second_state = graph.invoke(
        Command(
            resume={
                "target_pitch_deg": 18.0,
                "pitch_speed_deg_s": "3.0",
            }
        ),
        config=config,
    )
    print_interrupt("2. 第二次暂停：等待人工复核", second_state)

    final_state = graph.invoke(
        Command(
            resume={
                "approved": True,
                "actor_id": "DEMO-CHIEF-DESIGNER",
                "basis_id": "DEMO-PITCH-SPEED-3-DEG-S",
            }
        ),
        config=config,
    )

    snapshot = graph.get_state(config)
    print("\n3. 恢复完成")
    print("最终状态:", final_state["status"])
    print("下一节点:", snapshot.next)
    print("计算结果:")
    print(json.dumps(final_state["calculation"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

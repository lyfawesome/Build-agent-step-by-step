"""第七步：LangGraph 编排 LLM 选工具、工具执行、LLM 最终回答。"""

import json

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph

from demo_config import get_langchain_chat_model


@tool
def get_project_power(project_id: str) -> dict:
    """根据项目编号查询调距桨项目的额定功率。"""

    return {
        "CPP-001": {"rated_power": 5000, "unit": "kW"},
    }.get(project_id, {"error": "项目不存在"})


@tool
def get_project_diameter(project_id: str) -> dict:
    """根据项目编号查询调距桨项目的桨直径。"""

    return {
        "CPP-001": {"diameter": 4.2, "unit": "m"},
    }.get(project_id, {"error": "项目不存在"})


TOOLS = [get_project_power, get_project_diameter]
TOOLS_BY_NAME = {candidate.name: candidate for candidate in TOOLS}


def build_graph():
    llm = get_langchain_chat_model()
    llm_with_tools = llm.bind_tools(TOOLS, tool_choice="required")

    def select_tool_with_llm(state: MessagesState) -> dict:
        response = llm_with_tools.invoke(
            [
                SystemMessage(
                    content=(
                        "你是调距桨项目查询助手。"
                        "在给定工具中选择恰好一个最匹配的工具。"
                    )
                ),
                *state["messages"],
            ]
        )
        return {"messages": [response]}

    def route_after_llm(state: MessagesState) -> str:
        last_message = state["messages"][-1]
        return "run_tools" if last_message.tool_calls else "write_final_answer"

    def run_requested_tools(state: MessagesState) -> dict:
        tool_messages = []
        for tool_call in state["messages"][-1].tool_calls:
            selected_tool = TOOLS_BY_NAME.get(tool_call["name"])
            if selected_tool is None:
                raise ValueError(f"不允许执行未知工具: {tool_call['name']}")
            tool_result = selected_tool.invoke(tool_call["args"])
            tool_messages.append(
                ToolMessage(
                    content=json.dumps(tool_result, ensure_ascii=False),
                    tool_call_id=tool_call["id"],
                    name=tool_call["name"],
                )
            )
        return {"messages": tool_messages}

    def write_final_answer(state: MessagesState) -> dict:
        response = llm.invoke(
            [
                SystemMessage(
                    content="严格依据工具结果简短回答，不得编造数据。"
                ),
                *state["messages"],
            ]
        )
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("select_tool_with_llm", select_tool_with_llm)
    builder.add_node("run_tools", run_requested_tools)
    builder.add_node("write_final_answer", write_final_answer)
    builder.add_edge(START, "select_tool_with_llm")
    builder.add_conditional_edges(
        "select_tool_with_llm",
        route_after_llm,
        {
            "run_tools": "run_tools",
            "write_final_answer": "write_final_answer",
        },
    )
    builder.add_edge("run_tools", "write_final_answer")
    builder.add_edge("write_final_answer", END)
    return builder.compile()


def main() -> None:
    graph = build_graph()
    final_state = graph.invoke(
        {
            "messages": [
                HumanMessage(content="查询 CPP-001 项目的桨直径。")
            ]
        }
    )

    print("完整消息序列:")
    for message in final_state["messages"]:
        print(f"\n{message.type}:")
        print("content =", message.content)
        if getattr(message, "tool_calls", None):
            print("tool_calls =", message.tool_calls)

    print("\n最终回答:")
    print(final_state["messages"][-1].content)


if __name__ == "__main__":
    main()

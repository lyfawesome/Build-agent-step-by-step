"""第七步：LangGraph 编排 LLM 选工具、工具执行、LLM 生成最终回答。"""

import json

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph

from demo_config import get_langchain_chat_model


@tool
def get_project_power(project_id: str) -> dict:
    """根据项目编号查询调距桨项目的额定功率。"""

    demo_database = {
        "CPP-001": {"rated_power": 5000, "unit": "kW"},
    }
    return demo_database.get(project_id, {"error": "项目不存在"})


@tool
def get_project_diameter(project_id: str) -> dict:
    """根据项目编号查询调距桨项目的桨直径。"""

    demo_database = {
        "CPP-001": {"diameter": 4.2, "unit": "m"},
    }
    return demo_database.get(project_id, {"error": "项目不存在"})


tools = [get_project_power, get_project_diameter]
tools_by_name = {tool.name: tool for tool in tools}

# ChatOpenAI 通过 OpenAI 兼容格式连接到你已经配置的 DeepSeek API。
llm = get_langchain_chat_model()

# 本轮要求必须调用一个工具，但由模型在两个候选工具中自己选择。
llm_with_tools = llm.bind_tools(tools, tool_choice="required")


def select_tool_with_llm(state: MessagesState) -> dict:
    """LLM 节点：理解问题，返回 AIMessage，其中可能含 tool_calls。"""

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
    """路由是确定性代码，不让 LLM 决定图的下一条边。"""

    last_message = state["messages"][-1]
    return "run_tools" if last_message.tool_calls else "write_final_answer"


def run_requested_tools(state: MessagesState) -> dict:
    """工具节点：读取 LLM 已生成的 name 和 args，执行本地 Tool。"""

    tool_messages = []
    for tool_call in state["messages"][-1].tool_calls:
        selected_tool = tools_by_name[tool_call["name"]]
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
    """第二个 LLM 节点：阅读 ToolMessage，生成自然语言答复。"""

    response = llm.invoke(
        [
            SystemMessage(
                content="请严格依据工具返回结果，用简短中文回答。不得编造数据。"
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
builder.add_conditional_edges("select_tool_with_llm", route_after_llm)
builder.add_edge("run_tools", "write_final_answer")
builder.add_edge("write_final_answer", END)
graph = builder.compile()

final_state = graph.invoke(
    {"messages": [HumanMessage(content="CPP-001 项目的R？")]}
)

print("完整消息序列:")
for message in final_state["messages"]:
    print(f"\n{message.type}:")
    print("content =", message.content)
    if getattr(message, "tool_calls", None):
        print("tool_calls =", message.tool_calls)

print("\n最终回答:")
print(final_state["messages"][-1].content)

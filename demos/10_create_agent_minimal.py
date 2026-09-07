"""第十步：对照 create_agent() 与显式 LangGraph 工具调用循环。"""

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from demo_config import get_langchain_chat_model


@tool
def get_project_power(project_id: str) -> dict:
    """根据项目编号查询调距桨项目的额定功率。"""

    return {
        "CPP-001": {"rated_power": 5000, "unit": "kW"},
    }.get(project_id, {"error": "项目不存在"})


SYSTEM_PROMPT = (
    "你是调距桨项目查询助手。回答项目功率问题时必须先调用工具，"
    "然后严格依据工具结果用简短中文回答。"
)
USER_MESSAGE = HumanMessage(content="请查询 CPP-001 项目的额定功率。")
TOOLS = [get_project_power]


def build_prebuilt_agent(model):
    """使用 LangChain 高层接口创建预制 Agent。"""

    return create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )


def build_manual_agent(model):
    """用 LangGraph 显式构建当前配置下行为等价的核心拓扑。"""

    model_with_tools = model.bind_tools(TOOLS)

    def call_model(state: MessagesState) -> dict:
        response = model_with_tools.invoke(
            [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        )
        return {"messages": [response]}

    def route_after_tools(_state: MessagesState) -> str:
        # 保留条件边形式，以对应 create_agent 的可扩展内部路由。
        return "model"

    builder = StateGraph(MessagesState)
    builder.add_node("model", call_model)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "model")
    builder.add_conditional_edges(
        "model",
        tools_condition,
        {"tools": "tools", "__end__": END},
    )
    builder.add_conditional_edges(
        "tools",
        route_after_tools,
        {"model": "model"},
    )
    return builder.compile()


def print_result(title: str, agent, final_state: dict) -> None:
    print(f"\n{'=' * 20} {title} {'=' * 20}")
    print("Agent 类型:", type(agent).__name__)
    print("\n图结构（Mermaid）:")
    print(agent.get_graph().draw_mermaid())
    print("\n完整消息序列:")
    for index, message in enumerate(final_state["messages"], start=1):
        print(f"\n{index}. {message.type}")
        print("content =", message.content)
        if getattr(message, "tool_calls", None):
            print("tool_calls =", message.tool_calls)
    print("\n最终回答:")
    print(final_state["messages"][-1].content)


def main() -> None:
    model = get_langchain_chat_model()
    prebuilt_agent = build_prebuilt_agent(model)
    manual_agent = build_manual_agent(model)

    # 本例会完整运行两套 Agent，因此通常会产生四次模型请求。
    prebuilt_final_state = prebuilt_agent.invoke({"messages": [USER_MESSAGE]})
    manual_final_state = manual_agent.invoke({"messages": [USER_MESSAGE]})

    print_result("create_agent() 自动构建", prebuilt_agent, prebuilt_final_state)
    print_result("StateGraph 手工构建", manual_agent, manual_final_state)
    print(
        "\n结论：当前最小配置下，两者都执行 model -> tools -> model "
        "条件循环；create_agent() 还封装了中间件、结构化响应和持久化等扩展。"
    )


if __name__ == "__main__":
    main()

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

    demo_database = {
        "CPP-001": {"rated_power": 5000, "unit": "kW"},
    }
    return demo_database.get(project_id, {"error": "项目不存在"})


SYSTEM_PROMPT = (
    "你是调距桨项目查询助手。回答项目功率问题时必须先调用工具，"
    "然后严格依据工具结果用简短中文回答。"
)
USER_MESSAGE = HumanMessage(content="请查询 CPP-001 项目的额定功率。")

model = get_langchain_chat_model()
tools = [get_project_power]


# ---------------------------------------------------------------------------
# 写法一：LangChain 高层接口
# ---------------------------------------------------------------------------
# create_agent() 隐藏了图的节点、条件边和循环构建过程，直接返回编译后的图。
prebuilt_agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
)


# ---------------------------------------------------------------------------
# 写法二：用 LangGraph 显式构建与上面最小 Agent 行为等价的流程
# ---------------------------------------------------------------------------
# bind_tools() 只是把工具说明交给模型，使模型能够生成 tool_calls；
# 真正执行工具的是下面加入图中的 ToolNode。
model_with_tools = model.bind_tools(tools)


def call_model(state: MessagesState) -> dict:
    """模型节点：决定调用工具，或者在已有工具结果后给出最终回答。"""

    response = model_with_tools.invoke(
        [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    )
    return {"messages": [response]}


def route_after_tools(state: MessagesState) -> str:
    """当前工具执行后回到模型；保留条件边形式以对应 create_agent()。"""

    return "model"


manual_builder = StateGraph(MessagesState)
manual_builder.add_node("model", call_model)
manual_builder.add_node("tools", ToolNode(tools))

manual_builder.add_edge(START, "model")

# tools_condition 检查最后一条 AIMessage：
# - 存在 tool_calls：进入 tools 节点；
# - 不存在 tool_calls：进入 END。
manual_builder.add_conditional_edges(
    "model",
    tools_condition,
    {"tools": "tools", "__end__": END},
)

# create_agent() 在工具节点后也使用条件边，以便扩展 return_direct 工具和结构化响应。
# 当前最小示例没有这些提前结束条件，所以该路由固定回到模型节点。
manual_builder.add_conditional_edges(
    "tools",
    route_after_tools,
    {"model": "model"},
)
manual_agent = manual_builder.compile()


def print_result(title: str, agent, final_state: dict) -> None:
    """打印图结构和消息序列，便于比较两种写法。"""

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


prebuilt_final_state = prebuilt_agent.invoke({"messages": [USER_MESSAGE]})
manual_final_state = manual_agent.invoke({"messages": [USER_MESSAGE]})

print_result("create_agent() 自动构建", prebuilt_agent, prebuilt_final_state)
print_result("StateGraph 手工构建", manual_agent, manual_final_state)

print(
    "\n结论：在当前最小配置下，两者都执行 "
    "model -> tools -> model 的条件循环；create_agent() 还封装了中间件、"
    "结构化响应、状态持久化等扩展能力，本例没有逐项复刻这些扩展。"
)

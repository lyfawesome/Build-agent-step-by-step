"""第二步：执行本地工具，把结果发回模型，再取得最终自然语言回答。"""

import json

from demo_config import get_chat_client


def get_project_power(project_id: str) -> dict:
    """根据项目编号查询调距桨项目的额定功率。"""

    demo_database = {
        "CPP-001": {"rated_power": 5000, "unit": "kW"},
    }
    return demo_database.get(project_id, {"error": "项目不存在"})


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_project_power",
            "description": "根据项目编号查询调距桨项目的额定功率。",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                },
                "required": ["project_id"],
            },
        },
    }
]


def main() -> None:
    client, model, thinking = get_chat_client()
    messages = [
        {
            "role": "system",
            "content": (
                "你是调距桨项目查询助手。最终回答只能依据工具返回的数据；"
                "如果工具返回 error，只说明该项目未查到，不得猜测原因、"
                "推荐其他项目编号或补充数据库中不存在的信息。"
            ),
        },
        {"role": "user", "content": "查询 CPP-002 项目的额定功率。"}
    ]

    # auto 允许模型直接回答，所以应用必须处理没有 tool_calls 的情况。
    first_response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        extra_body={"thinking": {"type": thinking}},
    )

    assistant_message = first_response.choices[0].message
    messages.append(assistant_message)
    if not assistant_message.tool_calls:
        print("模型选择了直接回答，没有请求工具:")
        print(assistant_message.content)
        return

    tool_call = assistant_message.tool_calls[0]
    arguments = json.loads(tool_call.function.arguments)
    print("模型要求调用:", tool_call.function.name)
    print("模型给出的参数:", arguments)

    # Python 根据白名单中的名字执行真正的本地函数。
    if tool_call.function.name != "get_project_power":
        raise ValueError(f"不允许执行未知工具: {tool_call.function.name}")
    tool_result = get_project_power(**arguments)
    print("本地函数返回:", tool_result)

    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(tool_result, ensure_ascii=False),
        }
    )

    second_response = client.chat.completions.create(
        model=model,
        messages=messages,
        extra_body={"thinking": {"type": thinking}},
    )

    print("\n发回模型的 tool 消息:")
    print(json.dumps(messages[-1], ensure_ascii=False, indent=2))
    print("\n模型最终回答:")
    print(second_response.choices[0].message.content)


if __name__ == "__main__":
    main()

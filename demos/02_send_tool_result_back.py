"""第二步：执行本地工具，把结果发回模型，再取得最终自然语言回答。"""

import json

from demo_config import get_chat_client


client, model, thinking = get_chat_client()


# 这才是真正执行的本地工具。模型不能直接运行这个函数。
def get_project_power(project_id):
    demo_database = {
        "CPP-001": {"rated_power": 5000, "unit": "kW"},
    }
    return demo_database.get(project_id, {"error": "项目不存在"})


tools = [
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

messages = [
    {"role": "user", "content": "查询 CPP-002 项目的额定功率。"}
]

# 第一次请求：模型决定调用工具，并返回工具名和参数。
first_response = client.chat.completions.create(
    model=model,
    messages=messages,
    tools=tools,
    tool_choice="auto",
    extra_body={"thinking": {"type": thinking}},
)

assistant_message = first_response.choices[0].message
messages.append(assistant_message)

tool_call = assistant_message.tool_calls[0]
arguments = json.loads(tool_call.function.arguments)

print("模型要求调用:", tool_call.function.name)
print("模型给出的参数:", arguments)

# Python 根据模型给出的名字和参数，执行真正的本地函数。
tool_result = get_project_power(**arguments)
print("本地函数返回:", tool_result)

# 关键：tool_call_id 把这个结果与模型刚才的调用请求对应起来。
messages.append(
    {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(tool_result, ensure_ascii=False),
    }
)

# 第二次请求：模型看见工具结果后，生成最终回答。
second_response = client.chat.completions.create(
    model=model,
    messages=messages,
    extra_body={"thinking": {"type": thinking}},
)

print("\n发回模型的 tool 消息:")
print(json.dumps(messages[-1], ensure_ascii=False, indent=2))
print("\n模型最终回答:")
print(second_response.choices[0].message.content)

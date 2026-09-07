"""第一步：把工具说明发给模型，只观察模型返回的工具调用请求。"""

import json

from demo_config import get_chat_client


client, model, thinking = get_chat_client()

# 这里只是告诉模型“有这样一个工具”，还没有执行任何 Python 函数。
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_project_power",
            "description": "根据项目编号查询调距桨项目的额定功率。",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "项目编号，例如 CPP-001",
                    }
                },
                "required": ["project_id"],
            },
        },
    }
]

response = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "user", "content": "查询 CPP-001 项目的额定功率。"}
    ],
    tools=tools,
    # 指定函数名，保证这一轮返回该工具的调用请求。
    tool_choice={
        "type": "function",
        "function": {"name": "get_project_power"},
    },
    extra_body={"thinking": {"type": thinking}},
)

message = response.choices[0].message
tool_call = message.tool_calls[0]

print("模型返回的 finish_reason:")
print(response.choices[0].finish_reason)
print("\n模型选择的工具名:")
print(tool_call.function.name)
print("\n模型生成的参数（原始 JSON 字符串）:")
print(tool_call.function.arguments)
print("\n解析后的参数:")
print(json.loads(tool_call.function.arguments))
print("\n完整 assistant message:")
print(message.model_dump_json(indent=2))
print("\n完整 response:")
print(response.model_dump_json(indent=2))

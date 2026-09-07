"""第三步：给模型多个候选工具，让模型根据用户问题选择一个。"""

import json

from demo_config import get_chat_client


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_project_power",
            "description": "根据项目编号查询调距桨项目的额定功率。",
            "parameters": {
                "type": "object",
                "properties": {"project_id": {"type": "string"}},
                "required": ["project_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_diameter",
            "description": "根据项目编号查询调距桨的直径。",
            "parameters": {
                "type": "object",
                "properties": {"project_id": {"type": "string"}},
                "required": ["project_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_pitch_time",
            "description": "查询调距桨从指定起始桨距调到目标桨距所需的时间。",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "项目编号，例如 CPP-001",
                    },
                    "start_pitch_deg": {
                        "type": "number",
                        "description": "起始桨距角，单位为度",
                    },
                    "target_pitch_deg": {
                        "type": "number",
                        "description": "目标桨距角，单位为度",
                    },
                },
                "required": [
                    "project_id",
                    "start_pitch_deg",
                    "target_pitch_deg",
                ],
            },
        },
    },
]


def main() -> None:
    client, model, thinking = get_chat_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "查询 CPP-001 项目从 10 度调到 25 度需要多长时间。",
            }
        ],
        tools=TOOLS,
        # required 只规定“必须调用工具”，没有指定名字。
        tool_choice="required",
        extra_body={"thinking": {"type": thinking}},
    )

    message = response.choices[0].message
    print("候选工具:")
    for tool_definition in TOOLS:
        print("-", tool_definition["function"]["name"])

    print("\n模型返回的 finish_reason:")
    print(response.choices[0].finish_reason)

    if not message.tool_calls:
        print("\n模型没有返回工具调用。")
        return

    print("\n模型选择的工具:")
    for tool_call in message.tool_calls:
        print("工具名:", tool_call.function.name)
        print("参数:", json.loads(tool_call.function.arguments))


if __name__ == "__main__":
    main()

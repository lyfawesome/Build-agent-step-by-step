"""第四步：让模型从问题中提取参数，并把参数传给本地工具。"""

import json

from demo_config import get_chat_client


client, model, thinking = get_chat_client()


# 这是实际执行的本地工具，共有三个参数。
def calculate_pitch_change_time(project_id, start_pitch_deg, target_pitch_deg):
    pitch_speed_database = {
        "CPP-001": 3.0,  # 单位：度/秒
    }

    pitch_speed = pitch_speed_database.get(project_id)
    if pitch_speed is None:
        return {"error": "项目不存在"}

    pitch_change = abs(target_pitch_deg - start_pitch_deg)
    change_time = pitch_change / pitch_speed

    return {
        "project_id": project_id,
        "pitch_change_deg": pitch_change,
        "change_time_seconds": change_time,
    }


# 这里只是向模型说明工具需要哪些参数，还没有执行上面的 Python 函数。
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate_pitch_change_time",
            "description": "计算指定调距桨项目从起始桨距角调到目标桨距角所需的时间。",
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
    }
]

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": "CPP-001 项目从负 6 度调到正 18 度需要多长时间？",
        }
    ],
    tools=tools,
    # 本例只演示参数提取，因此直接指定要使用的工具。
    tool_choice={
        "type": "function",
        "function": {"name": "calculate_pitch_change_time"},
    },
    extra_body={"thinking": {"type": thinking}},
)

tool_call = response.choices[0].message.tool_calls[0]

# 模型返回的 arguments 是 JSON 字符串，先转换为 Python 字典。
arguments = json.loads(tool_call.function.arguments)

print("模型返回的原始参数:")
print(tool_call.function.arguments)
print("\n转换后的 Python 字典:")
print(arguments)

# ** 会把字典中的键值对展开为函数的关键字参数。
tool_result = calculate_pitch_change_time(**arguments)

print("\n实际执行的效果相当于:")
print(
    "calculate_pitch_change_time("
    f"project_id={arguments['project_id']!r}, "
    f"start_pitch_deg={arguments['start_pitch_deg']!r}, "
    f"target_pitch_deg={arguments['target_pitch_deg']!r})"
)
print("\n本地工具返回:")
print(json.dumps(tool_result, ensure_ascii=False, indent=2))

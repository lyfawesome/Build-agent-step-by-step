"""第四步：让模型从问题中提取参数，并把参数传给本地工具。"""

import json

from demo_config import get_chat_client


def calculate_pitch_change_time(
    project_id: str,
    start_pitch_deg: float,
    target_pitch_deg: float,
) -> dict:
    """计算调距桨从起始桨距角调到目标桨距角所需的时间。"""

    pitch_speed_database = {"CPP-001": 3.0}
    pitch_speed = pitch_speed_database.get(project_id)
    if pitch_speed is None:
        return {"error": "项目不存在"}

    pitch_change = abs(target_pitch_deg - start_pitch_deg)
    return {
        "project_id": project_id,
        "pitch_change_deg": pitch_change,
        "change_time_seconds": pitch_change / pitch_speed,
    }


TOOLS = [
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


def main() -> None:
    client, model, thinking = get_chat_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "CPP-001 项目从负 6 度调到正 18 度需要多长时间？",
            }
        ],
        tools=TOOLS,
        tool_choice={
            "type": "function",
            "function": {"name": "calculate_pitch_change_time"},
        },
        extra_body={"thinking": {"type": thinking}},
    )

    tool_calls = response.choices[0].message.tool_calls
    if not tool_calls:
        print("模型没有返回工具调用，请检查接口能力。")
        return

    tool_call = tool_calls[0]
    arguments = json.loads(tool_call.function.arguments)
    print("模型返回的原始参数:")
    print(tool_call.function.arguments)
    print("\n转换后的 Python 字典:")
    print(arguments)

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


if __name__ == "__main__":
    main()

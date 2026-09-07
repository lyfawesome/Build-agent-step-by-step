"""第九步：把 LLM 输出解析并校验为结构化的 Pydantic 对象。"""

import json
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from demo_config import get_langchain_chat_model


class PitchDiagnosis(BaseModel):
    """调距桨诊断结果的数据契约。"""

    project_id: str = Field(description="项目编号")
    symptom: str = Field(description="根据输入归纳的故障现象")
    possible_causes: list[str] = Field(
        description="仅依据已给信息提出的可能原因",
        min_length=1,
        max_length=3,
    )
    required_checks: list[str] = Field(
        description="形成确定结论前必须完成的检查"
    )
    risk_level: Literal["low", "medium", "high"] = Field(
        description="初步风险等级"
    )
    conclusion_status: Literal["insufficient", "preliminary", "confirmed"] = Field(
        description="结论成熟度；资料不足时不得填写 confirmed"
    )


def main() -> None:
    llm = get_langchain_chat_model()
    structured_llm = llm.with_structured_output(
        PitchDiagnosis,
        method="function_calling",
        include_raw=True,
    )

    result = structured_llm.invoke(
        [
            SystemMessage(
                content=(
                    "你是调距桨工程诊断助手。只能依据用户明确提供的信息输出；"
                    "不得虚构测量值、检查结果或已确认结论。"
                )
            ),
            HumanMessage(
                content=(
                    "项目 CPP-001 在低螺距运行时出现变距时间延长。"
                    "尚未检查液压压力、油温和反馈传感器。"
                )
            ),
        ]
    )

    raw_message = result["raw"]
    parsed = result["parsed"]
    parsing_error = result["parsing_error"]
    print("1. 原始模型输出类型:")
    print(type(raw_message).__name__)
    print("\n2. 原始模型工具调用参数:")
    print(json.dumps(raw_message.tool_calls, ensure_ascii=False, indent=2))
    print("\n3. 结构化解析结果类型:")
    print(type(parsed).__name__ if parsed is not None else None)
    print("\n4. 通过 Pydantic 校验后的结果:")
    print(
        json.dumps(
            parsed.model_dump() if parsed is not None else None,
            ensure_ascii=False,
            indent=2,
        )
    )
    print("\n5. 解析错误:")
    print(repr(parsing_error))


if __name__ == "__main__":
    main()

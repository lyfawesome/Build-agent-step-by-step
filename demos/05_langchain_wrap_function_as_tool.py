"""第五步：用 LangChain 把普通 Python 函数包装成结构化 Tool。"""

import json

from langchain_core.tools import tool


@tool
def get_project_power(project_id: str) -> dict:
    """根据项目编号查询调距桨项目的额定功率。"""

    demo_database = {
        "CPP-001": {"rated_power": 5000, "unit": "kW"},
    }
    return demo_database.get(project_id, {"error": "项目不存在"})


def main() -> None:
    print("Tool 名称:")
    print(get_project_power.name)
    print("\nTool 描述:")
    print(get_project_power.description)
    print("\nLangChain 自动生成的参数 JSON Schema:")
    print(
        json.dumps(
            get_project_power.args_schema.model_json_schema(),
            ensure_ascii=False,
            indent=2,
        )
    )

    # invoke() 不经过 LLM，直接执行这个 Tool。
    result = get_project_power.invoke({"project_id": "CPP-001"})
    print("\n直接调用 Tool 的结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

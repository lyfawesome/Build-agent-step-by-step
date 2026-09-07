# 05b：Pydantic、输入模型类与实际数据

[学习总目录](README.md) · [详细 Schema 边界](05_langchain_tool_and_schema.md)

## 1. Pydantic 是什么

Pydantic 是独立的 Python 数据校验与序列化库，不是大模型，不属于 LangChain，也不是 JSON Schema 标准本身。你声明数据字段、类型和约束，它可以解析输入、校验数据、构造对象，并导出 Schema。[官方介绍](https://docs.pydantic.dev/latest/why/)

普通 Python 类型标注不会单独强制运行时检查：

```python
def ordinary(project_id: str):
    return project_id

assert ordinary(123) == 123
```

Pydantic 把声明交给真正的校验机制执行。默认可能进行某些类型转换，需要严格拒绝时另配置严格模式。

## 2. 手动建立一个输入模型类

```python
from pydantic import BaseModel, Field, ValidationError


class ProjectPowerInput(BaseModel):
    project_id: str = Field(min_length=1)


data = ProjectPowerInput.model_validate({"project_id": "CPP-001"})
print(data.project_id)

try:
    ProjectPowerInput.model_validate({})
except ValidationError:
    print("缺少必填参数")
```

- `BaseModel` 是 Pydantic 的基类。
- `ProjectPowerInput(BaseModel)` 是 Python 继承；通过继承获得模型构造、校验与序列化能力。
- `ProjectPowerInput` 是类，也就是数据结构和规则的定义。
- `data` 是这个类的一次实例，保存具体输入 `CPP-001`。
- “数据模型”不是“AI 模型”，没有训练权重或 token 生成。

## 3. 四个相似的方法

| 调用 | 输入/对象 | 输出 | 不是做什么 |
| --- | --- | --- | --- |
| `ProjectPowerInput.model_validate(raw)` | 原始数据 | 校验后的实例 | 不调用查询函数 |
| `data.model_dump()` | 实例 | 数据字典 | 不导出 Schema |
| `data.model_dump_json()` | 实例 | 数据 JSON 文本 | 不导出全部应用历史 |
| `ProjectPowerInput.model_json_schema()` | 模型类 | 规则的 Schema 字典 | 不包含某个实际项目的所有数据 |

```python
data.model_dump()       # {"project_id": "CPP-001"}
data.model_dump_json()  # '{"project_id":"CPP-001"}'
```

生成 Schema 则描述 `project_id` 为必填、非空字符串，而不是把 `CPP-001` 变成唯一合法值。Schema 导出通常在类上完成，序列化实际值则在实例上完成。[Schema 导出说明](https://docs.pydantic.dev/latest/concepts/json_schema/)

## 4. LangChain 帮你省略了哪一步

对第 05 个 demo 的函数，LangChain 根据签名动态建立一个输入模型类，概念上类似上面的 `ProjectPowerInput`。实际生成的名称和元数据由框架决定，不能把概念示例当成逐字源码。

该类保存于 `get_project_power.args_schema`。因此同一份输入定义可用于：

1. 导出工具参数 Schema，供适配器描述给模型。
2. 本地调用时解析/校验模型给出的参数。

这是一套声明、多处使用，不是必须先导出 JSON Schema 再把 JSON Schema 读回来才能校验。Pydantic 有自己的运行时校验结构。

需要更复杂输入时，也可自己定义模型，通过 `@tool(args_schema=ProjectPowerInput)` 提供给工具。这个类仍不负责数据库权限、项目是否存在或工程结论是否获批。

## 5. 几个容易误解的限制

- `Field(description="压力应小于上限")` 不会自动形成大小约束。
- 自定义验证器可以检查更复杂的逻辑，但其任意 Python 代码未必能导出为 JSON Schema。
- 类型正确不等于数据真实；Schema 不能单独证明出处可靠。
- `BaseModel` 实例不是自动不可变、不是自动永久保存；冻结/赋值校验/存储需要显式配置。
- `TypedDict` 主要描述字典的静态类型，不等于创建了一个会自动校验输入的 Pydantic 实例。
- `json.loads` 只把文本解析成 Python 数据；Pydantic 再按规则校验，两者不是同一步。

## 与已有笔记的分工

本篇回答“谁在执行数据校验、类与实例是什么”。[笔记 05](05_langchain_tool_and_schema.md)回答“规则从哪里来、哪些可以自动推断”，其中保留了文档字符串、多段文本、必填/空值、范围、嵌套及调用方式的完整讨论。

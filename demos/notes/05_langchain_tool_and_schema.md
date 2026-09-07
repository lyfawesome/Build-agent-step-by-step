# 学习笔记 05：函数包装、文档字符串与 Schema 识别边界

配套代码：[05_langchain_wrap_function_as_tool.py](../05_langchain_wrap_function_as_tool.py) · [返回教学目录](../README.md)

完整知识导航：[两个对话的学习手册](README.md)。如果不熟悉数据模型类、校验和序列化，先读 [Pydantic 入门](05b_pydantic_basics.md)，再回到本章的自动 Schema 推断。

这份笔记记录围绕第 05 个 demo 的讨论：包装发生了什么、工具描述怎样取得、Schema 能自动生成到什么程度，以及 `invoke` 的同级调用方法。它不是完整 JSON Schema 标准手册，也不是所有模型 API 的兼容性清单。

本轮观察环境：Python 3.11、`langchain 1.3.14`、`langchain-core 1.5.3`、`pydantic 2.13.4`。版本更新后，生成细节应以本机输出为准。笔记中的范围与型号都是教学例子，不是客户批准的工程规则。以下本地实验不需要 API Key，也不调用模型。

## 1. 先记住五个结论

1. `@tool` 把普通函数包装成工具对象，不改写函数的业务算法，也不自动执行它。
2. 文档字符串先由 Python 认定并保存为函数的 `__doc__`，LangChain 再读取它；不是搜索函数里所有字符串。
3. Schema 自动生成主要是“读取声明 → 转换结构”，不使用 LLM，不理解函数体里的业务逻辑。
4. 必填、允许空值、默认值、字段类型是不同维度；不要互相替代。
5. 能生成 Schema、模型 API 能接受 Schema、本地如何验证输入，是三件不同的事。

## 2. `@tool` 包装究竟改变了什么

原代码：

```python
@tool
def get_project_power(project_id: str) -> dict:
    """根据项目编号查询调距桨项目的额定功率。"""
    # 原函数体……
```

从装饰器语义看，等价于先定义函数，再执行：

```python
get_project_power = tool(get_project_power)
```

右边接收原函数，左边接收包装后的对象。因此，名字 `get_project_power` 此后指向 `StructuredTool`，原函数保存在它的 `func` 属性中。

| 包装后的成员 | 含义 |
| --- | --- |
| `name` | 工具名称，默认取函数名 |
| `description` | 工具实际使用的描述 |
| `args_schema` | 输入参数的 Pydantic 模型类；本 demo 自动建立 |
| `func` | 原来的同步 Python 函数 |
| `invoke` | 统一的同步执行入口 |

包装带来工具元数据、输入模型、运行时参数校验、统一调用接口，以及框架的配置/回调接入能力。它不会自动提供工程正确性、身份认证、权限控制、外部动作幂等性，也不会自动把工具提交给模型。

本例的调用过程可以简化为：

```text
get_project_power.invoke({"project_id": "CPP-001"})
  → 按输入模型校验参数
  → 展开参数并调用保存的原函数
  → 执行本地字典查询
  → 返回 {"rated_power": 5000, "unit": "kW"}
```

两类失败要分清：

```python
get_project_power.invoke({})
# ValidationError：缺少 project_id，尚未进入原函数。

get_project_power.invoke({"project_id": "CPP-002"})
# {"error": "项目不存在"}：参数结构合法，进入函数后得到业务错误结果。
```

这里传入的是普通参数字典，返回原函数结果。若传入完整工具调用对象并携带调用 ID，工具接口还可能返回关联该调用的消息对象；不要将本例的返回类型推广到所有调用形式。

## 3. 工具描述：Python 文档字符串的精确规则

### 3.1 位置是“函数体第一条语句”，不是“第一行”

以下成立，因为注释和空行不算 Python 语句：

```python
def example():
    # 给读代码的人看的注释。

    """给函数保存的文档字符串。"""
    return None

print(example.__doc__)
```

以下不成立，因为赋值已经占据第一条语句：

```python
def example():
    value = 1
    """这不再是函数文档字符串。"""
    return value

assert example.__doc__ is None
```

`description = "说明"` 也不成立：第一条语句是赋值，不是独立的字符串字面量。`print`、`pass`、`return` 等放在前面同样会失去这个位置。

### 3.2 引号种类与字符串形式

下表都以该表达式位于函数体第一条语句为前提。

| 写法 | 能否成为 `__doc__` | 细节 |
| --- | --- | --- |
| `"说明"` | 可以 | 英文双引号 |
| `'说明'` | 可以 | 英文单引号 |
| `"""说明"""` | 可以 | 三个英文双引号，便于多行书写 |
| `'''说明'''` | 可以 | 三个英文单引号 |
| `r"说明"` | 可以 | 原始字符串，反斜杠转义行为不同 |
| `f"说明"` | 不可以 | 即使没有插值变量也不成立 |
| `b"description"` | 不可以 | 字节串不是文本字符串 |
| `"甲" "乙"` | 可以 | 相邻字面量合并为一个字符串 |
| `"甲" + "乙"` | 不可以 | 运算表达式不是文档字符串 |
| `# 说明` | 不可以 | 注释不会保存为函数文档字符串 |
| `“说明”` | 语法错误 | 中文弯引号不能作为 Python 字符串定界符 |

内容可以是中文，也可以包含弯引号，例如 `"""查询“额定功率”。"""`。通常统一使用三双引号，但它是书写惯例，不是成立的唯一条件。

### 3.3 多段文字与多个字符串不是一回事

一个字符串内写多段文字，全部属于文档字符串：

```python
def example():
    """第一段说明。

    第二段说明。
    """
    return None
```

分开写成多个字符串语句，只有第一个有效：

```python
def example():
    """第一段说明。"""
    """第二段不会自动追加。"""
    return None

assert example.__doc__ == "第一段说明。"
```

括号中的相邻字符串字面量可以自动合并；不会自动补空格或换行：

```python
def example():
    (
        "第一段说明。\n"
        "第二段说明。"
    )
    return None
```

### 3.4 LangChain 读取哪一个属性

默认工具描述来自原函数 `__doc__`，并经过一定的空白整理。默认不会只截取第一行，也不需要运行函数。

包装后观察：

```python
get_project_power.func.__doc__  # 原函数的文档字符串。
get_project_power.description  # 工具实际使用的描述。
```

不要把包装后对象自身的 `get_project_power.__doc__` 当作工具描述，因为这个对象已经不是原函数。

对本 demo 的默认包装方式，如果没有文档字符串，也没有其他描述来源，会在包装阶段报 `ValueError`。本机观察到：空字符串会被视为缺描述；纯空白字符串可能被接受后整理为空描述，不应依赖这个边界行为。

可以显式指定描述，且它优先于函数文档字符串：

```python
@tool(description="给模型看的工具描述。")
def example(project_id: str) -> dict:
    """给原函数保存的说明。"""
    return {}
```

### 3.5 描述文本与参数说明的解析

默认 `parse_docstring=False`，普通中文即可，不要求 `Args:`。即使写了 `Args:`，默认也不会把其中的文字拆成每个参数的 Schema 描述。

显式开启解析时，需要使用受支持的 Google 风格文档：

```python
@tool(parse_docstring=True)
def example(project_id: str) -> dict:
    """查询项目的额定功率。

    Args:
        project_id: 项目编号，例如 CPP-001。
    """
    return {}
```

这时参数 `project_id` 的 Schema 会出现 `description`。段落、缩进和参数名要正确；参数名要与签名一致。开启解析后，当前 `@tool` 默认会对不符合要求的文档报错。

这仍是格式解析，不会将“功率不能超过某值”的中文自动变成数值上限。

## 4. `args_schema.model_json_schema()` 为什么能生成 Schema

底层路径：读取函数签名与类型标注 → LangChain 借助 Pydantic 建立输入模型类 → Pydantic 导出 JSON Schema。

把 demo 的一行拆开：

```python
schema_class = get_project_power.args_schema
schema_dict = schema_class.model_json_schema()
schema_text = json.dumps(schema_dict, ensure_ascii=False, indent=2)
```

| 对象 | 当前是什么 | 用途 |
| --- | --- | --- |
| `schema_class` | Pydantic 输入模型类 | 描述参数，并供工具调用时解析/校验 |
| `schema_dict` | Python 字典 | JSON Schema 的结构化表示 |
| `schema_text` | JSON 文本字符串 | 打印、阅读或传输 |

自动生成不读取函数体里的 `demo_database`，不运行查询，不调用 LLM。普通 Python 类型注解本身也不会强制检查调用参数；运行时校验是包装后由 Pydantic 等执行的。

`-> dict` 是返回类型标注，不会让当前输入 `args_schema` 自动包含输出字段，更不会推断返回字典必须有 `rated_power` 和 `unit`。

### 4.1 必填、默认值与空值

针对 demo 中的普通参数：没有默认值，调用者就必须提供，因此生成 `required`。这来自函数签名，而不是参数在函数体里是否被使用。

| 定义 | 必须提供字段 | 允许传入 `None` |
| --- | --- | --- |
| `project_id: str` | 是 | 否 |
| `project_id: str = "CPP-001"` | 否 | 否 |
| `project_id: str \| None` | 是 | 是 |
| `project_id: str \| None = None` | 否 | 是 |

对第三行，`{"project_id": None}` 是提供了一个空值，`{}` 则是没提供字段，二者不同。没有其他必填参数时，生成器可以省略整个 `required` 项，而不是必须写空数组。

本机未给参数标注类型的实验中，生成器仍能识别必填，但字段没有类型限制。它不会仅凭名字 `project_id` 猜成字符串。

## 5. Schema 自动识别边界速查

### 5.1 从类型和签名可直接转换的结构

| 识别项 | 声明示例 | Schema 表达 |
| --- | --- | --- |
| 字段名 | `project_id: str` | `properties` 中的键 |
| 基础类型 | `str` / `int` / `float` / `bool` | `string` / `integer` / `number` / `boolean` |
| 必填 | 普通参数无默认值 | `required` |
| 默认值 | `count: int = 5` | `default: 5`，非必填 |
| 可空 | `str \| None` | 允许 `string` 或 `null`，常见形式为 `anyOf` |
| 联合类型 | `int \| str` | `anyOf` |
| 枚举 | `Literal["CW", "CCW"]` | `enum` |
| 固定值 | `Literal["kW"]` | `const` |
| 数组元素类型 | `list[str]` | `array` 与字符串 `items` |
| 集合唯一性 | `set[int]` | 数组与 `uniqueItems: true` |
| 固定位置与长度 | `tuple[str, int]` | `prefixItems` 及长度约束 |
| 字典值类型 | `dict[str, float]` | `object` 与值类型的 `additionalProperties` |
| 嵌套对象 | Pydantic 模型作为参数类型 | 嵌套结构，通常用 `$defs` / `$ref` |
| 日期 | `datetime.date` | 字符串与 `format: date` |
| 日期时间 | `datetime.datetime` | 字符串与 `format: date-time` |
| UUID | `uuid.UUID` | 字符串与 `format: uuid` |

只写 `dict` 或 `list`，不会自动得到内部字段和元素约束。嵌套多少层，就需要显式声明多少层的结构。

### 5.2 需要显式补充的约束

下列 `Field` 需要配合 `Annotated` 或 Pydantic 模型字段使用；单独写在说明文字中不起作用。

| 约束 | Python 声明 | Schema 表达 |
| --- | --- | --- |
| 包含下界 | `Field(ge=800)` | `minimum` |
| 包含上界 | `Field(le=55000)` | `maximum` |
| 不包含下界 | `Field(gt=0)` | `exclusiveMinimum` |
| 不包含上界 | `Field(lt=100)` | `exclusiveMaximum` |
| 倍数关系 | `Field(multiple_of=5)` | `multipleOf` |
| 字符串最短/最长长度 | `Field(min_length=3, max_length=20)` | `minLength` / `maxLength` |
| 字符串正则格式 | `Field(pattern=r"^CPP-\d{3}$")` | `pattern` |
| 数组最少/最多元素 | 列表上 `Field(min_length=1, max_length=10)` | `minItems` / `maxItems` |
| 禁止多余字段 | 模型配置 `ConfigDict(extra="forbid")` | 对该模型产生 `additionalProperties: false` |

配置一个嵌套模型禁止多余字段，不等于所有外层/其他对象都自动禁止；应检查每一层生成的 Schema。

`min_length` 的含义取决于所约束对象：

```python
from typing import Annotated
from pydantic import Field

# 字符串至少三个字符。
Code = Annotated[str, Field(min_length=3)]

# 列表至少一个元素；每个元素是上面的 Code。
Codes = Annotated[list[Code], Field(min_length=1)]
```

可声明的复杂输入模型也可以通过 `@tool(args_schema=某个模型类)` 显式提供，不必全部塞入函数签名。

### 5.3 描述性元数据不等于校验约束

| 项目 | 来源 | 是否直接限制有效输入 |
| --- | --- | --- |
| `title` | 自动生成或显式指定 | 否 |
| `description` | 文档或字段说明 | 否 |
| `examples` | 显式示例 | 否，不表示只能选示例中的值 |
| `default` | 默认值声明 | Schema 本身不会强制补值 |

例如 `Field(description="功率不超过 55000 kW")` 只是说明；`Field(le=55000)` 才是声明数值上限。Python/Pydantic 可以按自己的规则应用默认值，但 JSON Schema 的 `default` 本身不是执行补值的代码。动态默认值工厂也不能当作已经导出的固定默认值。

### 5.4 不会从函数或自然语言自动推导的规则

| 业务要求 | 为什么不能靠自动 Schema 推断 | 正确处理位置 |
| --- | --- | --- |
| 函数中 `if power > 55000` | 不分析函数体控制逻辑 | 显式约束或业务校验 |
| 参数名带 `_kw` | 不推导物理单位及换算关系 | 明确单位契约与转换逻辑 |
| 项目编号必须存在 | 不自动访问数据库 | 查询工具 |
| 最小角度小于最大角度 | 不自动建立跨字段比较 | 模型校验器或业务代码 |
| 冰区必须填写冰级 | 不从中文推导条件必填 | 显式条件 Schema 或校验代码 |
| 调用者必须有工程师权限 | 类型不能代表授权 | 可信身份与权限检查 |
| 知识版本必须有效 | 不自动查询有效期/撤销记录 | 知识适配器与业务门禁 |
| 完整工程输入是否充分 | 不理解项目设计责任边界 | 明确需求基线及工程审查 |
| 自定义验证器的任意 Python 逻辑 | 运行时可执行不代表可导出 | 保留验证器，必要时另写 Schema |

JSON Schema 本身有 `if/then/else` 等条件表达能力，不代表 LangChain 会把函数里的 `if` 自动转换成它。任意跨字段算术关系也不能假定都有通用 JSON Schema 表达。

## 6. 用一个最小反例理解“自动化不等于业务智能”

以下是独立教学代码，不修改原 demo：

```python
from langchain_core.tools import tool


@tool
def body_only(power_kw: float) -> bool:
    """教学示例：功率要求在 800 到 55000 kW 之间。"""
    if not 800 <= power_kw <= 55000:
        raise ValueError("功率越界")
    return True


print(body_only.args_schema.model_json_schema()["properties"]["power_kw"])
# 有 type: number，但没有 minimum/maximum。
```

传入越界数字时，输入类型校验可以通过，原函数中的业务检查随后失败。范围写成明确声明后，才能导出对应约束：

```python
from typing import Annotated
from pydantic import Field
from langchain_core.tools import tool


@tool
def declared(
    power_kw: Annotated[float, Field(ge=800, le=55000)],
) -> bool:
    """教学示例：显式声明输入范围。"""
    return True


print(declared.args_schema.model_json_schema()["properties"]["power_kw"])
# 包含 type: number、minimum: 800、maximum: 55000。
```

它能省去重复手写接口结构的工作，不能省去确定业务规则的工作。

## 7. 生成、模型接收、本地执行是三层边界

1. **生成层**：Pydantic 能否把声明转换成 Schema。
2. **模型接口层**：具体提供商/接口/模式是否接受这些关键词；常见接口只支持某个子集，不能以本地生成成功代替兼容性验证。
3. **执行层**：Pydantic 或其他校验器实际如何拒绝、转换和返回数据。

几个易错例子：

- `set[int]` 导出 `uniqueItems: true`，但 Pydantic 接收列表时可能直接去重，而非对重复项报错。
- `format: date` 表达日期格式，但通用 JSON Schema 校验器是否强制检查 `format`，取决于实现与配置。
- 某些宽松模式会把 `"123"` 转为整数；这不代表原始 JSON 字符串已经满足整数类型。
- `strict=True` 这类运行时严格性设置，不一定在生成的 JSON Schema 中有等价字段。
- 任意 `model_validator` / `field_validator` 的逻辑，不会普遍自动转成可发给模型的完整 Schema。

给模型看 Schema 可以帮助生成合规参数，但不能代替执行工具前的本地校验，更不能代替权限和工程检查。

## 8. `invoke` 与异步、批量、流式方法

| 用途 | 同步方法 | 异步方法 | 默认组织方式 |
| --- | --- | --- | --- |
| 单次调用 | `invoke` | `ainvoke` | 一个输入得到一个结果 |
| 批量，结果按输入顺序排列 | `batch` | `abatch` | 本工具同步批量用线程池；异步批量调度多次异步调用 |
| 批量，按完成顺序取得结果 | `batch_as_completed` | `abatch_as_completed` | 返回输入索引与相应结果，便于对应原请求 |
| 流式接口 | `stream` | `astream` | 是否真正分块输出取决于具体实现 |

示例中的 `get_project_power` 指第 05 个 demo 包装后的对象；异步代码须放在异步函数内。

```python
result = get_project_power.invoke({"project_id": "CPP-001"})

results = get_project_power.batch(
    [{"project_id": "CPP-001"}, {"project_id": "CPP-002"}],
    config={"max_concurrency": 2},
)
# 输出列表与输入列表顺序一致，不是哪个先完成就先排哪个。

for index, result in get_project_power.batch_as_completed(
    [{"project_id": "CPP-001"}, {"project_id": "CPP-002"}],
    config={"max_concurrency": 2},
):
    print(index, result)
```

```python
async def query_async():
    return await get_project_power.abatch(
        [{"project_id": "CPP-001"}, {"project_id": "CPP-002"}],
        config={"max_concurrency": 2},
    )
```

关键区别：

- 一次 `ainvoke` 不代表已经同时发起多个查询。异步是调度方式，并发要看是否安排了多个任务。
- 本 demo 原函数是同步函数，`ainvoke` 会在线程中执行同步调用，不会重写函数体为原生异步代码。
- 本工具的默认 `batch` 是执行多次 `invoke`，不是底层业务函数只调用一次，也不是模型一次生成多个候选。
- 普通字典查询函数不会因调用 `stream` 就逐字段输出；默认只产出一次完整结果。
- 并发适合某些 I/O 等待场景，不保证计算密集任务加速；原函数访问共享可变数据或外部写操作时，应另外考虑线程安全和幂等性。

## 9. 与当前工程项目的衔接

第 05 个 demo 解释的是“把函数声明转换成可调用工具”。完整项目还需要在工具外安排工程数据校验、受控知识、权限、人工审批、版本失效和存储事务。

因此，不能因为 `@tool` 已经生成 Schema，就认为“项目输入已完整”或“结果已可放行”。关键输入缺失时仍应保持 `DRAFT / INCOMPLETE`，列出明确未决项，不为了让程序运行而补工程默认值。

下一步可对照：

- [第 06 个 demo：纯工具节点](../06_langgraph_pure_tool_node.py)：看节点如何从 State 取参数、执行工具、写回结果。
- [第 07 个 demo：LLM 与工具编排](../07_langgraph_llm_tool_workflow.py)：看模型请求调用与真正执行工具如何分开；运行它会调用 DeepSeek API。
- [cae-agent-cpp 的 MVP 跨文件代码阅读地图](https://github.com/lyfawesome/cae-agent-cpp/blob/main/cpp_design_agent_mvp/docs/12_code_reading_guide.md)：看输入校验、工具执行、审批、事务和修订如何衔接。

## 10. 官方参考与观察依据

本文 Python 字符串、Schema 生成、默认值/空值、范围和容器映射等例子，结合本机已安装库的实际输出整理。源码观察入口是 `StructuredTool.from_function`、`create_schema_from_function`、`BaseTool.invoke` 与 `Runnable` 的批量/流式方法。

- Python 将函数体开头的字符串字面量保存为文档字符串：[Python 函数定义说明](https://docs.python.org/3.11/tutorial/controlflow.html#defining-functions)。
- 显式工具描述、Pydantic 输入模型等配置入口：[LangChain Tools](https://docs.langchain.com/oss/python/langchain/tools)。
- `parse_docstring` 等参数的准确含义：[LangChain tool API](https://reference.langchain.com/python/langchain-core/tools/convert/tool)。
- 字段约束与描述性元数据：[Pydantic Fields](https://docs.pydantic.dev/latest/concepts/fields/)。
- 类型到 Schema 的转换及定制边界：[Pydantic JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/)。
- 批量、异步与默认流式执行接口：[LangChain Runnable](https://reference.langchain.com/python/langchain-core/runnables/base/Runnable)。

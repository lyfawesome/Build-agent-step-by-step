# 最小工具调用 Demo

这里只保留十一个脚本，每个脚本只讲一个问题。

## 配套学习笔记

[两个对话的 Agent 学习手册：从这里开始](notes/README.md) 汇总当前对话与《代码实例学习》的知识，分为模型接口与工具调用、函数包装与 Schema、Pydantic、LangGraph 节点与路由、数据与证据、上下文管理、本地部署及阅读路线八个主题，并逐项关联下面的 demo。

其中 [笔记 05：函数包装、文档字符串与 Schema 识别边界](notes/05_langchain_tool_and_schema.md) 保留了位置、引号、多段字符串、必填与可空、约束推断以及 `invoke` 同级方法的详细讨论。笔记与脚本分开放在 `notes/`，保持 demo 简短，便于持续积累学习记录。

## 1. 模型如何知道有哪些工具

运行：

```bash
python 01_model_returns_tool_call.py
```

观察代码里的 `tools` 参数。它包含工具名称 `name`、使用说明 `description` 和参数的 JSON Schema `parameters`。

模型不会执行函数，只返回类似下面的调用请求：

```json
{
  "name": "get_project_power",
  "arguments": "{\"project_id\":\"CPP-001\"}"
}
```

## 2. 工具结果如何返回给模型

运行：

```bash
python 02_send_tool_result_back.py
```

只看四步：

1. 第一次请求得到 `message.tool_calls`；
2. Python 解析 `function.arguments` 并执行本地函数；
3. 把结果放进 `role="tool"` 消息，并带上对应的 `tool_call_id`；
4. 第二次请求让模型根据工具结果回答。

这里所谓“等待工具返回”，就是 Python 代码停在函数调用这一行，函数返回后才继续组织第二次模型请求。暂时没有加入 Agent 框架、循环、异步任务或调距桨完整业务规则。

## 3. 模型如何从多个工具中选择

运行：

```bash
python 03_model_selects_from_multiple_tools.py
```

脚本同时提供功率、直径和调距时间三个工具。`tool_choice="required"` 只要求模型必须调用工具，但不指定工具名；模型需要根据用户问题和工具描述选择合适的工具。

## 4. 如何提取参数并传给工具

运行：

```bash
python 04_extract_arguments_and_call_tool.py
```

模型从用户问题中提取项目编号、起始桨距角和目标桨距角。Python 使用 `json.loads()` 把模型返回的 JSON 字符串转换为字典，再通过 `calculate_pitch_change_time(**arguments)` 把字典中的三个值传给本地函数。

## 5. LangChain 如何包装本地函数为 Tool

运行：

```bash
python 05_langchain_wrap_function_as_tool.py
```

`@tool` 会读取函数名、docstring 和类型标注，创建 LangChain 的 `StructuredTool`。本例不调用 LLM，只观察自动生成的 JSON Schema，并用 `Tool.invoke()` 直接执行本地函数。

细节见[配套笔记 05](notes/05_langchain_tool_and_schema.md)。先看包装与文档字符串，再看第 5 节的 Schema 边界表；不要把“自动转换声明”理解成“自动分析业务代码”。

## 6. LangGraph 中的纯工具节点

运行：

```bash
python 06_langgraph_pure_tool_node.py
```

本例没有 LLM。LangGraph 节点从 State 读取三个字段，调用 `Tool.invoke()`，再把结果写回 State。这说明一个节点可以只是确定性工具调用。

## 7. LangGraph 如何编排 LLM 与 Tool

运行：

```bash
python 07_langgraph_llm_tool_workflow.py
```

本例才会调用 DeepSeek API，依次经过三个节点：LLM 从两个候选工具中选择一个、工具节点执行本地函数、第二个 LLM 节点根据工具结果生成最终回答。节点间的路由 `route_after_llm` 是普通 Python 代码，不依赖 LLM 的主观判断。

## 8. Schema、Evidence 和 Artifact 如何协作

运行：

```bash
python 08_schema_evidence_artifact.py
```

本例不调用 LLM。它读取完整 State 教学数据，使用项目的 `design_state.schema.json` 校验结构；随后沿 `calculation -> evidence -> artifact` 引用链找到真实计算制品，并重新计算文件 SHA-256，验证 State、Evidence 和 Artifact 中记录的哈希一致。教学数据保持 `DRAFT/PENDING`，不会伪装成可工程放行的数据。

## 9. 如何把模型输出解析为结构化对象

运行：

```bash
python 09_structured_output_parsing.py
```

本例使用 Pydantic 定义调距桨诊断结果的数据契约，再通过 LangChain 的 `with_structured_output()` 要求 DeepSeek 按该结构返回。运行后可以同时观察原始 `AIMessage` 中的工具调用参数、通过 Pydantic 校验后的 `PitchDiagnosis` 对象，以及 `parsing_error`。它说明结构化输出不只是要求模型“写成 JSON”，还包括将字段类型、枚举值和列表长度交给程序校验。

## 10. 如何用 create_agent() 创建最小 Agent

运行：

```bash
python 10_create_agent_minimal.py
```

本例先使用 LangChain 的 `create_agent()` 把 DeepSeek 模型和一个本地 Tool 组装成最小 Agent，再用 `StateGraph`、`ToolNode` 和 `tools_condition` 显式构建行为等价的最小流程。两种写法都会执行“模型判断 → 工具执行 → 回到模型 → 无工具调用时结束”的条件循环。脚本分别打印两个编译图的 Mermaid 结构和完整消息序列，便于观察 `create_agent()` 隐藏了哪些 LangGraph 构建代码。这里复刻的是当前最小配置下的核心拓扑，不包括 `create_agent()` 支持的中间件、结构化响应和持久化等扩展能力。

## 11. LangGraph 如何暂停并恢复同一个工作流

运行：

```bash
python 11_langgraph_interrupt_and_resume.py
```

本例不调用 LLM。工作流第一次因缺少计算字段在 `validate_input` 节点调用 `interrupt()` 暂停；使用相同 `thread_id` 和 `Command(resume=...)` 补充字段后，继续运行并在人工复核节点第二次暂停；再次恢复后才执行确定性计算。`InMemorySaver` 只支持当前 Python 进程内恢复，生产环境需要换成数据库支持的持久化 checkpointer。示例中的复核身份和依据均明确标记为 `DEMO`，不能视为真实工程授权。

## Python 环境

在仓库根目录创建独立环境并安装依赖：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r demos/requirements.txt
cd demos
```

## DeepSeek 配置从哪里读取

调用 LLM 的脚本通过 `demo_config.py` 读取以下变量：

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`
- `DEEPSEEK_THINKING`

`demo_config.py` 从当前文件所在目录开始逐级向上查找，第一个找到的 `.env.local` 会被加载。已有进程环境变量不会被同名文件配置覆盖。因此，本机放在仓库父目录中的共享 `.env.local` 可以继续供这些教学脚本使用。

对新的仓库克隆，推荐在仓库根目录执行：

```bash
cp .env.example .env.local
# 编辑 .env.local，填写真实的 DEEPSEEK_API_KEY
```

`.env.local` 已被仓库根目录的 `.gitignore` 排除。Git 只保存不含密钥的 `.env.example`；不要使用强制添加把 `.env.local`、API Key 或其他凭据提交到仓库。脚本也不会打印 API Key。

其中 `01`—`04`、`07`、`09` 和 `10` 会调用 DeepSeek API；`05`、`06`、`08` 和 `11` 不调用模型，可以离线观察 Tool、State、Schema、Evidence、Artifact、Checkpoint 与 Interrupt 的代码结构。

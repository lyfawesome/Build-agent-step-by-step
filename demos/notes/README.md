# 两个对话的 Agent 学习手册

[返回十一个 demo](../README.md)

本手册合并当前对话与指定对话[《代码实例学习》](codex://threads/01a06600-a6e2-7302-ab03-3cda43ab87dd)中的技术学习内容，以 `demos` 为实践入口。它是去重、校正后的知识笔记，不是聊天全文备份；仓库拉取、提交、推送等操作记录不冒充技术教程。

## 怎么读

| 顺序 | 笔记 | 对应实例或问题 |
| --- | --- | --- |
| 1 | [模型 API、响应与工具调用](01_model_api_and_tool_calling.md) | demo 01—04；接口层级、choices、工具参数、执行与结果回传 |
| 2 | [函数包装、文档字符串与 Schema 边界](05_langchain_tool_and_schema.md) | demo 05；已保留的详细笔记，含位置/引号/多段字符串和约束表 |
| 3 | [Pydantic 是什么](05b_pydantic_basics.md) | BaseModel、数据实例、校验、序列化、Schema 与输入模型类 |
| 4 | [LangChain、LangGraph、节点与路由](06_langgraph_and_agent_architecture.md) | demo 06—07；框架关系、State 更新、节点形态、人工审批 |
| 5 | [数据层、Evidence 与 Artifact](08_data_contracts_evidence_artifacts.md) | demo 08；结构、引用、真实文件、哈希与工程放行 |
| 6 | [上下文、记忆与压缩](09_context_memory_and_compaction.md) | 指定对话后半段；为什么存储历史不等于模型看见历史 |
| 7 | [本地部署、模型规模与性能观测](10_local_deployment_and_observability.md) | 指定对话；推理引擎、内网边界、模型/硬件评估、追踪 |
| 8 | [项目推进节奏、术语与讨论覆盖表](11_learning_path_and_coverage.md) | 两个对话的自测、易错结论修正、跨文件阅读入口 |
| 9 | [create_agent 与可恢复工作流](12_create_agent_and_resumable_workflows.md) | demo 10—11；预制 Agent 上限、Checkpoint、Interrupt 和恢复 |

编号延续学习主题：`05b` 是 05 的基础补充；笔记编号与可执行 demo 编号不要求一一对应。

## 十一个脚本各证明什么

| Demo | 输入 | 实际执行与观察 | 是否调用模型 |
| --- | --- | --- | --- |
| [01](../01_model_returns_tool_call.py) | 问题、手写工具定义、指定工具名 | 观察模型返回工具请求，不执行该工具 | 是 |
| [02](../02_send_tool_result_back.py) | 查询 CPP-002 | 执行本地函数，把不存在的业务结果回传，再问模型 | 是，两次请求 |
| [03](../03_model_selects_from_multiple_tools.py) | 三个候选工具与一个问题 | 观察选择和参数，不执行候选工具 | 是 |
| [04](../04_extract_arguments_and_call_tool.py) | 起止角度的自然语言 | 解析 arguments，用 `**arguments` 调真实函数 | 是，之后本地计算 |
| [05](../05_langchain_wrap_function_as_tool.py) | Python 函数声明 | 包装、导出 Schema、直接 invoke | 否 |
| [06](../06_langgraph_pure_tool_node.py) | 结构化初始 State | 一个纯工具节点返回 State 更新 | 否 |
| [07](../07_langgraph_llm_tool_workflow.py) | 消息列表 | LLM 选择 → 本地工具 → LLM 回答 | 是 |
| [08](../08_schema_evidence_artifact.py) | 示例 State、Schema、计算文件 | 校验结构及跨对象引用，核对文件哈希 | 否 |
| [09](../09_structured_output_parsing.py) | 调距桨故障现象 | 将模型输出解析并校验为 Pydantic 对象 | 是 |
| [10](../10_create_agent_minimal.py) | 项目功率查询 | 对照 `create_agent()` 与手工 LangGraph 工具循环 | 是 |
| [11](../11_langgraph_interrupt_and_resume.py) | 缺项输入与模拟复核 | Checkpoint、两次暂停及同线程恢复 | 否 |

## 阅读时的证据标签

- **本地代码事实**：由当前十一个脚本、输入文件或已安装库核对。
- **当前对话实验**：例如 docstring 边界、Pydantic Schema 输出，不调用外部模型。
- **指定对话历史实测**：该对话曾报告 DeepSeek 普通对话、流式、JSON、工具调用和适配器测试通过；本轮未再次用账号请求模型，不能写成此次实测。
- **机制说明**：由官方资料与本地实现支持；某个框架有此能力，不代表当前 demo 已配置它。
- **历史建议/待确认**：型号推荐、价格、吞吐、部署预算、压缩阈值和学习周数，不是永久规格或已验收能力。

读取指定任务时，任务接口有部分消息正文为空；已补读该任务对应的本地会话文件中的用户与助手消息。未把工具原始输出、隐藏推理、凭据或环境文件复制到笔记。原始对话仍通过上方任务链接追溯。

本轮核对的本地包版本：`openai 2.53.0`、`langchain 1.3.14`、`langchain-core 1.5.3`、`langgraph 1.2.10`、`pydantic 2.13.4`。教程中的符号位置与默认行为应随版本复核。

整理核验（2026-09-06）：本手册及 demo 目录说明的本地文件链接、代码围栏和 26 段 Python 示例语法检查通过；离线运行 demo 05、06、08 成功，08 的示例引用及文件哈希检查通过，仍保持未放行状态。未运行需请求模型的脚本；语法检查也不等于所有教学片段都可脱离上下文直接执行。

## 与工程项目的关系

这些 demo 是教学片段，不是生产执行器。调距桨工程原型另见 [cae-agent-cpp 的 MVP 跨文件代码阅读地图](https://github.com/lyfawesome/cae-agent-cpp/blob/main/cpp_design_agent_mvp/docs/12_code_reading_guide.md)。不要把教学数据 Schema、教学字典或模拟审批直接当作工程项目的批准基线。

贯穿全手册的工程要求：产品族范围不是完整项目输入；缺少关键事实、适用规则或批准证据时，保持 `DRAFT / INCOMPLETE` 并列出 `open_issues`，不能自动补默认值后升级放行。

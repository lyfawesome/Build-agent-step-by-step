# 项目推进节奏、术语与讨论覆盖表

[返回学习手册](README.md)

这份文档是两个对话的阅读导航和自测清单。它按问题合并重复内容，不按聊天顺序复印回答；此前过于绝对的说法以这里的边界说明为准。

## 1. 从当前理解程度继续学

你已经理解“模型提出工具调用请求，由 Python 真正执行，再把结果发回模型”。下一步不必先读完整本框架教材，可以沿着现有实例逐层增加一个概念。

| 阶段 | 先读 / 运行 | 必须能自己解释 | 再做的小实验 |
| --- | --- | --- | --- |
| 接口 | demo 01—04；[API 笔记](01_model_api_and_tool_calling.md) | 请求中工具定义与响应中调用请求的区别；谁执行函数 | 修改问题，比较工具名、参数与最终返回 |
| 包装 | demo 05；[Schema 边界](05_langchain_tool_and_schema.md)；[Pydantic](05b_pydantic_basics.md) | 为什么生成 required，为什么不理解函数体业务 | 增加默认值、可空类型、Field 约束，比较 Schema 与错误 |
| 状态流转 | demo 06；[节点笔记](06_langgraph_and_agent_architecture.md) | 节点返回的是状态更新，compile 不是执行任务 | 增加一个纯规则节点，观察输入 State 和更新值 |
| 模型与图组合 | demo 07 | bind_tools 不执行工具，ToolMessage 的关联作用 | 比较原始 SDK tool_calls 与 LangChain 规范化结构 |
| 数据可追溯 | demo 08；[数据层笔记](08_data_contracts_evidence_artifacts.md) | Schema 合法、引用闭合、文件未变和工程正确的区别 | 在副本中改引用或文件内容，观察不同检查发现什么 |
| 工程阅读 | [cae-agent-cpp 的 MVP 跨文件阅读地图](https://github.com/lyfawesome/cae-agent-cpp/blob/main/cpp_design_agent_mvp/docs/12_code_reading_guide.md) | 输入从哪里进入、何处校验、谁决定迁移、何处阻止放行 | 追踪一个缺失输入从接收到 open_issues 和结束状态 |
| 运行保障 | [上下文](09_context_memory_and_compaction.md)、[部署观测](10_local_deployment_and_observability.md) | 存储不等于进入上下文；任务数不等于模型并发 | 记录一次任务的模型次数、工具次数、耗时和失败原因 |

每次只改变一个因素并保留前后输出。学习速度以能解释数据流、能构造失败案例为标准，不承诺固定几周就达到工程交付能力。

## 2. 怎么运行，不误触模型请求

在 `demos` 目录、已安装所需依赖的 Python 环境下：

```bash
python 05_langchain_wrap_function_as_tool.py
python 06_langgraph_pure_tool_node.py
python 08_schema_evidence_artifact.py
```

以上三个脚本不调用 LLM，适合先观察结构。01—04、07 会使用模型接口，运行前确认环境配置和允许发送的数据。已有解释器可直接使用，无需因为整理笔记而重建环境或升级依赖。

教学脚本仍刻意省略了不少生产保护措施。例如基础示例只处理第一个工具调用，尚未覆盖所有网络错误和重试结果；`auto` 也不保证一定返回调用请求。读懂教学路径后，再逐项增加完整参数校验、并行工具结果、权限、幂等和审计，不把整个复杂框架一次塞进一个 demo。

## 3. 当前对话的学习内容覆盖表

| 讨论的问题 | 记录位置 | 核心结论 |
| --- | --- | --- |
| client.chat.completions.create 为什么有多层；Responses 又是什么 | [01](01_model_api_and_tool_calling.md) | SDK 资源组织与方法，不是必须逐层继承的四个类 |
| 各家工具 JSON 是否统一，type、parameters、properties、required | [01](01_model_api_and_tool_calling.md) | 内部可用 JSON Schema，外层 API 协议并不全球统一 |
| choices[0]、多候选 n、完整响应、finish_reason | [01](01_model_api_and_tool_calling.md) | SDK 接受某参数不等于服务支持；message 不等于整个 response |
| tool_choice、extra_body、thinking | [01](01_model_api_and_tool_calling.md) | 选择约束、额外请求字段、厂商字段是不同概念 |
| 模型是否按相似度选工具，是否概率性 | [01](01_model_api_and_tool_calling.md) | 模型结合上下文生成调用，不等于固定相似度匹配算法 |
| 工具参数如何提取、如何传入 Python、如何等待和回传 | [01](01_model_api_and_tool_calling.md) | JSON 字符串解析、白名单执行与结果关联由应用负责 |
| @tool 类似继承还是宏；包装增加什么 | [05](05_langchain_tool_and_schema.md) | 装饰器将函数名绑定到工具对象，不是 C++ 文本宏展开 |
| invoke 是什么意思，还有哪些同级方法 | [05](05_langchain_tool_and_schema.md) | 调用接口；异步、批量、流式是不同执行方式 |
| docstring 的位置、引号、多段字符串及描述提取 | [05](05_langchain_tool_and_schema.md) | Python 先认定 __doc__，LangChain 再使用；不是任意字符串 |
| Schema 自动推断有多智能；必填、可空、范围、枚举等边界 | [05](05_langchain_tool_and_schema.md) | 读取声明和约束，不自动从函数体或自然语言补业务规则 |
| Pydantic 是什么 | [05b](05b_pydantic_basics.md) | 数据模型、校验、转换和序列化库，与 LLM 无关 |
| 节点是否都是 LLM + Tool；八组合是否覆盖完整设计 | [06](06_langgraph_and_agent_architecture.md) | 三个布尔维度只构成一种分类，不是完整节点定义 |
| 路由是什么，节点间如何迁移 | [06](06_langgraph_and_agent_architecture.md) | 决定下一步去哪，可按规则，也可使用受约束模型输出 |
| 副作用、人工暂停、权限、证据、重试是否只是三元素的属性 | [06](06_langgraph_and_agent_architecture.md) | 可由代码和数据实现，但仍是必须单独设计的控制维度 |
| Tool 为什么与 Python 脚本分列 | [06](06_langgraph_and_agent_architecture.md) | Tool 是对外能力接口，Python 是实现方式，两者可以重叠 |
| State / Schema / Evidence / Artifact 如何设计 | [08](08_data_contracts_evidence_artifacts.md) | 当前事实、结构契约、依据、实际产物各司其职 |
| 任意输入输出都能有 Schema 吗 | [08](08_data_contracts_evidence_artifacts.md) | 可以；只有执行校验并处理失败，约束才生效 |
| 授权工程师、质量角色是不是人格提示词 | [06](06_langgraph_and_agent_architecture.md) | 真实审批需要身份、权限和批准对象版本，提示词不授予权力 |
| 产品族数据与项目完整输入；缺失输入怎么办 | [08](08_data_contracts_evidence_artifacts.md) | DRAFT / INCOMPLETE 与 open_issues，不可默认补齐后放行 |
| 架构怎么读、如何跨函数跨文件理解 | 本章、[cae-agent-cpp 的 MVP 阅读地图](https://github.com/lyfawesome/cae-agent-cpp/blob/main/cpp_design_agent_mvp/docs/12_code_reading_guide.md) | 追踪一条数据与决策链，比只按文件顺序阅读更有效 |
| 环境配置不提交是否还能运行，密钥安全怎么理解 | [01](01_model_api_and_tool_calling.md)、[10](10_local_deployment_and_observability.md) | 代码、无密钥模板、实际凭据分离；忽略规则不是历史安全证明 |

## 4. 指定对话《代码实例学习》的覆盖表

| 讨论的问题 | 记录位置 | 边界或修正 |
| --- | --- | --- |
| 保密单位本地模型与个人编码 Agent 如何规划 | [10](10_local_deployment_and_observability.md) | 分离专业工作流与编码权限，共享服务不等于共享所有数据 |
| LangChain / LangGraph 能否离线 | [10](10_local_deployment_and_observability.md) | 框架本地运行与模型、追踪、下载是否外联要分别检查 |
| LangSmith 是什么，能否自托管，替代方案 | [10](10_local_deployment_and_observability.md) | 支持自托管，但有许可条件；候选方案逐项核对版本许可 |
| 国产开放模型与 coding harness 的区别、选型 | [10](10_local_deployment_and_observability.md) | 模型、引擎、应用是不同层，历史名单不是本轮推荐排行 |
| B/T、Dense/MoE、激活参数、量化、KV cache | [10](10_local_deployment_and_observability.md) | 活跃计算参数不等于总存储；权重估算不等于部署显存 |
| GPU 规格、预算与 HTML 说明 | [10](10_local_deployment_and_observability.md) | 保留历史文件索引，不把旧估算当当前报价 |
| LangChain / LangGraph 区别、先后与依赖、主要组件 | [06](06_langgraph_and_agent_architecture.md) | 不是初级与高级，也不是所有 LangChain 操作都使用图 |
| 先学什么、读哪些材料、项目推进节奏 | 本章 | 先最小调用，再状态流转，使用官方概念资料按问题补读 |
| vLLM / SGLang / Ollama；已有 API 是否还要部署引擎 | [10](10_local_deployment_and_observability.md) | 托管 API 省去自身推理服务运维，不省去应用安全和评估 |
| 已配置 DeepSeek 是否支持所需能力 | [01](01_model_api_and_tool_calling.md)、[10](10_local_deployment_and_observability.md) | 历史测试与本轮离线核对明确分开 |
| 超上下文怎么办；裁剪摘要是否等于全新对话 | [09](09_context_memory_and_compaction.md) | 下一次推理重新处理所给上下文，但不必更换业务任务或丢失外部状态 |
| Codex / Claude / DeepSeek harness 的压缩机制 | [09](09_context_memory_and_compaction.md) | 讨论通用原理，不假定各产品内部实现和阈值相同 |

## 5. 最容易混淆的等号

下面这些都不能直接画等号：

- 模型返回工具调用请求 ≠ 工具已经执行成功。
- JSON 能解析 ≠ 参数通过 Schema ≠ 业务正确 ≠ 获准执行。
- 类型标注 ≠ Python 自动运行时类型检查。
- `required` ≠ 不允许 `null`；默认值 ≠ 客户确认值。
- `@tool` ≠ 自动接入模型；`bind_tools` ≠ 自动运行函数。
- 节点执行完成 ≠ 工程阶段批准；模拟人工结果 ≠ 真实身份授权。
- 状态中有一个字符串引用 ≠ 对应文件存在、内容可信或版本适用。
- 有 checkpoint ≠ 外部副作用自动恰好执行一次。
- 历史已保存 ≠ 全部历史都进入当前模型上下文。
- API 接口兼容 ≠ 模型能力、计费、限制和错误行为一致。

## 6. 从学习进入项目时，先检查哪些边界

在无法新增输入数据源的约束下，仍然可以完善校验、缺失项、版本绑定、权限、审计和失败恢复。不能用模型编造缺失数据来掩盖来源不足。

建议以当前工程为对象，逐个回答：输入在哪里校验？字段来源怎么追踪？哪些值只是候选？规则在哪里配置？谁能批准？批准绑定哪个版本？哪个条件阻止放行？重试会不会重复触发外部动作？如何证明输出文件对应本次计算？

业务调整空间应体现在显式配置、规则版本、适配器和清晰的数据契约中，而不是让模型自由改动安全门槛。规则修改后需要重新校验受影响的输入、证据与批准；“便于调整”不等于“绕过放行条件”。

最小测试集先覆盖成功、缺失字段、类型错误、超范围、未知工具、工具失败、证据缺失、版本变更和未批准输出，再按真实任务扩展。测试数量、模型输出漂亮程度和流程能跑通，都不能单独证明设计结果可放行。

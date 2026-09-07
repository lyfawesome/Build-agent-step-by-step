# 06—07：LangChain、LangGraph、节点与路由

[学习总目录](README.md) · [下一篇：数据层](08_data_contracts_evidence_artifacts.md)

## 1. 框架关系：高层与底层，不是初级与高级

LangChain 提供模型、消息、提示词、工具、检索、输出处理和高层 Agent 等组件。LangGraph 提供状态化图执行能力，让开发者显式组织节点、边、分支、循环及暂停恢复。

当前 LangChain 的 `create_agent` 使用 LangGraph 运行时，但不能由此推出“每个 LangChain Tool 或模型调用都必须经过图”。LangGraph 节点也不要求使用 LangChain 高层 Agent；可以调用普通 Python 函数或自定义模型客户端。[LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)

指定对话讨论过发布时间：LangChain 先出现，LangGraph 后来针对状态化 Agent 编排需求发展出来，新版高层 Agent 再使用这一运行时。历史先后不等于今天的依赖方向；这里不把旧教程的具体 API 当成当前推荐接口。

“LangChain = 模型随意做事，LangGraph = 自动安全”同样不准确。高层 Agent 可以有严格中间件，图内也可以放模型自主循环；安全取决于你写的约束、身份和执行边界。

## 2. LangChain 常见组件在项目里的位置

| 组件 | 做什么 | 对应阅读 |
| --- | --- | --- |
| Model | 连接模型服务，组织生成请求 | `demo_config.get_langchain_chat_model` |
| Message | 表达 system/user/assistant/tool 等消息 | demo 07 的四类消息对象 |
| Prompt | 模板化组织指令与当前资料 | demo 07 的 SystemMessage；不等于权限 |
| Tool | 封装查询/计算等可调用能力 | demo 05 |
| Structured Output | 让输出以预期字段返回并检查 | Pydantic 笔记；不是任意 JSON 都合格 |
| Runnable / LCEL | 统一调用与短流程组合 | `invoke`；`prompt \| model \| parser` 是组合表达式 |
| Agent | 封装模型与工具循环 | 当前 07 手动写出步骤，未使用 create_agent |
| Middleware | 在调用前后插入通用处理 | 权限、预算、摘要等；当前 demo 未配置 |
| Document | 文本及来源元数据 | 后续 RAG 的基础载体 |
| Loader / Splitter | 读取文档、切分片段 | 必须保留版本、章节、表格等定位信息 |
| Embedding / Vector Store | 文本向量化及索引 | 不是把知识训练进生成模型 |
| Retriever / Reranker | 检索候选及重排序 | 后续受控知识接入，八个 demo 未实现完整 RAG |
| Memory / Store / Checkpointer | 管理短期状态、跨任务信息与恢复 | 不会自动扩展模型上下文窗口 |

“核心工具”可能指这些框架组件，也可能专指 Agent 可调用的 Tool，交流时要明确。

## 3. demo 06：一个不含 LLM 的图

按代码顺序看：

1. `@tool` 包装调距时间函数。
2. `PitchState(TypedDict)` 描述状态字段。
3. `run_pitch_time_tool(state)` 取出三个输入字段，调用 Tool，返回 `{"tool_result": result}`。
4. `StateGraph(PitchState)` 建立图定义。
5. `add_node` 注册名字和执行函数，`add_edge` 连接顺序。
6. `compile()` 生成可执行图，不立即运行。
7. `graph.invoke(initial_state)` 才启动执行，返回最终状态。

路线只有：`START → run_pitch_time_tool → END`。节点返回的是状态更新，不必返回整个 State，也不必直接原地修改传入字典。[LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)

`TypedDict` 主要提供静态类型信息。demo 初始 State 没有 `tool_result`，运行后由节点补上；这不等于 TypedDict 自动做了运行时必填验证。生产输入检查要另行实现。

## 4. demo 07：消息状态、工具绑定与三节点流程

```text
START
  → select_tool_with_llm
      → 有 tool_calls：run_tools → write_final_answer → END
      → 无 tool_calls：write_final_answer → END
```

`llm.bind_tools(tools, tool_choice="required")` 生成带工具配置的模型调用对象，不执行本地函数。调用之后得到的 `AIMessage.tool_calls` 已由适配器规范化，常见字段是 `name/args/id`；其中 `args` 已是字典，不同于原始 SDK 的 JSON 字符串 `function.arguments`。

`tools_by_name` 是本地白名单映射。`run_requested_tools` 查表取得 Tool，真实调用 `invoke(args)`，再建立 `ToolMessage`。第二个模型节点收到这些消息才整理最终回答。

`MessagesState.messages` 使用 `add_messages` 合并规则：通常追加新消息，已有相同 ID 时可替换；不是简单对所有字典字段都做列表拼接。普通 State 字段没有自定义 reducer 时，更新通常替换相应字段。多个并行节点写同一字段时必须设计合并规则，不能假定框架猜得出正确结果。

07 是有限的教学流程，不是通用无限 Agent 循环；其中 `for tool_call ...` 顺序执行工具，不能因模型一次给出多个调用就称它并行。

## 5. 路由是什么

路由就是“决定接下来走哪个节点”。demo 的代码：

```python
def route_after_llm(state):
    last_message = state["messages"][-1]
    return "run_tools" if last_message.tool_calls else "write_final_answer"
```

模型影响了 `tool_calls` 是否存在；Python 判断它并决定允许走的路线。这是“模型产出数据 + 程序执行路由”，不是路由函数本身一定调用模型。

固定边是总走同一步；条件边依据状态选择。路由通常只是读取 State，返回目标或分支标签；它可以在节点外作为条件函数，并不一定是独立业务节点。需要语义分类时可以使用 LLM，但要对它给出的标签设允许集合与兜底路径。

## 6. 一个节点可以装什么

节点是执行单位，不是固定的 LLM+Tool 模板。可执行纯规则、工具、LLM、多次工具、LLM 与工具组合，也可在其中组织子图或受控子 Agent。

沿“是否调用 LLM、是否调用工具、是否更新图 State”三个布尔轴，确实可以列八种组合，但这只是分类切片，不是 Agent 世界只有八种节点。数学上是 2×2×2；Python 写组合数量应写 `2 ** 3`，不能把连写幂运算当成同一个意思。

| LLM | Tool | 更新图 State | 可能用途与边界 |
| --- | --- | --- | --- |
| 否 | 否 | 否 | 控制同步点、等待或诊断；是否单独建节点由流程需要决定 |
| 否 | 否 | 是 | 纯 Python 数据变换、规则判断 |
| 否 | 是 | 否 | 外部读取后输出事件，或外部写动作；需另做记录和副作用管理 |
| 否 | 是 | 是 | demo 06 的纯工具节点 |
| 是 | 否 | 否 | 通过事件流输出解释而不更新图 State；不一定没有意义 |
| 是 | 否 | 是 | 解析、分类、解释节点 |
| 是 | 是 | 否 | 组合调用但结果不进入图 State；外部动作必须可追踪 |
| 是 | 是 | 是 | 混合节点，可在复杂时拆分便于检查和恢复 |

“不更新图 State”不等于“没有效果”，它可能写文件、输出事件、计费或调用外部系统。Tool 本身可以是 Python 函数，所以“Python 脚本”和“Tool”也不是互斥技术种类；前者描述实现载体，后者描述系统赋予它的调用接口。

## 7. 完整设计还要记录哪些维度

| 维度 | 要回答的问题 | 可由什么实现 |
| --- | --- | --- |
| 输入/输出契约 | 读什么、写什么、是否允许缺项 | Schema、类型和运行时校验 |
| 副作用 | 会不会写库、发消息、启动任务 | 工具适配器、事务、幂等键、回执 |
| 人工暂停 | 等谁、等哪个对象、如何恢复 | 待办、审核接口、interrupt 或应用状态机 |
| 路由 | 允许走哪些步骤 | 固定边、条件代码、经校验的模型标签 |
| 权限 | 谁能看、谁能执行/批准 | 可信身份、权限检查与隔离 |
| 证据 | 本结论源自何处与哪版内容 | 来源定位、版本、哈希与批准记录 |
| 重试/恢复 | 故障后从哪里继续、会不会重复写 | Checkpoint、任务表、CAS、幂等性 |
| 资源预算 | 最多几次调用、多少时间和并发 | 超时、调用次数限制、并发控制 |

这些最终会用代码、State 和工具实现，但概念上不能省去。仅知道“三个布尔值”无法推断权限、安全、失败语义和放行条件。

## 8. Agent 的原子单元与节点交叉关系

| 单元 | 职责 | 与节点的关系 |
| --- | --- | --- |
| State | 保存任务数据和流程位置 | 节点读取/产生更新 |
| Schema | 定义结构与约束 | 可用于所有输入输出边界，须实际执行校验 |
| Node | 一次受控执行 | 可含零到多次模型/工具调用 |
| Edge / Router | 决定执行顺序 | 连接节点，不必是 LLM |
| Policy / Guardrail | 定义许可和拒绝条件 | 在入口、执行前后和放行点生效 |
| Tool | 调用外部或本地能力 | 被节点或 Agent 执行器调用 |
| LLM Call | 解析、生成、规划、解释 | 只是节点可选能力 |
| Human Task | 人工补充、评审、签署 | 暂停与恢复的受控事件 |
| Event / Checkpoint | 记录变化、支持恢复 | 不等于自动保证外部操作只执行一次 |
| Evidence | 可追溯依据 | 支撑数据、计算与审批结论 |
| Artifact | 图纸、报告、仿真文件等产物 | 节点生成或引用，通常存外部文件/对象库 |
| Evaluator | 测试正确性、越权和失效情境 | 可离线测试，也可作为在线检查组件 |

## 9. “授权工程师/质量角色”不是换个提示词

模拟角色提示词可以辅助解释或生成审查建议，但没有真实权限效力。工程审批至少绑定可信人员身份、项目范围、角色、待审内容版本/哈希、决定时间和审计记录，并禁止不允许的自审或过期批准。

是否需人工审查可以由确定性政策决定；LLM 可以提供风险线索，但不能自行宣布免审。信息缺失不应交给模型“判断应该没问题”。

当前 MVP 用应用执行器保存等待状态并由受控 `approve` 方法处理决定；其 LangGraph 适配器不使用 `interrupt/Command(resume=...)`。不要把 LangGraph 提供的某种机制写成当前代码已经使用它。

## 自测

能否指出 06 的更新字段、07 的消息合并规则、route 的条件，以及“模型决定使用功率工具”与“程序决定下一步执行工具节点”的区别？随后阅读 [cae-agent-cpp 的 MVP 执行器地图](https://github.com/lyfawesome/cae-agent-cpp/blob/main/cpp_design_agent_mvp/docs/12_code_reading_guide.md)，观察比教学图多出的控制层。

# create_agent 与可恢复 LangGraph 工作流

[学习总目录](README.md) · [create_agent 对照示例](../10_create_agent_minimal.py) · [暂停恢复示例](../11_langgraph_interrupt_and_resume.py)

## 1. create_agent 的最低条件

只有模型也能创建 `create_agent(model=model)`，但这时图里没有 Tool 节点，实际是单模型调用。要形成最小工具调用 Agent，需要：

1. 一个能产生 Tool Calling 响应的聊天模型；
2. 至少一个普通函数或 LangChain Tool；
3. 清晰的工具名称、用途说明和参数类型；
4. `create_agent(model, tools)`；
5. 以 `{"messages": [...]}` 形式调用编译后的图。

模型返回工具请求不代表工具已执行。`create_agent` 内部的 Tool 节点负责执行，生成 `ToolMessage`，再把消息交回模型。

## 2. create_agent 的核心拓扑

最小拓扑是：

```text
START
  ↓
model
  ├─ 没有 tool_calls → END
  └─ 有 tool_calls → tools
                       ↓
                     model
```

因此 `create_agent()` 返回 `CompiledStateGraph`。第 10 个 demo 同时打印高层接口生成的图，以及使用 `StateGraph`、`ToolNode` 和 `tools_condition` 手工构建的行为等价图。

## 3. 可以扩展什么

`create_agent` 可以配置系统提示、静态或动态工具、Middleware、结构化最终输出、自定义 State、运行时 Context、Checkpointer、长期 Store、节点前后 Interrupt、缓存、流式处理和子图名称。

Middleware 可以在模型或工具调用前后实现动态提示、工具权限过滤、模型切换、日志、错误处理、重试、限流和人工确认。工具数量没有一个由 `create_agent` 单独规定的固定上限，但会受到模型上下文、工具选择准确率、延迟、并发和可测试性的实际限制。

## 4. create_agent 的架构边界

如果任务可以描述为“模型反复选择下一项工具，直到给出答案”，适合使用 `create_agent`。

如果任务要求强制阶段顺序、多个工程门禁、指定位置循环、并行模块、失败补偿、明确的重试上限或独立质量签署，应使用显式 LangGraph。调距桨专业 Agent 更适合外层使用确定性 StateGraph，只在需求理解、检索查询生成和报告草拟等局部节点中使用 `create_agent`。

## 5. Checkpoint、thread_id 与 Interrupt

Checkpoint 保存的是图执行状态。`thread_id` 标识具体工作流实例；恢复时必须继续使用相同的 `thread_id`，否则会得到另一条独立状态链。

节点调用 `interrupt(payload)` 后，LangGraph 保存状态并把暂停载荷返回给外部应用。外部取得补充输入或人工决定后，通过 `Command(resume=value)` 恢复。恢复时暂停节点会从开头重新执行，因此在 `interrupt()` 之前不要放置不可重复的外部副作用。

第 11 个 demo 依次演示：

```text
缺少字段 → 暂停
补充字段 → 恢复
人工复核 → 再次暂停
提交复核结果 → 恢复
确定性计算 → DRAFT_COMPLETE
```

`InMemorySaver` 只在当前 Python 进程中保存状态，适合教学和单元测试。跨进程、程序重启或多实例服务需要数据库支持的持久化 Checkpointer，并同时设计事务、幂等键、身份认证、权限和审计。

## 6. 工程安全边界

- `actor_id` 字符串不是身份认证结果；真实身份必须由受信系统注入。
- `approved=true` 不是工程签署；批准必须绑定 State 版本、知识快照和制品哈希。
- Checkpoint 能恢复执行，不会自动保证外部工具恰好执行一次。
- 模型可以建议调用工具，不能自行提升权限或绕过工程门禁。
- 教学示例的计算常数和模拟批准始终保持 `DRAFT`，不能直接进入制造放行。

## 7. 官方参考

- [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [LangChain Middleware](https://docs.langchain.com/oss/python/langchain/middleware/overview)
- [LangChain Structured Output](https://docs.langchain.com/oss/python/langchain/structured-output)
- [LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)

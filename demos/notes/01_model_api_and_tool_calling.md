# 01—04：模型 API、响应对象与工具调用闭环

[学习总目录](README.md) · [下一篇：函数包装与 Schema](05_langchain_tool_and_schema.md)

## 1. `client.chat.completions.create` 不是四个嵌套类

| 表达式部分 | 实际角色 |
| --- | --- |
| `client` | SDK 客户端对象，持有连接、认证和请求配置 |
| `client.chat` | Chat 类接口的资源对象 |
| `client.chat.completions` | Chat Completions 资源对象，组织这个端点的相关方法 |
| `.create(...)` | 发起创建请求的方法，不是第四个类 |

一句话：`completions` 是 SDK 中组织“生成聊天补全”相关操作的资源层。

点号是 Python 属性访问。调用到 `create` 才发请求，是 SDK 的接口组织方式，不是 HTTP 协议规定必须写四层，也不是 DeepSeek 特有要求。其他 SDK 可以使用不同路径或函数名。

本项目 [demo_config.py](../demo_config.py) 构造 OpenAI SDK 客户端但把 `base_url` 指向 DeepSeek；“使用 OpenAI SDK”不代表“请求发给 OpenAI”。

## 2. 为什么又有 `responses.create`？

在 OpenAI 风格接口中，常见的几类生成入口是：

| 入口 | 核心输入/输出形态 | 怎样理解 |
| --- | --- | --- |
| `client.chat.completions.create` | 输入 `messages`，输出 `choices` | 消息式生成；本教学使用它 |
| `client.responses.create` | 输入 `input` 等，输出类型化 `output` 项 | 另一种统一生成与工具交互接口；SDK 可用 `output_text` 汇总文本 |
| `client.completions.create` | 输入 `prompt`，输出补全文本 | 旧式文本补全接口，不等于 `.chat.completions` |
| Realtime 类接口 | 持续双向事件 | 交互音频等实时会话，不是只换一个方法名 |

这些不是“全世界只有四种”。提供商可以有自己的 Messages、generateContent 等接口，同一家也有多种任务端点。Chat Completions 与 Responses 的请求和工具返回结构不同，不能机械改名字就迁移。[OpenAI 迁移指南](https://developers.openai.com/api/docs/guides/migrate-to-responses)

某服务兼容 Chat Completions 不代表支持 Responses。指定对话曾讨论 DeepSeek 的 Responses 能力，但本八个 demo 的配置与执行路径仍是 Chat Completions；其他端点应分别确认，不能由 Python 客户端有某个属性推断服务一定支持。

## 3. `tools` 的外壳与参数 Schema 是两种格式

demo 01 的请求结构：

```json
{
  "type": "function",
  "function": {
    "name": "get_project_power",
    "description": "根据项目编号查询额定功率。",
    "parameters": {
      "type": "object",
      "properties": {
        "project_id": {"type": "string"}
      },
      "required": ["project_id"]
    }
  }
}
```

- 外层 `type/function/name/description/parameters`：模型 API 的工具声明协议。
- `parameters` 内部：描述函数输入的 JSON Schema。
- `type: object` 不是“打开 JSON 模式”，而是规定参数整体是 JSON 对象；JSON 还可以表示数组、字符串、数字、布尔值和 null。
- `properties` 声明字段如何约束，`required` 声明哪些字段不能省略。定义了 properties 不等于所有字段都必填。
- 严格 JSON 不允许尾逗号；Python 字典允许尾逗号。聊天里 Python 代码不能不加区分地直接当 JSON 文件。

本次核对的 DeepSeek Chat 工具列表仅列 `function`；OpenAI 不同端点还可以有其他工具类别。具体枚举归属于具体接口，不能把 Responses 内建工具列表复制进 DeepSeek Chat 请求。[DeepSeek Chat 参考](https://api-docs.deepseek.com/api/create-chat-completion/)

不同厂商可能都采用 JSON Schema 描述参数，但外壳、支持的 Schema 子集、严格模式和消息回传规则不统一。LangChain 适配器可以做转换，却不能替后端创造不支持的能力。

## 4. 模型怎样知道当前应该用工具

应用每次请求显式提供可用工具及说明。模型结合当前问题、历史消息、系统要求和工具参数定义生成响应，可能产生工具名与参数。

这不是自动扫描你的电脑，也不必然是“算语义相似度最高就调用”。底层是条件生成；某些系统另有检索或路由，但不能把它当作所有模型工具选择的固定实现。

| `tool_choice` | 协议层意图 | 不保证什么 |
| --- | --- | --- |
| `auto` | 模型可回答，也可请求工具 | 不保证一定有 `tool_calls` |
| `none` | 不请求工具 | 不保证回答正确 |
| `required` | 要求请求一个或多个工具 | 不保证恰好一个、不保证选对 |
| 指定函数名对象 | 要求请求该工具 | 不代表函数已执行、参数正确、服务永不报错 |

上述约束以端点支持并成功响应为前提。超时、拒绝、截断、不支持的组合等仍要处理。demo 01/04 的“保证”注释应按这个前提理解，不能当成端到端成功保证。[函数调用机制](https://developers.openai.com/api/docs/guides/function-calling)

低温度可以减少采样波动，不是业务正确性或绝对可复现性的证明。对于关键步骤，应用应明确决定工具或路由，而非只写一句“你必须检查”。

## 5. 模型决定与真实执行为何分开

demo 02 的完整链：

```text
用户问题 + 工具定义
  → 第一次模型请求
  → assistant 返回 tool_calls（名字、参数、调用 ID）
  → 应用保存这条 assistant 消息
  → 应用用 json.loads 解析参数
  → Python 真正调用函数
  → 应用追加 role=tool 的结果消息，关联 tool_call_id
  → 第二次模型请求
  → 模型依据工具结果组织最终回答
```

这正是本地函数工具常见的规范交互方式。框架 Agent 可以把循环封装起来，但真正执行函数的仍是应用或工具执行服务，不是模型生成文本直接变成操作。由服务端托管的内建工具则可能在服务内部执行，不能与本地 Python 工具混为一谈。

demo 02 直接调用固定的本地函数，没有完整的参数校验和授权工具表。生产执行器应在真实调用前补上这些检查；上面的教学流程不能当作已经实现了安全门禁。

同步 demo 中，程序执行函数调用这一行并等待返回，之后继续运行；慢工具可以用异步任务，但届时需要任务状态、超时、回执和关联 ID。不是模型“在后台自动等到了你电脑上的函数”。

## 6. JSON 参数怎样成为 Python 实参

```python
import json

arguments_text = '{"project_id":"CPP-001","start_pitch_deg":-6,"target_pitch_deg":18}'
arguments = json.loads(arguments_text)
```

`arguments_text` 是文本，`arguments` 是 Python 字典。demo 04 中：

```python
tool_result = calculate_pitch_change_time(**arguments)
```

相当于：

```python
tool_result = calculate_pitch_change_time(
    project_id="CPP-001",
    start_pitch_deg=-6,
    target_pitch_deg=18,
)
```

`**` 按字典键名展开为关键字参数，不是按字典排列顺序猜位置。多余键、缺少必填参数都会影响调用；`json.loads` 只解析 JSON，不证明类型、单位、权限或工程范围正确。

当前 demo 用虚构恒定调距速度演示参数传递，其 8 秒结果不等于真实液压动态仿真。不要据此给客户作工程性能承诺。

## 7. 逐层读懂 response

| 路径/字段 | 含义与边界 |
| --- | --- |
| `response` | SDK 解析后的整次非流式响应对象 |
| `response.id` | 本次生成标识；不是项目 ID 或工具调用 ID |
| `created` | Unix 时间戳，通常为秒，不是耗时 |
| `model` | 服务报告的模型标识 |
| `object` | 响应对象类型，例如 `chat.completion` |
| `choices` | 生成候选列表，不是每个工具一项 |
| `choices[0]` | Python 零基索引的第一个候选，不表示已经按质量排名第一 |
| `choices[0].index` | 服务提供的候选索引 |
| `choices[0].message` | 该候选的 assistant 消息 |
| `message.content` | 普通文本；仅工具调用时可为空或 null |
| `message.tool_calls` | 工具请求列表；每项有调用 ID、类型、函数名与 arguments |
| `tool_call.id` | 用来把结果与本次具体调用关联；同一个工具可被调用多次 |
| `finish_reason` | 为什么此次候选停止生成，不是工具执行状态 |
| `logprobs` | 可选的 token 概率信息，不是工程置信度 |
| `refusal` | SDK/服务可能提供的拒绝信息；不保证所有服务使用该字段 |
| `function_call` | 旧协议字段；新代码优先读 `tool_calls` |
| `annotations` / `audio` | 可选扩展信息，当前纯文本 demo 不依赖 |
| `usage` | token 用量；总量通常为输入与输出用量之和 |
| `prompt_tokens` / `completion_tokens` | 输入/生成 token，不是汉字数 |
| 缓存命中/未命中字段 | 提供商的用量分项；不要与总输入量再次重复相加 |
| `system_fingerprint` | 后端配置标识信息，不是权重文件或证据的安全哈希 |
| `service_tier` / `moderation` | 服务扩展字段；缺失或 null 不等于已启用某能力 |

用户曾贴出的 352 tokens = 310 输入 + 42 输出，只是那次请求的历史用量，不是 demo 固定成本。缓存分项 256 与 54 合计为当时的 310 输入，不应另加一次。

### `model_dump_json` 到底有多“完整”

```python
message.model_dump_json(indent=2)   # 只导出 message 对象。
response.model_dump_json(indent=2)  # 导出整个 SDK response 对象。
```

两者都不是“模型所有内部信息”。后者包含 SDK 已解析响应字段，但不等于原始 HTTP 字节/响应头，也不包含未公开的模型内部推理。SDK 补出的 null/default 与原始响应的“未提供”也可能不同。

### finish_reason 常见值

| 值 | 含义 | 后续处理 |
| --- | --- | --- |
| `stop` | 自然停止或命中停止条件 | 仍需校验输出 |
| `length` | 达到生成等长度限制 | 检查截断，不执行不完整参数 |
| `tool_calls` | 返回工具调用请求 | 解析、鉴权、校验后执行 |
| `content_filter` | 内容过滤影响输出 | 不当作完整业务成功 |
| `function_call` | OpenAI SDK 中保留的旧函数调用结束值 | 兼容旧协议，不推荐新建流程依赖它 |
| `insufficient_system_resource` | DeepSeek 文档列出的推理资源不足中断 | 明确失败/重试策略，不当作成功 |

前五项可见于本机 OpenAI SDK 的类型定义；DeepSeek 文档的枚举与其不完全一致。流式中间块的 finish_reason 还可能是 null。不能把 SDK 类型声明当成所有兼容服务的完整枚举。

## 8. 多个候选与多个工具调用不是同一件事

部分 Chat 接口支持 `n` 指定多个生成候选；当前对话曾实际遇到 DeepSeek 的 `only n = 1 is supported` 错误。应将它记为该端点/当时配置的实测限制，不能因 SDK 接受 `n` 就认为后端支持。

不支持单次多候选时，应用可以显式发起多次请求再比较，但会增加 token/费用且不保证答案不同。多候选生成不等于授权执行所有候选中的工具，尤其不能把有写入副作用的候选全部自动执行。

`choices` 是回答候选维度；一个候选里的 `tool_calls` 是工具请求维度。`batch` 是应用组织多个调用的方式；三者不能互相替代。

## 9. `extra_body` 与 DeepSeek 参数

`extra_body` 是 OpenAI Python SDK 允许添加额外请求体字段的入口，不是 DeepSeek 发明的参数容器；它没有跨厂商固定的“全部可选项”。内部键由后端协议定义。

当前配置使用：

```python
extra_body={"thinking": {"type": thinking}}
```

它向实际请求体增加 `thinking` 对象，而不是要求后端接收一个名为 `extra_body` 的业务字段。当前 DeepSeek 文档列 `thinking.type` 为 `enabled/disabled`。思考强度等其他字段及 SDK 是否已有同名顶层参数，应按具体版本核对，不要复制一份永久参数清单。

`temperature`、`max_tokens`、`response_format`、`stream` 等已有 SDK 参数时通常直接使用相应入口。不要在两个位置写互相冲突的配置，也不要假设未知键会被安全忽略。

## 10. 配置、安全与教学代码的简化

[demo_config.py](../demo_config.py) 从脚本目录向上寻找第一个 `.env.local`，读取其中的配置；已有环境变量不会被默认覆盖。这里不会读取名为 `enve` 的特殊文件，“环境文件”的实际名字是 `.env.local`。

密钥文件保持本地、不提交；仓库共享变量名与无密钥模板。未推送密钥不会使已配置的本机环境自动失效，但新克隆/新机器必须重新安全配置。`.gitignore` 不会自动清除已经提交的秘密，不能用它证明历史从未泄漏；若真发生泄漏需撤销/轮换并处理历史。

当前任务未读取密钥值、未发模型请求、未替用户推送仓库。

demo 01/02/04 为突出机制，直接取 `[0]`；demo 02 用 `auto` 却假设一定返回调用；demo 07 的提示词要求一个工具但 `required` 协议并不限定恰好一个。生产版必须验证空响应、工具数量、名字白名单、参数、权限、超时、异常、截断、结果大小和幂等性。不要用 `eval` 执行模型生成代码。

## 自测

能否指出：哪一行发模型请求，哪一行真正执行函数，哪一个 ID 配对调用与结果，以及缺参数和项目不存在为何是不同类型的失败？能解释这些，再进入第 05 个 demo。

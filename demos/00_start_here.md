# 从这里开始：零基础 Agent 学习路线

[返回仓库首页](../README.md) · [Demo 说明](README.md) · [练习册](exercises/README.md) · [学习笔记](notes/README.md)

## 1. 这个仓库适合谁

本课程不要求你了解 LLM Agent，但默认你能阅读最基础的 Python。完全没有编程经验时，先掌握：

- 变量、字符串、数字、`list` 和 `dict`；
- `if`、`for`、函数参数和返回值；
- `class`、类型标注与装饰器的基本含义；
- JSON、HTTP API 和环境变量是什么；
- 如何在终端进入目录并运行 Python 文件。

不需要先学会异步编程、数据库、Web 后端或完整的 LangChain/LangGraph。

## 2. 先建立五个基本区分

1. 模型生成工具调用请求，不等于工具已经执行。
2. Python 函数是实现；Tool 是交给模型和框架使用的能力接口。
3. Schema 合法，不等于业务数据真实或工程结论正确。
4. Agent State 是应用状态；模型上下文只是某次推理实际看到的内容。
5. `create_agent()` 是预制工具循环；显式 LangGraph 用于确定性业务流程。

## 3. 准备独立环境

推荐使用 Python 3.11。不要把依赖安装进 Conda `base` 环境。

### Conda

```bash
conda env create -f environment.yml
conda activate build-agent-step-by-step
python -m pip install -r demos/requirements.lock.txt
```

### 标准 venv

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r demos/requirements.lock.txt
```

## 4. 两条学习路线

### 完全离线

```text
05 Tool 包装
→ 06 LangGraph State 与纯工具节点
→ 08 Schema / Evidence / Artifact
→ 11 Checkpoint / Interrupt / Resume
```

运行：

```bash
./run_offline_demos.sh
```

### 完整路线

```text
01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11
```

01–04、07、09、10 会调用 DeepSeek API。先复制配置模板：

```bash
cp .env.example .env.local
```

在 `.env.local` 中填写自己的 Key。不要提交该文件，也不要把客户资料写入教学问题。

## 5. 每个 Demo 学什么

| Demo | 核心问题 | 是否调用模型 | 主要输出 |
| --- | --- | --- | --- |
| 01 | 模型如何返回工具调用请求 | 是，1 次 | 工具名、JSON 参数、完整响应 |
| 02 | 工具结果如何回传给模型 | 是，通常 2 次 | Tool 结果与最终回答 |
| 03 | 模型如何在多个工具间选择 | 是，1 次 | 被选工具和参数 |
| 04 | 如何提取参数并调用 Python | 是，1 次 | 参数字典与确定性计算结果 |
| 05 | `@tool` 包装了什么 | 否 | 自动生成的 JSON Schema |
| 06 | 节点怎样读取和更新 State | 否 | 完整最终 State |
| 07 | LangGraph 怎样编排 LLM 与 Tool | 是，通常 2 次 | 完整消息序列 |
| 08 | 数据如何形成可核验引用链 | 否 | Schema、引用和哈希检查 |
| 09 | 如何获得结构化模型输出 | 是，1 次 | Pydantic 对象或解析错误 |
| 10 | `create_agent()` 隐藏了什么图 | 是，通常 4 次 | 两张图和两套消息序列 |
| 11 | 工作流怎样暂停和恢复 | 否 | 两次 Interrupt 和最终草案 |

模型输出具有概率性。“预期输出”指必须保持的结构和程序不变量，不要求自然语言逐字相同。

## 6. 正确练习方法

每次只改变一个因素，并记录：

```text
改动：
运行前预测：
实际结果：
保持不变的机制：
为什么与预测相同或不同：
```

先运行原始版本，再完成[练习册](exercises/README.md)。不要通过一次成功调用证明模型“总能理解”，至少重复运行或准备一组表达方式进行比较。

## 7. 安全边界

- Demo 数据和常数仅用于教学。
- `approved=true` 或 `actor_id` 字符串不是有效身份认证。
- 不把模型输出直接传给 Shell、数据库写入、CAD 或放行接口。
- 工具必须经过白名单、参数校验、权限检查和审计。
- 任何 API 示例都可能产生网络传输、费用和日志。

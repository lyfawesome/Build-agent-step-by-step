# Build Agent Step by Step

这个仓库保存 Agent 学习过程中形成的渐进式可运行示例和配套笔记。示例从原始 Tool Calling 协议开始，逐步覆盖 LangChain Tool、LangGraph State、结构化输出、`create_agent()`、Checkpoint、Interrupt 与恢复。

## 目录

- [渐进式 Demo](demos/README.md)：01—11 的可运行 Python 示例。
- [学习笔记](demos/notes/README.md)：模型接口、Schema、LangChain、LangGraph、上下文、本地部署与观测。
- [数据 Schema](schemas/design_state.schema.json)：第 08 个 demo 使用的教学 State Schema。
- [部署与成本 HTML](artifacts/Qwen3.8-27B_本地部署与成本说明.html)：国产模型本地部署术语、算力与历史成本估算。

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r demos/requirements.txt
cp .env.example .env.local
```

需要调用模型的示例运行前，请在 `.env.local` 中填写自己的 DeepSeek API 配置。离线示例可以直接运行：

```bash
cd demos
python 05_langchain_wrap_function_as_tool.py
python 06_langgraph_pure_tool_node.py
python 08_schema_evidence_artifact.py
python 11_langgraph_interrupt_and_resume.py
```

这些内容用于学习 Agent 的构建机制，不是经过工程批准的调距桨设计系统；示例数据、计算常数和模拟审批均不得直接用于工程放行。

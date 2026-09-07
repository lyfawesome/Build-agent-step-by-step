# 08：State、Schema、Evidence 与 Artifact

[学习总目录](README.md) · [示例代码](../08_schema_evidence_artifact.py)

## 1. 不是四种互斥数据，而是四种职责

| 概念 | 回答什么 | 典型内容 |
| --- | --- | --- |
| State | 当前项目知道什么、做到哪一步 | 原始/已确认输入、流程位置、未决项、产物引用 |
| Schema | 数据应该长什么样 | 类型、必填、状态枚举、嵌套结构 |
| Evidence | 凭什么作出这个结论 | 来源 ID、版本、页码/定位、内容指纹、批准状态 |
| Artifact | 实际生成或使用了什么文件 | 报告、图纸、BOM、计算 JSON、仿真文件 |

Evidence 元数据和 Artifact 引用可以保存在 State 里；大文件本体通常留在外部存储。它们不是“State 之外另外三个聊天窗口”。

## 2. 直接打开本项目的真实教学数据

- [完整示例 State](../data_layer_examples/design_state_with_evidence_artifact.demo.json)
- [实际计算文件 Artifact](../data_layer_examples/pitch_time_calculation.demo.json)
- [旧蓝图 State Schema](../../schemas/design_state.schema.json)

这些文件真实存在，但内容是教学数据，不是客户工程依据。例中有如下引用：

```text
calculations[CALC-PITCH-TIME-001]
  → evidence_ids: EVD-CALC-PITCH-TIME-001
  → evidence 中的 locator 指向 ART-CALC-PITCH-TIME-001
  → artifacts 记录实际 JSON 文件 URI 与内容哈希
  → 文件中保存教学输入、计算过程与结果
```

实际元数据还包含 `produced_by`、`revision`、`mime_type`、`maturity`、`approval_ids`。示例的产物为 `DRAFT`，证据批准为 `PENDING`，`release.allowed` 为 false。计算得到数值与获得批准完全不同。

## 3. demo 08 三层检查

1. 用 `Draft202012Validator` 检查 State 的结构、必填与枚举。
2. 用代码检查计算引用的 Evidence 存在、Artifact 关联同一 Evidence。
3. 读取 Artifact 文件字节，重算 SHA-256，与 State/Evidence 的记录比较。

这三层分别回答“形状对不对”“引用通不通”“文件是不是记录中的那一份”。哈希一致不证明公式正确、数据真实、知识适用或人员已批准。

脚本当前打印检查结果，某些失败并没有统一转成异常后停止全部流程，所以它是观察器而不是生产放行门禁。文件字节哈希对空格/换行敏感；当前 MVP 的 `canonical_hash` 则对规范化 JSON 内容取指纹，二者不能不经说明混用。

## 4. 任意输入输出边界都可以有 Schema 吗

原则上可以：用户输入、LLM 候选提取、工具参数、工具结果、节点 State 更新、审批请求、持久化记录、对外报告都可以声明契约。不是每个纯内部临时变量都必须独立建文件，但可信边界值得明确。

需要区分：有 Schema 文件、代码调用了校验器、错误会真正阻断流程，是三个条件。普通 `TypedDict` 不能代替运行时校验；JSON 语法合法也不等于满足业务 Schema。

推荐按数据成熟度分开：

| 数据形态 | 可以保存什么 | 不允许什么 |
| --- | --- | --- |
| 原始输入 | 客户原话、单位、来源 | 静默改写为默认值 |
| 解析候选 | 模型提取值、出处、冲突/置信度 | 自动成为批准事实 |
| 已校验输入 | 满足结构和业务前置条件的数据 | 自动等于人工批准 |
| 批准基线 | 审批对象、输入版本和证据绑定 | 新需求继续沿用旧签署 |
| 草稿产物 | 工具结果、执行版本、未决项 | 无批准直接放行 |

## 5. 产品族范围不是项目完整输入

客户提供的功率、直径、调距角、调距时间、液压压力和控制精度范围只描述产品族。具体项目还至少需要核对：船型/任务剖面、设计航速、轴系转速与旋向、发动机/电机特性、伴流、吃水、空泡、噪声/振动、冰区/海况、船级社与规范版本、安装空间、轴系接口、能源、冗余、安全/寿命、制造能力、成本/交期。

字段是否适用可以由经确认的业务条件规定，但“不适用”必须显式说明并保留依据，不能和“没填”混在一起。任一关键输入缺失时，只输出 `DRAFT / INCOMPLETE` 与明确 `open_issues`，不猜默认值再升级为可放行。

## 6. 旧蓝图与当前 MVP 的数据组织不同

当前工程核心将轻量 `WorkflowState` 与完整 `EngineeringProject` 分开，通过租户、项目、运行和修订关联。它还保存业务策略快照、知识哈希、逐阶段产物及人工批准记录。

- `WorkflowState` 不是全部工程数据：它主要记录运行游标、待审 ID、问题引用。
- `EngineeringProject` 保存事实、产物、批准和审计。
- 改输入/策略/知识需新修订，保留历史并使旧结论不可复用。
- 工具 `READY`、产物 `FROZEN`、流程 `DRAFT_COMPLETE`、制造放行是不同层级。

两个包的 Schema 不可交叉混用。继续看 cae-agent-cpp 的 [MVP 数据与调用链](https://github.com/lyfawesome/cae-agent-cpp/blob/main/cpp_design_agent_mvp/docs/12_code_reading_guide.md)和[配置与运行指南](https://github.com/lyfawesome/cae-agent-cpp/blob/main/cpp_design_agent_mvp/docs/10_configuration_and_runtime.md)。

## 7. 面向真实工具的接口清单

一个计算工具不只返回最终数值。逐步补齐：输入及单位、算法/求解器版本、执行 ID、状态、结果、检查项、证据引用、产物位置、错误分类和可否重试。外部写操作还要增加幂等键、回执和重复提交处理。

LLM 解释可以引用冻结结果，但不得改写事实。解释的证据 ID 要能解析到当前有权限、有效的内容，不能只在文本里出现一个貌似真的引用编号。

## 自测

如果把 Artifact JSON 中一个空格改掉，哪项检查可能变化？如果保持哈希一致但算法错误，哪些检查发现不了？如果 Schema 校验通过但审批仍是 PENDING，为什么不能放行？

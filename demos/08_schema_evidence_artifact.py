"""第八步：观察 Schema、Evidence 和 Artifact 如何共同支撑 State。"""

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator


demo_directory = Path(__file__).resolve().parent
blueprint_directory = demo_directory.parent

schema_path = blueprint_directory / "schemas" / "design_state.schema.json"
state_path = (
    demo_directory
    / "data_layer_examples"
    / "design_state_with_evidence_artifact.demo.json"
)

schema = json.loads(schema_path.read_text(encoding="utf-8"))
state = json.loads(state_path.read_text(encoding="utf-8"))

# 1. Schema 校验：检查数据结构、必填字段、类型和枚举是否合法。
validator = Draft202012Validator(schema)
schema_errors = sorted(validator.iter_errors(state), key=lambda error: list(error.path))

print("1. Schema 校验:")
if schema_errors:
    for error in schema_errors:
        location = ".".join(str(part) for part in error.path) or "<root>"
        print(f"- {location}: {error.message}")
else:
    print("- PASS：State 符合 design_state.schema.json")

# 2. Evidence：解释某个计算结果来自哪里，并指向真实制品文件。
calculation = state["calculations"]["CALC-PITCH-TIME-001"]
evidence_id = calculation["evidence_ids"][0]
evidence = state["evidence"][evidence_id]

print("\n2. 计算结果:")
print(json.dumps(calculation["outputs"], ensure_ascii=False, indent=2))
print("\n3. 支撑该结果的 Evidence:")
print(json.dumps(evidence, ensure_ascii=False, indent=2))

# 3. Artifact：真正的输出文件不直接塞进 State；State 只保存 URI 和元数据。
artifact_record = state["artifacts"][0]
artifact_path = demo_directory / artifact_record["uri"]
artifact_bytes = artifact_path.read_bytes()
actual_hash = "sha256:" + hashlib.sha256(artifact_bytes).hexdigest()

print("\n4. Artifact 元数据:")
print(json.dumps(artifact_record, ensure_ascii=False, indent=2))
print("\n5. Artifact 文件:")
print("- 路径:", artifact_path)
print("- 文件存在:", artifact_path.is_file())
print("- State 记录哈希:", artifact_record["content_hash"])
print("- 实际文件哈希:", actual_hash)
print("- 哈希一致:", actual_hash == artifact_record["content_hash"])

# 4. 交叉引用校验：Schema 很难表达的对象关系，由确定性代码检查。
evidence_exists = evidence_id in state["evidence"]
artifact_evidence_matches = evidence_id in artifact_record["evidence_ids"]
evidence_hash_matches = evidence["content_hash"] == actual_hash

print("\n6. 跨对象关系检查:")
print("- calculation 引用的 evidence 存在:", evidence_exists)
print("- artifact 引用了同一个 evidence:", artifact_evidence_matches)
print("- evidence 哈希与文件一致:", evidence_hash_matches)

print("\n7. 当前成熟度:")
print("- Artifact maturity:", artifact_record["maturity"])
print("- Evidence approval_status:", evidence["approval_status"])
print("- 是否允许工程放行:", state["release"]["allowed"])

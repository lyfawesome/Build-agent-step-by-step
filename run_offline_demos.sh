#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python_bin="${PYTHON:-python}"

cd "$repo_dir/demos"

for demo in \
  05_langchain_wrap_function_as_tool.py \
  06_langgraph_pure_tool_node.py \
  08_schema_evidence_artifact.py \
  11_langgraph_interrupt_and_resume.py
do
  echo "Running $demo"
  "$python_bin" "$demo"
done

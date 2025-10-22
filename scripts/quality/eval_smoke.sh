#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
RULESET_PATH="${PROJECT_ROOT}/quality/guardrails/rules.yaml"

cd "${PROJECT_ROOT}"

python -m quality.pipeline.normalize "$@"
python -m quality.evaluator.cli --ruleset "${RULESET_PATH}" "$@"

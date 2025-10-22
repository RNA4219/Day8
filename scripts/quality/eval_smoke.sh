#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
RULESET_PATH="${PROJECT_ROOT}/quality/guardrails/rules.yaml"

INPUT_ARG=""
FORWARDED_ARGS=()

while (($#)); do
  case "$1" in
    --input=*)
      INPUT_ARG="${1#*=}"
      ;;
    --input)
      if (($# < 2)); then
        echo "--input requires a path" >&2
        exit 1
      fi
      shift
      INPUT_ARG="$1"
      ;;
    --)
      shift
      FORWARDED_ARGS+=("$@")
      break
      ;;
    *)
      FORWARDED_ARGS+=("$1")
      ;;
  esac
  shift || true
done

cd "${PROJECT_ROOT}"

TEMP_INPUT_CREATED=0
if [[ -n "${INPUT_ARG}" ]]; then
  INPUT_PATH="${INPUT_ARG}"
else
  INPUT_PATH="$(mktemp "${TMPDIR:-/tmp}/eval-smoke-input.XXXXXX")"
  TEMP_INPUT_CREATED=1
  printf '%s\n' 'Day8 quality smoke test input' >"${INPUT_PATH}"
fi

NORMALIZED_PATH="$(mktemp "${TMPDIR:-/tmp}/eval-smoke-normalized.XXXXXX")"
DEFAULT_METRICS_PATH="${PROJECT_ROOT}/scripts/quality/metrics.json"
METRICS_PATH="${EVAL_SMOKE_METRICS_PATH:-${DEFAULT_METRICS_PATH}}"

OUTPUT_SPECIFIED=0
for ((index = 0; index < ${#FORWARDED_ARGS[@]}; index++)); do
  arg="${FORWARDED_ARGS[${index}]}"
  if [[ "${arg}" == "--output" ]]; then
    OUTPUT_SPECIFIED=1
    next_index=$((index + 1))
    if ((next_index < ${#FORWARDED_ARGS[@]})); then
      METRICS_PATH="${FORWARDED_ARGS[${next_index}]}"
    fi
    break
  elif [[ "${arg}" == --output=* ]]; then
    OUTPUT_SPECIFIED=1
    METRICS_PATH="${arg#--output=}"
    break
  fi
done

if [[ -n "${METRICS_PATH}" ]]; then
  mkdir -p "$(dirname "${METRICS_PATH}")"
fi

cleanup() {
  rm -f "${NORMALIZED_PATH}"
  if [[ "${TEMP_INPUT_CREATED}" == "1" ]]; then
    rm -f "${INPUT_PATH}"
  fi
}

trap cleanup EXIT

python -m quality.pipeline.normalize --input "${INPUT_PATH}" --output "${NORMALIZED_PATH}"

EVALUATOR_CMD=(python -m quality.evaluator.cli --ruleset "${RULESET_PATH}")

if [[ "${OUTPUT_SPECIFIED}" == 0 ]]; then
  EVALUATOR_CMD+=(--output "${METRICS_PATH}")
fi

EVALUATOR_CMD+=("${NORMALIZED_PATH}")

if ((${#FORWARDED_ARGS[@]})); then
  EVALUATOR_CMD+=("${FORWARDED_ARGS[@]}")
fi

"${EVALUATOR_CMD[@]}"

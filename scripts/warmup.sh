#!/usr/bin/env bash
set -euo pipefail

: "${DAY8_API_HEALTHCHECK_URL:?DAY8_API_HEALTHCHECK_URL is required}"
: "${DAY8_API_WARMUP_URL:?DAY8_API_WARMUP_URL is required}"

HEALTH_TIMEOUT="${DAY8_API_HEALTHCHECK_TIMEOUT:-5}"
WARMUP_TIMEOUT="${DAY8_API_WARMUP_TIMEOUT:-5}"
WARMUP_METHOD="${DAY8_API_WARMUP_METHOD:-POST}"
WARMUP_PAYLOAD="${DAY8_API_WARMUP_PAYLOAD:-}"

curl --fail --silent --show-error \
  --max-time "${HEALTH_TIMEOUT}" \
  "${DAY8_API_HEALTHCHECK_URL}" \
  >/dev/null

if [[ -n "${WARMUP_PAYLOAD}" ]]; then
  curl --fail --silent --show-error \
    --max-time "${WARMUP_TIMEOUT}" \
    -X "${WARMUP_METHOD}" \
    -H 'Content-Type: application/json' \
    --data "${WARMUP_PAYLOAD}" \
    "${DAY8_API_WARMUP_URL}" \
    >/dev/null
else
  curl --fail --silent --show-error \
    --max-time "${WARMUP_TIMEOUT}" \
    -X "${WARMUP_METHOD}" \
    "${DAY8_API_WARMUP_URL}" \
    >/dev/null
fi

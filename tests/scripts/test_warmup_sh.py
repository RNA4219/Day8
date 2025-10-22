"""Tests for scripts/warmup.sh."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "warmup.sh"


def test_warmup_script_has_strict_mode() -> None:
    content = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "set -euo pipefail" in content.splitlines()[:5]


def test_warmup_script_runs_healthcheck_then_warmup(tmp_path: Path) -> None:
    log_path = tmp_path / "curl_calls.jsonl"
    curl_stub = tmp_path / "curl"
    curl_stub.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "log_path = Path(os.environ['WARMUP_LOG'])\n"
        "with log_path.open('a', encoding='utf-8') as fh:\n"
        "    json.dump(sys.argv[1:], fh)\n"
        "    fh.write('\\n')\n",
        encoding="utf-8",
    )
    curl_stub.chmod(curl_stub.stat().st_mode | stat.S_IEXEC)

    env = {
        **os.environ,
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "WARMUP_LOG": str(log_path),
        "DAY8_API_HEALTHCHECK_URL": "https://api.example/healthz",
        "DAY8_API_HEALTHCHECK_TIMEOUT": "2",
        "DAY8_API_WARMUP_URL": "https://api.example/warmup",
        "DAY8_API_WARMUP_METHOD": "POST",
        "DAY8_API_WARMUP_TIMEOUT": "3",
        "DAY8_API_WARMUP_PAYLOAD": "{\"ping\":\"warmup\"}",
    }

    subprocess.run([str(SCRIPT_PATH)], check=True, env=env)

    calls = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert len(calls) == 2

    health_call, warmup_call = calls
    assert health_call[-1] == "https://api.example/healthz"

    assert warmup_call[-1] == "https://api.example/warmup"
    assert "--data" in warmup_call
    assert "-X" in warmup_call or "--request" in warmup_call

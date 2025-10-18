from __future__ import annotations

from pathlib import Path
from typing import IO, Any, Dict, Tuple

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for test envs without PyYAML
    class _MiniYAML:
        def safe_load(self, stream: IO[str] | str) -> Dict[str, Any]:
            if hasattr(stream, "read"):
                content = stream.read()
            else:
                content = str(stream)

            root: Dict[str, Any] = {}
            stack: list[Dict[str, Any]] = [root]
            indents = [0]

            for raw_line in content.splitlines():
                stripped = raw_line.lstrip()
                if not stripped or stripped.startswith("#"):
                    continue

                indent = len(raw_line) - len(stripped)
                key, _, value = stripped.partition(":")
                value = value.strip()

                while indent < indents[-1]:
                    stack.pop()
                    indents.pop()

                if value == "":
                    new_map: Dict[str, Any] = {}
                    stack[-1][key] = new_map
                    stack.append(new_map)
                    indents.append(indent + 2)
                else:
                    if value.startswith("[") and value.endswith("]"):
                        items = []
                        raw_items = value[1:-1].split(",") if value[1:-1].strip() else []
                        for raw_item in raw_items:
                            item = raw_item.strip()
                            if item.startswith("\"") and item.endswith("\""):
                                item = item[1:-1]
                            items.append(item)
                        stack[-1][key] = items
                    else:
                        if value.startswith("\"") and value.endswith("\""):
                            value = value[1:-1]
                        stack[-1][key] = value

            return root
    yaml = _MiniYAML()  # type: ignore


def _load_pr_gate_workflow() -> Tuple[Dict[str, Any], str]:
    workflow_path = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "pr_gate.yml"
    raw_text = workflow_path.read_text(encoding="utf-8")
    parsed = yaml.safe_load(raw_text)
    return parsed, raw_text


def _find_step_indices_from_text(raw_text: str, expected_command: str) -> tuple[int, int, int]:
    checkout_index = raw_text.find("uses: actions/checkout")
    setup_python_index = raw_text.find("uses: actions/setup-python@v5")
    governance_index = raw_text.find(expected_command)
    if governance_index == -1:
        governance_index = raw_text.find("python workflow-cookbook/tools/ci/check_governance_gate.py")
    return checkout_index, setup_python_index, governance_index


def _extract_github_script_text(workflow: Dict[str, Any], raw_text: str) -> str:
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "jobs セクションが必要です"
    gate = jobs.get("gate")
    assert isinstance(gate, dict), "jobs.gate が必要です"

    steps = gate.get("steps")
    if isinstance(steps, list):
        for raw_step in steps:
            if not isinstance(raw_step, dict):
                continue
            uses = raw_step.get("uses")
            if uses == "actions/github-script@v7":
                with_block = raw_step.get("with")
                assert isinstance(with_block, dict), "github-script ステップには with ブロックが必要です"
                script = with_block.get("script")
                assert isinstance(script, str), "github-script ステップには script が必要です"
                return script

    marker = "script: |"
    start = raw_text.find(marker)
    assert start != -1, "github-script の script ブロックが必要です"
    start += len(marker)
    lines = raw_text[start:].splitlines()
    script_lines = []
    for line in lines:
        if not line.startswith(" " * 12) and line.strip():
            break
        if line.startswith(" " * 12):
            script_lines.append(line[12:])
    script_text = "\n".join(script_lines).rstrip()
    assert script_text, "github-script の script ブロックを取得できませんでした"
    return script_text


def test_pr_gate_runs_governance_check_after_checkout() -> None:
    workflow, raw_text = _load_pr_gate_workflow()
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict) and "gate" in jobs, "pr_gate.yml の jobs.gate が必要です"

    gate_job = jobs["gate"]
    assert isinstance(gate_job, dict), "jobs.gate はマッピングである必要があります"
    workflow_defaults = workflow.get("defaults")
    default_working_directory = None
    if isinstance(workflow_defaults, dict):
        run_defaults = workflow_defaults.get("run")
        if isinstance(run_defaults, dict):
            working_dir = run_defaults.get("working-directory")
            if isinstance(working_dir, str):
                default_working_directory = working_dir

    gate_defaults = gate_job.get("defaults")
    if isinstance(gate_defaults, dict):
        run_defaults = gate_defaults.get("run")
        if isinstance(run_defaults, dict):
            working_dir = run_defaults.get("working-directory")
            if isinstance(working_dir, str):
                default_working_directory = working_dir

    assert (
        default_working_directory == "workflow-cookbook"
    ), "defaults.run.working-directory は workflow-cookbook を指す必要があります"

    expected_command = "python tools/ci/check_governance_gate.py"

    raw_steps = gate_job.get("steps")
    checkout_index, setup_python_index, governance_index = -1, -1, -1

    if isinstance(raw_steps, list):
        for index, raw_step in enumerate(raw_steps):
            if not isinstance(raw_step, dict):
                continue

            uses = raw_step.get("uses")
            if isinstance(uses, str) and uses.startswith("actions/checkout@"):
                checkout_index = index
                checkout_with = raw_step.get("with")
                if isinstance(checkout_with, dict):
                    fetch_depth = checkout_with.get("fetch-depth")
                    assert fetch_depth in {0, "0"}, "actions/checkout は fetch-depth: 0 を指定する必要があります"
                else:
                    assert "fetch-depth: 0" in raw_text, "actions/checkout に fetch-depth: 0 が必要です"

            run = raw_step.get("run")
            if isinstance(run, str) and "check_governance_gate.py" in run:
                governance_index = index
                assert (
                    expected_command in run
                ), "ガバナンスゲートの実行コマンドが defaults.run.working-directory に合致する必要があります"

            if isinstance(uses, str) and uses.startswith("actions/setup-python@"):
                assert (
                    uses == "actions/setup-python@v5"
                ), "actions/setup-python は v5 を使用する必要があります"
                setup_python_index = index
    else:
        checkout_index, setup_python_index, governance_index = _find_step_indices_from_text(
            raw_text, expected_command
        )

    assert checkout_index != -1, "actions/checkout ステップが必要です"
    assert setup_python_index != -1, "actions/setup-python ステップが必要です"
    assert governance_index != -1, "python workflow-cookbook/tools/ci/check_governance_gate.py を実行するステップが必要です"
    assert (
        governance_index > checkout_index
    ), "ガバナンスゲートの実行は actions/checkout の後に行う必要があります"
    assert (
        governance_index > setup_python_index > checkout_index
    ), "actions/setup-python のステップは checkout の後、ガバナンスゲート実行の前に必要です"

    assert "fetch-depth: 0" in raw_text, "checkout ステップには fetch-depth: 0 の指定が必要です"


def test_pr_gate_reviews_are_evaluated_via_github_script() -> None:
    workflow, raw_text = _load_pr_gate_workflow()
    script = _extract_github_script_text(workflow, raw_text)

    assert (
        "github.rest.pulls.listReviews" in script
    ), "CODEOWNERS 判定には github.rest.pulls.listReviews を利用する必要があります"
    assert "await github.paginate" in script, "レビュー一覧は github.paginate で取得する必要があります"
    assert "const latestStates = new Map();" in script, "最新レビュー状態を保持する Map が必要です"
    assert "latestStates.set(`@${login}`, state);" in script, "レビュアー毎に最新状態を記録する必要があります"
    assert "APPROVED" in raw_text, "承認状態(APPROVED)の判定ロジックが必要です"
    assert (
        "CHANGES_REQUESTED" in raw_text
    ), "差し戻し状態(CHANGES_REQUESTED)の判定ロジックが必要です"


def test_pr_gate_filters_manual_requests_via_codeowners_intersection() -> None:
    workflow, raw_text = _load_pr_gate_workflow()
    script = _extract_github_script_text(workflow, raw_text)

    assert (
        "const filteredRequestedUsers = Array.from(requestedUsers).filter((login) =>" in script
        and "codeownerUsers.has(login)" in script
    ), "手動リクエストのうち CODEOWNERS 該当者のみを対象にするフィルタが必要です"
    assert (
        "const filteredRequestedTeams = Array.from(requestedTeams).filter((team) =>" in script
        and "codeownerTeams.has(team)" in script
    ), "手動チームリクエストも CODEOWNERS との共通部分でフィルタする必要があります"
    assert "const blockers = [];" in script, "ブロッカー集合の初期化が必要です"
    assert (
        "core.setOutput('blockers', JSON.stringify(blockers));" in script
    ), "ブロッカー集合をアクション出力へ公開する必要があります"


def test_pr_gate_requires_all_codeowners_to_approve_latest_reviews() -> None:
    workflow, raw_text = _load_pr_gate_workflow()
    script = _extract_github_script_text(workflow, raw_text)

    assert "const approvals = new Set();" in script, "承認済みレビュアー集合の管理が必要です"
    assert (
        "const allChangeRequesters = Array.from(latestStates.entries())" in script
    ), "CHANGES_REQUESTED を抽出する処理が必要です"
    assert (
        "const requiredUsers = Array.from(codeownerUsers);" in script
    ), "CODEOWNERS 個人の一覧が必要です"
    assert (
        "const pendingApprovals = requiredUsers.filter" in script
    ), "CODEOWNERS の未承認者検知が必要です"
    change_request_message = "Changes requested by: ${allChangeRequesters.join(', ')}"
    assert (
        any(
            marker in script
            for marker in (
                f"core.setFailed(`{change_request_message}`);",
                f"failWith(`{change_request_message}`);",
            )
        )
    ), "CHANGES_REQUESTED 残存時の失敗メッセージが必要です"
    pending_message = "Awaiting required review from: ${messages.join(', ')}"
    assert (
        any(
            marker in script
            for marker in (
                f"core.setFailed(`{pending_message}`);",
                f"failWith(`{pending_message}`);",
            )
        )
    ), "未承認 CODEOWNERS の失敗メッセージが必要です"
    team_message = "Awaiting required review from: ${teamMessages.join(', ')}"
    assert (
        any(
            marker in script
            for marker in (
                f"core.setFailed(`{team_message}`);",
                f"failWith(`{team_message}`);",
            )
        )
    ), "CODEOWNERS チーム承認の失敗メッセージが必要です"


def test_pr_gate_github_script_reads_repo_codeowners() -> None:
    workflow, raw_text = _load_pr_gate_workflow()
    script = _extract_github_script_text(workflow, raw_text)

    assert (
        "github.rest.pulls.listFiles" in script
    ), "変更ファイル一覧の取得に github.rest.pulls.listFiles を用いる必要があります"
    assert ".github/CODEOWNERS" in script, "CODEOWNERS ファイルを参照して必須レビュアーを決定する必要があります"
    assert "fs.readFileSync" in script, "CODEOWNERS ファイルはワークスペースから読み取る必要があります"

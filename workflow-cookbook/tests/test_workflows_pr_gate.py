from __future__ import annotations

import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import IO, Any, Dict, Tuple

import pytest

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


def _find_step_indices_from_text(raw_text: str) -> tuple[int, int]:
    checkout_index = raw_text.find("uses: actions/checkout")
    setup_python_index = raw_text.find("uses: actions/setup-python@v5")
    return checkout_index, setup_python_index


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

    raw_steps = gate_job.get("steps")
    checkout_index, setup_python_index = -1, -1

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

            if isinstance(uses, str) and uses.startswith("actions/setup-python@"):
                assert (
                    uses == "actions/setup-python@v5"
                ), "actions/setup-python は v5 を使用する必要があります"
                setup_python_index = index
    else:
        checkout_index, setup_python_index = _find_step_indices_from_text(raw_text)

    assert checkout_index != -1, "actions/checkout ステップが必要です"
    assert setup_python_index != -1, "actions/setup-python ステップが必要です"
    assert (
        setup_python_index > checkout_index
    ), "actions/setup-python のステップは checkout の後に必要です"

    assert "fetch-depth: 0" in raw_text, "checkout ステップには fetch-depth: 0 の指定が必要です"


def test_pr_gate_reviews_are_evaluated_via_github_script() -> None:
    workflow, raw_text = _load_pr_gate_workflow()
    script = _extract_github_script_text(workflow, raw_text)

    assert (
        "github.rest.pulls.listReviews" in script
    ), "CODEOWNERS 判定には github.rest.pulls.listReviews を利用する必要があります"
    assert "await github.paginate" in script, "レビュー一覧は github.paginate で取得する必要があります"
    assert "const latestStates = new Map();" in script, "最新レビュー状態を保持する Map が必要です"
    assert (
        "const loginHandle = `@${login}`;" in script
        and "latestStates.set(loginHandle, state);" in script
    ), "レビュアー毎に最新状態を記録する際、ログインIDを正規化した変数を利用する必要があります"
    assert "APPROVED" in raw_text, "承認状態(APPROVED)の判定ロジックが必要です"
    assert (
        "CHANGES_REQUESTED" in raw_text
    ), "差し戻し状態(CHANGES_REQUESTED)の判定ロジックが必要です"


def test_pr_gate_codeowners_required_handles_are_parsed() -> None:
    workflow, raw_text = _load_pr_gate_workflow()
    script = _extract_github_script_text(workflow, raw_text)

    assert "github.rest.pulls.listFiles" in script, "変更ファイル取得に github.rest.pulls.listFiles を使用する必要があります"
    assert (
        "const parseCodeowners" in script
    ), "CODEOWNERS 解析用のヘルパー関数 parseCodeowners が定義されている必要があります"
    assert (
        "const requiredHandles = new Set" in script
    ), "CODEOWNERS から抽出した必須レビュアー集合を requiredHandles として扱う必要があります"
    assert (
        "if (requiredHandles.has(loginHandle)) {" in script
    ), "レビュアー状態の判定は CODEOWNERS 上のハンドルが対象となる必要があります"


def test_pr_gate_team_approvals_skip_failure_when_team_is_approved() -> None:
    workflow, raw_text = _load_pr_gate_workflow()
    script = _extract_github_script_text(workflow, raw_text)

    assert (
        "const requestedTeamHandles = new Set(" in script
    ), "チーム承認判定では requestedTeamHandles の集合を構築する必要があります"
    assert (
        "const collaboratorApprovals = new Set();" in script
    ), "チーム承認済みレビュアーを追跡する集合が必要です"
    assert (
        "const pendingTeamHandles = teamHandles.filter((handle) => requestedTeamHandles.has(handle));" in script
    ), "ブロッカーとして扱うのは requested_team に残っているチームだけに限定する必要があります"
    assert (
        "const teamApprovals = collaboratorApprovals;" in script
    ), "チーム承認済み集合を最終判定に利用する必要があります"
    assert (
        "&& teamApprovals.size === 0" in script
    ), "チーム承認が存在する場合は failWith を呼び出さないようにする必要があります"


def test_pr_gate_no_approval_failure_allows_team_coverage() -> None:
    workflow, raw_text = _load_pr_gate_workflow()
    script = _extract_github_script_text(workflow, raw_text)

    assert (
        "const hasTeamCoverage = codeownerTeams.size > 0 && pendingTeamHandles.length === 0;"
        in script
    ), "コードオーナーチームのみのケースで pendingTeamHandles が空なら緩和される必要があります"
    assert (
        "&& !hasTeamCoverage" in script
    ), "Awaiting CODEOWNERS approval 判定でチームカバレッジを考慮する必要があります"


def test_pr_gate_allows_email_only_codeowners(tmp_path: Path) -> None:
    node_path = shutil.which("node")
    if node_path is None:
        pytest.skip("node 実行環境が必要です")

    workflow, raw_text = _load_pr_gate_workflow()
    script = _extract_github_script_text(workflow, raw_text)

    script_file = tmp_path / "codeowners_script.js"
    script_file.write_text(script, encoding="utf-8")

    runner_file = tmp_path / "runner.js"
    runner_file.write_text(
        textwrap.dedent(
            """
            'use strict';
            const fs = require('fs');
            const scriptPath = process.argv[2];
            const workspace = process.argv[3];
            const scriptSource = fs.readFileSync(scriptPath, 'utf8');
            const outputs = new Map();
            let failedMessage = null;
            const core = { setOutput: (k, v) => outputs.set(k, v), setFailed: (msg) => { failedMessage = msg; }, notice: () => {} };
            const github = {
              rest: { pulls: { listFiles: 'listFiles', listReviews: 'listReviews' } },
              paginate: async (fn) => (fn === 'listFiles' ? [{ filename: 'src/example.txt' }] : []),
            };
            const context = {
              repo: { owner: 'octo', repo: 'demo' },
              payload: { pull_request: { number: 1, requested_reviewers: [], requested_teams: [] } },
            };
            const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
            (async () => {
              process.env.GITHUB_WORKSPACE = workspace;
              const runner = new AsyncFunction('core', 'github', 'context', 'require', 'process', scriptSource);
              await runner(core, github, context, require, process);
              if (failedMessage) throw new Error(failedMessage);
              const approval = outputs.get('hasApproval');
              if (approval !== 'true') throw new Error(`Unexpected hasApproval output: ${approval}`);
            })().catch((error) => {
              const message = error instanceof Error ? error.stack ?? error.message : String(error);
              console.error(message);
              process.exit(1);
            });
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    workspace = tmp_path / "workspace"
    codeowners_dir = workspace / ".github"
    codeowners_dir.mkdir(parents=True)
    (codeowners_dir / "CODEOWNERS").write_text("* email@example.com\n", encoding="utf-8")

    result = subprocess.run(
        [node_path, str(runner_file), str(script_file), str(workspace)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_pr_gate_filters_manual_requests_via_codeowners_intersection() -> None:
    workflow, raw_text = _load_pr_gate_workflow()
    script = _extract_github_script_text(workflow, raw_text)

    assert (
        "const filteredRequestedUsers = Array.from(requestedUserHandles).filter((login) =>" in script
        and "codeownerUsers.has(login)" in script
    ), "手動リクエストのうち CODEOWNERS 該当者のみを対象にするフィルタが必要です"
    assert (
        "const filteredRequestedTeams = Array.from(requestedTeamHandles).filter((team) =>" in script
        and "codeownerTeams.has(team)" in script
    ), "手動チームリクエストも CODEOWNERS との共通部分でフィルタする必要があります"
    assert "const requestedUserHandles = new Set(" in script, "requested_reviewers を集合化する必要があります"
    assert "const requestedTeamHandles = new Set(" in script, "requested_teams を集合化する必要があります"
    assert "const blockers = [];" in script, "ブロッカー集合の初期化が必要です"
    assert (
        "core.setOutput('blockers', JSON.stringify(blockers));" in script
    ), "ブロッカー集合をアクション出力へ公開する必要があります"


def test_pr_gate_pending_ignores_non_codeowner_manual_reviewers() -> None:
    workflow, raw_text = _load_pr_gate_workflow()
    script = _extract_github_script_text(workflow, raw_text)

    assert (
        "const requiredUsers = Array.from(new Set([...codeownerUsers, ...filteredRequestedUsers]));"
        in script
    ), "必須レビュアー集合には CODEOWNERS とフィルタ済み手動リクエストの和集合を用いる必要があります"
    assert (
        "const teamHandles = Array.from(codeownerTeams);" in script
        and "const pendingTeamHandles = teamHandles.filter((handle) => requestedTeamHandles.has(handle));" in script
    ), "CODEOWNERS 以外のチームリクエストを除外した pending 判定が必要です"


def test_pr_gate_requires_all_codeowners_to_approve_latest_reviews() -> None:
    workflow, raw_text = _load_pr_gate_workflow()
    script = _extract_github_script_text(workflow, raw_text)

    assert "const approvals = new Set();" in script, "承認済みレビュアー集合の管理が必要です"
    assert (
        "const allChangeRequesters = new Set(" in script
    ), "CHANGES_REQUESTED を抽出する処理が必要です"
    assert (
        "const requiredUsers = Array.from(new Set([...codeownerUsers, ...filteredRequestedUsers]));"
        in script
    ), "CODEOWNERS 個人の一覧とフィルタ済み手動リクエストの組み合わせが必要です"
    assert (
        "const pendingApprovals = requiredUsers.filter" in script
    ), "CODEOWNERS の未承認者検知が必要です"
    change_request_message = "Changes requested by: ${Array.from(allChangeRequesters).join(', ')}"
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

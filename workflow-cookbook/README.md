---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-14
next_review_due: 2025-11-14
---

# Workflow Cookbook / Codex Task Kit

This repo defines QA/Governance-first workflows (not application code).
AI agents implement changes under these policies with acceptance tests and
canary rules.

<!-- LLM-BOOTSTRAP v1 -->
読む順番:

1. `workflow-cookbook/docs/birdseye/index.json` …… ノード一覧・隣接関係（軽量）
2. `workflow-cookbook/docs/birdseye/caps/<path>.json` …… 必要ノードだけ point read（個別カプセル）

フォーカス手順:

- 直近変更ファイル±2hopのノードIDを index.json から取得
- 対応する caps/*.json のみ読み込み

<!-- /LLM-BOOTSTRAP -->

任意のリポジトリに貼るだけで、**仕様→実装→検収**まで一貫して回せるMD群。

- 人間にもエージェント（Codex等）にも読ませやすい最小フォーマット
- 言語・技術スタック非依存（存在するコマンドだけ使う）

## 使い方（最短）

1. これらのMDをリポジトリ直下に配置
2. `BLUEPRINT.md` で要件と制約を1ページに集約
3. 実行手順は `RUNBOOK.md`、評価基準は `EVALUATION.md` に記述し、
   以下で Birdseye の最小読込とタスク分割の前提を共有

    - [`GUARDRAILS.md`](GUARDRAILS.md) …… (`workflow-cookbook/GUARDRAILS.md`) 行動指針と Birdseye の `deps_out`
      と整合する最小読込ガードレールを確認
    - [`tools/codemap/README.md`](tools/codemap/README.md) …… (`workflow-cookbook/tools/codemap/README.md`)
      Birdseye カプセル再生成前提と `codemap.update` の流れを把握
    - [`tools/codemap/update.py`](tools/codemap/update.py) …… `python tools/codemap/update.py`
      (`workflow-cookbook/tools/codemap/update.py`) で `codemap.update` を実行し Birdseye カプセルを再生成する
      （`workflow-cookbook/GUARDRAILS.md` の[鮮度管理](GUARDRAILS.md#%E9%AE%AE%E5%BA%A6%E7%AE%A1%E7%90%86staleness-handling)参照）
    - [`HUB.codex.md`](HUB.codex.md) …… (`workflow-cookbook/HUB.codex.md`) 仕様集約とタスク分割ハブを整備し、Birdseye カプセルの依存関係を維持
    - [`docs/IN-20250115-001.md`](docs/IN-20250115-001.md) …… (`workflow-cookbook/docs/IN-20250115-001.md`)
      インシデントログを参照し
      Birdseye カプセル要約で指示される `deps_out` を照合
4. タスクごとに `workflow-cookbook/TASK.codex.md` を複製して内容を埋め、エージェントに渡す
5. リリースは `workflow-cookbook/CHECKLISTS.md` をなぞり、差分は `workflow-cookbook/CHANGELOG.md` に追記

## Repository structure

- `workflow-cookbook/docs/` …… Birdseye カプセルや仕様補助ドキュメントを格納
- `workflow-cookbook/governance/` …… ポリシーとガードレール定義を配置
- `workflow-cookbook/logs/` …… インシデントやメトリクスの JSONL ログを保管
- `workflow-cookbook/reports/` …… 日次レポートや評価結果を出力
- `workflow-cookbook/scripts/` …… 自動化スクリプトとユーティリティを配置
- `workflow-cookbook/tools/` …… Codemap などの補助ツールを格納

<!-- markdownlint-disable MD013 -->
![lint](https://github.com/RNA4219/workflow-cookbook/actions/workflows/markdown.yml/badge.svg)
![links](https://github.com/RNA4219/workflow-cookbook/actions/workflows/links.yml/badge.svg)
![lead_time_p95_hours](https://img.shields.io/badge/lead__time__p95__hours-72h-blue)
![mttr_p95_minutes](https://img.shields.io/badge/mttr__p95__minutes-60m-blue)
![change_failure_rate_max](https://img.shields.io/badge/change__failure__rate__max-0.10-blue)
<!-- markdownlint-enable MD013 -->

> バッジ値は `governance/policy.yaml` の `slo` と同期。更新時は同ファイルの値を修正し、上記3つのバッジ表示を揃える。

### Commit message guide

- feat: 〜 を追加
- fix: 〜 を修正
- chore/docs: 〜 を整備
- semver:major/minor/patch ラベルでリリース自動分類

### Pull Request checklist (CI 必須項目)

- PR 本文に `Intent: INT-xxx`（例: `Intent: INT-123`）を含めること。
- `EVALUATION` 見出し（例:
  `[Acceptance Criteria](EVALUATION.md#acceptance-criteria)`）へのリンクを
  本文に明示すること。
- Priority Score は必須。必ず `Priority Score: <number> / <justification>` の形式で記載し、根拠を `workflow-cookbook/governance/prioritization.yaml` と整合させる（例: `Priority Score: 5 / impact_scope=0.4 (critical fix)`）。

> `workflow-cookbook/governance/prioritization.yaml` で定義された `impact_scope`（0.4）などの重み付け基準に基づき、Justification には該当指標と判断理由を明記する。

# Day8 コントリビューションガイド

Day8 では Day8 標準ワークフローを基準に、人間と AI が propose-only で安全に改善提案を回します。まずは索引となる
[`docs/ROADMAP_AND_SPECS.md`](docs/ROADMAP_AND_SPECS.md) と [Day8 Birdseye](docs/birdseye/README.md) を通読し、最新の運用ログや
SLO は [`docs/UPSTREAM.md`](docs/UPSTREAM.md) / [`docs/UPSTREAM_WEEKLY_LOG.md`](docs/UPSTREAM_WEEKLY_LOG.md) で確認してから着手
してください。

## ブランチ運用
- 変更は propose-only（自動マージ禁止）で扱い、反映までの応答 SLO（通常 24h 以内）を意識して `Plan → Patch → Tests → Notes`
  を Task Seed 上で更新します。遅延が見込まれる場合は `status` と `next_review_due` を更新し、SLO を再宣言してください。
- 作業ブランチ名は Task Seed の `work_branch` に合わせます。Seed の作り方は [`docs/TASKS.md`](docs/TASKS.md) および
  [`workflow-cookbook/TASK.codex.md`](workflow-cookbook/TASK.codex.md) を参照し、タスクの背景・検証計画・フォローアップを
  先に固めてから差分作業に入ります。
- ガバナンスや Guardrails を変更する場合は [`governance/`](governance) 配下の担当者へ Issue で事前相談し、必要に応じて
  `workflow-cookbook/logs/` や `reports/` に観測ログを残してください。

## セットアップ
- 依存関係やツールの導入は [`INSTALL.md`](INSTALL.md) の順に進め、ローカルでは `make bootstrap` → `make check` を初回実行の
  目安とします。
- Node.js/TypeScript の開発は ESM 構成を前提に、`.nvmrc` と `package.json` のバージョンピンを尊重してください。
- Birdseye など生成物を更新した場合は、[`docs/birdseye/README.md`](docs/birdseye/README.md) と
  [`scripts/birdseye_refresh.py`](scripts/birdseye_refresh.py) の手順に従い `index` / `caps` / `hot` を同期します。

## テストマトリクスと例外ポリシー
- 変更前後で必ず以下のコマンドを成功させ、結果を PR に添付します。
  1. `ruff check .`
  2. `mypy --strict`
  3. `pytest`
  4. `node --test`
- `make check` は上記 Python 系ツールをまとめて実行する補助ですが、CI と同じ粒度での記録が必要です。
- 例外は以下のみ許容されます。
  - 実行環境に依存する flaky が既知で、`workflow-cookbook/GUARDRAILS.md` に回避策が明記されている場合：Issue リンクと
    再試行ログを添えて `⚠️ known flaky` と明記してください。
  - サードパーティ API など外部依存の停止：テストを `-k` で限定し、残タスクを Task Seed の `Follow-ups` に登録します。
  - 上記以外の失敗は差し戻し扱いです。回避策を提案できない場合はタスクを保留し、SLO を更新してください。

## ADR 更新フロー
- 仕様・意思決定の変更は [`docs/adr/`](docs/adr) のテンプレートに従って追記し、関連する Task Seed と PR にリンクします。
- 新旧の整合性を保つため、ADR を更新したら [`CHANGELOG.md`](CHANGELOG.md) と [`workflow-cookbook/CHANGELOG.md`](workflow-cookbook/CHANGELOG.md)
  の対象節を同一コミットで補足してください。
- Birdseye のカバレッジに影響する場合は、`scripts/birdseye_refresh.py` を実行したログを PR に添付し、生成物の `generated_at`
  を揃えます。

## Guardrails 同期と連携ドキュメント
- セーフティ要件は [`workflow-cookbook/GUARDRAILS.md`](workflow-cookbook/GUARDRAILS.md) と
  [`workflow-cookbook/RUNBOOK.md`](workflow-cookbook/RUNBOOK.md) を基準とし、変更時は
  [`workflow-cookbook/logs/`](workflow-cookbook/logs) 配下へ観測ログを配置します。
- Task Seed（[`docs/TASKS.md`](docs/TASKS.md)）・Guardrails・Birdseye の間で差分が発生したら、`docs/seeds/` 配下の Seed に
  追記し、`Plan/Patch/Tests/Notes` の更新履歴を残してください。
- Birdseye のホットスポットは [`docs/birdseye/hot.json`](docs/birdseye/hot.json) を参照し、SLO に影響する箇所は先にレビューへ
  回します。

## Issue / PR 運用とテストログの扱い
- Issue は `.github/ISSUE_TEMPLATE/` の順番で、`不具合: Bug Report` → `提案: Feature Request` → `反省: Why-Why` を優先利用します。
  テンプレート外で起票する場合は Task Seed のリンクを添付し、優先度ラベルを設定してください。
- PR は `.github/PULL_REQUEST_TEMPLATE.md` のチェックリストを必ず埋め、実行ログ（`ruff` / `mypy --strict` / `pytest` / `node --test`）
  を貼り付けます。複数環境で実行した場合は、ログを `workflow-cookbook/logs/` に保存しパスを明記してください。
- 依存ドキュメントに破壊的変更を加えた際は、`README.md` または `INSTALL.md` の該当節に更新内容を追記し、Birdseye を同期します。
  今回のガイド改訂では追加案内は不要です。

---
- 行動規範は [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) を参照してください。
- ライセンス表記は [`LICENSE`](LICENSE) / [`NOTICE`](NOTICE) / [`workflow-cookbook/LICENSE`](workflow-cookbook/LICENSE) を確認してください。

---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-30
next_review_due: 2025-11-30
---

# Checklists

## Development

- [workflow-cookbook/EVALUATION.md](./EVALUATION.md) の品質ゲートに従い、作業前に `ruff`, `mypy --strict`, `pytest`, `node --test` をローカル実行し、基準逸脱を先に除去する。
- 変更で使用する Task Seed を [workflow-cookbook/TASK.codex.md](./TASK.codex.md) と照合し、必要なら Seed 追記とレビュー依頼を同一ブランチで行う。
- セキュリティ影響が疑われる場合は [workflow-cookbook/SECURITY.md](./SECURITY.md) のチェックリストを読み合わせ、追加調査やトリアージを事前に依頼する。
- 実装・検証手順を [workflow-cookbook/RUNBOOK.md](./RUNBOOK.md) へ反映し、チーム内での再現性を確保する。

## Pull Request

- PR 説明欄に [docs/Release_Checklist.md](../docs/Release_Checklist.md) の該当項目と結果をリンク付きで記録する。
- [workflow-cookbook/EVALUATION.md](./EVALUATION.md#acceptance-criteria) の人手検証ステップを満たした証跡（動画・スクショ・ログ）を添付し、再現条件を明示する。
- [workflow-cookbook/SECURITY.md](./SECURITY.md#review-workflow) に沿って Security Review 連携が必要か判定し、該当する場合はレビュー依頼の Issue / Slack URL を記載する。
- Birdseye 更新の要否を判断し、必要なら `python scripts/birdseye_refresh.py --docs-dir docs/birdseye --docs-dir workflow-cookbook/docs/birdseye` の実行ログを添付する。

## Release

- [docs/Release_Checklist.md](../docs/Release_Checklist.md) の段階ゲートに沿って `type:*` / `semver:*` ラベル、Priority Score、互換性根拠を整備する。
- [docs/addenda/M_Versioning_Release.md](../docs/addenda/M_Versioning_Release.md) を参照し、API/CLI 互換性とタグ運用が揃っているか確認する。
- 配布物の LICENSE / NOTICE / SBOM 更新可否を確認し、変化がある場合は [docs/addenda/H_Deploy_Guide.md](../docs/addenda/H_Deploy_Guide.md) の梱包手順を適用する。
- リリース用ブランチと `main` の差分を確認し、必要な場合は [workflow-cookbook/CHANGELOG.md](./CHANGELOG.md) と `docs/UPSTREAM_WEEKLY_LOG.md` を同期する。

## Ops

- 初動対応では [docs/addenda/J_Runbook.md](../docs/addenda/J_Runbook.md) と [workflow-cookbook/RUNBOOK.md](./RUNBOOK.md) を突合し、アラート種別ごとのトリアージ順序とエスカレーション経路が一致するか確認する。
- 対応内容を [workflow-cookbook/SECURITY.md](./SECURITY.md#incident-response-checklist) の Security Checklist と比較し、緊急パッチや情報共有が漏れていないか洗い出す。
- インシデント記録は `quality/incidents/` 配下のテンプレートに追記し、必要に応じて [docs/addenda/J_Runbook.md](../docs/addenda/J_Runbook.md#postmortem) のポストモーテム手順を実施する。
- 影響範囲の手動確認ログ（dashboards, metrics, chainlit transcripts）を `workflow-cookbook/logs/` に保存し、再発防止策を RUNBOOK へ反映する。

## Hygiene

- 命名・ディレクトリ構成・コメント整備を行い、[workflow-cookbook/GUARDRAILS.md](./GUARDRAILS.md) の保守性ガイドに従ってレガシー化を防ぐ。
- ドキュメント差分と Birdseye 反映を同一コミットで実施し、`python scripts/birdseye_refresh.py --docs-dir docs/birdseye --docs-dir workflow-cookbook/docs/birdseye` の結果を PR に添付する。
- 反映済みタスクを [workflow-cookbook/TASK.codex.md](./TASK.codex.md) で閉じ、未着手の Task Seed との差分を明示する。

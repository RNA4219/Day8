---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-20
next_review_due: 2025-11-20
---

# Safety Policy

Katamari ワークフローの安全対策を Day8 向けにローカライズした基準。自動化とレビュー・承認プロセスの境界を明確化し、Day8 の `docs/safety.md` と矛盾しないよう同期する。

## 適用範囲

- Day8 リポジトリで運用するワークフロー、テンプレート、チェックリスト。
- Guardrails が適用される自動化（`tools/`、`scripts/`、`workflow-cookbook/tools/`）。
- プロダクトコードやインフラ構成の変更要求に接続する運用ドキュメント。

## 基本原則

1. **人間の最終承認** — `docs/safety.md` のポリシーに従い、本番影響のある変更は人間の責任者が最終判断する。
2. **自動化の制限** — 自動化は検知・報告までとし、変更適用はガードレールで許可された範囲に限定する。
3. **トレーサビリティ** — 各アクションは `workflow-cookbook/logs/` と Day8 側の監査ログに記録し、`docs/birdseye/` の索引を更新する。
4. **最小権限** — ツールは読み取り中心で実行し、書き込み権限は安全承認フェーズでのみ付与する。

## 運用フロー

1. **計画** — 変更提案時に `workflow-cookbook/BLUEPRINT.md` と `docs/ROADMAP_AND_SPECS.md` を照合し、影響と安全性チェックを事前評価する。
2. **設計レビュー** — Guardrails の例外が必要な場合、`workflow-cookbook/GUARDRAILS.md` の例外承認手順を踏む。Day8 では `governance/policy.yaml` に従い承認者を割り当てる。
3. **実装・検証** — テストと静的解析を優先し、`docs/day8/security/05_security.md` の保護要件を満たすテスト証跡を残す。
4. **ローンチ判定** — `workflow-cookbook/RUNBOOK.md` のリリース手順で安全チェックを再実施し、人間の承認後に本番反映を許可する。
5. **運用モニタリング** — 実行後は `workflow-cookbook/EVALUATION.md` と `workflow-cookbook/CHECKLISTS.md` を参照し、逸脱があれば即座に緊急手順へ移行する。

## インシデント対応

- 重大度分類は `docs/day8/security/05_security.md` の S1–S4 を使用。
- S1/S2 の場合は 1 時間以内に安全責任者へ通知し、影響範囲を Birdseye で共有。
- 一時的に自動化を停止する場合は `workflow-cookbook/scripts/` のジョブを無効化し、手動ログに切り替える。
- 根本原因分析は 48 時間以内に `workflow-cookbook/reports/` へ記録し、必要に応じて Guardrails と本ドキュメントを更新する。

## レビューとメンテナンス

- 月次で `docs/safety.md`・`docs/birdseye/index.json`・本ドキュメントの整合性を確認する。
- Day8 と Katamari で安全プロセスに差分が生じた場合、`workflow-cookbook/CHANGELOG.md` と Day8 のロードマップに反映する。
- 緊急改訂時は Birdseye の `generated_at` と該当 Capsule を即時更新し、ホットリンクへ追加する。

## 参照資料

- [docs/safety.md](../docs/safety.md)
- [docs/day8/security/05_security.md](../docs/day8/security/05_security.md)
- [workflow-cookbook/GUARDRAILS.md](GUARDRAILS.md)
- [workflow-cookbook/RUNBOOK.md](RUNBOOK.md)
- [workflow-cookbook/EVALUATION.md](EVALUATION.md)
- [workflow-cookbook/CHECKLISTS.md](CHECKLISTS.md)

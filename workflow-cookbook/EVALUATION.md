---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-14
next_review_due: 2025-11-14
---

# Evaluation

Day8 の品質ゲートを統制する評価フレーム。Guardrails／Runbook／Checklist で定義された振る舞いと整合し、Birdseye から最小ホップで参照できることを前提にする。

## 目的

- 各 PR / リリースが Guardrails に適合し、Day8 固有の運用ルール（mypy/strict, ruff, pytest, node:test, 例外ポリシー）を逸脱しないことを確認する。
- KPI・テスト・証跡を Checklist/RUNBOOK と一貫して提示し、Priority Score を用いた意思決定ログを残す。
- 重大インシデント時の対応記録（docs/IN-YYYYMMDD-XXX.md）を RUNBOOK・該当 PR へ確実にリンクする。

## 評価ステップ

1. **Intake & Scope 認定**
   - `README.md` の LLM-BOOTSTRAP → `docs/birdseye/index.json` → 対象ノード Capsule の順で読み、Scope とガードレール差分を確定する。
   - `governance/policy.yaml` の forbidden_paths に抵触しない変更であることを確認し、必要なら Task Seed 側へフォローアップを登録する。
2. **実装準備と検証計画**
   - `workflow-cookbook/RUNBOOK.md` の「準備→実行→確認」をベースにテスト計画を整備し、最初にテスト（pytest / node:test 等）を追加・更新する。
   - KPI とトレードオフを定義し、Priority Score（値・根拠）を PR 本文に暫定記載する。
   - [docs/day8/spec/02_spec.md](../docs/day8/spec/02_spec.md) のチェーン制御・Provider 抽象・性能指標セクションを読み、今回の差分が各フェーズの SLO（`duration_p95` / `pass_rate` / `retention_ratio`）と整合するか確認する。
3. **検証とサインオフ**
   - `workflow-cookbook/CHECKLISTS.md` の Release/Hygiene を全て満たしたエビデンスを PR に添付し、lint/type/test の完走ログを提示する。
   - 受け入れ基準に未達がある場合はフォローアップ Task Seed を登録し、Birdseye index/caps/hot を同一コミットで再生成する。

## 受け入れ基準

### 必須

- PR 本文に Priority Score（数値・根拠・依拠した KPI）が明記されている。
- lint（ruff）/ type（mypy --strict）/ test（pytest, node:test）の実行ログが全て成功している。
- `governance/policy.yaml` の forbidden_paths を変更していない（必要な場合は別途ガバナンス承認を経て専用 PR を起票）。
- Day8 Guardrails のスコープ制約（1変更≤100行 or 2ファイル、ドキュメント除外）と例外ポリシーを遵守している。
- 例外対応または障害対応時は docs/IN-YYYYMMDD-XXX.md を作成し、該当 PR と `workflow-cookbook/RUNBOOK.md` 「Observability」「Rollback / Retry」へ相互リンクを追記する。
- 仕様で定義されたチェーン制御・Provider フォールバック・性能 SLO のエビデンス（ログ / メトリクス）を添付し、Birdseye 参照先を明記する。

### 推奨

- 変更点の実行コスト/レイテンシ影響を ±5% 以内に抑えた評価と代替策の検討結果を PR ノートへ記載する。
- 依存する Birdseye ノード（index/caps/hot）を更新し、`generated_at` が最新コミットと同日である。
- `workflow-cookbook/SAFETY.md`・`workflow-cookbook/SECURITY.md` と矛盾がないことを確認し、必要な場合は該当文書も同時更新する。

## 指標 (KPIs)

- **品質**: lint/type/test 成功率 100%、再実行回数 0 を基本ラインとし、例外時は原因と恒久対応を記録する。
- **パフォーマンス**: 主要処理のレイテンシ・実行コストを ±5% 以内で維持。超過見込み時はノートに補填策を提示する。
- **安定性**: エラー率 0%、デプロイ後 24h の監視でアラートが無いこと。発生時はインシデントレポートを作成。
- **コンプライアンス**: forbidden_paths 違反 0 件、Priority Score 未設定 0 件。

## チェックリスト連携

- **Daily**: 失敗通知と主要 KPI 閾値を監視し、逸脱時は RUNBOOK の再実行手順へ誘導。
- **Release**: 受け入れ基準エビデンス、Priority Score、ライセンス添付、lint/type/test 完走ログ、Docker スモーク結果を記録。
- **Hygiene**: 命名規約とディレクトリ構造が Guardrails に準拠しているか、ドキュメント差分が Birdseye に反映されているかを確認。

## エビデンス管理

- `workflow-cookbook/RUNBOOK.md` に沿って検証ログを整理し、PR コメントまたは付随ノートに記録する。
- Birdseye index/caps を更新し、`docs/birdseye/caps/workflow-cookbook.EVALUATION.md.json` を最新の依存関係で再生成する。
- すべての評価記録を `workflow-cookbook/CHANGELOG.md` および関連 Task Seed へ転記し、次回レビュー（`next_review_due`）に備える。

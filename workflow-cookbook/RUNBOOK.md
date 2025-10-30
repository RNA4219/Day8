---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-11-21
next_review_due: 2025-12-21
---

# Day8 Workflow Runbook

## Purpose

- Day8 リポジトリのワークフロー運用を統制し、Blueprint/Evaluation の要件を実務手順へ落とし込む。
- チェックリスト・Birdseye・インシデントログの鮮度を維持し、最低限のトークン読込で運用判断を下す。

## Roles

| ロール | 主担当タスク | エスカレーション |
| --- | --- | --- |
| Ops Steward | `workflow-cookbook/CHECKLISTS.md#daily` に基づくデイリー確認と Birdseye 更新のトリガー。 | Guardrail Owner |
| Guardrail Owner | `workflow-cookbook/GUARDRAILS.md`・`workflow-cookbook/SAFETY.md`・`workflow-cookbook/SECURITY.md` の改訂と適用監査。 | Incident Commander |
| Incident Commander | 重大インシデント発生時に `workflow-cookbook/docs/IN-*.md` を更新し、`docs/ROADMAP_AND_SPECS.md` へ連携。 | Steering Committee |

## Guardrails & Inputs

- [workflow-cookbook/GUARDRAILS.md](GUARDRAILS.md)：最小読込とタスク分解ガイドライン。
- [workflow-cookbook/BLUEPRINT.md](BLUEPRINT.md)：対象スコープと I/O 契約の出典。
- [workflow-cookbook/SAFETY.md](SAFETY.md) / [workflow-cookbook/SECURITY.md](SECURITY.md)：フェイルセーフと秘匿情報の扱い。
- [docs/ROADMAP_AND_SPECS.md](../docs/ROADMAP_AND_SPECS.md)：上位ロードマップとの整合確認。
- [workflow-cookbook/tools/codemap/README.md](tools/codemap/README.md)：Birdseye 再生成フロー。

## Guardrail 項目

- [ ] AI 提案は `workflow-cookbook/TASK_SEED.md` へ検証ログを残しつつ、人手検証で根拠と差分影響を確認する。
- [ ] Secrets や `.env` の平文参照は避け、`workflow-cookbook/SECURITY.md` に従って疑似値サンプルのみを共有する。
- [ ] `workflow-cookbook/docs/birdseye/` と `workflow-cookbook/TASKS.md` の同期状況を確認し、Birdseye 更新後にタスク追跡を整合させる。
- [ ] Task Seed で意思決定の判断根拠を記録し、`docs/addenda/J_Runbook.md` へのリンクや引用を添えて運用履歴を残す。

## Run Sequence

### Preparation

1. **環境セットアップ**（Python 3.11 以上、外部依存なし）
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. フロントマター整合性を確認。
   ```bash
   python workflow-cookbook/tools/ci/check_front_matter.py --check .
   ```
3. 直近インシデントとチェックリストの差分を確認し、対応ロールを明確化。
   - `workflow-cookbook/docs/IN-*.md`
   - `workflow-cookbook/CHECKLISTS.md`

### Execution

1. 作業ブランチを作成し、Blueprint / Guardrails を参照して差分を設計。
2. 変更適用後、Birdseye を同期。
   ```bash
   python scripts/birdseye_refresh.py \
     --docs-dir docs/birdseye \
     --docs-dir workflow-cookbook/docs/birdseye
   ```
3. 運用ログを収集し、必要に応じて解析レポートを出力。
   ```bash
   python workflow-cookbook/scripts/analyze.py
   ```

### Verification

1. `workflow-cookbook/logs/test.jsonl` が最新状態か確認し、異常行を抽出する。
2. `workflow-cookbook/reports/today.md`・`workflow-cookbook/reports/issue_suggestions.md` を点検し、未処理アクションがないか確認する。
3. `workflow-cookbook/CHECKLISTS.md` の該当セクション（Daily / Release / Hygiene）を完了状態にする。
4. Birdseye の `generated_at`（`docs/birdseye/index.json`・`workflow-cookbook/docs/birdseye/index.json`）と参照ファイルの更新日時が揃っているか確認する。
5. Task Seed に作業根拠と検証結果を追記し、必要に応じて `docs/addenda/J_Runbook.md` の参照手順を更新する。

### 最小フロー

- **Development フェーズ**
  - [ ] Guardrail 項目のチェックリストを全て通過し、AI 提案との差分を Task Seed に記録する。
  - [ ] Secrets/.env の扱いと Birdseye 再生成計画をレビュー担当へ共有する。
- **Review フェーズ**
  - [ ] Birdseye/TASKS の同期状態と `workflow-cookbook/CHECKLISTS.md` の進捗を確認する。
  - [ ] Task Seed の判断ログにレビューコメントを追記し、必要なら追加検証を指示する。
- **Ops フェーズ**
  - [ ] `workflow-cookbook/docs/IN-*.md` のインシデントログを更新し、対応済み・未対応の差異を明文化する。
  - [ ] 最終コミット前にインシデント連絡網への通知と `docs/addenda/J_Runbook.md` の参照更新を完了させる。
  - [ ] Birdseye 再生成コマンド実行ログとチェックリスト完了状態を Task Seed に添付する。

## Checklist Alignment

- **Daily**：入力到着・失敗通知・主要メトリクスを `logs/test.jsonl` とレポートで照合。
- **Release**：Birdseye 再生成、lint/test（該当する場合）、ライセンス同梱、ラベル設定を完了。
- **Hygiene**：命名規約とドキュメント差分を `GUARDRAILS.md`・`RUNBOOK.md`・`CHECKLISTS.md` 間で同期。

## References

- `docs/birdseye/index.json` / `workflow-cookbook/docs/birdseye/index.json`：ノード間依存の鳥瞰図。
- `scripts/birdseye_refresh.py`：Birdseye 自動再生成スクリプト。
- `workflow-cookbook/scripts/analyze.py`：ログ解析および日次レポート生成。
- `workflow-cookbook/CHECKLISTS.md`：運用判断の最終ゲート。
- `workflow-cookbook/docs/IN-*.md`：インシデントサマリとロールバック記録。
- `docs/addenda/J_Runbook.md`：SSE 断・初回遅延・OAuth 失敗など一次切り分け時の初動判断。

---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-21
next_review_due: 2025-11-21
---

# Safety Policy & 審査基準

Katamari 本家の安全審査ワークフローを Day8 に適用するための基準。Guardrails・RUNBOOK・docs/safety.md と整合し、Birdseye で追跡できる安全ゲートを維持する。

## 目的

- 本番影響のある変更は必ず人間の責任者が最終承認し、判断材料をログに残す。
- 自動化の役割を検知/通知に限定し、安全審査で許可された操作のみ実行する。
- 安全レビュー結果と関連ドキュメントのリンクを Birdseye に同期し、再利用可能な監査証跡を残す。

## スコープとドキュメント

1. Day8 リポジトリのワークフロー、テンプレート、チェックリスト全般。
2. Guardrails が適用される自動化（`tools/`、`scripts/`、`workflow-cookbook/tools/`）。
3. `docs/safety.md`、`docs/day8/security/05_security.md`、`workflow-cookbook/BLUEPRINT.md` 等の安全判断資料。
4. 審査結果は `workflow-cookbook/logs/` と Birdseye ノードへ反映し、`workflow-cookbook/CHANGELOG.md` で履歴管理する。
5. インシデント後の更新は `workflow-cookbook/reports/` と `docs/ROADMAP_AND_SPECS.md` の安全セクションを同時に更新する。

## 実装原則

- **最小権限**：自動化は読み取り中心で実行し、書き込みやデプロイ権限は安全承認フェーズでのみ付与する。
- **テストと証跡**：TDD を基本とし、`docs/day8/security/05_security.md` の保護要件を満たすテストとログを保存する。
- **整合性**：`docs/safety.md` と矛盾があれば本ドキュメントを優先的に更新し、Birdseye インデックス/capsule/hot を再生成する。
- **トレーサビリティ**：`workflow-cookbook/logs/` に審査ログを格納し、関連プルリクには該当ログと審査責任者を添付する。
- **例外の明示**：Guardrails の例外は `workflow-cookbook/GUARDRAILS.md` の手順で承認し、許容期間と監視方法を記録する。

## プロセスと自己検証

- **計画**：変更提案時に `workflow-cookbook/BLUEPRINT.md` で安全影響分析を記録し、`docs/ROADMAP_AND_SPECS.md` の該当ノードを確認する。
- **レビュー**：安全審査会議の結果を `workflow-cookbook/CHECKLISTS.md` の安全項目に反映し、審査ログを Birdseye にリンクする。
- **実装/検証**：`workflow-cookbook/RUNBOOK.md` に沿って安全テストを実施し、`workflow-cookbook/EVALUATION.md` で受入条件を満たしたことをチェックする。
- **ローンチ判定**：人間責任者がサインオフするまで自動化によるリリース操作を禁止し、承認後に `workflow-cookbook/scripts/` のジョブを解禁する。
- **振り返り**：月次レビューで `docs/safety.md`・Birdseye・本ドキュメントのリンク切れを確認し、必要に応じて再発防止計画を `workflow-cookbook/reports/` に記録する。

## 例外処理

- 緊急対応で例外が必要な場合は、Guardrails 例外記録と合わせて期限・影響範囲・暫定コントロールを必ず記す。
- 重大度 S1/S2 のインシデントは 1 時間以内に安全責任者へ通知し、Birdseye ホットリストに一時的な警告ノードを追加する。
- 自動化停止が必要なときは `workflow-cookbook/scripts/` のジョブを無効化し、手動運用とログ記録へ切り替える。
- 48 時間以内に根本原因分析（RCA）を作成し、本ドキュメントと Guardrails を必要に応じて更新する。

## リマインダー

- 変更前に必ずテストと安全チェックリストを更新し、審査ログを添付してから承認を依頼する。
- Birdseye の `generated_at` が古い場合は `workflow-cookbook/tools/codemap/update.py` を実行してインデックスとカプセルを同期する。
- 監査対象のやり取りは `workflow-cookbook/logs/`・`docs/birdseye/` の両方へ記録し、監査トレイルを欠損させない。

## Birdseye / Minimal Context Intake Guardrails（鳥図×最小読込）

**目的**：安全審査に必要な情報を最小トークンで共有し、Day8/Workflow-cookbook 双方の責任者が同じ前提で判断できるようにする。

### 運用の前提（Dual Stack互換）

- Day8 はデュアルスタック（Function Calling / ツールレス JSON 封筒）を前提とし、安全審査ログも両方の経路で取得できるよう整備する。
- ツール利用環境では安全審査チェックリストを自動取得し、ツールレス環境では `tool_request` JSON を添付して審査ログの参照先を示す。
- Birdseye Capsule には審査責任者・関連チェックリスト・例外期限を要約し、推論時に過去判断を再確認できる状態を保つ。

---

### 配置ポリシー（3層で最小読込）

1. **Bootstrap（超小型）** — `README.md` の LLM-BOOTSTRAP ブロックに安全審査ノードへの導線を含める。
2. **Index（軽量インデックス）** — `docs/birdseye/index.json` で SAFETY ノードを Guardrails・Runbook と 2 hop 以内で接続し、`generated_at` を揃える。
3. **Capsules（点読みパケット）** — `docs/birdseye/caps/workflow-cookbook.SAFETY.md.json` に審査プロセスと依存資料をまとめ、ホットリストに登録する。

> 補助：重大度 S1/S2 が発生したら暫定的に Birdseye Hot List へ警告タグを追加し、復旧後に履歴へ移す。

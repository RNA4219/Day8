---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-14
next_review_due: 2025-11-14
---

# Changelog

## 0.1.0 - 2025-10-13

- 初版（MD一式 / Codex対応テンプレ含む）

## 1.0.0 - 2025-10-16

### Added

- Stable Template API（主要MDの凍結）
- PR運用の明確化（Intent / EVALUATION リンク / semverラベル）
- CIワークフロー（links/prose/release）

### Known limitations

- SLOバッジ自動生成は未実装（README と policy.yaml を手動同期）
- Canary 連携は任意

## 1.1.0 - 2025-10-20

### Added

- Day8 向けにローカライズした SAFETY ポリシーと内部ノード/カプセル定義の同期

## 1.1.1 - 2025-10-21

### Updated

- Day8 SAFETY 全体を再整備し、Guardrails と同一セクション構成に揃えた。
- SAFETY index/caps/hot を再生成し、Guardrails 系エッジと `generated_at` を同期。
- リンク重複を解消し、SAFETY ホットエントリを単一化。

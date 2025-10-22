---
task_id: 20250115-01
repo: https://github.com/day8/Day8
base_branch: main
work_branch: feat/sample-day8-task
priority: P2
langs:
  - python
  - typescript
status: draft
created_at: 2025-01-15
last_reviewed_at: 2025-01-15
next_review_due: 2025-01-29
---

# Task Seed – sample-day8-template

## Objective

Day8 反省パイプラインで追加する自動化の要件と検証フローを一箇所に整理し、レビュー準備を整える。

## Scope

- In:
  - docs/day8/spec 配下の要件整理
  - scripts/birdseye_refresh.py の Birdseye 連携調整
- Out:
  - 本番 API 実装
  - workflow-cookbook 配下のガードレール本体

## Requirements

- Behavior:
  - Task Seed に記載した受入基準が満たされるまで差分を積み上げる。
  - Plan/Tests/Commands の各ログを最新状態に更新する。
- I/O Contract:
  - Input: 日次のリフレクション結果と Birdseye 参照リスト
  - Output: docs/seeds/ 以下に配置された最新 Task Seed
- Constraints:
  - 既存 API・CLI の互換性維持
  - 追加依存なし、CI コマンドは既存運用に準拠
- Acceptance Criteria:
  - 受入コマンドが lint/type/test を通過したログを記録
  - 影響パスと Deliverables が PR 本文と整合

## Affected Paths

- docs/day8/spec/**
- docs/seeds/**
- scripts/birdseye_refresh.py

## Local Commands

```bash
make lint
make typecheck
make test
```

## Deliverables

- PR: Intent ID、Priority Score、リスク評価を本文へ記載
- Artifacts: 更新済み Task Seed、検証ログ、必要なスクリーンショット

---

## Plan

### Steps

1. 既存ドキュメントと仕様を確認し、差分対象を洗い出す。
2. 必要なテストとドキュメントの更新手順を整理する。
3. 実装とドキュメント更新を行い、Birdseye を同期する。
4. lint/type/test を実行し、結果を Tests/Commands セクションへ記録する。
5. フォローアップやリスクを Notes に追記し、レビュー準備を完了する。

## Patch

***Provide a unified diff. Include full paths. New files must be complete.***

## Tests

### Outline

- Unit:
  - scripts/birdseye_refresh.py のユーティリティ関数に対する正常系テスト
  - docs/day8/spec の要件差分を検証するメタテスト
- Integration:
  - Birdseye 再生成コマンドのドライラン結果を確認

## Commands

### Run gates

- make lint
- make typecheck
- make test

## Notes

### Rationale

- Day8 の propose-only ポリシーを維持しつつ、最小差分で Seed を更新するため。

### Risks

- Birdseye を未同期のまま運用すると索引が破綻する可能性。

### Follow-ups

- Day8 Reflection の次回見直しで Plan 手順を最新版へ更新する。

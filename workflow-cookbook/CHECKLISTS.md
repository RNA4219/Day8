---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-14
next_review_due: 2025-11-14
---

# Checklists

## Daily

- 入力到着の確認
- 失敗通知の有無
- 主要メトリクス閾値

## Release

- 変更点の要約
- Priority Score（値・根拠・関連KPI）を PR に記録
- 受け入れ基準に対するエビデンス
- 影響範囲の再確認
- 成果物に LICENSE / NOTICE を同梱済み
- lint / test を全ジョブ完走
- Birdseye index/caps を `python workflow-cookbook/tools/codemap/update.py --targets docs/birdseye/index.json,workflow-cookbook/docs/birdseye/index.json --emit index+caps` で再生成
- Docker イメージをビルドし主要機能のスモーク確認
- PR に `type:*` および `semver:*` ラベルを付与済み
- governance/policy.yaml の forbidden_paths を変更していないことを確認

## Hygiene

- 命名・ディレクトリ整備
- ドキュメント差分反映

---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-20
next_review_due: 2025-11-20
---

# Safety Policy (Day8 ローカライズ)

Day8 で自動化エージェントが活動する際の安全審査と抑制フローを Day8 の基準に沿って再構成したもの。`docs/safety.md` の運用方針とクロスチェックしつつ、Cookbook 側での実行許容範囲と監査観点を明示する。

## 目的

- エージェントが Day8 リポジトリで扱う情報・操作を安全域に制限する。
- 変更要求のスコープと危険度を判定し、適切なレビュー/エスカレーション先へ誘導する。
- ガードレール・Runbook・Security ドキュメントとの整合性を保ち、Birdseye 索引に即時反映する。

## 適用範囲

- `workflow-cookbook/**`, `docs/**`, `governance/**` など Day8 の運用知識ベース。
- Git 操作、ドキュメント更新、手順書・ポリシーの整備。
- **除外**: `src/**`, `infrastructure/**`, `secrets/**` など本番資産。これらは観測・報告に留める。

## 基本原則

1. **最小権限での観測優先** — 変更前に `docs/safety.md` / `workflow-cookbook/GUARDRAILS.md` / `RUNBOOK.md` を確認し、操作目的と安全装置を記録する。
2. **タスク分割とドラフト運用** — 高リスク変更は Task Seed へ分解し、ドラフト PR で人間承認を得る。自動マージ禁止。
3. **例外制御** — 再試行可能な失敗（ネットワーク不調など）は Runbook のリトライ手順に従い、不可逆な障害は `SECURITY.md` の連絡先へ即時報告。
4. **証跡の一元化** — 安全審査結果、ログ、追加ガードは `CHECKLISTS.md` と `logs/` に記録し、Birdseye を再生成する。

## ワークフロー

1. **スコーピング**: `HUB.codex.md` で対象ノードを抽出し、危険度 (Low/Mid/High) を仮設定。
2. **安全レビュー準備**: `BLUEPRINT.md` で入出力制約を確認し、`RUNBOOK.md` の該当ステップを抜粋。
3. **審査**: High リスクの場合は Security オーナーと共同レビュー。Mid 以下でも自動化は観測モードに限定。
4. **実行/検証**: 許可後に変更を実施し、`EVALUATION.md` の検収条件で検証。想定外の副作用は即ロールバック。
5. **記録/同期**: 結果を `CHANGELOG.md` へ記載し、`docs/birdseye/index.json`/`caps/*.json` を更新。

## 禁止事項

- 本番環境への書き込み、外部サービスへの未承認リクエスト。
- レビュー未完了の自動コミットや強制 push。
- 安全審査を経ずに `src/**` へ修正を直接適用する行為。

## 例外とエスカレーション

- 緊急度 High のセキュリティ事故は `SECURITY.md` の連絡先へ 2 時間以内に報告し、Runbook のインシデントフローへ移行。
- 安全審査の判断が割れる場合は `governance/policy.yaml` の優先度決定ルールに従って決裁者を指名。

## 監査・更新

- 月次で本ドキュメントと `docs/safety.md`、`workflow-cookbook/SECURITY.md` の齟齬を確認する。
- Birdseye `hot.json` の優先度が過去 1 か月のインシデントと乖離した場合は再評価。
- 更新時は `python workflow-cookbook/tools/codemap/update.py --targets docs/birdseye/index.json --emit index+caps` を実行し、索引とカプセルを同時更新する。

## 関連資料

- [docs/safety.md](../docs/safety.md)
- [workflow-cookbook/GUARDRAILS.md](./GUARDRAILS.md)
- [workflow-cookbook/SECURITY.md](./SECURITY.md)
- [workflow-cookbook/RUNBOOK.md](./RUNBOOK.md)
- [workflow-cookbook/CHECKLISTS.md](./CHECKLISTS.md)

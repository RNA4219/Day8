# Day8 セキュリティレビュー チェックリスト

Katamari の `docs/Security_Review_Checklist.md` を Day8 の運用と用語へ合わせて再編したチェックリストです。`docs/day8/security/05_security.md` の審査手順と Appendix G（`docs/addenda/G_Security_Privacy.md`）で定義された運用ノートを補完し、PR 審査やリリース判定で Secrets / CORS / Rate limit / OAuth / 依存性スキャンの整合を即座に確認できる単一ページを提供します。

## 利用手順
1. 審査対象の変更点を確認したら、本チェックリストの対象セクションをすべて開き、該当項目を順に確認してください。
2. 各項目は **「Day8 の必須要件を満たしているか」** を Yes/No で判断できる粒度になっています。該当しない場合でも背景をコメントに残し、`docs/day8/security/05_security.md` の詳細手順に沿って是正計画を記録します。
3. 完了後は PR 本文・Birdseye Capsule に結果を転記し、必要に応じて Appendix G と Release Checklist を同期してください。

> **備考:** 本ドキュメントはチェック項目の集約に特化しています。個別のハンドブックや例外承認フローは `docs/day8/security/05_security.md` と Appendix G を参照してください。

## Secrets
- [ ] Vault / Secret Manager に格納し、Git 管理や Issue コメントへ出力していない。
- [ ] ローテーション計画と実施履歴を Appendix G および `workflow-cookbook/SECURITY.md` に同期した。
- [ ] CI/CD で利用するシークレットの参照権限を最小化し、不要な共有を停止した。

## CORS
- [ ] 新規 / 変更エンドポイントのオリジンを Allowlist に追加し、ワイルドカードを使用していない。
- [ ] `OPTIONS` プリフライトレスポンスに必要なヘッダ (`Access-Control-Allow-Methods` / `Headers` / `Max-Age`) を設定し、回帰テストで検証した。
- [ ] Appendix G の通信保護ガイドに従い、HTTPS/TLS 設定とヘッダポリシー（`Strict-Transport-Security` 等）を確認した。

## Rate limit
- [ ] `governance/policy.yaml` の `rate_limits` を更新し、リクエスト増加時のフォールバック策を定義した。
- [ ] 追加のバースト制御・キューイングが必要な場合、Appendix G / Release Checklist に周知済み。
- [ ] Rate limit 逸脱時のアラート閾値と通知経路を Ops Runbook と同期した。

## OAuth
- [ ] クライアント ID / シークレットを Vault に格納し、ローカル設定ファイルに平文で保存していない。
- [ ] 付与スコープを最小化し、不要なスコープを削除した。
- [ ] リダイレクト URI とトークンライフタイムを見直し、例外がある場合は Appendix G と `docs/safety.md` へ承認記録を残した。

## 依存性スキャン
- [ ] Python (`requirements*.txt`) / Node (`package*.json`) など該当するマニフェストで最新の脆弱性スキャンを実施した。
- [ ] Critical / High の CVE はパッチ済み、または Appendix G にリスク受容メモを記録した。
- [ ] SBOM や lockfile を更新した場合、Release Checklist と Birdseye インデックスへ反映した。

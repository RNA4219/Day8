---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-20
next_review_due: 2025-11-14
---

# Security Policy

- 連絡先: [security@example.com](mailto:security@example.com)
- 報告範囲: 本リポ内の仕様・ワークフローに関する脆弱性
- 初回応答SLA: 5営業日以内
- 公開方針: 影響評価と修正完了後に公開。重大案件はCVE取得を検討

## Security Review Checklist

リリース前・重大変更時のセキュリティレビューでは、以下のチェックリストのガイドに従って確認する。

- [ ] Secrets 管理: 平文Secretsの混入がなく、Vault等で権限分離とローテーションが実施されている。
- [ ] CORS 制限: 本番で許可するオリジンを明示し、ワイルドカード許可や不要なヘッダー開放がない。
- [ ] レート制限: 公開API/エンドポイントにレート・同時接続制御が設定され、DoS/ブルートフォース緩和が有効。
- [ ] OAuth リダイレクト検証: 登録済みリダイレクトURIのみ許可し、state/nonce 等の検証でオープンリダイレクトを防いでいる。
- [ ] 依存性スキャン: SCA/Dependabot等の依存性スキャンが最新で、Critical/Highの未対応Issueがない。

# Day8 Theme Catalog

Katamari 版 `themes/` をベースに、Day8 のブランドカラーと運用要件へ最適化したテーマセットです。Chainlit 1.x の `theme_path` へ `.theme.json` を指定すると UI 全体へ即時適用されます。

## プリセット一覧

| ファイル | 説明 | アクセント | 想定シーン |
| --- | --- | --- | --- |
| `classic.theme.json` | Katamari Classic を Day8 ロゴブルーへ合わせた標準テーマ。最小限の変更で Katamari 互換運用を継続できます。 | `#1F6FEB` | デフォルト UI、オンボーディング、Docs 共有 |
| `mocha.theme.json` | ナイトモードを前提にウォームトーンへ再調整。Evaluator/Reporter の夜間レビューで視認性を確保します。 | `#E48D6A` | 夜間レビュー、低照度環境 |
| `highcontrast.theme.json` | Appendix K の AA コントラスト基準を満たすアクセシビリティ特化パック。主要操作の輪郭を強調します。 | `#0EA5E9` | アクセシビリティレビュー、投影資料 |

## 適用手順

1. `chainlit.toml` の `[project.ui]` セクションに `theme_path = "themes/classic.theme.json"` などを設定します。
2. `public/theme.json` を既定テーマとして配置すると、Chainlit Hosted Static から直接読み込まれます。
3. `public/stylesheet.css` を `custom_css` で指定すると補助的なレイアウト調整が適用されます。

### Day8 での配布ポリシー

- テーマ追加時は Appendix B (UI Mock) と Appendix C (Persona Schema) の導線が崩れないかを確認します。
- `docs/birdseye/index.json` / `hot.json` の `generated_at` を更新し、Capsule を追加して参照ハブを維持してください。

## Appendix との関連

- Appendix B: UI Mock と色分布の擦り合わせ。
- Appendix C: ペルソナごとの表示要件とチェーン設定の整合。
- Appendix K: アクセシビリティ要件の再確認 (High Contrast 適用時)。

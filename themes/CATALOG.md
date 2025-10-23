# Day8 Theme Catalog

Day8 のテーマセットは、ブランド体験とオペレーション効率の両立を目的にチューニングした UI プリセットです。各テーマは Day8 の評価ワークフローとペルソナ導線を前提に配色・奥行きを再構成しており、Chainlit 1.x の `theme_path` へ `.theme.json` を指定するだけで適用できます。

## プリセット一覧

| ファイル | 説明 | アクセント | 想定シーン |
| --- | --- | --- | --- |
| `classic.theme.json` | Day8 のロゴブルーを軸に情報密度の高い画面でも視線誘導しやすいよう設計したオールラウンダー。 | `#1F6FEB` | デフォルト UI、オンボーディング、Docs 共有 |
| `mocha.theme.json` | 夜間稼働するレビューチーム向けにウォームダークで目の疲労を軽減し、ハイライトの温度差で優先度を伝える構成。 | `#E48D6A` | 夜間レビュー、低照度環境 |
| `highcontrast.theme.json` | Appendix K 準拠で Day8 の操作ハイライトを強調し、色覚多様性にも配慮したアシスト重視のセット。 | `#0EA5E9` | アクセシビリティレビュー、投影資料 |

## 適用手順

1. `chainlit.toml` の `[project.ui]` セクションに `theme_path = "themes/classic.theme.json"` などを設定します。
2. テーマ切替時は `python scripts/switch_theme.py <theme-name>` を実行し、`themes/<theme-name>.theme.json` を `public/theme.json` へコピーします。
3. `public/theme.json` を既定テーマとして配置すると、Chainlit Hosted Static から直接読み込まれます。
4. `public/stylesheet.css` を `custom_css` で指定すると補助的なレイアウト調整が適用されます。

### Day8 での配布ポリシー

- テーマ追加時は Appendix B (UI Mock) と Appendix C (Persona Schema) の導線が崩れないかを確認します。
- `docs/birdseye/index.json` / `hot.json` の `generated_at` を更新し、Capsule を追加して参照ハブを維持してください。

## Appendix との関連

- Appendix B: UI Mock と色分布の擦り合わせ。
- Appendix C: ペルソナごとの表示要件とチェーン設定の整合。
- Appendix K: アクセシビリティ要件の再確認 (High Contrast 適用時)。

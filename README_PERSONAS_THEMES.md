# Day8 Personas & Themes ガイド

Katamari `README_PERSONAS_THEMES.md` をベースに、Day8 へ導入する Chainlit テーマと今後拡張するペルソナ運用ルールを集約します。Appendix B (UI Mock) と Appendix C (Persona Schema) を主導線とし、Birdseye と TOML 設定で即時適用できる構成を維持します。

## 1. Chainlit 設定

`chainlit.toml` に以下の設定を追加し、Day8 既定のテーマ・カスタム CSS を読み込ませます。

```toml
[project.ui]
theme_path = "themes/classic.theme.json"
custom_css = "public/stylesheet.css"

[project]
# Day8 での Hosted Static 配布を想定し、プリセットを公開ディレクトリにも配置する
public = "public"
```

- `public/theme.json` は Hosted Static 側で即時反映されるプリセットです。`theme_path` を変更しても fallback として利用されます。
- `custom_css` は Chainlit 1.1 以降でサポートされており、アクセントやカードレイアウトの微調整を Day8 標準へ揃えます。

## 2. テーマ導線

- `themes/CATALOG.md`: Day8 向けテーマ一覧と Appendix 連動要件を整理。
- `public/theme.json`: Hosted Static/iframe 配信時のデフォルトテーマ。
- `public/stylesheet.css`: ロゴカラー (#1F6FEB) に合わせた補助的なレイアウト。

## 3. ペルソナ拡張予定

- Appendix C に定義されている `insights_required` を満たす UI 要件をテーマと同期。
- 追加予定のペルソナ YAML は `personas/` 配下へ配置し、本ドキュメントから導線を張る。
- 追加時は Birdseye (`docs/birdseye/index.json` / `hot.json`) の `generated_at` と Capsule を同時更新し、差分検知を維持。

### TODO (ペルソナ追加時)

- [ ] Analyzer 系の夜間レビュー向けテーマ要件を Appendix B と突き合わせる。
- [ ] Reporter 系のダッシュボード改修時に High Contrast 運用を追記する。
- [ ] 新規 YAML 追加後は `personas/README.md` と `themes/CATALOG.md` のクロスリンクを確認する。

## 4. Appendix 参照

- **Appendix B:** UI Mock でテーマ別の画面バランスを確認。
- **Appendix C:** ペルソナスキーマの必須フィールドと UI 要件を再確認。
- **Appendix K:** アクセシビリティ基準 (High Contrast) を満たしているか検証。

## 5. Birdseye 連携

- `docs/birdseye/index.json` に `themes/CATALOG.md` と本ドキュメントを登録。
- Capsule (`docs/birdseye/caps/themes.CATALOG.md.json` / `docs/birdseye/caps/README_PERSONAS_THEMES.md.json`) を作成し、`generated_at` をホットリストと同期。
- ホットリストは Appendix 更新時のみ追加。初回はリンク網の確認を優先する。

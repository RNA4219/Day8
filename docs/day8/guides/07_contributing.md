# 貢献ガイド（Contributing）

## ブランチ/PR ルール
- 1タスク=1ブランチ=1PR（±300行/≤3ファイルを目安）
- レビュー前・マージ前に rebase で追従
- 公開 API/スキーマ変更は先行PR（契約合意）

## タスク化（衝突回避）
- タスクは独立性が保てる粒度まで分割し、責務の重複（コンフリクト）を避ける。
- 変更は小さく・短時間で終わるブランチとして切り、早めの rebase で常に最新に追従する。
- リスクや重なりがある場合は **Task Seeds**（ガイド: [`docs/TASKS.md`](../../TASKS.md) / テンプレート: [`workflow-cookbook/TASK.codex.md`](../../../workflow-cookbook/TASK.codex.md) / 保存先: `docs/seeds/TASK.<slug>-YYYY-MM-DD.md`）を作成し、「背景/手順/検証ログ/フォローアップ」を Day8 テンプレート順に埋めてから着手する。テンプレートのメタデータや検証ログ更新の詳細は [`docs/TASKS.md`](../../TASKS.md) と [Day8 Upstream ガイド](../../UPSTREAM.md) を参照する。

# Task Seed 配置ガイド

- **命名規約**: `TASK.<slug>-YYYY-MM-DD`
  - `<slug>` はタスクを要約する英小文字・ハイフン区切り。
  - `YYYY-MM-DD` は Seed 作成日。
- **Day8 テンプレート**: すべての Seed は [docs/seeds/TASK.template-YYYY-MM-DD.md](TASK.template-YYYY-MM-DD.md) を基準に作成する。テンプレート内コメントのチェックリストに沿って、作業内容を Day8 形式で整理する。
  1. `cp docs/seeds/TASK.template-YYYY-MM-DD.md docs/seeds/TASK.<slug>-YYYY-MM-DD.md`
  2. ファイル名と front matter (`task_id`, `repo`, `base_branch`, `work_branch`, `priority`, `langs`, `status`, `last_reviewed_at`, `next_review_due` など) をタスク情報へ置き換える。
  3. Objective / Scope / Requirements を起点に、Plan・Patch・Tests・Commands・Notes へ進捗を反映させる。各セクションの期待内容はテンプレート先頭の説明と [`../TASKS.md`](../TASKS.md) の運用ガイドを参照する。
- **必須セクション**:
  1. メタデータ（YAML front matter: `task_id`, `repo`, `base_branch`, `work_branch`, `priority`, `langs`, `status`, `last_reviewed_at`, `next_review_due`）
  2. Objective / Scope / Requirements
  3. Affected Paths / Local Commands / Deliverables
  4. Plan / Patch / Tests / Commands / Notes（検証ログとフォローアップの更新記録）
- **補足**: 運用詳細と記入方法は [`../TASKS.md`](../TASKS.md) を参照してください。

# Task Seed 配置ガイド

- **命名規約**: `TASK.<slug>-YYYY-MM-DD`
  - `<slug>` はタスクを要約する英小文字・ハイフン区切り。
  - `YYYY-MM-DD` は Seed 作成日。
- **Katamari テンプレート**: [docs/TASKS.md](../TASKS.md) に従い、「背景」「手順」「検証ログ」「フォローアップ」の流れで記入する。
- **Day8 テンプレート**: [docs/seeds/TASK.template-YYYY-MM-DD.md](TASK.template-YYYY-MM-DD.md) をコピーし、`<slug>`・`YYYY-MM-DD`・`task_id` などのメタデータを作業内容に合わせて差し替える。
  1. `cp docs/seeds/TASK.template-YYYY-MM-DD.md docs/seeds/TASK.<slug>-YYYY-MM-DD.md`
  2. ファイル名と front matter (`task_id`, `work_branch`, `langs`, `status`, `last_reviewed_at`, `next_review_due` など) を更新する。
  3. Objective 以降の各セクションをタスク固有の情報で埋め、Plan/Tests/Commands/Notes を進捗に合わせて更新する。
- **必須セクション**:
  1. メタデータ（YAML front matter: `task_id`, `repo`, `base_branch`, `work_branch`, `priority`, `langs`, `status`, `last_reviewed_at`, `next_review_due`）
  2. Objective / Scope / Requirements
  3. Affected Paths / Local Commands / Deliverables
  4. Plan / Patch / Tests / Commands / Notes（検証ログとフォローアップの更新記録）
- **補足**: 運用詳細と記入方法は [`../TASKS.md`](../TASKS.md) を参照してください。

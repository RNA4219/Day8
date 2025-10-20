# Task Seed 配置ガイド

- **命名規約**: `TASK.<slug>-YYYY-MM-DD.md`
  - `<slug>` はタスクを要約する英小文字・ハイフン区切り。
  - `YYYY-MM-DD` は Seed 作成日。
- **必須セクション**:
  1. メタデータ（YAML front matter: `task_id`, `repo`, `base_branch`, `work_branch`, `priority`, `langs`, `status`, `last_reviewed_at`, `next_review_due`）
  2. Objective / Scope / Requirements
  3. Affected Paths / Local Commands / Deliverables
  4. Plan / Patch / Tests / Commands / Notes
- **補足**: 運用詳細と記入方法は [`../TASKS.md`](../TASKS.md) を参照してください。

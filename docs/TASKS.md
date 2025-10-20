# Task Seeds 運用方針（Day8）

## 目的
Task Seed はリポジトリ内で進行する作業を事前共有し、衝突や抜け漏れを防ぐための軽量ドキュメントです。`workflow-cookbook/TASK.codex.md` のテンプレートに準拠し、目的・範囲・受入基準を簡潔に整理します。

## 作成・更新手順
1. **タスク識別子を定義**: `task_id` には日付ベースの連番（例: `20250115-01`）を用います。`work_branch` は作業ブランチ名、`priority` は `P1|P2|P3` のいずれかを選択します。
2. **メタデータを記入**: テンプレートの YAML ブロックへリポジトリ URL、ベース/作業ブランチ、対応言語などを記載します。
3. **Objective/Scoop/Requirements を整備**:
   - Objective: 目的を一文で明示します。
   - Scope: 対象領域と非対象領域を箇条書きで列挙します。
   - Requirements: 期待挙動、I/O 契約、制約、受入基準をテンプレート順で埋めます。
4. **影響範囲とローカルコマンド**: 変更が想定されるパスを `glob` 表記で示し、対象スタックに合ったローカルコマンド（lint/type/test 等）を列挙します。
5. **成果物と後続管理**: PR で明記すべき項目（Intent ID、Priority Score、評価セクションなど）や、想定リスク・フォローアップを記入します。

## 保存規約
- **配置先**: `docs/seeds/` ディレクトリ配下に保存します。
- **ファイル名**: `TASK.<slug>-YYYY-MM-DD.md`（例: `TASK.payment-retry-2025-01-15.md`）。`<slug>` はタスク概要を表す英小文字・ハイフン区切りで命名します。
- **構成**: テンプレートの全セクション（メタデータ、Objective、Scope、Requirements、Affected Paths、Local Commands、Deliverables、Plan、Patch、Tests、Commands、Notes）を保持します。
- **運用**: Seed はドラフトからアクティブまでの状態管理（`status` フィールド）を必ず更新し、レビュー期限 (`last_reviewed_at` / `next_review_due`) を記録します。

## レビューとアーカイブ
- 定期的に `next_review_due` を確認し、期限切れの Seed は更新もしくは `deprecated` へ移行します。
- 完了したタスクの Seed には PR/コミットなどの成果リンクを追記し、将来の参照に備えます。

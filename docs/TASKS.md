# Task Seeds（Day8）

Day8 のタスク運用は、Guardrails と Day8 固有の CI ルールに合わせて最小編集で連携できるよう再構成しています。変更の衝突を防ぎ、レビュー前に要件・検証観点を揃えるため、以下の手順で Task Seed を作成・保守してください。

## 保存場所と命名規約
- 保存先: `docs/tasks/`
- ファイル名: `TASK.<slug>-YYYY-MM-DD.md`
  - `<slug>` は対象領域を 1〜2 語で表現（例: `observability`, `docs-refresh`）。
  - 日付は作成日（UTC 基準）。
- 既存の Seed を更新するときは追記履歴を残し、必要なら `Follow-ups` セクションを分割して明示します。

> **Note:** 旧パス（`docs/seeds/` や ルート直下 `TASK.*`）を参照する資料を見つけた場合は、本ページに従ってリンクと記法を `docs/tasks/` へ移行してください。

## Seed の目的
- 意図と完了条件をレビュー前に共有し、作業単位を 1 ブランチ 1 PR に収束させる。
- Guardrails／CHECKLISTS／Runbook で定義されたゲート（Lint/Type/Test/優先度報告）を外さずに適用する。
- Birdseye（index → caps → hot）から参照したときに、どの文書を更新するか即座に追跡できるようにする。

## テンプレート
以下は Day8 版の Task Seed テンプレートです。必要に応じて [workflow-cookbook/TASK.codex.md](../workflow-cookbook/TASK.codex.md) と突き合わせてください。

```markdown
---
task_id: YYYYMMDD-xx
repo: https://github.com/owner/repo
base_branch: main
work_branch: feat/<short-slug>
priority: P1|P2|P3
langs: [auto]
owner: contributor-handle
---

# Objective
{{一文で目的}}

## Scope
- In:
  - {{対象（ディレクトリ/機能/CLI）}}
- Out:
  - {{非対象}}

## Requirements
- Behavior:
  - {{期待挙動1}}
  - {{期待挙動2}}
- I/O Contract:
  - Input: {{型/例}}
  - Output: {{型/例}}
- Constraints:
  - 既存API破壊なし / 依存追加なし
  - Lint/Type/Test はゼロエラー（例: `ruff check`, `mypy --strict`, `pytest -q`）
- Acceptance Criteria:
  - {{検収条件1}}
  - {{検収条件2}}

## Affected Paths
- {{glob 例: backend/src/**, frontend/src/hooks/**, tools/*.sh}}

## Local Commands
- {{適用スタックのコマンド}}

## Deliverables
- PR: タイトル・要約・影響・ロールバックに加え `Intent: INT-xxx` と `## EVALUATION` を明記
- Artifacts: コード差分／テスト結果／必要なドキュメント更新

## Notes
### Rationale
- {{設計判断}}

### Risks
- {{互換性リスク}}

### Follow-ups
- {{後続タスクや検証項目が残る場合に記載}}
```

## フォローアップ手順
1. Seed を作成／更新したら、PR 説明に `Task Seed: docs/tasks/TASK.<slug>-YYYY-MM-DD.md` を添付。
2. 対応完了後も未解決の懸念があれば `Follow-ups` に残し、Birdseye のカプセル再生成時に拾えるよう日時と担当を追記。
3. Guardrails や CHECKLISTS に影響する変更を検出した場合は、関連ドキュメントを同一 PR で更新するか、別 Seed を起票して依存関係を明示。
4. Seed をクローズ（完了）したら、最後のコミットで `Follow-ups` を空にするか、派生 Seed へのリンクでクローズ可否を示してください。

---
Day8 では Seed 作成時の証跡が CI の観測対象となるため、本ページを更新した場合は `docs/birdseye/index.json` の再生成手順に従って Birdseye を同期することを忘れないでください。

# コントリビューションガイド

Day8 への参加に関心をお寄せいただきありがとうございます。開発の背景や仕様の詳細は [`docs/ROADMAP_AND_SPECS.md`](docs/ROADMAP_AND_SPECS.md) で俯瞰できます。変更提案の前に必ず参照し、目的と整合するか確認してください。

## 参加手順
1. 課題調査
   - 既存の仕様・ロードマップ: [`docs/ROADMAP_AND_SPECS.md`](docs/ROADMAP_AND_SPECS.md)
   - 運用と安全策: [`workflow-cookbook/GUARDRAILS.md`](workflow-cookbook/GUARDRAILS.md)、[`workflow-cookbook/RUNBOOK.md`](workflow-cookbook/RUNBOOK.md)
2. Issue 作成
   - `.github/ISSUE_TEMPLATE/` のテンプレートから最適な形式を選び、背景・検証方針・影響範囲を明記してください。
3. 実装
   - `INSTALL.md` の開発環境手順に従いセットアップし、変更は最小限に保ちます。
   - Lint/テストポリシー（`mypy --strict`、`ruff`、`pytest`、`node:test`）を遵守し、コミット前に実行してください。
4. プルリクエスト
   - [`workflow-cookbook/RUNBOOK.md`](workflow-cookbook/RUNBOOK.md) の検証フローと `.github/PULL_REQUEST_TEMPLATE.md` のチェックリストを順守します。
   - 反省レポートや生成物は `workflow-cookbook/` 配下の規約に従って整理します。

## 行動規範
Day8 の協力者はすべて [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) に従う必要があります。違反が疑われる場合は runbook の連絡手順に従って報告してください。

## ガバナンス
リリースポリシーや権限管理は `governance/` 以下の設定ファイルで管理しています。変更が必要な場合は別途 Issue を起票し、CODEOWNERS の承認を得てください。

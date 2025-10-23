# Day8 Fork Notes

Day8 リポジトリで維持するコンポーネント・依存関係・ライセンス同梱ルールを整理したメモです。Day8 のリリースや配布物を更新する際は、本ページと Birdseye (`docs/birdseye/index.json` / `docs/birdseye/caps/docs.FORK_NOTES.md.json`) を同じコミットでそろえて反映してください。Day8 固有の履歴は [CHANGELOG.md](../CHANGELOG.md) に、運用手順やスクリプトの履歴は [workflow-cookbook/CHANGELOG.md](../workflow-cookbook/CHANGELOG.md) に記録し、双方の更新タイミングを揃えます。

## Day8 固有コンポーネント
- **Day8 ドキュメント群** — `docs/day8/` 配下の仕様・設計・運用ディレクトリを一括で維持します。Collector / Analyzer / Reporter / Proposer / Governance の責務は [Day8 アーキテクチャ](day8/design/03_architecture.md) を最優先で参照し、Mermaid が読めない環境では [Architecture ASCII](Architecture_ASCII.md) を併用します。
- **Birdseye 拡張** — `docs/birdseye/index.json`・`docs/birdseye/caps/`・`docs/birdseye/hot.json` は Day8 固有の索引／ホットリストを含みます。更新フローは [docs/birdseye/README.md](birdseye/README.md) の「index → caps → hot」順を維持してください。
- **workflow-cookbook サブツリー** — CI ログ・レポート・スクリプトは `workflow-cookbook/` をサブツリー取り込みして共有します。Collector 出力は `workflow-cookbook/logs/`、Reporter 出力は `workflow-cookbook/reports/` に揃え、[リポジトリ README](../README.md) に記載された参照順序を守ります。

- **Python 3.11+** — Birdseye 再生成ツール `scripts/birdseye_refresh.py` は標準ライブラリのみで動作しますが、実行には Python 3.11 以上が必須です。
- **Lint & Test スイート** — Day8 では `mypy --strict`、`ruff`、`pytest`、`node --test` を常に通すことを [CONTRIBUTING.md](../CONTRIBUTING.md) で要求しています。追加モジュールを導入する場合は、CI で同じ順序のジョブを維持してください。
- **GitHub Actions 反省フロー** — `test` → `reflection` → `pr_gate` の 3 ワークフローが Day8 導入手順の基本であり、`workflow-cookbook/scripts/analyze.py` を用いた Analyzer が必須です。[INSTALL.md](../INSTALL.md) を確認し、必要ファイルの同梱を忘れないでください。

## ライセンスと同梱ルール
- **Day8 本体** — Apache License 2.0 (`LICENSE`) を維持し、フォークでも変更しません。
- **workflow-cookbook 資産** — `workflow-cookbook/` 配下は MIT License です。フォークで取り込む際は [NOTICE](../NOTICE) に列挙された表記と `workflow-cookbook/LICENSE` の同梱を必須にしてください。
- **リリース前チェック** — 依存追加でライセンス同梱が変わる場合は [Day8 Release Checklist](Release_Checklist.md) の該当項目を更新し、Birdseye を同一コミットで再生成します。

## 参照・更新順
1. Day8 リリース差分の整理 — [CHANGELOG.md](../CHANGELOG.md)
2. Day8 共通メモ — 本ページ（Day8 Fork Notes）
3. Day8 Birdseye リソース — `docs/birdseye/index.json` → `docs/birdseye/caps/docs.FORK_NOTES.md.json` → `docs/birdseye/hot.json`
4. Day8 運用ログ — [docs/UPSTREAM.md](UPSTREAM.md) / [docs/UPSTREAM_WEEKLY_LOG.md](UPSTREAM_WEEKLY_LOG.md)

Day8 固有の依存や配布物を追加した場合は、上記の順で差分確認と記録を行い、`docs/UPSTREAM_WEEKLY_LOG.md` に同期ログを追記してください。

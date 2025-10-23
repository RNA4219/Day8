# Day8 リリースチェックリスト

Day8 のリリースフローは本リポジトリ内で完結することを前提に、`main` ブランチを唯一の信頼できるソースとして運用します。すべての変更は Pull Request を通じて統合し、Day8 のドキュメント・Birdseye ノード・CI 設定との整合を段階的に確認します。本チェックリストは Day8 固有の計画、実装、検証、承認、リリース後対応を順序立てて整理したものです。

## 1. 計画とスコープの明確化
- [ ] Day8 リポジトリ内の `workflow-cookbook/CHECKLISTS.md` Release セクションを確認し、本リリースで扱う変更点と優先度を PR 説明欄へ下書きする。
- [ ] 変更が Day8 の公開 API や CLI に影響する場合、`docs/addenda/M_Versioning_Release.md` を参照して互換性判断と semver ラベル案を調整する。
- [ ] `main` ブランチへの直接 push を防ぐ分岐保護とレビューア割当が有効であることを確認する。

## 2. 実装ブランチ準備
- [ ] lint (`ruff`)、型検査 (`mypy --strict`)、テスト（`pytest` / `node --test`）をローカルで実行し、失敗時は原因を特定して差分を再作成する。
- [ ] `pip install -r requirements-dev.txt` を実行し、CI と同一バージョンの依存関係で開発できるよう整える。
- [ ] 対象ドキュメントの更新要否を確認し、Birdseye への反映対象であれば必要な差分を準備する。
- [ ] `NOTICE` / `LICENSE` へ影響する依存追加の有無を確認し、必要時は `docs/addenda/H_Deploy_Guide.md` を参照して同梱手順を整理する。

## 3. CI とドキュメント整合
- [ ] `docker build -t day8 .` を実行し、開発環境に依存せずビルドが成功することを確認する。完了後に `docker run --rm day8` で `pytest` が成功することを記録する。
- [ ] GitHub Actions とローカル CI（mypy, ruff, pytest, node:test, Docker ビルド）の成功ログを取得して共有可能な状態にする。
- [ ] Birdseye を `python scripts/birdseye_refresh.py --docs-dir docs/birdseye --docs-dir workflow-cookbook/docs/birdseye` で再生成し、`generated_at` を含む生成物が一貫していることを確認する。生成物の参照先は Day8 リポジトリ配下で揃える。
- [ ] `python scripts/perf/collect_metrics.py --prom-url http://localhost:8000/metrics --chainlit-log workflow-cookbook/logs/test.jsonl` を実行し、Day8 が収集する `day8_*` メトリクスが更新されていることを確認する。必要に応じて直近の Chainlit ログへ差し替える。
- [ ] Birdseye に追加されたノードやエッジが `docs/README.md` および `docs/ROADMAP_AND_SPECS.md` から到達可能であることを確認する。
- [ ] `docs/addenda/M_Versioning_Release.md` の指針に沿って `semver:*` ラベルを確定し、互換性判断を PR 本文へ反映する。
- [ ] `workflow-cookbook/reflection.yaml` を変更した場合は [ADR 0005](docs/adr/0005-reflection-manifest.md) の既定値との整合を確認し、関連する Birdseye 生成物 (`index.json`, `caps`, `hot.json`) の `generated_at` を揃える。

## 4. レビューと承認
- [ ] PR テンプレートに沿って変更概要、影響範囲、検証結果、Birdseye コマンド出力を記載する。
- [ ] レビュー担当が検証できるよう、`scripts/` や `tools/` の代表的な実行例を提示する。
- [ ] `governance/policy.yaml` など Day8 のガバナンス設定に違反していないか再確認し、必要に応じてガバナンス担当へエスカレーションする。
- [ ] レビュー承認後に `type:*` / `semver:*` ラベル、Priority Score、テスト結果が揃っていることを確認し、merge queue へ登録する。

## 5. リリース後対応
- [ ] タグ付与とリリースノート作成は `docs/addenda/M_Versioning_Release.md` の手順に従い、PR ベースで進める。
- [ ] release ブランチが `main` と同期していることを確認し、Birdseye `hot.json` の重点参照対象に変更があれば更新する。
- [ ] リリース結果を `docs/UPSTREAM_WEEKLY_LOG.md` に追記し、`workflow-cookbook/CHANGELOG.md` を含む Day8 内ドキュメントと整合を取る。

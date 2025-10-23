---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-14
next_review_due: 2025-11-14
---

# Checklists

## Daily

- 入力到着の確認
- 失敗通知の有無
- 主要メトリクス閾値

## Release

- `workflow-cookbook/CHECKLISTS.md` > Release の適用範囲を確認し、PR 説明欄に Priority Score と semver ラベル案を下書きする。
- 変更内容が Day8 の公開 API や CLI を破壊しないか洗い出し、必要なら [docs/addenda/M_Versioning_Release.md](../docs/addenda/M_Versioning_Release.md) の互換性ガイドを参照してスコープを再調整する。
- propose-only 運用のため、`main` 直 push を禁止する分岐保護が有効であること、ならびにレビューア割当が完了していることを確認する。
- lint (`ruff`)、型検査 (`mypy --strict`)、テスト（`pytest` / `node --test`）のローカル実行結果を記録し、失敗時は fixup ではなく再実装で対応する。
- `pip install -r requirements-dev.txt` で Python 依存を同期し、`workflow-cookbook/scripts/run_ci_tests.py` の `python::root` ジョブが同 requirements を参照することを確認する。
- リリース対象ファイルに係るドキュメント差分を作成し、Birdseye 対象の更新が必要か判定する。
- `NOTICE` / `LICENSE` の同梱に影響する依存追加がないかチェックし、必要なら [docs/addenda/H_Deploy_Guide.md](../docs/addenda/H_Deploy_Guide.md) の同梱手順を参照する。
- `docker build -t day8 .` を実行し、`requirements-dev.txt` が正しく解決されることを確認。完了後に `docker run --rm day8` で pytest がローカル CI と同等に成功することを記録する。
- GitHub Actions / ローカル CI の全ジョブ（mypy, ruff, pytest, node:test, Docker ビルド）が成功したログを取得する。
- Birdseye を `python scripts/birdseye_refresh.py --docs-dir docs/birdseye --docs-dir workflow-cookbook/docs/birdseye` で再生成し、`index.json` → `caps` → `hot.json` を含む全ファイルの `generated_at` を同一値へ揃える。
- `python scripts/perf/collect_metrics.py --prom-url http://localhost:8000/metrics --chainlit-log workflow-cookbook/logs/chainlit.jsonl` を実行し、`day8_*` メトリクスが Prometheus / Chainlit 双方で更新されていることを確認する。
- Birdseye で新規に追加したノード／エッジが `docs/README.md`、`docs/ROADMAP_AND_SPECS.md` から到達可能か確認する。
- [docs/addenda/M_Versioning_Release.md](../docs/addenda/M_Versioning_Release.md) の semver 区分に沿って `semver:*` ラベルを更新し、互換性根拠を PR 本文へ反映する。
- `workflow-cookbook/reflection.yaml` を更新した場合は [docs/adr/0005-reflection-manifest.md](../docs/adr/0005-reflection-manifest.md) の既定値を再確認し、Appendix L / Birdseye の `generated_at` を同じコミットで揃える。
- PR テンプレートに沿って、変更概要・影響範囲・検証結果・Birdseye コマンド出力を記載する。
- Reviewer が propose-only ブランチで動作確認できるよう、`scripts/`・`tools/` の実行例を提示する。
- ガバナンス違反（`governance/policy.yaml` の `forbidden_paths` 等）がないか再確認し、必要ならガバナンス担当へエスカレーションする。
- Reviewer 承認後に `type:*` / `semver:*` ラベル・Priority Score・テスト結果が揃っていることを再確認し、merge queue へ登録する。
- タグ付け・リリースノートの作成は [docs/addenda/M_Versioning_Release.md](../docs/addenda/M_Versioning_Release.md) の手順に従って propose-only で実施する。
- release ブランチが `main` と一致していることを検証し、Birdseye `hot.json` の重点参照対象に変更があれば更新する。
- リリース結果を `docs/UPSTREAM_WEEKLY_LOG.md` に追記し、Day8 内の `workflow-cookbook/CHANGELOG.md` を含む関連ドキュメントと整合させる。

## Hygiene

- 命名・ディレクトリ整備
- ドキュメント差分反映

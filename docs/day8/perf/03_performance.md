# Day8 パフォーマンス運用ガイド

Day8 の Collector → Analyzer → Proposer パイプラインで観測されるレイテンシと成功率を運用チームが共通言語で確認できるよう、SLO 定義・計測手順・ウォームアップフローを Day8 用語へ揃えてまとめる。`workflow-cookbook/` のレポート再生成と Birdseye Capsule の更新を前提とする。

## Day8 SLO テーブル

| 指標 | 目標値 | 根拠 | サンプリング元 | 補足 |
| --- | --- | --- | --- | --- |
| `duration_p95` | ≤ 45 秒 | [docs/day8/spec/02_spec.md](../spec/02_spec.md) の「観測 → 反省 → 提案」往復 SLO | `workflow-cookbook/reports/today.md` の `latency.p95` | Collector/Analyzer/Proposer 全体の P95。|
| `pass_rate` | ≥ 99% | 同上、失敗時は Error Budget を消費 | `workflow-cookbook/reports/today.md` の `summary.pass_rate` | `retry_count` を含めた最終成功率。|
| `cold_start_p95` | ≤ 5 秒（ウォームアップ後） | Katamari 本家の初回応答 SLO を Day8 向けに縮小 | `workflow-cookbook/logs/test.jsonl` (`cold_start=true`) | Analyzer モデルロード完了後の P95。|
| `error_budget_consumption` | 移動 7 日平均で < 40% | Propose-only 運用での改善余地確保 | `workflow-cookbook/reports/today.md` の `error_budget` | 40% 超で Appendix J へエスカレーション。|

- いずれかが逸脱した場合は Appendix J の性能セクションへ記録し、Birdseye Capsule `docs/day8/perf/03_performance.md` の `maintenance.refresh` を更新する。
- Error Budget の計算は pass_rate を起点に行い、`retry_count` の増加が要因なら Analyzer の再試行ポリシーを Appendix H と照合する。

## 計測ワークフロー

### 日次サイクル
1. `python workflow-cookbook/scripts/analyze.py --root . --emit report --focus latency` を実行し、`workflow-cookbook/reports/today.md` と `reports/latency.json` を再生成する。
2. レポートの `latency` と `summary` セクションを SLO テーブルと突き合わせ、`duration_p95` と `pass_rate` のしきい値判定を行う。
3. `python workflow-cookbook/scripts/analyze.py --root . --emit report --focus reliability` を追加で実行し、`error_budget` と `retry_count` の増減を把握する。
4. 結果を Birdseye Capsule の `maintenance.refresh` に転記し、`generated_at` を本日のタイムスタンプへ更新する。

### 逸脱調査
1. `duration_p95` が閾値を超えた場合、`python workflow-cookbook/scripts/analyze.py --root . --emit samples --focus latency --window 15m` を実行して直近 15 分のリクエストを抽出する。
2. `workflow-cookbook/logs/test.jsonl` で該当 Request ID の `cold_start`・`retry_count` を確認し、Collector・Analyzer・Proposer のどの段が遅延したかを分類する。
3. Analyzer の初回ロードが原因の場合、`python workflow-cookbook/scripts/run_ci_tests.py --suite analyzer_smoke` を実行してキャッシュを温める。
4. 調査内容を Appendix J の性能チェックリストと Appendix H のデプロイ後確認表へ追記し、Birdseye `hot.json` へラベル `latency-incident` を追加するか検討する。

### レポート同期
- `workflow-cookbook/reports/today.md` の更新後は `docs/birdseye/index.json` と Capsule の `generated_at` を同一値に揃える。
- Appendix J/H のチェックリストで完了チェックを付ける際は、Birdseye Capsule の `tests` セクションへ参照済みのレポート名を追記して重複調査を防ぐ。

## ウォームアップフロー

Cold Start による Analyzer 遅延を最小化するため、日次リリースや長時間未使用後の再起動時に次のフローを実施する。

1. **現状確認** — Birdseye Capsule `docs/day8/perf/03_performance.md` の `maintenance.refresh` から直近計測の `latency.p95` を確認し、閾値との差をメモする。
2. **API Ping** — `python workflow-cookbook/scripts/analyze.py --root . --emit ping --focus latency` を 5 回連続で実行し、Collector と Analyzer の健康状態をウォームアップする。
3. **モデルロード** — Analyzer が外部モデルを使用する場合、`python workflow-cookbook/scripts/run_ci_tests.py --suite analyzer_smoke` を実行し、初回ロードのキャッシュを生成する。
4. **結果検証** — `python workflow-cookbook/scripts/analyze.py --root . --emit report --focus latency` を再実行し、`cold_start=true` のイベントが 3 件以内かを確認する。
5. **ドキュメント同期** — Appendix J の「初回応答遅延」行と Appendix H の性能チェック欄に結果を反映し、Birdseye Capsule の `generated_at` を更新する。

## 運用チェックリスト

- [ ] `latency.p95` が 45 秒以内か、Birdseye Capsule と Appendix J の両方に反映した
- [ ] `summary.pass_rate` が 99% を下回った場合、原因と対応を Birdseye `maintenance.refresh` に記録した
- [ ] `cold_start=true` のイベントが 3 件以内で、ウォームアップフロー完了を Appendix H へ記録した
- [ ] Error Budget 消費が 40% 未満であることを確認し、閾値超過時は Appendix J でエスカレーションした
- [ ] `docs/birdseye/index.json` と `docs/birdseye/caps/docs.day8.perf.03_performance.md.json` の `generated_at` を揃えた

## 関連リファレンス

- [docs/day8/spec/02_spec.md](../spec/02_spec.md) — Day8 の性能要件と SLO 定義
- [docs/day8/quality/06_quality.md](../quality/06_quality.md) — メトリクス設計と評価手順
- [docs/addenda/H_Deploy_Guide.md](../../addenda/H_Deploy_Guide.md) — リリース前後の性能チェック
- [docs/addenda/J_Runbook.md](../../addenda/J_Runbook.md) — インシデント初動と Birdseye 更新フロー

# Day8 性能ガイド（Katamari 移植版）

Day8 の Collector→Analyzer→Proposer チェーンを Katamari 本家の性能運用手順に沿って監視するためのガイド。Day8 特有の SLO と計測フローへ調整し、`workflow-cookbook/` のレポート群と Birdseye を同期させる前提で利用する。

## SLO 指標

| 指標 | 目標値 | 根拠 | サンプリング元 |
| --- | --- | --- | --- |
| `duration_p95` | ≤ 45 秒 | [docs/day8/spec/02_spec.md](../spec/02_spec.md) の Day8 全体 SLO | `workflow-cookbook/reports/today.md` の `latency.p95` |
| `pass_rate` | ≥ 99% | 同上 | `workflow-cookbook/reports/today.md` の `summary.pass_rate` |
| `cold_start_p95` | ≤ 5 秒（ウォームアップ後） | Katamari 運用での初回応答 SLO を Day8 リソースに合わせて縮小 | `workflow-cookbook/logs/test.jsonl`（`cold_start=true` 行） |
| `error_budget_consumption` | 7 日移動平均で 40% 未満 | Day8 propose-only 運用でのバッファ確保 | `workflow-cookbook/reports/today.md` の `error_budget` |

- いずれかの SLO が逸脱した場合は Appendix J のランブックに従いインシデントとして扱う。
- Error Budget は pass_rate 起点で計算し、40% を超えた場合は評価・Ops 両方のレビューで原因を合意してから SLO を更新する。

## 計測手順

1. `python workflow-cookbook/scripts/analyze.py --root . --emit report --focus latency` を実行し、`reports/today.md` と `reports/latency.json` を再生成する。
2. `workflow-cookbook/reports/today.md` の `latency` と `summary` セクションを確認し、SLO 表と突き合わせる。
3. P95 逸脱を検知したら `python workflow-cookbook/scripts/analyze.py --root . --emit samples --focus latency --window 15m` を実行し、直近 15 分のログを抽出する。
4. `workflow-cookbook/logs/test.jsonl` から対象 Request ID を抽出し、`cold_start`・`retry_count` のタグを Birdseye Capsule の `maintenance.refresh` に転記する。
5. 計測結果を `docs/birdseye/index.json` と Capsule の `generated_at` と同期させたうえで、Appendix J/H のチェックリストに記録する。

### 補助スクリプト

- Katamari 由来の `workflow-cookbook/scripts/run_ci_tests.py` を活用し、CI 走査時の遅延とテスト失敗率を同時取得する。
- 今後 `scripts/warmup.sh` を整備する場合は、本ガイドのウォームアップ手順をスクリプト化して再利用する。

## ウォームアッププロセス

Cold Start 遅延の再発防止を目的に、Analyzer のキャッシュ・モデルロードを先行実行する。

1. **前提確認** — Birdseye の `docs/day8/perf/03_performance.md` Capsule `maintenance.refresh` に前回計測時の `latency.p95` を記録する。
2. **API ウォームアップ** — `python workflow-cookbook/scripts/analyze.py --root . --emit ping --focus latency` を実行し、Collector/Analyzer のヘルスチェックを連続 5 回行う。
3. **モデルロード** — Analyzer が外部モデルを使用する場合は `workflow-cookbook/scripts/run_ci_tests.py --suite analyzer_smoke` を実行し、初回ロードのキャッシュを温める。
4. **結果確認** — `workflow-cookbook/reports/today.md` を再生成し、`cold_start=true` のイベントが 3 件を超えないか確認する。
5. **ドキュメント同期** — ウォームアップ結果を Appendix J の「初回応答遅延」チェックリストと Appendix H のローカルチェックリストへ反映し、Birdseye の `generated_at` を更新する。

## 運用チェックリスト

- [ ] `workflow-cookbook/reports/today.md` の `latency.p95` が 45 秒以内か確認した
- [ ] `summary.pass_rate` が 99% を下回った場合の原因を特定し、Birdseye Capsule に追記した
- [ ] Cold Start 監視で `cold_start=true` が 3 件以内であることを確認した
- [ ] ウォームアップ後に Appendix J/H の性能項目を更新した
- [ ] `docs/birdseye/index.json` と `docs/birdseye/caps/docs.day8.perf.03_performance.md.json` の `generated_at` を揃えた

## 関連ドキュメント

- [docs/day8/spec/02_spec.md](../spec/02_spec.md) — Day8 の性能要件と SLO 定義
- [docs/day8/quality/06_quality.md](../quality/06_quality.md) — メトリクス設計と評価手順
- [docs/addenda/J_Runbook.md](../../addenda/J_Runbook.md) — インシデント初動と Birdseye 更新フロー
- [docs/addenda/H_Deploy_Guide.md](../../addenda/H_Deploy_Guide.md) — リリース前後の性能チェック手順

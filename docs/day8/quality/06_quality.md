# 品質・メトリクス

## 最低メトリクス
- pass_rate（合格率）
- duration_p95（95パーセンタイル遅延）
- flaky_rate（任意）

メトリクスを整理したら、[付録I: Day8 テストケース観点](../../addenda/I_Test_Cases.md)でチェックリスト化やレビュー前の観点洗い出しを行い、CI・レポート基盤に必要な検証項目を漏れなく揃える。

## 自動評価手順
1. ケース定義を [`workflow-cookbook/EVALUATION.md`](../../../workflow-cookbook/EVALUATION.md) と同期し、入力 YAML の `prompt`/`expected`/`metadata` を整備する。
2. 推論ログを `quality/pipeline/normalize.py` で前処理したうえで、[付録E: 評価器構成](../../addenda/E_Evaluator_Details.md) に従い BERTScore・ROUGE・ルール判定を実行する。
3. 生成された `metrics.json` をレビューし、`overall_pass`/`needs_review` を評価ログへ記録する。ルール違反が `critical` の場合は即時にガバナンスへエスカレーションする。

### チェックリスト
- [ ] Appendix E の BERTScore / ROUGE 設定と実行結果の閾値が一致しているか
- [ ] `quality/guardrails/rules.yaml` と評価ログの違反コードが同期しているか
- [ ] `metrics.json` の `generated_at` と Birdseye index/caps/hot のタイムスタンプを揃えたか
- [ ] 週次レビューで `overall_pass=false` のケースを分析し、必要に応じて Appendix E を更新したか

## レポート（例）
- 本日分のサマリ（合計テスト数、合格率、p95、失敗項目）
- Why-Why 草案（失敗の暫定仮説）

## ゲート（PR）
- CI グリーン
- CODEOWNERS 承認
- 自動改変なし（提案のみ）

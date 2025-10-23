# ADR 0006: Evaluator ゲートとハイブリッド評価ライン

- **ステータス**: Accepted
- **作成日**: 2025-11-06
- **レビュアー**: @quality-owner, @evaluation-wg
- **関連チケット/タスク**: docs/addenda/E_Evaluator_Details.md, docs/day8/quality/06_quality.md, workflow-cookbook/EVALUATION.md

## 背景
- Day8 では BERTScore・ROUGE・ルール判定を組み合わせたハイブリッド評価を `workflow-cookbook/EVALUATION.md` のフローで運用し、提案公開前に Gate を通過させている。
- `docs/day8/quality/06_quality.md` のチェックリストはこの構成を前提としているが、Evaluator の閾値や `overall_pass` 判定基準が ADR で明文化されていなかった。
- Appendix E（評価器構成）や Birdseye の品質ノードが本決定を引用しておらず、閾値変更時に根拠を辿りづらい。

## 決定
- Day8 の評価ラインは BERTScore（F1 >= 0.85）、ROUGE-L（>= 0.70）、ルール判定（違反最大重大度 < critical）を組み合わせ、いずれかのスコアが閾値を満たし、かつ重大なルール違反が無い場合に `overall_pass=true` とする。
- 評価結果は `metrics.json` に `semantic`（BERTScore）、`surface`（ROUGE）、`violations`（ルール判定）の 3 セクションで記録し、各セクションへ `threshold_met` を付与して Appendix E と同期する。
- Gate 未通過 (`overall_pass=false`) の場合は自動提案を Draft として扱い、ガバナンス承認があるまで公開を停止する。
- 閾値やルールセットを更新する際は Appendix E / `quality/06_quality.md` / Birdseye index/caps/hot を同一コミットで更新し、本 ADR を変更履歴に明記する。

## 根拠
- ハイブリッド評価により LLM のばらつきとルール判定のギャップを補完し、Day8 の品質指標（pass_rate/duration_p95）のレビューラインを安定させられる。
- `metrics.json` の構造を固定することで、CI・ダッシュボード・ガバナンスチェックが同じ根拠を参照できる。
- Gate 失敗時に Draft 扱いとする決定は propose-only ポリシーと整合し、未承認提案が公開されるリスクを防ぐ。

## 影響
- 評価器やルールセットを更新する PR は Appendix E と本 ADR を参照し、閾値の根拠を明示する必要がある。
- 自動テストでは `metrics.json` の `overall_pass` 判定と Draft 提案の制御を確認し、Gate の逸脱を検出する。
- Birdseye では ADR 0006 を品質ノードの依存に追加し、Hot リストで重大度判定のチェックポイントを共有する。

## フォローアップ
- [ ] Appendix E の「改訂ガイド」に ADR 0006 の参照と閾値更新時の手順を追記する。
- [ ] `quality/guardrails/rules.yaml` の更新テンプレートに本 ADR のリンクを追加する。

# Day8 ロードマップ & 仕様メモ

プロジェクト全体の現在地と次の一手を素早く把握するためのガイドです。既存ドキュメントの骨格を保ちつつ、各資料の読みどころを短くまとめました。迷ったときはここから辿れば、必要な一次資料に直接到達できます。

## 方向性・やりたいこと
- [docs/day8/spec/01_requirements.md](day8/spec/01_requirements.md)
  - ユーザー課題と優先機能の一覧。機能間の依存関係とスコープ境界を確認する際の出発点。
- [docs/day8/spec/02_spec.md](day8/spec/02_spec.md)
  - プロダクト仕様の決定版。画面遷移図・ユースケース・成功条件がまとまっており、追加要望が来た際の差分判断に利用。

## しくみと運用メモ
- [docs/day8/design/03_architecture.md](day8/design/03_architecture.md)
  - ドメインレイヤ構成と主要コンポーネントのデータフローを整理。新規機能を追加する場合の配置場所と既存インタフェースの制約を確認。
- [docs/day8/ops/04_ops.md](day8/ops/04_ops.md)
  - 本番／ステージングの運用手順、リリースフロー、監視アラートの扱い。障害対応や当番引き継ぎ時の必読。
- [docs/day8/quality/06_quality.md](day8/quality/06_quality.md)
  - テストピラミッド、品質ゲート、計測指標 (エラーバジェット等) の定義。変更時に満たすべき品質チェックリストがまとまっています。

## セキュリティ & サンプル
- [docs/day8/security/05_security.md](day8/security/05_security.md)
  - 脅威モデリング、データ保護方針、権限設計の指針。レビュー時に確認すべきセキュリティ境界と例外プロセスが記載。
- [docs/day8/examples/10_examples.md](day8/examples/10_examples.md)
  - 実装例・ CLI サンプル・テストダブルの使い方。既存コードに習う際のリファレンスとして利用。

## 貢献メモ
- [docs/day8/guides/07_contributing.md](day8/guides/07_contributing.md)
  - Issue テンプレート、ブランチ戦略、レビュー SLA、合意済みのコーディング規約を網羅。新規参加者へのオンボーディングにも使用。

リンク先を増やしたり構成を変えたくなった場合は、このページを更新し、合わせて Issue か PR の説明欄に簡単な変更理由を記載してください。

## Guardrails 参照順
- [workflow-cookbook/HUB.codex.md](../workflow-cookbook/HUB.codex.md)
  - ガイド全体の索引。迷った際は最初に確認し、対象ガードレールへの入口として利用。
- [workflow-cookbook/GUARDRAILS.md](../workflow-cookbook/GUARDRAILS.md)
  - Day8 の意思決定原則と境界条件。仕様検討やレビュー基準を決める場面で参照。
- [workflow-cookbook/BLUEPRINT.md](../workflow-cookbook/BLUEPRINT.md)
  - プロセス定義と責務分担のドラフト。新しい取り組みを設計する前に最新状態を確認。
- [workflow-cookbook/RUNBOOK.md](../workflow-cookbook/RUNBOOK.md)
  - 日々の運用手順。リリースや障害対応など具体的な作業に着手する直前に参照。
- [workflow-cookbook/CHECKLISTS.md](../workflow-cookbook/CHECKLISTS.md)
  - 実行前後の確認項目。RUNBOOK を進めながら、抜け漏れ確認に利用。
- [workflow-cookbook/EVALUATION.md](../workflow-cookbook/EVALUATION.md)
  - 成果検証とレトロスペクティブの観点。作業完了後に振り返り基準として適用。
- [workflow-cookbook/TASK.codex.md](../workflow-cookbook/TASK.codex.md)
  - タスク種別とハンドオフの記録フォーマット。RUNBOOK 実行記録や改善アイデアを残すときに使用。

### Guardrails 更新フロー
1. BLUEPRINT の対象セクションをドラフト化し、新しい前提や役割変更を明記する。
2. ドラフト内容に基づき RUNBOOK・CHECKLISTS・EVALUATION を同期更新し、運用手順と検証観点の齟齬を解消する。
3. 変更により新設・改訂が必要な作業テンプレートを TASK.codex.md の該当 Seed に追記する。
4. Birdseye・ADR 等の上位設計資料と整合性を確認し、差異がある場合は同一イテレーションで追随修正する。

Day8 ドキュメント群はプロダクト仕様と運用の現場知識を、Guardrails 群は意思決定とプロセス原則を担当します。どちらかを更新した際は、もう一方に影響する差分を同一コミットで反映し、常に整合した状態を保ってください。

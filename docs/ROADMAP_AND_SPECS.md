# Day8 ロードマップ & 仕様メモ

プロジェクト全体の現在地と次の一手を素早く把握するためのガイドです。既存ドキュメントの骨格を保ちつつ、各資料の読みどころを短くまとめました。迷ったときはここから辿れば、必要な一次資料に直接到達できます。

| 区分 | 文書 | 役割 / 重点観点 | 更新時のチェック |
| --- | --- | --- | --- |
| 要件 | [docs/day8/spec/01_requirements.md](day8/spec/01_requirements.md) | エンドユーザー課題と優先機能の定義。 | 機能スコープ変更時に差分を Issue へ記録。 |
| 仕様 | [docs/day8/spec/02_spec.md](day8/spec/02_spec.md) | 画面・ユースケース・成功条件の確定版。 | シーケンス/ユースケース変更時は QA チェックリストに反映。 |
| ADR / 決定ログ | [docs/day8/design/03_architecture.md](day8/design/03_architecture.md)<br>[governance/policy.yaml](../governance/policy.yaml) | 主要コンポーネントの責務と運用制約。暫定 ADR は Architecture に集約。 | 重要な設計判断は policy.yaml の SLO/制約と突き合わせ、Birdseye カプセルを同コミットで更新。 |
| チェックリスト | [workflow-cookbook/CHECKLISTS.md](../workflow-cookbook/CHECKLISTS.md)<br>[docs/day8/quality/06_quality.md](day8/quality/06_quality.md) | 実装・運用時の検証項目、品質ゲート。 | 新しい手順追加時は RUNBOOK / Birdseye deps_out と整合を取る。 |

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

## 主要ディレクトリと仕様の対応表

| ディレクトリ | 主な責務 | 紐づく仕様 / 運用資料 |
| --- | --- | --- |
| `docs/day8/spec/` | 要件・詳細仕様の一次情報。 | [01_requirements.md](day8/spec/01_requirements.md)、[02_spec.md](day8/spec/02_spec.md) |
| `docs/day8/design/` | アーキテクチャ構成と決定ログの暫定集約。 | [03_architecture.md](day8/design/03_architecture.md)、[governance/policy.yaml](../governance/policy.yaml) |
| `docs/day8/ops/` & `docs/day8/quality/` | 運用手順と品質基準。 | [04_ops.md](day8/ops/04_ops.md)、[06_quality.md](day8/quality/06_quality.md)、[workflow-cookbook/RUNBOOK.md](../workflow-cookbook/RUNBOOK.md) |
| `docs/birdseye/` & `workflow-cookbook/docs/birdseye/` | Birdseye インデックスとカプセル。参照経路の最新化を管理。 | [docs/birdseye/index.json](birdseye/index.json)、[workflow-cookbook/tools/codemap/README.md](../workflow-cookbook/tools/codemap/README.md) |
| `workflow-cookbook/` | ガードレール・チェックリスト・自動化スクリプト。 | [HUB.codex.md](../workflow-cookbook/HUB.codex.md)、[GUARDRAILS.md](../workflow-cookbook/GUARDRAILS.md)、[tools/codemap/update.py](../workflow-cookbook/tools/codemap/update.py) |

### 優先度付きロードマップ

1. **ドキュメント整備** — [docs/day8/spec](day8/spec/) 群と [docs/birdseye/index.json](birdseye/index.json) の整合性確認。差分が出た場合は [workflow-cookbook/tools/codemap/update.py](../workflow-cookbook/tools/codemap/update.py) で Birdseye を再収集し、[CHECKLISTS.md](../workflow-cookbook/CHECKLISTS.md) を同期。
2. **CI / 自動化** — [workflow-cookbook/scripts](../workflow-cookbook/scripts) や `tools/codemap` の再生成コマンドを点検し、[workflow-cookbook/GUARDRAILS.md](../workflow-cookbook/GUARDRAILS.md) の Birdseye 運用ルールに沿って自動チェックを追加。
3. **実装フェーズ** — [docs/day8/design/03_architecture.md](day8/design/03_architecture.md) の責務割りをベースに実装/テストを更新。変更内容は [docs/day8/examples/10_examples.md](day8/examples/10_examples.md) や [docs/day8/guides/07_contributing.md](day8/guides/07_contributing.md) へ反映し、最終的に REQUIREMENTS / SPEC の差分と合わせて報告。

リンク先を増やしたり構成を変えたくなった場合は、このページを更新し、合わせて Issue か PR の説明欄に簡単な変更理由を記載してください。

## 参照クイックリンク
- Birdseye 更新ルール: [workflow-cookbook/GUARDRAILS.md#Birdseye / Minimal Context Intake Guardrails（鳥観図×最小読込）](../workflow-cookbook/GUARDRAILS.md#birdseye--minimal-context-intake-guardrails鳥観図最小読込)
- Birdseye 再生成手順: [workflow-cookbook/tools/codemap/README.md](../workflow-cookbook/tools/codemap/README.md)、[tools/codemap/update.py](../workflow-cookbook/tools/codemap/update.py)
- 変更導線の総覧: [workflow-cookbook/HUB.codex.md](../workflow-cookbook/HUB.codex.md)、[docs/birdseye/caps/README.md.json](birdseye/caps/README.md.json)

## ライセンス
- プロジェクトライセンス: [LICENSE](../LICENSE)
- 追加通知・依存ライセンス: [NOTICE](../NOTICE)

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

| ドキュメント | 役割 | 参照タイミング |
| --- | --- | --- |
| HUB.codex | Guardrails 群の索引。関連資料への導線と更新履歴の確認窓口。 | Guardrails に触れる前の入口確認時 |
| GUARDRAILS | 意思決定原則・境界条件の基準書。例外判断や原則整理を担う。 | 仕様議論・レビュー方針策定時 |
| BLUEPRINT | プロセス設計と責務分担の草案。変更時の前提整理を担う。 | 新施策や大幅なプロセス変更検討開始時 |
| RUNBOOK | 日次運用手順と対応フローの詳細。 | 実作業の直前および作業中 |
| CHECKLISTS | RUNBOOK と連動する確認項目群。抜け漏れ検知を担う。 | 作業準備・完了報告時 |
| EVALUATION | 成果検証・振り返り観点の集約。 | 作業完了後の評価・レトロスペクティブ時 |
| TASK.codex | タスク種別テンプレートと Seed 管理。ナレッジ連携を担う。 | RUNBOOK 実行記録・改善事項の共有時 |

### Guardrails 更新フロー
1. BLUEPRINT の対象セクションをドラフト化し、新しい前提や役割変更を明記する。
2. ドラフト内容に基づき RUNBOOK と CHECKLISTS を同一コミットで更新し、運用手順と確認項目の整合を取る。
3. 続けて EVALUATION の観点を見直し、成果検証の指標・問いを改訂する。
4. 変更により新設・改訂が必要な作業テンプレートを TASK.codex.md の該当 Seed に追記し、運用時のタスク参照を最新化する。
5. Birdseye・ADR 等の上位設計資料と整合性を確認し、差異がある場合は同一イテレーションで追随修正する。

Guardrails を更新した場合は、本 ROADMAP_AND_SPECS.md も併せて同期し、参照順や概要が最新であることを確認してください。同じコミット内で `workflow-cookbook/` 配下の関連ドキュメント (HUB/GUARDRAILS/BLUEPRINT/RUNBOOK/CHECKLISTS/EVALUATION/TASK) を更新し、読者が最新フローを一貫して追える状態を維持します。

Day8 ドキュメント群はプロダクト仕様と運用の現場知識を、Guardrails 群は意思決定とプロセス原則を担当します。どちらかを更新した際は、もう一方に影響する差分を同一コミットで反映し、常に整合した状態を保ってください。

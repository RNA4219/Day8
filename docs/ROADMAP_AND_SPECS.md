# Day8 ロードマップ & 仕様メモ

プロジェクト全体の現在地と次の一手を素早く把握するためのガイドです。既存ドキュメントの骨格を保ちつつ、各資料の読みどころを短くまとめました。迷ったときはここから辿れば、必要な一次資料に直接到達できます。

## 上位ドキュメント索引

| 種別 | 主な用途 | Day8 リポジトリ | workflow-cookbook | 備考 |
| --- | --- | --- | --- | --- |
| 要求 | ユーザー課題の把握と範囲整理 | [docs/day8/spec/01_requirements.md](day8/spec/01_requirements.md) | [workflow-cookbook/BLUEPRINT.md](../../workflow-cookbook/BLUEPRINT.md) | 要求追加時は両リポのスコープ境界を確認 |
| 仕様 | 画面・振る舞いの確定版 | [docs/day8/spec/02_spec.md](day8/spec/02_spec.md) | [workflow-cookbook/HUB.codex.md](../../workflow-cookbook/HUB.codex.md) | 仕様差分は HUB の自動タスク分割に反映 |
| 設計 | アーキテクチャと設計判断 | [docs/day8/design/03_architecture.md](day8/design/03_architecture.md) | [workflow-cookbook/GUARDRAILS.md](../../workflow-cookbook/GUARDRAILS.md) | 設計更新時は Guardrails の原則を再確認 |
| セキュリティ | 脅威・権限・データ保護 | [docs/day8/security/05_security.md](day8/security/05_security.md) | [workflow-cookbook/SECURITY.md](../../workflow-cookbook/SECURITY.md) | 例外運用は SECURITY.md 記載の窓口へ相談 |
| 品質/テスト | 品質ゲートとテスト方針 | [docs/day8/quality/06_quality.md](day8/quality/06_quality.md) | [workflow-cookbook/EVALUATION.md](../../workflow-cookbook/EVALUATION.md) / [workflow-cookbook/CHECKLISTS.md](../../workflow-cookbook/CHECKLISTS.md) | 受入条件とチェックリストを両方確認 |
| リリースチェック | リリース前確認と承認フロー | [docs/day8/ops/04_ops.md](day8/ops/04_ops.md) | [workflow-cookbook/RUNBOOK.md](../../workflow-cookbook/RUNBOOK.md) | カナリア配信・承認プロセスは RUNBOOK が最新 |


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

## 実装モジュールと対応仕様

| 実装領域 | Day8 側の主要ディレクトリ | 参照すべき仕様/設計 | workflow-cookbook の対応資料 | 補足 |
| --- | --- | --- | --- | --- |
| 仕様・要求ドキュメント | `docs/day8/spec/` / `docs/day8/design/` | [docs/day8/spec/01_requirements.md](day8/spec/01_requirements.md) / [docs/day8/spec/02_spec.md](day8/spec/02_spec.md) | [workflow-cookbook/BLUEPRINT.md](../../workflow-cookbook/BLUEPRINT.md) / [workflow-cookbook/GUARDRAILS.md](../../workflow-cookbook/GUARDRAILS.md) | スコープや原則が変わったら両ハブを同時更新 |
| 運用・品質管理 | `docs/day8/ops/` / `docs/day8/quality/` | [docs/day8/ops/04_ops.md](day8/ops/04_ops.md) / [docs/day8/quality/06_quality.md](day8/quality/06_quality.md) | [workflow-cookbook/RUNBOOK.md](../../workflow-cookbook/RUNBOOK.md) / [workflow-cookbook/CHECKLISTS.md](../../workflow-cookbook/CHECKLISTS.md) / [workflow-cookbook/EVALUATION.md](../../workflow-cookbook/EVALUATION.md) | リリース判断や受入条件を同期 |
| セキュリティ・リスク管理 | `docs/day8/security/` / `docs/birdseye/` | [docs/day8/security/05_security.md](day8/security/05_security.md) | [workflow-cookbook/SECURITY.md](../../workflow-cookbook/SECURITY.md) / [workflow-cookbook/GUARDRAILS.md](../../workflow-cookbook/GUARDRAILS.md) | 監視対象や例外承認のフローを共有 |
| 自動化・CI パイプライン | `scripts/` / `tools/` | [docs/day8/quality/06_quality.md](day8/quality/06_quality.md) | [workflow-cookbook/CHECKLISTS.md](../../workflow-cookbook/CHECKLISTS.md) / [workflow-cookbook/scripts/run_ci_tests.py](../../workflow-cookbook/scripts/run_ci_tests.py) | CI のゲート条件を共通化し、Katamari 承認ルールを遵守 |
| ガバナンス・優先度管理 | `governance/` | [docs/ROADMAP_AND_SPECS.md](../ROADMAP_AND_SPECS.md) | [workflow-cookbook/governance/policy.yaml](../../workflow-cookbook/governance/policy.yaml) / [workflow-cookbook/governance/prioritization.yaml](../../workflow-cookbook/governance/prioritization.yaml) / [workflow-cookbook/HUB.codex.md](../../workflow-cookbook/HUB.codex.md) | 優先順位と承認フローをここから決定 |

## ロードマップ（優先タスク順）

1. **ドキュメント整備フェーズ**: 上位索引とモジュール対応表を毎スプリント冒頭に見直し、Katamari ガバナンス（[workflow-cookbook/GUARDRAILS.md](../../workflow-cookbook/GUARDRAILS.md)）の合意事項を記録。
2. **CI / 自動化強化フェーズ**: `tools/` と `scripts/` を点検し、workflow-cookbook の [CHECKLISTS.md](../../workflow-cookbook/CHECKLISTS.md) と整合する mypy/ruff/pytest/node:test ゲートを自動化。本ページの「自動化・CI パイプライン」行に差分を反映。
3. **実装フェーズ**: 要求→設計→運用メモの順でトレーサビリティを確認しつつ、定義済みの Definition of Done を [RUNBOOK.md](../../workflow-cookbook/RUNBOOK.md) と [EVALUATION.md](../../workflow-cookbook/EVALUATION.md) に反映。
4. **リリース準備フェーズ**: リリースチェックリストと RUNBOOK をレビューし、Katamari の進行指針を [governance/policy.yaml](../../workflow-cookbook/governance/policy.yaml) に沿って承認記録へ残す。

### 更新手順

- 各フェーズ完了時に関連ドキュメントを更新し、Katamari 進行指針の基準となる [workflow-cookbook/CHANGELOG.md](../../workflow-cookbook/CHANGELOG.md) に差分を追記する。
- 変更は PR 説明欄にリンク付きで記載し、レビュワーは workflow-cookbook 側の対応資料が同期しているか確認する。
- 不整合が見つかった場合は Issue を起票し、優先タスク一覧の先頭に追加する。

## 参照クイックリンク

- [Katamari ガードレール](../../workflow-cookbook/GUARDRAILS.md)
- [運用 RUNBOOK](../../workflow-cookbook/RUNBOOK.md)
- [品質チェックリスト](../../workflow-cookbook/CHECKLISTS.md)
- [Day8 コントリビューションガイド](day8/guides/07_contributing.md)
- [ガバナンス方針](../../workflow-cookbook/governance/policy.yaml)

## ライセンス

- Day8 リポジトリ: [LICENSE](../LICENSE)
- workflow-cookbook: [workflow-cookbook/LICENSE](../../workflow-cookbook/LICENSE)

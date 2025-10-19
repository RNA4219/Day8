# Day8 ROADMAP & SPECS ハブ

Day8 リポジトリ内の仕様・設計・運用・実装ロードマップを集約するハブです。Day8 専用インデックス（`docs/README.md`）と並び、**横断的なロードマップとワークフロー資料の参照起点**として利用してください。

## 索引

### Day8 ドキュメント群
- [Day8 Docs 総覧](docs/day8/README.md) — Day8 の目的とディレクトリ構成。
- [要件（Requirements）](docs/day8/spec/01_requirements.md) — Day8 の機能・非機能要件。
- [仕様詳細（Spec）](docs/day8/spec/02_spec.md) — モジュール別仕様とワークフロー。
- [アーキテクチャ](docs/day8/design/03_architecture.md) — コンポーネント分解とデータフロー。
- [運用ガイド](docs/day8/ops/04_ops.md) — ディレクトリ管理・導入手順・CI 運用。
- [セキュリティ指針](docs/day8/security/05_security.md) — セーフティ/ガバナンス方針。
- [品質評価](docs/day8/quality/06_quality.md) — メトリクス、SLO、評価基準。
- [貢献ガイド](docs/day8/guides/07_contributing.md) — コントリビューションと Task Seeds 運用。
- [サンプル集](docs/day8/examples/10_examples.md) — 反省 DSL とガバナンスサンプル。

### workflow-cookbook リファレンス
- [BLUEPRINT](workflow-cookbook/BLUEPRINT.md) — 入出力インタフェース定義と前提条件。
- [RUNBOOK](workflow-cookbook/RUNBOOK.md) — 準備→実行→確認の最短手順。
- [EVALUATION](workflow-cookbook/EVALUATION.md) — 受入基準と検証項目。
- [GUARDRAILS](workflow-cookbook/GUARDRAILS.md) — 行動指針と変更時の遵守事項。
- [TASK Seed Catalog](workflow-cookbook/TASK.codex.md) — 自動タスク化ポリシーと命名規則。

## 実装ディレクトリ対応表

| 実装レイヤ/ディレクトリ | 主担当ドキュメント | 役割と補足 |
| --- | --- | --- |
| `docs/day8/spec/` | `docs/day8/spec/01_requirements.md`, `docs/day8/spec/02_spec.md` | 仕様・要件の一次ソース。Workflow 定義や CI 連携要件を記載。|
| `docs/day8/design/` | `docs/day8/design/03_architecture.md` | アーキテクチャ図と依存関係。実装の分割指針。|
| `docs/day8/ops/` | `docs/day8/ops/04_ops.md` | ディレクトリ運用、導入/CI 実務。|
| `docs/day8/security/` | `docs/day8/security/05_security.md` | セーフティ/ガバナンス設定の統括。|
| `docs/day8/quality/` | `docs/day8/quality/06_quality.md` | 観測/評価メトリクス、SLO、レポート形式。|
| `docs/day8/guides/` & `docs/day8/examples/` | `docs/day8/guides/07_contributing.md`, `docs/day8/examples/10_examples.md` | 貢献手順とサンプル DSL。Task Seeds とガイドライン。|
| `workflow-cookbook/` ルート | `workflow-cookbook/BLUEPRINT.md`, `workflow-cookbook/EVALUATION.md`, `workflow-cookbook/RUNBOOK.md` | 実装フェーズ別の作業指針。要求と検証の契約書。
| `workflow-cookbook/GUARDRAILS.md` | 同左 | 行動指針・例外規約。CI/LLM 連携時の守るべきルール。|
| `workflow-cookbook/TASK.codex.md` | 同左 | タスク分割と配布規約。Task Seed の命名・配布フロー。|

## ロードマップ

1. **仕様整合フェーズ** — `docs/day8/spec/*.md` と `workflow-cookbook/BLUEPRINT.md` を照合し、入出力契約と依存リストを最新化。
2. **運用/セーフティ統合フェーズ** — `docs/day8/ops/04_ops.md` と `docs/day8/security/05_security.md` を参照しながら、CI 上の運用設計とセーフティ制御を更新。必要に応じ `workflow-cookbook/RUNBOOK.md` へ反映。
3. **品質評価フェーズ** — `docs/day8/quality/06_quality.md` のメトリクス定義に基づき、`workflow-cookbook/EVALUATION.md` の受入基準を強化。評価手順の差分は `docs/ROADMAP_AND_SPECS.md` の本セクションへ追記。
4. **ガバナンス・タスク配布フェーズ** — Guardrails 更新と Task Seed 発行を同期。`workflow-cookbook/GUARDRAILS.md` と `workflow-cookbook/TASK.codex.md` をクロスレビューし、変更後は当ハブと `docs/README.md` のリンク優先度を確認。

## Guardrails 更新フロー

1. **変更要件の収集** — `docs/day8/spec/` および本ハブのロードマップ記録から更新背景を整理する。必要なら `docs/day8/guides/07_contributing.md` でプロセス影響を確認。
2. **ドラフト作成** — `workflow-cookbook/GUARDRAILS.md` へドラフトを作成。関連する入出力契約 (`workflow-cookbook/BLUEPRINT.md`) と評価条件 (`workflow-cookbook/EVALUATION.md`) を並行確認し、矛盾を排除。
3. **ハブ同期** — Guardrails 変更後は本ハブの「Guardrails 更新フロー」と「ロードマップ」を必要に応じ更新し、参照リンクを揃える。
4. **RUNBOOK / TASK Seed 反映** — 運用手順に影響する場合は `workflow-cookbook/RUNBOOK.md` を更新し、タスク配布要件は `workflow-cookbook/TASK.codex.md` に追記。最新状態を `docs/README.md` のリンク優先順位に沿って案内する。
5. **レビューと告知** — 更新内容を Day8 コア資料 (`docs/day8/README.md`) の更新履歴で告知し、CHANGELOG/Task Seed へ展開。レビュー完了後、`workflow-cookbook/GUARDRAILS.md` のメタ情報（レビュー日など）を更新する。

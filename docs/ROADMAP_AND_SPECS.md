# Day8 ロードマップ & 仕様メモ

プロジェクト全体の現在地と次の一手を素早く把握するためのガイドです。既存ドキュメントの骨格を保ちつつ、各資料の読みどころを短くまとめました。迷ったときはここから辿れば、必要な一次資料に直接到達できます。

## 1. 上位ドキュメント索引

| 種別 | 主な用途 | Day8 リポジトリ | workflow-cookbook | 備考 |
| --- | --- | --- | --- | --- |
| 要求 | ユーザー課題の把握とスコープ設定 | [docs/day8/spec/01_requirements.md](day8/spec/01_requirements.md) | [workflow-cookbook/BLUEPRINT.md](../../workflow-cookbook/BLUEPRINT.md) | Katamari 側のブループリントとペアで更新 |
| 仕様 | 画面・ユースケースの確定版 | [docs/day8/spec/02_spec.md](day8/spec/02_spec.md) | [workflow-cookbook/HUB.codex.md](../../workflow-cookbook/HUB.codex.md) | HUB の自動タスク分解と整合させる |
| 設計 | アーキテクチャと責務分担 | [docs/day8/design/03_architecture.md](day8/design/03_architecture.md) | [workflow-cookbook/GUARDRAILS.md](../../workflow-cookbook/GUARDRAILS.md) | 設計判断を Guardrails の原則に沿って記録 |
| 運用・品質 | リリース手順と品質ゲート | [docs/day8/ops/04_ops.md](day8/ops/04_ops.md) / [docs/day8/quality/06_quality.md](day8/quality/06_quality.md) | [workflow-cookbook/RUNBOOK.md](../../workflow-cookbook/RUNBOOK.md) / [workflow-cookbook/CHECKLISTS.md](../../workflow-cookbook/CHECKLISTS.md) / [workflow-cookbook/EVALUATION.md](../../workflow-cookbook/EVALUATION.md) | 承認フローと計測指標を同期 |
| セキュリティ | 脅威モデリングと権限設計 | [docs/day8/security/05_security.md](day8/security/05_security.md) | [workflow-cookbook/SECURITY.md](../../workflow-cookbook/SECURITY.md) | 例外運用は SECURITY.md に従ってエスカレーション |
| 安全性レビュー | 倫理・安全配慮の基準 | [docs/safety.md](safety.md) | [workflow-cookbook/SAFETY.md](../../workflow-cookbook/SAFETY.md) | Day8 特有の追加ガードを明記 |
| ガバナンス | 優先度・承認ルール | [governance/policy.yaml](../governance/policy.yaml) | [workflow-cookbook/governance/policy.yaml](../../workflow-cookbook/governance/policy.yaml) / [workflow-cookbook/governance/prioritization.yaml](../../workflow-cookbook/governance/prioritization.yaml) | Katamari ガバナンスに倣い意思決定を記録 |

## 2. 実装モジュールと対応仕様

| 領域 | Day8 側の主要ディレクトリ | 参照すべき仕様/設計 | workflow-cookbook の対応資料 | 補足 |
| --- | --- | --- | --- | --- |
| 要求・仕様トレーサビリティ | `docs/day8/spec/` / `docs/day8/design/` | [docs/day8/spec/01_requirements.md](day8/spec/01_requirements.md) / [docs/day8/spec/02_spec.md](day8/spec/02_spec.md) / [docs/day8/design/03_architecture.md](day8/design/03_architecture.md) | [workflow-cookbook/BLUEPRINT.md](../../workflow-cookbook/BLUEPRINT.md) / [workflow-cookbook/GUARDRAILS.md](../../workflow-cookbook/GUARDRAILS.md) | スプリント冒頭に差分確認 |
| オペレーション & QA | `docs/day8/ops/` / `docs/day8/quality/` | [docs/day8/ops/04_ops.md](day8/ops/04_ops.md) / [docs/day8/quality/06_quality.md](day8/quality/06_quality.md) | [workflow-cookbook/RUNBOOK.md](../../workflow-cookbook/RUNBOOK.md) / [workflow-cookbook/CHECKLISTS.md](../../workflow-cookbook/CHECKLISTS.md) / [workflow-cookbook/EVALUATION.md](../../workflow-cookbook/EVALUATION.md) | CI・運用承認の判断基準を同期 |
| セキュリティ & レジリエンス | `docs/day8/security/` / `docs/birdseye/` / `docs/safety.md` | [docs/day8/security/05_security.md](day8/security/05_security.md) / [docs/safety.md](safety.md) | [workflow-cookbook/SECURITY.md](../../workflow-cookbook/SECURITY.md) / [workflow-cookbook/SAFETY.md](../../workflow-cookbook/SAFETY.md) | 監査ログと例外手続きの窓口を共有 |
| 自動化・CI パイプライン | `tools/` / `scripts/` | [docs/day8/quality/06_quality.md](day8/quality/06_quality.md) / [docs/day8/examples/10_examples.md](day8/examples/10_examples.md) | [workflow-cookbook/scripts/run_ci_tests.py](../../workflow-cookbook/scripts/run_ci_tests.py) / [workflow-cookbook/CHECKLISTS.md](../../workflow-cookbook/CHECKLISTS.md) | mypy/ruff/pytest/node:test のゲート維持 |
| ガバナンス・優先度管理 | `governance/` / `docs/ROADMAP_AND_SPECS.md` | [governance/policy.yaml](../governance/policy.yaml) / 本ページ | [workflow-cookbook/governance/policy.yaml](../../workflow-cookbook/governance/policy.yaml) / [workflow-cookbook/governance/prioritization.yaml](../../workflow-cookbook/governance/prioritization.yaml) / [workflow-cookbook/HUB.codex.md](../../workflow-cookbook/HUB.codex.md) | Katamari 承認フローを Day8 に反映 |

## 3. ロードマップ

1. **索引・基準整備** — 本ページと [docs/day8/spec](day8/spec/) を照合し、Katamari 版の索引（[workflow-cookbook/HUB.codex.md](../../workflow-cookbook/HUB.codex.md)）との差異を毎スプリントで解消。差分は [docs/birdseye/index.json](birdseye/index.json) にも反映する。
2. **自動化ゲートの維持** — `tools/` / `scripts/` の CI エントリポイントを見直し、[workflow-cookbook/scripts/run_ci_tests.py](../../workflow-cookbook/scripts/run_ci_tests.py) で実行される mypy / ruff / pytest / node:test の整合を保証。チェックリスト更新時は [docs/day8/quality/06_quality.md](day8/quality/06_quality.md) を同時改訂する。
3. **実装・検証のアップデート** — [docs/day8/design/03_architecture.md](day8/design/03_architecture.md) に基づき実装やテストの差分をまとめ、[docs/day8/examples/10_examples.md](day8/examples/10_examples.md)・[docs/day8/guides/07_contributing.md](day8/guides/07_contributing.md) を更新。Katamari の [workflow-cookbook/CHANGELOG.md](../../workflow-cookbook/CHANGELOG.md) に成果を同期する。
4. **リリース・承認フロー** — フェーズ完了ごとに [docs/day8/ops/04_ops.md](day8/ops/04_ops.md) と [workflow-cookbook/RUNBOOK.md](../../workflow-cookbook/RUNBOOK.md) を突き合わせ、[workflow-cookbook/governance/policy.yaml](../../workflow-cookbook/governance/policy.yaml) の承認記録を更新。例外は [docs/safety.md](safety.md) の安全審査に連携。

### 更新手順

- **BLUEPRINT** — `workflow-cookbook/BLUEPRINT.md` と Day8 側の [docs/day8/spec/01_requirements.md](day8/spec/01_requirements.md) / [docs/day8/spec/02_spec.md](day8/spec/02_spec.md) を突き合わせ、スコープ・制約・Guardrails 原則（[workflow-cookbook/GUARDRAILS.md](../../workflow-cookbook/GUARDRAILS.md)）のズレがないかを確認する。
- **RUNBOOK / CHECKLISTS** — `workflow-cookbook/RUNBOOK.md`・`workflow-cookbook/CHECKLISTS.md` と [docs/day8/ops/04_ops.md](day8/ops/04_ops.md) / [docs/day8/quality/06_quality.md](day8/quality/06_quality.md) を同期し、運用フロー・ゲート条件・例外経路の改訂差分を洗い出す。
- **EVALUATION** — `workflow-cookbook/EVALUATION.md` と [docs/day8/quality/06_quality.md](day8/quality/06_quality.md) の指標・計測方法を比較し、CI 計測およびレビュー判定の最新化を反映させる。
- **TASK** — `workflow-cookbook/TASK.codex.md` と [workflow-cookbook/HUB.codex.md](../../workflow-cookbook/HUB.codex.md) を基に、必要なタスク分解と割当を整理し、Day8 側のロードマップ差分に紐づく Issue / チェックリスト項目を更新する。
- **Birdseye / ADR** — [docs/birdseye/index.json](birdseye/index.json) と [docs/day8/design/03_architecture.md](day8/design/03_architecture.md) を更新し、可視化ビューと設計判断（ADR 相当）の反映を確認した上で [workflow-cookbook/CHANGELOG.md](../../workflow-cookbook/CHANGELOG.md) に記録する。

> 更新完了後は、本 ROADMAP と関連 Guardrails（`workflow-cookbook/GUARDRAILS.md` など）の差分を同一 PR でまとめて同期すること。

## 4. 参照クイックリンク

- [Katamari ガードレール](../../workflow-cookbook/GUARDRAILS.md)
- [運用 RUNBOOK](../../workflow-cookbook/RUNBOOK.md)
- [品質チェックリスト](../../workflow-cookbook/CHECKLISTS.md)
- [Day8 コントリビューションガイド](day8/guides/07_contributing.md)
- [安全性レビュー基準](safety.md)
- [ガバナンス方針](../../workflow-cookbook/governance/policy.yaml)

## ライセンス

- Day8 リポジトリ: [LICENSE](../LICENSE)
- workflow-cookbook: [workflow-cookbook/LICENSE](../../workflow-cookbook/LICENSE)

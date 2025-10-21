# Day8 Architecture Decision Records

Day8 の設計判断を追跡するための ADR 集約ディレクトリです。Collector / Analyzer / Reporter などの主要コンポーネントについて、Katamari で策定された方針を Day8 に適合させた記録を配置します。

## 目次

| ID | タイトル | ステータス | 概要 |
| --- | --- | --- | --- |
| [0000](0000-template.md) | ADR テンプレート | Draft | 新規 ADR を作成する際の雛形。判断項目とレビュー手順を統一します。 |
| [0001](0001-collector-analyzer-reporter-pipeline.md) | Collector/Analyzer/Reporter の 3 層パイプライン | Accepted | Day8 におけるログ収集→解析→レポート生成の責務分離と依存経路を定義します。 |
| [0002](0002-jsonl-event-contract.md) | JSONL イベント契約と Analyzer 連携 | Accepted | Collector が出力する JSONL 形式と Analyzer への受け渡し契約、失敗時のフォールバックを規定します。 |
| [0003](0003-propose-only-governance.md) | Propose-only 運用と Governance 境界 | Accepted | レポート/提案の自動化が Git の変更権限を持たない運用制約と、ガバナンス文書との連携を定義します。 |
| [0004](0004-provider-interface.md) | Provider SPI と Adapter 層の統一 | Accepted | `provider_spi` を通じて外部 Provider を抽象化し、[Appendix F](../addenda/F_Provider_Matrix.md) / [Appendix L](../addenda/L_Config_Reference.md) と連携して資格情報とフォールバック順序を固定します。 |
| [0005](0005-reflection-manifest.md) | Reflection Manifest とデフォルト挙動の固定 | Accepted | `workflow-cookbook/reflection.yaml` を単一の真実源とし、Why-Why/Issue 提案の既定値と Birdseye 同期手順を明文化します。 |
| [0006](0006-evaluator-gates.md) | Evaluator ゲートとハイブリッド評価ライン | Accepted | BERTScore / ROUGE / ルール判定の閾値と `metrics.json` の構造を固定し、[Appendix E](../addenda/E_Evaluator_Details.md)・[docs/day8/quality/06_quality.md](../day8/quality/06_quality.md) と同期します。 |
| [0007](0007-proposal-priority-handshake.md) | 提案生成と Priority Score ハンドシェイク | Accepted | Analyzer/Proposer が生成する Issue/Task Seed に Priority Score を必須化し、[docs/TASKS.md](../TASKS.md) とガバナンスポリシーの整合を保証します。 |

## メンテナンス方針

- 新規 ADR は `000X-title.md` 形式で追加し、本 README の目次に追記します。
- Birdseye (`docs/birdseye/index.json` と `docs/birdseye/caps/docs.adr.*.json`) を同一コミットで更新し、`generated_at` を揃えます。
- 既存 ADR を改訂した場合は、関連ドキュメント (`docs/day8/design/03_architecture.md` や `workflow-cookbook/GUARDRAILS.md` 等) の参照を見直します。

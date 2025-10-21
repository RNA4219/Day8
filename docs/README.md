# Day8 ドキュメント索引

Day8 の仕様・設計・運用資料を一覧化した索引用ページです。必要なトピックへ素早くアクセスするための起点として利用してください。

## ハブドキュメント
- [Day8 ROADMAP & SPECS ハブ](ROADMAP_AND_SPECS.md) — Guardrails や workflow-cookbook との横断整合を確認する際の起点。
  - 参照優先度: 横断計画・ロードマップの確認は本ハブ→本索引の順、Day8 専用ディレクトリの詳細閲覧は本索引を優先。

## Day8 コア資料
- [Day8 Docs 総覧](day8/README.md) — サブディレクトリ構成とドキュメント群の概要。

## 仕様・設計
- [要件（Requirements）](day8/spec/01_requirements.md) — Day8 の機能要件と非機能要件。
- [仕様詳細（Spec）](day8/spec/02_spec.md) — ワークフローとコンポーネントの具体的な仕様。
- [アーキテクチャ](day8/design/03_architecture.md) — システム構成とアーキテクチャガイドライン。
  - ASCII フォールバック: [Day8 Architecture ASCII Map](Architecture_ASCII.md) — Mermaid が読めない環境で Collector/Analyzer/Reporter/Proposer/Governance の流れを再確認するときに利用。

## 運用・セキュリティ・品質
- [運用ガイド](day8/ops/04_ops.md) — 導入・運用フローとサブディレクトリ管理手順。
- [Day8 デプロイ付録（Appendix H）](addenda/H_Deploy_Guide.md) — ローカル検証、Docker 化、GitHub Actions リリースの要点をまとめた導入補助資料。
- [Day8 設定リファレンス（Appendix L）](addenda/L_Config_Reference.md) — 環境変数・設定ファイル・デバッグフラグを網羅し、導入前チェックリストとして活用できる設定付録。
- [セキュリティ指針](day8/security/05_security.md) — セキュリティ/ガバナンスポリシーと対応方針。Appendix G と連携し、Secrets/Rate limit/OAuth のチェックリストを提供。
- [品質評価](day8/quality/06_quality.md) — メトリクス、SLO、評価プロセス。

## Upstream 運用
- [Day8 Upstream 運用ガイド](UPSTREAM.md) — Katamari ワークフロー資産との同期手順と週次チェックの基準。
- [Day8 Upstream 週次ログ テンプレート](UPSTREAM_WEEKLY_LOG.md) — 週次レビュー用の記録テンプレート。

## 貢献・サンプル
- [貢献ガイド](day8/guides/07_contributing.md) — 貢献手順とタスク運用ルール。
- [サンプル集](day8/examples/10_examples.md) — 反省 DSL やガバナンス設定のサンプル。

## セーフティ関連
- [安全性ドキュメント](safety.md) — `workflow-cookbook/SAFETY.md` をハブとし、フェイルセーフ/例外/Hot 更新手順を整理。
- [セキュリティ & プライバシー付録（Appendix G）](addenda/G_Security_Privacy.md) — キー管理・ログ衛生・データ保持・通信保護・OAuth ガードの運用ノート。

## 付録
- [Day8 用語集](addenda/A_Glossary.md) — ドキュメントレビューや新規タスク着手前に、Collector/Analyzer などの用語を素早く再確認するための参照先。

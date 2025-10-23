# Day8 ドキュメント索引

Day8 の仕様・設計・運用資料を一覧化した索引用ページです。必要なトピックへ素早くアクセスするための起点として利用してください。

## ハブドキュメント
- [Day8 ROADMAP & SPECS ハブ](ROADMAP_AND_SPECS.md) — Day8 のガバナンス・ワークフロー資料を横断して整合確認する際の起点。補足: 旧 Guardrails / workflow-cookbook 起源の手順が必要な場合は本ハブ内の注記を参照。
  - 参照優先度: 横断計画・ロードマップの確認は本ハブ→本索引の順、Day8 専用ディレクトリの詳細閲覧は本索引を優先。
- [Day8 マイルストーン WBS](day8_wbs.csv) — マイルストーン別の作業分解を可視化し、スプリント計画やレビューでロードマップと整合を取る際のチェックリストとして利用。

## Day8 コア資料
- [Day8 Docs 総覧](day8/README.md) — サブディレクトリ構成とドキュメント群の概要。

## Architecture Decision Records (ADR)
- [ADR 目次](adr/README.md) — Collector / Analyzer / Reporter の設計判断や propose-only 運用方針を整理した記録。
- [ADR 0001: Collector/Analyzer/Reporter の 3 層パイプライン](adr/0001-collector-analyzer-reporter-pipeline.md)
- [ADR 0002: JSONL イベント契約と Analyzer 連携](adr/0002-jsonl-event-contract.md)
- [ADR 0003: Propose-only 運用と Governance 境界](adr/0003-propose-only-governance.md)

## 仕様・設計
- [要件（Requirements）](day8/spec/01_requirements.md) — Day8 章立てに沿って固定事項/スコープ/ユースケース/FR/NFR/データモデル/受入基準/マイルストーンを整理し、Appendix G/J/K/M1 などの参照を束ねた要件ハブ。
- [仕様詳細（Spec）](day8/spec/02_spec.md) — ワークフローとコンポーネントの具体的な仕様。
- [アーキテクチャ](day8/design/03_architecture.md) — システム構成とアーキテクチャガイドライン。
  - ASCII フォールバック: [Day8 Architecture ASCII Map](Architecture_ASCII.md) — Mermaid が読めない環境で Collector/Analyzer/Reporter/Proposer/Governance の流れを再確認するときに利用。

## 運用・セキュリティ・品質
- [運用ガイド](day8/ops/04_ops.md) — 導入・運用フローとサブディレクトリ管理手順。
- [Day8 デプロイ付録（Appendix H）](addenda/H_Deploy_Guide.md) — ローカル検証、Docker 化、GitHub Actions リリースの要点をまとめた導入補助資料。
- [Day8 設定リファレンス（Appendix L）](addenda/L_Config_Reference.md) — 環境変数・設定ファイル・デバッグフラグを網羅し、導入前チェックリストとして活用できる設定付録。
- [Day8 設定テンプレート](../config/env.example) / [モデルレジストリ雛形](../config/model_registry.json) — Appendix L/F の要件を満たすサンプル構成。`.env` とプロバイダー定義を Day8 用語へ合わせて初期化するときに利用。
- [Day8 Release Checklist](Release_Checklist.md) — Day8 固有のリリースゲートとエビデンス整備を網羅した手順書。Collector/Analyzer/Reporter の各段階で必要な承認ログと Birdseye キャッシュ更新のタイミングを定義。
  - 付随資料: [Versioning & Release Operations（Appendix M）](addenda/M_Versioning_Release.md)、[Day8 デプロイ付録（Appendix H）](addenda/H_Deploy_Guide.md)。Day8 のタグ/バージョン管理と環境更新手順を Release Checklist のステップと連動させる。
  - フロー概要: Collector → Analyzer → Reporter → Birdseye 更新の順で Day8 Release Flow を駆動し、チェックリスト完了時にすべての監査ログと可視化を同期する。
  - 運用コマンド例: `python scripts/birdseye_refresh.py --docs-dir docs/birdseye --docs-dir workflow-cookbook/docs/birdseye`
- [Day8 セキュリティレビュー チェックリスト](Security_Review_Checklist.md) — Secrets/CORS/Rate limit/OAuth/依存性スキャンを PR 審査用に集約。実施結果は Appendix G と 05_security の詳細手順へ引き渡す。
- [Versioning & Release Operations（Appendix M）](addenda/M_Versioning_Release.md) — semver ラベル運用とタグ作成フロー、互換性レビューの基準を集約。
- [Day8 評価器構成（Appendix E）](addenda/E_Evaluator_Details.md) — BERTScore/ROUGE/ルール判定の設定と運用チェックリスト。
- [セキュリティ指針](day8/security/05_security.md) — セキュリティ/ガバナンスポリシーと対応方針。Appendix G と連携し、詳細な審査フローと例外承認手順を管理（速査は `Security_Review_Checklist.md` を参照）。
- [品質評価](day8/quality/06_quality.md) — メトリクス、SLO、評価プロセス。

## API 仕様・監視契約
- [Day8 Observability OpenAPI](openapi/day8_openapi.yaml) — `/healthz` と `/metrics` のコントラクトを確認し、Ops/Release のヘルスチェック検証前にレスポンス形式とヘッダ要件を整合させる。

## Upstream 運用
Day8 の upstream 取り込みは propose-only ガバナンスを前提に Day8 Release Flow と同じ証跡管理を維持する。Collector/Analyzer/Reporter への差分を週次で同期し、ロールバックや再適用も Day8 固有の運用基準に従って処理するための資料を下記に集約。
- [Day8 Fork Notes](FORK_NOTES.md) — 上流ブランチ取り込み時に必要な Day8 固有の追加コンポーネント・依存・ライセンス同梱ルールを整理し、差分適用時に確認すべき追加検証ポイントを列挙。
- [Day8 Upstream 運用ガイド](UPSTREAM.md) — Collector/Analyzer/Reporter のコード同期を週次で行うための運用ガードライン。Day8 のタグ基準と propose-only 運用ルールに合わせたマージ手順と巻き戻し手順を明記。
  - 週次手順: Upstream トラッキングブランチの再取り込み → Analyzer/Reporter の差分検証 → Release Checklist 該当ステップの再確認 → Birdseye キャッシュと週次ログの更新。
- [Day8 Upstream 週次ログ テンプレート](UPSTREAM_WEEKLY_LOG.md) — 週次レビュー用の記録テンプレート。

## 貢献・サンプル
- [貢献ガイド](day8/guides/07_contributing.md) — 貢献手順とタスク運用ルール。
- [サンプル集](day8/examples/10_examples.md) — 反省 DSL やガバナンス設定のサンプル。

## UI テーマ & ペルソナ
- [Day8 Personas & Themes ガイド](../README_PERSONAS_THEMES.md) — テーマ適用手順とペルソナ拡張 TODO、Appendix B/C/K の接続を整理。補足: Chainlit 向け設定は注記として整理。
- [Day8 Theme Catalog](../themes/CATALOG.md) — classic / mocha / highcontrast の配布パックと Appendix 連携要件。

## セーフティ関連
- [安全性ドキュメント](safety.md) — Day8 のフェイルセーフ/例外/Hot 更新手順を集約した安全性ハブ。補足: 旧 workflow-cookbook 由来の参考項目は注記で参照先を示す。
- [セキュリティ & プライバシー付録（Appendix G）](addenda/G_Security_Privacy.md) — キー管理・ログ衛生・データ保持・通信保護・OAuth ガードの運用ノート。

## 付録
- [Day8 用語集](addenda/A_Glossary.md) — ドキュメントレビューや新規タスク着手前に、Collector/Analyzer などの用語を素早く再確認するための参照先。
- [トリム設計付録（Appendix D）](addenda/D_Trim_Design.md) — Sliding Window / Semantic / Memory Hybrid の圧縮戦略と保持率指標を整理し、ログトリムの判断と Birdseye メタデータ整合の根拠を提供。
- [UI モック（Appendix B）](addenda/B_UI_Mock.md) — 画面共有できない環境で CLI/レポートの骨子をレビューし、Day8 の主要画面を擦り合わせるときに利用。
- [プロバイダーマトリクス（Appendix F）](addenda/F_Provider_Matrix.md) — モデル差分調査やフォールバック順序の確認時に、Day8 が許容するプロバイダー構成と運用ガードを参照。

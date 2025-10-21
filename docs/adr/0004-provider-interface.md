# ADR 0004: Provider SPI と Adapter 層の統一

- **ステータス**: Accepted
- **作成日**: 2025-11-06
- **レビュアー**: @governance, @quality-owner
- **関連チケット/タスク**: workflow-cookbook/reflection.yaml, docs/addenda/F_Provider_Matrix.md, docs/addenda/L_Config_Reference.md

## 背景
- Katamari では LLM/Embedding/Tool ごとに Provider Adapter を実装し、`provider_spi` でフェイルオーバーやメトリクス連携を統一していた。
- Day8 でも Reflection DSL から複数の Provider を切り替える必要があり、`workflow-cookbook/reflection.yaml` の `analysis.llm_model` や `actions` が Provider 差分に依存する。
- Appendix F（プロバイダーマトリクス）と Appendix L（設定リファレンス）で管理している資格情報や環境変数が ADR と結び付いておらず、運用時に参照元が分散していた。

## 決定
- Day8 の自動化で利用する外部 Provider は `provider_spi.ProviderAdapter` を実装し、`analyze.py` などの上位層は Adapter 経由でのみ呼び出す。
- Reflection DSL (`workflow-cookbook/reflection.yaml`) は Adapter 名と論理モデル ID を宣言し、Appendix F のフォールバック優先度と同期する。
- Provider ごとの接続情報は Appendix L に記載された環境変数のみを参照し、スクリプト内で追加の暗黙設定を持たない。
- フェイルオーバーとレートリミット処理は Adapter に閉じ込め、Analyzer/Reporter 側には成功/失敗とメトリクスのみを返す。

## 根拠
- Adapter 層を固定することで、Provider の追加・切り替えが Reflection DSL の宣言と Appendix F の更新だけで完結し、Day8 の propose-only 運用に適合する。
- Katamari で実績のある `provider_spi` 設計を踏襲することで、Telemetry やレート制御のテストを再利用できる。
- Appendix L の環境変数を単一の真実源とすることで、CI とローカルで同じ構成を再現しやすい。

## 影響
- 新しい Provider を導入する場合は `provider_spi` に Adapter を追加し、Appendix F/L と本 ADR を同一 PR で更新する必要がある。
- Analyzer/Reporter のテストでは Adapter をモックし、フォールバック順序や例外伝播が spec 02 の要件を満たしているか確認する。
- Birdseye index/caps に ADR 0004 を追加し、Provider 関連ドキュメントとの依存を明示する。

## フォローアップ
- [ ] `provider_spi` のサンプル Adapter 実装に Day8 用の docstring と型ヒントを追記する。
- [ ] Appendix F/L の更新手順に本 ADR へのリンクを追加する。

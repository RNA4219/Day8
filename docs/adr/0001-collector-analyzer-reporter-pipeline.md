# ADR 0001: Collector/Analyzer/Reporter の 3 層パイプライン

- **ステータス**: Accepted
- **作成日**: 2025-10-31
- **レビュアー**: @day8-core, @ops-lead
- **関連チケット/タスク**: docs/TASKS.md#architecture, workflow-cookbook/CHECKLISTS.md#release

## 背景
- Day8 の GitHub Actions（`test.yml` / `reflection.yml`）と workflow-cookbook スクリプトは、CI 実行ログを `workflow-cookbook/logs/` に集約し、Analyzer・Reporter で後続処理する構成を継続運用している。
- 2025 年のリリースレビューで、収集・解析・レポート生成を単一スクリプトに統合した検証では障害切り戻しが難しく、CI 停止時のトリアージが 2 倍以上に膨らんだことが Ops チームにより報告された（`docs/day8/ops/04_ops.md`）。
- `docs/day8/design/03_architecture.md` では Collector → Analyzer → Reporter → Proposer → Governance の流れを提示しているが、意思決定の根拠が散在しており Birdseye でのトレースが困難だった。

## 決定
1. **Collector**
   - CI や補助スクリプトからの JSONL ログを `workflow-cookbook/logs/` 配下へ集約し、スキーマは ADR 0002 で定義する契約に準拠する。
   - 取り込み時にエラーが発生した場合は再試行可能な一時失敗として扱い、Analyzer への入力を生成しない。
2. **Analyzer**
   - `workflow-cookbook/scripts/analyze.py` を単一エントリポイントとし、Collector から提供されたログを読み込み、メトリクスと Why-Why 草案を生成する。
   - 計算結果は中間成果物として `workflow-cookbook/reports/` へ書き出し、Reporter 以外の層から直接参照しない。
3. **Reporter**
   - Analyzer が吐き出したデータをもとに `reports/today.md` や `reports/issue_suggestions.md` を生成する。
   - Reporter は propose-only の制約を守り、自動コミットや push は行わない（詳細は ADR 0003）。
4. **観測性**
   - 3 層の境界は Birdseye (`docs/birdseye/index.json`) に Collector → Analyzer → Reporter → Proposer へのエッジとして登録し、`docs/day8/design/03_architecture.md` に図解する。

## 根拠
- Day8 Ops の障害記録では、Collector と Analyzer の処理を分離した運用に切り戻したことで、ログ欠損時の再投入が 1 ワークフロー単位で完結し、復旧時間が短縮された。
- Analyzer と Reporter を分けることで、`workflow-cookbook/scripts/analyze.py` の再実行だけでメトリクスを再計算でき、`reports/` 配下の生成は Reporter で安全に再試行できる。
- propose-only 制約下で Reporter がリポジトリを書き換えないよう、Birdseye から Collector/Analyzer/Reporter の境界を追跡する必要があり、本 ADR が依存関係の一次根拠となる。

## 影響
- `docs/day8/design/03_architecture.md` は本 ADR を根拠とする説明を追加する。
- `workflow-cookbook/GUARDRAILS.md` は 3 層境界と propose-only 制約を参照する。
- Birdseye index/caps に新しいノード (`docs/adr/0001-...`) を追加し、`generated_at` を同期させる。

## フォローアップ
- [ ] Analyzer の計算ロジックを追加実装する際、メトリクスの中間成果物スキーマを ADR で追記する。
- [ ] Reporter が扱うレポート種別が増えた場合、本 ADR の影響範囲を再評価する。

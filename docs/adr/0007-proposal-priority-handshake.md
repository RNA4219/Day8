# ADR 0007: 提案生成と Priority Score ハンドシェイク

- **ステータス**: Accepted
- **作成日**: 2025-11-06
- **レビュアー**: @governance, @quality-owner
- **関連チケット/タスク**: docs/TASKS.md, workflow-cookbook/governance/prioritization.yaml, workflow-cookbook/TASK.codex.md

## 背景
- Katamari では Analyzer/Proposer が提案する Issue や Draft PR に Priority Score を必ず付与し、ガバナンス審査と同期していた。
- Day8 の propose-only 運用でも Priority Score を基準にレビュー順序を決定しているが、自動生成される `reports/issue_suggestions.md` と Task Seed の整合ルールが ADR にまとめられていなかった。
- `docs/TASKS.md` や `workflow-cookbook/TASK.codex.md` では Priority Score 記法を要求しているものの、Analyzer が生成する提案にどのように埋め込むかが不明確だった。

## 決定
- Analyzer/Proposer が出力する Issue 下書きおよび Task Seed には `Priority Score: <number> / <justification>` を必須とし、`workflow-cookbook/governance/prioritization.yaml` の重み付けを参照して算出する。
- Priority Score の値と根拠は `reports/issue_suggestions.md` の各エントリ、および自動生成 Task Seed の `Deliverables` セクションへ同一形式で埋め込む。
- スコア計算に必要なメトリクス（pass_rate, duration_p95, flaky_rate）は `workflow-cookbook/scripts/analyze.py` が収集し、Proposal 生成時に参照できるよう JSON 出力へ含める。
- Priority Score テンプレートの変更や重み付けの更新が発生した場合は、本 ADR・`docs/TASKS.md`・`workflow-cookbook/TASK.codex.md` を同時に更新し、Birdseye の依存グラフを再生成する。

## 根拠
- Katamari の Priority Score ルールを Day8 でも統一することで、レビュー順序と提案の緊急度が自動的に整合し、手動補正が不要になる。
- Analyzer がメトリクスを同時に記録することで、Priority Score の根拠が明示され、ガバナンス審査のトレーサビリティが向上する。
- Task Seed と Issue 下書きが同じフォーマットを持つことで、提案内容を手動で移植する際のフォーマット崩れを防げる。

## 影響
- Proposal を生成するツールは Priority Score が欠落している場合に失敗扱いとし、CI のガバナンスゲートで検知する必要がある。
- Task Seed テンプレートを更新する際は本 ADR を参照し、Priority Score の形式や根拠フィールドを削除しない。
- Birdseye Hot リストに Priority Score ハンドシェイクのノードを追加し、レビュー直前に参照できるようにする。

## フォローアップ
- [ ] `workflow-cookbook/scripts/analyze.py` の Issue 生成ロジックに Priority Score 埋め込みテストを追加する。
- [ ] `docs/TASKS.md` のチェックリストへ ADR 0007 の参照を追記する。

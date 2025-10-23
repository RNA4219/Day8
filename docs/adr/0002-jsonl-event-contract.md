# ADR 0002: JSONL イベント契約と Analyzer 連携

- **ステータス**: Accepted
- **作成日**: 2025-10-31
- **レビュアー**: @collector-owner, @data-quality
- **関連チケット/タスク**: docs/TASKS.md#telemetry, workflow-cookbook/CHECKLISTS.md#quality

## 背景
- Day8 の Collector は GitHub Actions（`test`・`reflection`）と補助スクリプトからのログを `workflow-cookbook/logs/` に集約し、Analyzer がストリーム処理する前提で運用している。
- 2025 年の品質レビューで、ワークフローごとに JSON フィールドの揺れが発生し `workflow-cookbook/scripts/analyze.py` が例外停止、Reporter が成果物を生成できない事象が複数回確認された。
- `/healthz` と MetricsRegistry の値を整合させるには、ログ欠損やフィールド追加を Analyzer が即座に検知し、`docs/day8/ops/04_ops.md` の切り分け手順に沿って隔離できることが求められる。

## 決定
- Collector は以下の JSONL スキーマを必須とする：

  ```json
  {
    "ts": "ISO8601",          // イベント発生時刻 (UTC)
    "name": "pytest::suite",  // テストまたはタスクの識別子
    "status": "passed|failed|skipped|errored",
    "duration_ms": 1234,       // 実行時間 (ミリ秒)
    "payload": {               // 任意の追加情報（例: stderr サマリ、retry flag）
      "source": "gha|manual",
      "retryable": true
    }
  }
  ```

- 追加フィールドは `payload` にネストし、トップレベルの互換性を維持する。
- Analyzer はスキーマ検証を実行し、欠落フィールドがある行を隔離ログ（`workflow-cookbook/logs/invalid/`）へ退避した上で処理を継続する。
- Collector は JSONL 生成後に sha256 チェックサムを計算し、`workflow-cookbook/logs/.checksums` に記録する。Analyzer はチェックサムを検証し、破損を検知した場合は再処理を要求する。
- Reporter は Analyzer が生成した中間成果物に対してのみ依存し、生ログには触れない。

## 根拠
- JSONL を採用することで Analyzer が逐次読み込みを維持でき、Day8 の CI が生成する数万行規模のログでもメモリ使用量が安定する。
- `payload` ネストで拡張フィールドを隔離すれば、既存の Analyzer/Reporter テスト（`docs/day8/quality/06_quality.md` の最低メトリクス）を壊さずにメタデータを追加できる。
- チェックサム検証を行うことで、Ops が報告した I/O 障害や部分的なアップロード失敗を早期検知し、再取得リトライの判断が迅速になる。

## 影響
- Collector 実装は JSONL スキーマに準拠するためのバリデーションを組み込む必要がある。
- Analyzer と Reporter の実装は本スキーマを前提としてテストケースを更新する。
- `docs/day8/design/03_architecture.md` と `docs/day8/ops/04_ops.md` はログフローの説明に本 ADR をリンクする。
- Birdseye index/caps を更新し、Collector → Analyzer の依存が ADR 0002 に紐づくことを示す。

## フォローアップ
- [ ] JSON スキーマ定義を `workflow-cookbook/schemas/collector.json` として整備し、本 ADR から参照する。
- [ ] Analyzer のユニットテストに invalid ログの隔離パスを追加する。

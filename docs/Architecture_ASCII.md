# Day8 Architecture ASCII Map

Day8 の Collector / Analyzer / Reporter / Proposer / Governance 構成を素早く把握するための内部リファレンスです。Day8 チームが運用フローを確認する際に、テキストベースで全体像を共有できるよう ASCII 図で整理しています。

### 参照の進め方
1. まず本図で各コンポーネントの接続関係を把握する。
2. 詳細仕様が必要になった場合は後述の設計ドキュメントや索引へ遷移し、該当するセクションを確認する。
3. 差分レビュー時は Birdseye のリンクから対象コンポーネントを開き、本図と突き合わせて影響範囲を整理する。

```
+----------------+        +----------------+        +----------------+        +----------------+        +--------------------+
|    Collector   |  logs  |    Analyzer    | report |    Reporter    | draft  |    Proposer    | policy |     Governance     |
|----------------|------->|----------------|------->|----------------|------->|----------------|------->|--------------------|
| - CI テスト    |        | - analyze.py   |        | - reports/today|        | - Issue/PR提案 |        | - policy.yaml      |
| - JSONL ログ収集|       | - メトリクス算出|       | - Why-Why 草案  |        | - 自動改変なし |        | - SLO/制約         |
+----------------+        +----------------+        +----------------+        +----------------+        +--------------------+
        |                        |                        |                        |                          ^
        |                        |                        |                        |                          |
        |                        v                        v                        v                          |
        |                 +--------------+        +----------------+        +----------------+               |
        |                 | Metrics Store|        |  Review Inputs |        |   Governance    |---------------+
        |                 | (JSON/Markdown)       | (Markdown/Logs)|        |   Feedback Loop |
        +-----------------+--------------+--------+----------------+--------+----------------+
                          |                              ^
                          |                              |
                          +------------------------------+
                            (Birdseye / ROADMAP 索引)
```

## 主要フロー
1. **Collector** が GitHub Actions やローカル CI から JSONL ログを `workflow-cookbook/logs/` に収集する。
2. **Analyzer** (`workflow-cookbook/scripts/analyze.py`) がログを解析し、メトリクスと Why-Why 草案を生成して `reports/` 配下へ出力する。
3. **Reporter** がメトリクスと草案を Markdown レポート（`reports/today.md` など）へ整形し、Birdseye へリンク可能な形で保存する。
4. **Proposer** が Analyzer/Reporter の成果を参照しつつ Issue やドラフト PR の提案を作成するが、Day8 のルール上で自動改変は行わない。
5. **Governance** (`governance/policy.yaml`) が各ステップの行動制約・SLO を定義し、承認結果や再試行条件を更新する。必要なフィードバックは Reporter/Proposer に戻り、Birdseye からのナビゲーションで整合を確認する。

## 関連資料
- 詳細なコンポーネント説明: [docs/day8/design/03_architecture.md](day8/design/03_architecture.md)
- Birdseye 索引とノード定義: [docs/birdseye/index.json](birdseye/index.json)
- ロードマップ/参照手順: [docs/ROADMAP_AND_SPECS.md](ROADMAP_AND_SPECS.md)

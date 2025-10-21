# 仕様（Specification）

## ディレクトリ標準
- `.github/workflows/` : `test.yml`, `reflection.yml`（必要に応じ `pr_gate.yml`）
- `workflow-cookbook/`
  - `workflow-cookbook/reflection.yaml` （反省DSL）
  - `workflow-cookbook/scripts/analyze.py` （ログ→レポート）
  - `logs/` / `reports/` / `docs/`

## 反省DSL（例）
```yaml
# workflow-cookbook/reflection.yaml
targets:
  - name: unit
    logs: ["logs/test.jsonl"]
metrics: [pass_rate, duration_p95, flaky_rate]
analysis:
  engine: heuristic        # 将来: llm
  llm_model: gpt-4.1-mini  # デチューン時は使用しない
  max_tokens: 0
actions:
  suggest_issues: true
  open_pr_as_draft: false
  auto_fix: false
report:
  output: "reports/today.md"
  include_why_why: true
```

> モデル差分を調査・反映する際は [Appendix F: プロバイダーマトリクス](../../addenda/F_Provider_Matrix.md) を参照し、`llm_model` の切替やフォールバック順序、ガードレール更新をガバナンスに記録する。
>
> ログ圧縮や保持率の調整は [Appendix D: トリム設計](../../addenda/D_Trim_Design.md) に従い、`workflow-cookbook/scripts/analyze.py` の `--trim` オプションや `reflection.yaml` の保持設定を更新する前に保持率指標 (`retention_ratio` など) の SLO と整合させる。

## GitHub Actions（要点）
- `test.yml`: ログ生成→アーティファクト化
- `reflection.yml`: `workflow_run` で `test` 連動。ログを解析してレポートコミット、必要なら Issue 草案起票。
- サブディレクトリ対応: `defaults.run.working-directory: workflow-cookbook`

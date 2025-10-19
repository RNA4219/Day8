# サンプル

## test.yml（サブディレクトリ対応）
```yaml
name: test
on:
  push:
    branches: ["**"]
  pull_request:
defaults:
  run:
    working-directory: workflow-cookbook
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests (dummy)
        run: |
          mkdir -p logs
          echo '{"name":"ok","status":"pass","duration_ms":120}' >> logs/test.jsonl
          echo '{"name":"ng","status":"fail","duration_ms":900}' >> logs/test.jsonl
      - name: Upload logs
        uses: actions/upload-artifact@v4
        with:
          name: test-logs
          path: workflow-cookbook/logs
```

## reflection.yml（連動）
```yaml
name: reflection
on:
  workflow_run:
    workflows: ["test"]
    types: [completed]
defaults:
  run:
    working-directory: workflow-cookbook
jobs:
  reflect:
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: write
      issues: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: test-logs
          run-id: ${{ github.event.workflow_run.id }}
          path: workflow-cookbook

      # アーティファクト取得には permissions.actions: read が必要です。
      # 別リポジトリや手動指定の run を参照する場合は、下記のように repository/run-id/github-token を明示しないと
      # "Artifact not found" エラーになります。ダウンロードには permissions.actions: read が必須で、github-token には
      # actions: read を付与した PAT を渡してください。
      #- uses: actions/download-artifact@v4.1.7
      #  with:
      #    repository: owner/repo
      #    run-id: 1234567890
      #    name: test-logs
      #    path: workflow-cookbook
      #    github-token: ${{ secrets.CROSS_REPO_PAT }}
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Analyze logs → report
        run: |
          python scripts/analyze.py
      - name: Determine reflection outputs
        id: reflection-paths
        run: |
          REPORT_PATH="reports/today.md"
          ISSUE_RELATIVE_PATH="reports/issue_suggestions.md"
          ISSUE_CONTENT_PATH="workflow-cookbook/${ISSUE_RELATIVE_PATH}"
          ISSUE_HASH_PATH="$ISSUE_CONTENT_PATH"
          echo "report-path=$REPORT_PATH" >> "$GITHUB_OUTPUT"
          echo "issue-content-path=$ISSUE_CONTENT_PATH" >> "$GITHUB_OUTPUT"
          echo "issue-hash-path=$ISSUE_HASH_PATH" >> "$GITHUB_OUTPUT"
          echo "ISSUE_CONTENT_PATH=$ISSUE_CONTENT_PATH" >> "$GITHUB_ENV"
          echo "ISSUE_HASH_PATH=$ISSUE_HASH_PATH" >> "$GITHUB_ENV"
          git config user.name "reflect-bot"
          git config user.email "bot@example.com"
          git add "$REPORT_PATH"
          git commit -m "chore(report): reflection report [skip ci]" || echo "no changes"
          git push || true
      - name: Open issue if needed
        if: ${{ hashFiles(format('{0}', steps.reflection-paths.outputs.issue-hash-path)) != '0' }}
        uses: peter-evans/create-issue-from-file@v5
        with:
          title: "反省TODO ${{ github.run_id }}"
          content-filepath: ${{ steps.reflection-paths.outputs.issue-content-path }}
          labels: reflection, needs-triage
```

> `defaults.run.working-directory` で `workflow-cookbook` を指定しているため、アーティファクトは `path: workflow-cookbook` でリポジトリルート直下に展開され、スクリプトは `python scripts/analyze.py` として呼び出します。
> 同じ理由でレポート生成後の処理も `workflow-cookbook/` を基準に行い、`Determine reflection outputs` ステップで `REPORT_PATH` や `ISSUE_RELATIVE_PATH` を算出します。
> ステップ内では、算出したパスを `$GITHUB_OUTPUT` / `$GITHUB_ENV` へ書き出し、`git add "$REPORT_PATH"` のように変数からステージング先を決定しています。
> `Open issue if needed` でも `steps.reflection-paths.outputs.issue-content-path` などの出力を再利用し、`hashFiles(format('{0}', ...))` の評価結果に応じて Issue 起票を行います。

## analyze.py（骨子）
- JSONLを読み、合格率・p95・失敗数を算出
- Why-Why 草案と Issue 候補を出力

# ADR 0005: Reflection Manifest とデフォルト挙動の固定

- **ステータス**: Accepted
- **作成日**: 2025-11-06
- **レビュアー**: @quality-owner, @ops-lead
- **関連チケット/タスク**: workflow-cookbook/reflection.yaml, workflow-cookbook/scripts/analyze.py, docs/addenda/L_Config_Reference.md

## 背景
- Day8 の Reflection DSL は `workflow-cookbook/reflection.yaml` を真実源として運用し、Collector/Analyzer/Reporter の挙動を設定ファイルで切り替えている。
- スクリプトが YAML 読み込みに失敗した際のフォールバックや Why-Why 生成の既定値が明文化されておらず、CI での復旧手順がレビューごとに変動していた。
- Appendix L（設定リファレンス）や spec 02 の記述に反映されていない運用ルール（`suggest_issues` の既定値など）が存在し、レビュー時に判定が揺れていた。

## 決定
- `workflow-cookbook/reflection.yaml` を Day8 の Reflection Manifest と定義し、Analyzer/Reporter/Proposer の挙動は Manifest を介してのみ変更する。
- Manifest を読み込めない場合は `analyze.py` のフォールバックロジックで `suggest_issues=true`、`report.include_why_why=true`、`targets[0].logs="logs/test.jsonl"` を採用し、CI で常に同じ既定値になるよう固定する。
- Manifest の更新は Appendix L のチェックリストに追加し、Birdseye index/caps/hot の `generated_at` と同時に同期する。
- Why-Why 出力と Issue 提案の有効化は Manifest による制御を優先し、コマンドライン引数から上書きしない。

## 根拠
- Manifest を一次情報と定義すると、CI とローカルで同じ設定が適用され、再現検証の際に差分を排除できる。
- フォールバック既定値を固定することで、YAML パース失敗時でもレポート/提案が欠落せず、Day8 Ops のトリアージが容易になる。
- Why-Why や Issue 提案の有効化条件を Manifest へ集中させることで、ガードレールや propose-only ポリシーと矛盾しない。

## 影響
- Reflection 設定を変更する PR では Manifest と Appendix L の両方を更新し、Birdseye の依存グラフを再生成する必要がある。
- Analyzer のテストケースは Manifest フォールバックを検証し、`suggest_issues` と `include_why_why` の既定値が変化しないことを保証する。
- 既存の CLI オプションで Manifest の値を上書きしていた場合は非推奨とし、今後のバージョンで削除する計画を追記する。

## フォローアップ
- [ ] Appendix L の Reflection Manifest セクションに既定値と本 ADR のリンクを記載する。
- [ ] Manifest 更新手順を Release Checklist の「Birdseye 反映」ステップへ組み込む。

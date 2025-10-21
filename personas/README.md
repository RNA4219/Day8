# Day8 Personas Index

Day8 で運用する代表的なロール視点を YAML で管理するハブ。`docs/addenda/C_Persona_Schema.md` のスキーマに沿って作成した各ペルソナを Task Seed 起票や評価指標レビューの初動で選択し、ハンドオフ条件とエスカレーションを明示する。

## 利用タイミング
- Task Seed 起票時に、対象ロールの YAML を参照して `insights_required` と品質ゲートをテンプレートへ転記する。
- CI/運用ログの再分析を依頼する際に、`log_slice` と `operations_hooks` を確認して初動通知を揃える。
- Birdseye で Appendix C を開いた後、本ディレクトリの YAML を辿り実務向けの具体例を補強する。

## ペルソナ一覧
| ファイル | ロール | ハイライト |
| --- | --- | --- |
| [day8-analyzer-oncall.yaml](day8-analyzer-oncall.yaml) | Analyzer | Why-Why 断面と PagerDuty エスカレーションを組み込んだ解析当番向けプロファイル |
| [day8-reporter-concise-engineer.yaml](day8-reporter-concise-engineer.yaml) | Reporter | 失敗要約と提案下書きを迅速に整えるためのレポーター視点 |

新規ペルソナを追加する際は、`persona_id` を `day8-<role>-<slug>` で付与し、Birdseye の index/caps を Appendix C と同時に再生成する。

テーマ適用や UI 要件の擦り合わせは [`README_PERSONAS_THEMES.md`](../README_PERSONAS_THEMES.md) を参照してください。

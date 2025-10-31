# 付録E: 評価器構成

## Status
- Published: 2025-10-28
- Steward: Day8 Quality WG

## 目的
Day8 品質 WG が運用する自動評価ライン（Evaluation Line; E-Line）における BERTScore・ROUGE・ルール判定から成る複合スコアリングの前提条件、入力形式、出力解釈を一元化する。`docs/day8/quality/06_quality.md` に記載された品質評価プロセスや `workflow-cookbook/EVALUATION.md` のケース定義との連携背景を明示し、Birdseye / Guardrails での差分追跡を行う際の参照点を整理する。

## コンポーネント概要
| コンポーネント | 役割 | 主要設定 | 入力 | 出力 |
| --- | --- | --- | --- | --- |
| BERTScore 評価器 | モデル出力と参照回答の意味的近さを計測 | `bert-base-multilingual-cased`、`rescale_with_baseline=true`、`batch_size=16` | 正解テキスト、モデル生成テキスト | Precision/Recall/F1（0〜1）、閾値 `>=0.85` で合格判定補助 |
| ROUGE 評価器 | 要約タスクの文字列一致度を測定 | `rougeL`, `rouge1`（SentencePiece + Janome による語彙正規化） | 正解テキスト、モデル生成テキスト | ROUGE-1/L スコア、閾値 `>=0.70` で合格判定補助 |
| ルール判定エンジン | Guardrails 由来の制約チェック | `ruleset=quality/guardrails/rules.yaml`、`mode=blocking` | モデル生成テキスト、メタ情報（タスク種別、ユーザー指示） | 違反コード（`minor`, `major`, `critical`）、自動失格判定 |

### Guardrails ルール詳細

| 重大度 | ルール ID | チェック内容 | 再発防止のポイント |
| --- | --- | --- | --- |
| minor | `content.minor.priority_score_missing` | `Priority Score 未記載` など優先度テンプレートの欠如を検出 | PR/レポートへ `Priority Score: <number> / <justification>` を必ず記入し、優先度テンプレートを整備する |
| minor | `content.minor.template_incomplete` | Day8 テンプレート未充足（背景/手順/検証ログ/フォローアップ欠落）の記述を検出 | `docs/TASKS.md` と Task Seed テンプレートの全セクションを埋めたうえで提出する |
| major | `content.major.followup_missing` | フォローアップ未記載の警告を検出 | Task Seed/PR の Follow-ups に未完了タスクを列挙し、レビューログと同期する |
| major | `content.major.summary_missing` | 要約欠落・サマリー未記載を検出 | Day8 レポート冒頭に成果サマリを 3 行以内で記入し、更新をレビュー記録へ反映する |
| critical | `content.critical.secret_exposure` | 秘密鍵や資格情報 (`-----BEGIN PRIVATE KEY-----`, `AWS_SECRET_ACCESS_KEY`, `AKIA` など) の露出を検出 | 秘密は Vault 等に隔離し、公開前にレッドアクト・自動スキャンを実施する |
| critical | `content.critical.pii_exposure` | SSN/マイナンバーなど個人情報漏洩を検出 | 個人識別子はマスクまたはダミーデータへ置換し、テンプレートで PII 排除を確認する |

Guardrails ルールは `when.metadata` を利用してメタ情報に基づく分岐を記述できる。例：

```yaml
- id: content.major.report-mandatory-section
  severity: major
  when:
    metadata:
      task_type: report
  match:
    any:
      - contains: "テンプレート未充足"
```
`task_type` が `report` のケースのみ該当し、他タスクの評価には影響しない。

## セットアップ
- Day8 ルートで `pip install -r requirements-eval.txt` を実行し、BERTScore・ROUGE・PyTorch・SentencePiece・Janome・tokenizers・BeautifulSoup（bs4）を含む評価専用依存を導入する。
- CI は `requirements-eval.txt` をインストールしないため、ローカル検証や品質 WG のバッチ計測時のみ追加セットアップが必要になる。

## CLI パラメータ
- `--bert-model` / `--bert-batch-size`: Appendix E 既定値（`bert-base-multilingual-cased`, `16`）を踏襲。GPU 台数に応じて上書き可能。
- `--sentencepiece-model`: SentencePiece `.model` パス。未指定時は `DAY8_SENTENCEPIECE_MODEL` 環境変数、もしくはリポジトリ同梱モデルを探索する。トークン化後は Janome で基本形へ正規化し、Juman++ stemmer と同等の表層一致性を確保する。
- `--generated-at`: `metrics.json` の `generated_at` を外部リビジョン番号や Birdseye index のタイムスタンプで上書きする。未指定時は UTC 現在時刻が自動採番される。

## 入力と前処理
1. **正解テキスト** — `workflow-cookbook/EVALUATION.md` に準拠した YAML ケースから取得。`prompt`, `expected`, `metadata` を含め、正解側はマスク済み個人情報であることを確認する。
2. **モデル生成テキスト** — Day8 Analyzer の推論ログから取得。HTML や Markdown を含む場合でも、`quality/pipeline/normalize.py` の正規化処理を通してから評価器に渡す。
3. **メタ情報** — タスク種別、リージョン、モデル ID を含める。評価バンドル（`inputs.jsonl` / `expected.jsonl`）には `metadata` フィールドを必須とし、少なくとも `task_type` を設定する。ルール判定では `task_type` が `report` / `proposal` の場合に追加チェック（禁止語句、根拠リンク数）を有効化する。以下は最小構成例：

   ```jsonl
   {"id": "case-001", "output": "...", "metadata": {"task_type": "report", "region": "JP"}}
   {"id": "case-001", "expected": "...", "metadata": {"task_type": "report"}}
   ```

   `metadata` は入力・期待値の両方からマージされ、Guardrails の `when.metadata` 条件で参照できる。

## 出力整形
- **BERTScore / ROUGE**: 小数第4位で四捨五入し、`metrics.json` の `semantic`・`surface` セクションへ格納する。評価ログには `threshold_met` のブール値を追加する。
- **ルール判定**: 最も高い重大度を `violations.max_severity` として記録し、`critical` を検出した場合は `violations.threshold_met=false` として即座に Gate 失敗扱いにする。
- **集計**: 3 評価の結果から `overall_pass` を決定する。`critical` 違反が無く、かつ BERTScore F1 または ROUGE-L の少なくとも一方が閾値を満たす場合に合格 (`overall_pass=true`)。いずれかのスコアが閾値未満、もしくは重大度が `major` 以上の場合は再審査対象として `needs_review=true` を付与する。

## 運用チェックリスト
1. `quality/pipeline/normalize.py` と `workflow-cookbook/EVALUATION.md` の入力形式が一致しているか照合する。
2. ルールセット更新時は `ruleset=quality/guardrails/rules.yaml` をコミット単位でバージョン管理し、Birdseye `hot.json` の評価器ノードを同期する。
3. BERTScore / ROUGE のモデル更新やトークナイザ変更を行った場合は、Day8 Ops のスモークテスト（`scripts/quality/eval_smoke.sh`）を実行し、`metrics.json` の差分をレビュー記録へ添付する。
4. `overall_pass=false` のケースを週次でレビューし、ルール判定とスコア基準の乖離がないか確認する。乖離が継続する場合は閾値調整を提案し、Appendix E を更新する。

## 連携ドキュメント
- [ADR 0006: Evaluator ゲートとハイブリッド評価ライン](../adr/0006-evaluator-gates.md)
- [Day8 品質評価プロセス](../day8/quality/06_quality.md)
- [Day8 評価ケース定義 (workflow-cookbook/EVALUATION.md)](../../workflow-cookbook/EVALUATION.md)
- [Appendix I: Day8 テストケース観点](I_Test_Cases.md)

## 改訂ガイド
- 閾値やモデルを更新したら、BERTScore/ROUGE の設定値とルール判定ロジックを本付録に反映し、Birdseye index/caps/hot の `generated_at` を揃える。
- ルールセットの破壊的変更は Day8 Governance WG の承認ログと共に記録し、`docs/day8/quality/06_quality.md` の手順・チェックリストへ反映する。


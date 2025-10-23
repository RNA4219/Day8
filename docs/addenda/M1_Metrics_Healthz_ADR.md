# Day8 Addendum: M1 Metrics + Healthz ADR

Day8 Observability Council が承認した ADR `M1_Metrics_Healthz_ADR` を Day8 の導入計画へ落とし込み、`/healthz` エンドポイントと MetricsRegistry 公開値の更新ロードマップを整理します。Day8 側でメトリクスを運用する際の実装順序・監視動線・リリース連携を明文化し、既存の Ops/Quality ドキュメントと Birdseye へ反映するための補助資料です。

## M1 ADR の要点
- `GET /healthz` は即時応答可能なライトウェイト検査のみを行い、依存サービスの深い疎通はメトリクスでカバーする。
- MetricsRegistry にはサービスのライフサイクルを示す `app_boot_timestamp` と、主要機能の処理件数・失敗件数が必須とされる。
- ダミー値はスプリント内で実測値へ置き換えること、エンドポイントのキャッシュやリダイレクトは禁止というガードレールが定義されている。

## Day8 実装計画
### `/healthz`
1. Day8 API Gateway に `GET /healthz` を追加し、ステータスコードと JSON ボディ（`status` / `revision` / `generated_at`）を返す。
2. レスポンス生成では、プロセス内ヘルスチェックのみに限定し、外部依存（DB・キューなど）はメトリクスへ委譲する。
3. Guardrails に従い、レスポンスヘッダーへ `Cache-Control: no-store` を固定で付与し、CDN 側でのキャッシュ禁止を徹底する。

### MetricsRegistry
1. 既存のスタブ値を以下へ差し替える:
   - `app_boot_timestamp`: プロセス起動時の UTC ISO8601
   - `jobs_processed_total`: 実処理件数
   - `jobs_failed_total`: 失敗件数（リトライ含む）
   - `healthz_request_total`: `/healthz` への HTTP リクエスト件数
2. `/metrics` の公開粒度は ADR で定義したネームスペース（`day8_*`）へ揃え、Prometheus スクレイプ間隔 30s を前提にサマリをエクスポートする。
3. ダミー値を廃止するコミットでは、Day8 側のテストベンチにカウンタ初期値をモックするテストを追加し、M1 フェーズで求められる妥当性チェックを行う。

### Metrics コレクタ CLI
- `python scripts/perf/collect_metrics.py --prom-url http://localhost:8000/metrics --chainlit-log workflow-cookbook/logs/chainlit.jsonl`
  - `day8_*` プレフィクスの Prometheus 値と Chainlit JSONL ログを同時に取得し、リリース判定時にカウンタが期待値へ到達しているか
    を確認する。
  - Chainlit 側の JSONL は ADR で定義したイベント契約（`metric` + `value`、もしくは `metrics` ディクショナリ）を想定し、欠損時は
    0 件として扱う。
  - スクレイプ先の URL / ログパスは環境に合わせて引数で上書きできる。Birdseye 生成対象の資料では本 CLI を正式な検証手順として採
    用する。

### リリース・運用タイムライン
| フェーズ | 依頼元 | 主要作業 | 完了条件 |
| --- | --- | --- | --- |
| Sprint N | Ops | `/healthz` 実装 + スモークテスト | Day8 API で 200/JSON を返却、Birdseye 更新 PR に ADR 参照を記載 |
| Sprint N+1 | Data Platform | MetricsRegistry のダミー値置換 | `/metrics` に実測値が流れる。Day8 Runbook と Checklists を同期 |
| Sprint N+1 | Release | 先行組織への逆同期検討 | 共有レポジトリのタスク seed に Day8 差分を登録 |

## 影響範囲
- Day8 Ops/Release 文書: 監視項目とリリース承認条件に ADR 参照を追加。
- Birdseye: 本資料を新規ノードとして index/caps/hot を同期。
- MetricsRegistry 実装: Day8 API 層でのダミー値削除とテスト更新を別タスクで追跡。

## フォローアップ
- MetricsRegistry のカウンタ更新ロジックは Day8 API 実装タスクで扱う。完了後、本 ADR の「ダミー値差替え」節を完了済みへ更新する。
- 先行組織で ADR 改訂が入った場合は、Day8 で差分を取り込み本資料と Birdseye を再同期する。

# Contracts (Cookbook ↔ External)

Cookbook は単独で動作します。外部リポジトリは任意で次の契約を満たすことで追加データを提供できます。

## Artifacts
- `.ga/qa-metrics.json`: CI メトリクスの任意拡張。存在すれば Metrics Harvest が自動で取り込みます。

## Configurations
- `governance/predictor.yaml`: 予測ガバナンス向けの重み・閾値。未提供の場合は既定値で評価します。
- `governance/risk_config.yaml`: 旧互換パス。将来的に `governance/predictor.yaml` へ移行してください。

## 原則
- 契約ファイルが無い場合でも Cookbook はエラーにしません（フォールバック動作）。
- 契約の命名やスキーマは破壊変更しません。拡張が必要な場合は新しいキーを追加します。

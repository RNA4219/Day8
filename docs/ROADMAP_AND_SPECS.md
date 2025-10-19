# Day8 ロードマップ & 仕様メモ

プロジェクト全体の現在地と次の一手を素早く把握するためのガイドです。既存ドキュメントの骨格を保ちつつ、各資料の読みどころを短くまとめました。迷ったときはここから辿れば、必要な一次資料に直接到達できます。

## 方向性・やりたいこと
- [docs/day8/spec/01_requirements.md](day8/spec/01_requirements.md)
  - ユーザー課題と優先機能の一覧。機能間の依存関係とスコープ境界を確認する際の出発点。
- [docs/day8/spec/02_spec.md](day8/spec/02_spec.md)
  - プロダクト仕様の決定版。画面遷移図・ユースケース・成功条件がまとまっており、追加要望が来た際の差分判断に利用。

## しくみと運用メモ
- [docs/day8/design/03_architecture.md](day8/design/03_architecture.md)
  - ドメインレイヤ構成と主要コンポーネントのデータフローを整理。新規機能を追加する場合の配置場所と既存インタフェースの制約を確認。
- [docs/day8/ops/04_ops.md](day8/ops/04_ops.md)
  - 本番／ステージングの運用手順、リリースフロー、監視アラートの扱い。障害対応や当番引き継ぎ時の必読。
- [docs/day8/quality/06_quality.md](day8/quality/06_quality.md)
  - テストピラミッド、品質ゲート、計測指標 (エラーバジェット等) の定義。変更時に満たすべき品質チェックリストがまとまっています。

## セキュリティ & サンプル
- [docs/day8/security/05_security.md](day8/security/05_security.md)
  - 脅威モデリング、データ保護方針、権限設計の指針。レビュー時に確認すべきセキュリティ境界と例外プロセスが記載。
- [docs/day8/examples/10_examples.md](day8/examples/10_examples.md)
  - 実装例・ CLI サンプル・テストダブルの使い方。既存コードに習う際のリファレンスとして利用。

## 貢献メモ
- [docs/day8/guides/07_contributing.md](day8/guides/07_contributing.md)
  - Issue テンプレート、ブランチ戦略、レビュー SLA、合意済みのコーディング規約を網羅。新規参加者へのオンボーディングにも使用。

リンク先を増やしたり構成を変えたくなった場合は、このページを更新し、合わせて Issue か PR の説明欄に簡単な変更理由を記載してください。

# workflow-cookbook Addons Starter

テンプレートとして八日間で立ち上げることを想定した、workflow-cookbook 追加素材のスターターパックです。 `.github` と `docs` を含む最小骨格を提供し、CI/レポート自動化の導線を検証できます。

## 適用範囲
- workflow-cookbook を拡張する新規リポジトリの初期雛形
- GitHub Actions を用いたテスト結果収集とレポート生成のデモ
- 実サービスコードは含まず、ガバナンス/ドキュメント体験を整備したいケース

## 最短セットアップ
```bash
git clone <your-repo-url>
cd workflow-cookbook-addons
make bootstrap
make test
make report  # 失敗ログから reports/today.md を生成
```
`make test` は CI と同じダミーログを生成し、`make report` が `scripts/analyze.py` を実行します。必要に応じて `.venv` を有効化してカスタマイズしてください。

## フォルダ構成
- `.github/` – CI（`test.yml` / `reflection.yml` / `pr_gate.yml`）とテンプレート（Issue/PR/CODEOWNERS）
- `docs/` – 安全運用ノート（`safety.md`）
- `governance/` – ポリシー/権限 (`policy.yaml`)
- `logs/` – テストログの出力先（`test.jsonl`）
- `reports/` – 反省レポート (`today.md` / `issue_suggestions.md`)
- `scripts/` – 解析スクリプト (`analyze.py`)
- `workflow-cookbook/` – 参考用の完全版リソース集

## 運用ルール
- ブランチ戦略：`main` に直接 push せず PR 経由で反映。CODEOWNERS 承認必須。
- コミット：ガバナンス方針に従い、危険な自動修正は `docs/tests/reports` のみに限定。
- テスト/レポート：PR 前に `make test && make report` を実行し、`reports/` を確認。
- リリース：`reports/today.md` を軸に CHANGELOG/タグ運用を拡張予定（未実装）。

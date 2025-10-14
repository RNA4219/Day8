# 運用（Operations）

## 導入手順（サブディレクトリ運用の例）
1. `workflow-cookbook/` をリポジトリ直下に配置
2. `.github/workflows/test.yml` と `reflection.yml` を配置
3. コミット＆プッシュ → `test` 実行 → `reflection` 連動

## 失敗時の切り分け
- `test` がこける: ログが生成されているか確認（Artifacts）
- `reflection` がこける: `analyze.py` のパスと Python バージョンを確認
- 既存の CI と競合する場合: ワークフロー名やトリガを調整

## 併用例（Codex 近似環境）
- 失敗時のみ `ghcr.io/openai/codex-universal` で再実行し、環境差分を切り分ける

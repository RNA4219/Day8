# codemap ツール

`codemap.update` は Birdseye のインデックスおよびカプセルを再生成するコマンドです。標準ライブラリのみで動作し、複数ターゲットを一
括で更新できます。

## 依存

- Python 3.11 以上
- 追加の外部ライブラリは不要

## 実行手順

1. （任意）仮想環境を作成し、有効化します。
2. リポジトリルートで次のコマンドを実行します。

   ```bash
   python workflow-cookbook/tools/codemap/update.py --targets docs/birdseye/index.json,workflow-cookbook/docs/birdseye/index.json --emit index+caps
   ```

   - `--targets`: 再生成したい Birdseye インデックス（`.../index.json`）をカンマ区切りで指定します。指定順に処理します。
   - `--emit`: 出力する成果物を `index` / `caps` / `index+caps` から選択します。
   - `--dry-run`: 差分検知のみを行い、ファイルを変更しません。
     更新対象だったパスは `[dry-run] would update ...` 形式で標準出力に表示されます。
3. 実行後、対象配下の `index.json`・`caps/*.json`・`hot.json`（存在する場合）の `generated_at` と依存関係が同期されます。

## Birdseye 再生成スクリプト

`update.py` は JSON の正規化・依存関係再計算・差分検知を一括で実行します。I/O または JSON 解析に失敗した場合は `UpdateError` を投げ
て終了します。

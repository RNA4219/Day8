# codemap ツール

`codemap.update` は Birdseye のインデックスおよびカプセルを再生成するコマンドです。標準ライブラリのみで動作し、複数ターゲットを一
括で更新できます。

## 挙動サマリ

- **複数ターゲット**: `--targets` に与えた `index.json` をカンマ区切りの順番で巡回し、それぞれ独立に差分検知・書き込みを行います。空要素は無視されます。
- **`--emit` 制御**: `index` はインデックスのみ、`caps` はカプセルのみ、`index+caps` は両方を更新します。インデックスを書き換えた場合は同じターゲットのカプセル更新時にも新しい `generated_at` が強制適用されます。
- **`generated_at` 同期**: `index.json` の `edges` が正規化された結果と変わった場合にファイルを書き出し、新しい UTC タイムスタンプを付与します。`caps/*.json` は依存関係に変化があるか、インデックス更新で `generated_at` が変化したときだけ更新します。
- **ホットリスト**: `index.json` と同じ階層の `hot.json` が存在する場合、インデックスを書き換えたタイミングで `generated_at` を同一値へ更新します（存在しない場合は無視します）。

## 依存

- Python 3.11 以上
- 追加の外部ライブラリは不要

## 実行手順

1. （任意）仮想環境を作成し、有効化します。
2. リポジトリルートで次のコマンドを実行します。

   ```bash
   python workflow-cookbook/tools/codemap/update.py --targets docs/birdseye/index.json,workflow-cookbook/docs/birdseye/index.json --emit index+caps
   ```

   - `--targets`: 再生成したい Birdseye インデックス（`.../index.json`）をカンマ区切りで指定します。空文字は無視され、指定順に処理します。
   - `--emit`: 出力する成果物を `index` / `caps` / `index+caps` から選択します。`index+caps` は既定値です。
   - `--dry-run`: 差分検知のみを行い、ファイルを変更しません。
3. 実行後、対象配下の `index.json`・`caps/*.json`・`hot.json`（存在する場合）の `generated_at` と依存関係が同期されます。

## Birdseye 再生成スクリプト

`update.py` は JSON の正規化・依存関係再計算・差分検知を一括で実行します。I/O または JSON 解析に失敗した場合は `UpdateError` を投げ
て終了します。

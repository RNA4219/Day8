# codemap ツール

`codemap.update` は Birdseye のインデックスおよびカプセルを再生成するコマンドです。標準ライブラリのみで動作し、複数ターゲットを一
括で更新できます。Day8 では `python scripts/birdseye_refresh.py --docs-dir ...` が本モジュールをラップして呼び出します。

## 挙動サマリ

- **複数ターゲット**: `--targets` に与えた `index.json` をカンマ区切りの順番で巡回し、それぞれ独立に差分検知・書き込みを行います。空要素は無視されます。
- **`--emit` 制御**: `index` はインデックスのみ、`caps` はカプセルのみ、`index+caps` は両方を更新します。`index` / `index+caps` を指定した場合はエッジ差分の有無にかかわらず毎回 `generated_at` が再採番され、`index+caps` では同じ値がカプセルにも強制適用されます。
- **`generated_at` 同期**: `index.json` は `--emit index` / `index+caps` 実行ごとに新しい UTC タイムスタンプを採番します。`caps/*.json` は依存関係に変化があるか、またはインデックスで採番された `generated_at` を共有する必要があるときに更新されます。
- **ホットリスト**: `index.json` と同じ階層の `hot.json` が存在する場合、`--emit index` / `index+caps` により `generated_at` が更新されたタイミングで同一値へ同期します（存在しない場合は無視します）。

## 依存

- Python 3.11 以上
- 追加の外部ライブラリは不要

## 実行手順

1. （任意）仮想環境を作成し、有効化します。
2. リポジトリルートで次のコマンドを実行します。

   ```bash
   python scripts/birdseye_refresh.py --docs-dir docs/birdseye --docs-dir workflow-cookbook/docs/birdseye
   ```

   - `--docs-dir`: 再生成したい Birdseye ディレクトリ（`.../birdseye`）を繰り返し指定します。内部で `codemap.update` の `--targets` へ変換されます。
   - `--dry-run`: 差分検知のみを行い、ファイルを変更しません。更新対象だったパスは `[dry-run] would update ...` 形式で標準出力に表示されます。
3. 実行後、対象配下の `index.json`・`caps/*.json`・`hot.json`（存在する場合）の `generated_at` と依存関係が同期されます。

## Birdseye 再生成スクリプト

`update.py` は JSON の正規化・依存関係再計算・差分検知を一括で実行します。I/O または JSON 解析に失敗した場合は `UpdateError` を投げ
て終了します。

# Day8 デプロイガイド付録（Appendix H）

Day8 環境向けのデプロイ手順を開発・Docker・GitHub Actions の 3 つの観点で整理した付録です。Day8 のリポジトリ構成と workflow-cookbook の運用に合わせて最小限の変更で導入できるように設計しています。環境変数や設定ファイルの網羅チェックは Appendix L（[docs/addenda/L_Config_Reference.md](L_Config_Reference.md)）とセットで運用してください。

## 開発環境フロー

1. **ブランチ戦略** — `main` から派生したトピックブランチで作業し、ドキュメント/ワークフロー更新は最小差分でコミットします。リリース前に `git rebase origin/main` を実行し、Birdseye の `generated_at` などメタデータの競合を解消します。
2. **依存セットアップ** — Python 依存はリポジトリ直下で `pip install -r requirements-dev.txt` を実行して同期します。`workflow-cookbook/scripts/run_ci_tests.py` が `python::root` を検出し、CI の Python ジョブでこの requirements を利用します。
3. **ローカル検証** — デプロイ前に `python workflow-cookbook/scripts/analyze.py --root . --emit report` を実行し、CI での差分検出を先取りします。必要に応じて `--focus docs` オプションで Day8 配下に絞り込み、リンク切れや Birdseye 未更新を確認します。
4. **構成テスト** — リリースフローに追加するワークフロー/スクリプトは `python -m compileall` や `node --test` など既存ポリシーのコマンドで事前検証し、CI の失敗を予防します。
5. **リリースタグ** — Day8 では GitHub Release に連動するタグ名を `day8-vYYYYMMDD` 形式で管理します。タグ作成前に `git status --short` と `git diff --stat origin/main` で差分を再確認してください。

### チェックリスト（ローカル）
- [ ] `python workflow-cookbook/scripts/analyze.py --root . --emit report`
- [ ] `set -a; source config/env.example; set +a` → `scripts/warmup.sh` で Cold Start を事前解消
- [ ] 必要な Docker build を手元で `docker build` し、ランタイム依存の抜けを確認
- [ ] `python scripts/birdseye_refresh.py --docs-dir docs/birdseye --docs-dir workflow-cookbook/docs/birdseye` を実行し、`index.json` → `caps` → `hot.json` を含む全ファイルの `generated_at` を同一タイムスタンプへ揃える
- [ ] `git tag -a day8-vYYYYMMDD -m "Day8 release YYYYMMDD"` を作成（Release 発行前）

## Docker デプロイ

Day8 のワークフローをコンテナ化する際は、リポジトリ直下の `Dockerfile` を利用します。`python:3.11-slim` をベースに `requirements-dev.txt` をインストールしたうえで、Day8 リポジトリを `/opt/day8` にコピーし、CI 互換のデフォルトコマンドとして `pytest -q tests workflow-cookbook/tests` を実行します。

### ビルドと検証手順
1. ルートで `docker build -t day8 .` を実行し、`requirements-dev.txt` の依存が解決できることを確認します。ビルド時に追加の OS パッケージが必要な場合は `Dockerfile` の `apt-get` レイヤへ追記し、`pip install` レイヤを分割し直します。
2. `docker run --rm day8` を実行し、Day8 CI と同じ `pytest -q tests workflow-cookbook/tests` が完走することを確認します。失敗した場合はテストログを収集し、Day8 CI の pytest ジョブと差分がないか確認してください。

### 運用メモ
- `Dockerfile` の `CMD` は pytest を既定としています。アプリケーション起動用途で利用する場合は override するか、`ENTRYPOINT`/`CMD` を適宜差し替えてください。
- Day8 では `.dockerignore` に `docs/birdseye/` を残し、軽量なビルドコンテキストを維持します。Birdseye の再生成は CI 側で実施します。
- コンテナイメージのタグは Git タグと同じ `day8-vYYYYMMDD` を採用し、GitHub Container Registry へ `ghcr.io/<org>/day8:<tag>` として公開します。

## GitHub Actions リリース設定

1. **ワークフローファイル** — `.github/workflows/release.yml` を作成し、`push` の `tags: ["day8-v*"]` トリガで発火させます。ビルド→テスト→Docker push→GitHub Release 更新の順でジョブを配置します。
2. **ローカル検証の再実行** — `analyze` ステップを最初に実行し、ドキュメントや Birdseye の整合性チェックを CI で再確認します。`python workflow-cookbook/scripts/analyze.py --root . --emit report --fail-on warnings` のように、警告で失敗させるフラグを有効化します。Birdseye の再生成には `python scripts/birdseye_refresh.py --dry-run --docs-dir docs/birdseye --docs-dir workflow-cookbook/docs/birdseye` で差分を確認してから本実行する運用を推奨します。
3. **Docker ビルド & プッシュ** — `docker/login-action` と `docker/build-push-action` を利用し、`day8-v*` タグごとのイメージをビルドします。GitHub Actions のキャッシュは `actions/cache` で `workflow-cookbook/` の依存インストールを短縮します。
4. **成果物の添付** — `actions/upload-artifact` で `workflow-cookbook/scripts/analyze.py` の出力や `docs/birdseye/*.json` の差分をアーカイブし、リリース監査を容易にします。
5. **権限管理** — `permissions: contents: write, packages: write` を設定し、タグ付き push 時のみリリース更新・コンテナ公開が成功するようにします。

### Release テンプレート
```
## Summary
- <変更のハイライト>

## Verification
- python workflow-cookbook/scripts/analyze.py --root . --emit report --fail-on warnings
- docker build -t ghcr.io/<org>/day8:day8-vYYYYMMDD .
- pytest / node --test

## Notes
- Birdseye generated_at: <YYYY-MM-DDTHH:MM:SSZ>（`python scripts/birdseye_refresh.py --docs-dir docs/birdseye --docs-dir workflow-cookbook/docs/birdseye` 実行後に `index.json` / `caps` / `hot.json` で揃える）
- Related PRs: <リンク>
```

## 参考リンク
- [workflow-cookbook/RUNBOOK.md](../../workflow-cookbook/RUNBOOK.md)
- [workflow-cookbook/CHECKLISTS.md](../../workflow-cookbook/CHECKLISTS.md)
- [workflow-cookbook/scripts/analyze.py](../../workflow-cookbook/scripts/analyze.py)

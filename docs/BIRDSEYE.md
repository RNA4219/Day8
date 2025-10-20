# Day8 Birdseye フォールバック手順

Day8 では [workflow-cookbook/GUARDRAILS.md](../workflow-cookbook/GUARDRAILS.md) に従い、Birdseye の index/caps/hot を用いた最小読込を必須としています。本ガイドは Guardrails が要求するフォールバック手順を Day8 向けにまとめたものです。`docs/birdseye/index.json` の `generated_at` が古い、対象ノードの Capsule が存在しない、`codemap.update` が実行できない等の例外時に参照してください。

## 1. 適用条件
- `docs/birdseye/index.json.generated_at` が最新コミットより古い、もしくは `edges` に対象ノードが存在しない。
- 対応する `docs/birdseye/caps/*.json` が欠損しており、再生成ツール (`codemap.update`) を即時に実行できない。
- Guardrails で定められた「最小読込」の前提が崩れ、Birdseye 情報の手動補完が必要な場合。

上記条件が解消されるまでは、ここに記載のフォールバックのみを使用し、恒久対応として Birdseye を再生成するタスクを併走させてください。

## 2. `edges` からの ±1 hop 抽出
1. 直近で変更したファイルやノード ID を起点に、`docs/birdseye/index.json.edges` から **起点に接続するエッジ** を探します。
2. 起点ノードと直接接続したノードを **±1 hop** として一次集合に含めます。
3. 追加で追跡が必要な場合のみ、一次集合に含まれるノードのエッジを再帰的に辿り、**最短で目的資料へ到達できる経路**を記録します。
4. 集合化したノード ID をメモ化し、読み込む Capsule の順番（入口 → 中核 → 補助）を整理します。

> Guardrails の規定上、`±2 hop` が既定ですが、フォールバック時は最小トークン消費のため **±1 hop で止める**ことを推奨します。必要に応じて `docs/ROADMAP_AND_SPECS.md` の Birdseye 反映 4 ステップを参照し、恒久対応の更新対象を洗い出してください。

## 3. Capsule / Hot リスト参照順
フォールバック中も Guardrails の読込順序を維持します。各ステップで参照すべき資料を以下に整理します。

1. **Capsule（一次参照）**
   - ±1 hop 抽出で得たノードに対応する `docs/birdseye/caps/<path>.json` を読み込み、役割・依存関係・更新条件を確認。
   - 欠損している Capsule の内容は [docs/birdseye/README.md](birdseye/README.md) のスキーマ説明を基に最小情報を補完します。
2. **Hot リスト（優先順位確認）**
   - `docs/birdseye/hot.json` を参照し、該当ノードがホットリスト対象かを確認。優先参照が指定されていれば、その理由に従い追加資料を抽出します。
3. **索引・復旧計画**
   - Birdseye 全体の更新計画は [docs/ROADMAP_AND_SPECS.md](ROADMAP_AND_SPECS.md) の「Birdseye 反映 4 ステップ」で確認し、再生成後の検証手順を明文化します。

Capsule やホットリストを手動で補完した場合は、後続の正式更新で JSON を再生成し、`generated_at` を同期させてください。

## 4. 関連ドキュメント
- [docs/birdseye/README.md](birdseye/README.md): Birdseye 運用全体像と更新フロー。
- [docs/ROADMAP_AND_SPECS.md](ROADMAP_AND_SPECS.md): Birdseye 反映 4 ステップと Day8 全体の索引ルール。
- [workflow-cookbook/GUARDRAILS.md](../workflow-cookbook/GUARDRAILS.md): Guardrails が定義する最小読込とフォールバック要件。

## 5. 恒久対応チェックリスト
- [ ] `codemap.update` などの再生成ツールを実行し、`docs/birdseye/index.json` と `docs/birdseye/caps/` を最新化した。
- [ ] `docs/birdseye/hot.json` の `generated_at` と優先度を Birdseye 更新内容に合わせて見直した。
- [ ] 上記差分をコミットし、レビュー時にフォールバックから正式運用へ戻したことを明示した。

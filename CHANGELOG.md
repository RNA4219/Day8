---
release_track: day8-core
owner: day8-maintainers
status: active
last_reviewed_at: 2025-11-21
next_review_due: 2025-12-05
---

# Day8 Changelog

Day8 リポジトリ固有の変更履歴を記録します。Katamari 本家のアップデートは `workflow-cookbook/CHANGELOG.md` で管理し、必要に応じて Day8 側へ反映した差分のみ本書へ記載します。

## [Unreleased]
- Day8 propose-only フローで取り込む予定の変更があれば、`docs/Release_Checklist.md` の結果とともにここへ追記する。
- Birdseye（`docs/birdseye/index.json` / `docs/birdseye/caps/` / `docs/birdseye/hot.json`）と同じコミットで `generated_at` を同期する。

### Day8 リリース通番ルール
- バージョンは `vX.Y.Z`（Day8 SemVer）で記載する。詳細は [Appendix M — Versioning & Release Operations](docs/addenda/M_Versioning_Release.md) を参照。
- `X`（MAJOR）は propose-only フローを破壊するガバナンス更新や CLI/JSON 互換性断絶がある場合にのみ更新する。
- `Y`（MINOR）は後方互換を維持したまま新しい機能やドキュメント導線を追加した場合に更新する。Birdseye ノード追加や Release Checklist 拡張も含む。
- `Z`（PATCH）はバグ修正・既存ドキュメントの補強・CI 設定の保守を対象とする。互換性差分がないことを mypy/ruff/pytest/node:test の結果で確認する。


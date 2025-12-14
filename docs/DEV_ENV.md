# 推奨開発環境（2025 年末版）

## TL;DR

| 目的 | 推奨ツール | メモ |
| --- | --- | --- |
| Python バージョン管理 | `mise`（旧 `rtx`）or `uv python` | `.python-version`/`.mise.toml` で 3.13 を固定 |
| 依存・仮想環境 | `uv` | `uv sync --all-extras` でロック＆インストール |
| Lint / Format | `ruff` | `ruff format` と `ruff check` を pre-commit にも連携 |
| 型チェック | `mypy` + 必要に応じて `pyright` | コード量が増えたら `uvx pyright` を併用 |
| テスト | `pytest` + `hypothesis` | 実験ごとの `tests/` かルート `tests/` を作成 |
| 自動化 | `just` or `task` | `just lint`, `just test` などで共通コマンド化 |
| シェル環境 | `direnv` + `.envrc` | `uv` が作る `.venv` を自動で読み込む |
| エディタ | VS Code + Ruff 拡張 or Neovim + LSP | `pyright`/`ruff` の LSP をオンにする |

## セットアップ手順

1. **Python ランタイム**
   - `mise use -g python@3.13` でグローバル 3.13 を入れる、または
   - `uv python install 3.13 && uv python pin 3.13` でプロジェクト固定。
2. **依存同期**
   - `uv sync --all-extras`（`dev` extra を拾う）または `uv pip compile pyproject.toml -o uv.lock` でロック→ `uv pip sync uv.lock`。
3. **direnv**
   - `.envrc` 例: `layout python python3.13 && source .venv/bin/activate`.
   - `direnv allow`.
4. **リント / テスト自動化**
   - `pre-commit install` を実行。
   - `.pre-commit-config.yaml`（必要なら後で追加）に `ruff`, `mypy`, `pytest --maxfail=1 --quick` などを書く。
5. **タスクランナー**
   - `justfile` 例:

     ```just
     lint:
        uv run ruff check
     typecheck:
        uv run mypy
     test:
        uv run pytest
     ```

## 実験ディレクトリ運用

- `experiments/NN_topic/` を作ったら `uv add --group NN_topic <pkg>` でその実験専用依存を分離するやり方も可能（`uv` のグループは PEP 735 に相当）。
- スクリプト単体の依存が軽いなら `uv run python experiments/NN_topic/main.py` で都度実行。
- ノートブックは `uvx jupyter lab` or `uv run python -m notebook` で起動し、`notebooks/` に保存。

## 2025 年の安定トレンド Tips

- **uv + Ruff セット** が Python コミュニティでデファクト化しつつある。`pip`/`virtualenv` でも問題ないがスピード差が大きい。
- **mypy or pyright**: ランタイム型チェックよりエディタ連携の型サーバーを重視する流れ。CLI での CI チェックは `mypy` が依然安定（バージョン 1.11 以降）。
- **pytest 8 + hypothesis 6**: プロパティベーステストで実験結果の再現性を確保しやすい。
- **direnv / mise**: Reproducible dev shell を数秒で切り替えられるため、複数実験を平行するときに便利。
- **just / task / make**: 最低限 `lint` `test` `typecheck` くらいはコマンド化しておくと CI への移行が容易。
- **VS Code Remote / devcontainer**: 将来的にクラウド（Codespaces, GitHub.dev）で遊びたい場合は `.devcontainer` を用意しておくとラク。

## TODO/アイデア

- `.pre-commit-config.yaml` の整備（`ruff`, `mypy`, `pyproject-fmt`, `doctest`など）。
- `uv lock` をコミットして CI で `uv sync --frozen` を使えるようにする。
- `notes/2025xxxx.md` を作り、実験の記録やリンク集を残す。
- 実験別に `pyproject.toml` の optional dependency group を増やす例:

  ```toml
  [project.optional-dependencies."exp-vision"]
  dependencies = ["numpy", "opencv-python"]
  ```

  `uv sync --group exp-vision --dev` で該当実験のみ依存を入れる。


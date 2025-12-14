# python-fun-scripts (2025 reboot)

スクリプト遊び場をスクラップ＆ビルドしました。\
`experiments/番号_名前/` 以下に 1 トピック 1 ディレクトリでスクリプトを置き、軽い README と `main.py`（またはノート等）を追加していく想定です。

## ディレクトリ構成

```
experiments/
  01_sample/
    README.md
    main.py
docs/
  DEV_ENV.md   # 推奨開発環境メモ
```

必要に応じて `notes/`, `data/`, `notebooks/` などを生やして OK。共通ユーティリティを共有したい場合のみ `lib/` を追加し、モジュール import するようにします。

## スクリプト追加フロー（推奨）

1. `experiments/` に `NN_topic-name/` ディレクトリを作成（`NN` は 2 桁の連番または日付など）。
2. `README.md`（目的・使い方・得られた学び）と `main.py` などソースを配置。
3. 必要な依存を `pyproject.toml` の `[project.optional-dependencies."exp-<name>"]` などで管理するか、`uv add <pkg>` でピン留め。
4. `ruff format && ruff check && mypy && pytest` で最低限の検証。
5. README の「Experiment index」に追記（必要になったらセクションを作成）。

## クイックスタート

```bash
# 1. Python 3.13 (or >=3.12) を用意
uv python install 3.13

# 2. 依存の同期（dev extra を含む）
uv sync --all-extras

# 3. コマンド例
uv run python experiments/01_sample/main.py
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy
```

`uv` は PEP 723/PEP 621 に準拠した高速パッケージ / 仮想環境マネージャ。詳細は `docs/DEV_ENV.md` を参照。

## Lint / Format / Type-check

- **ruff**: Lint + Format（`ruff format`）。`pyproject.toml` で line-length やルールを定義。
- **mypy**: 型チェック。実験レベルでは `pyproject.toml` の設定で緩めてあり、必要な箇所だけ `reveal_type` 等を使う。
- **pytest**: 各実験ディレクトリ配下に `tests/` を置くか、共通 `tests/` を使う。

## そのほか

- `docs/DEV_ENV.md` に 2025 年末時点での「人気かつ安定している Python 開発環境」のまとめがあります。
- 追加で欲しいテンプレやタスクランナー（例: `just`, `task`) があれば別途導入してください。

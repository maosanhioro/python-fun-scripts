"""
目的:
  新しいスクリプト用フォルダの雛形を作成する。

使い方:
  python tools/new_script.py 02 bouncing_balls
"""

import sys
from pathlib import Path

if len(sys.argv) != 3:
    print("usage: python new_script.py <number> <name>")
    sys.exit(1)

num = sys.argv[1]
name = sys.argv[2]

folder = Path(f"{num}_{name}")

if folder.exists():
    print("すでに存在します:", folder)
    sys.exit(1)

folder.mkdir()

# main.py
(folder / "main.py").write_text(
    '''"""
目的:
  ここにこのスクリプトの目的を書く
"""

def main():
    print("Hello, fun python!")

if __name__ == "__main__":
    main()
'''
)

# README.md
(folder / "README.md").write_text(
    f"""# {num}_{name}

## 概要
このスクリプトは何をするものか。

## ポイント
- 面白い点
- 学べる点

## 実行方法
```bash
python main.py
```
"""
)

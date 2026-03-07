#!/usr/bin/env python3
"""
tree.py — Выводит структуру папок и файлов проекта.

Запуск из корня репо:
    python tree.py

Или с указанием папки:
    python tree.py /path/to/repo

Результат сохраняется в tree.txt и выводится в консоль.
"""

import os
import sys

IGNORE = {'.git', '.github', '__pycache__', 'node_modules', '.DS_Store', 'Thumbs.db'}

def tree(root, prefix="", output=None):
    entries = sorted(os.listdir(root))
    entries = [e for e in entries if e not in IGNORE]

    dirs = [e for e in entries if os.path.isdir(os.path.join(root, e))]
    files = [e for e in entries if os.path.isfile(os.path.join(root, e))]

    for f in files:
        path = os.path.join(root, f)
        size = os.path.getsize(path)
        if size < 1024:
            s = f"{size}B"
        elif size < 1024 * 1024:
            s = f"{size // 1024}KB"
        else:
            s = f"{size // (1024*1024)}MB"
        line = f"{prefix}{f}  ({s})"
        print(line)
        if output is not None:
            output.append(line)

    for d in dirs:
        line = f"{prefix}{d}/"
        print(line)
        if output is not None:
            output.append(line)
        tree(os.path.join(root, d), prefix + "    ", output)


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    root = os.path.abspath(root)

    print(f"📂 {root}\n")
    lines = [f"📂 {root}", ""]
    tree(root, "", lines)

    out_path = os.path.join(root, "tree.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n✅ Сохранено в {out_path}")

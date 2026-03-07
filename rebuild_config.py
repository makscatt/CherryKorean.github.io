#!/usr/bin/env python3
"""
rebuild_config.py — Автообновление config.json

Читает config.json, для каждого theme* берёт masterJsonPath,
открывает соответствующий videotheme*.json (локально в том же репо),
считает totalCount и hasNew, дописывает эти поля в config.json.

Остальные поля (blocks, coverImage, targetPageUrl, pathway и т.д.) не трогает.

Запуск из корня репо склада:
    python rebuild_config.py

Или с указанием папки где лежит videothemes/:
    python rebuild_config.py /path/to/repo/

Структура репо:
    videothemes/json/config.json
    videothemes/json/videotheme1.json
    videothemes/json/videotheme2.json
    ...

Добавь в GitHub Actions перед деплоем:
    - name: Rebuild config
      run: python rebuild_config.py
"""

import json
import os
import sys


def find_content_root(start=None):
    """Ищем папку, в которой лежит videothemes/json/config.json"""
    dirs_to_check = []

    if start:
        dirs_to_check.append(start)
        dirs_to_check.append(os.path.join(start, "videothemes", "json"))

    dirs_to_check.append(os.getcwd())
    dirs_to_check.append(os.path.join(os.getcwd(), "videothemes", "json"))
    dirs_to_check.append(os.path.dirname(os.path.abspath(__file__)))

    for d in dirs_to_check:
        cfg = os.path.join(d, "config.json")
        if os.path.exists(cfg):
            return d

    return None


def rebuild_config(root_arg=None):
    json_dir = find_content_root(root_arg)
    if not json_dir:
        print("❌ Не найден config.json")
        print("   Запусти из корня репо или укажи путь:")
        print("   python rebuild_config.py /path/to/repo/")
        sys.exit(1)

    config_path = os.path.join(json_dir, "config.json")

    # masterJsonPath в config: "videothemes/json/videotheme1.json"
    # json_dir это videothemes/json/, значит repo_root на 2 уровня выше
    repo_root = os.path.normpath(os.path.join(json_dir, "..", ".."))

    print(f"📂 config:    {config_path}")
    print(f"📂 repo root: {repo_root}\n")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    updated = 0
    total_themes = 0

    for key in sorted(config.keys()):
        entry = config[key]
        if not key.startswith("theme") or not isinstance(entry, dict):
            continue

        total_themes += 1
        master_path = entry.get("masterJsonPath", "")

        # Ищем файл: сначала по masterJsonPath от repo_root, потом в json_dir
        theme_file = os.path.join(repo_root, master_path)
        if not os.path.exists(theme_file):
            theme_file = os.path.join(json_dir, os.path.basename(master_path))
        if not os.path.exists(theme_file):
            print(f"  ⚠️  {key}: не найден {master_path}")
            continue

        with open(theme_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        total_count = 0
        has_new = False

        if isinstance(data, dict):
            for block_data in data.values():
                if isinstance(block_data, list):
                    total_count += len([
                        item for item in block_data
                        if isinstance(item, dict) and item.get("video")
                    ])
                    if any(isinstance(item, dict) and item.get("isNew")
                           for item in block_data):
                        has_new = True
        elif isinstance(data, list):
            total_count = len(data)
            has_new = any(
                isinstance(item, dict) and item.get("isNew") for item in data
            )

        old_count = entry.get("totalCount")
        old_new = entry.get("hasNew")

        entry["totalCount"] = total_count
        entry["hasNew"] = has_new

        changes = []
        if old_count != total_count:
            changes.append(f"видео: {old_count}→{total_count}")
        if old_new != has_new:
            changes.append(f"new: {old_new}→{has_new}")

        if changes:
            print(f"  ✏️  {key}: {', '.join(changes)}")
            updated += 1
        else:
            print(f"  ✓  {key}: {total_count} видео")

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Готово! {total_themes} тем, {updated} обновлено")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    rebuild_config(path)

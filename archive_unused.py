#!/usr/bin/env python3
"""
archive_unused.py — Перемещает неиспользуемые файлы в _archive/

Запуск из корня репо-склада:
    python archive_unused.py

Или с флагом --dry-run чтобы сначала посмотреть что будет перемещено:
    python archive_unused.py --dry-run

Файлы перемещаются в папку _archive/ с сохранением структуры.
Папка _archive/ добавлена в .gitignore чтобы не попадала в деплой.
"""

import os
import sys
import shutil

ARCHIVE_DIR = "_archive"

# === ФАЙЛЫ ДЛЯ АРХИВАЦИИ ===

# Корень: старые HTML шаблоны
ROOT_HTML = [
    "ai_tutor.html",
    "blocks.html",
    "game_words.html",
    "index.html",
    "menu.html",
    "offer2.html",
    "pathway_player.html",
    "success.html",
    "theme_menu_template.html",
    "twocardsmenu.html",
    "video_list_template.html",
    "video_random.html",
    "videorating.html",
    "videoreviews.html",
    "videothemebank.html",
    "videopremium.html",
    "videooffer.html",
]

# Корень: старые CSS
ROOT_CSS = [
    "buttonstyles.css",
    "font.css",
    "minimenu.css",
    "themes.css",
    "timer.CSS",
    "videoplayer.css",
    "videostyles.css",
    "videosubmenustyles.css",
]

# Корень: старые JS
ROOT_JS = [
    "analytics.js",
    "ranks.js",
    "sessionTracker.js",
    "trackActivity.js",
]

# Корень: шрифты
ROOT_FONTS = [
    "NetflixSans-Bold.otf",
    "NetflixSans-Light.otf",
    "NetflixSans-Medium.otf",
    "NetflixSans-Regular.otf",
    "coockierun.ttf",
]

# Корень: звуки
ROOT_SOUNDS = [
    "BTunaS - Kimchi Club.mp3",
    "card.MP3",
    "click.mp3",
    "excellent.mp3",
    "failure.mp3",
    "game_starts.mp3",
    "level_unlocked.MP3",
    "lvl_complete.MP3",
    "pushButton.MP3",
    "rankawards.mp3",
    "starsuccess.mp3",
    "startcardsgame.mp3",
    "success.MP3",
    "torch.mp3",
]

# Корень: промо-видео
ROOT_VIDEO = [
    "game.mp4",
    "pathway.mp4",
    "show.mp4",
]

# Корень: картинки-дубли
ROOT_IMAGES = [
    "app_name_1.png",
    "bridge.png",
    "cherrykorean-instruction.png",
    "favicon.ico",
    "instruction.png",
    "kimchibutton.png",
    "loading.png",
    "lock.png",
    "lockhorizont.png",
    "logo.png",
    "menu.png",
    "redlock.png",
    "redlockhorizont.png",
    "start.png",
    "startscreenBGnew.png",
    "videothemebc.png",
    "win.png",
]

# Корень: старые JSON
ROOT_JSON = [
    "audiobox.json",
    "easywords.json",
    "easytohardwords.json",
]

# Корень: служебные
ROOT_MISC = [
    "backup.txt",
    "package.json",
    "package-lock.json",
]

# twocards: неиспользуемые
TWOCARDS = [
    "twocards/background.png",
    "twocards/cardback.png",
]

# customcontrolbuttons/ — всё
CUSTOM_BUTTONS = [
    "customcontrolbuttons/play.png",
    "customcontrolbuttons/repeat.png",
    "customcontrolbuttons/speed.png",
]

# videothemes: неиспользуемые
VIDEOTHEMES_UNUSED = [
    "videothemes/communication.png",
    "videothemes/game.png",
    "videothemes/game_words.png",
    "videothemes/rating.png",
    "videothemes/reviews.png",
    "videothemes/reviewsbackground.png",
    "videothemes/bank.png",
    "videothemes/riddle/healer.png",
    "videothemes/riddle/runbts.png",
    "videothemes/json/Шаблон.json",
]

# Все файлы
ALL_FILES = (
    ROOT_HTML + ROOT_CSS + ROOT_JS + ROOT_FONTS + ROOT_SOUNDS +
    ROOT_VIDEO + ROOT_IMAGES + ROOT_JSON + ROOT_MISC +
    TWOCARDS + CUSTOM_BUTTONS + VIDEOTHEMES_UNUSED
)

# Целые папки для архивации
ARCHIVE_DIRS = [
    "fonts",
    "nvlm_project",
]

# Пустые папки webm_output/ для удаления
EMPTY_DIRS = []


def find_webm_output_dirs(root):
    """Находит все пустые webm_output/ папки."""
    result = []
    for dirpath, dirnames, filenames in os.walk(root):
        for d in dirnames:
            if d == "webm_output":
                full = os.path.join(dirpath, d)
                # Проверяем что папка пустая или содержит только пустые подпапки
                contents = list(os.listdir(full))
                if not contents:
                    result.append(full)
    return result


def move_file(src, dst, dry_run=False):
    """Перемещает файл, создавая папки при необходимости."""
    if not os.path.exists(src):
        return False

    if dry_run:
        size = os.path.getsize(src)
        if size < 1024:
            s = f"{size}B"
        elif size < 1024 * 1024:
            s = f"{size // 1024}KB"
        else:
            s = f"{size // (1024*1024)}MB"
        print(f"  → {src}  ({s})")
        return True

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)
    return True


def move_dir(src, dst, dry_run=False):
    """Перемещает целую папку."""
    if not os.path.exists(src):
        return False

    if dry_run:
        total = 0
        count = 0
        for dirpath, _, filenames in os.walk(src):
            for f in filenames:
                total += os.path.getsize(os.path.join(dirpath, f))
                count += 1
        s = f"{total // (1024*1024)}MB" if total > 1024*1024 else f"{total // 1024}KB"
        print(f"  → {src}/  ({count} файлов, {s})")
        return True

    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.move(src, dst)
    return True


def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("🔍 РЕЖИМ ПРОСМОТРА (--dry-run) — ничего не будет перемещено\n")
    else:
        print(f"📦 Перемещаю неиспользуемые файлы в {ARCHIVE_DIR}/\n")

    moved_count = 0
    total_size = 0

    # 1. Отдельные файлы
    for filepath in ALL_FILES:
        if os.path.exists(filepath):
            if not dry_run:
                size = os.path.getsize(filepath)
                total_size += size
            dst = os.path.join(ARCHIVE_DIR, filepath)
            if move_file(filepath, dst, dry_run):
                moved_count += 1
                if dry_run:
                    total_size += os.path.getsize(filepath)

    # 2. Целые папки
    for dirname in ARCHIVE_DIRS:
        if os.path.exists(dirname):
            if not dry_run:
                for dp, _, fns in os.walk(dirname):
                    for f in fns:
                        total_size += os.path.getsize(os.path.join(dp, f))
            dst = os.path.join(ARCHIVE_DIR, dirname)
            if move_dir(dirname, dst, dry_run):
                moved_count += 1
                if dry_run:
                    for dp, _, fns in os.walk(dirname):
                        for f in fns:
                            total_size += os.path.getsize(os.path.join(dp, f))

    # 3. Пустые webm_output/ — просто удаляем
    empty_dirs = find_webm_output_dirs("video") if os.path.exists("video") else []
    for d in empty_dirs:
        if dry_run:
            print(f"  🗑 {d}  (пустая папка)")
        else:
            os.rmdir(d)
        moved_count += 1

    # 4. Обновляем .gitignore
    if not dry_run:
        gitignore_path = ".gitignore"
        gitignore_entry = "_archive/"
        existing = ""
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r", encoding="utf-8") as f:
                existing = f.read()

        if gitignore_entry not in existing:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                if existing and not existing.endswith("\n"):
                    f.write("\n")
                f.write(f"\n# Archived unused files\n{gitignore_entry}\n")
            print(f"\n  ✏️  Добавлено '{gitignore_entry}' в .gitignore")

    # Итого
    if total_size > 1024 * 1024:
        size_str = f"{total_size / (1024*1024):.1f} MB"
    else:
        size_str = f"{total_size // 1024} KB"

    print(f"\n{'='*50}")
    if dry_run:
        print(f"  Будет перемещено: {moved_count} объектов ({size_str})")
        print(f"  Запусти без --dry-run чтобы выполнить")
    else:
        print(f"  ✅ Перемещено: {moved_count} объектов ({size_str})")
        print(f"  📁 Архив: {os.path.abspath(ARCHIVE_DIR)}/")
        print(f"\n  Следующий шаг:")
        print(f"    git add -A")
        print(f"    git commit -m 'archive: move unused files to _archive'")
        print(f"    git push")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()

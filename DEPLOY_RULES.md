# DEPLOY_RULES — Telegram-Korean-mini-App (контент-склад / CDN)

Деплой = **`git push` в `main`**. Всё остальное делает GitHub Actions автоматом.
Никаких ручных `scp`/`docker`/`ssh` — это не сервер, а статика в облаке.

## Что происходит при пуше в main

`git push origin main` → запускается `.github/workflows/deploy.yml`:

1. `python rebuild_config.py` — пересчёт `totalCount`/`hasNew` в `config.json`.
2. Автокоммит изменённого `config.json` обратно в репо (от `github-actions`).
3. Заливка в **Yandex Object Storage** через `s3cmd`:
   - `*.css` — отдельно, с MIME `text/css`;
   - всё остальное — `s3cmd sync --delete-removed`, исключая
     `.git/*`, `.github/*`, `*.md`, `deploy.yml`, `*.css`.

Инфра: endpoint `storage.yandexcloud.net`, регион `ru-central1`, ключи — в
GitHub Secrets (`YANDEX_ACCESS_KEY`/`SECRET_KEY`/`BUCKET`). Подробнее —
`Desktop/projects/INFRA.md` → «Yandex Object Storage». Репо:
`github.com/makscatt/CherryKorean.github.io`.

## Как деплоить

**Вариант 1 — батник (рекомендуется):** запустить `deploy-miniapp.bat`.
Делает `git add -A` → commit (спросит сообщение) → `git pull --rebase` → `git push`.

**Вариант 2 — вручную:**
```bash
git add -A
git commit -m "deploy: <что добавили>"
git pull --rebase origin main
git push origin main
```

## Важно

- **`sync --delete-removed`**: файл, удалённый локально, удаляется и из бакета.
  Не коммить удаление видео/картинок, если они ещё нужны.
- **`*.md` не заливаются** — этот файл, `SONGS.md`, `CLAUDE.md` остаются только
  в репо, на CDN их нет. Документацию можно коммитить свободно.
- `rebuild_config.py` всё равно прогоняется в CI — локальный прогон лишь
  страховка/проверка перед пушем (на Windows запускать с `PYTHONUTF8=1`, иначе
  падает на emoji в выводе под cp1251).
- Сборку проверяй до пуша: все ссылки `video`/`videoMp4` в мастер-JSON должны
  иметь файлы на диске, обe обложки темы (`videothemes/themeNN.png` +
  `videothemes/subthemebc/<bg>.png`) — на месте.

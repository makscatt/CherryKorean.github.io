# Песни (караоке-видеотемы) — алгоритм добавления

Единственный источник этой инструкции — этот файл
(`Telegram-Korean-mini-App/SONGS.md`). Эталон формата — `videotheme36.json`
(песня 나는 반딧불), последняя добавленная — `videotheme38.json` (가호 — 시작).

## Что должно быть на входе

1. Папка `video/<папка_песни>/` с нарезанными фрагментами-фразами:
   `.webm` в корне + такие же `.mp4` в подпапке `mp4/` (это выход пайплайна
   Makscut, папка `approved`).
2. Полный клип песни (обычно `[MV] ....webm`) — положить в ту же
   `video/<папка_песни>/`.
3. Черновой `videothemeNN.json` с блоком `b1` (фрагменты + дословные
   переводы из имён файлов) — тоже из Makscut.

## Шаги

### 1. mp4-копия полного клипа (лимит ~20 МБ)

```bash
ffmpeg -y -i "клип.webm" -c:v libx264 -b:v 620k -pass 1 -vf scale=-2:720 -preset medium -an -f mp4 NUL
ffmpeg -y -i "клип.webm" -c:v libx264 -b:v 620k -pass 2 -vf scale=-2:720 -preset medium \
  -c:a aac -b:a 128k -movflags +faststart "mp4/клип.mp4"
```

Положить в `video/<папка_песни>/mp4/` с тем же именем.

### 2. Тайминги строк — karaoke_timer

Тулза: `projects/archive/karaoke/karaoke_timer.pyw`
(нужны `pip install python-vlc` + установленный VLC).

Загрузить полный клип, вставить текст песни, по строкам жать `T` (или SET) —
сохранить JSON: `[{"t": 26.6, "korean": "..."}]` → положить как
`video/<папка_песни>/karaoke_lyrics.json`.

### 3. Переводы — контекстные, НЕ дословные

Это песня: переводить с учётом всего текста, а не построчно в лоб
(строки часто продолжают друг друга, подлежащее может быть в соседней строке).
Перевести и `karaoke.lyrics`, и `b1` — одними и теми же формулировками.
Поля: `russian` + `english` у каждой строки/фрагмента.
Строки типа «Ah-ah-ah» оставлять как есть.

### 4. Сшивка videothemeNN.json

Итоговая структура (порядок ключей как в 36):

```json
{
  "isSong": true,
  "isNewSong": true,
  "karaoke": {
    "clip": "video/<папка>/<полный клип>.webm",
    "clipMp4": "video/<папка>/mp4/<полный клип>.mp4",
    "lyrics": [{"t": 10.85, "korean": "...", "russian": "...", "english": "..."}]
  },
  "b1": [{"video": "...", "videoMp4": "...", "korean": "...", "russian": "...", "english": "...", "new": true}],
  "b2": [], "b3": [], "b4": [], "b5": []
}
```

Файл кладётся в `videothemes/json/videothemeNN.json`.

### 4.1. Сортировка b1 по тексту песни

Makscut выдаёт `b1` отсортированным по алфавиту (по именам файлов) — в режиме
тренировки песня пойдёт не с первой строчки. Обязательно пересортировать `b1`
по порядку строк `karaoke.lyrics` (по `t`, дубли-варианты одной фразы — подряд).

### 5. Снять isNewSong с предыдущей песни

`isNewSong: true` должна быть только у новой песни — у прошлой ключ удалить
(дашборд kimchi-server показывает в «Новинках» все мастер-JSON с
`isNewSong === true`).

### 6. Регистрация в config.json

В `videothemes/json/config.json`, секция `songs`, добавить запись:

```json
"songN": {
  "title": "원제 (Перевод названия)",
  "title_en": "원제 (English Title)",
  "cover": "videothemes/songs_covers/songN.png",
  "masterJsonPath": "videothemes/json/videothemeNN.json"
}
```

Обложку положить в `videothemes/songs_covers/songN.png`.

### 7. rebuild_config + деплой

```bash
python rebuild_config.py   # обновит totalCount/hasNew у theme*
deploy-miniapp.bat         # деплой контент-репо (запускает босс)
```

## Как это рендерится (kimchi-server)

- Дашборд: `templates/dashboard.html` → `config.songs` → fetch мастер-JSON →
  бейдж NEW при `isNewSong:true`, карточка ведёт в тренажёр с
  `selectedSongMaster` + `trainerLoadMode=song`.
- Караоке-режим: `templates/video_list_template.html` (`karaoke-view`,
  `klLyrics`) — играет `karaoke.clip`, подсвечивает строку по `t`,
  перевод берёт из `russian`/`english`.

# -*- coding: utf-8 -*-
"""
translate_content_en.py — дополняет банки фраз полем `english`.

Phase 2 EN-локализации. Проходит по videotheme*.json + begginer/intermediate/
advanced.json в videothemes/json/, для каждой записи с `korean`+`russian` без
`english` добавляет английский перевод через OpenAI API.

ИДЕМПОТЕНТНО: повторный запуск переводит только записи без `english`.
Сохраняет файл после каждого обработанного — прерывание не теряет прогресс.

Запуск:
    set OPENAI_API_KEY=sk-...        (Windows cmd)
    $env:OPENAI_API_KEY="sk-..."     (PowerShell)
    python translate_content_en.py                  # все файлы
    python translate_content_en.py videotheme0.json # один файл
    python translate_content_en.py --dry-run        # только посчитать, без API

Модель и размер батча — константы ниже.
"""

from __future__ import annotations

import glob
import json
import os
import sys
import time

import requests

JSON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videothemes", "json")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"          # дёшево и достаточно для коротких фраз
BATCH_SIZE = 10                # фраз в одном запросе (меньше = меньше дрейфа)
SLEEP_BETWEEN = 0.4            # пауза между запросами, сек

# Какие файлы обрабатывать (банки фраз korean/russian).
TARGET_GLOBS = ["videotheme*.json", "begginer.json", "intermediate.json",
                "advanced.json", "levels.json"]


def _iter_entries(data):
    """Отдаёт все dict-записи с korean+russian внутри JSON.

    Поддерживает три раскладки:
      - dict-of-lists (videotheme*.json: {"b1": [{korean,russian}, ...]})
      - list-of-dicts (begginer/intermediate/advanced.json)
      - levels.json: list уровней, у каждого вложенный список `words`
    """
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                for e in v:
                    if isinstance(e, dict) and "korean" in e and "russian" in e:
                        yield e
            elif isinstance(v, dict) and "korean" in v and "russian" in v:
                yield v
    elif isinstance(data, list):
        for e in data:
            if not isinstance(e, dict):
                continue
            if "korean" in e and "russian" in e:
                yield e
            # levels.json: уровень с вложенными словами
            if isinstance(e.get("words"), list):
                for w in e["words"]:
                    if isinstance(w, dict) and "korean" in w and "russian" in w:
                        yield w


def _translate_batch(items, api_key):
    """items — список (korean, russian). Возвращает список english той же длины
    и порядка.

    Модель эхо-возвращает корейский рядом с переводом — скрипт сверяет, что
    result[i].ko совпадает с items[i].korean. Если модель потеряла/сдвинула
    элементы, эхо не сойдётся → ValueError → вызывающий код уходит в пофразный
    фолбэк. Это защищает от тихого рассинхрона батча."""
    payload_items = [{"i": idx, "ko": k, "ru": r} for idx, (k, r) in enumerate(items)]
    system = (
        "You translate short Korean phrases from K-dramas into natural, "
        "conversational English. The `ru` field is a Russian reference for "
        "meaning/register — do NOT translate from Russian, translate the Korean `ko`. "
        "Keep it short and spoken. "
        "Reply ONLY with JSON: {\"items\": [{\"i\": <same index>, \"ko\": \"<echo the EXACT input ko>\", "
        "\"en\": \"<english translation>\"}, ...]}. "
        "Return exactly one object per input, in the same order, echoing `i` and `ko` verbatim."
    )
    user = json.dumps({"items": payload_items}, ensure_ascii=False)
    resp = requests.post(
        OPENAI_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        },
        timeout=60,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].strip()
    parsed = json.loads(content)

    # Достаём список объектов {i, ko, en}
    rows = None
    if isinstance(parsed, dict):
        for key in ("items", "translations", "result", "data"):
            if isinstance(parsed.get(key), list):
                rows = parsed[key]
                break
        if rows is None:
            vals = list(parsed.values())
            if len(vals) == 1 and isinstance(vals[0], list):
                rows = vals[0]
    elif isinstance(parsed, list):
        rows = parsed
    if not isinstance(rows, list) or len(rows) != len(items):
        raise ValueError(f"batch shape mismatch: got {len(rows) if isinstance(rows, list) else '?'}, expected {len(items)}")

    # Сверяем выравнивание по эхо корейского. Сначала пробуем по полю `i`,
    # иначе позиционно. Если хоть один `ko` не совпал с входным — рассинхрон.
    out = [None] * len(items)
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("batch row is not an object")
        idx = row.get("i")
        if not isinstance(idx, int) or not (0 <= idx < len(items)):
            raise ValueError("batch row missing/bad index")
        if (row.get("ko") or "").strip() != items[idx][0].strip():
            raise ValueError("batch echo mismatch — possible drift")
        out[idx] = str(row.get("en", "")).strip()
    if any(v is None or v == "" for v in out):
        raise ValueError("batch has empty/missing translations")
    return out


def process_file(path, api_key, dry_run=False, reset=False):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if reset:
        # Полная перетрансляция: сбрасываем все english.
        for e in _iter_entries(data):
            e.pop("english", None)

    pending = [e for e in _iter_entries(data) if not e.get("english")]
    name = os.path.basename(path)
    if not pending:
        print(f"  {name}: всё переведено, пропуск")
        return 0
    if dry_run:
        print(f"  {name}: {len(pending)} фраз к переводу")
        return len(pending)

    done = 0
    for start in range(0, len(pending), BATCH_SIZE):
        chunk = pending[start:start + BATCH_SIZE]
        pairs = [(e["korean"], e["russian"]) for e in chunk]
        try:
            translations = _translate_batch(pairs, api_key)
            for entry, en in zip(chunk, translations):
                entry["english"] = en
            done += len(chunk)
        except Exception as ex:
            # Батч не разобрался (модель теряет элементы / кривой JSON) —
            # фолбэк: переводим по одной фразе, тут mismatch невозможен.
            print(f"  {name}: батч {start}-{start+len(chunk)} ошибка: {ex} — перевожу по одной")
            fixed = 0
            for entry in chunk:
                try:
                    one = _translate_batch([(entry["korean"], entry["russian"])], api_key)
                    entry["english"] = one[0]
                    fixed += 1
                except Exception as ex2:
                    print(f"    пропуск '{entry['korean'][:30]}': {ex2}")
                time.sleep(SLEEP_BETWEEN)
            done += fixed
        # сохраняем после каждого батча — прерывание не теряет прогресс
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  {name}: {done}/{len(pending)}")
        time.sleep(SLEEP_BETWEEN)

    return done


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv
    reset = "--reset" in sys.argv

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key and not dry_run:
        print("ERROR: переменная OPENAI_API_KEY не задана.")
        sys.exit(1)

    if args:
        files = [os.path.join(JSON_DIR, a) for a in args]
    else:
        files = []
        for pattern in TARGET_GLOBS:
            files.extend(sorted(glob.glob(os.path.join(JSON_DIR, pattern))))
        files = sorted(set(files))

    if reset:
        print("РЕЖИМ --reset: все english будут сброшены и переведены заново.\n")

    total = 0
    for path in files:
        if not os.path.exists(path):
            print(f"  SKIP (нет файла): {path}")
            continue
        total += process_file(path, api_key, dry_run=dry_run, reset=reset)

    verb = "к переводу" if dry_run else "переведено"
    print(f"\nИТОГО {verb}: {total} фраз.")


if __name__ == "__main__":
    main()

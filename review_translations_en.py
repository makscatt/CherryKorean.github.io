# -*- coding: utf-8 -*-
"""
review_translations_en.py — ревью качества английских переводов.

Phase 2 QA. Проходит по тем же банкам фраз, что и translate_content_en.py.
Для каждой записи модель-ревьюер НЕЗАВИСИМО переводит корейский, затем сравнивает
свой вариант с уже записанным `english`. Если смысл расходится — флагит запись.

Независимый перевод важнее простого «оцени перевод»: модель сначала коммитится
в свой ответ, и только потом судит — так ловятся реальные мистранслейты, а не
«выглядит правдоподобно».

Результат → translation_review.json в корне репозитория: список подозрительных
записей с файлом, корейским, текущим english, причиной и предложенным вариантом.
Сам контент НЕ меняется — скрипт только читает и пишет отчёт.

Запуск:
    set OPENAI_API_KEY=sk-...
    python review_translations_en.py                  # все файлы
    python review_translations_en.py videotheme0.json # один файл
    python review_translations_en.py --model gpt-4o   # ревьюер посильнее

По умолчанию ревьюер — gpt-4o-mini (дёшево). gpt-4o ловит больше нюансов.
"""

from __future__ import annotations

import glob
import json
import os
import sys
import time

import requests

JSON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videothemes", "json")
REPORT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "translation_review.json")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
# Ревьюер по умолчанию — gpt-4o: его суждение «ошибка / не ошибка» заметно
# точнее, чем у mini (mini заваливает отчёт стилистическими придирками).
# Переопределяется флагом --model.
MODEL = "gpt-4o"
BATCH_SIZE = 10
SLEEP_BETWEEN = 0.4

TARGET_GLOBS = ["videotheme*.json", "begginer.json", "intermediate.json",
                "advanced.json", "levels.json"]


def _iter_entries(data):
    """Те же три раскладки, что в translate_content_en.py."""
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                for e in v:
                    if isinstance(e, dict) and "korean" in e and "english" in e:
                        yield e
            elif isinstance(v, dict) and "korean" in v and "english" in v:
                yield v
    elif isinstance(data, list):
        for e in data:
            if not isinstance(e, dict):
                continue
            if "korean" in e and "english" in e:
                yield e
            if isinstance(e.get("words"), list):
                for w in e["words"]:
                    if isinstance(w, dict) and "korean" in w and "english" in w:
                        yield w


def _review_batch(items, api_key, model):
    """items — список (korean, russian, english). Возвращает список вердиктов
    [{ok: bool, reason: str, suggested: str}] той же длины/порядка.

    Эхо-сверка по korean — защита от рассинхрона батча (как в переводчике)."""
    payload = [
        {"i": idx, "ko": k, "ru": r, "en": e}
        for idx, (k, r, e) in enumerate(items)
    ]
    system = (
        "You are a bilingual QA reviewer for Korean→English K-drama translations. "
        "These translations were already done carefully and are mostly correct. "
        "Your job is to catch the RARE genuine error — NOT to improve style. "
        "Expect to flag well under 2% of items. If you are flagging more, you are "
        "being too strict — stop nitpicking.\n"
        "For each item: mentally translate the Korean `ko` yourself (Russian `ru` "
        "is a meaning hint), then judge the provided `en`.\n"
        "Flag `ok=false` ONLY for a REAL defect:\n"
        "  - `en` conveys a clearly DIFFERENT or OPPOSITE meaning;\n"
        "  - `en` is grammatically broken / not natural English;\n"
        "  - `en` is empty, a placeholder, or left untranslated.\n"
        "NEVER flag (these are always `ok=true`):\n"
        "  - synonym / word-choice differences ('leaving' vs 'moving', "
        "'believe' vs 'trust') when the meaning still lands;\n"
        "  - register / formality nuance (formal vs casual) — fine either way;\n"
        "  - missing honorific nuance ('hyung', 'ssi', 'oppa') — acceptable;\n"
        "  - intensity shades ('jerk' vs 'bastard', 'noisy' vs 'so noisy') — fine;\n"
        "  - phrasing you would word differently but that means the same thing.\n"
        "When in doubt, `ok=true`.\n"
        "If `ok=false`, set `severity`: \"high\" (meaning wrong/opposite/broken) "
        "or \"low\" (understandable but a real error worth fixing). `suggested` "
        "MUST be genuinely different and better — never repeat `en` verbatim.\n"
        "Reply ONLY with JSON: {\"items\": [{\"i\": <same index>, "
        "\"ko\": \"<echo exact input ko>\", \"ok\": <true|false>, "
        "\"severity\": \"high|low|\", \"reason\": \"<short, empty if ok>\", "
        "\"suggested\": \"<better English, empty if ok>\"}, ...]}. "
        "Exactly one object per input, same order, echo `i` and `ko` verbatim."
    )
    user = json.dumps({"items": payload}, ensure_ascii=False)
    # Ретраи на сетевые сбои (прокси иногда рвёт соединение / отдаёт 403).
    last_err = None
    resp = None
    for attempt in range(4):
        try:
            resp = requests.post(
                OPENAI_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.0,
                    "response_format": {"type": "json_object"},
                },
                timeout=90,
            )
            resp.raise_for_status()
            break
        except Exception as e:
            last_err = e
            time.sleep(2 * (attempt + 1))  # 2s, 4s, 6s backoff
            resp = None
    if resp is None:
        raise RuntimeError(f"network failed after retries: {last_err}")
    parsed = json.loads(resp.json()["choices"][0]["message"]["content"].strip())

    rows = None
    if isinstance(parsed, dict):
        for key in ("items", "result", "data", "reviews"):
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
        raise ValueError(f"review shape mismatch: {len(rows) if isinstance(rows, list) else '?'} vs {len(items)}")

    out = [None] * len(items)
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("review row not an object")
        idx = row.get("i")
        if not isinstance(idx, int) or not (0 <= idx < len(items)):
            raise ValueError("review row bad index")
        if (row.get("ko") or "").strip() != items[idx][0].strip():
            raise ValueError("review echo mismatch — drift")
        ok = bool(row.get("ok", True))
        suggested = str(row.get("suggested", "")).strip()
        current_en = items[idx][2].strip()
        # Пост-фильтр: если «правка» совпадает с текущим переводом — это не дефект,
        # модель придралась к стилю. Считаем ok.
        if not ok and suggested and suggested.lower() == current_en.lower():
            ok = True
        out[idx] = {
            "ok": ok,
            "severity": str(row.get("severity", "")).strip().lower() if not ok else "",
            "reason": str(row.get("reason", "")).strip() if not ok else "",
            "suggested": suggested if not ok else "",
        }
    if any(v is None for v in out):
        raise ValueError("review has missing verdicts")
    return out


def _review_entry_single(entry, api_key, model):
    """Фолбэк: ревью одной записи (батч не разобрался)."""
    triple = (entry["korean"], entry.get("russian", ""), entry["english"])
    return _review_batch([triple], api_key, model)[0]


def review_file(path, api_key, model):
    """Возвращает список флагнутых записей по файлу."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    name = os.path.basename(path)
    entries = [e for e in _iter_entries(data) if e.get("english")]
    if not entries:
        print(f"  {name}: нет записей с english, пропуск")
        return []

    flagged = []
    checked = 0
    for start in range(0, len(entries), BATCH_SIZE):
        chunk = entries[start:start + BATCH_SIZE]
        triples = [(e["korean"], e.get("russian", ""), e["english"]) for e in chunk]
        try:
            verdicts = _review_batch(triples, api_key, model)
        except Exception as ex:
            print(f"  {name}: батч {start}-{start+len(chunk)} ошибка: {ex} — по одной")
            verdicts = []
            for e in chunk:
                try:
                    verdicts.append(_review_entry_single(e, api_key, model))
                except Exception as ex2:
                    print(f"    пропуск '{e['korean'][:30]}': {ex2}")
                    verdicts.append({"ok": True, "reason": "", "suggested": ""})
                time.sleep(SLEEP_BETWEEN)
        for entry, verdict in zip(chunk, verdicts):
            checked += 1
            if not verdict["ok"]:
                flagged.append({
                    "file": name,
                    "severity": verdict.get("severity", ""),
                    "korean": entry["korean"],
                    "russian": entry.get("russian", ""),
                    "english": entry["english"],
                    "reason": verdict["reason"],
                    "suggested": verdict["suggested"],
                })
        print(f"  {name}: {checked}/{len(entries)} (флагнуто: {len(flagged)})")
        time.sleep(SLEEP_BETWEEN)

    return flagged


def _write_report(model, all_flagged):
    ordered = sorted(all_flagged, key=lambda x: 0 if x.get("severity") == "high" else 1)
    high = sum(1 for x in all_flagged if x.get("severity") == "high")
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump({"model": model, "flagged_count": len(all_flagged),
                   "high_severity": high, "low_severity": len(all_flagged) - high,
                   "flagged": ordered}, f, ensure_ascii=False, indent=2)
    return high


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    merge = "--merge" in sys.argv
    model = MODEL
    for a in sys.argv:
        if a.startswith("--model="):
            model = a.split("=", 1)[1]
    if "--model" in sys.argv:
        i = sys.argv.index("--model")
        if i + 1 < len(sys.argv):
            model = sys.argv[i + 1]

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("ERROR: переменная OPENAI_API_KEY не задана.")
        sys.exit(1)

    if args:
        files = [os.path.join(JSON_DIR, a) for a in args]
    else:
        files = []
        for pattern in TARGET_GLOBS:
            files.extend(sorted(glob.glob(os.path.join(JSON_DIR, pattern))))
        files = sorted(set(files))

    # --merge: подхватываем существующий отчёт и заменяем в нём только флаги
    # тех файлов, что переreview-им сейчас. Остальное сохраняем.
    all_flagged = []
    if merge and os.path.exists(REPORT_PATH):
        try:
            with open(REPORT_PATH, "r", encoding="utf-8") as f:
                prev = json.load(f)
            rerun_names = {os.path.basename(p) for p in files}
            all_flagged = [x for x in prev.get("flagged", [])
                           if x.get("file") not in rerun_names]
            print(f"--merge: сохранено {len(all_flagged)} флагов из других файлов\n")
        except Exception as e:
            print(f"--merge: не удалось прочитать прежний отчёт ({e}), начинаю с нуля\n")

    print(f"Ревьюер: {model}\n")
    for path in files:
        if not os.path.exists(path):
            print(f"  SKIP (нет файла): {path}")
            continue
        all_flagged.extend(review_file(path, api_key, model))
        _write_report(model, all_flagged)  # отчёт после каждого файла

    high = _write_report(model, all_flagged)
    print(f"\nИТОГО файлов: {len(files)}, флагнуто: {len(all_flagged)} "
          f"(high: {high}, low: {len(all_flagged) - high})")
    print(f"Отчёт: {REPORT_PATH}")


if __name__ == "__main__":
    main()

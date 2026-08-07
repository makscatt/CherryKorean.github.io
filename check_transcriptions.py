#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_transcriptions.py — аудит русских транскрипций в videothemes/**/*.json

Ищет места, где в поле "transcription" НЕ отражено обязательное позиционное
изменение корейского чтения (ассимиляция). Раскладывает "korean" на джамо и
проверяет пары «батчим + начальный согласный» следующего слога.

Классы правил:
  A  비음화   ㅁ/ㅇ + ㄹ            → ㄹ читается ㄴ   (음력 → 음녁, «ымнёк»)
  B  비음화   ㄱ/ㄷ/ㅂ + ㄹ         → ㄴ + ㄴ/ㅁ        (국립 → 궁닙)
  C  비음화   ㄱ/ㄷ/ㅂ + ㄴ/ㅁ      → ㅇ/ㄴ/ㅁ          (입니다 → 임니다)
  D  유음화   ㄴ+ㄹ / ㄹ+ㄴ / ㄹ+ㄹ  → ㄹㄹ             (연락 → 열락, «ёлляк»)
  E  구개음화 ㄷ/ㅌ + 이            → 지/치            (같이 → 가치, «качи»)
  F  ㅎ-батчим (ㅎ/ㄶ/ㅀ) + гласная → ㅎ выпадает      (많아 → 마나, «мана»)
     ㅎ-батчим + ㄱ/ㄷ/ㅈ           → аспирация        (많고 → 만코, «манко»)

НЕ ошибка (и не флагуется): ㅎ как НАЧАЛЬНЫЙ звук после сонорного —
전화 «чонхва», 말해 «мальхэ», 은행 «ынхэң», 열심히 «ёльщимхи».

Запуск из корня репо:
    python check_transcriptions.py            # только проблемные
    python check_transcriptions.py --all      # + сводка по файлам
Код возврата: 0 — чисто, 1 — есть находки.
"""

import glob
import json
import os
import re
import sys

LEAD = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
TAIL = ["", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ",
        "ㄽ", "ㄾ", "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ", "ㅆ", "ㅇ", "ㅈ",
        "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]

VOWEL_I = 20  # ㅣ — индекс гласной в наборе, нужен для 구개음화


def decompose(ch):
    """'음' -> ('ㅇ', vowel_idx, 'ㅁ'); не-хангыль -> None."""
    code = ord(ch) - 0xAC00
    if 0 <= code < 11172:
        return LEAD[code // 588], (code % 588) // 28, TAIL[code % 28]
    return None


def coda_class(tail):
    """Представительный звук батчима."""
    if tail in ("ㄱ", "ㄲ", "ㅋ", "ㄳ", "ㄺ"):
        return "K"
    if tail in ("ㄷ", "ㅅ", "ㅆ", "ㅈ", "ㅊ", "ㅌ"):
        return "T"
    if tail in ("ㅂ", "ㅍ", "ㅄ", "ㄼ", "ㄿ"):
        return "P"
    if tail in ("ㅁ", "ㄻ"):
        return "M"
    if tail in ("ㄴ", "ㄵ"):
        return "N"
    if tail == "ㅇ":
        return "NG"
    if tail in ("ㄹ", "ㄽ", "ㄾ"):
        return "L"
    if tail in ("ㅎ", "ㄶ", "ㅀ"):
        return "H"
    return ""


# варианты кириллического написания начального согласного и гласной —
# нужны, чтобы для ㅎ-батчима искать «х» именно в его слоге, а не где угодно
# в фразе (иначе 전화 «чонхва» ловится как ошибка).
LEAD_CYR = {
    "ㄱ": ("к", "г"), "ㄲ": ("кк",), "ㄴ": ("н",), "ㄷ": ("т", "д"),
    "ㄸ": ("тт",), "ㄹ": ("р", "л"), "ㅁ": ("м",), "ㅂ": ("п", "б"),
    "ㅃ": ("пп",), "ㅅ": ("с", "щ"), "ㅆ": ("сс", "щщ"), "ㅇ": ("",),
    "ㅈ": ("ч", "чж"), "ㅉ": ("чч", "ччж"), "ㅊ": ("чх", "ч"),
    "ㅋ": ("кх", "к"), "ㅌ": ("тх", "т"), "ㅍ": ("пх", "п"), "ㅎ": ("х",),
}
VOWEL_CYR = [
    ("а", "я"), ("э", "е"), ("я",), ("е", "э"), ("о", "ё"), ("э", "е"),
    ("ё",), ("е", "э"), ("о",), ("ва",), ("вэ", "ве"), ("вэ", "ве"),
    ("ё",), ("у",), ("во",), ("вэ", "ве"), ("ви",), ("ю",), ("ы",),
    ("ый", "и", "ы"), ("и",),
]

# как батчим обычно пишут кириллицей в этом проекте (варианты написания)
CODA_CYR = {
    "K": ("к", "г"),
    "T": ("т", "с", "д", "ч", "щ"),
    "P": ("п", "б"),
    "M": ("м",),
    "N": ("н",),
    "NG": ("нг", "ң", "н"),
    "L": ("ль", "л"),
}


def walk(obj):
    """Все словари с ключом 'korean' на любой глубине."""
    if isinstance(obj, dict):
        if "korean" in obj:
            yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)


def check_entry(korean, transcription):
    """Список сработавших правил: [(код, пояснение, найденная подстрока)]."""
    t = (transcription or "").lower()
    if not t:
        return []
    found = []

    for i in range(len(korean) - 1):
        a, b = decompose(korean[i]), decompose(korean[i + 1])
        if not a or not b:
            continue
        coda, lead, vowel = coda_class(a[2]), b[0], b[1]

        # --- F: ㅎ-батчим ---
        if coda == "H":
            # собираем, как выглядел бы САМ этот слог с непроизносимым ㅎ:
            # 많 → «манх», 싫 → «щильх», 잃 → «ильх»
            tail_cyr = "н" if a[2] in ("ㄶ", "ㅎ") else "ль"
            frags = [ld + vw + tail_cyr + "х"
                     for ld in LEAD_CYR.get(a[0], ("",))
                     for vw in VOWEL_CYR[a[1]]]
            hit = next((f for f in frags if f in t), None)
            if hit:
                if lead == "ㅇ":
                    found.append(("F ㅎ-батчим + гласная → ㅎ выпадает", hit))
                else:
                    found.append(("F ㅎ-батчим + согласный → аспирация/ㄴ", hit))
            continue

        if not coda:
            continue

        # --- A/B/D: следующий начальный ㄹ ---
        if lead == "ㄹ":
            for cv in CODA_CYR.get(coda, ()):
                if cv + "р" in t:
                    if coda in ("M", "NG"):
                        rule = "A ㅁ/ㅇ + ㄹ → ㄴ"
                    elif coda in ("K", "T", "P"):
                        rule = "B 폐쇄음 + ㄹ → ㄴㄴ/ㅁㄴ"
                    elif coda == "N":
                        rule = "D 유음화 ㄴ + ㄹ → ㄹㄹ"
                    else:
                        rule = "D ㄹ + ㄹ → ㄹㄹ (лл, не «льр»)"
                    found.append((rule, cv + "р"))
                    break

        # --- C: 비음화 перед ㄴ/ㅁ ---
        elif lead in ("ㄴ", "ㅁ"):
            cl = "н" if lead == "ㄴ" else "м"
            if coda in ("K", "T", "P"):
                for cv in CODA_CYR[coda]:
                    if cv + cl in t:
                        found.append(("C 비음화 폐쇄음 + ㄴ/ㅁ", cv + cl))
                        break
            elif coda == "L" and lead == "ㄴ":
                for cv in CODA_CYR["L"]:
                    if cv + "н" in t:
                        found.append(("D 유음화 ㄹ + ㄴ → ㄹㄹ", cv + "н"))
                        break

        # --- E: 구개음화 ---
        if a[2] in ("ㄷ", "ㅌ") and lead == "ㅇ" and vowel == VOWEL_I:
            for bad in ("ти", "тхи", "тьи"):
                if bad in t:
                    found.append(("E 구개음화 ㄷ/ㅌ + 이 → 지/치", bad))
                    break

    # схлопнуть дубли правил внутри одной фразы
    seen, uniq = set(), []
    for rule, frag in found:
        if rule in seen:
            continue
        seen.add(rule)
        uniq.append((rule, frag))
    return uniq


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    show_all = "--all" in sys.argv

    files = sorted(glob.glob("videothemes/**/*.json", recursive=True))
    total, flagged = 0, []

    for path in files:
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as exc:
            print(f"!! не читается {path}: {exc}")
            continue
        for item in walk(data):
            tr = item.get("transcription")
            if not tr:
                continue
            total += 1
            hits = check_entry(item.get("korean") or "", tr)
            for rule, frag in hits:
                flagged.append((path, item.get("korean", ""), tr, rule, frag))

    for path, kor, tr, rule, frag in flagged:
        print(f"{rule:34} | {kor[:32]:32} | {tr[:36]:36} | [{frag}] | {path}")

    if show_all:
        per_file = {}
        for path, *_ in flagged:
            per_file[path] = per_file.get(path, 0) + 1
        print("\n--- по файлам ---")
        for path, cnt in sorted(per_file.items()):
            print(f"   {cnt:3}  {path}")

    print(f"\nпроверено транскрипций: {total}; находок: {len(flagged)}")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())

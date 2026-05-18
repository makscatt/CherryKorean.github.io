"""
Нормализация громкости 9 «живых» клипов song1 под единый LUFS.
Двухпроходный ffmpeg loudnorm. Видео остаётся как есть (-c:v copy),
аудио перекодируется (aac для mp4, libopus для webm).
Результат — рядом с оригиналом с суффиксом _norm.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent / "video" / "song1"
TARGET_I = -14.0       # LUFS — стриминговый стандарт
TARGET_TP = -1.5       # dBTP — запас от клиппинга
TARGET_LRA = 11.0

LIVE_BASE_NAMES = [
    "나는 내가 빛나는 별인 줄 알았어요",
    "몰랐어요 난 내가 벌레라는 것을",
    "그래도 괜찮아 난 눈부시니까",
    "하늘에서 떨어진 별인 줄 알았어요",
    "소원을 들어주는 작은 별",
    "한 번도 의심한 적 없었죠",
    "한참 동안 찾았던 내 손톱",
    "하늘로 올라가 초승달 돼 버렸지",
    "누가 저기 걸어놨어 누가 저기 걸어놨어",
]


def measure(src: Path) -> dict:
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(src),
        "-af", f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json",
        "-f", "null", "-",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    stderr = p.stderr
    m = re.search(r"\{[\s\S]*?\}", stderr.split("Parsed_loudnorm")[-1])
    if not m:
        raise RuntimeError(f"loudnorm JSON not found for {src.name}\n{stderr[-500:]}")
    return json.loads(m.group(0))


def apply(src: Path, dst: Path, meas: dict, audio_codec: str, audio_bitrate: str):
    af = (
        f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}"
        f":measured_I={meas['input_i']}"
        f":measured_TP={meas['input_tp']}"
        f":measured_LRA={meas['input_lra']}"
        f":measured_thresh={meas['input_thresh']}"
        f":offset={meas['target_offset']}"
        f":linear=true:print_format=summary"
    )
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats", "-y", "-i", str(src),
        "-af", af, "-ar", "48000",
        "-c:v", "copy", "-c:a", audio_codec, "-b:a", audio_bitrate,
        str(dst),
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed for {src.name}\n{p.stderr[-800:]}")


def process_one(base: str):
    mp4_src  = ROOT / "mp4"  / f"{base}.mp4"
    webm_src = ROOT          / f"{base}.webm"
    if not mp4_src.exists():
        print(f"  [skip mp4]  {mp4_src.name}: not found")
    else:
        print(f"  mp4 measure...", end=" ", flush=True)
        m = measure(mp4_src)
        dst = mp4_src.with_name(f"{base}_norm.mp4")
        print(f"in_i={m['input_i']} → apply...", end=" ", flush=True)
        apply(mp4_src, dst, m, "aac", "192k")
        print(f"OK → {dst.name}")
    if not webm_src.exists():
        print(f"  [skip webm] {webm_src.name}: not found")
    else:
        print(f"  webm measure...", end=" ", flush=True)
        m = measure(webm_src)
        dst = webm_src.with_name(f"{base}_norm.webm")
        print(f"in_i={m['input_i']} → apply...", end=" ", flush=True)
        apply(webm_src, dst, m, "libopus", "96k")
        print(f"OK → {dst.name}")


def main():
    print(f"Target: I={TARGET_I} LUFS, TP={TARGET_TP} dBTP, LRA={TARGET_LRA}")
    print(f"Root:   {ROOT}")
    print()
    for i, base in enumerate(LIVE_BASE_NAMES, 1):
        print(f"[{i}/{len(LIVE_BASE_NAMES)}] {base}")
        process_one(base)
        print()
    print("Done.")


if __name__ == "__main__":
    sys.exit(main())

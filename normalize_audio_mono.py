"""
Mono dual-channel downmix для уже опубликованных видео темы в TG mini app.
Видео copy, аудио перекодируется с pan-фильтром (одинаковый сигнал в L и R)
для фикса phase cancellation на мобильных плеерах при multichannel / matrix-stereo
источниках (например DSNP-рипы с Lt/Rt или 5.1).

Использование:
    python normalize_audio_mono.py <theme_folder>   # например: wfools
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent / "video"

PAN_FILTER = (
    "pan=stereo"
    "|c0=0.5*FL+0.5*FR+0.707*FC+0.5*BL+0.5*BR"
    "|c1=0.5*FL+0.5*FR+0.707*FC+0.5*BL+0.5*BR"
)


def process(src: Path, audio_codec: str, audio_bitrate: str) -> None:
    tmp = src.with_name(f"~tmp~{src.name}")
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats", "-y", "-i", str(src),
        "-af", PAN_FILTER,
        "-c:v", "copy",
        "-c:a", audio_codec, "-b:a", audio_bitrate,
        str(tmp),
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        raise RuntimeError(f"ffmpeg failed for {src.name}\n{p.stderr[-800:]}")
    os.replace(tmp, src)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("theme", help="theme folder name under video/, e.g. wfools")
    args = ap.parse_args()

    theme_dir = ROOT / args.theme
    if not theme_dir.is_dir():
        print(f"Not found: {theme_dir}", file=sys.stderr)
        return 2

    webms = sorted(theme_dir.glob("*.webm"))
    mp4_dir = theme_dir / "mp4"
    mp4s = sorted(mp4_dir.glob("*.mp4")) if mp4_dir.is_dir() else []

    total = len(webms) + len(mp4s)
    print(f"Theme: {args.theme}  webm: {len(webms)}  mp4: {len(mp4s)}  total: {total}", flush=True)

    done = 0
    failed: list[tuple[Path, str]] = []

    for f in webms:
        done += 1
        print(f"[{done}/{total}] webm  {f.name}", flush=True)
        try:
            process(f, "libopus", "128k")
        except RuntimeError as e:
            print(f"  FAIL: {e}", flush=True)
            failed.append((f, str(e)))

    for f in mp4s:
        done += 1
        print(f"[{done}/{total}] mp4   {f.name}", flush=True)
        try:
            process(f, "aac", "192k")
        except RuntimeError as e:
            print(f"  FAIL: {e}", flush=True)
            failed.append((f, str(e)))

    if failed:
        print(f"\nDone with {len(failed)} failures:", flush=True)
        for f, _ in failed:
            print(f"  {f}", flush=True)
        return 1
    print("\nDone.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

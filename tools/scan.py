#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["numpy>=1.26", "scipy>=1.11", "soundfile>=0.12", "librosa>=0.10"]
# ///
"""音を一定の長さで区切って特徴を表にする。弾き方（スラップ・指弾きなど）や場面の境目を探すのに使う。

使い方:
  tools/scan.py output/<曲>/bass.wav [--start 20 --end 40] [--window 2]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from analyze import analyze, load_mono  # noqa: E402


def fmt(v, w: int = 6, p: int = 1) -> str:
    return f"{v:{w}.{p}f}" if v is not None else " " * (w - 1) + "-"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("wav", type=Path)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float)
    ap.add_argument("--window", type=float, default=2.0, help="区切る長さ（秒）")
    ap.add_argument("--instrument", choices=["bass", "guitar"], default="bass")
    a = ap.parse_args(argv)

    x, sr = load_mono(a.wav)
    end = len(x) / sr if a.end is None else min(a.end, len(x) / sr)
    print("区間            rms  crest centroid  upperH low_mid    mid hi_mid   high  range  decay")
    t = a.start
    while t + a.window <= end + 1e-6:
        s = x[int(t * sr):int((t + a.window) * sr)]
        label = f"{int(t // 60)}:{t % 60:04.1f}-{int((t + a.window) // 60)}:{(t + a.window) % 60:04.1f}"
        if np.sqrt(np.mean(s**2)) < 1e-3:
            print(f"{label}  （無音）")
        else:
            f = analyze(s, sr, a.instrument)
            b = f["bands_db"]
            print(f"{label} {fmt(f['level']['rms_dbfs'])} {fmt(f['level']['crest_factor_db'])} "
                  f"{fmt(f['brightness']['centroid_hz'], 8, 0)} {fmt(f['distortion']['upper_harmonic_db'], 7)} "
                  f"{fmt(b['low_mid'], 7)} {fmt(b['mid'])} {fmt(b['high_mid'])} {fmt(b['high'])} "
                  f"{fmt(f['dynamics']['range_p95_p10_db'])} {fmt(f['dynamics']['decay_db_per_sec'])}")
        t += a.window
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["numpy>=1.26", "scipy>=1.11", "soundfile>=0.12", "librosa>=0.10"]
# ///
"""stem（ベース／ギター）の音色の特徴を測って features.json にする。

時間で平均した「音色」を測る（波形やフレーズは比べない）。各値の意味と読み方は
knowledge/gx/mapping.md にある。

使い方:
  tools/analyze.py output/<曲>/bass.wav [-o features.json] [--instrument bass|guitar]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

# 帯域（Hz）。ベースの EQ（BASS / MIDDLE / TREBLE、PARA.EQ）を考える単位。
BANDS = {
    "bass": {
        "sub": (30, 60),
        "low": (60, 250),
        "low_mid": (250, 800),
        "mid": (800, 2000),
        "high_mid": (2000, 5000),
        "high": (5000, 10000),
    },
    "guitar": {
        "low": (80, 250),
        "low_mid": (250, 800),
        "mid": (800, 2000),
        "high_mid": (2000, 5000),
        "presence": (5000, 8000),
        "high": (8000, 12000),
    },
}
F0_RANGE = {"bass": (30.0, 400.0), "guitar": (75.0, 1000.0)}

FRAME = 4096
HOP = 1024
SILENCE_DB = -45.0  # 最大のフレームからこれより小さいフレームは無音として除く


def load_mono(path: Path) -> tuple[np.ndarray, int]:
    x, sr = sf.read(str(path), dtype="float32", always_2d=True)
    return x.mean(axis=1), sr


def frame_rms_db(x: np.ndarray) -> np.ndarray:
    import librosa

    rms = librosa.feature.rms(y=x, frame_length=FRAME, hop_length=HOP)[0]
    return 20 * np.log10(rms + 1e-12)


def active_mask(rms_db: np.ndarray) -> np.ndarray:
    return rms_db > (rms_db.max() + SILENCE_DB)


def band_levels(S_pow: np.ndarray, freqs: np.ndarray, bands: dict) -> dict:
    """帯域ごとのエネルギーを、全帯域の合計に対する dB で返す。"""
    total = S_pow.sum() + 1e-20
    out = {}
    for name, (lo, hi) in bands.items():
        sel = (freqs >= lo) & (freqs < hi)
        out[name] = round(float(10 * np.log10(S_pow[sel].sum() / total + 1e-20)), 2)
    return out


def harmonic_distortion(x: np.ndarray, sr: int, fmin: float, fmax: float) -> dict:
    """歪みの量。基音が安定しているフレームで、倍音のエネルギーの比を測る。

    - upper_harmonic_db: 4〜10 次 ÷ 1〜3 次。**歪みの量の主な目安**。弦の音は元から 2・3 次が
      強いが、4 次より上は歪ませると大きく増える（クリーンでは小さい）
    - harmonic_ratio_db: 2〜10 次 ÷ 基音。参考（歪ませると 2・3 次が潰れて下がることもある）
    - odd_even_ratio_db: 奇数次 ÷ 偶数次。大きいほど対称な（ハードな）クリップ寄り
    絶対値ではなく、同じ楽器の音どうしで比べる。
    """
    import librosa

    f0, voiced, _ = librosa.pyin(x, fmin=fmin, fmax=fmax, sr=sr, frame_length=FRAME, hop_length=HOP)
    S = np.abs(librosa.stft(x, n_fft=FRAME, hop_length=HOP)) ** 2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=FRAME)
    n = min(S.shape[1], len(f0))
    ratios, uppers, odd_even = [], [], []
    bin_hz = sr / FRAME
    for t in range(n):
        if not voiced[t] or not np.isfinite(f0[t]):
            continue
        def energy(h: int) -> float:
            fc = f0[t] * h
            if fc >= sr / 2:
                return 0.0
            sel = np.abs(freqs - fc) <= max(bin_hz * 1.5, fc * 0.03)
            return float(S[sel, t].sum())
        e = [energy(h) for h in range(1, 11)]
        if e[0] <= 0:
            continue
        ratios.append(sum(e[1:]) / e[0])
        uppers.append(sum(e[3:]) / (sum(e[:3]) + 1e-20))
        even = sum(e[1::2])  # 2,4,6,8,10 次
        odd = sum(e[2::2])  # 3,5,7,9 次
        if even > 0:
            odd_even.append(odd / even)
    if not ratios:
        return {"upper_harmonic_db": None, "harmonic_ratio_db": None, "odd_even_ratio_db": None, "voiced_frames": 0}
    return {
        "upper_harmonic_db": round(float(10 * np.log10(np.median(uppers) + 1e-12)), 2),
        "harmonic_ratio_db": round(float(10 * np.log10(np.median(ratios) + 1e-12)), 2),
        "odd_even_ratio_db": round(float(10 * np.log10(np.median(odd_even) + 1e-12)), 2) if odd_even else None,
        "voiced_frames": len(ratios),
    }


def decay_rate(rms_db: np.ndarray, sr: int) -> float | None:
    """音の減り方（dB/秒、負の値）。ピークから次の立ち上がりまでの傾きの中央値。

    ベースの自然な減衰に、コンプ（減りが遅い）や残響（尾が伸びる）が重なった値。
    """
    import scipy.signal as ss

    peaks, _ = ss.find_peaks(rms_db, prominence=6, distance=4)
    slopes = []
    for i, p in enumerate(peaks):
        end = peaks[i + 1] if i + 1 < len(peaks) else len(rms_db)
        seg = rms_db[p:end]
        if len(seg) < 6:
            continue
        seg = seg[: max(6, int(np.argmin(seg)) + 1)]
        t = np.arange(len(seg)) * HOP / sr
        slopes.append(np.polyfit(t, seg, 1)[0])
    return round(float(np.median(slopes)), 2) if slopes else None


def analyze(x: np.ndarray, sr: int, instrument: str = "bass") -> dict:
    import librosa

    rms_db = frame_rms_db(x)
    act = active_mask(rms_db)
    S = np.abs(librosa.stft(x, n_fft=FRAME, hop_length=HOP)) ** 2
    m = min(S.shape[1], len(act))
    S_act = S[:, :m][:, act[:m]]
    freqs = librosa.fft_frequencies(sr=sr, n_fft=FRAME)
    spec = S_act.mean(axis=1)

    # 明るさは「鳴っている区間を平均したパワースペクトル」で測る。フレームごとの重心の中央値だと、
    # 小さい音のフレーム（弦のノイズなど）に引っぱられて、ベースでは何 kHz にもなってしまう。
    centroid = float((spec * freqs).sum() / (spec.sum() + 1e-20))
    cum = np.cumsum(spec) / (spec.sum() + 1e-20)
    rolloff = float(freqs[min(int(np.searchsorted(cum, 0.85)), len(freqs) - 1)])
    flatness = librosa.feature.spectral_flatness(S=np.sqrt(S_act))[0]

    xa = x[np.abs(x) > 0]
    peak = float(np.max(np.abs(x))) if len(x) else 0.0
    rms_all = float(np.sqrt(np.mean(x**2))) if len(x) else 0.0
    act_db = rms_db[act]

    fmin, fmax = F0_RANGE[instrument]
    return {
        "instrument": instrument,
        "duration_sec": round(len(x) / sr, 2),
        "sample_rate": sr,
        "active_ratio": round(float(act.mean()), 3),
        "level": {
            "rms_dbfs": round(20 * np.log10(rms_all + 1e-12), 2),
            "peak_dbfs": round(20 * np.log10(peak + 1e-12), 2),
            "crest_factor_db": round(20 * np.log10((peak + 1e-12) / (rms_all + 1e-12)), 2) if len(xa) else None,
        },
        "bands_db": band_levels(spec, freqs, BANDS[instrument]),
        "brightness": {
            "centroid_hz": round(centroid, 1),
            "rolloff85_hz": round(rolloff, 1),
            "flatness": round(float(np.median(flatness)), 5),
        },
        "distortion": harmonic_distortion(x, sr, fmin, fmax),
        "dynamics": {
            # 鳴っているフレームの音量のばらつき。小さいほど音量が揃っている（コンプが強い）
            "range_p95_p10_db": round(float(np.percentile(act_db, 95) - np.percentile(act_db, 10)), 2) if len(act_db) else None,
            "decay_db_per_sec": decay_rate(rms_db, sr),
        },
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("wav", type=Path)
    ap.add_argument("-o", "--out", type=Path, help="書き出す features.json（省略時は wav と同じ場所）")
    ap.add_argument("--instrument", choices=list(BANDS), default="bass")
    a = ap.parse_args(argv)

    x, sr = load_mono(a.wav)
    feats = {"source": str(a.wav), **analyze(x, sr, a.instrument)}
    out = a.out or a.wav.with_name(a.wav.stem + ".features.json")
    out.write_text(json.dumps(feats, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(feats, ensure_ascii=False, indent=2))
    print(f"→ {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

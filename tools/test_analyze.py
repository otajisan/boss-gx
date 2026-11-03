#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["numpy>=1.26", "scipy>=1.11", "soundfile>=0.12", "librosa>=0.10", "pytest>=8"]
# ///
"""analyze.py を合成した音で確かめる。大小の向きが逆にならないことを見る。"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import scipy.signal as ss

sys.path.insert(0, str(Path(__file__).parent))
from analyze import analyze  # noqa: E402

SR = 44100


def plucks(f0: float = 55.0, notes: int = 8, dur: float = 0.5, decay: float = 4.0) -> np.ndarray:
    """弦をはじいたような音（倍音が少しあり、減衰する）を並べる。"""
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-decay * t)
    tone = sum((0.5 ** (h - 1)) * np.sin(2 * np.pi * f0 * h * t) for h in range(1, 4))
    note = (env * tone / 1.75).astype(np.float32)
    return np.tile(note, notes) * 0.5


def test_clipping_raises_distortion():
    clean = plucks()
    driven = np.tanh(clean * 12) / np.tanh(12 * 0.5)
    a, b = analyze(clean, SR), analyze(driven * 0.5, SR)
    assert a["distortion"]["upper_harmonic_db"] + 20 < b["distortion"]["upper_harmonic_db"]


def test_lowpass_is_darker():
    bright = plucks(f0=110.0)
    bright = np.tanh(bright * 6) * 0.5  # 高域まで倍音を出す
    sos = ss.butter(4, 800, "low", fs=SR, output="sos")
    dark = ss.sosfilt(sos, bright).astype(np.float32)
    a, b = analyze(bright, SR), analyze(dark, SR)
    assert b["brightness"]["centroid_hz"] < a["brightness"]["centroid_hz"]
    assert b["bands_db"]["high_mid"] < a["bands_db"]["high_mid"]


def test_compression_narrows_dynamics():
    rng = np.random.default_rng(0)
    gains = rng.uniform(0.1, 1.0, 8)
    note = plucks(notes=1)
    dynamic = np.concatenate([note * g for g in gains])
    squashed = np.concatenate([note * (g ** 0.2) for g in gains])  # 音量差を縮めたもの
    a, b = analyze(dynamic, SR), analyze(squashed, SR)
    assert b["dynamics"]["range_p95_p10_db"] < a["dynamics"]["range_p95_p10_db"]


def test_slow_decay_is_detected():
    fast = analyze(plucks(decay=8.0), SR)["dynamics"]["decay_db_per_sec"]
    slow = analyze(plucks(decay=2.0), SR)["dynamics"]["decay_db_per_sec"]
    assert fast is not None and slow is not None
    assert fast < slow < 0


def test_third_octave_finds_notch():
    """1kHz 付近を削ると、1/3 オクターブでその位置に谷が見える。"""
    rng = np.random.default_rng(1)
    noise = rng.normal(0, 0.1, SR * 3).astype(np.float32)
    sos = ss.butter(2, [700, 1400], "bandstop", fs=SR, output="sos")
    notched = ss.sosfilt(sos, noise).astype(np.float32)
    a, b = analyze(noise, SR)["third_octave_db"], analyze(notched, SR)["third_octave_db"]
    assert a["100"] == 0.0 and b["100"] == 0.0
    assert b["1000"] < a["1000"] - 10
    assert abs(b["4000"] - a["4000"]) < 2


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))

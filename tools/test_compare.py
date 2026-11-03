#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["numpy>=1.26", "scipy>=1.11", "soundfile>=0.12", "librosa>=0.10", "matplotlib>=3.8", "pytest>=8"]
# ///
"""compare.py を合成した音で確かめる。"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import scipy.signal as ss

sys.path.insert(0, str(Path(__file__).parent))
from analyze import analyze  # noqa: E402
from compare import compare_features, format_table, plot  # noqa: E402

SR = 48000


def bassish(seed: int = 0) -> np.ndarray:
    """ベースっぽい音: 倍音のある減衰音を並べ、広い帯域にノイズを少し足す（1/3 オクターブが全部埋まる）。"""
    rng = np.random.default_rng(seed)
    t = np.arange(int(0.5 * SR)) / SR
    notes = []
    for f0 in (55.0, 73.4, 82.4, 65.4, 55.0, 98.0):
        tone = sum((0.6 ** (h - 1)) * np.sin(2 * np.pi * f0 * h * t) for h in range(1, 12))
        notes.append(np.exp(-4 * t) * tone)
    x = np.concatenate(notes)
    x = np.tanh(x * 2) * 0.3 + rng.normal(0, 0.01, len(x))
    return x.astype(np.float32)


@pytest.fixture(scope="module")
def base():
    x = bassish()
    return x, analyze(x, SR)


def test_same_sound_is_zero(base):
    x, f = base
    res = compare_features(f, [("same", f)])
    assert res["candidates"][0]["distance_db"] < 0.05


def test_notch_at_1k_is_far_and_negative(base):
    x, f = base
    sos = ss.butter(2, [800, 1250], "bandstop", fs=SR, output="sos")
    notched = ss.sosfilt(sos, x).astype(np.float32)
    res = compare_features(f, [("notch", analyze(notched, SR)), ("same", f)])
    by = {r["name"]: r for r in res["candidates"]}
    assert res["candidates"][0]["name"] == "same"
    assert by["notch"]["distance_db"] > 2.0
    d = by["notch"]["band_diff_db"]
    assert d["1000"] < -6
    assert d["1000"] == min(d.values())
    assert by["notch"]["worst_bands"][0]["hz"] == 1000.0


def test_volume_only_changes_level_not_distance(base):
    x, f = base
    quiet = analyze((x * 0.5).astype(np.float32), SR)
    res = compare_features(f, [("loud", f), ("quiet", quiet)])
    by = {r["name"]: r for r in res["candidates"]}
    assert by["quiet"]["distance_db"] < 0.1
    assert by["quiet"]["rms_vs_loudest_db"] == pytest.approx(-6.02, abs=0.1)
    assert by["loud"]["rms_vs_loudest_db"] == 0.0


def test_max_hz_limits_bands(base):
    x, f = base
    res = compare_features(f, [("same", f)], max_hz=5000)
    bands = [float(k) for k in res["candidates"][0]["band_diff_db"]]
    assert min(bands) >= 40 and max(bands) == 5000
    assert res["settings"]["norm_range_hz"] == [63.0, 5000.0]


def test_table_and_plot(base, tmp_path):
    x, f = base
    res = compare_features(f, [("U01", f)])
    assert "U01" in format_table(res)
    out = tmp_path / "c.png"
    plot(res, "target", out)
    assert out.stat().st_size > 1000


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q", "-p", "no:cacheprovider"]))


def test_min_hz_excludes_low_bands(base):
    _, f = base
    res = compare_features(f, [("same", f)], min_hz=100)
    assert min(float(k) for k in res["candidates"][0]["band_diff_db"]) >= 100
    assert res["settings"]["norm_range_hz"][0] == 100

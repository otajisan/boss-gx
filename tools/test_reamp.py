#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["numpy>=1.26", "scipy>=1.11", "soundfile>=0.12", "soxr>=0.3", "pytest>=8"]
# ///
"""reamp.py の実機を使わない部分（遅れの検出、送る信号、DI の音量）を確かめる。"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import scipy.signal as ss

sys.path.insert(0, str(Path(__file__).parent))
from reamp import OUT_EFX, SR, build_send, check_di_level, detect_latency, make_pulse  # noqa: E402


def recorded(delay: int, noise_db: float = -80.0, lowpass: float | None = None, gain_db: float = -6.0,
             leading_zeros: int = 0, di_db: float | None = None, seed: int = 0) -> np.ndarray:
    """build_send の信号を delay サンプル遅らせ、フィルタ・ノイズを足した 2ch の「録音」を作る。"""
    rng = np.random.default_rng(seed)
    di = np.zeros(SR, np.float32) if di_db is None else (
        np.sin(2 * np.pi * 55 * np.arange(SR) / SR) * 10 ** (di_db / 20)).astype(np.float32)
    send, _ = build_send(di)
    y = np.concatenate([np.zeros(delay), send[:, OUT_EFX[0]]])[: len(send)] * 10 ** (gain_db / 20)
    if lowpass:
        y = ss.sosfilt(ss.butter(2, lowpass, "low", fs=SR, output="sos"), y)
    y = np.stack([y, y * 0.9], axis=1) + rng.normal(0, 10 ** (noise_db / 20), (len(y), 2))
    y[:leading_zeros] = 0
    return y.astype(np.float32)


@pytest.mark.parametrize("delay", [0, 1, 480, 12499, 30000])
def test_exact_delay(delay):
    assert detect_latency(recorded(delay)) == delay


def test_known_gx_value_with_noise_and_zero_start():
    # 実機の値（12499）。ストリームの先頭がゼロ埋め、ノイズの多いパッチ（-55 dBFS）でも測れる
    rec = recorded(12499, noise_db=-55.0, leading_zeros=2048)
    assert detect_latency(rec) == 12499


def test_filtered_pulse_within_few_samples():
    # キャビのように高域を削るとパルスがなまるが、ずれは数サンプルに収まる
    lat = detect_latency(recorded(12499, lowpass=3000, gain_db=-20))
    assert 12499 <= lat <= 12499 + 8


def test_loud_di_does_not_confuse():
    # DI がパルスより大きくても、先に来るパルスを拾う
    assert detect_latency(recorded(12499, di_db=-3.0, noise_db=-60.0)) == 12499


def test_no_pulse_raises():
    with pytest.raises(ValueError):
        detect_latency(np.random.default_rng(0).normal(0, 1e-4, (SR * 2, 2)))


def test_send_layout():
    di = np.full(100, 0.1, np.float32)
    send, start = build_send(di)
    pulse = make_pulse()
    assert len(pulse) == 48 and pulse.max() == pytest.approx(10 ** (-10 / 20))
    assert start == 48 + SR // 2
    assert np.all(send[:, :2] == 0)  # 出力 ch1-2 には何も出さない
    assert np.all(send[:, 2] == send[:, 3])
    assert np.all(send[start:start + 100, 2] == 0.1)
    assert np.all(send[48:start, 2] == 0)


def test_di_level_checks():
    x, notes = check_di_level(np.array([0.0, 1.5, -0.5], np.float32))
    assert np.max(np.abs(x)) < 1.0 and notes
    _, notes = check_di_level(np.full(10, 0.001, np.float32))
    assert any("小さい" in n for n in notes)
    _, notes = check_di_level(np.full(10, 0.3, np.float32))
    assert notes == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q", "-p", "no:cacheprovider"]))

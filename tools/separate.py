#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "demucs==4.0.1",
#   "torch==2.5.1",
#   "torchaudio==2.5.1",
#   "numpy>=1.26,<2.1",
#   "soundfile>=0.12",
#   "soxr>=0.3",
# ]
# ///
"""曲の音源から楽器の stem を取り出す（demucs）。区間を指定して切り出せる。

- ベース: htdemucs（安定している）
- ギター: htdemucs_6s の guitar（実験的。質はそこそこ）

出力（output/<曲名>/ の下。コミットしない）:
  mix.wav      … 切り出した区間の元の音
  <stem>.wav   … 取り出した楽器の音（44.1kHz、ステレオ）

使い方:
  tools/separate.py input/song.mp3 --stem bass [--start 62.5 --end 78] [--name song-riff]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
MODEL_FOR = {"bass": "htdemucs", "drums": "htdemucs", "vocals": "htdemucs", "other": "htdemucs",
             "guitar": "htdemucs_6s", "piano": "htdemucs_6s"}


def load_section(path: Path, start: float | None, end: float | None) -> tuple[np.ndarray, int]:
    info = sf.info(str(path))
    sr = info.samplerate
    a = int((start or 0) * sr)
    b = int(end * sr) if end is not None else info.frames
    if not 0 <= a < b <= info.frames:
        raise SystemExit(f"区間が音源の長さ（{info.frames / sr:.1f} 秒）の外です: {start}〜{end}")
    x, _ = sf.read(str(path), start=a, stop=b, dtype="float32", always_2d=True)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    return x[:, :2], sr


def separate(x: np.ndarray, sr: int, stem: str, device: str) -> tuple[np.ndarray, int]:
    import soxr
    import torch
    from demucs.apply import apply_model
    from demucs.pretrained import get_model

    model = get_model(MODEL_FOR[stem])
    model.eval()
    if sr != model.samplerate:
        x = soxr.resample(x, sr, model.samplerate)
        sr = model.samplerate
    wav = torch.from_numpy(np.ascontiguousarray(x.T))
    ref = wav.mean(0)
    mean, std = ref.mean(), ref.std() + 1e-8
    with torch.no_grad():
        out = apply_model(model, ((wav - mean) / std)[None], device=device, split=True, overlap=0.25, progress=True)[0]
    out = out * std + mean
    return out[model.sources.index(stem)].cpu().numpy().T, sr


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", type=Path, help="曲の音源（wav / flac / mp3 など）")
    ap.add_argument("--stem", choices=sorted(MODEL_FOR), default="bass")
    ap.add_argument("--start", type=float, help="切り出しの開始（秒）")
    ap.add_argument("--end", type=float, help="切り出しの終わり（秒）")
    ap.add_argument("--name", help="出力のフォルダ名（省略時は音源のファイル名）")
    ap.add_argument("--out-root", type=Path, default=ROOT / "output")
    ap.add_argument("--device", default="cpu", help="cpu / mps")
    a = ap.parse_args(argv)

    x, sr = load_section(a.audio, a.start, a.end)
    out_dir = a.out_root / (a.name or a.audio.stem)
    out_dir.mkdir(parents=True, exist_ok=True)
    sf.write(out_dir / "mix.wav", x, sr, subtype="PCM_24")
    y, ysr = separate(x, sr, a.stem, a.device)
    peak = float(np.max(np.abs(y))) if y.size else 0.0
    if peak > 1.0:
        y = y / peak * 0.99
        print(f"注意: {a.stem} の音が大きすぎたので {20 * np.log10(peak):.1f} dB 下げました", file=sys.stderr)
    path = out_dir / f"{a.stem}.wav"
    sf.write(path, y, ysr, subtype="PCM_24")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

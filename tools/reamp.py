#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["numpy>=1.26", "soundfile>=0.12", "sounddevice>=0.4.6", "soxr>=0.3"]
# ///
"""GX-1B で DI を録る／リアンプする（USB オーディオ）。

チャンネルの割り当てと GX 側の設定は knowledge/gx/reamp-setup.md にある。
  入力 ch1-2 = EFX（処理後）、入力 ch3 = DRY（入力そのまま）、出力 ch3-4 = EFX への入力
  GX 側は DRY TO EFX ON・LOOPBACK OFF にしておく。

対話はしない（1 回の実行で 1 パッチ）。パッチの切り替えは本体で手で行う。

使い方:
  tools/reamp.py record-di --seconds 30 --wait 3 -o output/reamp/<名前>/di.wav
  tools/reamp.py run output/reamp/<名前>/di.wav --label U01 -o output/reamp/<名前>/U01.wav
  tools/reamp.py devices
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 48000
DEVICE_NAME = "GX-1"  # GX-1B をつないでもこの名前（reamp-setup.md）
CHANNELS = 4
IN_EFX = (0, 1)  # 入力 ch1-2
IN_DRY = 2  # 入力 ch3
OUT_EFX = (2, 3)  # 出力 ch3-4

PULSE_SEC = 0.001
PULSE_DBFS = -10.0
GAP_SEC = 0.5
TAIL_SEC = 1.5  # 往復の遅れ（約 0.26 秒）＋残響のぶん、DI の後ろに足して録る

# DI の音量の目安（警告だけ。止めない）
DI_PEAK_LOW_DBFS = -30.0
DI_PEAK_HIGH_DBFS = -1.0


def db(x: float) -> float:
    return float(20 * np.log10(x + 1e-12))


def warn(msg: str) -> None:
    print(f"警告: {msg}", file=sys.stderr)


# ---------------------------------------------------------------- デバイス

def find_device(name: str = DEVICE_NAME) -> int:
    """名前に name を含み、入出力とも 4ch 以上あるデバイスの番号を返す。"""
    try:
        import sounddevice as sd
    except OSError as e:  # PortAudio が読めない
        raise SystemExit(f"オーディオの初期化に失敗しました（PortAudio）: {e}")
    devs = sd.query_devices()
    found = [(i, d) for i, d in enumerate(devs) if name.lower() in d["name"].lower()]
    if not found:
        names = "、".join(sorted({d["name"] for d in devs})) or "（なし）"
        raise SystemExit(
            f"オーディオデバイス「{name}」が見つかりません。GX-1B が USB でつながっているか、"
            f"GX-1 Driver が入っているかを確かめてください。\n見えているデバイス: {names}"
        )
    for i, d in found:
        if d["max_input_channels"] >= CHANNELS and d["max_output_channels"] >= CHANNELS:
            return i
    i, d = found[0]
    raise SystemExit(
        f"「{d['name']}」のチャンネルが足りません（入力 {d['max_input_channels']}ch・出力 "
        f"{d['max_output_channels']}ch。どちらも {CHANNELS}ch 必要）。ドライバーを確かめてください。"
    )


# ---------------------------------------------------------------- 信号

def make_pulse(sr: int = SR) -> np.ndarray:
    n = max(1, int(round(PULSE_SEC * sr)))
    return np.full(n, 10 ** (PULSE_DBFS / 20), dtype=np.float32)


def detect_latency(rec: np.ndarray, sr: int = SR, search_sec: float = GAP_SEC + 1.0,
                   min_db: float = -60.0, above_floor_db: float = 24.0) -> int:
    """録音（モノまたは多チャンネル）の中から、最初のパルスの立ち上がりのサンプル位置を返す。

    1. ノイズの床: 先頭 search_sec 秒を 5 ms ごとに区切った RMS の 25 パーセンタイル
       （ちょうど 0 の区間＝ストリームの立ち上がりは除く）。この区間の大半はパルス前と無音の間なので、
       DI が大きくてもノイズの値になる
    2. 床より above_floor_db 以上、かつ min_db 以上の最初のサンプルを探す（おおよその到着）
    3. そこから 10 ms の中の最大値の半分を最初に超えるサンプルを立ち上がりとする
       （パッチの EQ・キャビで波形がなまっても、前後にぶれにくい）
    見つからなければ ValueError。
    """
    x = np.asarray(rec, dtype=np.float64)
    env = np.abs(x).max(axis=1) if x.ndim == 2 else np.abs(x)
    env = env[: int(search_sec * sr)]
    fl = max(1, int(0.005 * sr))
    nf = len(env) // fl
    floor = 0.0
    if nf:
        frames = np.sqrt(np.mean(env[: nf * fl].reshape(nf, fl) ** 2, axis=1))
        frames = frames[frames > 0]
        if len(frames):
            floor = float(np.percentile(frames, 25))
    thr = max(10 ** (min_db / 20), floor * 10 ** (above_floor_db / 20))
    idx = np.flatnonzero(env > thr)
    if len(idx) == 0:
        raise ValueError(
            f"パルスが録れませんでした（先頭 {search_sec:.1f} 秒に {db(thr):.0f} dBFS を超える音がない）"
        )
    i0 = int(idx[0])
    win = env[i0 : i0 + int(0.01 * sr)]
    half = win.max() * 0.5
    return i0 + int(np.flatnonzero(win >= half)[0])


def load_di(path: Path) -> tuple[np.ndarray, list[str]]:
    """DI を読み、モノ・48 kHz にする。返り値は（信号, 警告の一覧）。"""
    x, sr = sf.read(str(path), dtype="float32", always_2d=True)
    x = x.mean(axis=1)
    notes: list[str] = []
    if sr != SR:
        import soxr

        x = soxr.resample(x, sr, SR).astype(np.float32)
        notes.append(f"DI のサンプリング周波数 {sr} Hz を {SR} Hz に変換した")
    return x, notes


def check_di_level(x: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """ピークが 0 dBFS を超えないようにし、音量が極端なら警告を返す。"""
    notes: list[str] = []
    if len(x) == 0:
        raise SystemExit("DI が空です")
    peak = float(np.max(np.abs(x)))
    if peak >= 1.0:
        x = (x / peak * 10 ** (-1 / 20)).astype(np.float32)
        notes.append(f"DI のピークが {db(peak):+.1f} dBFS で 0 dBFS を超えていたので、-1 dBFS に下げた")
        peak = float(np.max(np.abs(x)))
    if db(peak) < DI_PEAK_LOW_DBFS:
        notes.append(f"DI のピークが {db(peak):.1f} dBFS と小さい（{DI_PEAK_LOW_DBFS:.0f} dBFS 未満）。"
                     "歪み方が実際に弾いたときと変わる")
    elif db(peak) > DI_PEAK_HIGH_DBFS:
        notes.append(f"DI のピークが {db(peak):.1f} dBFS と 0 dBFS に近い")
    return x, notes


def build_send(di: np.ndarray, sr: int = SR, tail_sec: float = TAIL_SEC) -> tuple[np.ndarray, int]:
    """出力 4ch の信号（ch3-4 に パルス → 無音 → DI → 無音）と、DI の開始位置を返す。"""
    pulse = make_pulse(sr)
    gap = int(GAP_SEC * sr)
    di_start = len(pulse) + gap
    mono = np.concatenate([pulse, np.zeros(gap, np.float32), di, np.zeros(int(tail_sec * sr), np.float32)])
    out = np.zeros((len(mono), CHANNELS), np.float32)
    for ch in OUT_EFX:
        out[:, ch] = mono
    return out, di_start


# ---------------------------------------------------------------- コマンド

def cmd_devices(_: argparse.Namespace) -> int:
    import sounddevice as sd

    print(sd.query_devices())
    return 0


def cmd_record_di(a: argparse.Namespace) -> int:
    if a.seconds <= 0:
        raise SystemExit("--seconds は正の数にしてください")
    import sounddevice as sd

    dev = find_device(a.device)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    if a.wait > 0:
        print(f"{a.wait:g} 秒後に録り始めます…", file=sys.stderr, flush=True)
        time.sleep(a.wait)
    print(f"録音中（{a.seconds:g} 秒）。弾いてください", file=sys.stderr, flush=True)
    rec = sd.rec(int(a.seconds * SR), samplerate=SR, channels=CHANNELS, device=dev, dtype="float32")
    sd.wait()
    di = rec[:, IN_DRY]
    peak, rms = float(np.max(np.abs(di))), float(np.sqrt(np.mean(di**2)))
    sf.write(str(a.out), di, SR, subtype="PCM_24")
    print(f"→ {a.out}（ピーク {db(peak):.1f} dBFS・RMS {db(rms):.1f} dBFS）")
    if peak >= 0.999:
        warn("DI がクリップしている。GX の入力（INPUT のレベル）か弾く強さを下げて録り直す")
    elif db(peak) < DI_PEAK_LOW_DBFS:
        warn(f"DI が小さい（ピーク {db(peak):.1f} dBFS）。音が入っていないかもしれない")
    return 0


def cmd_run(a: argparse.Namespace) -> int:
    import sounddevice as sd

    di, notes = load_di(a.di)
    if a.gain_db:
        di = (di * 10 ** (a.gain_db / 20)).astype(np.float32)
        notes.append(f"DI に {a.gain_db:+.1f} dB をかけて送った")
    di, more = check_di_level(di)
    notes += more
    for n in notes:
        warn(n)

    dev = find_device(a.device)
    send, di_start = build_send(di, SR, a.tail)
    print(f"[{a.label}] 送って録っています（{len(send) / SR:.1f} 秒）…", file=sys.stderr, flush=True)
    rec = sd.playrec(send, samplerate=SR, channels=CHANNELS, device=(dev, dev), dtype="float32")
    sd.wait()
    efx = rec[:, list(IN_EFX)]

    if a.latency is not None:
        lat = a.latency
    else:
        try:
            lat = detect_latency(efx, SR)
        except ValueError as e:
            raise SystemExit(
                f"{e}。GX の DRY TO EFX が ON か、LOOPBACK が OFF か、パッチの音量が 0 でないかを確かめてください"
            )
    start = lat + di_start
    end = min(len(efx), start + len(di) + int(a.keep_tail * SR))
    out = efx[start:end]
    if len(out) < len(di):
        warn("録音の後ろが足りない（遅れが想定より大きい）。--tail を大きくする")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(a.out), out, SR, subtype="PCM_24")

    peak, rms = float(np.max(np.abs(out))), float(np.sqrt(np.mean(out**2)))
    if peak >= 0.999:
        warn("録音がクリップしている（パッチの音量が大きすぎる）")
    info = {
        "label": a.label,
        "di": str(a.di),
        "out": str(a.out),
        "recorded_at": datetime.now().isoformat(timespec="seconds"),
        "sample_rate": SR,
        "latency_samples": int(lat),
        "latency_ms": round(lat / SR * 1000, 2),
        "latency_forced": a.latency is not None,
        "rms_dbfs": round(db(rms), 2),
        "peak_dbfs": round(db(peak), 2),
        "notes": notes,
    }
    meta = a.out.with_suffix(".json")
    meta.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n")
    print(f"[{a.label}] 遅れ {lat} サンプル（{info['latency_ms']} ms）・RMS {info['rms_dbfs']} dBFS・"
          f"ピーク {info['peak_dbfs']} dBFS")
    print(f"→ {a.out}\n→ {meta}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--device", default=DEVICE_NAME, help="デバイス名（の一部）。既定は GX-1")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("devices", help="オーディオデバイスの一覧")
    p.set_defaults(func=cmd_devices)

    p = sub.add_parser("record-di", help="DRY（入力 ch3）を録る（本人が弾く）")
    p.add_argument("--seconds", type=float, required=True, help="録る長さ（秒）")
    p.add_argument("--wait", type=float, default=3.0, help="録り始めるまで待つ秒数（既定 3）")
    p.add_argument("-o", "--out", type=Path, required=True)
    p.set_defaults(func=cmd_record_di)

    p = sub.add_parser("run", help="1 パッチ分のリアンプ（DI を出力 ch3-4 へ送り、入力 ch1-2 を録る）")
    p.add_argument("di", type=Path)
    p.add_argument("--label", required=True, help="パッチの名前（U01 など）")
    p.add_argument("-o", "--out", type=Path, required=True)
    p.add_argument("--gain-db", type=float, default=0.0, help="DI にかけてから送る（既定 0）")
    p.add_argument("--tail", type=float, default=TAIL_SEC, help="DI の後ろに足して録る秒数（遅れ＋残響ぶん）")
    p.add_argument("--keep-tail", type=float, default=0.0,
                   help="保存する録音に、DI の長さより後ろを何秒残すか（残響を見るとき。既定 0 = DI と同じ長さ）")
    p.add_argument("--latency", type=int, help="遅れ（サンプル）を測らずにこの値で揃える（パルスが録れないとき）")
    p.set_defaults(func=cmd_run)

    a = ap.parse_args(argv)
    if getattr(a, "keep_tail", 0) and a.keep_tail > a.tail - 0.5:
        raise SystemExit("--keep-tail は --tail より 0.5 秒以上短くしてください（遅れのぶん）")
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())

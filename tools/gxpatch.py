#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""tone.json（人が読める音作り）と GX-1B の .tsl を相互に変換する。

型紙（確かめ済みの本物のパッチ）を土台にして、意味がわかっている欄だけを書き換える。
わからない欄は型紙のまま残すので、BTS で読み込めない形にはならない。
形式の根拠: knowledge/gx/tsl-format.md、knowledge/gx/gx-1b.md

使い方:
  tools/gxpatch.py build tone1.json [tone2.json ...] -o out.tsl [--set-name NAME] [--template X.tsl]
  tools/gxpatch.py inspect patch.tsl            # 各パッチを tone.json の形で表示
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = ROOT / "knowledge/gx/samples/gx-1b_viva-beers-2026.tsl"
DEVICE = "GX-1B"

# 番号は GX-1B の Parameter Guide の並び順（knowledge/gx/gx-1b.md）。BTS の表示で確かめたものは gx-1b.md に印あり。
AMP_TYPES = ["NATURAL", "X-DRIVE", "CONCERT", "STUDIO", "SILVER", "CLAS BLUE", "SOLID STK", "FAT TUBE",
             "DARK DRV", "ACOUSTIC", "SUPR FLAT", "FLIPTOP", "SW-TOUR", "GT CRNCH", "GT HI GAIN", "GT MODDED"]
SP_TYPES = ["OFF", "ORIGINAL", "B1x15", "B1x18", "B2x15", "B4x10", "B8x10"] + [f"USER{i}" for i in range(1, 9)]
MIC_TYPES = ["DYN57", "DYN421", "CND451", "CND87", "FLAT", "RIBON121", "BLEND A", "BLEND B", "BLEND C"]
ODDS_TYPES = ["MID BOOST", "CLEAN BST", "TREBLE BST", "NATURAL OD", "WARM OD", "BLUES OD", "OVERDRIVE", "CRUNCH",
              "T-SCREAM", "TURBO OD", "CENTA OD", "X-OD", "DIST", "A-DIST", "FAT DS", "LEAD DS", "RAT", "GUV DS",
              "DIST+", "X-DIST", "METAL DS", "METAL ZONE", "HVY METAL", "METAL CORE", "OCT FUZZ", "60S FUZZ",
              "MUFF FUZZ", "BASS OD", "X-BASS OD", "BASS DS", "BASS DI", "SA DI DRIVE", "HI BAND DRV", "BASS MT",
              "BASS FUZZ"]
FX_TYPES = ["COMPRESSOR", "LIMITER", "ENHANCER", "TOUCH WAH", "AUTO WAH", "FIXED WAH", "DEFRETTER", "ENV FILTER",
            "BASS SYNTH", "SLOW GEAR", "AC BASS", "FEEDBACKER", "OD/DS", "PARA. EQ", "GEQ", "LOW GEQ", "HIGH GEQ",
            "CHORUS", "FLANGER", "PHASER", "SCRIPT PH", "CLASSIC-VIBE", "ROTARY", "VIBRATO", "TREMOLO", "SLICER",
            "OVERTONE", "PAN", "RING MOD", "HUMANIZER", "PITCH SHIFT", "HARMONIST", "OCTAVE", "HEAVY OCT", "S-BEND",
            "PEDAL BEND", "TUNE DOWN", "DELAY", "REVERB"]

FREQ_STEPS = ["20Hz", "25Hz", "31.5Hz", "40Hz", "50Hz", "63Hz", "80Hz", "100Hz", "125Hz", "160Hz", "200Hz",
              "250Hz", "315Hz", "400Hz", "500Hz", "630Hz", "800Hz", "1kHz", "1.25kHz", "1.6kHz", "2kHz", "2.5kHz",
              "3.15kHz", "4kHz", "5kHz", "6.3kHz", "8kHz", "10kHz", "12.5kHz"]
FREQ_LOW_CUT = ["FLAT", *FREQ_STEPS]
FREQ_HIGH_CUT = [*FREQ_STEPS, "FLAT"]

# PARA. EQ: FX 本体の byte 31 から（GX-1 の FORMAT.md と同じ並び。見本の FX2 で値の形を確かめた）
PEQ_OFFSET = 31
PEQ_FIELDS = [
    (0, "low_gain", (-20, 20)), (1, "high_gain", (-20, 20)), (2, "level", (-20, 20)),
    (3, "mid_freq", FREQ_STEPS), (4, "mid_gain", (-20, 20)), (5, "low_cut", FREQ_LOW_CUT), (6, "high_cut", FREQ_HIGH_CUT),
]
PEQ_SIGNED = {"low_gain", "high_gain", "level", "mid_gain"}

# COMPRESSOR（GX-1B）: FX 本体の byte 4〜9。X-COMP で BTS の表示と照らし合わせた
# （byte 0〜3 は GX-1 のコンプの欄で、GX-1B では使われない）
COMP_OFFSET = 4
COMP_TYPES = ["BOSS COMP", "D-COMP", "ORANGE", "X-COMP", "STEREO"]  # 3 = X-COMP だけ確かめた
# RATIO の一覧（BOSS の一般的な並び）。15 = 12:1 だけ確かめた
RATIOS = ["1:1", "1.2:1", "1.4:1", "1.6:1", "1.8:1", "2:1", "2.3:1", "2.6:1", "3:1", "3.5:1", "4:1", "5:1", "6:1",
          "8:1", "10:1", "12:1", "20:1", "INF:1"]
XCOMP_FIELDS = [(0, "type", ["X-COMP"]), (1, "threshold", (0, 100)), (2, "attack", (0, 100)), (3, "level", (0, 100)),
                (4, "ratio", RATIOS), (5, "direct", (0, 100))]
# CHORUS: FX 本体の byte 123〜127（GX-1 と同じ）。RATE / DEPTH / LEVEL / DIRECT を BTS で確かめた。
# TYPE（MONO/STEREO など）は GX-1B では byte 122 ではない（未解明なので書かない）
CHORUS_OFFSET = 123
CHORUS_FIELDS = [(0, "rate", (0, 100)), (1, "depth", (0, 100)), (2, "level", (0, 100)), (4, "direct", (0, 100))]

# (バイト位置, 名前, 範囲 or 一覧)
AMP_FIELDS = [
    (0, "on", bool), (2, "type", AMP_TYPES), (3, "gain", (0, 120)), (4, "level", (0, 100)),
    (5, "bass", (0, 100)), (6, "middle", (0, 100)), (7, "treble", (0, 100)),
    (9, "speaker", SP_TYPES), (10, "mic", MIC_TYPES),
]
ODDS_FIELDS = [
    (0, "on", bool), (1, "type", ODDS_TYPES), (2, "drive", (0, 120)), (3, "tone", (-50, 50)),
    (4, "level", (0, 100)), (5, "direct", (0, 100)),
]
NS_FIELDS = [(0, "on", bool), (1, "threshold", (0, 100)), (2, "release", (0, 100))]
BLOCKS = {"amp": ("MEMORY%AMP", AMP_FIELDS), "odds": ("MEMORY%ODDS", ODDS_FIELDS), "ns": ("MEMORY%NS", NS_FIELDS)}
SIGNED_CENTER = {("odds", "tone"): 50}
# ON/OFF と種類だけ読み書きするブロック（中身は型紙のまま）
SWITCHES = {"fx1": "MEMORY%FX1_COM", "fx2": "MEMORY%FX2_COM", "fx3": "MEMORY%FX3_COM",
            "delay": "MEMORY%DLY", "reverb": "MEMORY%REV"}


class ToneError(ValueError):
    pass


def _name_bytes(name: str) -> list[str]:
    try:
        raw = name.encode("ascii")
    except UnicodeEncodeError:
        raise ToneError(f"name は半角英数字のみ: {name!r}") from None
    if len(raw) > 16:
        raise ToneError(f"name は 16 文字まで: {name!r}")
    raw = raw.ljust(16, b" ")
    return [f"{b:02X}" for b in raw]


def _encode(block: str, field: str, spec, value, center: int | None = None) -> int:
    where = f"{block}.{field}"
    if spec is bool:
        if not isinstance(value, bool):
            raise ToneError(f"{where} は true / false: {value!r}")
        return int(value)
    if isinstance(spec, list):
        if value not in spec:
            raise ToneError(f"{where} は {spec} のどれか: {value!r}")
        return spec.index(value)
    lo, hi = spec
    if not isinstance(value, int) or isinstance(value, bool) or not lo <= value <= hi:
        raise ToneError(f"{where} は {lo}〜{hi} の整数: {value!r}")
    return value + (center if center is not None else SIGNED_CENTER.get((block, field), 0))


def _decode(block: str, field: str, spec, raw: int, center: int | None = None):
    if spec is bool:
        return bool(raw)
    if isinstance(spec, list):
        return spec[raw] if raw < len(spec) else f"?{raw}"
    return raw - (center if center is not None else SIGNED_CENTER.get((block, field), 0))


def _apply_fx(ps: dict, key: str, vals: dict) -> None:
    """FX スロット: on / type と、type が PARA. EQ のときの peq（中身）を書く。"""
    com, body = SWITCHES[key], "MEMORY%" + key.upper()
    bad = set(vals) - {"on", "type", "peq", "comp", "chorus"}
    if bad:
        raise ToneError(f"{key} に知らない項目: {sorted(bad)}")
    if "on" in vals:
        ps[com][0] = f"{_encode(key, 'on', bool, vals['on']):02X}"
    if "type" in vals:
        if vals["type"] != "PARA. EQ":
            raise ToneError(f"{key}.type は今は PARA. EQ だけ変えられる（他は中身の並びが未確認）: {vals['type']!r}")
        t = f"{FX_TYPES.index('PARA. EQ'):02X}"
        ps[com][1] = ps[com][2] = t  # 見本では byte 1 と 2 が同じ値
    cur = FX_TYPES[int(ps[com][2], 16)] if int(ps[com][2], 16) < len(FX_TYPES) else None
    if "peq" in vals:
        if cur != "PARA. EQ":
            raise ToneError(f"{key}.peq は type が PARA. EQ のときだけ（今は {cur}）")
        by_name = {f: (i, sp) for i, f, sp in PEQ_FIELDS}
        bad = set(vals["peq"]) - set(by_name)
        if bad:
            raise ToneError(f"{key}.peq に知らない項目: {sorted(bad)}")
        for f, v in vals["peq"].items():
            i, sp = by_name[f]
            ps[body][PEQ_OFFSET + i] = f"{_encode(key, f, sp, v, 20 if f in PEQ_SIGNED else 0):02X}"
    for sub, need, offset, fields in (("comp", "COMPRESSOR", COMP_OFFSET, XCOMP_FIELDS),
                                      ("chorus", "CHORUS", CHORUS_OFFSET, CHORUS_FIELDS)):
        if sub not in vals:
            continue
        if cur != need:
            raise ToneError(f"{key}.{sub} は FX の種類が {need} のときだけ（今は {cur}）")
        if sub == "comp" and COMP_TYPES[int(ps[body][COMP_OFFSET], 16)] != "X-COMP" and vals[sub].get("type") != "X-COMP":
            raise ToneError(f"{key}.comp は今は X-COMP だけ（他の TYPE は中身の並びが未確認）")
        by_name = {f: (i, sp) for i, f, sp in fields}
        bad = set(vals[sub]) - set(by_name)
        if bad:
            raise ToneError(f"{key}.{sub} に知らない項目: {sorted(bad)}")
        for f, v in vals[sub].items():
            i, sp = by_name[f]
            raw = 3 if (sub, f) == ("comp", "type") else _encode(key, f, sp, v)
            ps[body][offset + i] = f"{raw:02X}"


def apply_tone(param_set: dict, tone: dict) -> dict:
    ps = copy.deepcopy(param_set)
    known = {"name", "device", "memo", "notes", *BLOCKS, *SWITCHES}
    extra = set(tone) - known
    if extra:
        raise ToneError(f"知らない項目: {sorted(extra)}")
    if tone.get("device", DEVICE) != DEVICE:
        raise ToneError(f"device は {DEVICE} のみ: {tone['device']!r}")
    if "name" in tone:
        ps["MEMORY%COM"] = _name_bytes(tone["name"])
    for key, (mem, fields) in BLOCKS.items():
        vals = tone.get(key)
        if vals is None:
            continue
        by_name = {f: (i, s) for i, f, s in fields}
        bad = set(vals) - set(by_name)
        if bad:
            raise ToneError(f"{key} に知らない項目: {sorted(bad)}")
        for f, v in vals.items():
            i, s = by_name[f]
            ps[mem][i] = f"{_encode(key, f, s, v):02X}"
    for key, mem in SWITCHES.items():
        vals = tone.get(key)
        if vals is None:
            continue
        if key.startswith("fx"):
            _apply_fx(ps, key, vals)
            continue
        bad = set(vals) - {"on"}
        if bad:
            raise ToneError(f"{key} は on だけ書き換えられる（中身は型紙のまま）: {sorted(bad)}")
        if "on" in vals:
            ps[mem][0] = f"{_encode(key, 'on', bool, vals['on']):02X}"
    return ps


def read_tone(param_set: dict) -> dict:
    name = bytes(int(h, 16) for h in param_set["MEMORY%COM"]).decode("ascii", "replace").rstrip()
    tone: dict = {"name": name, "device": DEVICE}
    for key, (mem, fields) in BLOCKS.items():
        tone[key] = {f: _decode(key, f, s, int(param_set[mem][i], 16)) for i, f, s in fields}
    for key, mem in SWITCHES.items():
        b = param_set[mem]
        tone[key] = {"on": b[0] == "01"}
        if key.startswith("fx"):
            t = int(b[2], 16)  # GX-1B は byte 2（ベース用の欄）
            tone[key]["type"] = FX_TYPES[t] if t < len(FX_TYPES) else f"?{t}"
            body = param_set["MEMORY%" + key.upper()]
            if tone[key]["type"] == "COMPRESSOR":
                ct = int(body[COMP_OFFSET], 16)
                tone[key]["comp_type"] = COMP_TYPES[ct] if ct < len(COMP_TYPES) else f"?{ct}"
                if tone[key]["comp_type"] == "X-COMP":
                    tone[key]["comp"] = {f: _decode(key, f, sp, int(body[COMP_OFFSET + i], 16))
                                         for i, f, sp in XCOMP_FIELDS[1:]}
            if tone[key]["type"] == "CHORUS":
                tone[key]["chorus"] = {f: int(body[CHORUS_OFFSET + i], 16) for i, f, _ in CHORUS_FIELDS}
            if tone[key]["type"] == "PARA. EQ":
                body = param_set["MEMORY%" + key.upper()]
                tone[key]["peq"] = {f: _decode(key, f, sp, int(body[PEQ_OFFSET + i], 16), 20 if f in PEQ_SIGNED else 0)
                                    for i, f, sp in PEQ_FIELDS}
    return tone


def load_tsl(path: Path) -> dict:
    env = json.loads(path.read_text())
    if env.get("device") != DEVICE:
        raise ToneError(f"{path} は {DEVICE} のファイルではありません（device={env.get('device')!r}）")
    return env


def build(tones: list[dict], template: Path, set_name: str) -> dict:
    tpl = load_tsl(template)
    base = tpl["data"][0][0]
    patches = []
    for t in tones:
        p = copy.deepcopy(base)
        p["memo"] = t.get("memo", "")
        p["paramSet"] = apply_tone(base["paramSet"], t)
        patches.append(p)
    if not 1 <= len(patches) <= 99:
        raise ToneError("パッチは 1〜99 個")
    return {"name": set_name, "formatRev": tpl["formatRev"], "device": DEVICE, "data": [patches, []]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("tones", nargs="+", type=Path)
    b.add_argument("-o", "--out", type=Path, required=True)
    b.add_argument("--set-name", default="BOSS-GX")
    b.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    i = sub.add_parser("inspect")
    i.add_argument("tsl", type=Path)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "build":
            tones = [json.loads(p.read_text()) for p in a.tones]
            env = build(tones, a.template, a.set_name)
            a.out.parent.mkdir(parents=True, exist_ok=True)
            a.out.write_text(json.dumps(env, ensure_ascii=False, separators=(",", ":")))
            print(f"{a.out}（{len(tones)} パッチ）")
        else:
            env = load_tsl(a.tsl)
            for n, p in enumerate(env["data"][0], 1):
                print(f"# U{n:02d}")
                print(json.dumps(read_tone(p["paramSet"]), ensure_ascii=False, indent=2))
    except ToneError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest>=8"]
# ///
"""gxpatch.py を見本のパッチで確かめる。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import gxpatch as g  # noqa: E402

TPL = g.DEFAULT_TEMPLATE


def tpl_ps() -> dict:
    return json.loads(TPL.read_text())["data"][0][0]["paramSet"]


def test_reads_sample_as_bts_shows():
    """BTS の表示（ユーザーが確かめた値）と同じに読める。"""
    t = g.read_tone(tpl_ps())
    assert t["name"] == "Viva Beers 2026"
    assert t["amp"]["type"] == "CLAS BLUE"
    assert t["amp"]["speaker"] == "B1x18"
    assert t["amp"]["mic"] == "CND87"
    assert t["odds"]["type"] == "SA DI DRIVE" and t["odds"]["tone"] == 10
    assert [t[k]["type"] for k in ("fx1", "fx2", "fx3")] == ["COMPRESSOR", "PARA. EQ", "CHORUS"]


def test_reads_sample_peq():
    """見本の FX2（PARA. EQ）の中身。BTS の表示とはまだ照らし合わせていない。"""
    peq = g.read_tone(tpl_ps())["fx2"]["peq"]
    assert peq == {"low_gain": -2, "high_gain": 2, "level": 2, "mid_freq": "800Hz", "mid_gain": 6,
                   "low_cut": "63Hz", "high_cut": "FLAT"}


def test_reads_sample_comp_and_chorus_as_bts_shows():
    """BTS の表示（ユーザーのスクリーンショット）と同じ。"""
    t = g.read_tone(tpl_ps())
    assert t["fx1"]["comp_type"] == "X-COMP"
    assert t["fx1"]["comp"] == {"threshold": 60, "attack": 40, "level": 45, "ratio": "12:1", "direct": 0}
    assert t["fx3"]["chorus"] == {"rate": 48, "depth": 43, "level": 50, "direct": 100}


def test_comp_writes_only_comp_bytes():
    ps = tpl_ps()
    out = g.apply_tone(ps, {"fx1": {"comp": {"threshold": 40, "ratio": "4:1"}}})
    diff = [i for i, (a, b) in enumerate(zip(ps["MEMORY%FX1"], out["MEMORY%FX1"])) if a != b]
    assert diff == [5, 8] and out["MEMORY%FX1"][5] == "28" and out["MEMORY%FX1"][8] == "0A"


def test_roundtrip_is_identical():
    """読んだ tone をそのまま書き戻すと、型紙と 1 バイトも変わらない。"""
    ps = tpl_ps()
    t = g.read_tone(ps)
    for k in ("fx1", "fx3"):
        t[k].pop("type")
    t["fx1"].pop("comp_type")
    assert g.apply_tone(ps, t) == ps


def test_peq_writes_only_eq_bytes():
    ps = tpl_ps()
    out = g.apply_tone(ps, {"fx2": {"on": True, "type": "PARA. EQ",
                                    "peq": {"low_cut": "40Hz", "mid_freq": "1kHz", "mid_gain": 3, "high_gain": -1}}})
    body = out["MEMORY%FX2"]
    assert body[31 + 5] == "04" and body[31 + 3] == "11" and body[31 + 4] == "17" and body[31 + 1] == "13"
    diff = [i for i, (a, b) in enumerate(zip(ps["MEMORY%FX2"], body)) if a != b]
    assert diff and all(31 <= i <= 37 for i in diff)


def test_peq_needs_peq_type():
    with pytest.raises(g.ToneError):
        g.apply_tone(tpl_ps(), {"fx3": {"peq": {"mid_gain": 3}}})  # FX3 は CHORUS


def test_build_changes_only_named_bytes():
    ps = tpl_ps()
    out = g.apply_tone(ps, {"name": "TEST", "amp": {"type": "DARK DRV", "gain": 80}, "ns": {"on": True}})
    assert out["MEMORY%AMP"][2] == "08" and out["MEMORY%AMP"][3] == "50"
    assert out["MEMORY%AMP"][1] == ps["MEMORY%AMP"][1]  # ギター用の欄は触らない
    assert out["MEMORY%NS"][0] == "01"
    changed = {k for k in ps if ps[k] != out[k]}
    assert changed == {"MEMORY%COM", "MEMORY%AMP", "MEMORY%NS"}


def test_build_file_has_one_patch_per_tone(tmp_path):
    env = g.build([{"name": "A"}, {"name": "B"}], TPL, "SET")
    assert env["device"] == "GX-1B" and len(env["data"][0]) == 2 and env["data"][1] == []


@pytest.mark.parametrize("tone", [
    {"amp": {"type": "NOPE"}},
    {"amp": {"gain": 121}},
    {"odds": {"tone": 51}},
    {"amp": {"volume": 1}},
    {"fx1": {"type": "CHORUS"}},
    {"fx2": {"peq": {"mid_gain": 21}}},
    {"fx2": {"comp": {"threshold": 40}}},
    {"fx1": {"comp": {"ratio": "7:1"}}},
    {"fx1": {"chorus": {"rate": 10}}},
    {"fx2": {"peq": {"mid_freq": "900Hz"}}},
    {"device": "GX-1"},
    {"name": "日本語"},
    {"name": "X" * 17},
])
def test_rejects_bad_values(tone):
    with pytest.raises(g.ToneError):
        g.apply_tone(tpl_ps(), tone)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))

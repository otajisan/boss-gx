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


def test_roundtrip_is_identical():
    """読んだ tone をそのまま書き戻すと、型紙と 1 バイトも変わらない。"""
    ps = tpl_ps()
    t = g.read_tone(ps)
    for k in ("fx1", "fx2", "fx3"):
        t[k].pop("type")
    assert g.apply_tone(ps, t) == ps


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
    {"device": "GX-1"},
    {"name": "日本語"},
    {"name": "X" * 17},
])
def test_rejects_bad_values(tone):
    with pytest.raises(g.ToneError):
        g.apply_tone(tpl_ps(), tone)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))

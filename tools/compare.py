#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["numpy>=1.26", "scipy>=1.11", "soundfile>=0.12", "librosa>=0.10", "matplotlib>=3.8"]
# ///
"""目標（原曲のベースなど）とリアンプした候補の音色を数値で比べ、近い順に並べる。

時間で平均した音色を比べる（フレーズは一致しないので波形は比べない）。特徴は analyze.py の
analyze() で測る。

主なスコア（距離）: 1/3 オクターブのレベルを、目標・候補それぞれ中域（63 Hz〜5 kHz の平均）を
0 dB に揃えてから帯域ごとに差を取り、40 Hz〜--max-hz の RMS（dB）にしたもの。小さいほど近い。
差は「候補 − 目標」。+5 dB なら、その帯域が目標より 5 dB 多い（削る）。

使い方:
  tools/compare.py --target "input/UNDEAD - Bass.wav" output/reamp/undead/U0*.wav \\
      [--target-start 20 --target-end 50] [--max-hz 10000] [--plot out.png] [-o out.json]
  曲から取り出した stem を目標にするときは --max-hz 5000（stem は 5 kHz より上が削れている）
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from analyze import analyze, load_mono  # noqa: E402

DIST_MIN_HZ = 40.0
NORM_RANGE = (63.0, 5000.0)  # この範囲の平均を 0 dB に揃える
TOP_N = 3  # 表に出す「ずれの大きい帯域」の数


def normalized_third(feats: dict, lo: float, hi: float) -> dict[str, float]:
    """1/3 オクターブ（analyze の値。100 Hz 基準）を、lo〜hi の平均が 0 dB になるようずらす。"""
    t = {k: v for k, v in feats["third_octave_db"].items() if v is not None}
    mid = [v for k, v in t.items() if lo <= float(k) <= hi]
    if not mid:
        raise ValueError("中域の 1/3 オクターブの値がありません")
    off = float(np.mean(mid))
    return {k: round(v - off, 2) for k, v in t.items()}


def _sub(a, b):
    return None if a is None or b is None else round(a - b, 2)


def compare_features(target: dict, cands: list[tuple[str, dict]], max_hz: float = 10000.0) -> dict:
    """特徴（analyze の出力）どうしを比べる。cands は（名前, 特徴）の並び。距離の小さい順に返す。"""
    lo, hi = NORM_RANGE[0], min(NORM_RANGE[1], max_hz)
    tn = normalized_third(target, lo, hi)
    rows = []
    for idx, (name, f) in enumerate(cands):
        cn = normalized_third(f, lo, hi)
        diff = {k: round(cn[k] - tn[k], 2) for k in tn if k in cn and DIST_MIN_HZ <= float(k) <= max_hz}
        if not diff:
            raise ValueError(f"{name}: 比べられる帯域がありません")
        dist = math.sqrt(float(np.mean([d * d for d in diff.values()])))
        worst = sorted(diff.items(), key=lambda kv: -abs(kv[1]))[:TOP_N]
        rows.append({
            "name": name,
            "input_index": idx,
            "distance_db": round(dist, 2),
            "band_diff_db": diff,
            "worst_bands": [{"hz": float(k), "diff_db": v} for k, v in worst],
            "third_octave_norm_db": cn,
            "aux_diff": {
                "upper_harmonic_db": _sub(f["distortion"]["upper_harmonic_db"], target["distortion"]["upper_harmonic_db"]),
                "range_p95_p10_db": _sub(f["dynamics"]["range_p95_p10_db"], target["dynamics"]["range_p95_p10_db"]),
                "decay_db_per_sec": _sub(f["dynamics"]["decay_db_per_sec"], target["dynamics"]["decay_db_per_sec"]),
                "crest_factor_db": _sub(f["level"]["crest_factor_db"], target["level"]["crest_factor_db"]),
            },
            "rms_dbfs": f["level"]["rms_dbfs"],
            "peak_dbfs": f["level"]["peak_dbfs"],
        })
    loudest = max(r["rms_dbfs"] for r in rows)
    for r in rows:
        r["rms_vs_loudest_db"] = round(r["rms_dbfs"] - loudest, 2)
    rows.sort(key=lambda r: r["distance_db"])
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return {
        "settings": {"max_hz": max_hz, "dist_min_hz": DIST_MIN_HZ, "norm_range_hz": [lo, hi]},
        "target_third_octave_norm_db": tn,
        "candidates": rows,
    }


def _fmt(v, nd=1):
    return "-" if v is None else f"{v:+.{nd}f}"


def format_table(res: dict) -> str:
    s = res["settings"]
    lines = [
        f"距離 = 1/3 オクターブの差の RMS（{s['dist_min_hz']:g} Hz〜{s['max_hz']:g} Hz、"
        f"{s['norm_range_hz'][0]:g}〜{s['norm_range_hz'][1]:g} Hz の平均で揃えた）。差は 候補 − 目標",
        "",
        "| 順位 | 候補 | 距離 dB | ずれの大きい帯域 | 歪み差 | ばらつき差 | 減り方差 | crest 差 | RMS dBFS | 最大との差 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in res["candidates"]:
        worst = "、".join(f"{w['hz']:g} Hz {w['diff_db']:+.1f}" for w in r["worst_bands"])
        a = r["aux_diff"]
        lines.append(
            f"| {r['rank']} | {r['name']} | {r['distance_db']:.2f} | {worst} | {_fmt(a['upper_harmonic_db'])} | "
            f"{_fmt(a['range_p95_p10_db'])} | {_fmt(a['decay_db_per_sec'])} | {_fmt(a['crest_factor_db'])} | "
            f"{r['rms_dbfs']:.1f} | {r['rms_vs_loudest_db']:+.1f} |"
        )
    # 帯域ごとの差（どこを直すか）
    bands = list(res["candidates"][0]["band_diff_db"]) if res["candidates"] else []
    lines += ["", "帯域ごとの差（dB、+ は目標より多い）", "",
              "| Hz | " + " | ".join(r["name"] for r in res["candidates"]) + " |",
              "|---|" + "---|" * len(res["candidates"])]
    for k in bands:
        lines.append(f"| {k} | " + " | ".join(f"{r['band_diff_db'].get(k, float('nan')):+.1f}" for r in res["candidates"]) + " |")
    lines += ["", "歪み差 = upper_harmonic_db（+ は目標より歪んでいる）、ばらつき差 = range_p95_p10_db（- は目標より"
              "揃っている＝コンプが強い）、減り方差 = decay（+ は目標より減りが遅い）"]
    return "\n".join(lines)


def plot(res: dict, target_name: str, out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 5.5))
    tn = res["target_third_octave_norm_db"]
    xs = [float(k) for k in tn]
    ax.semilogx(xs, list(tn.values()), "k-o", lw=2.5, ms=4, label=f"目標 {target_name}")
    for r in res["candidates"]:
        c = r["third_octave_norm_db"]
        ax.semilogx([float(k) for k in c], list(c.values()), "-", lw=1.2, marker=".",
                    label=f"{r['rank']}. {r['name']}（{r['distance_db']:.1f} dB）")
    ax.axvline(res["settings"]["max_hz"], color="gray", ls="--", lw=0.8)
    ticks = [31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000]
    ax.set_xticks(ticks, [f"{t:g}" if t < 1000 else f"{t / 1000:g}k" for t in ticks])
    ax.minorticks_off()
    ax.set_xlabel("Hz")
    ax.set_ylabel(f"dB（{res['settings']['norm_range_hz'][0]:g}〜{res['settings']['norm_range_hz'][1]:g} Hz の平均 = 0）")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8)
    ax.set_title("1/3 オクターブ")
    for fam in ("Hiragino Sans", "Hiragino Maru Gothic Pro", "AppleGothic"):
        try:
            from matplotlib import font_manager

            font_manager.findfont(fam, fallback_to_default=False)
            for t in [ax.title, ax.xaxis.label, ax.yaxis.label, *ax.get_legend().get_texts()]:
                t.set_fontfamily(fam)
            break
        except Exception:
            continue
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=120)
    plt.close(fig)


def features_of(path: Path, start: float = 0.0, end: float | None = None) -> dict:
    x, sr = load_mono(path)
    x = x[int(start * sr): len(x) if end is None else int(end * sr)]
    if len(x) < sr:
        raise SystemExit(f"{path}: 区間が短すぎます（1 秒以上にしてください）")
    return analyze(x, sr, "bass")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", type=Path, required=True, help="目標の wav（原曲のベースなど）")
    ap.add_argument("--target-start", type=float, default=0.0, help="目標の測る区間の開始（秒）")
    ap.add_argument("--target-end", type=float, help="目標の測る区間の終わり（秒）")
    ap.add_argument("recs", type=Path, nargs="+", help="候補の録音（reamp.py run の出力）")
    ap.add_argument("--max-hz", type=float, default=10000.0, help="距離に入れる上限（stem が目標なら 5000）")
    ap.add_argument("--plot", type=Path, help="1/3 オクターブの曲線を描いた PNG")
    ap.add_argument("-o", "--out", type=Path, help="結果の JSON")
    a = ap.parse_args(argv)

    for p in [a.target, *a.recs]:
        if not p.exists():
            raise SystemExit(f"ファイルがありません: {p}")
    print(f"目標を測っています: {a.target}", file=sys.stderr, flush=True)
    tf = features_of(a.target, a.target_start, a.target_end)
    cands = []
    for p in a.recs:
        print(f"候補を測っています: {p}", file=sys.stderr, flush=True)
        cands.append((p.stem, features_of(p)))
    res = compare_features(tf, cands, a.max_hz)
    res = {
        "target": {"path": str(a.target), "start_sec": a.target_start, "end_sec": a.target_end,
                   "rms_dbfs": tf["level"]["rms_dbfs"]},
        **res,
    }
    for r in res["candidates"]:
        r["path"] = str(a.recs[r["input_index"]])
    print(format_table(res))
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n")
        print(f"→ {a.out}", file=sys.stderr)
    if a.plot:
        plot(res, a.target.stem, a.plot)
        print(f"→ {a.plot}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

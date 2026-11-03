# 作った音の一覧

| 日付 | 曲・区間 | 楽器 | パッチ名 | ファイル | 評価・メモ |
|---|---|---|---|---|---|
| 2026-11-03 | セブンティーン 0:20〜0:28（通常） | GX-1B | 17 NORMAL | `output/セブンティーン/seventeen.tsl` U01 | モコモコ・輪郭なし（R1 外れ） |
| 2026-11-03 | セブンティーン 0:28〜0:40（スラップ） | GX-1B | 17 SLAP | 同 U02 | アタックが痛い・ローが足りない（R1 外れ） |
| 2026-11-03 | セブンティーン 通常 | GX-1B | 17 NORMAL A / B | `output/セブンティーン/seventeen-r2.tsl` U01 / U02 | **A を採用**（B は行き過ぎ） |
| 2026-11-03 | セブンティーン スラップ | GX-1B | 17 SLAP A / B | 同 U03 / U04 | **B を採用** |
| 2026-11-03 | 祝福 0:40〜0:52（明るめ） | GX-1B | SHUKU BRIGHT A / B | `output/rounds/r1-shukufuku-undead/shukufuku-undead.tsl` U01 / U02 | **A** |
| 2026-11-03 | 祝福 1:16〜1:36（暗め） | GX-1B | SHUKU DARK A / B | 同 U03 / U04 | **B**（歪みが強すぎる） |
| 2026-11-03 | UNDEAD 0:16〜0:28 | GX-1B | UNDEAD A / B | 同 U05 / U06 | **B** |
| 2026-11-03 | 祝福 明るめ | GX-1B | SHUKU BRIGHT 1 / 2 | `output/rounds/r2-shukufuku-undead/shukufuku-undead-r2.tsl` U01 / U02 | 未 |
| 2026-11-03 | 祝福 暗め | GX-1B | SHUKU DARK 1 / 2 | 同 U03 / U04 | 未 |
| 2026-11-03 | UNDEAD | GX-1B | UNDEAD 1 / 2 | 同 U05 / U06 | 未 |

## 採用した音（tone.json は `knowledge/tones/<曲>/`）

| 曲 | パターン | tone.json | 要点 |
|---|---|---|---|
| セブンティーン | 通常（0:20〜0:28） | `tones/seventeen/normal.json` | CONCERT gain 45、50/55/50、B8x10、DYN57、コンプ ON |
| セブンティーン | スラップ（0:28〜0:40） | `tones/seventeen/slap.json` | SW-TOUR gain 30、75/40/50、B2x15、RIBON121、コンプ ON |

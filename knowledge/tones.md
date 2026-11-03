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
| 2026-11-03 | 祝福 明るめ | GX-1B | SHUKU BRIGHT 1 / 2 | `output/rounds/r2-shukufuku-undead/shukufuku-undead-r2.tsl` U01 / U02 | **2 を採用** |
| 2026-11-03 | 祝福 暗め | GX-1B | SHUKU DARK 1 / 2 | 同 U03 / U04 | **2 を採用** |
| 2026-11-03 | UNDEAD | GX-1B | UNDEAD 1 / 2 | 同 U05 / U06 | どちらも潰れて抜けが悪い（コンプ 12:1 が疑わしい） |
| 2026-11-03 | UNDEAD | GX-1B | UNDEAD 1 / 2 / 3（R3） | `output/rounds/r3-undead/undead-r3.tsl` U01〜U03 | イメージに近づかない（中域を持ち上げていたのが逆だった） |
| 2026-11-03 | UNDEAD 40〜55 秒（スラップ） | GX-1B | UNDEAD SLAP A / B | `output/rounds/r4-undead/undead-r4.tsl` U01 / U02 | 未 |
| 2026-11-03 | UNDEAD 56〜67 秒（指弾き） | GX-1B | UNDEAD FINGER A / B | 同 U03 / U04 | 未 |

## 採用した音（tone.json は `knowledge/tones/<曲>/`）

| 曲 | パターン | tone.json | 要点 |
|---|---|---|---|
| セブンティーン | 通常（0:20〜0:28） | `tones/seventeen/normal.json` | CONCERT gain 45、50/55/50、B8x10、DYN57、コンプ ON |
| セブンティーン | スラップ（0:28〜0:40） | `tones/seventeen/slap.json` | SW-TOUR gain 30、75/40/50、B2x15、RIBON121、コンプ ON |
| 祝福 | 明るめ（0:40〜0:52） | `tones/shukufuku/bright.json` | STUDIO gain 35、50/60/55、B4x10、DYN57 ＋ BASS DI（drive 25、direct 70）＋ EQ（LOW CUT 40Hz、800Hz +3、HIGH +2） |
| 祝福 | 暗め（1:16〜1:36） | `tones/shukufuku/dark.json` | CLAS BLUE gain 20、60/50/45、B1x18、DYN57 ＋ EQ（LOW CUT 40Hz、250Hz -3、LOW +3、HIGH CUT 5kHz） |

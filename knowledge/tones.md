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
| 2026-11-03 | UNDEAD 40〜55 秒（スラップ） | GX-1B | UNDEAD SLAP A / B | `output/rounds/r4-undead/undead-r4.tsl` U01 / U02 | **B を採用**（音量が小さい → 上げた） |
| 2026-11-03 | UNDEAD 56〜67 秒（指弾き） | GX-1B | UNDEAD FINGER A / B | 同 U03 / U04 | **B を採用**（同上） |

## 採用した音（tone.json は `knowledge/tones/<曲>/`）

| 曲 | パターン | tone.json | 要点 |
|---|---|---|---|
| セブンティーン | 通常（0:20〜0:28） | `tones/seventeen/normal.json` | CONCERT gain 45、50/55/50、B8x10、DYN57、コンプ ON |
| セブンティーン | スラップ（0:28〜0:40） | `tones/seventeen/slap.json` | SW-TOUR gain 30、75/40/50、B2x15、RIBON121、コンプ ON |
| 祝福 | 曲全体（ピック。基準の区間 0:06〜0:21） | `tones/shukufuku/main.json` | SW-TOUR gain 30、70/25/48、B4x10、RIBON121 ＋ EQ（LOW CUT 40Hz、LOW +1、800Hz -10、HIGH -3、HIGH CUT 4kHz、LEVEL +1）＋ X-COMP 4:1・DIRECT 25。Phase 2（リアンプ）で詰めた最初の音。旧 bright / dark（耳だけで作った 2 パッチ）を置き換えた |
| UNDEAD | スラップ（40〜55 秒） | `tones/undead/slap.json` | SW-TOUR gain 25、60/35/60、level 60、B4x10、CND87 ＋ EQ（LOW CUT 31.5Hz、LOW +4、1kHz -7、HIGH +5、LEVEL +3）＋ X-COMP 4:1・DIRECT 40・ATTACK 70 |
| UNDEAD | 指弾き（56〜67 秒） | `tones/undead/finger.json` | STUDIO gain 30、55/40/55、level 60、B4x10、CND87 ＋ EQ（LOW CUT 31.5Hz、LOW +3、800Hz -6、HIGH +3、LEVEL +3）＋ X-COMP 3:1・DIRECT 50 |
| 2026-11-03 | 祝福（リアンプ R5〜R8） | GX-1B | SHUKU BR R5 1〜4 / SHUKUFUKU R6〜R8 | `output/rounds/r5-shuku-bright-reamp/` 〜 `r8-shukufuku/` | R5-4（SW-TOUR）が数値・耳とも近い → 高域が痛い → R8-4 を採用 |

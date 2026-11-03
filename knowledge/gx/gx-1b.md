# GX-1B（ベース用）

出典: BOSS「GX-1B パラメーター・ガイド／サウンド・リスト」（jpn01_W）。PDF は `input/` に置く（コミットしない）。
番号（.tsl に書く値）は**ガイドの並び順**。✅ は見本のパッチ（`samples/gx-1b_viva-beers-2026.tsl`）と BTS の表示で確かめたもの。

## ブロックとバイトの位置

| ブロック | GX-1B が使う欄 | 範囲 |
|---|---|---|
| AMP | byte 0 on、**byte 2 type**、3 gain、4 level、5 bass、6 middle、7 treble、**byte 9 speaker**、10 mic | gain 0〜120、他 0〜100 |
| ODDS（OD/DS） | 0 on、1 type、2 drive、3 tone（50 が 0）、4 level、5 direct | drive 0〜120、tone -50〜+50 |
| NS | 0 on、1 threshold、2 release、3 detect | 0〜100 |
| FX1〜3_COM | 0 on、**byte 2 type** | |
| FX 本体（251 バイト） | GX-1 と並びが違う欄がある（コンプの TYPE は byte 4 と考えられる）。**未解明なので型紙のまま使う** | |

AMP の byte 1・8、FX_COM の byte 1 はギター用の欄。GX-1B では書き換えない。

## AMP TYPE（16 種）

| # | 名前 | モデル（ガイドの説明） |
|---|---|---|
| 0 | NATURAL | 素直なクリーン（アンプ固有のクセを抑えたもの） |
| 1 | X-DRIVE | ベース用ハイゲイン（MDP） |
| 2 | CONCERT | Ampeg SVT |
| 3 | STUDIO | Markbass Little Mark III |
| 4 | SILVER | Fender Bassman100 |
| 5 | CLAS BLUE ✅ | acoustic 360 |
| 6 | SOLID STK | Gallien-Krueger 800RB |
| 7 | FAT TUBE | ORANGE AD200B MKIII |
| 8 | DARK DRV | Darkglass MICROTUBES B7K |
| 9 | ACOUSTIC | アコースティック・ベース向け |
| 10 | SUPR FLAT | フラットな特性 |
| 11 | FLIPTOP | Ampeg B-15 |
| 12 | SW-TOUR | SWR SM-400 |
| 13 | GT CRNCH | ギター・アンプ（クランチ） |
| 14 | GT HI GAIN | ギター・アンプ（ハイゲイン） |
| 15 | GT MODDED | ギター・アンプ（過激なゲイン） |

## SP TYPE

0 OFF / 1 ORIGINAL / 2 B1×15" / **3 B1×18" ✅** / 4 B2×15" / 5 B4×10"（密閉・大型） / 6 B8×10"（4×10 の 2 段） / 7〜14 USER1〜8

## MIC TYPE

0 DYN57 / 1 DYN421 / 2 CND451 / **3 CND87 ✅** / 4 FLAT / 5 RIBON121 / 6 BLEND A / 7 BLEND B / 8 BLEND C

## OD/DS TYPE（35 種。GX-1 と同じ並び）

0 MID BOOST / 1 CLEAN BST / 2 TREBLE BST / 3 NATURAL OD / 4 WARM OD / 5 BLUES OD / 6 OVERDRIVE / 7 CRUNCH /
8 T-SCREAM / 9 TURBO OD / 10 CENTA OD / 11 X-OD / 12 DIST / 13 A-DIST / 14 FAT DS / 15 LEAD DS / 16 RAT /
17 GUV DS / 18 DIST+ / 19 X-DIST / 20 METAL DS / 21 METAL ZONE / 22 HVY METAL / 23 METAL CORE / 24 OCT FUZZ /
25 60S FUZZ / 26 MUFF FUZZ / 27 BASS OD / 28 X-BASS OD / 29 BASS DS / 30 BASS DI（MXR Bass D.I.+） /
**31 SA DI DRIVE ✅**（SansAmp Bass Driver DI） / 32 HI BAND DRV（高域だけ歪む） / 33 BASS MT / 34 BASS FUZZ

## FX TYPE（39 種。**GX-1 と並びが違う**）

0 COMPRESSOR ✅ / 1 LIMITER / 2 ENHANCER / 3 TOUCH WAH / 4 AUTO WAH / 5 FIXED WAH / 6 DEFRETTER / 7 ENV FILTER /
8 BASS SYNTH / 9 SLOW GEAR / 10 AC BASS / 11 FEEDBACKER / 12 OD/DS / **13 PARA. EQ ✅** / 14 GEQ / 15 LOW GEQ /
16 HIGH GEQ / **17 CHORUS ✅** / 18 FLANGER / 19 PHASER / 20 SCRIPT PH / 21 CLASSIC-VIBE / 22 ROTARY / 23 VIBRATO /
24 TREMOLO / 25 SLICER / 26 OVERTONE（FX3 のみ） / 27 PAN / 28 RING MOD / 29 HUMANIZER / 30 PITCH SHIFT /
31 HARMONIST / 32 OCTAVE / 33 HEAVY OCT / 34 S-BEND / 35 PEDAL BEND / 36 TUNE DOWN / 37 DELAY / 38 REVERB

✅ のないもの（7 以降の多く）は並び順からの推定。使う前に BTS で 1 度確かめる。

COMPRESSOR の TYPE: BOSS COMP（CS-3） / D-COMP（MXR Dyna Comp） / ORANGE（Orange Squeezer） / X-COMP ✅ / STEREO

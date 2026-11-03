---
name: tone-analyze
description: 曲の音源からベース（またはギター）の音を取り出し、区間の音色を測って読み解く。「〇〇の 0:20〜0:40 の音を調べて」「この曲のベースを分析して」「どこからスラップか見て」などと言われたら使う。音作り（tone-design）の前段。
---

# 音色を測って読み解く（tone-analyze）

## 前提・参照資料
- `knowledge/gx/mapping.md` の「特徴の読み方」と実測の記録を読む（とくに stem の高域の扱い）
- 音源は `input/`（著作物。**コミットしない・外へ送らない**）。出力は `output/<曲名>/`（コミットしない）
- ツール: `tools/separate.py`・`tools/scan.py`・`tools/analyze.py`（どれも `uv run --script` で動く）

## 手順
1. **音源を確かめる**: `input/` のファイルを特定する。ベースだけの音源か（250Hz より下にエネルギーの 9 割前後が集まる）、曲全体かを見分ける
2. **楽器を取り出す**（曲全体のときだけ）:
   `tools/separate.py "input/<曲>.wav" --stem bass`（全体を一度取り出して `output/<曲>/bass.wav` を使い回す。CPU で 4 分の曲が数分。`--device mps` は動かない）
   - ギターは `--stem guitar`（htdemucs_6s。質はそこそこ）
3. **区間を区切って境目を探す**: `tools/scan.py output/<曲>/bass.wav --start <s> --end <e> --window 2`（細かく見るときは `--window 1`）
   - `hi_mid`（2〜5 kHz）・`centroid`・`decay`・`crest` が大きく変わる所が、弾き方（スラップ／指弾き／ピック）や場面の境目
   - 境目の秒数と根拠を出す。ユーザーが言った区間と食い違うときは、その旨を書く
4. **パターンごとに測る**: `tools/analyze.py <wav> --start <s> --end <e> -o output/<曲>/<パターン>.features.json`
5. **読み解く**: 下の観点で、音作りの担当者（bass-tech）が使える言葉にする
   - 1/3 オクターブ（`third_octave_db`、100Hz = 0dB）で **山と谷の位置**（例: 50Hz が山、630Hz〜1.25kHz が深い谷、2.5kHz で持ち上がる）
   - 歪み（`upper_harmonic_db`）、音量の揃い方（`range_p95_p10_db`）、伸び（`decay_db_per_sec`）、アタック（`crest_factor_db`）
   - **曲から取り出した stem の注意**: 5kHz より上はほぼ残らない・他の楽器に隠れて実際より暗く測れる。stem の高域・暗さは「参考」と明記し、設定の判断材料にしない。ベースだけの音源のときは高域まで信頼できる
   - 過去の採用パッチ（`knowledge/tones.md`）の特徴と比べて、どれに近いか

## 出力形式
```markdown
## 分析: <曲> <区間>
- 音源: <ベースだけ / 曲から取り出した stem>
- 境目: <秒> — <根拠>
### パターン: <名前>（<区間>）
| 特徴 | 値 | 読み方 |
|---|---|---|
...
- 1/3 オクターブの形: <山・谷・持ち上がりの位置と量>
- 似ている過去の音: <tones.md の名前と、どこが似ているか>
- 信頼度の注意: <stem の高域など>
- features.json: output/<曲>/<パターン>.features.json
```

## やってはいけないこと
- `input/`・`output/` の中身や音声ファイルをコミットしない。外部のサービスに送らない
- パラメーター（アンプの種類・EQ の値）を決めない（bass-tech の担当）
- stem の高域や暗さを、そのまま「暗い音」「高域が少ない音」と断定しない

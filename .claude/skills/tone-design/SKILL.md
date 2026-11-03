---
name: tone-design
description: 分析結果と感想から、GX-1B のベースの音作り（tone.json）の候補を作る・直す。「この分析で音を作って」「もっと抜けるように直して」「アタックが痛い」「モコモコする」などの音作りの依頼や、弾いた感想を受けたときに使う。
---

# ベースの音作り（tone-design）

## 前提・参照資料
- `knowledge/gx/mapping.md`（特徴 → パラメーターの対応と、これまでの当たり外れ・学び）を**必ず全部読む**
- `knowledge/gx/gx-1b.md`（アンプ・スピーカー・マイク・OD/DS・FX の名前と範囲。書き換えられる欄）
- `knowledge/tones.md` と `knowledge/tones/<曲>/*.json`（採用した音）
- tone.json の形は `tools/gxpatch.py`（`inspect` の出力と同じ形）。書ける欄: `amp`・`odds`・`ns`・`fx1`〜`fx3` の `on`、FX の `peq`（PARA. EQ）・`comp`（X-COMP）・`chorus`（rate/depth/level/direct）、`delay`・`reverb` の `on`、`name`（半角 16 文字まで）、`notes`

## 手順
1. **分析を読む**: tone-analyst の出力（1/3 オクターブの山と谷、歪み、伸び、アタック、stem の注意）
2. **キャラクターを言葉にする**: 例「太いロー・深いミッドの谷・2.5kHz と高域が残るハイファイな音」
3. **候補を A / B の 2 案作る**（1 回で方向を確かめるため）。A と B で変えるのは**1 つの軸だけ**（アンプの種類、または EQ・OD/DS の足し方）
   - アンプ: 音のキャラクターで選ぶ。**別の曲で当たったアンプを理由なく流用しない**
   - EQ（FX2 の PARA. EQ。アンプの後ろ）: 1/3 オクターブの谷の位置を MID FREQ で削る／持ち上げる。LOW CUT は 31.5〜40Hz。丸くしたいときはアンプの TREBLE ではなく HIGH CUT（5kHz など）で
   - OD/DS（アンプの前）: 芯を足すときは DIRECT 多め（60〜80）で薄く
   - コンプ（FX1、X-COMP）: **型紙のまま（RATIO 12:1・DIRECT 0）は強すぎて潰れる**。RATIO 3:1〜4:1、DIRECT 40〜50、スラップは ATTACK 70 前後から
   - stem から測った「暗さ」「高域の少なさ」は設定に写さない。TREBLE・MIDDLE は 50 前後から
   - EQ で大きく削る・DIRECT を上げると音量が下がる → amp の level か EQ の level で戻す
   - FX3・ディレイ・リバーブは、分析に根拠がなければ OFF
4. **tone.json を書く**: `output/rounds/<日付や回>-<曲>/<パターン>-<a|b>.json`。`notes` に「何を見て、何を変えたか」を 1〜2 文で書く
5. **感想を受けて直すとき**: 感想を mapping.md の学びと照らし、原因の仮説を立ててから直す。原因が切り分けられないときは、切り分ける候補（例: コンプを OFF にした版）を入れる
6. **採用されたら**: `knowledge/tones/<曲の英字名>/<パターン>.json` に保存し（`name` を最終名に、`notes` の先頭に「採用（どの回のどれ）」）、`knowledge/gx/mapping.md` に結果と学びを、`knowledge/tones.md` に評価を書く

## 出力形式
```markdown
## 音作り: <曲> <パターン>
- 狙い（キャラクター）: ...
| 候補 | アンプ | EQ | OD/DS | コンプ | 変えた軸 |
|---|---|---|---|---|---|
- tone.json: <パス一覧>
- 弾いて確かめてほしいこと: <A と B のどちらが近いか、など>
```

## やってはいけないこと
- 書けない欄（BOSS COMP など X-COMP 以外のコンプの中身、コーラスの TYPE、ディレイ・リバーブの中身、FX の種類の変更（PARA. EQ 以外））を書こうとしない。必要なら `## 要相談` で gx-operator に回す
- 感想を聞かずに「採用」として記録しない
- `input/`・`output/` の中身をコミットしない

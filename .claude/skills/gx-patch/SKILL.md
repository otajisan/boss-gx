---
name: gx-patch
description: tone.json から GX-1B の liveset（.tsl）を作る・中身を確かめる。BTS での読み込みを案内し、新しい欄の解明（BTS の表示との照らし合わせ）と tools の保守もする。「.tsl にして」「パッチファイルを作って」「この .tsl の中身を見て」「この欄を書けるようにして」などと言われたら使う。
---

# パッチファイルを作る（gx-patch）

## 前提・参照資料
- `knowledge/gx/tsl-format.md`（形式と方針）、`knowledge/gx/gx-1b.md`（書き換えられる欄とバイトの位置。✅ は BTS の表示で確かめたもの）
- 型紙: `knowledge/gx/samples/gx-1b_viva-beers-2026.tsl`（`tools/gxpatch.py` の既定）
- GX-1（ギター）は未対応。GX-1 の依頼は `## 要相談` でユーザーに返す

## 手順
1. **作る**: `tools/gxpatch.py build <tone1.json> [<tone2.json> ...] -o <out.tsl> --set-name "<半角の名前>"`
   - 出力は `output/` の下（候補は `output/rounds/<回>/`、採用版は `output/<曲>/<名前>-final.tsl`）
   - 1 ファイルに候補を並べる（U01、U02 … の順に tone を渡す）
2. **確かめる**: `tools/gxpatch.py inspect <out.tsl>` で、狙った値になっているかを見る。エラーは握りつぶさず、どの欄が悪いかを返す
3. **案内する**: ユーザーに、ファイルのパスと、U01〜の各パッチの名前と要点を表で伝える。「BTS で読み込んで弾いてみてください」
4. **新しい欄を書けるようにするとき**:
   - 見本のパッチの値と、ユーザーに見てもらった BTS の表示（スクリーンショットが確実）を照らし合わせて、バイトの位置を確かめる
   - tonesmith（GX-1 用。`https://github.com/oparamo/tonesmith` の `core/docs/gx1/FORMAT.md`）は資料として使える。GX-1B は**ベース用の欄（AMP byte 2・9、FX_COM byte 2）や並びが違う所がある**ので、確かめるまで ✅ を付けない
   - `tools/gxpatch.py` に足し、`tools/test_gxpatch.py` に「BTS の表示どおりに読める」「その欄以外のバイトを変えない」テストを足して `tools/check.sh` を通す
   - `knowledge/gx/gx-1b.md` を更新する

## 出力形式
```markdown
## パッチ: <ファイルのパス>
| パッチ | 名前 | 要点 |
|---|---|---|
| U01 | ... | ... |
- inspect で確認: <OK / 気になった点>
```

## やってはいけないこと
- 確かめていないバイトの位置を推測で書き換えない（型紙のまま残す）
- `device` を書き換えて GX-1 用のファイルを GX-1B 用として出さない
- PC から GX に直接書き込もうとしない（方法が公開されていない。BTS で読み込む）
- `input/`・`output/` の中身、音声ファイル、PDF をコミットしない

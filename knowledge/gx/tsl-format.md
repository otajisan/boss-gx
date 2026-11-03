# .tsl（BOSS TONE STUDIO の liveset）の形式

BOSS は形式を公開していない。解析済みの OSS **tonesmith**（https://github.com/oparamo/tonesmith 、MIT）の `core/docs/gx1/FORMAT.md` を基にする。
確かめた版: commit `41bcc66`（2026-10-21）。npm には公開されていない（clone して使う）。

## 中身のあらまし

- JSON。`{"name", "formatRev": "0000", "device", "data": [[ユーザーパッチ...], [プリセット]]}`
- 1 パッチ = `{"memo", "paramSet": {"MEMORY%<ブロック>": ["2 桁の 16 進", ...]}}`
- ブロック: COM（名前 16 バイト）・CHAIN・FX1〜3（_COM 3 バイト + 本体 251 バイト）・FX3A・ODDS・AMP・DLY・REV・PFX・FV・NS・OTHER・CTL・ASGN1〜8

## GX-1B について（2026-11-03 に確かめた）

見本: `samples/gx-1b_viva-beers-2026.tsl`（BOSS TONE EXCHANGE で公開済みのパッチ）

| 項目 | 結果 |
|---|---|
| `device` の文字列 | **`"GX-1B"`**（GX-1 は `"GX-1"`） |
| ブロックの種類と長さ | **GX-1 と全部同じ**（tonesmith の工場出荷パッチと比べた） |
| tonesmith で読めるか | そのままでは読めない（`device` が `"GX-1"` 以外だと拒否する: `core/src/device/gx1/format/tsl.ts` の `FILE_DEVICE`） |
| `device` を `"GX-1"` に置き換えて「読む → 書く」 | **1 バイトも変わらず一致**（`device` を戻すと元のファイルと同じ文字列になる） |

→ GX-1 の形式には最初から**ベース用の欄**がある（FORMAT.md で "bass-mode" と書かれている欄）。GX-1B は同じ形式で、ベース用の欄を使っていると考えられる。

| ブロック | ギター用 | ベース用（GX-1B が使うと考えられる） |
|---|---|---|
| AMP | byte 1 `type`（0–22）、byte 8 `speaker` | byte 2 `type_bass`、byte 9 `sp_type_bass` |
| FX1〜3_COM | byte 1 | byte 2 `type_bass` |
| FX 本体の FIXED WAH | p[1] 以外 | p[1] |
| PFX | byte 2 | byte 3 `subType_bass` |

見本の値: AMP = `01 01 05 …`（type=1, type_bass=5）、speaker=1, sp_type_bass=3。FX の _COM は byte 1 と 2 が同じ値（00/0D/11）。
OD/DS は共通の一覧に BASS OD・BASS DI・SA DI DRIVE などベース用のものが入っていて、見本は `SA DI DRIVE`（0x1F）と読めた。

### BTS の表示と照らし合わせた結果（見本 1 つ）

ユーザーが BTS で見本を開いて、表示名を確かめた。

| 欄 | 値 | BTS の表示 | わかったこと |
|---|---|---|---|
| AMP byte 2 `type_bass` | 5 | TYPE: **CLAS BLUE** | GX-1B のアンプは byte 2 を使う（byte 1 = 1 は使われていない） |
| AMP byte 9 `sp_type_bass` | 3 | SP TYPE: **B1 x 18** | GX-1B のスピーカーは byte 9 を使う |
| FX1_COM byte 1/2 | 0 / 0 | FX TYPE: COMPRESSOR | 0・13・17 は GX-1 とたまたま同じ。**FX の一覧は GX-1B では並びが違う**（`gx-1b.md`） |
| FX2_COM byte 1/2 | 13 / 13 | FX TYPE: PARA.EQ | 同上 |
| FX3_COM byte 1/2 | 17 / 17 | FX TYPE: CHORUS | 同上 |
| FX1 本体 byte 0 / byte 4 | 0 / 3 | TYPE: **X-COMP** | GX-1 ではコンプの種類は byte 0（0=BOSS COMP … 3=X-COMP）。見本は byte 0 = 0 で、byte 4 = 3。**GX-1B のコンプの種類は byte 4 にある**と考えられる（GX-1 の番号表と同じなら 3 = X-COMP）。FX2・FX3 の byte 4 は 0 |

### まだわからないこと

- アンプ・スピーカー・OD/DS・FX の一覧は Parameter Guide の並び順で `gx-1b.md` に書いた（見本と合う）。✅ のないものは BTS で確かめる
- コンプ以外にも、種類を GX-1 と違う場所に持つ FX があるか（CHORUS・OD/DS など、本体の先頭に種類を持つもの）
- tonesmith で読むと、ベース用の欄は「そのまま残す」だけで解釈されない（アンプは GX-1 の 1 番 `NATURAL` と出る）。GX-1B の値を読み書きするのはこちらの処理で行う

## 書き込みの方針（決定）

- tonesmith は GX-1B のベース用の欄を解釈しない（そのまま残すだけ）ので、GX-1B の書き込みには使わない
- `tools/gxpatch.py`（Python）: 確かめ済みの本物のパッチを**型紙**にして、意味がわかっている欄（AMP・OD/DS・NS、各ブロックの ON/OFF、名前）だけを書き換える。わからない欄は型紙のまま
- tonesmith の FORMAT.md は、バイトの位置を調べるときの資料として使う

## 生成したファイルが BTS で読み込めるか

- 2026-11-03: `gxpatch.py build` で作った 2 パッチの liveset（AMP の種類・値、スピーカー、マイク、NS、各ブロックの ON/OFF、名前を書き換えたもの）が、**BTS で読み込めた**（ユーザーが確認）

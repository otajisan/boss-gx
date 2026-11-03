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

### まだわからないこと

- GX-1B のアンプ（16 種）・スピーカーの**番号と名前の対応**。tonesmith には GX-1 の一覧しかない（見本の AMP を読むと GX-1 の 1 番 `NATURAL` と出るが、GX-1B で実際に使うのは type_bass=5 のはず）
- GX-1B の FX の種類の番号が GX-1 と同じか

## 書き込みの方針（案）

- tonesmith の codec（ブロックの読み書き）はそのまま使える。`device` の文字列と、ベース用の欄・番号の一覧を GX-1B 用に足す
- やり方: tonesmith に手を入れず、`device` を読む前に `"GX-1"`、書いた後に `"GX-1B"` に戻す薄い包みを `tools/gxpatch/` に作り、GX-1B の一覧はこちらで持つ

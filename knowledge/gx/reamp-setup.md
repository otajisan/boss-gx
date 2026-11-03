# リアンプの設定（USB オーディオ）

## Mac での認識（2026-11-03 に確認）

- ドライバー: BOSS の「GX-1 Driver」（macOS）。入れると `/Library/Audio/Plug-Ins/HAL/RDUSB033CAudio.driver` ができる
  - 入れる前は USB 機器としては見えるが、オーディオデバイスに出てこない
- USB: ベンダー BOSS、製品番号 `0x033C`
- **GX-1B をつないでも、USB の製品名・オーディオデバイス名は「GX-1」になる**。名前で GX-1 と GX-1B を見分けられない（同じドライバーで動く）
  - 両方を同時につなぐ場合の見分け方は未確認

| 項目 | GX-1B | GX-1 |
|---|---|---|
| デバイス名（Core Audio） | GX-1 | 未確認 |
| 入力（GX → PC） | 4ch | 未確認 |
| 出力（PC → GX） | 4ch | 未確認 |
| 既定のサンプリング周波数 | 48000 Hz | 未確認 |

確かめ方: `uv run --with sounddevice python -I -m sounddevice`

## チャンネルの割り当て（未確認）

4ch のうち、どれが EFX（処理後）、DRY（入力そのまま）、再生（PC → GX）かを実測して書く。

| 方向 | ch | 中身 |
|---|---|---|
| 入力 | 1-2 | 未確認 |
| 入力 | 3-4 | 未確認 |
| 出力 | 1-2 | 未確認 |
| 出力 | 3-4 | 未確認 |

## GX 側の設定（未確認）

- `DRY TO EFX` ON（PC から送った DI を EFX に通す）
- `LOOPBACK` OFF
- `DIR.MON.` の扱い
- 遅延の補正値

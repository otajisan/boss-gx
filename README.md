# boss-gx

好きな曲の音源から、そのギター（BOSS GX-1）・ベース（BOSS GX-1B）の音に近いパッチを作るための作業場です。
my-work-knowledge-base の workspace として、Claude Code が専門家（エージェント）とルール（スキル）に沿って作業します。

## 全体の流れ

```
曲の音源 ──分離(demucs)──▶ stem(ギター/ベース) ──分析──▶ features.json
                                                          │
                                         対応表(ルール)＋専門家の判断
                                                          ▼
                         tone.json（人が読める中間形式: アンプ・ゲイン・EQ・エフェクト）
                                                          │ tonesmith
                                                          ▼
                                              patch.tsl ──★BOSS TONE STUDIO で読み込み
リアンプで詰める:
 DI(本人の演奏) ──USB──▶ GX（候補パッチ）──USB──▶ 録音 ──比べる(stem と)──▶ スコア
          └──── 候補を作り直す（最大 3 ラウンド）◀──────────────┘
```

- **Phase 0**: workspace と土台。実機で .tsl の読み書きと USB のチャンネル配置を確かめる
- **Phase 1**: 分析 → パッチ（.tsl）を作る
- **Phase 2**: リアンプで録って比べ、パラメーターを詰める

## セットアップ（別の PC で使うとき）

フック（`.claude/settings.json`）とスキルの symlink が `../../shared` を参照するため、
**my-work-knowledge-base の `workspaces/boss-gx` に clone してください。**

```sh
cd <my-work-knowledge-base>/workspaces
git clone https://github.com/otajisan/boss-gx.git
cd boss-gx
git config core.hooksPath tools/git-hooks   # 音声ファイルのコミットを止めるフックを有効にする
kb boss-gx   # この workspace で Claude Code を起動
```

## ディレクトリ

| パス | 中身 |
|---|---|
| `knowledge/gx/` | GX-1 / GX-1B の知識（.tsl の形式、対応表、リアンプの設定など） |
| `knowledge/gx/samples/` | BOSS TONE STUDIO から書き出した .tsl の見本 |
| `tools/` | 分離・分析・パッチ生成・リアンプのスクリプト（Phase 1 以降） |
| `input/` | 曲の音源（**コミットしない**） |
| `output/` | stem・録音・生成物（**コミットしない**） |

## 注意

- 曲の音源・stem・録音は著作物を含むため、コミットしません（私的な利用の範囲で使います）。
  - `.gitignore` で `input/`・`output/` と音声ファイル（`*.wav` `*.mp3` など）を除外し、
    さらに `tools/git-hooks/pre-commit` が、強制的に add されたものもコミットの前に止めます。
- パッチは PC から直接書き込めないため、生成した .tsl は BOSS TONE STUDIO で手で読み込みます。

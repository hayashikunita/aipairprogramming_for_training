# RAG サンプル（ローカル簡易インデックス）

このフォルダは、小規模・学習用途向けの最小限な RAG 構成を提供します。

- 対象: .md / .txt をチャンク分割 → OpenAI Embeddings でベクトル化 → ローカルに保存（.npz + .jsonl）
- 検索: 質問を埋め込み → 上位K件をコサイン類似で取得 → コンテキストとして Chat へ投入
- 依存: openai, numpy（外部DB不要）

注意: 大規模運用には FAISS/Chroma/pgvector などの専用ベクトルDBを推奨します。本サンプルはシンプルさ重視です。

---

## まずはここから（3分クイックスタート）

1) 依存インストールとAPIキー設定（Windows PowerShell）

```powershell
pip install -r .\RAG\requirements.txt
$env:OPENAI_API_KEY = "sk-..."   # 一時的に有効
# 永続化（再起動後も使いたい場合）
# setx OPENAI_API_KEY "sk-..."
```

2) サンプル文書をインデックス化（埋め込みを作る）

```powershell
python .\RAG\ingest.py --input-dir .\RAG\data
```

3) 質問してみる

```powershell
python .\RAG\query.py --question "バックアップの実行時刻は？"
```

結果が返ればOKです。以降は詳細です。

---

## RAGとは？超ざっくり

- Retrieval Augmented Generation の略。外部知識（手元ドキュメントなど）を「検索→取り出して→LLMに渡す」ことで、最新かつ正確な回答を引き出します。
- 本サンプルでは、手元の .md/.txt（やPDF）を「ベクトル化」してローカル保存し、質問時に「似ている文章」を上位K件取り出してLLMへ渡します。

概念図:

```
┌─────────────┐    ┌─────────────┐
│  ドキュメント  │──▶│ ベクトル化(埋め込み) │──┐
└─────────────┘    └─────────────┘  │ 保存(.npz/.jsonl)
										  ▼
ユーザ質問 ──▶ ベクトル化 ──▶ 類似検索(上位K) ──▶ LLMへ文脈として渡す ──▶ 回答
```

## セットアップ

PowerShell（Windows）

```powershell
pip install -r .\RAG\requirements.txt
$env:OPENAI_API_KEY = "sk-..."
```

フォルダ構成（初期）

```
RAG/
	common.py         # 共有ユーティリティ（OpenAIクライアント、分割、埋め込み、類似度）
	ingest.py         # ドキュメント投入 → index.npz + meta.jsonl 生成
	query.py          # 質問 → 上位K抽出 → Chatに投げて回答
	requirements.txt  # 依存
	data/
		sample.md       # サンプル資料（ダミー）
	index/            # 生成物（初回は空）
```

## ドキュメント投入（ingest）

```powershell
# 乾式（プレビュー）
python .\RAG\ingest.py --input-dir .\RAG\data --dry-run

# 実行（埋め込みを作成して保存）
python .\RAG\ingest.py --input-dir .\RAG\data --emb-model text-embedding-3-small
```

主なオプション:
- --input-dir: 読み込み元（既定: .\RAG\data）
- --pattern: カンマ区切りglob（既定: **/*.md,**/*.txt）
- --chunk-size / --chunk-overlap: 文字数ベースの分割（既定: 800 / 200）
- --emb-model: 埋め込みモデル（既定: text-embedding-3-small）
- --out / --meta: 出力パス（既定: .\RAG\index\index.npz / .\RAG\index\meta.jsonl）
- --dry-run: 実行前に要約を表示

生成物:
- index.npz: ベクトル（float32）を格納
- meta.jsonl: 1行1チャンクのメタ（file, chunk_index, text）

小ネタ:
- `.npz` はNumPy配列の簡易保存形式。`index.npz` の中に `vectors` という配列名で埋め込みが入っています。
- `.jsonl` は「1行1JSON」。`meta.jsonl` はどのテキストが何番目のベクトルかを対応付けます。
- 文書を増やすときは、`RAG/data` に `.md` / `.txt` を追加して `ingest.py` を再実行（上書き保存）。

## 質問（query）

```powershell
# 乾式（Chatへの投入ペイロードを確認）
python .\RAG\query.py --question "バックアップの実行時刻は？" --dry-run

# 実行（上位Kを取り出して回答）
python .\RAG\query.py --question "バックアップの実行時刻は？" --k 4 --chat-model gpt-5
```

主なオプション:
- --index / --meta: 生成物のパス（既定: .\RAG\index\index.npz / .\RAG\index\meta.jsonl）
- --question: 質問（必須）
- --k: 取り出すチャンク数（既定: 4）
- --emb-model: クエリ埋め込みのモデル（既定: text-embedding-3-small）
- --chat-model: 回答生成モデル（既定: gpt-5）
- --system: 回答方針（既定: 根拠が無ければ「不明です」）
- --max-tokens, --temperature, --no-temperature, --dry-run

実装のポイント:
- 温度パラメータはAPI互換性を考慮し、エラー時に温度なしで自動リトライ
- プロンプトは「コンテキストと質問」を明示し、根拠の無い憶測を避ける指示を付与

ヒント:
- 最初は `--k 4` くらいが扱いやすいです。回答が薄い/根拠不十分なら `--k` を増やす、関係ない話が混じるなら減らす、で調整。
- `--system` は回答スタイルの統制に重要。運用ポリシー（「不明なら不明と答える」など）を明示しましょう。

## 設計メモ

- チャンク設計: 800文字/200文字オーバーラップは入門向けの妥協値。長文が多い、回答が根拠不足になる等の状況では調整してください。
- トークン制約: Chatに渡すコンテキストが長すぎると費用/品質に影響。まずは K=4 から開始し、必要に応じて増減。
- プライバシー: 機微情報をクラウドへ送る前に、適切な匿名化・削除・マスキングを検討。
- 多言語: 本サンプルは日本語前提。英語中心の場合は system プロンプトや前処理を英語化。

## うまくいかないとき

- "meta.jsonl が空です": 先に `ingest.py` を実行し、`data/` に .md/.txt があるか確認。
- "ベクトルが見つかりません": `index/index.npz` を確認。パスを --index で明示可能。
- ImportError: numpy が無い → `pip install -r .\RAG\requirements.txt` を再実行。
- APIキー関連: `$env:OPENAI_API_KEY` がセットされているか確認。

チェックリスト:
1) `pip show openai numpy` で依存が入っているか
2) `echo $env:OPENAI_API_KEY` でキーが設定されているか
3) `RAG/index/` に `index.npz` と `meta.jsonl` があるか
4) ネットワーク/プロキシでAPI疎通がブロックされていないか
5) モデル名のtypo（`text-embedding-3-small`, `gpt-5` など）がないか

## 次の一手（拡張アイデア）

- ベクトルDB化: FAISS/Chroma/pgvector に移行し、スケールと検索性能を強化。
- ドキュメント対応拡大: PDF/Word/HTML 取り込み（pypdf/pdfminer, python-docx, trafilatura 等）。
- 品質評価: 合成質問集を用意し、RAG有無で回答の正確性を測定（Simple eval スクリプト）。
- 応答整形: JSON Schema で構造化出力し、UIや下流処理に繋げる。

---

## 追加サンプル

### HyDE クエリ（仮想文書を使った検索の強化）

ファイル: `hyde_query.py`

手順: 質問 → Chatで「理想的な短い要約文（仮想文書）」を生成 → その埋め込みで検索 → 回答。

```powershell
python .\RAG\hyde_query.py --question "SLAの一次回答時間は？" --dry-run
python .\RAG\hyde_query.py --question "SLAの一次回答時間は？" --k 4 --chat-model gpt-5
```

メモ: 通常のクエリよりも、検索時の表現揺れに頑健になることが期待できます。

### PDF の投入

ファイル: `ingest_pdf.py`

```powershell
python .\RAG\ingest_pdf.py --input-dir .\RAG\data --pattern "**/*.pdf" --dry-run
python .\RAG\ingest_pdf.py --input-dir .\RAG\data --pattern "**/*.pdf"
```

メモ: `pypdf` でテキスト抽出しています。レイアウト依存で改行等が崩れる場合があります。

### Chat による再ランク付け（Re-ranking）

ファイル: `rerank_with_chat.py`

流れ: まず埋め込みで上位Kを取得 → Chat に候補の関連度をJSONで採点させる → 上位から最終K件を採用 → 回答。

```powershell
python .\RAG\rerank_with_chat.py --question "導入コストの考慮点は？" --dry-run
python .\RAG\rerank_with_chat.py --question "導入コストの考慮点は？" --k 8 --final-k 4 --chat-model gpt-5
```

メモ: JSON解析が失敗した場合はフォールバックとして初回の順序を使用します。

---

## よくある質問（FAQ）

Q. 埋め込みモデルはどれを選べば良い？

- まずは `text-embedding-3-small`（軽量でコスパ良し）。より高精度なら `text-embedding-3-large`。

Q. 回答モデルは？

- 学習用途なら `gpt-5` を既定にしていますが、コスト/速度重視なら `gpt-4o-mini` 等も検討。

Q. コストはどれくらい？

- ドキュメント投入時: トークン数（文字数）× 埋め込み単価。長文・大量投入でコスト増。
- 質問時: コンテキスト長（上位Kで増える）× 回答トークンで変動。`--k` と `--max-tokens` を調整。

Q. どのくらいの粒度で分割すべき？

- 目安は 500〜1200 文字。短すぎると前後関係が切れ、長すぎると検索が粗くなります。ドメインごとに調整。

Q. インデックスを作り直すには？

- `RAG/index/` の `index.npz` と `meta.jsonl` を削除してから `ingest.py` を再実行。

---

## セキュリティ/プライバシーの注意

- 機微情報は投入前にマスキング/匿名化してください。API先はクラウドです。
- ローカルの `meta.jsonl` には生テキストが入ります。アクセス権限管理に注意。
- 録画や画面共有時は APIキーや内部URL が映らないようにしましょう。

---

## スクリプトごとの役割（まとめ）

- `ingest.py`: .md/.txt をチャンク→埋め込み→`index/index.npz` と `index/meta.jsonl` へ保存
- `query.py`: 質問→埋め込み→上位K→コンテキスト付きでChat→回答
- `ingest_pdf.py`: PDF抽出（pypdf）→チャンク→埋め込み→保存
- `hyde_query.py`: 質問から「仮想要約」を生成→その埋め込みで検索→回答
- `rerank_with_chat.py`: 初回KをChatで採点→上位を採用→回答


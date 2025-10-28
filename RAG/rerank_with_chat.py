#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional

from common import client, embed_texts, pretty, top_k_similar


def _load_meta(meta_path: Path) -> List[Dict]:
    items: List[Dict] = []
    if not meta_path.exists():
        return items
    with meta_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                pass
    return items


def _load_vectors(npz_path: Path):
    import numpy as np
    if not npz_path.exists():
        raise FileNotFoundError(f"ベクトルが見つかりません: {npz_path}")
    data = np.load(npz_path)
    return data["vectors"]


def _chat_rerank(question: str, candidates: List[str], model: str, max_tokens: int, temperature: Optional[float]) -> List[int]:
    """Chatに候補を採点させ、上位のインデックスを返す。解析失敗時は元順序を返す。"""
    c = client()
    # シンプルなJSON出力を要求
    system = "あなたは問い合わせと候補テキストの関連度を0..10で採点する評価者です。"
    user = (
        "次の質問に対して、各候補の関連度を整数0..10で採点し、JSONで返してください。\n"
        "JSON形式: {\"scores\": [{\"index\": <int>, \"score\": <int>}, ...]}\n"
        f"質問: {question}\n"
        "候補:\n" + "\n".join(f"[{i}] {txt[:500]}" for i, txt in enumerate(candidates))
    )
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    payload: Dict = {"model": model, "messages": messages, "max_tokens": max_tokens, "response_format": {"type": "json_object"}}
    if temperature is not None:
        payload["temperature"] = temperature
    try:
        resp = c.chat.completions.create(**payload)
    except Exception:
        # フォールバック: 温度なし
        payload.pop("temperature", None)
        resp = c.chat.completions.create(**payload)

    text = (resp.choices[0].message.content or "").strip()
    try:
        data = json.loads(text)
        scores = data.get("scores") or []
        # 高得点順に index を返す
        ordered = sorted(scores, key=lambda x: int(x.get("score", 0)), reverse=True)
        idxs = [int(x.get("index")) for x in ordered if 0 <= int(x.get("index", -1)) < len(candidates)]
        # 重複除去して返す（足りない分は元順序で補完）
        seen = set()
        result = []
        for i in idxs:
            if i not in seen:
                seen.add(i)
                result.append(i)
        for i in range(len(candidates)):
            if i not in seen:
                result.append(i)
        return result
    except Exception:
        return list(range(len(candidates)))


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="RAG: re-rank top-K with Chat and answer")
    p.add_argument("--question", required=True)
    p.add_argument("--index", default="./RAG/index/index.npz")
    p.add_argument("--meta", default="./RAG/index/meta.jsonl")
    p.add_argument("--k", type=int, default=8, help="初回取得K")
    p.add_argument("--final-k", type=int, default=4, help="最終的に使うK")
    p.add_argument("--emb-model", default="text-embedding-3-small")
    p.add_argument("--chat-model", default="gpt-5")
    p.add_argument("--system", default="あなたは有能な日本語アシスタントです。提供されたコンテキストのみで回答。")
    p.add_argument("--max-tokens", type=int, default=512)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--no-temperature", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    index_path = Path(args.index).resolve()
    meta_path = Path(args.meta).resolve()

    if args.dry_run:
        print("[DRY-RUN] rerank flow: embeddings -> top-K -> chat scoring -> final-K -> answer")
        return 0

    vectors = _load_vectors(index_path)
    meta_items = _load_meta(meta_path)
    if not len(meta_items):
        raise RuntimeError("meta.jsonl が空です。先に ingest.py を実行してください。")

    q_vec = embed_texts([args.question], model=args.emb_model, dry_run=False)[0]
    top = top_k_similar(q_vec, vectors, args.k)
    candidates: List[str] = []
    for i, score in top:
        if 0 <= i < len(meta_items):
            candidates.append(meta_items[i].get("text", ""))

    temp_val = None if args.no_temperature else args.temperature
    order = _chat_rerank(args.question, candidates, args.chat_model, max_tokens=256, temperature=temp_val)

    chosen = [candidates[i] for i in order[: args.final_k]]
    messages = [
        {"role": "system", "content": args.system},
        {
            "role": "user",
            "content": (
                "以下のコンテキストを参照して質問に答えてください。\n\n"
                + "\n\n".join(f"- {c}" for c in chosen)
                + f"\n\n質問: {args.question}"
            ),
        },
    ]
    payload = {"model": args.chat_model, "messages": messages, "max_tokens": args.max_tokens}
    if not args.no_temperature:
        payload["temperature"] = args.temperature

    c = client()
    try:
        resp = c.chat.completions.create(**payload)
    except Exception as e:
        if "temperature" in payload and "temperature" in str(e).lower():
            payload.pop("temperature", None)
            resp = c.chat.completions.create(**payload)
        else:
            raise
    print((resp.choices[0].message.content or "").strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

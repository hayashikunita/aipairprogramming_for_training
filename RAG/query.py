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


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="RAG: query with simple local index")
    p.add_argument("--index", default="./RAG/index/index.npz")
    p.add_argument("--meta", default="./RAG/index/meta.jsonl")
    p.add_argument("--question", required=True)
    p.add_argument("--k", type=int, default=4)
    p.add_argument("--emb-model", default="text-embedding-3-small")
    p.add_argument("--chat-model", default="gpt-5")
    p.add_argument("--system", default="あなたは有能な日本語アシスタントです。提供されたコンテキストのみを根拠に、誠実に回答してください。根拠がなければ『不明です』と答えてください。")
    p.add_argument("--max-tokens", type=int, default=512)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--no-temperature", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    index_path = Path(args.index).resolve()
    meta_path = Path(args.meta).resolve()

    if args.dry_run:
        meta_items = _load_meta(meta_path)
        contexts = [it.get("text", "")[:200] for it in meta_items[:args.k]] or ["<no-meta>"]
        messages = [
            {"role": "system", "content": args.system},
            {
                "role": "user",
                "content": (
                    "以下のコンテキストを参照して質問に答えてください。\n\n"
                    + "\n\n".join(f"- {c}" for c in contexts)
                    + f"\n\n質問: {args.question}"
                ),
            },
        ]
        payload = {"model": args.chat_model, "messages": messages, "max_tokens": args.max_tokens}
        if not args.no_temperature:
            payload["temperature"] = args.temperature
        print("[DRY-RUN] chat.completions.create payload (RAG):")
        print(pretty(payload))
        return 0

    # 実行: 埋め込み→検索→Chat
    vectors = _load_vectors(index_path)
    meta_items = _load_meta(meta_path)
    if not len(meta_items):
        raise RuntimeError("meta.jsonl が空です。先に ingest.py を実行してください。")

    q_vec = embed_texts([args.question], model=args.emb_model, dry_run=False)[0]
    top = top_k_similar(q_vec, vectors, args.k)
    contexts: List[str] = []
    for i, score in top:
        if 0 <= i < len(meta_items):
            contexts.append(meta_items[i].get("text", ""))

    messages = [
        {"role": "system", "content": args.system},
        {
            "role": "user",
            "content": (
                "以下のコンテキストを参照して質問に答えてください。\n\n"
                + "\n\n".join(f"- {c}" for c in contexts)
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

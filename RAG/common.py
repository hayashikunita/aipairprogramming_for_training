#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from typing import Any, Iterable, List, Tuple


def need_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY が未設定です。PowerShell では\n"
            "  $env:OPENAI_API_KEY = \"sk-...\"\n"
            "  setx OPENAI_API_KEY \"sk-...\"  # 永続\n"
        )


def client() -> Any:
    need_key()
    from openai import OpenAI  # type: ignore
    return OpenAI()


def pretty(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)


def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 200) -> List[str]:
    """単純な固定長分割（日本語も扱いやすいように文字数ベース）"""
    if chunk_size <= 0:
        return [text]
    chunks: List[str] = []
    i = 0
    n = len(text)
    step = max(1, chunk_size - max(0, chunk_overlap))
    while i < n:
        chunks.append(text[i : i + chunk_size])
        i += step
    return chunks


def cosine_sim_matrix(a, b):
    import numpy as np

    a = a.astype("float32")
    b = b.astype("float32")
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-8)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-8)
    return a_norm @ b_norm.T


def top_k_similar(query_vec, vectors, k: int) -> List[Tuple[int, float]]:
    import numpy as np

    q = query_vec.reshape(1, -1)
    sims = cosine_sim_matrix(q, vectors)[0]
    idx = np.argsort(-sims)[:k]
    return [(int(i), float(sims[i])) for i in idx]


def embed_texts(texts: Iterable[str], model: str, dry_run: bool = False):
    import numpy as np

    if dry_run:
        # 乾式: ダミー埋め込み（固定次元=1536）
        rng = np.random.default_rng(42)
        return rng.normal(size=(len(list(texts)), 1536)).astype("float32")

    c = client()
    # OpenAI SDK v1: embeddings.create は一括で応答
    resp = c.embeddings.create(model=model, input=list(texts))
    vecs = [d.embedding for d in resp.data]
    return np.array(vecs, dtype="float32")

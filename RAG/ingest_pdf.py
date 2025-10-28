#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional

from common import chunk_text, embed_texts, pretty


def _extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as e:
        raise RuntimeError("pypdf が必要です。pip install pypdf") from e

    reader = PdfReader(str(path))
    texts: List[str] = []
    for page in reader.pages:
        t = page.extract_text() or ""
        texts.append(t)
    return "\n".join(texts)


def _gather_chunks(input_dir: Path, patterns: List[str], chunk_size: int, chunk_overlap: int) -> List[Dict]:
    items: List[Dict] = []
    for pat in patterns:
        for p in input_dir.rglob(pat):
            if not p.is_file():
                continue
            if p.suffix.lower() != ".pdf":
                continue
            text = _extract_pdf_text(p)
            chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            for i, ch in enumerate(chunks):
                items.append({
                    "file": str(p.resolve()),
                    "chunk_index": i,
                    "text": ch,
                })
    return items


def _save_index(out_npz: Path, meta_jsonl: Path, vectors, items: List[Dict]) -> None:
    import numpy as np

    out_npz.parent.mkdir(parents=True, exist_ok=True)
    meta_jsonl.parent.mkdir(parents=True, exist_ok=True)

    np.savez(out_npz, vectors=vectors)
    with meta_jsonl.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="RAG: ingest PDFs -> build simple local index")
    p.add_argument("--input-dir", default="./RAG/data", help="入力ディレクトリ")
    p.add_argument("--pattern", default="**/*.pdf", help="PDFのglobパターン")
    p.add_argument("--chunk-size", type=int, default=1200)
    p.add_argument("--chunk-overlap", type=int, default=200)
    p.add_argument("--emb-model", default="text-embedding-3-small")
    p.add_argument("--out", default="./RAG/index/index.npz")
    p.add_argument("--meta", default="./RAG/index/meta.jsonl")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    input_dir = Path(args.input_dir).resolve()
    patterns = [s.strip() for s in args.pattern.split(",") if s.strip()]
    out_npz = Path(args.out).resolve()
    meta_jsonl = Path(args.meta).resolve()

    items = _gather_chunks(input_dir, patterns, args.chunk_size, args.chunk_overlap)

    if args.dry_run:
        preview = {
            "input_dir": str(input_dir),
            "patterns": patterns,
            "chunks": len(items),
            "emb_model": args.emb_model,
            "out_npz": str(out_npz),
            "meta_jsonl": str(meta_jsonl),
            "sample": items[:1],
        }
        print("[DRY-RUN] ingest-pdf preview:")
        print(pretty(preview))
        return 0

    vectors = embed_texts((it["text"] for it in items), model=args.emb_model, dry_run=False)
    _save_index(out_npz, meta_jsonl, vectors, items)
    print(f"saved index: {out_npz}")
    print(f"saved meta:  {meta_jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

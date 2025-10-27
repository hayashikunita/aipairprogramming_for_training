#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import base64
import json
import os
from typing import Any


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


def save_b64_png(b64: str, out_path: str) -> None:
    data = base64.b64decode(b64)
    with open(out_path, "wb") as f:
        f.write(data)


def pretty(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)

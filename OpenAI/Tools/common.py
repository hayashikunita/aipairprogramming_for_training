#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

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


def pretty(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)

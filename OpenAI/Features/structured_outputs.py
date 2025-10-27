#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
import json
from typing import Any, Dict, Optional
from common import client

SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "products": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": "number", "minimum": 0},
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "price"],
                "additionalProperties": False,
            },
            "minItems": 1,
        }
    },
    "required": ["products"],
    "additionalProperties": False,
}


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Structured outputs: JSON Schema で厳密出力")
    p.add_argument("-p", "--prompt", required=True, help="例: '商品を3つ提案して' など")
    p.add_argument("--model", default="gpt-5")
    p.add_argument("--use-json-object", action="store_true", help="json_object モード（簡易）")
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--no-temperature", action="store_true")
    args = p.parse_args(argv)

    c = client()
    messages = [{"role": "user", "content": args.prompt}]

    if args.use_json_object:
        payload = {
            "model": args.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
        }
    else:
        payload = {
            "model": args.model,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "products", "schema": SCHEMA, "strict": True},
            },
        }
    if not args.no_temperature:
        payload["temperature"] = args.temperature

    resp = c.chat.completions.create(**payload)
    text = (resp.choices[0].message.content or "").strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print(text)
        return 0
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

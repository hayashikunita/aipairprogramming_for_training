#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JSON Schema 応答サンプル v2

v1 との差分:
- 外部スキーマファイルを --schema-file で読み込み可能
- ネスト構造のサンプルスキーマ (invoice) を内蔵
- --dry-run / --no-temperature / ローカル検証 などの基本機能は踏襲
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

DEFAULT_MODEL = os.getenv("OPENAI_GPT5_MODEL", os.getenv("OPENAI_CHAT_MODEL", "gpt-5"))


def _lazy_imports():
    try:
        from openai import OpenAI  # type: ignore
    except Exception as e:
        raise RuntimeError("OpenAI SDK が見つかりません。`pip install openai` を実行してください。") from e
    try:
        import jsonschema  # type: ignore
    except Exception:
        jsonschema = None
    return OpenAI, jsonschema


def require_key_or_dry_run(dry_run: bool) -> None:
    if dry_run:
        return
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY が未設定です。PowerShell では\n"
            "  $env:OPENAI_API_KEY = \"sk-...\"\n"
            "  setx OPENAI_API_KEY \"sk-...\"  # 永続\n"
        )


# 内蔵のネスト構造スキーマ: 請求書 -------------------------------------------------

INVOICE_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "invoice_id": {"type": "string"},
        "issue_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
        "seller": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "address": {"type": "string"},
                "tax_id": {"type": "string"},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        "buyer": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "address": {"type": "string"},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        "items": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "quantity": {"type": "number", "minimum": 0},
                    "unit_price": {"type": "number", "minimum": 0},
                    "tax_rate": {"type": "number", "minimum": 0},
                },
                "required": ["description", "quantity", "unit_price"],
                "additionalProperties": False,
            },
        },
        "currency": {"type": "string", "minLength": 1},
        "total": {"type": "number", "minimum": 0},
    },
    "required": ["invoice_id", "issue_date", "seller", "buyer", "items", "currency"],
    "additionalProperties": False,
}


BUILTIN_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "invoice": INVOICE_SCHEMA,
}


def build_payload(prompt: str, schema: Dict[str, Any], schema_name: str, *, model: str, system: Optional[str], temperature: Optional[float], include_temperature: bool) -> Dict[str, Any]:
    messages = [
        {"role": "system", "content": system or "あなたは JSON を厳密に生成する日本語アシスタントです。"},
        {"role": "user", "content": prompt},
    ]
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "schema": schema,
                "strict": True,
            },
        },
    }
    if include_temperature and temperature is not None:
        payload["temperature"] = temperature
    return payload


def run_with_schema(prompt: str, schema: Dict[str, Any], schema_name: str, *, model: str, system: Optional[str], temperature: float, include_temperature: bool, dry_run: bool) -> Dict[str, Any]:
    payload = build_payload(prompt, schema, schema_name, model=model, system=system, temperature=temperature, include_temperature=include_temperature)

    if dry_run:
        print("[DRY-RUN] chat.completions.create payload (json_schema):")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return {}

    OpenAI, jsonschema = _lazy_imports()
    client = OpenAI()

    try:
        resp = client.chat.completions.create(**payload)
    except Exception as e:
        if "temperature" in payload and "temperature" in str(e).lower():
            payload.pop("temperature", None)
            resp = client.chat.completions.create(**payload)
        else:
            raise

    text = (resp.choices[0].message.content or "").strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text, "error": "not_json"}

    if jsonschema is not None:
        try:
            jsonschema.validate(instance=data, schema=schema)
        except Exception as ve:
            data["validation_error"] = str(ve)
    else:
        data["validation_note"] = "jsonschema が未インストールのため検証スキップ"
    return data


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="JSON Schema 応答サンプル v2")
    p.add_argument("-p", "--prompt", required=True, help="ユーザープロンプト")
    p.add_argument("--schema", choices=sorted(BUILTIN_SCHEMAS.keys()), default="invoice", help="内蔵スキーマ名")
    p.add_argument("--schema-file", default=None, help="外部スキーマ(JSON)のパス。指定時はこれを優先")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--system", default=None)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--no-temperature", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    try:
        require_key_or_dry_run(args.dry_run)
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        if not args.dry_run:
            return 2

    # スキーマ決定
    schema_name = "schema_builtin_" + args.schema
    schema: Dict[str, Any]
    if args.schema_file:
        try:
            with open(args.schema_file, "r", encoding="utf-8") as f:
                schema = json.load(f)
            schema_name = os.path.splitext(os.path.basename(args.schema_file))[0]
        except Exception as e:
            print(f"外部スキーマ読込エラー: {e}", file=sys.stderr)
            return 2
    else:
        schema = BUILTIN_SCHEMAS[args.schema]

    data = run_with_schema(
        prompt=args.prompt,
        schema=schema,
        schema_name=schema_name,
        model=args.model,
        system=args.system,
        temperature=args.temperature,
        include_temperature=not args.no_temperature,
        dry_run=args.dry_run,
    )

    if data:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

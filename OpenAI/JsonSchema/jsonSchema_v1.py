#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JSON Schema を用いた OpenAI 応答の構造化サンプル

ポイント:
- Chat Completions API の response_format=json_schema を使用
- --dry-run で送信ペイロードのみ表示（APIキー不要）
- 返却JSONを Python 側でも jsonschema で検証（任意）

事前準備:
  pip install -r requirements.txt
  PowerShell: $env:OPENAI_API_KEY = "sk-..."
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
	except Exception as e:  # pragma: no cover
		raise RuntimeError("OpenAI SDK が見つかりません。`pip install openai` を実行してください。") from e
	try:
		import jsonschema  # type: ignore
	except Exception:
		jsonschema = None  # optional
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


# 組み込みスキーマ例 ---------------------------------------------------------

SCHEMAS: Dict[str, Dict[str, Any]] = {
	"todo": {
		"$schema": "https://json-schema.org/draft/2020-12/schema",
		"type": "object",
		"properties": {
			"items": {
				"type": "array",
				"minItems": 1,
				"items": {
					"type": "object",
					"properties": {
						"title": {"type": "string", "minLength": 1},
						"priority": {"type": "string", "enum": ["low", "medium", "high"]},
						"due_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
					},
					"required": ["title", "priority"],
					"additionalProperties": False,
				},
			}
		},
		"required": ["items"],
		"additionalProperties": False,
	},
	"contact": {
		"$schema": "https://json-schema.org/draft/2020-12/schema",
		"type": "object",
		"properties": {
			"name": {"type": "string"},
			"email": {"type": "string", "format": "email"},
			"phone": {"type": "string"},
		},
		"required": ["name", "email"],
		"additionalProperties": False,
	},
}


def build_payload(
	prompt: str,
	schema: Dict[str, Any],
	schema_name: str,
	model: str,
	system: Optional[str],
	temperature: Optional[float],
	include_temperature: bool,
) -> Dict[str, Any]:
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


def run_json_schema(
	prompt: str,
	schema_key: str,
	model: str = DEFAULT_MODEL,
	system: Optional[str] = None,
	temperature: float = 0.0,
	include_temperature: bool = True,
	dry_run: bool = False,
) -> Dict[str, Any]:
	if schema_key not in SCHEMAS:
		raise ValueError(f"未知のスキーマです: {schema_key} (choices: {list(SCHEMAS)})")
	schema = SCHEMAS[schema_key]
	payload = build_payload(
		prompt=prompt,
		schema=schema,
		schema_name=f"schema_{schema_key}",
		model=model,
		system=system,
		temperature=temperature,
		include_temperature=include_temperature,
	)

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
		# 何らかの理由で JSON でない場合に備えたフォールバック
		return {"raw": text, "error": "not_json"}

	# 任意: Python 側でもスキーマ検証
	if jsonschema is not None:
		try:
			jsonschema.validate(instance=data, schema=schema)
		except Exception as ve:
			data["validation_error"] = str(ve)
	else:
		data["validation_note"] = "jsonschema が未インストールのため検証スキップ"
	return data


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
	p = argparse.ArgumentParser(description="JSON Schema 応答サンプル (Chat Completions)")
	p.add_argument("-p", "--prompt", required=True, help="ユーザープロンプト")
	p.add_argument("--schema", choices=sorted(SCHEMAS.keys()), default="todo")
	p.add_argument("--model", default=DEFAULT_MODEL, help="使用モデル")
	p.add_argument("--system", default=None, help="system プロンプト上書き")
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

	data = run_json_schema(
		prompt=args.prompt,
		schema_key=args.schema,
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


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GPT-5 学習用サンプルスクリプト

- 基本のチャット応答 (chat)
- JSON 形式での出力 (json)
- ツール呼び出しのデモ (tools)

環境変数 OPENAI_API_KEY を使用します。キーが無い場合は --dry-run で
送信ペイロードの確認ができます。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

# zoneinfo は Python 3.9+ で利用可能
try:
	from zoneinfo import ZoneInfo  # type: ignore
except Exception:  # pragma: no cover
	ZoneInfo = None  # type: ignore


DEFAULT_MODEL = os.getenv("OPENAI_GPT5_MODEL", "gpt-5")


def _lazy_import_openai():
	"""OpenAI SDK を必要な時にのみ import する。"""
	try:
		from openai import OpenAI  # type: ignore
		return OpenAI
	except Exception as e:  # pragma: no cover - import 時の例外をユーザーに伝える
		raise RuntimeError(
			"OpenAI SDK が見つかりません。`pip install openai` を実行してください。"
		) from e


def get_api_key() -> Optional[str]:
	return os.getenv("OPENAI_API_KEY")


def ensure_api_key_or_dry_run(dry_run: bool) -> None:
	if not dry_run and not get_api_key():
		raise RuntimeError(
			"OPENAI_API_KEY が設定されていません。PowerShell では\n"
			"    $env:OPENAI_API_KEY = \"sk-...\"\n"
			"で一時設定、または\n"
			"    setx OPENAI_API_KEY \"sk-...\"\n"
			"で永続設定できます (再起動後有効)。"
		)


def build_client() -> Any:
	OpenAI = _lazy_import_openai()
	# API キーは環境変数から自動取得される
	return OpenAI()


def run_chat(
	prompt: str,
	model: str = DEFAULT_MODEL,
	system: str = "あなたは有能な日本語アシスタントです。",
	temperature: float = 0.2,
	max_tokens: int = 4096,
	dry_run: bool = False,
	include_temperature: bool = True,
) -> str:
	messages = [
		{"role": "system", "content": system},
		{"role": "user", "content": prompt},
	]

	payload = {
		"model": model,
		"messages": messages,
		"max_tokens": max_tokens,
	}
	if include_temperature and temperature is not None:
		payload["temperature"] = temperature

	if dry_run:
		print("[DRY-RUN] chat payload:")
		print(json.dumps(payload, ensure_ascii=False, indent=2))
		return ""

	client = build_client()
	try:
		resp = client.chat.completions.create(**payload)
	except Exception as e:
		# 一部モデルで temperature が未対応/無視されるケースに備えて再試行
		if "temperature" in payload and "temperature" in str(e).lower():
			payload.pop("temperature", None)
			resp = client.chat.completions.create(**payload)
		else:
			raise
	return (resp.choices[0].message.content or "").strip()


def run_json(
	prompt: str,
	model: str = DEFAULT_MODEL,
	system: str = "あなたは日本語で正確に JSON を生成します。",
	temperature: float = 0.0,
	max_tokens: int = 2048,
	dry_run: bool = False,
	include_temperature: bool = True,
) -> Dict[str, Any]:
	messages = [
		{"role": "system", "content": system},
		{"role": "user", "content": prompt},
	]

	# Chat Completions の JSON モード
	payload = {
		"model": model,
		"messages": messages,
		"max_tokens": max_tokens,
		"response_format": {"type": "json_object"},
	}
	if include_temperature and temperature is not None:
		payload["temperature"] = temperature

	if dry_run:
		print("[DRY-RUN] json payload:")
		print(json.dumps(payload, ensure_ascii=False, indent=2))
		return {}

	client = build_client()
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
		return json.loads(text)
	except json.JSONDecodeError:
		# モデルによっては余計なテキストが混じる可能性があるためフォールバック
		return {"raw": text}


# ---- ツール呼び出しデモ用の関数定義 --------------------------------------


def tool_get_time(timezone: str = "UTC") -> str:
	"""指定タイムゾーンの現在時刻を ISO8601 で返す。"""
	tzinfo = None
	if ZoneInfo is not None:
		try:
			tzinfo = ZoneInfo(timezone)
		except Exception:
			tzinfo = ZoneInfo("UTC")
	now = datetime.now(tzinfo)
	return now.isoformat()


TOOLS_SPEC = [
	{
		"type": "function",
		"function": {
			"name": "tool_get_time",
			"description": "指定したタイムゾーンの現在時刻を ISO8601 で返します。",
			"parameters": {
				"type": "object",
				"properties": {
					"timezone": {
						"type": "string",
						"description": "IANA タイムゾーン名 (例: Asia/Tokyo, UTC)",
					}
				},
				"required": ["timezone"],
				"additionalProperties": False,
			},
		},
	}
]


def _dispatch_tool(name: str, arguments: Dict[str, Any]) -> str:
	if name == "tool_get_time":
		return tool_get_time(**arguments)
	raise ValueError(f"未知のツールが指定されました: {name}")


def run_tools_demo(
	prompt: str,
	model: str = DEFAULT_MODEL,
	system: str = (
		"あなたはツールを上手く使う日本語アシスタントです。必要に応じて tool_get_time を呼び出してください。"
	),
	temperature: float = 0.2,
	max_tokens: int = 4096,
	dry_run: bool = False,
	include_temperature: bool = True,
) -> str:
	messages: List[Dict[str, Any]] = [
		{"role": "system", "content": system},
		{"role": "user", "content": prompt},
	]

	base_payload = {
		"model": model,
		"max_tokens": max_tokens,
		"tools": TOOLS_SPEC,
		"tool_choice": "auto",
	}
	if include_temperature and temperature is not None:
		base_payload["temperature"] = temperature

	if dry_run:
		print("[DRY-RUN] tools payload (first turn):")
		preview = {**base_payload, "messages": messages}
		print(json.dumps(preview, ensure_ascii=False, indent=2))
		return ""

	client = build_client()

	# ツールコールが無くなるまでループ
	for _ in range(4):  # 安全のため最大 4 ターン
		try:
			resp = client.chat.completions.create(messages=messages, **base_payload)
		except Exception as e:
			if "temperature" in base_payload and "temperature" in str(e).lower():
				# 一度だけ temperature を外して再送
				base_payload.pop("temperature", None)
				resp = client.chat.completions.create(messages=messages, **base_payload)
			else:
				raise
		choice = resp.choices[0]
		msg = choice.message

		# tool_calls が返る場合 (関数呼び出しの指示)
		tool_calls = getattr(msg, "tool_calls", None)
		if tool_calls:
			# アシスタントのツール呼び出しメッセージを履歴に追加
			assistant_msg = {
				"role": "assistant",
				"content": msg.content or "",
				"tool_calls": [
					{
						"id": tc.id,
						"type": "function",
						"function": {
							"name": tc.function.name,
							"arguments": tc.function.arguments,
						},
					}
					for tc in tool_calls
				],
			}
			messages.append(assistant_msg)

			# 各ツールをローカルで実行し、tool メッセージを追加
			for tc in tool_calls:
				try:
					args = json.loads(tc.function.arguments or "{}")
				except json.JSONDecodeError:
					args = {}
				result_text = _dispatch_tool(tc.function.name, args)
				messages.append(
					{
						"role": "tool",
						"tool_call_id": tc.id,
						"name": tc.function.name,
						"content": result_text,
					}
				)
			# 次のターンへ
			continue

		# ツール呼び出しが無ければ最終応答
		return (msg.content or "").strip()

	return "(ツールコールが連鎖し過ぎたため打ち切りました)"


# ---- CLI --------------------------------------------------------------


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="GPT-5 学習用サンプル")
	sub = parser.add_subparsers(dest="command", required=True)

	def add_common(p: argparse.ArgumentParser) -> None:
		p.add_argument("-p", "--prompt", required=True, help="ユーザープロンプト")
		p.add_argument("--system", default=None, help="system プロンプトを上書き")
		p.add_argument("--model", default=DEFAULT_MODEL, help="使用モデル (既定: gpt-5)")
		p.add_argument("--temperature", type=float, default=0.2)
		p.add_argument("--max-tokens", type=int, default=4096)
		p.add_argument("--dry-run", action="store_true", help="APIを呼ばずペイロードを表示")
		p.add_argument("--no-temperature", action="store_true", help="temperature を送らない (一部モデル向け)")

	p_chat = sub.add_parser("chat", help="基本のチャット応答")
	add_common(p_chat)

	p_json = sub.add_parser("json", help="JSON 形式での出力")
	add_common(p_json)
	p_json.set_defaults(temperature=0.0, max_tokens=2048)

	p_tools = sub.add_parser("tools", help="ツール呼び出しデモ")
	add_common(p_tools)

	return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
	args = parse_args(argv)

	# API キー確認 (dry-run なら不要)
	try:
		ensure_api_key_or_dry_run(args.dry_run)
	except Exception as e:
		print(f"エラー: {e}", file=sys.stderr)
		if not args.dry_run:
			return 2

	system = args.system

	if args.command == "chat":
		text = run_chat(
			prompt=args.prompt,
			model=args.model,
			system=system or "あなたは有能な日本語アシスタントです。",
			temperature=args.temperature,
			max_tokens=args.max_tokens,
			dry_run=args.dry_run,
			include_temperature=not getattr(args, "no_temperature", False),
		)
		if text:
			print(text)
		return 0

	if args.command == "json":
		data = run_json(
			prompt=args.prompt,
			model=args.model,
			system=system or "あなたは日本語で正確に JSON を生成します。",
			temperature=args.temperature,
			max_tokens=args.max_tokens,
			dry_run=args.dry_run,
			include_temperature=not getattr(args, "no_temperature", False),
		)
		if data:
			print(json.dumps(data, ensure_ascii=False, indent=2))
		return 0

	if args.command == "tools":
		text = run_tools_demo(
			prompt=args.prompt,
			model=args.model,
			system=system
			or "あなたはツールを上手く使う日本語アシスタントです。必要に応じて tool_get_time を呼び出してください。",
			temperature=args.temperature,
			max_tokens=args.max_tokens,
			dry_run=args.dry_run,
			include_temperature=not getattr(args, "no_temperature", False),
		)
		if text:
			print(text)
		return 0

	print("未対応のコマンドです", file=sys.stderr)
	return 2


if __name__ == "__main__":
	sys.exit(main())


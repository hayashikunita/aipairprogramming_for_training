#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
from typing import Optional

from common import client


def _validate_file(path: str) -> None:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"ファイルが見つかりません: {path}")


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Modalities: Video (Input only via audio track)")
    p.add_argument("--file", required=True, help="動画ファイルパス (mp4/mpeg/mov/webm など)")
    p.add_argument(
        "--task",
        choices=["transcribe", "translate", "summarize", "qa"],
        default="transcribe",
        help="transcribe=文字起こし, translate=英訳, summarize=要約 (文字起こし→Chat), qa=質問応答 (文字起こし→Chat)",
    )
    p.add_argument("--prompt", default=None, help="qa タスク時の質問プロンプト")
    p.add_argument("--model", default="whisper-1", help="音声モデル (動画の音声トラックを処理)")
    p.add_argument("--chat-model", default="gpt-5", help="summarize/qa に使うChatモデル")
    p.add_argument("--system", default="あなたは有能な日本語アシスタントです。")
    p.add_argument("--max-tokens", type=int, default=512)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--no-temperature", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    _validate_file(args.file)

    if args.dry_run:
        preview = {
            "video": {"file": os.path.basename(args.file)},
            "task": args.task,
            "audio_model": args.model,
        }
        if args.task in {"summarize", "qa"}:
            chat_preview = {
                "model": args.chat_model,
                "messages": [
                    {"role": "system", "content": args.system},
                    {
                        "role": "user",
                        "content": (
                            "<transcript from video will be inserted here>\n\n"
                            + (args.prompt or "(no prompt)")
                            if args.task == "qa"
                            else "次の動画の文字起こしを日本語で簡潔に要約してください: <transcript here>"
                        ),
                    },
                ],
                "max_tokens": args.max_tokens,
                **({"temperature": args.temperature} if not args.no_temperature else {}),
            }
            preview["chat"] = chat_preview

        from common import pretty

        print("[DRY-RUN] video->audio flow preview:")
        print(pretty(preview))
        return 0

    c = client()

    # Whisper/Transcribe API は動画の音声トラックも受け付けます
    with open(args.file, "rb") as f:
        if args.task == "translate":
            aresp = c.audio.translations.create(model=args.model, file=f)
        else:
            aresp = c.audio.transcriptions.create(model=args.model, file=f)

    transcript = getattr(aresp, "text", None) or getattr(aresp, "text", None) or str(aresp)

    if args.task in {"summarize", "qa"}:
        messages = [{"role": "system", "content": args.system}]
        if args.task == "summarize":
            user_content = f"次の動画の文字起こしを日本語で簡潔に要約してください:\n\n{transcript}"
        else:
            user_content = (
                (args.prompt or "この動画内容に関して有用な要点を挙げてください。")
                + "\n\n[文字起こし]\n" + transcript
            )

        messages.append({"role": "user", "content": user_content})

        payload = {
            "model": args.chat_model,
            "messages": messages,
            "max_tokens": args.max_tokens,
        }
        if not args.no_temperature:
            payload["temperature"] = args.temperature

        try:
            resp = c.chat.completions.create(**payload)
        except Exception as e:
            if "temperature" in payload and "temperature" in str(e).lower():
                payload.pop("temperature", None)
                resp = c.chat.completions.create(**payload)
            else:
                raise
        print((resp.choices[0].message.content or "").strip())
    else:
        print((transcript or "").strip())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import time
from typing import Optional

from common import client


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Tools: Assistants Code Interpreter (minimal)")
    p.add_argument("prompt", help="実行してほしい処理内容（自然言語でOK）")
    p.add_argument("--assistant-model", default="gpt-5")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    if args.dry_run:
        print(f"[DRY-RUN] assistants.create with code_interpreter; run with prompt='{args.prompt}'")
        return 0

    c = client()

    # 1) Assistant を作成（code_interpreter 有効化）
    assistant = c.beta.assistants.create(
        model=args.assistant_model,
        tools=[{"type": "code_interpreter"}],
        instructions="あなたは有能なデータ・コードアシスタントです。安全に配慮して実行してください。",
    )

    # 2) Thread を作成
    thread = c.beta.threads.create()

    # 3) ユーザーメッセージを投入
    c.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=args.prompt,
    )

    # 4) Run を開始（Assistantに処理させる）
    run = c.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

    # 5) ポーリングで完了待ち
    while True:
        run = c.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run.status in ("completed", "failed", "cancelled", "expired"):
            break
        time.sleep(1.0)

    if run.status != "completed":
        print(f"Run finished with status={run.status}")
        return 1

    # 6) 最終メッセージを取得
    messages = c.beta.threads.messages.list(thread_id=thread.id, order="desc", limit=10)
    for m in messages.data:
        if m.role == "assistant":
            # 現行APIでは content 内要素に text や image 等が混在する可能性がある
            parts = []
            for cpart in m.content:
                if getattr(cpart, "type", None) == "text":
                    parts.append(cpart.text.value)
            if parts:
                print("\n".join(parts))
            break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

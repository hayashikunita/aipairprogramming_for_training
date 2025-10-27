#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
import json
from typing import Optional
from common import client

"""
Distillation（知識蒸留）の最小例: Teacher モデルで合成データを作り JSONL に保存

- 入力: プロンプト一覧のテキストファイル（1行=1プロンプト）
- 出力: Chat Fine-tuning 用 JSONL（{"messages": [...]} 形式）
- 使い方:
    python distillation.py --prompts prompts.txt --teacher-model gpt-5 --output dataset.jsonl

注: これは学習用サンプルです。実用ではプロンプト設計、品質チェック、バイアス対応が必要です。
"""


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Distillation: Teacher で合成データ作成 → JSONL")
    p.add_argument("--prompts", required=True, help="1行ごとにプロンプトを記したテキストファイル")
    p.add_argument("--teacher-model", default="gpt-5")
    p.add_argument("--system", default="あなたは丁寧で簡潔に回答するアシスタントです。")
    p.add_argument("--max-tokens", type=int, default=512)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--no-temperature", action="store_true")
    p.add_argument("--output", default="dataset.jsonl")
    args = p.parse_args(argv)

    c = client()

    with open(args.prompts, "r", encoding="utf-8") as f:
        prompts = [line.strip() for line in f if line.strip()]

    with open(args.output, "w", encoding="utf-8") as out:
        for pr in prompts:
            payload = {
                "model": args.teacher_model,
                "messages": [
                    {"role": "system", "content": args.system},
                    {"role": "user", "content": pr},
                ],
                "max_tokens": args.max_tokens,
            }
            if not args.no_temperature:
                payload["temperature"] = args.temperature

            resp = c.chat.completions.create(**payload)
            answer = (resp.choices[0].message.content or "").strip()

            example = {
                "messages": [
                    {"role": "system", "content": args.system},
                    {"role": "user", "content": pr},
                    {"role": "assistant", "content": answer},
                ]
            }
            out.write(json.dumps(example, ensure_ascii=False) + "\n")

    print(f"saved JSONL: {args.output}")
    print("次のステップ: files API でアップロード → fine_tuning.jobs.create で微調整へ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

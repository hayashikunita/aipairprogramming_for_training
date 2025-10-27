#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenAI API 全エンドポイント 学習用オールインワン CLI

サブコマンド:
- models: モデル一覧
- chat: チャット生成
- completions: 旧/レガシー Completions（非推奨）
- edits: 旧/レガシー Edits（非推奨）
- embeddings: 埋め込み
- images: 画像生成
- transcribe: 音声→テキスト
- translate: 音声→英訳
- moderations: モデレーション
- files: ファイル upload/list/delete
- finetune: 微調整 create/list
- usage: 利用量（参考・非公式）

共通:
- --dry-run でリクエスト内容のみ表示（APIは呼ばない）
- --no-temperature で temperature を送らない

注意:
- 実運用では SDK/モデルの最新ドキュメントを参照してください。
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import sys
from typing import Any, Dict, List, Optional

DEFAULTS = {
    "CHAT_MODEL": os.getenv("OPENAI_CHAT_MODEL", os.getenv("OPENAI_GPT5_MODEL", "gpt-5")),
    "EMBED_MODEL": os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-large"),
    "IMAGE_MODEL": os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1"),
    "MODERATION_MODEL": os.getenv("OPENAI_MODERATION_MODEL", "omni-moderation-latest"),
    "ASR_MODEL": os.getenv("OPENAI_ASR_MODEL", "whisper-1"),
    "COMPLETIONS_MODEL": os.getenv("OPENAI_COMPLETIONS_MODEL", "gpt-3.5-turbo-instruct"),
    "EDITS_MODEL": os.getenv("OPENAI_EDITS_MODEL", "text-davinci-edit-001"),
}


def _lazy_openai_client():
    try:
        from openai import OpenAI  # type: ignore
        return OpenAI()
    except Exception as e:
        raise RuntimeError("OpenAI SDK が見つかりません。`pip install openai` を実行してください。") from e


def _need_key_or_dry_run(dry_run: bool) -> None:
    if dry_run:
        return
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY が未設定です。PowerShell では\n"
            "  $env:OPENAI_API_KEY = \"sk-...\"\n"
            "  setx OPENAI_API_KEY \"sk-...\"  # 永続\n"
        )


# ---------------- models ----------------

def cmd_models(args: argparse.Namespace) -> int:
    _need_key_or_dry_run(args.dry_run)
    payload = {}
    if args.dry_run:
        print("[DRY-RUN] models.list payload:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    client = _lazy_openai_client()
    models = client.models.list()
    for m in models.data:
        print(m.id)
    return 0


# ---------------- chat ----------------

def cmd_chat(args: argparse.Namespace) -> int:
    _need_key_or_dry_run(args.dry_run)
    messages = [
        {"role": "system", "content": args.system or "あなたは有能な日本語アシスタントです。"},
        {"role": "user", "content": args.prompt},
    ]
    payload: Dict[str, Any] = {
        "model": args.model or DEFAULTS["CHAT_MODEL"],
        "messages": messages,
        "max_tokens": args.max_tokens,
    }
    if not args.no_temperature and args.temperature is not None:
        payload["temperature"] = args.temperature

    if args.dry_run:
        print("[DRY-RUN] chat.completions.create payload:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    client = _lazy_openai_client()
    try:
        resp = client.chat.completions.create(**payload)
    except Exception as e:
        if "temperature" in payload and "temperature" in str(e).lower():
            payload.pop("temperature", None)
            resp = client.chat.completions.create(**payload)
        else:
            raise
    print((resp.choices[0].message.content or "").strip())
    return 0


# ---------------- completions (legacy) ----------------

def cmd_completions(args: argparse.Namespace) -> int:
    _need_key_or_dry_run(args.dry_run)
    payload: Dict[str, Any] = {
        "model": args.model or DEFAULTS["COMPLETIONS_MODEL"],
        "prompt": args.prompt,
        "max_tokens": args.max_tokens,
    }
    if not args.no_temperature and args.temperature is not None:
        payload["temperature"] = args.temperature
    if args.dry_run:
        print("[DRY-RUN] completions.create payload:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    client = _lazy_openai_client()
    # v1 SDK では client.completions.create が用意されています（レガシー）
    resp = client.completions.create(**payload)  # type: ignore[attr-defined]
    text = resp.choices[0].text or ""
    print(text.strip())
    return 0


# ---------------- edits (legacy) ----------------

def cmd_edits(args: argparse.Namespace) -> int:
    _need_key_or_dry_run(args.dry_run)
    payload = {
        "model": args.model or DEFAULTS["EDITS_MODEL"],
        "input": args.input,
        "instruction": args.instruction,
    }
    if args.dry_run:
        print("[DRY-RUN] edits.create payload:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    client = _lazy_openai_client()
    # v1 SDK では client.edits.create が用意されています（レガシー）
    resp = client.edits.create(**payload)  # type: ignore[attr-defined]
    print((resp.choices[0].text or "").strip())
    return 0


# ---------------- embeddings ----------------

def cmd_embeddings(args: argparse.Namespace) -> int:
    _need_key_or_dry_run(args.dry_run)
    payload = {
        "model": args.model or DEFAULTS["EMBED_MODEL"],
        "input": args.text,
    }
    if args.dry_run:
        print("[DRY-RUN] embeddings.create payload:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    client = _lazy_openai_client()
    resp = client.embeddings.create(**payload)
    vec = resp.data[0].embedding
    print(len(vec), vec[:8])
    return 0


# ---------------- images ----------------

def cmd_images(args: argparse.Namespace) -> int:
    _need_key_or_dry_run(args.dry_run)
    payload: Dict[str, Any] = {
        "model": args.model or DEFAULTS["IMAGE_MODEL"],
        "prompt": args.prompt,
        "size": args.size,
        "quality": args.quality,
        "n": args.n,
    }
    if args.dry_run:
        print("[DRY-RUN] images.generate payload:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    client = _lazy_openai_client()
    resp = client.images.generate(**payload)
    # 最初の画像を保存
    b64 = resp.data[0].b64_json
    if not b64:
        print("画像が返りませんでした", file=sys.stderr)
        return 2
    data = base64.b64decode(b64)
    out = args.output or "image_1.png"
    with open(out, "wb") as f:
        f.write(data)
    print(f"saved: {out}")
    return 0


# ---------------- audio: transcribe ----------------

def cmd_transcribe(args: argparse.Namespace) -> int:
    _need_key_or_dry_run(args.dry_run)
    payload = {
        "model": args.model or DEFAULTS["ASR_MODEL"],
    }
    if args.dry_run:
        print("[DRY-RUN] audio.transcriptions.create payload:")
        preview = dict(payload)
        preview["file"] = f"<binary:{args.file}>"
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return 0
    client = _lazy_openai_client()
    with open(args.file, "rb") as f:
        resp = client.audio.transcriptions.create(**payload, file=f)
    print(resp.text)
    return 0


# ---------------- audio: translate ----------------

def cmd_translate(args: argparse.Namespace) -> int:
    _need_key_or_dry_run(args.dry_run)
    payload = {
        "model": args.model or DEFAULTS["ASR_MODEL"],
    }
    if args.dry_run:
        print("[DRY-RUN] audio.translations.create payload:")
        preview = dict(payload)
        preview["file"] = f"<binary:{args.file}>"
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return 0
    client = _lazy_openai_client()
    with open(args.file, "rb") as f:
        resp = client.audio.translations.create(**payload, file=f)
    print(resp.text)
    return 0


# ---------------- moderations ----------------

def cmd_moderations(args: argparse.Namespace) -> int:
    _need_key_or_dry_run(args.dry_run)
    payload = {
        "model": args.model or DEFAULTS["MODERATION_MODEL"],
        "input": args.text,
    }
    if args.dry_run:
        print("[DRY-RUN] moderations.create payload:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    client = _lazy_openai_client()
    resp = client.moderations.create(**payload)
    print(json.dumps(resp.model_dump(), ensure_ascii=False, indent=2))
    return 0


# ---------------- files ----------------

def cmd_files(args: argparse.Namespace) -> int:
    _need_key_or_dry_run(args.dry_run)
    client = None if args.dry_run else _lazy_openai_client()

    if args.action == "upload":
        payload = {"purpose": args.purpose}
        if args.dry_run:
            preview = dict(payload)
            preview["file"] = f"<binary:{args.file}>"
            print("[DRY-RUN] files.create payload:")
            print(json.dumps(preview, ensure_ascii=False, indent=2))
            return 0
        with open(args.file, "rb") as f:
            resp = client.files.create(file=f, purpose=args.purpose)
        print(resp.id)
        return 0

    if args.action == "list":
        if args.dry_run:
            print("[DRY-RUN] files.list payload: {}")
            return 0
        files = client.files.list()
        for f in files.data:
            print(f.id, f.filename)
        return 0

    if args.action == "delete":
        if args.dry_run:
            print(f"[DRY-RUN] files.delete file_id={args.file_id}")
            return 0
        resp = client.files.delete(args.file_id)
        print(resp.deleted)
        return 0

    print("未知の files action", file=sys.stderr)
    return 2


# ---------------- fine-tuning ----------------

def cmd_finetune(args: argparse.Namespace) -> int:
    _need_key_or_dry_run(args.dry_run)
    client = None if args.dry_run else _lazy_openai_client()

    if args.action == "create":
        payload = {
            "training_file": args.training_file,
            "model": args.model,
        }
        if args.dry_run:
            print("[DRY-RUN] fine_tuning.jobs.create payload:")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        resp = client.fine_tuning.jobs.create(**payload)
        print(json.dumps(resp.model_dump(), ensure_ascii=False, indent=2))
        return 0

    if args.action == "list":
        if args.dry_run:
            print("[DRY-RUN] fine_tuning.jobs.list payload: {}")
            return 0
        jobs = client.fine_tuning.jobs.list()
        for j in jobs.data:
            print(j.id, j.status, j.model)
        return 0

    print("未知の finetune action", file=sys.stderr)
    return 2


# ---------------- usage (reference) ----------------

def cmd_usage(args: argparse.Namespace) -> int:
    _need_key_or_dry_run(args.dry_run)
    start = args.start or dt.date.today().replace(day=1).isoformat()
    end = args.end or dt.date.today().isoformat()
    url = f"https://api.openai.com/v1/usage?start_date={start}&end_date={end}"
    if args.dry_run:
        print("[DRY-RUN] GET /v1/usage")
        print(json.dumps({"url": url, "headers": {"Authorization": "Bearer <API_KEY>"}}, ensure_ascii=False, indent=2))
        return 0
    # 参考実装（ベータ/非公式のため将来変更の可能性あり）
    try:
        import requests  # type: ignore
    except Exception as e:
        print("requests が必要です。`pip install requests`", file=sys.stderr)
        return 2
    headers = {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}", "Content-Type": "application/json"}
    r = requests.get(url, headers=headers, timeout=60)
    print(r.status_code)
    try:
        print(json.dumps(r.json(), ensure_ascii=False, indent=2))
    except Exception:
        print(r.text)
    return 0


# ---------------- CLI ----------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="OpenAI API 全エンドポイント CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(pp: argparse.ArgumentParser) -> None:
        pp.add_argument("--dry-run", action="store_true")
        pp.add_argument("--no-temperature", action="store_true")
        pp.add_argument("--temperature", type=float, default=0.2)
        pp.add_argument("--max-tokens", type=int, default=1024)

    # models
    pm = sub.add_parser("models", help="モデル一覧")
    pm.set_defaults(func=cmd_models)
    pm.add_argument("--dry-run", action="store_true")

    # chat
    pc = sub.add_parser("chat", help="チャット生成")
    pc.set_defaults(func=cmd_chat)
    add_common(pc)
    pc.add_argument("-p", "--prompt", required=True)
    pc.add_argument("--system", default=None)
    pc.add_argument("--model", default=DEFAULTS["CHAT_MODEL"])

    # completions (legacy)
    pcl = sub.add_parser("completions", help="テキスト完結（レガシー）")
    pcl.set_defaults(func=cmd_completions)
    add_common(pcl)
    pcl.add_argument("-p", "--prompt", required=True)
    pcl.add_argument("--model", default=DEFAULTS["COMPLETIONS_MODEL"])

    # edits (legacy)
    pe = sub.add_parser("edits", help="テキスト編集（レガシー）")
    pe.set_defaults(func=cmd_edits)
    pe.add_argument("--dry-run", action="store_true")
    pe.add_argument("--model", default=DEFAULTS["EDITS_MODEL"])
    pe.add_argument("--input", required=True)
    pe.add_argument("--instruction", required=True)

    # embeddings
    pem = sub.add_parser("embeddings", help="埋め込み")
    pem.set_defaults(func=cmd_embeddings)
    pem.add_argument("--dry-run", action="store_true")
    pem.add_argument("--model", default=DEFAULTS["EMBED_MODEL"])
    pem.add_argument("--text", required=True)

    # images
    pi = sub.add_parser("images", help="画像生成")
    pi.set_defaults(func=cmd_images)
    pi.add_argument("--dry-run", action="store_true")
    pi.add_argument("--model", default=DEFAULTS["IMAGE_MODEL"])
    pi.add_argument("--prompt", required=True)
    pi.add_argument("--size", default="1024x1024")
    pi.add_argument("--quality", default="standard")
    pi.add_argument("--n", type=int, default=1)
    pi.add_argument("--output", default=None)

    # transcribe
    pt = sub.add_parser("transcribe", help="音声文字起こし")
    pt.set_defaults(func=cmd_transcribe)
    pt.add_argument("--dry-run", action="store_true")
    pt.add_argument("--model", default=DEFAULTS["ASR_MODEL"])
    pt.add_argument("--file", required=True)

    # translate
    ptt = sub.add_parser("translate", help="音声翻訳 → 英語")
    ptt.set_defaults(func=cmd_translate)
    ptt.add_argument("--dry-run", action="store_true")
    ptt.add_argument("--model", default=DEFAULTS["ASR_MODEL"])
    ptt.add_argument("--file", required=True)

    # moderations
    pmod = sub.add_parser("moderations", help="モデレーション")
    pmod.set_defaults(func=cmd_moderations)
    pmod.add_argument("--dry-run", action="store_true")
    pmod.add_argument("--model", default=DEFAULTS["MODERATION_MODEL"])
    pmod.add_argument("--text", required=True)

    # files
    pf = sub.add_parser("files", help="ファイル操作")
    pf.set_defaults(func=cmd_files)
    pf.add_argument("--dry-run", action="store_true")
    pf.add_argument("action", choices=["upload", "list", "delete"])  # positional は自動的に必須
    pf.add_argument("--file", help="アップロード時のファイルパス")
    pf.add_argument("--purpose", default="fine-tune")
    pf.add_argument("--file-id", dest="file_id", default=None)

    # fine-tuning
    pft = sub.add_parser("finetune", help="微調整")
    pft.set_defaults(func=cmd_finetune)
    pft.add_argument("--dry-run", action="store_true")
    pft.add_argument("action", choices=["create", "list"])  # positional は自動的に必須
    pft.add_argument("--training-file", default=None)
    pft.add_argument("--model", default=DEFAULTS["CHAT_MODEL"], help="対応モデルに置き換えてください")

    # usage
    pu = sub.add_parser("usage", help="利用量 (参考)")
    pu.set_defaults(func=cmd_usage)
    pu.add_argument("--dry-run", action="store_true")
    pu.add_argument("--start", default=None)
    pu.add_argument("--end", default=None)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    func = getattr(args, "func", None)
    if not func:
        parser.print_help()
        return 2
    try:
        return func(args)
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

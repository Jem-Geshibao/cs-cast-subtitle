# -*- coding: utf-8 -*-
"""阶段二：分段转写主流程（严禁整段 transcribe）。

用法：
    python transcribe.py <音频路径> --lang en --out seg.json
    python transcribe.py <音频路径> --lang zh --chunk 45 --overlap 5 --model medium
    python transcribe.py <音频路径> --lang en --no-prompt        # 干净复转，避免中文 prompt 污染人名
    python transcribe.py <音频路径> --prompt "Spirit vs MOUZ ..."  # 锁定比赛后的定制提示词
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asr_util as U  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--lang", default="auto", choices=["auto", "en", "zh"])
    ap.add_argument("--model", default="medium")
    ap.add_argument("--chunk", type=float, default=45.0)
    ap.add_argument("--overlap", type=float, default=5.0)
    ap.add_argument("--beam", type=int, default=8)
    ap.add_argument("--prompt", default=None)
    ap.add_argument("--no-prompt", action="store_true")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    audio = U.load_audio(args.audio)
    total = len(audio) / U.SR
    print(f"duration {total:.2f}s", flush=True)

    lang = args.lang
    if lang == "auto":
        small = U.load_model("small")
        lang, prob = U.detect_language(small, audio)
        print(f"detected language: {lang} (p={prob:.2f})", flush=True)
        del small

    prompt = U.pick_prompt(lang, args.no_prompt, args.prompt)
    model = U.load_model(args.model)
    results = U.transcribe_chunked(model, audio, total, lang, prompt,
                                   args.chunk, args.overlap, args.beam)
    U.save_json(args.out, results)
    print(f"Done: {len(results)} segments, lang={lang}")


if __name__ == "__main__":
    main()

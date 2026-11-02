# -*- coding: utf-8 -*-
"""阶段三/四：指定区间补录与攻坚重转。

用法：
    python recheck.py <音频路径> --ranges "23-27,26-33" --lang en --out recheck.json
    python recheck.py <音频路径> --ranges "104-241" --lang en --no-prompt   # 英文段无预设复转
    python recheck.py <音频路径> --ranges "8.5-10.5" --prompt "Spirit vs MOUZ, donk, zont1x ..."
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
    ap.add_argument("--ranges", required=True, help='秒级区间，如 "23-27,26-33"')
    ap.add_argument("--lang", default="en", choices=["en", "zh"])
    ap.add_argument("--model", default="medium")
    ap.add_argument("--beam", type=int, default=10)
    ap.add_argument("--prompt", default=None)
    ap.add_argument("--no-prompt", action="store_true")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    audio = U.load_audio(args.audio)
    ranges = U.parse_ranges(args.ranges)
    prompt = U.pick_prompt(args.lang, args.no_prompt, args.prompt)
    model = U.load_model(args.model)

    out = U.transcribe_ranges(model, audio, ranges, args.lang, prompt, args.beam)
    U.save_json(args.out, out)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""阶段一：探测音频 —— 时长、语言、RMS 能量分布、有声/静音区间。

用法：
    python probe_audio.py <音频路径> [--step 4] [--json probe.json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asr_util as U  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--step", type=float, default=4.0)
    ap.add_argument("--json", default=None, help="可选：把探测结果落盘")
    args = ap.parse_args()

    audio = U.load_audio(args.audio)
    total = len(audio) / U.SR
    print(f"file   : {args.audio}")
    print(f"duration: {total:.2f}s\n")

    small = U.load_model("small")
    lang, prob = U.detect_language(small, audio)
    print(f"language: {lang} (p={prob:.2f})\n")

    print("RMS 能量扫描（# 越密越响）：")
    U.print_rms(audio, args.step)

    ivs = U.voiced_intervals(audio, args.step)
    print("\n有声区间：")
    for a, b in ivs:
        print(f"  {a:7.1f} - {b:7.1f}s")
    silent = []
    prev = 0.0
    for a, b in ivs:
        if a - prev > 1.0:
            silent.append((prev, a))
        prev = b
    if total - prev > 1.0:
        silent.append((prev, round(total, 1)))
    print("\n静音区间（>1s）：")
    for a, b in silent:
        print(f"  {a:7.1f} - {b:7.1f}s")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"duration": round(total, 2), "language": lang,
                       "language_probability": prob,
                       "voiced": ivs, "silent": silent}, f, ensure_ascii=False, indent=2)
        print(f"\nsaved -> {args.json}")


if __name__ == "__main__":
    main()

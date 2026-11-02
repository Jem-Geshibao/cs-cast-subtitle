# -*- coding: utf-8 -*-
"""阶段三辅助：把已有转写结果与 RMS 有声区间对比，自动列出「有声音却没转出内容」的可疑漏段。

用法：
    python gaps.py <音频路径> <segments.json> [--tolerance 1.5] [--min-gap 2.0]
    python gaps.py <音频路径> recheck.json        # 也支持 recheck.py 产出的 {区间: [段]} 结构
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asr_util as U  # noqa: E402


def _iter_segments(obj):
    if isinstance(obj, list):
        for e in obj:
            yield float(e["start"]), float(e["end"])
    elif isinstance(obj, dict):
        for v in obj.values():
            if isinstance(v, list):
                for e in v:
                    yield float(e["start"]), float(e["end"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("segments")
    ap.add_argument("--tolerance", type=float, default=1.5,
                    help="转写段之间允许的空隙（小于此值视为连续）")
    ap.add_argument("--min-gap", type=float, default=2.0,
                    help="只报告长度超过该值的漏段")
    args = ap.parse_args()

    audio = U.load_audio(args.audio)
    total = len(audio) / U.SR
    seg = json.load(open(args.segments, encoding="utf-8"))

    spans = sorted(_iter_segments(seg))
    covered = []
    for s, e in spans:
        if covered and s - covered[-1][1] < args.tolerance:
            covered[-1][1] = max(covered[-1][1], e)
        else:
            covered.append([s, e])

    voiced = U.voiced_intervals(audio)
    holes = []
    for vs, ve in voiced:
        t = vs
        for cs, ce in covered:
            if ce <= t:
                continue
            if cs > t:
                holes.append((t, min(cs, ve)))
            t = max(t, ce)
            if t >= ve:
                break
        if t < ve:
            holes.append((t, ve))

    holes = [(a, b) for a, b in holes if b - a >= args.min_gap and b <= total + 0.5]
    print(f"音频总长 {total:.1f}s，已覆盖 {len(covered)} 段，有声区间 {len(voiced)} 段")
    if not holes:
        print("未发现明显漏段。")
        return
    print("可疑漏段（建议用 recheck.py 单独补录）：")
    for a, b in holes:
        print(f"  {a:7.1f} - {b:7.1f}s  ({b - a:.1f}s)")
    print("\n可直接复制：")
    print(",".join(f"{a:.1f}-{b:.1f}" for a, b in holes))


if __name__ == "__main__":
    main()

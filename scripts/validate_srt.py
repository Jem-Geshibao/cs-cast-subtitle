# -*- coding: utf-8 -*-
"""SRT 发布前校验：序号连续、时间轴单调不重叠、行宽达标、无空块。

排版模式（scripts/layouts.py）——两种模式共用同一硬约束：
  **源语言 1 行 + 中文 1 行，任何一行不许折行，不可超出字幕安全区**。
  * landscape（抖音横屏，默认）：加权行宽 ≤48；
  * portrait（抖音竖屏）：加权行宽 ≤46。

用法：
    python validate_srt.py <file.srt>                        # 默认横屏
    python validate_srt.py <file.srt> --layout portrait      # 竖屏
    python validate_srt.py <file.srt> --limit 40 --max-lines 3
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layouts as L  # noqa: E402


def ts(s: str) -> float:
    h, m, rest = s.split(":")
    sec, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000


def width(s: str) -> float:
    w = 0.0
    for c in s:
        o = ord(c)
        w += 1.9 if (o > 0x2E80 or 0xFF00 <= o <= 0xFFEF) else 1.0
    return w


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("srt")
    ap.add_argument("--layout", default=L.DEFAULT, choices=sorted(L.LAYOUTS),
                    help="排版模式：landscape=抖音横屏（行宽 ≤48），portrait=抖音竖屏（行宽 ≤46），均单行不折行")
    ap.add_argument("--limit", type=float, default=None,
                    help="加权行宽上限（默认取所选模式）")
    ap.add_argument("--max-lines", type=int, default=None,
                    help="单块最大行数（默认取所选模式）")
    args = ap.parse_args()

    prof = L.resolve(args.limit, args.max_lines, args.layout)
    print(f"排版模式：{prof['label']}（{prof['note']}）")

    text = open(args.srt, encoding="utf-8-sig").read()
    blocks = [b for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]
    errs, prev_end = [], -1.0
    for i, b in enumerate(blocks, 1):
        lines = b.strip().splitlines()
        if len(lines) < 3:
            errs.append(f"[{i}] 块内容不足（序号/时间轴/文本）")
            continue
        idx = lines[0].strip()
        if idx != str(i):
            errs.append(f"[{i}] 序号不连续: {idx}")
        m = re.match(r"(\d\d:\d\d:\d\d,\d\d\d)\s*-->\s*(\d\d:\d\d:\d\d,\d\d\d)", lines[1])
        if not m:
            errs.append(f"[{i}] 时间轴格式错误: {lines[1]}")
            continue
        st, en = ts(m.group(1)), ts(m.group(2))
        if en <= st:
            errs.append(f"[{i}] 结束 <= 开始")
        if st < prev_end - 0.001:
            errs.append(f"[{i}] 与上一条重叠（上一条结束 {prev_end:.2f}s）")
        prev_end = en
        body = lines[2:]
        cap = L.max_lines_for(body, prof)
        if len(body) > cap:
            errs.append(f"[{i}] 行数 {len(body)} 超过上限 {cap}"
                        + ("（双语只许 2 行、纯中文 1 行）" if prof["bilingual_only"]
                           else f"（单块最多 {cap} 行）"))
        for ln in body:
            if width(ln) > prof["limit"]:
                errs.append(f"[{i}] 行超宽 ≈{width(ln):.0f}/{prof['limit']:.0f}: {ln[:30]}...")

    print(f"共 {len(blocks)} 条字幕，时长覆盖至 {prev_end:.2f}s")
    if errs:
        print("发现问题：")
        for e in errs:
            print("  " + e)
        sys.exit(1)
    print("校验通过：序号连续、时间轴单调无重叠、行宽与行数达标。")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None
    main()

# -*- coding: utf-8 -*-
"""SRT 发布前校验：序号连续、时间轴单调不重叠、行宽达标、无空块。

用法：
    python validate_srt.py <file.srt> [--limit 46] [--max-lines 4]
"""
from __future__ import annotations

import argparse
import re
import sys


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
    ap.add_argument("--limit", type=float, default=46.0)
    ap.add_argument("--max-lines", type=int, default=5,
                    help="单块最大行数（已交付稿出现过 源3行+中2行，默认 5）")
    args = ap.parse_args()

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
        if len(body) > args.max_lines:
            errs.append(f"[{i}] 行数 {len(body)} 超过竖屏安全值 {args.max_lines}")
        for ln in body:
            if width(ln) > args.limit:
                errs.append(f"[{i}] 行超宽 ≈{width(ln):.0f}/{args.limit:.0f}: {ln[:30]}...")

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

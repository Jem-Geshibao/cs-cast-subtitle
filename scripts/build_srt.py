# -*- coding: utf-8 -*-
"""把人工校对+翻译好的对照数据渲染成 SRT，并顺带做行宽体检。

pairs.json 格式（时间轴必须来自 ASR 原值，严禁手改）：
[
  {"start": 0.0,  "end": 3.06, "src": "do anything too drastic with the knife,\\nbut it'll guarantee the kill.",
   "zh": "用刀不必太激进，\\n但这刀稳拿击杀"},
  {"start": 25.62,"end": 29.78,"src": null, "zh": "这波换人很果断"}   // src 为空 => 纯中文段
]

用法：
    python build_srt.py pairs.json out.srt [--limit 46] [--no-lower]
"""
from __future__ import annotations

import argparse
import json
import sys


def width(s: str) -> float:
    """抖音竖屏 6 号字宽度估算：CJK/全角按 1.9，其余按 1。"""
    w = 0.0
    for c in s:
        o = ord(c)
        w += 1.9 if (o > 0x2E80 or 0xFF00 <= o <= 0xFFEF) else 1.0
    return w


def fmt(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600 * 1000)
    m, ms = divmod(ms, 60 * 1000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pairs")
    ap.add_argument("out")
    ap.add_argument("--limit", type=float, default=46.0)
    ap.add_argument("--no-lower", action="store_true", help="不把源语言强制小写")
    args = ap.parse_args()

    pairs = json.load(open(args.pairs, encoding="utf-8"))
    blocks, warns = [], []
    for i, p in enumerate(pairs, 1):
        st, en = float(p["start"]), float(p["end"])
        if en <= st:
            warns.append(f"[{i}] end<=start")
        src = (p.get("src") or "").strip()
        if src and not args.no_lower:
            src = src.lower()
        zh = (p.get("zh") or "").strip()
        lines = [ln for ln in src.split("\n") if ln.strip()]
        lines += [ln for ln in zh.split("\n") if ln.strip()]
        if not lines:
            warns.append(f"[{i}] 空字幕块")
        for ln in lines:
            if width(ln) > args.limit:
                warns.append(f"[{i}] 行超宽 ≈{width(ln):.0f}/{args.limit:.0f}: {ln}")
        if len(lines) > 5:
            warns.append(f"[{i}] 行数过多（{len(lines)} 行），竖屏会遮挡画面")
        blocks.append(f"{i}\n{fmt(st)} --> {fmt(en)}\n" + "\n".join(lines))

    text = "\n\n".join(blocks) + "\n"
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"已生成 {args.out} —— {len(blocks)} 条字幕")
    if warns:
        print("体检提示：")
        for w in warns:
            print("  " + w)
    else:
        print("体检通过：时间轴合法、行宽与行数均在安全范围。")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None
    main()

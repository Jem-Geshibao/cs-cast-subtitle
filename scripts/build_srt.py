# -*- coding: utf-8 -*-
"""把人工校对+翻译好的对照数据渲染成 SRT，并顺带做行宽体检。

排版模式（scripts/layouts.py）：
  * landscape（抖音横屏，默认）：源语言 1 行 + 中文 1 行，不许折行；
    加权行宽 ≤48（中文 ≈25 字 / 英文 ≈48 字符）；纯中文段只许 1 行。
    输入里写了 "\\n" 也会被合并为单行（--keep-breaks 可关闭）。
  * portrait（抖音竖屏）：允许折行，单块 ≤5 行（源 ≤3 + 中 ≤2），
    加权行宽 ≤46（中文 ≈19 字 / 英文 ≈46 字符）。

pairs.json 格式（时间轴必须来自 ASR 原值，严禁手改）：
[
  {"start": 0.0,  "end": 3.06, "src": "not too drastic with the knife, but it's a kill",
   "zh": "用刀不必太激进，这刀稳拿击杀"},
  {"start": 25.62,"end": 29.78,"src": null, "zh": "这波换人很果断"}   // src 为空 => 纯中文段
]

用法：
    python build_srt.py pairs.json out.srt                          # 默认横屏
    python build_srt.py pairs.json out.srt --layout portrait        # 竖屏
    python build_srt.py pairs.json out.srt --limit 40 --max-lines 3 # 覆盖模式默认
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layouts as L  # noqa: E402


def width(s: str) -> float:
    """行宽估算：CJK/全角按 1.9，其余按 1。"""
    w = 0.0
    for c in s:
        o = ord(c)
        w += 1.9 if (o > 0x2E80 or 0xFF00 <= o <= 0xFFEF) else 1.0
    return w


def merge_to_one_line(text: str) -> tuple[str, int]:
    """把软换行合并为一行：英文用空格连接，中文直接连接。返回 (文本, 原行数)。"""
    parts = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if not parts:
        return "", 0
    out = parts[0]
    for nxt in parts[1:]:
        sep = " " if out[-1].isascii() and nxt[0].isascii() else ""
        out += sep + nxt
    return out, len(parts)


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
    ap.add_argument("--layout", default=L.DEFAULT, choices=sorted(L.LAYOUTS),
                    help="排版模式：landscape=抖音横屏（单行），portrait=抖音竖屏（多行）")
    ap.add_argument("--limit", type=float, default=None, help="加权行宽上限（默认取所选模式）")
    ap.add_argument("--max-lines", type=int, default=None, help="单块最大行数（默认取所选模式）")
    ap.add_argument("--no-lower", action="store_true", help="不把源语言强制小写")
    ap.add_argument("--single-line", action="store_true", help="强制单行（覆盖竖屏模式的多行）")
    ap.add_argument("--keep-breaks", action="store_true", help="保留输入换行（覆盖横屏模式的合并）")
    args = ap.parse_args()

    prof = L.resolve(args.limit, args.max_lines, args.layout)
    single = args.single_line or (prof["single_line"] and not args.keep_breaks)
    suffix = ""
    if prof["single_line"] and not single:
        suffix = "，但已用 --keep-breaks 保留换行"
    print(f"排版模式：{prof['label']}（{prof['note']}）{suffix}")

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

        if single:
            src, n_src = merge_to_one_line(src)
            zh, n_zh = merge_to_one_line(zh)
            src_lines = [src] if src else []
            zh_lines = [zh] if zh else []
            if n_src > 1 or n_zh > 1:
                warns.append(f"[{i}] 已将 {n_src}/{n_zh} 行合并为单行，务必确认合并后仍在安全区内")
        else:
            src_lines = [ln.strip() for ln in src.split("\n") if ln.strip()]
            zh_lines = [ln.strip() for ln in zh.split("\n") if ln.strip()]

        lines = src_lines + zh_lines
        if not lines:
            warns.append(f"[{i}] 空字幕块")
        for ln in lines:
            w = width(ln)
            if w > prof["limit"]:
                over = ("精简该行文字（不许换行、不许改时间轴）"
                        if single else "在逗号/连词处断行或精简文字")
                warns.append(f"[{i}] 行超宽 ≈{w:.0f}/{prof['limit']:.0f} → {over}: {ln}")
        cap = L.max_lines_for(lines, prof)
        if len(lines) > cap:
            warns.append(f"[{i}] 行数 {len(lines)} 超过上限 {cap}"
                         + ("（双语只许 2 行、纯中文 1 行）" if prof["bilingual_only"]
                            else f"（单块最多 {cap} 行）"))
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
        print("体检通过：时间轴合法、行宽与行数均在所选模式的安全范围内。")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None
    main()

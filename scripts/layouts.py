# -*- coding: utf-8 -*-
"""排版模式统一配置：抖音竖屏（portrait，多行）与抖音横屏（landscape，单行）。

build_srt.py / validate_srt.py 共用这里的 profile，保证两处阈值一致。
"""

LAYOUTS = {
    "portrait": {
        "label": "抖音竖屏",
        "limit": 46.0,          # 加权行宽上限（英文 ≈46 字符 / 中文 ≈19 字）
        "max_lines": 5,         # 单块总行数上限（源 3 行 + 中 2 行）
        "single_line": False,   # 允许折行：超宽时在逗号/连词处断行
        "bilingual_only": False,
        "note": "允许折行，单块 ≤5 行（源 ≤3 + 中 ≤2），行宽 ≤46",
    },
    "landscape": {
        "label": "抖音横屏",
        "limit": 48.0,          # 加权行宽上限（英文 ≈48 字符 / 中文 ≈25 字）
        "max_lines": 2,         # 双语段 = 源 1 行 + 中 1 行
        "single_line": True,    # 强制单行：任何一行都不许折行
        "bilingual_only": True, # 纯中文段最多 1 行
        "note": "源语言 1 行 + 中文 1 行，不许折行，放不下就精简文字",
    },
}

DEFAULT = "landscape"


def get(name: str) -> dict:
    if name not in LAYOUTS:
        raise KeyError(f"未知排版模式 {name!r}，可选：{', '.join(LAYOUTS)}")
    return LAYOUTS[name]


def resolve(limit=None, max_lines=None, layout: str = DEFAULT) -> dict:
    """返回最终生效的 profile（CLI 传入的 limit / max_lines 优先于模式默认）。"""
    prof = dict(get(layout))
    if limit is not None:
        prof["limit"] = float(limit)
    if max_lines is not None:
        prof["max_lines"] = int(max_lines)
    return prof


def has_latin(s: str) -> bool:
    return any(ch.isascii() and ch.isalpha() for ch in s)


def has_cjk(s: str) -> bool:
    return any(ord(c) > 0x2E80 for c in s)


def is_bilingual(lines) -> bool:
    """一段是否双语对照：既有含中文的行，也有纯拉丁行。"""
    has_cjk_line = any(has_cjk(ln) for ln in lines)
    has_pure_latin = any(has_latin(ln) and not has_cjk(ln) for ln in lines)
    return has_cjk_line and has_pure_latin


def max_lines_for(lines, prof: dict) -> int:
    """横屏模式下，纯中文段只允许 1 行；竖屏统一 ≤5。"""
    cap = prof["max_lines"]
    if prof.get("bilingual_only") and not is_bilingual(lines):
        cap = min(cap, 1)
    return cap

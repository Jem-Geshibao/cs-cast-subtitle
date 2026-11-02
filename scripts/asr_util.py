# -*- coding: utf-8 -*-
"""CS 解说双语字幕流水线 —— 共用 ASR 工具层。

所有脚本共用这里的模型加载、音频解码、RMS 扫描与分块转写逻辑，
避免每次任务重写一遍（也避免重复踩 HuggingFace 联网 / 代理 502 的坑）。
"""
from __future__ import annotations

import glob
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SR = 16000
HF_HUB = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")

# ---------------------------------------------------------------- 领域提示词
# 经实战验证：把真实选手 ID + 地图点位 + 战术术语喂给 initial_prompt，
# 能显著减少 ASR 把人名听成普通单词（donk -> don't / orb）的概率。
CS_PROMPT_EN = (
    "CS2 professional match English commentary. "
    "Players: donk, sh1ro, zont1x, chopper, magixx, tN1R, zweih, Spinx, xertioN, Brollan, "
    "Jimpphat, torzsi, m0NESY, NiKo, huNter-, ZywOo, ropz, flameZ, apEX, Mezii, broky, rain, "
    "frozen, Twistzz, karrigan, jL, iM, b1t, Aleksib, w0nderful, attacker, summer, JamYoung, "
    "Danking, amanek, aliStair, INS, Vexite. "
    "Maps: Mirage, Inferno, Nuke, Ancient, Anubis, Dust2, Vertigo, Train, Overpass. "
    "Terms: CT spawn, T spawn, A site, B site, mid, jungle, connector, ramp, palace, underpass, "
    "short, long, banana, pit, tetris, heaven, catwalk, window, vents, squeaky, lobby, "
    "entry frag, trade, clutch, ace, eco, force buy, full buy, save, plant, defuse, retake, "
    "post-plant, execute, flash, smoke, molotov, HE grenade, one-tap, spray, wallbang."
)

CS_PROMPT_ZH = (
    "CS:GO 职业比赛中文解说，中英混杂，涉及选手名如 donk、m0NESY、ZywOo、NiKo、s1mple、huNter-、"
    "ropz、broky、rain、Twistzz、frozen、apEX、flameZ、Mezii、Spinx、jL、iM、b1t、Aleksib、"
    "magixx、zont1x、sh1ro、chopper、nafany、Perfecto、electroNic、Boombl4、"
    "attacker、summer、JamYoung、Danking、TYLOO、天禄。"
    "战术术语：Mirage、Inferno、Nuke、Ancient、Anubis、Dust2、Vertigo、Train、Overpass、"
    "A点、B点、包点、警家、匪家、中路、短、长、斜坡、香蕉道、二楼、下包、拆弹、残局、回防、"
    "eco、强起、全枪、保枪、道具、烟、闪、燃烧瓶、手雷、对枪、直架、头皮位、"
    "entry frag、trade、clutch、ace、one-tap、spray、wallbang、prefire、hold angle、"
    "smoke、flash、molotov、molly、HE、defuse、plant、bomb site、post-plant、retake、execute。"
)


def pick_prompt(lang: str, no_prompt: bool = False, prompt: str | None = None) -> str | None:
    """英文段默认用英文提示词，中文段默认用中文提示词；--no-prompt 时不给任何预设。"""
    if no_prompt:
        return None
    if prompt:
        return prompt
    return CS_PROMPT_EN if lang == "en" else CS_PROMPT_ZH


# ---------------------------------------------------------------- 模型加载
def force_offline() -> None:
    """按名称加载会触发联网校验，墙内常被代理 502 打断 —— 一律走本地 snapshot。"""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
        os.environ.pop(k, None)


def resolve_model_dir(size: str = "medium") -> str:
    pat = os.path.join(HF_HUB, f"models--Systran--faster-whisper-{size}", "snapshots", "*")
    cands = []
    for d in sorted(glob.glob(pat)):
        bin_path = os.path.join(d, "model.bin")
        if os.path.exists(bin_path) and os.path.getsize(bin_path) > 200 * 1024 * 1024:
            cands.append(d)
    if not cands:
        raise FileNotFoundError(
            f"未找到可用的 faster-whisper-{size} 本地权重（含完整 model.bin）。已扫描：{pat}"
        )
    return cands[-1]


def load_model(size: str = "medium", compute_type: str = "int8"):
    force_offline()
    from faster_whisper import WhisperModel

    return WhisperModel(resolve_model_dir(size), device="cpu",
                        compute_type=compute_type, local_files_only=True)


def load_audio(path: str):
    from faster_whisper import decode_audio

    return decode_audio(path, sampling_rate=SR)


# ---------------------------------------------------------------- 能量扫描
def scan_rms(audio, step: float = 4.0, sr: int = SR):
    """每 step 秒采样一次 RMS，用来定位真实有声区间。"""
    import numpy as np

    total = len(audio) / sr
    out = []
    t = 0.0
    while t < total:
        seg = audio[int(t * sr): int(min(t + step, total) * sr)]
        if len(seg) == 0:
            break
        rms = float(np.sqrt((seg.astype("float32") ** 2).mean()))
        out.append((round(t, 2), round(rms, 5)))
        t += step
    return out


def voiced_intervals(audio, step: float = 4.0, sr: int = SR,
                     abs_thr: float = 0.002, rel_thr: float = 0.02):
    """返回有声区间列表 [(start, end), ...]。

    阈值取 max(abs_thr, 峰值 * rel_thr)，兼顾底噪很低与整体偏响两类素材。
    """
    rms = scan_rms(audio, step, sr)
    if not rms:
        return []
    peak = max(r for _, r in rms)
    thr = max(abs_thr, peak * rel_thr)
    ivs, cur = [], None
    for t, r in rms:
        if r >= thr:
            if cur is None:
                cur = [t, t + step]
            else:
                cur[1] = t + step
        else:
            if cur is not None:
                ivs.append((cur[0], cur[1]))
                cur = None
    if cur is not None:
        ivs.append((cur[0], cur[1]))
    return ivs


def print_rms(audio, step: float = 4.0, sr: int = SR) -> None:
    rms = scan_rms(audio, step, sr)
    peak = max((r for _, r in rms), default=0.0)
    thr = max(0.002, peak * 0.02)
    for t, r in rms:
        bar = "#" * int(min(r * 300, 60))
        flag = "" if r >= thr else "  <silent>"
        print(f"{t:7.1f}s {r:.5f} {bar}{flag}")


# ---------------------------------------------------------------- 转写
def _collect(model, audio, start: float, end: float, lang: str, prompt,
             beam: int, temps, no_speech: float = 0.6, words: bool = True):
    segments, _ = model.transcribe(
        audio[int(start * SR): int(end * SR)],
        language=lang,
        beam_size=beam,
        vad_filter=False,
        word_timestamps=words,
        condition_on_previous_text=False,   # 分段时务必关掉，避免跨段污染与幻觉循环
        temperature=temps,
        initial_prompt=prompt,
        no_speech_threshold=no_speech,
    )
    out = []
    for s in segments:
        txt = (s.text or "").strip()
        if not txt:
            continue
        st, et = s.start + start, s.end + start
        entry = {"start": round(st, 2), "end": round(et, 2), "text": txt, "words": []}
        if words and s.words:
            for w in s.words:
                entry["words"].append({"start": round(w.start + start, 2),
                                       "end": round(w.end + start, 2),
                                       "word": (w.word or "").strip()})
        out.append(entry)
    return out


def transcribe_chunked(model, audio, total: float, lang: str, prompt,
                       chunk: float = 45.0, overlap: float = 5.0,
                       beam: int = 8, temps=(0.0, 0.2, 0.4, 0.6), verbose: bool = True):
    """分段转写。**严禁整段 transcribe**：3 分钟以上必出现幻觉循环并丢段。"""
    results, i = [], 0.0
    while i < total - 0.2:
        j = min(i + chunk, total)
        got = _collect(model, audio, i, j, lang, prompt, beam, list(temps))
        if verbose:
            print(f"--- chunk {i:.1f}-{j:.1f} -> {len(got)} segs", flush=True)
        for e in got:
            if results and e["start"] < results[-1]["end"] - 0.05:
                continue          # 丢弃重叠区重复结果
            results.append(e)
            if verbose:
                print(f"  [{e['start']:7.2f} -> {e['end']:7.2f}] {e['text']}", flush=True)
        if j >= total:
            break
        i = j - overlap
    return results


def transcribe_ranges(model, audio, ranges, lang: str, prompt,
                      beam: int = 10, temps=(0.0, 0.2, 0.4), verbose: bool = True):
    """对指定秒级区间单独重转 —— 用于补录漏段与攻坚听不清的片段。"""
    out = {}
    for (s, e) in ranges:
        got = _collect(model, audio, s, e, lang, prompt, beam, list(temps))
        out[f"{s}-{e}"] = got
        if verbose:
            print(f"=== range {s}-{e} ===", flush=True)
            for it in got:
                print(f"  [{it['start']:7.2f} -> {it['end']:7.2f}] {it['text']}", flush=True)
    return out


def detect_language(model_small, audio, probe_sec: float = 30.0):
    _, info = model_small.transcribe(
        audio[: int(probe_sec * SR)], language=None, beam_size=1, vad_filter=False)
    return info.language, float(info.language_probability)


def save_json(path: str, obj) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"saved -> {path} ({len(obj) if hasattr(obj, '__len__') else '?'} items)")


def parse_ranges(text: str):
    """把 '23-27,26-33' 解析为 [(23.0,27.0),(26.0,33.0)]。"""
    out = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        a, b = part.replace("~", "-").split("-")
        out.append((float(a), float(b)))
    return out

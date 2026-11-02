# -*- coding: utf-8 -*-
"""把 cs-cast-subtitle 安装到任意 agent 的 skills 目录。

用法：
    python install.py --list                          # 查看已预设的目标与安装状态
    python install.py --target workbuddy              # 安装到 ~/.workbuddy/skills
    python install.py --target claude --force          # 覆盖已存在的旧版本
    python install.py --path D:/my-agent/skills        # 安装到任意自定义目录
    python install.py --target claude --link           # 软链而非复制（改仓库即生效）
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SKILL_NAME = "cs-cast-subtitle"

# 仅收录有明确 skills 目录约定的 agent；其他 agent 请用 --path 指定。
TARGETS = {
    "workbuddy": "~/.workbuddy/skills",
    "claude": "~/.claude/skills",
}


def expand(p: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(p)))


def src_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def do_install(dest_root: Path, link: bool, force: bool) -> int:
    dest = dest_root / SKILL_NAME
    source = src_dir()
    if dest.exists() or dest.is_symlink():
        if not force:
            print(f"[跳过] {dest} 已存在。加 --force 覆盖，或先手动删除。")
            return 1
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        else:
            shutil.rmtree(dest)
    dest_root.mkdir(parents=True, exist_ok=True)
    if link:
        try:
            os.symlink(source, dest, target_is_directory=True)
            print(f"[软链] {dest} -> {source}")
        except OSError as e:  # Windows 无开发者模式时常见
            print(f"[警告] 创建软链失败（{e}），回退为复制。")
            shutil.copytree(source, dest)
            print(f"[复制] {source} -> {dest}")
    else:
        shutil.copytree(source, dest, ignore=shutil.ignore_patterns("dist", "__pycache__", ".git"))
        print(f"[复制] {source} -> {dest}")

    print("\n安装完成。接下来：")
    print("  1) 重启/刷新 agent 会话，让它重新扫描 skills 目录；")
    print("  2) 直接对话触发：「用这段解说音频生成双语字幕：<音频路径>」；")
    print(f"  3) 确认环境：python -c \"import faster_whisper\" 且已装 ffmpeg。")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=sorted(TARGETS), help="预设目标 agent")
    ap.add_argument("--path", help="自定义 skills 根目录（优先级高于 --target）")
    ap.add_argument("--link", action="store_true", help="软链方式安装（便于跟随仓库更新）")
    ap.add_argument("--force", action="store_true", help="目标已存在时覆盖")
    ap.add_argument("--list", action="store_true", help="只列出预设目标与当前安装状态")
    args = ap.parse_args()

    if args.list:
        print("预设目标：")
        for name, p in TARGETS.items():
            root = expand(p)
            installed = (root / SKILL_NAME).exists()
            print(f"  {name:<10} {root}   [{'已安装' if installed else '未安装'}]")
        return

    if args.path:
        root = expand(args.path)
    elif args.target:
        root = expand(TARGETS[args.target])
    else:
        ap.error("请指定 --target 或 --path（或先用 --list 查看预设目标）")

    raise SystemExit(do_install(root, args.link, args.force))


if __name__ == "__main__":
    main()

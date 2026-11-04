# cs-cast-subtitle

把 **CS:GO / CS2 职业比赛解说音频** 做成可直接发布的 **双语对照 SRT 字幕**（源语言小写 + 中文对照，时间轴严禁改动）。

> An agent skill that turns CS:GO / CS2 esports casting audio into publish-ready bilingual SRT subtitles — including automatic match identification when you don't know which match it is.

```
1
00:00:00,000 --> 00:00:03,060
not too drastic with the knife, but it's a kill
用刀不必太激进，这刀稳拿击杀
```

**排版双模式（抖音横屏 / 竖屏）**：同一份校对稿，用 `--layout landscape`（默认）出横屏版、`--layout portrait` 出竖屏版。两种模式共用同一硬约束：**一段 = 源语言 1 行 + 中文 1 行、不许折行、不可超出安全区**，区别只在行宽上限（横屏 ≤ 48 / 竖屏 ≤ 46）。

它解决的不是"翻译"问题，而是字幕翻车的三个真实原因：

| 坑 | 本技能的应对 |
|---|---|
| **ASR 幻觉漏段**：整段转写超过 3 分钟就循环重复同一句、丢掉中间大段 | 强制分段转写（45s 切片 / 5s 重叠）+ RMS 能量扫描自动找漏段 + 定点补录 |
| **人名听错**：`don't`→donk、`zelex`→xelex、`Sphinx`→Spinx、`天路`→TYLOO | 锁定比赛背景后把双方五人名单写进提示词重转；英文段再做一次无预设复转 |
| **背景缺失**：不知道是哪场比赛，`14-0` 和点位名就会译错 | 未提供比赛名时按选手 ID / 地图 / 比分 + 文件名日期反查比赛 |

**不是 CS 内容也能用** —— 判定为非赛事解说时自动降级为通用双语字幕流程（口播、访谈、课程同样适用）。

---

## 目录结构

```
cs-cast-subtitle/
├── SKILL.md                        # 技能主文件（agent 只读这一个入口）
├── README.md
├── LICENSE                         # MIT
├── scripts/
│   ├── asr_util.py                 # 共用层：本地模型加载 / RMS 扫描 / 分块转写
│   ├── probe_audio.py              # 探测：时长、语言、能量分布、静音区间
│   ├── transcribe.py               # 分段转写主流程
│   ├── recheck.py                  # 指定区间补录 / 攻坚重转
│   ├── gaps.py                     # 自动列出「有声音但没转出来」的漏段
│   ├── build_srt.py                # 对照数据 → SRT（顺带行宽体检，支持双模式）
│   ├── validate_srt.py             # 发布前校验（支持双模式）
│   ├── layouts.py                  # 排版模式统一配置（横屏/竖屏阈值）
│   └── install.py                  # 安装到各类 agent 的 skills 目录
├── references/
│   ├── cs-terminology.md           # 术语 / 地图点位 / 解说句型 / ASR 错识对照表
│   ├── players-teams.md            # 选手战队实体库、ID 大小写规范、核实方法
│   ├── match-identification.md     # 是否 CS 的判定、比赛反查流程、实战案例
│   ├── subtitle-style.md           # 抖音横屏/竖屏排版规范、翻译口吻、一致性清单
│   └── content-completeness.md     # 内容完整性（必读）：逐字呈现、失败模式、覆盖率审计
└── assets/
    ├── example_bilingual.srt           # 横屏单行版成品样例（landscape 格式基准）
    ├── example_bilingual_portrait.srt  # 竖屏单行版成品样例（portrait 格式基准）
    └── example_interview_bilingual.srt # 采访类成品样例（16 条逐字完整版，完整性基准）
```

---

## 快速开始

### 1. 环境

```bash
python -V                       # 3.9+（本项目在 3.13 实测）
pip install faster-whisper      # 1.2.1 实测可用，已含 PyAV，通常无需另装 ffmpeg
```

模型权重默认用 **medium**（CPU 上速度与精度平衡，解说场景够用）：

```bash
python -c "from faster_whisper import WhisperModel; WhisperModel('medium', device='cpu', compute_type='int8')"
```

> 中国大陆网络提示：HuggingFace 直连常 SSL 失败 / Xet 401 / 代理 502。
> 解决：`curl -sSL -o model.bin https://hf-mirror.com/Systran/faster-whisper-medium/resolve/main/model.bin`
> 再放进 `~/.cache/huggingface/hub/models--Systran--faster-whisper-medium/snapshots/<hash>/`。
> 本技能所有脚本都**按本地 snapshot 路径加载**，不会触发联网校验。

### 2. 安装技能

```bash
git clone https://github.com/Jem-Geshibao/cs-cast-subtitle.git
cd cs-cast-subtitle
python scripts/install.py --list          # 查看目标与安装状态
python scripts/install.py --target workbuddy
```

### 3. 跑第一个任务

对话式（推荐，agent 会自己走完 8 步）：

```
用这段解说音频生成双语字幕，发布到抖音：C:/audio/10月28日 (1).MP3
```

命令行式（想自己掌控每一步）：

```bash
PY="python"; SK="."
"$PY" "$SK/scripts/probe_audio.py"    "audio.mp3" --step 4 --json probe.json
"$PY" "$SK/scripts/transcribe.py"     "audio.mp3" --lang en --chunk 45 --overlap 5 --out segments.json
"$PY" "$SK/scripts/gaps.py"           "audio.mp3" segments.json          # 自动列漏段
"$PY" "$SK/scripts/recheck.py"        "audio.mp3" --ranges "23-27,26-33" --lang en --out recheck.json
# 人工校对+翻译后写成 pairs.json
"$PY" "$SK/scripts/build_srt.py"      pairs.json "audio_bilingual_corrected.srt" --layout landscape   # 竖屏用 portrait
"$PY" "$SK/scripts/validate_srt.py"   "audio_bilingual_corrected.srt" --layout landscape             # 必须与生成时同模式
```

`pairs.json` 格式（`src` 为空即纯中文段；横屏模式下脚本会自动把软换行合并为单行）：

```json
[
  {"start": 0.0, "end": 3.06,
   "src": "not too drastic with the knife, but it's a kill",
   "zh": "用刀不必太激进，这刀稳拿击杀"},
  {"start": 25.62, "end": 29.78, "src": null, "zh": "这波换人很果断"}
]
```

---

## 工作方式

```
探测音频 → 判定是否 CS 解说 → 锁定比赛背景(无比赛名则反查) → 分段转写
        → 漏段补录 + 英文段无预设复转 → 纠错/翻译/排版 → [非CS则降级] → 校验交付
```

1. **探测**：时长、语言、RMS 能量、静音区间（静音区不用补录，避免瞎猜）。
2. **判定**：选手 / 赛事 / 地图 / 玩法词四类线索，命中 2 类以上才算 CS 解说。
3. **锁定背景**：用户给了比赛名就检索确认；没给就抓线索反查（HLTV → Liquipedia → Bo3.gg），用文件名日期收敛。拿到名单后回填提示词重转验证。
4. **分段转写**：45s 切片 / 5s 重叠，`condition_on_previous_text=False` 写死防幻觉。
5. **补录**：`gaps.py` 找漏段，`recheck.py` 重转；英文段必做一次 `--no-prompt` 无预设复转。
6. **纠错翻译**：先结合背景推断说话人真实意图 → 改错词 → 再翻译。时间轴一律用 ASR 原值。
7. **降级**：非 CS 内容不终止任务，换领域提示词走通用双语流程。
8. **校验 + 覆盖率审计**：`validate_srt.py` 查序号、时间轴、行宽行数；再用 `gaps.py` 对最终 pairs.json 做**覆盖率审计**——每个"有声音无字幕"区间必须能解释为静音/环境声/存疑，**只要是人物说话就必须有字幕**，未解释区间不清零不交付（见 `references/content-completeness.md`）。

---

## 排版模式（横屏 / 竖屏）

同一份校对稿可出两种版本，阈值统一放在 `scripts/layouts.py`：

| | `landscape` 横屏（默认） | `portrait` 竖屏 |
|---|---|---|
| 单块结构 | 源语言 1 行 + 中文 1 行，**不许折行** | 源语言 1 行 + 中文 1 行，**不许折行** |
| 纯中文段 | 1 行 | 1 行 |
| 加权行宽 | ≤ 48（中文 ≈25 字 / 英文 ≈48 字符） | ≤ 46（中文 ≈24 字 / 英文 ≈46 字符） |
| 超宽处理 | 按词级时间轴**拆段**，严禁删内容 | 按词级时间轴**拆段**，严禁删内容 |
| 样例 | `assets/example_bilingual.srt` | `assets/example_bilingual_portrait.srt` |

两种模式规则完全相同，只是竖屏画面更窄、行宽上限更低；放不下时**首选按 ASR 词级时间轴把长句拆到连续多段**（说话内容必须逐字完整、严禁删内容），拆无可拆才精简，不许换行、不许改时间轴。

```bash
python scripts/build_srt.py    pairs.json out.srt --layout portrait   # 竖屏
python scripts/validate_srt.py out.srt     --layout portrait
```

**生成与校验必须用同一个 `--layout`**，否则校验结果不可信。

---

## 部署到其他 Agent

### 原理

符合 Anthropic *Agent Skills* 约定的目录即可被识别：一个含 `SKILL.md` 的文件夹，`SKILL.md` 顶部带 YAML frontmatter（`name` + `description`），`description` 决定 agent 何时触发它。本技能完全遵循该约定，因此**换 agent 只需换目录**。

### 一键安装

```bash
python scripts/install.py --target workbuddy          # ~/.workbuddy/skills
python scripts/install.py --target claude             # ~/.claude/skills
python scripts/install.py --path  /any/agent/skills   # 任意自定义目录
python scripts/install.py --target claude --link      # 软链，改仓库即时生效
python scripts/install.py --target claude --force     # 覆盖旧版本
```

| 目标 | skills 根目录 | 命令 |
|---|---|---|
| WorkBuddy / CodeBuddy | `~/.workbuddy/skills` | `python scripts/install.py --target workbuddy` |
| Claude Code | `~/.claude/skills` | `python scripts/install.py --target claude` |
| 其他有 skills 目录的 agent | 自定义 | `python scripts/install.py --path <its/skills/dir>` |

### 手动安装（复制 / 软链）

```bash
# 复制
cp -r cs-cast-subtitle ~/.workbuddy/skills/

# Linux / macOS 软链
ln -s "$(pwd)/cs-cast-subtitle" ~/.claude/skills/cs-cast-subtitle

# Windows（管理员或开发者模式）
cmd //c mklink /D "%USERPROFILE%\.claude\skills\cs-cast-subtitle" "%CD%\cs-cast-subtitle"
```

### 从 GitHub 安装

```bash
# 方式一：克隆后安装
git clone https://github.com/Jem-Geshibao/cs-cast-subtitle.git
python cs-cast-subtitle/scripts/install.py --target workbuddy

# 方式二：作为你自己仓库的子目录（推荐，便于改）
git submodule add https://github.com/Jem-Geshibao/cs-cast-subtitle.git skills/cs-cast-subtitle

# 方式三：Download ZIP → 解压 → 把 cs-cast-subtitle 文件夹放进 skills 目录
```

### 没有 skills 目录的 agent（Cursor 等）

1. 把 `SKILL.md` 全文作为该 agent 的**规则文件**（如 `.cursor/rules/cs-cast-subtitle.mdc`），frontmatter 保留即可；
2. 或把 `SKILL.md` 内容贴进 system prompt / 自定义指令；
3. 脚本仍可独立使用——它们不依赖 agent，直接 `python scripts/*.py` 即可。

### 多 agent / 团队共享

- 项目级共享：放到仓库的 `.workbuddy/skills/` 或 `.claude/skills/`，随代码一起提交；
- 团队统一：`git submodule` + `install.py --link`，保证所有人用的是同一份最新规则。

---

## 脚本参考

| 脚本 | 关键参数 | 作用 |
|---|---|---|
| `probe_audio.py` | `<音频>` `--step` `--json` | 时长、语言、RMS 扫描、静音区间 |
| `transcribe.py` | `--lang auto/en/zh` `--prompt` `--no-prompt` `--chunk` `--overlap` `--model` `--out` | 分段转写主流程 |
| `gaps.py` | `<音频> <segments.json>` `--tolerance` `--min-gap` | 自动列出可疑漏段并给出可复制区间 |
| `recheck.py` | `--ranges "23-27,26-33"` `--lang` `--prompt` `--no-prompt` `--beam` | 区间补录 / 攻坚重转 |
| `build_srt.py` | `<pairs.json> <out.srt>` `--layout` `--limit` `--max-lines` `--no-lower` `--keep-breaks` | 渲染 SRT（横屏默认自动合并为单行）+ 行宽体检 |
| `validate_srt.py` | `<file.srt>` `--layout` `--limit` `--max-lines` | 发布前校验，有问题退出码 1 |
| `layouts.py` | — | 横屏/竖屏阈值统一配置，被 build/validate 共用 |
| `install.py` | `--target` `--path` `--link` `--force` `--list` | 安装到各 agent |

---

## 常见问题

**Q：为什么不能直接用 `model.transcribe(整段音频)`？**
3 分钟以上必出幻觉循环（重复同一句十几遍）并丢段。脚本里已强制分段 + 关闭 `condition_on_previous_text`。

**Q：`WhisperModel("medium")` 报网络错误 / 502？**
按名称加载会联网校验。脚本统一走本地 snapshot 路径；也可用 `install.py` 同款环境变量：`HF_HUB_OFFLINE=1` 并清掉代理变量。

**Q：控制台中文乱码 / UnicodeEncodeError？**
Windows 下加 `PYTHONIOENCODING=utf-8`（脚本内已 `reconfigure`，极端情况仍需该变量）。

**Q：人名还是听错了？**
先确认比赛锁对了没——把双方五人名单写进 `recheck.py --prompt` 重转；仍不确定就在交付说明里标 `【?】`，不要编造。

**Q：一条字幕太长、超出安全区怎么办？**
先看用的是哪个模式。两种模式都是「一段 = 源 1 行 + 中 1 行、**不许折行**」，区别只在行宽：横屏 ≤ 48，竖屏 ≤ 46。**超宽时首选按 ASR 词级时间戳把这句话拆到连续多段**（内容必须逐字完整），拆到最细仍超宽才按 `references/subtitle-style.md` 第三节精简。**不要换行、不要改时间轴、不要整句丢弃**。

**Q：字幕文件改了，剪映里却没变化？**
剪映导入 SRT 时会把它**复制**成草稿内的文字片段，之后改源文件草稿不会同步。必须删掉旧字幕轨道后，走「文本 → 本地字幕 → 导入字幕」重新导入；**不要点「智能字幕 → 开始识别」**，那是机翻重识别，会盖掉人工稿。

**Q：large-v3 能不能用？**CPU 下极慢（4 分钟音频数十分钟），且部分镜像下载的 `model.bin` 不完整。默认 medium 即可。

---

## 硬规则（改代码时请保留）

1. **时间轴严禁改动**，必须用 ASR 原始 `start/end`。
2. **排版模式二选一**：两种模式均为「每段 源 1 行 + 中 1 行、不许折行、纯中文 1 行」，区别只在行宽（横屏 ≤ 48 / 竖屏 ≤ 46）。生成与校验必须用同一个 `--layout`。
3. 源语言行**全小写**；中文解说/采访段**只输出中文**，不做双语对照。
4. 无法确认的人名标 `【?】` 并在交付说明列出，**禁止编造**。
5. 校验不通过不得交付；**覆盖率审计未清零不得交付**（`gaps.py` 对最终 pairs.json 跑一次，说话内容必须全有字幕，详见 `references/content-completeness.md`）。
6. **说话内容逐字完整**：长句超宽按词级时间轴拆段，严禁删内容；短插语（yeah / and that's it 等）必须成条；环境声加「（全场欢呼）」标注。

---

## 贡献

欢迎提 issue / PR：

- 新增 ASR 错识对照（`references/cs-terminology.md` 第四节）
- 补充已核实的选手战队实体（`references/players-teams.md`，请附核实来源与时间）
- 沉淀新的比赛反查案例（`references/match-identification.md` 第五节）
- 脚本改进：保持 CLI 参数向后兼容，并在 README 脚本参考表同步更新

## 许可证

[MIT](LICENSE)

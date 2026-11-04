---
name: cs-cast-subtitle
description: 把 CS:GO/CS2 职业比赛解说音频做成可发布的双语对照 SRT 字幕（英文源语言小写 + 中文对照，时间轴严禁改动）。当用户提供解说/采访音频并要求"识别语音生成字幕""校对+翻译""生成双语 SRT""做成抖音字幕"时使用，支持未提供比赛名时按音频线索反查比赛以核实选手与战队；若音频并非 CS 赛事解说（口播、访谈、其他题材），则自动降级为通用双语对照字幕流程。含长音频幻觉规避、漏段补录、选手实体联网核实、抖音横屏/竖屏双模式排版规范（用 --layout landscape|portrait 切换）。
agent_created: true
---

# CS 职业解说 → 双语对照字幕

把解说音频转成可直接发布的双语 SRT。核心难点**不是翻译，而是三件事**：

1. **ASR 幻觉漏段** —— 整段转写会在 3 分钟以上循环重复同一句并丢掉中间大段；
2. **人名听错** —— `don't`/`donk`、`zelex`/`xelex`、`Sphinx`/`Spinx`，不锁定比赛就无从判断；
3. **背景缺失** —— 不知道哪场比赛，就无法把 `14-0` 和点位名译对。

## 输入

- 必填：音频文件路径（`MP3/WAV/M4A/MP4` 均可）。
- 可选：比赛名称（赛事 + 对阵 + 日期）。**未提供时必须走反查流程**。
- 可选：目标平台与排版模式（默认抖音横屏 `landscape`；竖屏用 `--layout portrait`，见 `references/subtitle-style.md`）。

工作目录即音频所在目录，所有中间产物与最终 SRT 都写在音频旁边。

## 环境

```bash
PY="C:/Users/34333/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
SK="C:/Users/34333/.workbuddy/skills/cs-cast-subtitle"
```

已装 `faster-whisper 1.2.1`，本地权重 medium / small 可用（large-v3 的 `model.bin` 下载不完整，CPU 下也极慢，**默认用 medium**）。

## 流程

### 步骤一：探测音频

```bash
"$PY" "$SK/scripts/probe_audio.py" "<音频路径>" --step 4 --json "<原名>_probe.json"
```

拿到时长、语言（中英混杂素材常判成 `zh`）、RMS 能量分布。**静音区间必须记录**——后续被 `gaps.py` 报出来的"漏段"若落在静音区，就是真静音，不用补录。

### 步骤二：判定是否为 CS 赛事解说

读 `references/match-identification.md` 的线索清单，对粗转结果做判定。

- 命中 → 继续步骤三。
- 未命中 → 跳到**步骤七（通用双语降级流程）**。

### 步骤三：锁定比赛背景

**这是翻译质量的分水岭，不可跳过。**

- 用户给了比赛名：检索确认赛事全称、阶段、比分、地图顺序、**双方首发五人名单与准确大小写**。
- 用户没给比赛名：按 `references/match-identification.md` 的反查流程走——抓选手 ID / 地图名 / 比分线索 → 组合检索（HLTV、Liquipedia、Bo3.gg）→ 用文件名日期收敛 → 命中后回填提示词验证。

拿到名单后，把**双方五人 ID 写进 `initial_prompt`** 再重转一遍不确定片段。若新结果明显更合理，说明比赛锁对了。
实体拼写与核实方法见 `references/players-teams.md`。

### 步骤四：分段转写（严禁整段）

```bash
"$PY" "$SK/scripts/transcribe.py" "<音频路径>" --lang en \
      --prompt "CS2 commentary. Spirit: donk, zont1x, sh1ro, magixx, tN1R. MOUZ: Spinx, xertioN, Brollan, Jimpphat, torzsi. ..." \
      --chunk 45 --overlap 5 --out "<原名>_segments.json"
```

- `--lang` 用 `auto` 自动探测；中文段用 `zh`（内置中文领域提示词）。
- 长音频默认 45s 切片 / 5s 重叠；效果不佳时用 16s / 4s 细粒度重来。
- `condition_on_previous_text=False` 已在脚本里写死，这是防幻觉循环的关键。

### 步骤五：补录漏段与攻坚重转

```bash
# 自动找「有声音但没转出来」的区间
"$PY" "$SK/scripts/gaps.py" "<音频路径>" "<原名>_segments.json"

# 对可疑区间单独重转（区间可直接复制上一条命令的输出）
"$PY" "$SK/scripts/recheck.py" "<音频路径>" --ranges "23-27,26-33" --lang en \
      --prompt "<回填双方名单>" --beam 10 --out "<原名>_recheck.json"
```

**英文段必须做一次无预设复转**（`--no-prompt`）：中文提示词会把英文人名带偏（经典案例 `that danking` 被听成 `that orb`）。无预设结果往往更准。

补录结果按时间轴并入主稿；同一时段有冲突时，选**符合比赛背景**的那一版。

### 步骤六：纠错、翻译与排版

读 `references/cs-terminology.md`（术语/点位/ASR 错识对照）与 `references/subtitle-style.md`（排版与口吻）。

顺序固定：**先结合背景推断说话人真实意图 → 改错词 → 再翻译**。

硬规则：
- **时间轴严禁改动**，一律用 ASR 原值。
- 源语言行**全小写**；中文解说段只输出中文，不做双语对照。
- 已确认的选手 ID、战队名、地图点位不翻译。
- 无法确认的人名：标 `【?】` 并在交付说明里列出，**禁止编造**。
- **排版模式二选一**（`--layout`，两种模式阈值与规则见 `references/subtitle-style.md` 第零节）：
  - 两种模式共用同一硬约束：一段 = 源语言 1 行 + 中文 1 行，**不许折行**；纯中文段 1 行；放不下时**精简文字**，不许换行、不许改时间轴。
  - `landscape`（横屏，默认）：行宽 ≤ 48。
  - `portrait`（竖屏）：行宽 ≤ 46（竖屏画面更窄）。

横屏模式下 `build_srt.py` 会把 `pairs.json` 里的软换行自动合并为单行；超宽时会提示精简。

把校对后的对照数据写成 `pairs.json`（`[{"start","end","src","zh"}]`，`src` 为空即纯中文段），再渲染：

```bash
"$PY" "$SK/scripts/build_srt.py" pairs.json "<原名>_bilingual_corrected.srt" --layout landscape   # 竖屏用 portrait
```

### 步骤七：非 CS 内容的降级流程

判定不属于 CS 赛事解说时，**不要终止任务**，改为通用双语对照字幕：

1. 同样执行步骤一、四、五（分段转写 + 补录），但提示词换成该音频的实际领域（口播/访谈/课程等），或直接用 `--no-prompt`。
2. 跳过步骤三的选手实体核实；通用专有名词（人名、品牌、产品型号）仍应联网核实。
3. 排版规则不变：源语言小写 + 中文对照、时间轴不改、按所选 `--layout` 模式的行宽与行数上限排版。
4. 交付物同名 `<原名>_bilingual_corrected.srt`，并在说明里注明"非 CS 解说素材，已按通用双语流程处理"。

### 步骤八：校验与交付

```bash
"$PY" "$SK/scripts/validate_srt.py" "<原名>_bilingual_corrected.srt" --layout landscape   # 必须与生成时同模式
```

校验项：序号连续、时间轴单调不重叠、`end > start`，以及按所选模式检查行宽与行数（两种模式均 ≤2 行 / 纯中文 1 行；横屏行宽 ≤48，竖屏 ≤46）。有报错必须修到通过。

交付时说明：比赛背景与核实来源、关键纠错表（错识 → 正确）、存疑清单、字幕条数与时长。

## 已知坑

- **WhisperModel 按名称加载会联网校验**，常被代理 502 打断 → 脚本一律走本地 snapshot 路径（`scripts/asr_util.py` 已处理）。
- **large-v3 的 model.bin 不完整**（约 2.96GB 处截断），需从 `hf-mirror` 重下才能用；CPU 下 medium 更快且对解说足够。
- **控制台打印中文** 需 UTF-8，脚本内已 `reconfigure`；若仍报 `UnicodeEncodeError`，加 `PYTHONIOENCODING=utf-8`。
- **文件名日期 ≠ 比赛日期**，通常是录制/下载日，比赛在当天或前 1–3 天。

## 参考文件

| 文件 | 用途 |
|---|---|
| `references/cs-terminology.md` | 术语/点位/解说句型/ASR 错识对照表 |
| `references/players-teams.md` | 已核实选手战队库、大小写规范、核实方法 |
| `references/match-identification.md` | 是否 CS 的判定、比赛反查流程、实战案例 |
| `references/subtitle-style.md` | 抖音横屏/竖屏双模式排版规范、单行化与精简、翻译口吻、一致性清单 |
| `scripts/layouts.py` | 排版模式统一配置（阈值由 build/validate 共用） |
| `assets/example_bilingual.srt` | 横屏单行版成品样例（landscape 格式基准） |
| `assets/example_bilingual_portrait.srt` | 竖屏单行版成品样例（portrait 格式基准） |

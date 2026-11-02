# 选手 / 战队实体库与核实方法

**战队名单变动极快（转会、下放、替补），本表只作为候选拼写提示，
任何进入最终字幕的人名都必须先联网核实当期首发名单。**

## 一、已核实过的实体（含核实时间与结论）

| 名称 | 身份 / 结论 | 核实时间 |
|---|---|---|
| Danking（吕郑豪，蛋总/蛋神） | 1999 年生于河北石家庄，前 TYLOO / EHOME 狙击手，现主播 | 2026-10 |
| TYLOO | 天禄，中国 CS 战队（**不是**"天路/天禄"以外的写法） | 2026-10 |
| donk（Danil Kryshkovets） | Team Spirit 明星选手，2024 上海 Major 期间打出名场面 | 2026-10 |
| xelex | MOUZ 选手（ASR 极易听成 zelex / Alex） | 2026-10 |
| xertioN | MOUZ 选手（ASR 极易听成 Zirchin / Zertian） | 2026-10 |
| Spinx | MOUZ / 前 Vitality 选手（ASR 易听成 Sphinx） | 2026-10 |
| attacker / summer / JamYoung | TYLOO 选手 | 2026-10 |
| amanek / aliStair | 曾效力 TYLOO / Renegades 的选手 | 2026-10 |
| NiKo / huNter- / m0NESY | G2 时期核心选手 | 2026-10 |

### 已核实的阵容快照

- **Team Spirit（2026 年核实）**：donk、magixx（IGL）、sh1ro、tN1R、zont1x；**chopper 已下放**（老音频里出现 chopper 时不一定错，需注意音频年份）。
- **MOUZ（2026 年核实）**：Spinx、xertioN、Brollan、Jimpphat、torzsi。
- **Vitality**：ZywOo、ropz、flameZ、apEX、Mezii。
- **FaZe**：broky、rain、frozen、Twistzz、karrigan。
- **NAVI**：jL、iM、b1t、Aleksib、w0nderful。

## 二、核实方法（按优先级）

1. **HLTV**（`hltv.org`）：`选手ID` 的 player page 显示现役队伍；`matches` 页可按日期查赛程与比分、地图顺序。
2. **Liquipedia**（`liquipedia.net/counterstrike`）：赛事页面含双方首发五人、替补、地图 BP 顺序，改名单有据可查。
3. **Bo3.gg / strafe.com**：快速查比赛结果与选手数据（ADR、K-D）。
4. **中文二创源（B站 / 抖音 / 虎扑）**：中文解说音频常搬运自这些平台，搜索 `选手ID + 赛事名` 常能直接定位到原视频与比赛信息。

**搜索模板**：
- `<选手ID> CS2 <地图名> <年份>`（如 `donk Mirage ace 2026`）
- `<赛事名> <阶段> <队伍A> vs <队伍B>`（如 `PGL Masters Bucharest 瑞士轮 Spirit MOUZ`）
- `site:liquipedia.net <赛事名> <队伍A> <队伍B>`
- 若音频文件名是日期（如 `10月28日.MP3`），比赛通常在当天或前 1–3 天 —— **把日期作为搜索过滤条件**。

## 三、核实清单（锁定比赛后必须拿到）

- [ ] 赛事全称 + 阶段（小组赛 / 瑞士轮 / 淘汰赛 / 决赛）
- [ ] 对阵双方与最终比分（大比分与每图比分）
- [ ] 地图顺序（判断点位名归属）
- [ ] 双方首发五人 ID 与**准确大小写**（donk 全小写、xertioN 大小写混合、m0NESY 中间是数字 0）
- [ ] 本场关键名场面（ace / clutch / 特殊战术），用于校验解说情绪句

## 四、大小写规范（字幕里极易出错）

| 正确 | 常见错误 |
|---|---|
| donk | Donk / don'k |
| xertioN | Xertion / xertion / XertioN |
| m0NESY | monesy / m0nesy（0 是数字零） |
| huNter- | hunter / huNter（结尾连字符要保留） |
| sh1ro | shiro / sh1r0（1 是数字一） |
| zont1x | zontix / zont1X |
| s1mple | simple |
| b1t（1 是数字一） | bit |
| ZywOo | zywoo / Zywoo |
| tN1R | tn1r |
| jL | JL / jl |
| iM | IM |
| apEX | apex |
| electroNic | electronic |

**源语言行按要求全小写输出**（如 donk、xelex、ct）。中文行内嵌入的 ID，历史交付稿同样采用全小写（`donk拉开距离`、`spinx和xertion联手得分`、`donk俯身击倒xelex`）——
**默认沿用小写以保持上下两行视觉一致**；仅当用户明确要求"ID 保留官方大小写"时，才在中文行写 `xertioN`、`m0NESY`、`huNter-`。
无论哪种写法，**同一份字幕内必须统一**，不能一处小写一处大写。

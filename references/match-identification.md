# 比赛背景锁定（未提供比赛名时的反查流程）

翻译准确性的上限取决于背景是否锁定。**人名翻译错了，整段字幕就废了**，所以这一步不能省。

## 一、先判断：这是不是 CS 赛事解说音频？

用 `probe_audio.py` 拿到语言后，用 small 模型粗转前 30–60 秒，检查是否出现以下任一类线索：

- 选手/战队：donk、m0NESY、ZywOo、TYLOO、Spirit、MOUZ、G2、NAVI、FaZe、Vitality……
- 赛事：Major、IEM、ESL、BLAST、PGL、StarLadder、Bucharest、Shanghai……
- 地图：Mirage、Inferno、Nuke、Ancient、Anubis、Dust2、Vertigo、Train、Overpass
- 玩法词：bomb site、plant、defuse、eco、clutch、ace、retake、CT、T side、entry frag
- 中文解说特征词：包点、下包、拆弹、残局、回防、警家、匪家、强起、保枪、A点、B点

**命中 2 类以上** → 判定为 CS 赛事解说，进入比赛背景锁定流程。
**均未命中** → 走「通用双语字幕」降级分支（见 SKILL.md 步骤七），仍用同一套 ASR 与排版规范，只是不做选手实体核实。

## 二、用户提供比赛名时

直接按 `<赛事名> <对阵> <日期>` 检索确认，拿到：赛事全称、阶段、比分、地图顺序、双方首发名单。
**不要完全信任用户给的信息**：若检索到的名单与音频里听到的名字矛盾，以音频为准并回问用户。

## 三、未提供比赛名时的反查流程

1. **提取线索**：从粗转文本里抓出所有疑似人名、地图名、赛事名、比分、日期。
2. **按可靠性排序选用**：
   - 强线索：罕见选手 ID（donk、xertioN、xelex）、具体赛事名
   - 中线索：地图名 + 年份
   - 弱线索：常见词（CT、flash）
3. **组合检索**（WebSearch）：
   - `<选手ID> <地图名> <年份>`
   - `<赛事名> <队伍A> vs <队伍B> 比分`
   - `site:liquipedia.net <赛事名> <队伍A> <队伍B>`
   - `<选手ID> CS2 <月份> <年份> ace/clutch`（找名场面视频）
4. **用文件名日期收敛**：音频文件名常是录制/下载日期（如 `10月28日.MP3`），比赛通常在当天或前 1–3 天；把日期加进检索词。
5. **锁定后回填提示词**：把双方五人名单写进 `recheck.py --prompt`，重转不确定的片段 —— 这也是验证假设的手段：如果新转写结果明显更合理，说明比赛锁对了。
6. **交叉验证**：音频里出现的比分/回合描述，必须能对上检索到的比赛进程。

## 四、无法锁定时

- 只用**音频内可自证**的实体，其余按音译处理。
- 存疑处在该条字幕的中文行尾不标注（会破坏画面），而是**在交付说明里单独列出存疑清单**，用 `【?】` 标记。
- 明确告知用户"比赛未锁定，人名按音译，建议确认后我再修订"。

## 五、实战案例（可参照）

**输入**：`10月28日 (1).MP3`，81 秒英文解说，无比赛名。
**线索**：反复出现 `don't/donk`、疑似人名 `zelex`、`Sphinx/Zirchin`、地图点位 `jungle`。
**反查**：`donk jungle ace 2026` + 文件名日期 → 10月27日 PGL Masters Bucharest 瑞士轮 **Spirit vs MOUZ**。
**回填**：Spirit（donk/magixx/sh1ro/tN1R/zont1x）vs MOUZ（Spinx/xertioN/Brollan/Jimpphat/torzsi）。
**纠错**：`zelex`→**xelex**、`Sphinx/Zirchin/Zertian`→**Spinx / xertioN**、`don't`→**donk**、`More fact toward CT`→**four back towards CT**。
**结论**：donk 在 Mirage 打出 ace，全场 35-20 —— 与音频情绪吻合，背景锁定成立。

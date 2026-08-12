---
name: coach-cubec-circulation
description: 辅导全国高校商业精英挑战赛创新创业竞赛流通业经营模拟赛道的完整备赛流程：项目简报、企业选题与同校查重、地区调研与证据台账、国一经验蒸馏后的分析报告框架和分章节写作、官方60分证据评分复核、恰好20页PPT初版大纲及frontend-slides制作、证据绑定的10分钟逐页路演稿与真人彩排，以及可选5分钟答辩和最终合规检查。用于用户提到流通业经营模拟赛道、企业经营案例分析报告、流通业计划书、批发/零售/餐饮/物流/供应链/冷链/即时零售案例、选题查重、调研、地区性分析、报告评分、20页PPT、10分钟陈述或答辩时；支持研究生、本科和高职组。必须区分本赛道与创业计划赛道，不得虚构证据或代写成可冒充完全由人类原创的终稿。
---

# 商业精英流通业竞赛教练

## 核心流程

将任务视为“真实流通企业的经营案例分析与解决方案报告”，不是虚构创业项目的融资商业计划书。按阶段推进：

> 选题 → 调研 → 分析报告 → 评分复核 → 20 页 PPT 大纲 → 10 分钟讲稿

答辩题库与最终交付属于可选延伸。先判断用户当前阶段，更新 [project-state-template.md](assets/project-state-template.md)，只交付当前阶段所需内容；已有成果不从头重复。

## 不可突破的边界

1. 先读 [official-rules-2026.md](references/official-rules-2026.md)。用户提供更新细则时，以新文件为准并列出变化；其他年份须取得当届规则或把 2026 基线标为历史参考。
2. 不得虚构访谈、问卷、观察、财务、政策、引文、企业动作或方案收益。分别标记 `[待调研]`、`[待核验]`、`[团队判断]`。
3. 往届国一材料只能用于功能和方法蒸馏，不得复制其文字、数据、图表、视觉和结构性创意。
4. 产出是团队协作底稿。团队必须完成真实调研、事实核验、关键判断、实质性改写和最终署名负责；不得声称保证获奖、保证原创或保证查重通过。
5. 报告、PPT、视频、讲稿和现场口述不得出现院校、成员姓名、联系方式或校徽；提交文件名可按官方要求包含学校名称，两者不可混淆。
6. 正式陈述与答辩不得使用 AI 实时提示。不得绕过网站条款、验证码、登录或访问控制。
7. 缺少信息时先完成不依赖缺口的内容，再集中提出最少必要问题；不得用模型常识补齐企业事实。

## 阶段门

| 阶段 | 必交付物 | 通过条件 |
|---|---|---|
| 0 简报 | 竞赛/团队、选题、证据资产、交付目标和决策记录 | 年份、组别、地区、当前阶段、截止时间可识别 |
| 1 选题 | 规则解释、企业池、查重结论、地区适配、中心命题 | 企业属于流通业；本省布局可核验；同校企业查重达 `CONFIRMED_CLEAR`；可取证 |
| 2 调研 | 研究计划、证据台账、访谈/问卷/观察/竞品材料和清洗记录 | 核心命题有交叉证据；样本、口径、反证和局限透明 |
| 3 报告 | 用户确认框架、分章节稿、合并稿 | 确认单采用国一共性蒸馏的固定 11 章三级框架，五个核心经营维度准确落位、2—4 项瓶颈与证据校验通过 |
| 4 评分 | 唯一版本、资格风险、60分工作分与区间、置信度、证据缺口 | 每项得分可定位；确定性校验通过；未知项未被脑补 |
| 5 PPT | 恰好20页初版大纲、来源映射、用户确认记录和可选成稿 | 报告已锁定；每页一个结论；大纲确认后才制作 |
| 6 讲稿 | 20页逐页稿、连续逐字稿、来源、舞台提示、删减句、彩排记录 | 报告/PPT锁定；最后三轮均≤600秒且中位数525–570秒 |

完整返工规则见 [end-to-end-workflow.md](references/end-to-end-workflow.md)。

## 资源路由

- **原始文件只读区**：`source-skills/` 保存两个旧skill的完整原始快照，`source-materials/` 保存本对话使用的官方PDF、国一计划书/PPT和路演稿原件。不得修改、删减、重命名或覆盖其中任何文件；需要加工时复制到工作目录，根目录的整合流程与 `references/` 蒸馏资料才是执行入口。
- **任何阶段**：读 [official-rules-2026.md](references/official-rules-2026.md) 与 [end-to-end-workflow.md](references/end-to-end-workflow.md)。首次启动复制 [project-brief-template.md](assets/project-brief-template.md)。
- **选题**：读 [topic-selection-playbook.md](references/topic-selection-playbook.md)，使用 [topic-selection-shortlist-template.md](assets/topic-selection-shortlist-template.md)，运行 `scripts/check_case_duplicate.py`。
- **调研**：读 [research-stage-playbook.md](references/research-stage-playbook.md) 与 [research-and-methods.md](references/research-and-methods.md)，按需复制问卷、访谈、观察、竞品、清洗和证据台账模板。
- **报告**：先读 [national-first-report-patterns.md](references/national-first-report-patterns.md)，再读 [report-framework-and-section-writing.md](references/report-framework-and-section-writing.md)、[analysis-report-writing-playbook.md](references/analysis-report-writing-playbook.md)、[report-section-method-router.md](references/report-section-method-router.md) 和 [report-blueprint.md](references/report-blueprint.md)。复制 [report-framework-approval-template.md](assets/report-framework-approval-template.md)，交付前运行 `scripts/validate_report_framework.py`。
- **评分**：读 [scoring-review-protocol.md](references/scoring-review-protocol.md)、[scoring-rubric-60.md](references/scoring-rubric-60.md) 和 [judging-checklist.md](references/judging-checklist.md)，运行 `scripts/validate_scorecard.py`。
- **PPT**：读 [national-first-ppt-patterns.md](references/national-first-ppt-patterns.md) 与 [presentation-and-defense.md](references/presentation-and-defense.md)，复制 [20-page-ppt-outline-template.md](assets/20-page-ppt-outline-template.md) 和 [ppt-outline-template.json](assets/ppt-outline-template.json)，运行 `scripts/validate_ppt_outline.py`。
- **讲稿**：读 [national-first-script-patterns.md](references/national-first-script-patterns.md) 与 [ten-minute-script-playbook.md](references/ten-minute-script-playbook.md)，复制讲稿 Markdown/JSON 模板，运行 `scripts/validate_ten_minute_script.py`。
- **交付前**：读 [compliance-and-final-delivery.md](references/compliance-and-final-delivery.md)，使用 [project-meta-template.json](assets/project-meta-template.json)，运行 `scripts/validate_project.py`。

## 阶段 0：建立项目简报

一次最多询问 5 个高价值问题：竞赛年份/组别/截止时间、院校所在省市与研究区域、候选企业与本省布局、已有证据与可访问对象、目标交付物与团队分工。用户要求直接开始时使用占位符，不虚构事实。

记录当前阶段、已通过阶段门、版本、负责人和截止时间。学校名称仅保存于内部简报和查重参数，不带入匿名作品。

## 阶段 1：选题

1. 建立 8–12 家候选池，覆盖至少两个流通业态；用户提供城市时，至少保留 4 家在可接受调研半径内有可观察业务节点的企业。
2. 逐家核实企业主体、流通业属性、典型性、本省实际经营和可获得的一手/公开证据。全国知名、可网购或偶发宣传不能单独证明本省布局。
3. 淘汰行业不符、企业不实、本省无布局、研究伦理高风险或无法诊断的候选；再按地区问题强度、取证可达性、公开数据、典型性、新颖性和交付可控性排序。
4. 用学校全称、历史写法、企业全称、品牌名、简称、旧称和关联主体运行查重：

```bash
python3 scripts/check_case_duplicate.py \
  --school "学校官方全称" \
  --enterprise "企业全称|品牌名|常用简称" \
  --title "拟定作品标题"
```

`BLOCK` 时换题；`REVIEW` 时人工核对；`CLEAR_IN_FILE` 仅表示内置名单未命中。只有校级负责人核对官方最新名单、本校登记和企业主体后，才能记录 `CONFIRMED_CLEAR`。

5. 为前三名各给 2–3 个问题方向，但未验证问题只能写成假设。锁定中心命题：

> 在【地区与阶段】，案例企业面临【可量化矛盾】；团队将用【证据与方法】检验【机制】，并设计【行动组合】改善【指标】。

## 阶段 2：调研

不得先定结论再拼证据。将中心命题拆成决策、2–4个研究目标、3–7个问题和可证伪假设；先做案头证据地图，再选择1–2个主方法及必要补充方法。

建立证据台账并保存标题、机构、日期、URL/文件、页码、地区、期间、指标口径、主张ID、限制与人工核验状态。完成预测试后再正式执行访谈、问卷、门店/网点观察和同商圈竞品对标。模拟回答不得作为真人数据。

调研结束时输出“可写结论 / 暂不下结论 / 需补证”。每个核心瓶颈至少由两类独立证据支持，其中至少一类是目标地区一手证据；同时记录反证和替代解释。

## 阶段 3：分析报告

1. 建立问题树：`现象 → 指标 → 直接原因 → 根因 → 经营影响 → 方案杠杆`。检验替代解释、地区机制和企业可控性。
2. 进入 `FRAMEWORK_DRAFT`：使用 11 份国一作品的稳定功能共性，固定一级目录为“目录、概要、引言、案例简介、企业内部分析、企业外部分析、企业经营模式、发展瓶颈、经营优化方案、结论与启示、附录及参考资料”。这是本 Skill 的工作框架，不宣称为官方唯一目录；官方“企业内部及外部分析”由第 5—7 章共同满足。
3. 固定五个核心经营维度的唯一主落点：`5.1 企业战略`、`5.2 运营管理`、`5.3 财务状况`、`6.3 市场竞争`、`7.1 商业模式`。企业内部分析只保留这三个二级标题，资源组织纳入战略，产品客户、采购供应和履约库存纳入运营；没有公开财务时使用可核验代理指标并披露局限，绝不虚构报表或数值。
4. 使用 [report-framework-approval-template.md](assets/report-framework-approval-template.md) 输出到三级标题。概要固定两个二级标题：`2.1 研究对象与核心问题`、`2.2 主要结论与方案方向`，各用一个三级标题凝练展开。引言使用正式书面标题 `3.1 研究背景与选题价值`、`3.2 研究设计与范围`；案例简介只保留理解后文所需的企业业务、地区基础和案例价值。每个三级标题下写2—3行结合项目材料的内容概括和证据边界，缺证时保留待处理状态，不得用通用经验补成企业事实。
5. 发展瓶颈最终保留 2—4 项。第8章每个二级标题直接用通俗语言说清“什么问题造成什么后果”，三级依次回答“问题表现在哪里、为什么会出现、会带来什么影响”。第9章与瓶颈一一对应，每个二级标题直接说清“改善什么结果、采用什么做法”，三级依次回答“具体怎么做、谁来做/何时做/需要什么、怎么判断有效/何时调整”。不得使用“内部挑战、原因树、行动组合、实施路径”等抽象二级标题。
6. 框架中的企业事实、数字、因果、瓶颈和方案依据必须登记为 `[已核验:E###]` 并给出同一证据 ID 的精确定位；证据不足时只写允许的待处理状态。**只输出框架并等待用户确认**，不得提前写长篇正文。
7. 交付确认单前运行：

```bash
python3 scripts/validate_report_framework.py path/to/report-framework-approval.md
```

只有校验为 `PASS` 且用户明确确认版本后才能记录 `FRAMEWORK_APPROVED`；未经确认不写长篇正文。
8. 确认后按一章或2–4个强相关小节分批写作，采用“结论 → 证据 → 对标 → 机制 → 决策含义 → 边界”。五个核心经营维度必须在正文形成实质判断，不得只在标题或清单中出现。
9. 只使用能回答明确问题的方法，不堆砌 PESTEL、SWOT、五力或画布。方法输出不是证据。
10. 每项方案明确根因、目标对象、流程动作、责任主体、0–3个月试点、3–12个月推广、资源/预算、KPI、验证、风险、触发器和回滚。
11. 所有批次确认后组装全文，完成证据、因果、地区性、跨章、匿名和原创复核，再进入评分。

## 阶段 4：评分复核

只评分唯一且完整可读的报告版本。标记 `SCORABLE / PROVISIONAL / UNSCORABLE`、`REPORT_ONLY / PARTIALLY_VERIFIED / EVIDENCE_VERIFIED` 和校准状态；只有提纲、截图或不可读文件时不输出60分数字。

先检查资格、匿名与格式，再按官方五维评分：分析框架20、分析对象10、分析视角10、分析方法10、分析结论10。为每项记录报告定位、`R/V/I/M`证据状态、支持、反证、上限、工作分、合理区间与置信度。双遍复核口径、因果、方法空转、方案泛化和引用可复核性。

国一成熟度只做定性诊断，不另行加分。评分属于辅导估计，不预测奖项、名次或晋级概率。

## 阶段 5：20页PPT大纲与制作

官方要求为PPT不少于20页；本 skill 的初版工作标准是**恰好20页**。

1. 只接受已确认合并报告或用户上传的完整可读报告。记录报告版本、范围和哈希，进入 `PPT_SOURCE_LOCKED`。
2. 建立“报告主张 → 报告定位/证据ID → PPT页”映射。不得新增报告中不存在的数字、因果、访谈或方案收益。
3. 生成恰好20页 `PPT_OUTLINE_DRAFT`。每页包含结论式标题、页面任务、主张/证据、报告定位、建议视觉、口播任务和秒数；不用纯目录、纯过渡或纯致谢页消耗页面。
4. 填写JSON并运行：

```bash
python3 scripts/validate_ppt_outline.py path/to/ppt-outline.json
```

5. 初次只交付大纲、来源映射、缺口和待决策项。用户明确确认某版本后，记录 `APPROVED`、确认版本与时间，再运行 `--for-production`。
6. 通过后才读取 [frontend-slides-integration.md](references/frontend-slides-integration.md) 并调用 `$frontend-slides`；先给3个真实封面预览，用户选定后制作固定1920×1080、恰好20页的单文件HTML。可编辑PPTX需另用演示文稿技能重建。

## 阶段 6：10分钟讲稿

讲稿只能建立在已确认20页PPT与锁定报告上。

1. 锁定PPT/报告版本、20页顺序、讲述人数和匿名要求。页序、数字或结论变化后重写受影响页并重新彩排。
2. 每位讲述人朗读同一60秒样稿三次，取中位数作为口播单位/分钟；未校准时按230单位/分钟生成 `RATE_UNCALIBRATED` 初稿，不能宣称已通过时间门。
3. 同时交付20页施工表与 `[P01]…[P20]` 连续稿。每页写必须讲、关键证据、决策含义、过渡、讲述人、秒数、来源、舞台动作和完整应急删减句。
4. 每页默认只说1–2个锚点数字，不朗读目录、表号、脚注或整表。方法页说限制，问题页区分症状与根因，方案页说责任、KPI和失败条件。
5. 默认口播预算554秒，预留46秒现场缓冲。开场30秒内给出地区矛盾与判断，结尾回答研究问题；多人交接不超过3次。
6. 初稿运行 `scripts/validate_ten_minute_script.py`。团队实质性改写并完成至少三轮真人彩排；最后三轮均≤600秒且中位数525–570秒，再运行 `--for-final`，通过后才记录 `SCRIPT_REHEARSED`。

只有旧讲稿而无对应PPT/报告时，状态降级为 `TIMING_STYLE_ONLY`：只审语言、结构、数字密度和粗略时长，不核验事实，也不保证10分钟内完成。

## 可选：5分钟答辩与最终交付

生成至少40题，覆盖选题地区性、数据样本、方法、五大经营维度、根因、方案、成本、创新、风险和AI使用。答案采用“直接回答 → 最强证据 → 决策含义 → 边界/备选”，常规控制25–40秒。

交付前运行全项目预检，并人工检查PDF、PPT、视频、文件名、文档属性、图片水印、附件隐私、引用、原创过程和备份。自动脚本只能检查结构与明显泄露，不能证明事实真实或原创合规。

## 输出契约

每次交付末尾列出：

1. 当前阶段、输入版本和阶段门状态；
2. 已确认事实及来源；
3. 待调研、待核验、团队判断、反证与局限；
4. 本轮团队必须亲自完成或确认的工作；
5. 下一步、负责人、截止时间和完成标准。

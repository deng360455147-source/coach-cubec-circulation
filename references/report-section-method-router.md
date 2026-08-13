# 报告章节方法与外部 Skill 路由

本文件记录截至 2026-08-12 对 GitHub、skills.sh/ClawHub 与本地可用 skills 的筛选。主技能不直接安装第三方包，而是吸收经审查的最小方法；若本地对应 skill 可用，可按章节调用。所有方法都必须服从赛事证据规则与框架确认门。

## 一、章节路由

| 报告任务 | 首选方法/可用 skill | 采用内容 | 赛事化限制 |
|---|---|---|---|
| B01研究框架、年报画像与双模型 | 本地 `data-analytics:jupyter-notebooks`、`validate-data`、`visualize-data` + 本Skill双模型协议 | 用年报建立连续年度数据底稿；生成研究框架图；从市场份额、协同效应、文化溢价DID、DEA‑Tobit中选两种READY方法并输出程序化图表 | 恰好两种且必须通过数据/识别门；年报不能自动提供市场分母、反事实、处理/对照面板或足够DMU；不足时阻断，不模拟 |
| 总体框架、章节施工说明 | ByteDance DeerFlow `consulting-analysis` 的两阶段方法 | 先定义问题/范围，再为每章写目标、逻辑、假设、数据、来源、检索词和视觉计划 | 在两阶段之间加入用户确认门；不强制每小节 200 字或每小节一图 |
| 案例画像与经营全景 | 本地 `data-analytics:product-business-analysis` | 从决策出发，建立少量可检验假设，分解驱动因素，给出决策含义 | 不写企业百科；集团事实不能代替目标地区事实 |
| 外部环境与地区竞争 | 本地 `competitive-analysis` / Pawel Huryn `competitor-analysis`；按需 PESTEL、五力 | 建立本地直接竞品/替代者集合、可比维度、证据来源和差距 | 同地区、同客群、同期间、同口径；PESTEL/五力不叠加堆砌 |
| 战略、商业模式与价值链 | 价值链、VRIO、商业模式画布的最小问题法 | 解释优势如何产生、价值在哪里创造/泄漏、哪些资源可持续 | 不因有模型就画图；无结果指标或竞品对标时降级为假设 |
| 运营与指标异常 | 本地 `data-analytics:metric-diagnostics` | 先定义指标和口径，再复现差距，按地区/门店/品类/渠道等拆解驱动，区分已验证/可能/未解决 | 不把问卷态度替代交易事实；没有基线时把 KPI 设为待测试 |
| 财务状况与方案测算 | Alireza Rezvani `financial-analyst` 的趋势—比率—驱动—情景法 | 统一口径后分析盈利、效率、现金与承受力；零售按需看同店、毛利、周转、损耗、坪效、客单等；方案做情景和敏感性 | 不默认做 DCF/估值；不套通用阈值；非上市企业不得伪造报表 |
| 瓶颈与根因 | 指标诊断 + 本技能“症状—差距—直接原因—结构根因—反证—可控性” | 先证明差距，再解释机制和替代解释，按影响×可控性排序 | 不采用以软件事故为中心的通用 root-cause skills；5 Why 不能替代证据 |
| 方案、实施与评价 | 本地 `data-analytics:design-kpis` + 逻辑模型/试点 | 1–3 个主 KPI、驱动指标、护栏、明确定义、目标范围、采集频率和责任 | 无基线不承诺精确提升；必须写停止条件、风险和回滚 |
| 章节成稿与全局报告 | 本地 `data-analytics:build-report` | 结论优先；每节使用主张—证据—解释—含义；视觉邻近解释；来源与局限清楚 | 输出须按用户确认后的章节批次进行，而非自动整稿 |

## 二、已采用来源

### ByteDance / DeerFlow / consulting-analysis

- 来源：`https://github.com/bytedance/deer-flow/tree/main/skills/public/consulting-analysis`
- 许可：MIT。
- 采用：框架阶段与成稿阶段分离；章节级目标、分析逻辑、假设、数据需求优先级和视觉规划；报告主张须可追溯。
- 改造：加入 `FRAMEWORK_APPROVED`；默认分章节交付；删除固定字数、图表数量和通用咨询语气要求。

### OpenAI / role-specific-plugins / data-analytics

- 来源：`https://github.com/openai/role-specific-plugins/tree/main/data-analytics/skills`
- 许可：仓库标注 MIT。
- 采用：`product-business-analysis`、`metric-diagnostics`、`design-kpis`、`build-report` 的决策导向、指标定义、驱动分解、主/驱动/护栏 KPI 和结论优先报告结构。
- 改造：将产品/SaaS 语境替换为流通企业、地区经营、门店/网点/仓配与赛事评分语境。

### Pawel Huryn / pm-skills / competitor-analysis

- 来源：`https://github.com/phuryn/pm-skills/tree/main/pm-market-research/skills/competitor-analysis`
- 许可：MIT。
- 采用：竞品集合、可比维度、证据来源、差距和机会。
- 改造：以本地直接竞品、替代业态和经营指标替代软件功能/价格表；禁止无来源市场份额。

### Alireza Rezvani / claude-skills / financial-analyst

- 来源：`https://github.com/alirezarezvani/claude-skills/tree/main/finance/skills/financial-analyst`
- 许可：MIT。
- 采用：先验证数据范围和口径，再做趋势、比率、驱动、同口径比较和情景；吸收零售行业指标提示。
- 改造：只保留经营诊断与方案测量，不把投资估值、DCF、资本市场结论作为默认任务。

## 三、ClawHub 与其他候选的取舍

| 候选 | 结论 | 原因 |
|---|---|---|
| ClawHub [`data-analysis-reporting`](https://clawhub.ai/gitcanadabrett/skills/data-analysis-reporting) | 不直接安装，吸收“先做数据质量与分析计划、标注置信度” | 与 OpenAI 数据分析技能重叠，且赛事仍需专门的地区性与证据台账 |
| ClawHub [`competitive-analysis`](https://clawhub.ai/jk-0001/skills/competitive-analysis) | 不采用 | 偏独立开发者/SaaS 场景，竞争维度与流通企业不匹配 |
| 通用 `business-case-development` | 不采用 | 重点是投资/审批商业论证，不是调研后的企业经营案例诊断 |
| 通用 `root-cause-analysis` | 不采用 | 高安装候选多面向软件事故或流程故障，难以覆盖地区经营与混合证据 |
| 通用 KPI dashboard skills | 不直接采用 | 侧重仪表盘呈现；本赛道更需要方案逻辑、指标定义、试点和回滚 |
| 财务估值/DCF 类 skills | 不作为默认 | 竞赛要求财务状况与建议可行性，不等于估值；易造成无数据精确化 |

## 四、调用原则

1. 一个章节先定义问题，再选择最多 1–2 个主方法；不得把多个框架作为“创新”堆叠。
   B01按用户要求固定选择两种实证方法，但仍须先通过 [annual-report-empirical-methods.md](annual-report-empirical-methods.md) 的可行性门槛；不足两种时停止补数，不执行空模型。
2. 外部 skill 只能提供流程和检查项，不能成为事实来源；数字、判断和引用仍回到证据台账。
3. 本地 skill 不可用时，按本文件的最小方法执行，不影响主流程。
4. 引入新第三方 skill 前，检查完整 `SKILL.md`、脚本、依赖、权限、凭据、许可和近期维护；禁止盲装。
5. 方法名称可以写入报告，skill 名、仓库名和代理工作流不写入参赛正文。

# 外部方法来源、筛选与许可

调研与报告阶段只将可审计的方法论改写为赛事专用流程，不直接执行第三方包。PPT 制作阶段按用户指定安装并调用已审计的 `frontend-slides`；安装版本、能力边界和外部写入限制见 [frontend-slides-integration.md](frontend-slides-integration.md)。

调研阶段采用来源记录如下；报告阶段的 GitHub/ClawHub 筛选、章节路由和未采用候选见 [report-section-method-router.md](report-section-method-router.md)。

## 已采用来源

### NKZ55 / research-planner

- 来源：`https://github.com/NKZ55/research-planner`
- ClawHub：`https://clawhub.ai/nkz55/skills/research-planner`
- 许可：MIT（ClawHub 标注 MIT-0；仓库 LICENSE 为 MIT 文本）
- 采用：从决策澄清到方法选择、研究计划、招募筛选、知情说明、访谈、问卷、现场研究材料和物流清单的阶段模型。
- 改造：删除软件可用性研究专属内容；增加流通行业、本地地区性、门店/网点、竞品和赛事评分映射。

### Corey Haines / marketingskills / customer-research

- 来源：`https://github.com/coreyhaines31/marketingskills/tree/main/skills/customer-research`
- 许可：MIT，Copyright (c) 2025 Corey Haines。
- 采用：已有材料/公开来源双模式、JTBD/VOC 字段、主题聚类、置信度、样本偏差和反证意识。
- 改造：将 SaaS/G2/Reddit 导向改为中国流通业可用的地图、电商、点评和社交公开来源；禁止把评论当代表性总体。

### Pawel Huryn / pm-skills

- 来源：`https://github.com/phuryn/pm-skills`
- 文件：`pm-market-research/skills/competitor-analysis/SKILL.md`、`pm-product-discovery/skills/interview-script/SKILL.md`
- 许可：MIT，Copyright (c) 2026 Pawel Huryn。
- 采用：竞品集合、比较维度、差异机会；访谈聚焦过去真实行为、开放式追问、不诱导、不推销。
- 改造：以本地直接竞品和行业经营指标替代通用软件功能/定价矩阵；禁止无来源估计市场份额。

### K-Dense-AI / scientific-agent-skills / experimental-design

- 来源：`https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/experimental-design`
- 许可：MIT。
- 采用：随机化、重复、分层/区组、避免伪重复的质量提醒。
- 改造：只用于问卷分发、观察时段和方案试点的设计原则，不引入该技能的 Python/DOE 依赖。

### Zara Zhang / frontend-slides

- 来源：`https://github.com/zarazhangrui/frontend-slides`
- 安装路径：`~/.codex/skills/frontend-slides`
- 固定提交：`9906a34d640d2111f724544cbc50f7f130569ae1`
- 许可：MIT，Copyright (c) 2025 Zara Zhang。
- 采用：20页大纲确认后的三套可视化风格预览、固定1920×1080单文件HTML演示、浏览器交互与可选PDF导出。
- 边界：不把它描述为原生 PPTX 生成器；不自动运行会上传内容的 Vercel 部署脚本；不直接运行会安装未固定依赖并启动本地文件服务的原仓库 PDF 导出脚本，PDF 改走受控 PDF 技能。

## 未采用/未直接安装

- Firecrawl market research：安装量高但依赖外部抓取服务，不是完成赛事调研的必要条件。
- 通用 ClawHub competitor-research：方法与上述来源重叠，并建议长期写入用户主目录；本技能改用项目内状态文件。
- UX research engine：方法选择矩阵可用，但与 research-planner 重叠，且样本量固定建议不适合直接套用学生便利样本。

## 更新准则

再次引入第三方方法时，先检查：原始 `SKILL.md`、所有脚本、依赖、工具权限、外部写入、凭据、许可证、最近更新和安全审计。只复制任务所需的最小方法，并保留来源与许可；不得直接运行未经审查的安装脚本。

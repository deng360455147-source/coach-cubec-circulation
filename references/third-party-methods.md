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

### Tw93 / Kami

- 来源：`https://github.com/tw93/Kami`
- 嵌入路径：`integrations/kami/`
- 固定版本：`1.12.0`
- 固定提交：`8bf6f46f74b5b640fa5612736a5cd24c724b7eca`
- 许可：MIT，Copyright (c) 2026 Tw93；嵌入目录保留上游 `LICENSE`。
- 采用：编辑式长文层级、墨蓝单一强调、克制图解、图表/页面密度检查、反AI套话与视觉复核原则；保留上游轻量 Skill 子目录中的模板、参考、脚本和资产。
- Word适配：Kami 原生输出 HTML/PDF，不是 DOCX 生成器。主 Skill 仅将它作为视觉与图解参考，DOCX 仍由 `$documents:documents` 生成、渲染和检查；量化图表由 `$data-analytics:validate-data` 与 `$data-analytics:visualize-data` 负责。
- 更新边界：赛事项目执行中保持固定版本，不运行自动更新覆盖；只有维护本 Skill 时才重新审计上游提交、许可证、脚本和资产后升级。

### 0xE1337 / thesis-figure-skill

- 来源：`https://github.com/0xE1337/thesis-figure-skill`
- 嵌入路径：`integrations/thesis-figure-skill/`
- 安装快照：2026-08-13，来自上游 `main` 的 `skills/thesis-figure-skill/`；原安装器没有记录提交号，`VERSION`保存来源、日期和 `SKILL.md` SHA-256，不虚构固定提交。
- 许可：MIT，Copyright (c) 2025；嵌入目录保留上游 `LICENSE`。
- 采用：TikZ/draw.io学术图解、布局骨架、编译验证、重叠检测和视觉复核，用于研究框架、价值链、流程、机制、泳道和路线图。
- 边界：每批调用该Skill完成关键学术图形的构图复核，只有适配时才实际重绘；量化统计图仍由数据验证与可视化链路生成；不把未核验文字自动变成确定性箭头；不修改年报/现场证据的事实内容；图内普通文字须在Word最终宽度不小于14pt，关键文字为16pt。
- 运行边界：实际调用前完整读取嵌入 `SKILL.md` 并遵守其编译和多视角审查要求；上游自动pip安装在本主Skill中改为先报告、经用户确认后再执行，MacTeX/draw.io/Graphviz/Homebrew或管理员权限不得自动安装；正文不得出现TikZ、draw.io、Skill、脚本路径或审查状态。

### coleam00 / excalidraw-diagram-skill

- 来源：`https://github.com/coleam00/excalidraw-diagram-skill`
- 审计提交：`8646fcc9f74f38539c6cdb4c969723336a96ddcd`，审计日期2026-08-13。
- 使用方式：外部安装，Skill frontmatter名为 `excalidraw-diagram`；本项目只保存 `integrations/excalidraw-diagram-adapter/` 和报告专用适配规则，不复制上游代码。
- 采用：把概念映射为分流、汇聚、时间轴、层级、反馈和前后对照等视觉结构；保存可编辑 `.excalidraw`；通过Playwright渲染后逐轮查看和修复截字、重叠、连线与留白。
- 报告覆盖：图片内不得嵌入题注，图前必须有正文引导，图内普通文字按最终Word尺寸不小于14pt，关键文字为16pt；统计图仍走数据验证与可复现程序。
- imagegen协作：只辅助适配的无文字位图或场景示意，不生成精确标签、数据图、地图、Logo、企业实拍或调研证据；准确文字在Excalidraw或Word添加。
- 依赖与隐私：上游渲染依赖Python 3.11+、Playwright和Chromium，HTML模板会从 `esm.sh` 加载Excalidraw模块；不得把未获授权的敏感内容送入该链路。安装新浏览器或系统依赖前须取得设备所有者确认。
- 许可边界：审计提交没有LICENSE文件。没有明确再分发授权，所以本公开仓库不原样嵌入上游源文件；若上游补充许可证，重新审计后再决定是否内嵌。

## 未采用/未直接安装

- Firecrawl market research：安装量高但依赖外部抓取服务，不是完成赛事调研的必要条件。
- 通用 ClawHub competitor-research：方法与上述来源重叠，并建议长期写入用户主目录；本技能改用项目内状态文件。
- UX research engine：方法选择矩阵可用，但与 research-planner 重叠，且样本量固定建议不适合直接套用学生便利样本。

## 更新准则

再次引入第三方方法时，先检查：原始 `SKILL.md`、所有脚本、依赖、工具权限、外部写入、凭据、许可证、最近更新和安全审计。只复制任务所需的最小方法，并保留来源与许可；不得直接运行未经审查的安装脚本。

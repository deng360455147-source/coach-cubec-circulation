# Canva可编辑母版与Word配图工作流

本协议用于用户要求Word中的图“可编辑”时。必须先区分Word原生可编辑和外部母版可编辑，不能把插入Word的PNG、JPG或Canva导出图描述为Word内部的可编辑形状。

## 1. 可编辑性的真实含义

| 模式 | Word中的状态 | 实际编辑位置 | 适用内容 |
|---|---|---|---|
| `WORD_NATIVE` | 可直接编辑 | Word表格、图表或形状 | 数据表、简单图表、少量流程形状 |
| `CANVA_MASTER` | Word中是渲染版 | 原Canva设计 | 已存在Canva母版的版式图、信息图 |
| `EXCALIDRAW_MASTER` | Word中是SVG/渲染版 | `.excalidraw`源文件 | 研究框架、流程、机制、泳道 |
| `THESIS_SOURCE` | Word中是SVG/PDF/渲染版 | `.tex`或`.drawio`源文件 | 公式、高密度学术机制图 |
| `REPRODUCIBLE_DATA_CHART` | Word中是图表或渲染版 | Excel、Notebook或绘图源文件 | 折线、柱状、热力、组合图 |
| `ORIGINAL_EVIDENCE_RASTER` | 不可编辑 | 原始证据文件 | 年报截图、现场照片、竞品页面 |

若用户要求“在Word里直接改数据和形状”，优先使用Word原生表格、图表或形状。Canva不能把Word中的扁平图片自动拆成独立文字、线条和形状；Canva母版可编辑不等于Word对象可编辑。

## 2. Canva启动条件

使用 `$canva:canva-edit-design` 前必须取得已有Canva设计链接或以 `D` 开头的设计ID。该能力只编辑既有设计，不能创建新页面、添加新文字框、更换字体家族、重组元素或把扁平图片向量化。缺少设计ID时记录 `AWAITING_DESIGN_ID`，继续准备其他可编辑源文件，但不得声称Canva版本已经完成。

## 3. 事务流程

1. 从完整链接、短链接或原始ID解析 `design_id`。
2. 调用 `Canva:start-editing-transaction`，保存 `transaction_id` 和完整 `pages` 数组，并向用户展示返回的缩略图。
3. 检查目标页是否为响应式页面。响应式页面只允许更新标题、替换文字或填充、删除元素和查找替换，不能格式化、移动、缩放或插入填充。
4. 根据现有 `element_id` 批量执行允许的操作。可能匹配多处的查找替换、删除或大范围调整必须先确认范围。
5. 展示修改后的缩略图，列明文字、媒体、位置和尺寸变化，并询问用户是否保存。
6. 只有用户明确同意后才调用 `Canva:commit-editing-transaction`。用户拒绝或不再继续时调用取消事务，不能留下未说明的草稿。
7. 提交成功后记录Canva链接、设计ID、页面索引、元素ID和提交结果，再更新Word中的渲染版。

## 4. Canva能力边界

可以修改既有文字内容及字号、粗细、样式、颜色、对齐和行距；可以替换、插入或删除媒体；可以移动、缩放既有元素并更新标题。不能改变字体家族，不能新建文字框、页面或渐变背景，不能改变动画、透明度、分组和形状样式。

因此，不得把Canva作为统计数据的计算工具、OCR拆图工具或Word对象转换器。需要新增结构或文字框时，先在Canva编辑器人工建立母版，或改用Excalidraw、draw.io、Word原生形状和可复现数据图。

## 5. Word落版与源文件交付

每张图同时交付Word渲染版和可编辑母版。Word中的替代文本写明图题和数据范围，但不暴露本地路径或内部状态。内部登记表记录母版类型、位置、Canva设计ID、页面、元素、数据源和重建步骤。

Canva或外部源文件修改后，必须重新导出图、替换Word中的旧版本、更新自动题注和目录、渲染全部页面并重新检查字号、来源、分页和图文一致性。不得只更新母版而保留过期Word图。

执行时复制 [editable-figure-register-template.json](../assets/editable-figure-register-template.json)，每批运行 `scripts/validate_editable_figure_register.py`。用户明确要求Canva时，将 `canva_requested_for_this_document` 设为 `true`；生产校验要求至少有一张实际提交的Canva母版。若用户尚未提供设计ID，校验会如实失败并提示缺口。

# Excalidraw Diagram 外部集成说明

主 Skill 通过外部 `$excalidraw-diagram` 调用 `coleam00/excalidraw-diagram-skill`。本目录只保存报告适配说明，不复制上游源文件。

- 上游：`https://github.com/coleam00/excalidraw-diagram-skill`
- 审计提交：`8646fcc9f74f38539c6cdb4c969723336a96ddcd`
- 审计日期：2026-08-13
- 本地安装名：`excalidraw-diagram-skill`；Skill frontmatter 名：`excalidraw-diagram`
- 上游依赖：Python 3.11+、Playwright和Chromium；渲染模板会从 `esm.sh` 加载Excalidraw模块，因此不得用于未获授权的敏感材料。

本机审计时，上游未固定的 `esm.sh` 导入解析到0.18.1后出现依赖404；本地安装将导入固定为 `@excalidraw/excalidraw@0.18.0` 后通过渲染冒烟测试。受代理环境限制的设备还需让浏览器显式使用可用代理。以上是本机兼容处理，不是本仓库再分发的上游补丁；其他设备应先运行最小渲染测试，再决定是否需要同类处理。

截至审计提交，上游仓库没有提供LICENSE文件。因而本公开项目不把其代码、模板或参考文件原样嵌入和再分发。使用者需从上游自行安装并遵守其当前许可；若上游未来补充明确许可证，重新审计后再决定是否内嵌。

本项目自己的路由、色板、Word约束和验收规则见：

- `references/excalidraw-imagegen-integration.md`
- `assets/excalidraw-report-palette.md`
- `assets/report-word-format-profile.json`
- `assets/word-visual-manifest-template.json`

# CEO 传记撰写项目

2026-10-16已封装为独立技能 `ceo-biography`，当前版本1.2.1。当前执行入口是 [SKILL.md](../../../.github/skills/ceo-biography/SKILL.md)，以重要事件组织正文，研究后归纳人物中心，定性分析优先。5,000–8,000中文字为通常参考范围，篇幅以材料和文章质量为准。资本配置为每篇传记的必查项，是否独立成章由材料决定。

调用示例：

```text
请使用 $ceo-biography，为林德现任CEO撰写一篇传记，研究截至今天。
```

在网页版GPT聊天中，复制[完整启动提示词](../../../.github/skills/ceo-biography/references/agent-task-prompt.md)的整个文本块，替换人物等信息后发送。模板可以单独使用；在本地调用技能时，也会先读取这份完整模板。

技能目录自带完整启动提示词、[写作规范](../../../.github/skills/ceo-biography/references/writing-standard.md)、[正文模板](../../../.github/skills/ceo-biography/assets/ceo-biography.md)和[书籍方法笔记](../../../.github/skills/ceo-biography/references/the-outsiders-method.md)，可以整体复制使用，不依赖原书PDF或本工作区的公司资料。

今后的执行规则以技能目录为准。本目录的[原写作规范](ceo-biography-standard.md)、[原任务提示词](agent-task-prompt.md)及 `templates/ceo-biography.md` 保留为封装前v2.2资料。[书籍蒸馏研究稿](the-outsiders-source-note.md)保留原研究版本、出处与页码；技能中的方法笔记为随包保存的适配版本。修改执行规则时更新技能，不再维护两套执行入口。

[兰巴简传样稿](../../companies/US/LIN-linde/management/sanjiv-lamba-biography-2026-10-15.md)及[林德试写记录](linde-pilot-review-2026-10-15.md)保留为实际写作记录。[早期试写记录](pilot-review-2026-10-15.md)也予保留。现有验证包含作者试写与自审，未进行独立Agent复现或用户可读性验收；技能结构检查不能代替具体文章的质量审阅。

原书、逐页OCR和来源清单位于 `sources/books/the-outsiders/`，不随技能打包，也不纳入Git。

2026-10-16已用用户提供的1.2.0插件包内技能替换底层技能；五个技能文件与包内内容一致，本地 `agents/openai.yaml` 启动配置保留。原始插件包、替换前完整技能备份和哈希清单位于 `sources/skills/ceo-biography/releases/1.2.0-1ecd19b90d2d/`，均保持Git忽略；这里只更新底层skill，不另行注册或发布插件。

2026-10-16按用户要求在1.2.0基础上更新为1.2.1：将资本配置明确设为必查项，是否独立成章仍由材料决定；同步更新技能入口、完整启动提示词、写作规范和正文模板。上段所述与插件包内容一致，指最初导入时的状态。

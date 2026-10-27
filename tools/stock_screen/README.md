# 股票初筛执行与验收

本目录保留旧版 `screen-v2` 的复现与验收工具。自 2026-10-23 起，新研究默认使用 `.github/skills/stock-initial-screen/SKILL.md` 中的 v4.4 工作流；下述命令仅用于旧报告复现或审计，不与 v4.4 混算。工具不内置饮料公司分数；业务名单、判断和假设保存在独立的curated配置，外部原件保存在sources。

```bash
.venv/bin/python tools/stock_screen/run_v2.py data/curated/screens/<run-id>/run.json
```

流程：`prepare_v2.py`规范化币种、余额和现金流；`build_v2.py`调用`engine_v2.py`计算资本回报/现金转化/毛利/同行/资本配置/目标配对/周期；`audit_v2.py`检查23家公司三维结果、证据一致性和原价/EPS时点；`render_v2.py`把同一结果写成完整Markdown及离线HTML。需要取数时可用`acquire_guidance.py`收集官方年度业绩附件，逐年首次目标和实际值须人工核对，不由抓取脚本猜测。

`run.json`的目录、同行、边界、带依据的调整可追溯；`assessments.json`保存判断事实与反证；`guidance-records.json`存首次指引/同口径实际及来源。运行从缓存重建，不重复网络抓取，不改原始文件。

完整性不等于没有N/A：至少4/5项形成每维；未评分项保留`evidence_limited/not_applicable`与解释。`pending_work`不通过验收；`complete_limited`只表有限覆盖流程完成。上界情景和短历史始终暂定；优先研究还须通过所有缺项取1的压力检查。详情见`.github/skills/stock-initial-screen/references/screen-v2.md`。

HTML完全内嵌，无需服务器。若配置`legacy_html_alias`，只有通过验收后才将旧书签转向新版；旧HTML按内容哈希留存，不覆盖同名不同内容。

## 旧版诊断

`aggregate_scores.py` 校验及汇总输入分数；成功退出并不代表资料核验及评分工作完成。本工具分别检查逐项覆盖、汇总一致性、证据账本分数及未决分类，不验证引用内容或判断质量。

```bash
.venv/bin/python tools/stock_screen/audit_run.py data/derived/screens/<run-id>
.venv/bin/python tools/stock_screen/audit_run.py data/derived/screens/<run-id> --require-complete
.venv/bin/python -m unittest discover -s tools/stock_screen/tests
```

输出写入指定派生目录的 `completion-audit.json`。普通模式允许生成明确标注未完成的诊断报告；严格模式有未决分类即退出 2。`structure_ready` 仅表示必要结构检查通过，不能代替原文、计算及判断复核。已明确触发硬淘汰的公司不要求补齐全部指标。

同一`audit_run.py`入口识别v2并转入v2验收；旧版仍保持原有诊断行为。测试覆盖门槛穷举、缺失/暂定资格、异常资本、Decimal端点、指引口径与验收一致性。

# Fundamentals: Statements, Derived Metrics and Chapter Writing

## 1. Reported statements first

Extract the latest audited consolidated balance sheet, income statement, and cash-flow statement in reported row order before interpreting them. Preserve currency, units, signs, period type, consolidated versus parent/NCI scope, continuing versus discontinued operations, and reported/restated/reclassified status.

Keep this complete extraction in the base workbook or source layer. A report chapter
selects material accounts and complete relevant periods rather than reproducing
all rows. Use sections 1–5 for extraction, mapping and calculation; use
[section 6](#6-资产负债表章节分析与写作) to plan, draft or review the balance-sheet
chapter. This skill owns the research narrative and chapter completion criteria;
the financial-statement and derived-analysis skills supply calculation tools.
Reuse a validated existing base rather than reconstructing it for each chapter.

Use a normalized JSON input compatible with the Workspace calculator. Object values should carry source metadata:

```json
{
  "period_order": ["FY2021", "FY2022"],
  "periods": {
    "FY2021": {
      "values": {
        "revenue": {"value": 100.0, "source_label": "Revenue", "statement": "income", "source": "S001", "page": "72", "status": "reported"}
      }
    }
  }
}
```

Run, when present:

```bash
.venv/bin/python .github/skills/financial-statement-analysis/scripts/calculate_metrics.py \
  data/curated/companies/<market>/<ticker>-<slug>/<input>.json \
  --format markdown --include-missing --strict \
  --output data/curated/companies/<market>/<ticker>-<slug>/metrics.md
```

The exact interpreter and path may differ on a colleague's machine; discover the repository root rather than hardcoding it.

## 2. Mapping ledger

Map each canonical field to exact source rows, transformation, economic scope, confidence, and comparability note. Use subtotal equations and footnotes, not label similarity alone. Keep issuer APMs such as adjusted EBITDA or company FCF separate from calculated EBITDA and CFO minus capex.

## 3. Required reconciliation checks

- Assets equal liabilities plus equity within disclosed rounding.
- Cash-flow subtotals bridge to change in cash, including FX and scope effects.
- Consolidated profit reconciles to parent and NCI attribution where disclosed.
- Restated comparatives take precedence in the current analytical series; original values remain documented.
- Blank, not disclosed, zero, and not applicable remain distinct.
- Debt excluding leases is matched with a pre-lease denominator; debt including leases uses a compatible after-lease denominator.
- ROE uses ownership-consistent income and equity.

## 4. Derived metrics

Present visible tables before narrative, grouped by profitability/returns, liquidity/leverage, working capital, and cash/capital intensity. Select metrics by route; do not fill a dashboard mechanically.

```text
revenue growth = current revenue / prior revenue - 1
operating margin = operating profit / revenue
calculated EBITDA = operating profit + D&A
net debt ex leases = short debt + long debt - cash - eligible liquid investments
cash after capex = CFO - PPE/intangible capex
CFO margin = CFO / revenue
CFO / net income = CFO / matching-scope net income
capex intensity = capex / revenue
DSO = average trade receivables / revenue * 365
DIO = average inventory / cost of revenue * 365
DPO = average trade payables / cost of revenue * 365
CCC = DSO + DIO - DPO
```

Only calculate DSO/DIO/DPO/CCC when balances are economically clean and opening stocks are available. Use `unavailable` or `not_meaningful` with the reason when denominators or source rows do not support a defensible metric.

### 4.1. 经营IC与经营ROIC的统一口径

分析师于2026-10-16确认并进一步澄清，后续研究统一按资产的经济性质使用以下资产端定义，名称为**经营IC**。某家公司列示的几个报表科目只是映射，不是扣除范围的上限：

```text
经营IC = 总资产－投资类资产－现金类资产
平均经营IC =（期初经营IC＋期末经营IC）÷2
NOPAT = 营业利润－当期实际所得税费用
经营ROIC = NOPAT÷平均经营IC
经营IC周转率 = 营业收入÷平均经营IC
经营ROIC = NOPAT利润率×经营IC周转率
```

- 本口径衡量资产端的经营资本占用，**不再扣除经营性负债，也不改用“有息债务＋权益”的资金来源法**。资产剔除思路相近，不代表这两类IC数值相等；对相同的投资扣除集合，两者差额为未计入有息债务的负债。
- 投资类资产包括权益法投资、其他股权投资、债券、基金、短期金融投资及其他可辨认投资。检查投资、税项、保险、其他流动/非流动资产及待售处置组附注，不能因投资列在“其他资产”或受到使用限制就漏扣。借款、处置应收款或投资预付款等按经济性质及可核对的期末余额判断，不能将历史交易金额直接当作当前投资余额。
- 现金类资产包括现金及现金等价物，以及可识别的受限现金、待售业务现金。不额外假定最低经营现金或“多余现金”。本节按资产性质剔除的范围，与净现金分析中能够用于抵债的资金范围分别判断。
- 保留逐期、逐科目的扣除映射及其来源，并处理嵌套与重分类：证券附注总额可能包含主表现金、有价证券和保险子公司投资，受限现金总额可能已包含待售现金，不能重复扣除；重述后的比较值已还原的资产不再额外加回。未披露金额不能当成零，无法连续识别的余额注明缺口及其影响，不宣称已得到精确的纯经营资产。
- 商标、商誉、固定资产、已包含于总资产的使用权资产及税务押金等非投资、非现金资产，按本约定保留。不把“总资产减投资及现金”自行扩展为剔除全部非经营资产；经营套保和养老金净资产也不因属于金融安排而自动视为投资。重大重分类、减值与口径变化仍须解释。
- 权益法投资的资本与收益单独分析；其股权收益不加进本口径的营业利润分子。实际集团所得税仍可能含投资及特殊税项，说明NOPAT是报表分析口径，不称为精确分摊经营税负后的利润。
- 年度使用相应期初期末平均经营IC；近期优先以TTM利润匹配一年前及当期期末经营IC，不将半年利润直接除以年度资本后与全年ROIC比较。
- 已有底稿、计算器或旧报告若使用其他IC公式，保留旧口径记录，并按本定义重算后再引用。工具内置的资金来源法ROIC不能仅改名为“经营ROIC”。其他资本回报口径只在明确需要时另行定义和标注。
- 展示时列明NOPAT、期末或平均经营IC、经营ROIC及必要的周转率，保持完整历史与近期数据可追溯。若某行业该指标不适用，说明原因，不静默更换公式。

## 5. Driver analysis

For every material change use:

```text
reported fact -> mechanical bridge -> price/volume/mix/perimeter/FX/
working-capital/financing/tax/one-off driver -> persistence assessment
-> investment implication -> monitoring KPI
```

Do not infer a driver from statements alone when notes, filings, or operating evidence do not support it. Label the point as a hypothesis and state what would confirm it.

## 6. 资产负债表章节分析与写作

本规范适用于资产负债表章节、对话中供粘贴到 Word 的正文，以及对应底稿和图表。它规定分析如何形成、证据如何展示，不把某家公司的资产分类或结论固化为模板。公式与输入要求同时遵循 [metric-catalog.md](../../financial-statement-analysis/references/metric-catalog.md) 和 [statement-mapping.md](../../financial-statement-analysis/references/statement-mapping.md)。

### 6.1. 分析目标与资料准备

读者读完应能回答：公司把资本投向了哪里，资金从哪里来，历史上哪些经营和战略变化形成了今天的报表，日常经营占用还是释放资金，以及哪些资产和义务需要重点检验。不要把章节写成科目释义或逐年数据复读。

写作前完成以下准备，不等待用户逐项提醒：

- 恢复现有报告、用户已确认的章节边界和底稿口径。已有完整底稿时直接使用并核对，不因开始撰写章节而重建整本工作簿。
- 以历年正式年报、近期中报或季报及其形成的 Excel 底稿为主线。先读主要科目、附注、重述和管理层解释，再确定分析问题；纪要与官网用于补充经营背景，不取代正式披露。
- 覆盖约定的完整历史区间及已有的近期数据，不任意缩短为三年或只展示最新一年。资产负债表是时点数，近期列用实际期末日期，年度与季度分开展示；同比、较年初变化和相邻季度变化必须标明比较对象。
- 在底稿保留完整报表、来源和映射，在正文只展示决定结构、趋势或风险判断的重点科目。底稿完整不等于正文必须照搬全部科目。
- 先检查收购、处置、合并范围、待售及终止经营分类、汇率、重估和会计政策变化；判断哪些跨期比较真正可比。没有足够证据的调整保留缺口，不估造连续序列。

### 6.2. 章节的行文顺序

普通非金融公司的默认顺序如下；根据商业模式与已完成章节调整，避免重复：

1. **总览与历史来龙去脉。** 开头用一至两段给出核心判断；随后以重点历史数据和若干关键阶段，讲清从过去到当前的资产配置与融资结构如何形成。总览不能只报期初期末总资产，再笼统归因于“收购和战略调整”。
2. **重点科目与重要事件。** 将决定资本占用、融资约束或比较口径的资产、负债和权益联系起来解释。与总览高度相关时连续展开，不为每个科目另设小节。
3. **运营资本与周转效率。** 在本节内完成经营性流动资产、经营性流动负债、净运营资本及必要周转指标的分析；相关性强时无需拆成独立大章节。
4. **资产结构与资本配置。** 用一张带占比标注的金额堆积图呈现长期及最新结构，解释资本投向、会计账面价值及后续回报责任。

若净现金、偿债能力、资本回报或股东回报另有专节，本节仍应交代重大借款、权益和特殊义务的性质及变化，但不重复后续指标全集。银行、保险等公司的资产负债本身构成经营业务，应按行业特性调整顺序和指标，不强套工业企业运营资本及堆积分类。

正文按核心矛盾、结构变化和重要转折组织。完整的十年数据可以由表图承担，文字不需要对应写十段；按阶段叙述只保留会改变理解的转折。每个重要细节须说明其为什么影响本节判断。

### 6.3. 把重大变化解释到位

写作前建立内部事件与科目对照：时间、事件、涉及科目、主要金额、现金发生时点、合并或重分类影响、来源及未解释差额。该对照用于组织因果，不必全部放入正文。

重大事项应让读者沿着以下关系读懂：

> 经营或战略动作 → 受影响的资产、负债及权益 → 现金与非现金变化 → 结构及投资含义。

- **收购：** 区分现金价款、或有对价及其重估、取得控制权与原持股重估、购买价分摊、商标等无形资产和商誉。说明付款与确认费用的时间差；大额尾款可能主要结算既有负债，不能再次全额解释为当期新增资产。
- **处置与再特许经营：** 说明哪些直接经营资产退出，换回多少现金或保留何种权益，是否改变合并范围。资产出售不等于总资产按出售资产账面额等额下降，也不能把业务移出合并范围直接描述为经营萎缩。
- **待售重分类：** 检查原来分散在固定资产、商誉等科目的余额是否转入处置组。不能把重分类造成的下降解释成已经出售、折旧下降或减值；已单列的待售资产不得再加回原科目。
- **减值与投资成效：** 区分经营预期下修、估值参数变化及实际现金流出。或有对价上升可能反映经营目标实现，也增加收购成本；减值反映账面价值调整，不能单凭任一项判断整笔投资成功或失败。没有可归属的利润与投入数据时，不编造收购 ROIC。
- **特殊资金占用：** 税务或诉讼押金、受限资金等即使保留为资产，也不等同可自由使用现金；说明本金、利息、可回收性与法律状态的披露边界。
- **融资与权益：** 区分借款、利润留存、分红回购、其他综合收益及少数股东权益。低账面权益可能源于长期分配或回购，不能直接等同经营亏损；债务变化需结合资金用途，不能只报资产负债率作结论。

不要求给每次变化制作精确金额桥。证据足够时量化主要贡献，证据不足时明确剩余变化包含哪些已知因素或尚未拆分，不能以叙事填平差额。

### 6.4. 重点科目表格

- 选择能支撑本节判断的总资产、重要资产类别、借款、关键经营及特殊负债、权益等；覆盖资产端与资金来源端，但不要求每家公司列相同项目。
- 表头清楚标示期间和单位；金额使用千位分隔，比例通常一位小数，缺失与零分开。正文金额使用中文习惯的万、亿单位，表格保留披露或底稿原尺度。
- 历史与近期表采用一致科目定义；表过宽时按经济含义拆表或转置，不能靠删除重要年份或挤小字体解决。
- 对资产负债表科目，按分析需要给出金额、占比或变动，不机械要求每个存量科目都列同比；若表中含收入或利润，继续遵守“金额（同比）”展示规范。占比明确分母，资产占比一般为该期总资产，不能混用权益或流动资产分母。
- 在相关表图旁简要解释陌生或易误解科目的经济含义，注明来源、分析者归并及重要重分类。无需为现金、存货等常见科目逐个写教材定义。

### 6.5. 运营资本：先明确经营范围，再解释资金占用

#### 6.5.1 三种概念分开

`流动资产－流动负债`是流动性净额，不能直接称为经营净运营资本。现金流量表中的“经营资产和负债变动”是期间流量，也不等于资产负债表两个期末净运营资本的差额。

经营净运营资本按该公司披露构造：

```text
经营性流动资产 = 流动资产－现金及等价物－可识别的流动金融与其他非经营资产
经营性流动负债 = 流动负债－短期借款及长期债务流动部分－可识别的非经营负债
净运营资本 NWC = 经营性流动资产－经营性流动负债
NWC / 收入    = 期末 NWC / 同口径全年收入（中期期末优先用 TTM 收入）
```

上述是映射起点，不是机械减项清单。对待售处置组、收购及出售应付款、或有对价、租赁、税项、结算资金等，依据性质及附注逐项判断，保持跨期一致。普通经营应计费用可以属于经营负债，收购尾款不能因列在“应付及应计费用”中就视为供应商融资。未拆分的剩余科目保留原归类并说明，不能声称已经完全纯化。

若重大非经营事项造成假波动，保留“调整前 → 有来源的调整 → 调整后”可核对关系；必要时在图中比较调整前后。没有重大混入时不制造调整口径。未披露不等于余额为零。

#### 6.5.2 表图与解释

- 显示完整历史的经营性流动资产、经营性流动负债、NWC 及 NWC/收入；有近期数据时补充相同口径的期末情况。解释主要由应收、存货、预付、贸易应付、经营应计等哪一端驱动。
- 有助于观察趋势时绘制 NWC 及收入占比折线，金额与比例分别设面板或明确刻度；负值保留零线。不能把中期期末 NWC 除以单季度收入后与年度比率直接比较，也不静默把季度收入乘四代替 TTM。
- 负 NWC 说明经营负债对经营资产形成资金支持，进一步检查其来源、稳定性和增长放缓时的现金压力；不直接推断议价能力强、现金流必然改善或没有偿债风险。
- 结合现金流附注解释重大差异：收购处置、汇率、非现金变动、税款、收购尾款、待售重分类等会使期末余额变化不同于经营现金流影响。不用简单的负 ΔNWC 强行配平 OCF。

#### 6.5.3 周转效率是补充证据

DSO、DIO、DPO、CCC 使用 [metric-catalog.md](../../financial-statement-analysis/references/metric-catalog.md#8-working-capital) 的公式和期初期末平均余额。DPO 必须回到附注取得贸易应付款，不能拿含营销、薪酬或收购应付款的整项“应付及应计费用”代替；采购额未披露时可用营业成本近似，但须说明。

期初余额缺失、近期贸易应付未拆分或分子分母范围不匹配时，显示不可计算及原因，不编造周转天数。中期使用实际覆盖天数或匹配的 TTM 分母与余额，并说明口径；处置重列造成断点时标注、断线或分段比较，不将机械改善解释为纯经营效率提升。

如需作图，可用一张图的不同面板展示三项周转天数及 CCC。正文解释哪个环节改变资金缺口，而非复述所有曲线。NWC 金额和周转天数的经营范围不同，不能未经桥接就把二者视为完全相同的结论。

### 6.6. 资产结构：一张图同时表达金额与占比

#### 6.6.1 先完成可核对的归并

- 资产分类依据公司商业模式、报表与附注，覆盖现金及金融资产、经营流动资产、生产经营资产、投资、收购形成的资产及重要特殊占用等实际存在的类别，不强制固定类别数量。
- 每项资产只归入一类，每期各组金额加总等于该期总资产，未取整占比合计 100%。每组保留原科目、公式、来源与归并说明。
- 重大且性质不同的资产单列；其余合并为含义明确的组。待售资产包括已嵌入“其他”科目的已披露处置组，重分时同时扣减原组。
- 某年未单列投资、无形资产或使用权资产，不等于不存在；若仍包含于其他资产，保留在该聚合项并注明跨期可比性。不得同时保留总项及其组成项造成重复。
- 百分比变动同时检查分子与总资产分母；占比下降不能自动解释为该类资产金额下降。账面结构不等于市场价值，也不代表所有资产都可变现或可抵债。

#### 6.6.2 默认图形与交付

默认采用**金额堆积柱状图，柱顶标总资产，各色区块标占总资产比例**。这一张图同时承担规模、金额结构与比例结构的比较；已有清晰占比标注时，不再默认重复提供百分比堆积图。

- 展示研究范围内完整年度及最新期末；最新中期与历史年末明确区分，标签写具体期间。年度细节和近期细节仍在底稿保留，不为图形清晰而漏掉研究数据。
- 所有非零区块均标占比，细小区块用引线或相邻注释；调整画布、分类和排版以保证可读，不能仅标最新年份或只标大区块。真实零值无需标注，未披露不得画成零值。
- 同一类别跨年颜色、顺序和口径一致，金额轴标单位，图例名称易懂，写明“区块数字为占比”。图下注明时点、重要分类断点、来源和归并属性，必要时注明取整误差。
- 图以中文读者便于理解的金额单位绘制；数据表保持原尺度。使用可复现的标准绘图工具，保存后检查中文、比例标注、引线、图例和 Word 实际插入尺寸下的可读性。
- 完整金额与占比归并表保留于工作底稿或可追溯数据。正文已有足够的重点表与该图时，不必再重复贴一整套资产结构表；用户要求数字明细时再完整提供。
- 图放在相关解释附近。图中文字说明“是什么”，正文说明“为什么变化、反映什么资本配置、由谁创造回报、还有什么风险”；不逐个颜色读数字。

在本 Workspace 中，可重建图表保存到公司 `outputs/figures/`，遵守 Git 忽略规则；原始披露不移动、不覆盖。对话交付时直接显示最终图片，用户要求手动粘贴时不擅自编辑 Word。

### 6.7. 交付前的完成判定

本节基本完成须同时满足：

- **主线完整：** 读者能解释历史资产配置的来龙去脉，重大转折已连接到科目与现金；融资和权益没有因只关注资产而遗漏。
- **覆盖完整：** 约定历史及已有近期数据已展示或有明确定位，重要科目、NWC 和适用的周转指标齐备；不适用或不可得的项目说明原因，不要求用户发现缺项。
- **证据可核对：** 资产等式、归并加总、占比及 NWC 公式通过检查；重分类及重大调整有附注依据，断点没有被虚构的可比性掩盖。
- **表达有效：** 图表承担完整数据，文字抓主要矛盾；没有逐年复读、重复图形或只有“战略调整”的空泛归因。
- **判断有边界：** 未将负 NWC、低固定资产比例、收购对价或减值直接等同经营质量结论；利润、现金、资本投入和账面变化分清。
- **衔接清楚：** 已完成内容可以收束，后续净现金、资本回报或股东回报按报告结构推进，不为追求“齐全”继续向本节堆砌指标。

只有与本节结论有实质影响的证据缺口才阻止完成；文字润色不必导致重开分析。检查现有报告时，区分“本节已基本完成”和“整套基本面分析全部完成”，简要指出真正剩余的工作。

## 7. 现金流章节：累计流向与股东现金回报

现金流模块必须同时回答三个问题：利润如何转化为经营现金及资本开支后现金；约定研究期内现金累计来自哪里、流向哪里；分红和回购给股东留下了什么、能否由经营现金支撑。只交付 CFO、资本开支和 FCF，或只评论最新一年分红，不构成该模块完成。后续资本配置、治理或估值章节可以深化判断，不能据此推迟本节的历史分配和缩股核验。

### 7.1. 完整历史与累计资金闭环

- 沿用约定的完整历史及最新可比期间。十年累计指十个财年的流量之和；累计股数变化匹配首年期初与末年期末，不能把十年支出与只有九个增长区间的期末比较混为同一窗口。
- 从完整现金流量表归并经营现金流、资本开支、并购及参股、资产和业务处置、现金分红、普通股回购、借款发行与偿还、短期金融投资回收或购入、股权行权、代扣税及其他重要流量。汇兑影响与期初期末现金范围同时配平；现金、受限现金和短期投资的分类保持一致。
- 可以净额展示借款或短期投资以提高可读性，但保留各自发行/偿还、买入/回收的映射。净融资现金不等同资产负债表债务变化。经营现金流已包含的税款、养老金、重组及整合付款不得再次列为独立用途。
- 说明分析者 FCF 与公司定义 FCF 的桥接，计算累计 FCF、累计分红加回购，以及分配前后的现金余缺。将缺口与其他资金来源共同解释，不把全部借款机械归因于分红，也不把全部投资现金流当作资本开支。

### 7.2. 分红：总额、每股与可持续性

- 展示现金分红完整历史、每股股息及其增长、相应盈利分配率、FCF 对分红和分红加回购的覆盖。每股数据使用原始披露，区分宣告股息与支付股息；不以总现金股息除以期末或加权股数冒充已披露每股支付股息。
- 分配率写明 GAAP/Core、归母/合并及期间。特殊税项或减值使报表盈利失真时，保留原口径并以有来源的可比盈利补充判断；不得假定 Core 调整项没有现金代价。
- 区分经营改善、支出延后、现金回收时点和一次性流入对覆盖的影响。最新 YTD 与同期比较，TTM 使用匹配累计数，不从一个中期缺口直接判断全年不可持续。

### 7.3. 回购：现金支出与实际净缩股分别验证

- 同时展示回购现金支出、原始披露回购股数、实际期初期末普通股数，以及行权、RSU/PSU 转换、其他发行或转换等抵销因素。以权益变动表、股份附注或可靠的期末在外股数建立股数桥，保留百万股披露的取整误差。
- 实际期末在外股数与 EPS 使用的基本/稀释加权平均股数分开。前者回答净缩股，后者仅用于解释每股盈利分母效应；不得用加权平均股数变化冒充精确期末注销或净缩股。
- 现金流表支付金额与权益表回购确认金额可能有分类或结算差异，不能无依据强求相等。代扣税收回股份不自动等同公开市场回购。不得将回购支出全部视为净缩股收益，也不凭“花钱后股数下降”断言回购价格划算。
- 结合规模、净缩股速度、抵销因素和现金约束评价回购的实际作用；需要讨论 EPS 增厚时，明确固定盈利的计算假设及使用的加权分母，不重复计入现金回报或估值收益。

### 7.4. 完成检查

交付前确认：完整年度和最新期间齐备；累计资金来源与用途闭环；分红及分红加回购的覆盖明确；每股股息口径清楚；回购支出、总回购股数与净缩股已经分开并核验；重大缺口有来源或明确保留；图表与结论能解释股东回报的现金代价和持续条件。图表数据保留于可追溯底稿，正文抓住主要矛盾，不逐年复读。

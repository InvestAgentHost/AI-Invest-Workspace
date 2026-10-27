# 批量初筛：取数、估值与交付可靠性

本文件是批量模式 Step 2、6—8 的执行约定。使用 `valuation_pipeline.py` 和 `checked_build.py`；不改变 `screener.py` 的数值公式、分位门槛或行动规则。个股筛选提示词不受影响。详尽原始标签由本轮转换者核验，脚本检查不能代替阅读披露。

## 1. 先建覆盖矩阵，再安排补缺

每家公司分别检查：证券/报价、历史价格、TTM EPS、TTM经营利润、纯D&A、实际在外股数、EV各项权益/债务请求权、FX。先检查 FocusAlpha 当前工具、同截止日完整缓存和公司/期间覆盖。不能只取年度报表和价格就宣布完成估值。

- 不以 USD、`us-gaap` 命名空间或普通股单一维度筛掉其他有效数据。IFRS、半年报、非美元和公司扩展标签走相应转换；SEC companyfacts 未出现某标签时，再看原始iXBRL的股类/业务维度与附注。
- 限流、权限不足、工具不支持该市场、空字段、返回预览、历史不足分别记录。限流不等于公司未覆盖；摘要或前后几行不等于全量序列。分页取完并保存完整响应才进入转换。
- 多agent共享同一份取数清单和缓存；按发行人/工具/期间去重，避免各自重复请求。出现同类限流后暂停并发；遵守提供方的重试提示，同轮最多再作一次有间隔的重试，之后记录限制并用可访问来源补缺，不反复撞接口。
- FocusAlpha 缺口再检查 Gangtise 的实际数据能力，见 `gangtise-screening.md`。能够直接补财务/市值的工具，与研报/纪要/生成一页通分开使用。数字优先回到监管、交易所和公司IR披露核验；不同提供方差异保留，不能选择最方便过门槛的值。
- 每个未解决的重大估值缺口，交付前必须有 FocusAlpha 查询/缓存、Gangtise能力检查或取数、原始披露查询的实际记录；可复用本轮相同市场/接口的能力证据，不要求逐公司机械重复已证实不适用的接口。未尝试就继续取数，不能直接写“数据源不覆盖”。已尝试仍无解，明确原因后可以交付，不要求用户另行批准N/A。

`source_attempts`每条包含：`provider`（`FocusAlpha` / `Gangtise` / `Original disclosure`）、`tool`、真实`query`、`retrieved_at`、`scope`、`status`、`source`、`raw_path`及必要的`reason`。状态仅用`returned/reused/empty/missing_field/rate_limited/permission_denied/unsupported_market/truncated/unavailable`；计划不算尝试。`scope`可为字段名（prices/eps/op/da/shares/claims/history）或financials/market_data/valuation/all。缓存记录原查询及截止日，不能用事后行情覆盖旧筛选日。

## 2. 财务与证券口径先核对

1. **TTM与公开时点。** 同一口径的上年全年−上年同期累计+本年同期累计；半年报不能套单季时效。`ttm_bridge`检查期间、长度、币种及定义，保留三个输入。每个交易日只用当时已公开的资料，保守从首次披露次日可用；重述比较数不能回填到较早披露日。正式年报与中报EPS股类分配不同，不强拼TTM。
2. **利润。** EPS为稀释、已报告每报价单位利润；经营利润采用原文未经调整的经营利润，另记分析小计。D&A必须为完整纯折旧摊销，不能混入减值、其他非现金项目或调整后EBITDA。不要把损失加回以制造正倍数。EPS/op/da分别可用，缺一项不能整家公司全部跳过。
3. **股数。** 每日市值用当时已披露的实际在外股数，扣库存股；不使用稀释加权股数。区分发行总数、各股类、可交换单位、ADS/普通股比例及拆股前后基础。价格/EPS/股数统一到同一个`quote_unit_id`，ADR比例变动与反向拆股也一样。股价可能回溯调整拆股，`adj_close`还含股息，不能直接除未对应调整的EPS。
4. **市值与Up-C。** 提供方市值不一定包括全部经济单位。以同日价格×对应实际经济单位核对。已价格化全部可交换单位时，不再把同一Up-C部分的账面NCI重复加到EV；若只使用上市A股市值，则需完整对应的其他权益请求权。把选择及原文写进`claims_review`，不一刀切地排除所有NCI。
5. **EV。** 确认借款是否已含融资/经营租赁；另查供应链融资、库存/商品回购融资、优先股、可赎回NCI及普通NCI、固定分期和解负债。逐项明确是否适用、是否已包含、正负号和来源。普通优先股授权未发行的0不能覆盖已发行的可赎回优先资本。负债付清后以新披露余额更新，不永久沿用旧数。历史义务余额未完整复原时该日EV留空；后续披露的比较数不能证明早期投资者当时已知其为0。
6. **币种与单位。** 年度main为百万，估值事件/市值为完整金额，ev.tev输出才转为百万。GBp先÷100为GBP；财报利润、净债务和当日FX转到报价币种。FX时间戳按提供方交易所时区映射日期，不能取UTC日期后直接说“早一天”；跨币种不能用今天的汇率回填全历史。M1薪酬也要对齐报价币种并保留原币金额、日期与FX来源。
7. **窗口。** 记录真实经济上市/可比业务日期，剔除前身SPAC壳期。IPO本身不自动加12个月；并购窗口继续按原`pe_from`规则。v4.7.2数值引擎默认采用10年，保留的`pe_default_from`仅影响旧版显示文字，不能用来缩短数值窗口；显示起点必须与实际可比数据一致。提供方历史起点不是公司上市日。窗口内缺失日保留，不能删除缺失交易日使覆盖率虚增。

## 3. 可复用输入与命令

把经核验的事件写到`$RUN/valuation_inputs.json`（schema_version=1）。它不是新的数据源，所有源响应和原文另存。顶层：

```json
{
  "schema_version": 1,
  "price_date": "2026-10-23",
  "disclosure_cutoff": "2026-10-26",
  "companies": {
    "AAA": {
      "key": "NYSE_AAA", "listing": "AAA.N",
      "listing_currency": "USD", "reporting_currency": "EUR",
      "accounting_standard": "IFRS", "quote_unit_id": "AAA-ordinary-split-basis-2026-10-23",
      "reporting_frequency": "semiannual",
      "ev_claims": {"debt": 1, "cash": -1, "preferred": 1, "nci": 1},
      "claims_review": {"complete": true, "source": "Original financial notes; no duplicate leases or priced units", "raw_path": "raw_sources/AAA_notes.html"},
      "prices": [], "fx": [], "market_caps": [], "metrics": {}, "source_attempts": []
    }
  }
}
```

数组省略内容是结构示例，不是可直接运行的数据文件。各数组内容：

- `prices`：`{date,value,currency,basis,source,raw_path}`，唯一升序交易日，`basis=quote_unit_id`。未知价格保留null。`market_caps`同形状，可只提供当前截面；其他日期用真实在外股数×价格。超过2%的差异须先核对，必要时提供有证据的`market_cap_reconciliation`；不能直接调大容差掩盖差异。
- `fx`：`{date,value,from,to,source,raw_path}`，定义为一单位财报币可换多少报价币；非相同币种必须有每日实际可用FX，默认最多向前取7天。相同币种无需数组。
- `metrics`：字段→事件数组。每事件含`available,published,period_end,value,currency,unit,basis,source,raw_path`；计算值含公式和`inputs`，其中各输入不能晚于输出可用日。null须有reason，0须有原文核实。金额事件`unit=currency`，均为完整金额。
- `eps`额外：`kind=ttm`、`unit=<币种>/quote_unit`、`basis=quote_unit_id`、`definition=diluted_reported_eps`。`op/da`额外：`kind=ttm,period_start`，同一期间/业务口径`basis`，definition分别为`reported_operating_profit`、`pure_depreciation_amortization`。不要为了通过检查改标签；先核对来源实际含义。
- `shares`：`unit=quote_units`、`basis=quote_unit_id`，实际在外报价单位；currency用`shares`。其他EV请求权的字段名由`ev_claims`列出，有适用项就必须有事件或明确缺口；不能把不存在的事件自动补0。声明不适用的权益项目由有来源的`claims_review`解释。
- `economic_history_from`只在有官方来源时填写，并给`history_start_evidence={source,raw_path,...}`。`max_age_days`按字段可覆盖默认时效：季报190、半年报290、年报410天；不能延长时效只为过覆盖门槛。年度股本/少数权益等代理可取最新公开余额，但须在limitations说明日期，不能标成同期直接披露值。
- `approximate_current={values:{pe,ebit,ebitda},reason,source,raw_path,...}`可单列有来源的近似当前倍数；不会写入精确历史，也不参与分位、方向和研究线。受限现金、未披露的当期租赁等不能隐去。无正利润分母也不是数据源失败。

从Workspace根目录用`.venv/bin/python`，`$RUN`等沿用批量工作流：

```bash
"$PY" "$RUN/valuation_pipeline.py" build "$RUN" --input "$RUN/valuation_inputs.json"
# 检查 valuation_stage/valuation_audit.json；纠正来源、维度和完整性后再提升候选输入，无需另问用户许可。
"$PY" "$RUN/valuation_pipeline.py" promote "$RUN"
"$PY" "$RUN/checked_build.py" "$RUN"
"$PY" "$RUN/valuation_pipeline.py" annotate "$RUN"
"$PY" "$RUN/vault_records.py" snapshot "$RUN"
"$PY" "$RUN/vault_records.py" compare "$RUN"
"$PY" "$RUN/make_html.py" "$RUN"
# 按 chinese-report-style.md 完成中文呈现后，再检查最终HTML。
"$PY" "$RUN/valuation_pipeline.py" check "$RUN" --html "$RUN/<output>.html"
```

`build`仅写候选；`promote`检查源/原输入哈希，备份到唯一的`valuation_revisions/`后提升。`checked_build`用原引擎公式，只把未核验的资本、利润修补、CFO/资本支出/SBC输入挡在确定评分之外；R1检查不全显示待核验。原facts不改，M1薪酬的规范化/缺口进入facts_model。个股提示词和原引擎阈值不改。

`annotate`不重写数值分数，核对引擎与来源覆盖状态一致后更新缺项原因、导出`valuation_coverage.csv`，并把底稿索引追加到来源台账。原始证据与生成的估值序列均绑定哈希；`delivery_bindings.json`再绑定最终page_data、事实输入、来源台账、覆盖表和运行元数据。`make_html`对新批量配置`valuation_pipeline_required=true`自动执行交付检查；HTML带page_data/config哈希，`check --html`可检出旧页面。修复后再跑原引擎build时必须重新annotate并重建HTML，不能沿用旧覆盖说明。中文规范见`chinese-report-style.md`，只改变呈现时不重建财务输入。

## 4. 部分补跑与交付

- 部分修复用`build --tickers AAA,BBB`，输入另存如`valuation_inputs_revision2.json`，不要覆盖先前输入；非目标的pe/ev从现有文件逐字段保留。提升后以`refresh`替代完整`checked_build`及`annotate`，只重算目标估值/行动，逐字段断言非目标公司和全部质量评分未变。已有新规范audit时脚本合并其余公司的同截止日审计，并核验旧源输入哈希；首次把旧报告迁入新规范时分清已补跑与原基线，不把未审计公司标成完整。默认新名单必须全公司纳入audit。
- 固定原价格和披露截止日，保存修复前page_data、来源索引、记录及原HTML/ZIP；不要覆盖原始响应、旧档案或手工决策。比较变化原因记为数据修复，不当作股价或经营变化。记录写入使用新revision的run-file锚点，防止同日修复被当成重复运行跳过；只更新目标记录，保留全部`our_*`字段和人工正文。
- 发布前检查全部未判定位公司，不只抽几个绿灯：逐倍数区分非正利润、当前缺项、短比较窗、正值日数不足、历史资料缺口及正值覆盖不足，列出正值/非正值/缺失天数。门槛从原RULES读取：当前分母>0、至少250正值日、至少60%正值覆盖（沿用引擎取整）。不能把剩余11家或某次修复数量固化进脚本。
- 右列标题为“历史估值分位不可用”；有当前倍数仍可列在此处。当前近似值与其限制单列；空EPS不能称为亏损，图线断点不能一概称为亏损期。无分位的Research at lower price必须说明是原引擎占位标签，尚未判断价格偏贵。
- HTML、CSV、公司记录、摘要、来源台账和档案必须对应同一最终输入。检查链接、公司数、截止日、分位/研究线、近似值标记；源文件变化后重新构建相关文件和清单。数值抽查覆盖跨币种/股类或ADS、一个真实亏损、一个临界历史样本及一个非目标公司保留检查。另做桌面/手机、注释开合和内部链接视觉检查。
- 把HTML、CSV、审计JSON和来源索引一并交付；完整原始资料保留在RUN档案。`check`允许已尝试补齐但仍未解决的缺口以warning交付，未取数、口径冲突、旧页面或审计不一致必须先修。不要用“保证以后不缺数据”代替这些检查。

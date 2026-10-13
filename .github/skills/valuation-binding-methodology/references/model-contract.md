# 计算口径、现金闭环与核验输入

## 方法与迁移

流程可组织 DCF、P/E、SOTP 等；股东分红+退出 PE 的折现回报模型不是标准永续 FCFF DCF。正的正常化归母利润、可解释退出倍数、现金股数可建模时可用 direct-pe-net-shares-v2。亏损、重大周期或异质集团用适当现金流/分部方法，不能硬塞正利润 PE 模型。

FCFF：税后经营现金流−再投资，以 WACC 折现得经营企业价值，再桥接现金、债务、租赁、非经营资产、NCI 到股权。FCFE：股权现金流含净借款，以股权成本折现。终值用匹配永续增长或退出倍数，不重复相加；永续增长低于折现率且再投资支持增长。租赁/融资不能在流量与权益桥双扣。核验脚本不实现这两条路线，需另建并验证。

旧 NI×c×m 先判明 m 是 PE 还是 FCF 倍数。若有效 PE=c×m，迁移将旧有效 PE 显式映射为直接 PE，保留快照与差异说明；原 m 若是 FCF 倍数可保留独立 FCF 方法。不得只换标签保留错公式，也不得静默改变历史输出。

## PE、股数与分红

统一金额/股数数量级，年度 t：

```text
NI_t = NI_(t-1) × (1+g_t)       # 优先用经营驱动推导的年度路径
N_t = N_(t-1) × (1-s_t)        # 期末实际流通股，正 s 为缩股
D_t = NI_t × p_t               # 现金分红，不含回购
dividend_per_share_t = D_t/N_t # 年末股数分红近似
terminal_per_share_H = NI_H × PE_H / N_H
```

PE_H 是直接退出市盈率，不得再乘 c。转换率 c 用于现金可行性和交叉验证。回购只通过股数改变每股价值，不再加到分红现金流。

按当前持有股份 N_0 折算：D_holder,t=D_t/(N_t/N_0)，TV_holder,H=NI_H×PE_H/(N_H/N_0)。这是原股东持股数量不变的等价总额，不是未来公司真实总市值，必须准确标注。

市值=估值日股价×当日实际流通股；报告 EPS 分母为期间加权平均稀释股数。EPS_t=归母利润/稀释加权平均股数。用发行回购时点加权，资料不足可明确用期初期末均值近似。期末股数算出的量只能标“期末股数口径每股盈利”。拆股/ADR 比例统一，不能当经济缩股。

多次记录日派息可用各记录日股数；年末股数/年末分红近似须说明。

## 日期

估值日、财年末、股数测量日、派息日分开。财年模型利润按财年，但投资现金流仍从实际估值日开始。不能跳过当前残余期间，不能再次计入已支付分红。

实际日期用 XIRR/XNPV，年末近似也注明日期；等距 IRR 须说明虚拟起点与首次收款距离，不把3个月称1年：

```text
P_0 = Σ dividend_per_share_t/(1+r)^τ_t + terminal_per_share_H/(1+r)^τ_H
τ = (收款日−估值日)实际天数/365
目标买入价 = 上式按要求回报率计算
```

先逐年建模再取持有节点，财年末终止须报告实际持有年数。短长 IRR 可与利润 CAGR 不同：PE 差异年化摊薄、分红、股数和时点均影响结果。

## 现金闭环

明确 FCF 的租赁/利息/税边界；必要用途未覆盖时不能称资金够用：

```text
期初可用现金 + FCF + 股权发行现金 + 总融资流入 + 处置/其他流入
− 分红 − 总回购 − 到期债务本金 − 融资租赁本金
− 未在 FCF 中包含的承诺支出/其他必要用途
= 期末现金（满足最低流动性）
```

若采用净融资则不可再重复扣本金。CFO 已含税息、FCF 已含计划/处置现金时不可重复处理。再融资可行性是判断，不能视作事实。

期内发行股数=N_start×d，总回购股数=N_start×(s+d)，回购价近似为 PE_buy×NI/N_end 时：

```text
总回购现金 ≈ (s+d)/(1-s) × NI × PE_buy
```

这是与明确发行比例 d、回购价一致的粗预算。员工激励、增发、库存股再发行、扣税股先做股数桥；SBC 费用不等于发行股数。股权交付不一定带来现金。s+d<0 说明机制不一致，须补股数变化解释。

持续缺口应调整资本配置或明确融资及成本，并反映到利润、股数、估值。未知远年债务不能填零。反推满足 c 所需 CFO 不独立证明 c，不能用这个循环声称 FCF 已包含全部投资。

## 核验器输入

calculate 接收 JSON，金额/股数为同币种与匹配数量级，比率为小数。示例仅说明接口，非默认假设：

```json
{
  "method_version": "direct-pe-net-shares-v2",
  "valuation_date": "2030-12-31",
  "currency": "USD", "amount_unit": "million", "share_unit": "million",
  "market_cap": 2000, "current_shares": 100,
  "opening_available_cash": 0, "required_return": 0.10,
  "years": [{
    "period_start": "2031-01-01", "period_end": "2031-12-31",
    "cashflow_date": "2031-12-31", "net_income": 110,
    "net_shrink": 0.01, "fcf_conversion": 0.9,
    "payout": 0.5, "exit_pe": 20, "diluted_average_shares": 99.5,
    "cash": {
      "dilution_rate": 0.002, "buyback_pe": 20,
      "debt_principal": 0, "financing_inflow": 0,
      "finance_lease_principal": 0, "other_necessary_uses": 0,
      "other_inflows": 0, "equity_issuance_cash": 0, "minimum_cash": 0
    }
  }]
}
```

net_shrink 是上一股数节点到本节点区间变化，首年残余期间不得直接用全年缩股率。可选 fcf 用独立推导金额覆盖 NI×c，并检验转换率一致；cash.gross_buyback_cash 用详细时点/价格预算覆盖近似回购额。用途含债务等全部必要明细，未包含项并入 other_necessary_uses，在底稿分解。

首年 period_start≤估值日时必须给 dividend_after_valuation（估值日后有权收到的公司分红）、budget_fcf（剩余期间 FCF）、cash.gross_buyback_cash 及其余用途的剩余期间预算；全年利润仍用于 EPS/终值。不能拿全年现金证明残余期间够用。

脚本逐终年输出日期 IRR、目标价格/市值、按当前股份退出价值、EPS、资金预算。现金字段缺失 PARTIAL、缺口 FAIL、错误输入拒算。此正收益单终值路线有常规唯一根；多次现金流变号另用多根诊断。脚本不抓数据、不改 Excel、不能代替来源、公式、现金边界与版面验收。

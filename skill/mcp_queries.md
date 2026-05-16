# MCP 查询模板

定义 senior_analyst MCP 工具在各任务类型中的查询序列。当 MCP server 可用时，优先按以下模板执行查询。

---

## 查询原则

### 分级查询
每个任务类型的查询分为**必查**和**选查**两级：
- **必查**：L2/L3 都必须执行，是分析结论的最小数据集
- **选查**：L3 必须执行，L2 按需补查（根据必查结果判断是否需要）

### 并行执行
标注 `[并行]` 的查询可以同时发起，减少总等待时间。标注 `[串行]` 的查询依赖前序结果。

### 超时控制
- 单次 MCP 查询超时上限：**8 秒**
- 超时自动降级到 P2（训练数据 + WebSearch），不阻塞后续分析
- 必查项超时后必须尝试 P2 补充，选查项超时可直接跳过

---

## 检查 MCP 可用性

在执行查询前，先确认 `senior_analyst` MCP 工具是否可用：
- 若可用 → 按 `mcp_queries.md` 执行
- 若不可用 → 回退到 `data_protocol.md` 中的 P2-P5 降级链

---

## 财报分析/排雷

### L2 必查 [并行]
```
1. company_financials(identifier, period="annual", years=3)
   → 获取营收、净利润、经营现金流、总资产、总负债
2. company_profile(identifier)
   → 获取行业、市值、估值指标（PE/PS/PB）
```

### L3 选查 [并行]
```
3. competitor_compare(identifier)
   → 获取对标公司关键指标（若需行业对比）
4. news_search(identifier, limit=5)
   → 获取近期重大事件/风险信号
```

**关键验证**：
- 确认经营现金流与净利润的比例关系（OCF/NI）
- 对比行业估值水平（是否高估/低估）

---

## 竞争对手对比

### L2 必查 [并行]
```
1. company_financials(target)
   → 目标公司财务数据
2. competitor_compare(target)
   → 获取对标公司列表及关键指标
```

### L3 选查 [串行，依赖必查结果]
```
3. company_financials(peer_1, years=3)
   company_financials(peer_2, years=3)
   → 对标公司详细财务数据（peer 从 competitor_compare 结果中选取）
4. company_profile(target)
   company_profile(peer_1)
   company_profile(peer_2)
   → 估值对比（PE/PS/PB）
```

**关键验证**：
- 至少对比 2-3 家对标公司
- 对比维度覆盖财务/运营/估值三个层面
- 对差异做归因分析

---

## 情景/敏感性分析

### L2 必查 [并行]
```
1. company_financials(identifier, period="annual", years=5)
   → 获取 5 年历史数据，用于趋势推演
2. market_data(industry, region)
   → 行业增长预测、市场规模
```

### L3 选查 [并行]
```
3. news_search(identifier, limit=5)
   → 近期催化剂和风险事件
4. competitor_compare(identifier)
   → 竞争格局变化
```

**关键验证**：
- 历史数据至少 3 年，5 年更佳
- 关键驱动因素需有数据支撑
- 情景假设需合理可验证

---

## 战略分析

### L2 必查 [并行]
```
1. market_data(industry, region)
   → TAM/SAM/SOM 估算
2. competitor_compare(identifier)
   → 竞争格局和市场份额
```

### L3 选查 [并行]
```
3. company_financials(identifier)
   → 资源配置评估（收入结构、利润率）
4. news_search(industry + "政策", limit=3)
   → 监管环境变化
```

---

## 商业模式/单位经济评估

### L2 必查 [并行]
```
1. company_financials(identifier, years=3)
   → 收入结构、成本结构、利润率趋势
2. company_profile(identifier)
   → 行业定位、估值
```

### L3 选查
```
3. competitor_compare(identifier)
   → 同行单位经济对比
```

---

## PMF/增长诊断

### L2 必查 [并行]
```
1. company_financials(identifier, period="quarterly", years=2)
   → 季度收入趋势、增速变化
2. competitor_compare(identifier)
   → 同行增速对比
```

### L3 选查
```
3. news_search(identifier + "用户增长", limit=3)
   → 用户增长动态
```

---

## 行业商业建模

### L2 必查 [并行]
```
1. market_data(industry, region)
   → TAM/增速/市场规模
2. competitor_compare(identifier)
   → 竞对格局（若用户指定了目标公司）
```

### L3 选查 [并行]
```
3. company_financials(identifier, years=3)
   → 仅用户指定公司时查
4. news_search(industry + "政策", limit=3)
   → 仅用户关注风险/监管时查
```

---

## 宏观经济分析（v1.7+）

### L2 必查 [并行]
```
1. macro_data(indicator="gdp" | "gdp_growth", region, years=5)
   → 经济增长趋势
2. macro_data(indicator="cpi" | "cpi_yoy", region, years=3)
   → 通胀水平
3. macro_data(indicator="unemployment", region, years=3)
   → 就业市场
```

### L3 选查 [并行]
```
4. macro_data(indicator="interest_rate" | "treasury_10y", region)
   → 利率环境
5. macro_data(indicator="m2", region)
   → 货币供给
6. macro_data(indicator="ppi" | "pmi", region)
   → 工业景气
7. macro_data(indicator="exports" | "imports" | "trade_balance", region)
   → 贸易状况
```

**支持的 region**：
- `US`：FRED（需 free key）→ World Bank 兜底
- `CN`：stats_gov_cn（NBS/PBOC via akshare）→ World Bank 兜底
- `EU` / `JP` / `UK` / `DE` / `FR` / `IN` / `global`：World Bank（年度数据）

**关键验证**：
- 至少覆盖 3 年时间序列
- 月度数据（CPI/PMI/失业率）优先于年度
- 政策窗口期（Fed FOMC、人行 LPR 调整）需 news_search 交叉验证

---

## 加密资产/Web3 分析

### 必查
```
1. crypto_data(identifier="BTC" | "ETH" | ...)
   → 价格、市值、24h 量、流通量、排名
```

### 选查
```
2. news_search("[token] regulation" | "[token] etf", limit=5)
   → 监管/资金流入信号
```

**关键验证**：
- 头部币种（BTC/ETH/SOL/BNB/USDT）支持 symbol 直接查询
- 长尾币种用 CoinGecko id（如 `avalanche-2` 而非 `AVAX`）
- 默认 30 req/min 限速；配 CoinGecko Pro key 可解锁

---

## 降级处理

| 场景 | 处理 |
|------|------|
| MCP server 未配置 | 跳过 P1，从 P2 开始 |
| 必查项超时（>8秒） | 切到 P2（WebSearch），必须尝试补充 |
| 选查项超时（>8秒） | 直接跳过，不影响分析推进 |
| MCP 返回 `success: false` | 切到 P2，标记该数据已尝试 |
| MCP 返回部分数据 | 用已获取部分 + P2 补充缺失 |
| eastmoney 不可用 | MCP 内部自动降级到 akshare → yfinance |
| 所有 MCP 源失败 | 提示用户数据获取受限，建议 WebSearch 补充 |
| **macro_data 全部失败** | 提示运行 `senior_analyst-doctor` 自检；若 region=US 建议配 FRED key |
| **crypto_data 失败** | 多为 CoinGecko 限速；30 秒后重试或配 Pro key |
| **doctor 报 Tier 0 失败** | 检查网络；akshare 旧版本可能需要 `pip install -U akshare` |

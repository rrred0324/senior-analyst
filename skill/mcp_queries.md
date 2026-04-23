# MCP 查询模板

定义 senior_analyst MCP 工具在各任务类型中的查询序列。当 MCP server 可用时，优先按以下模板执行查询。

---

## 检查 MCP 可用性

在执行查询前，先确认 `senior_analyst` MCP 工具是否可用：
- 若可用 → 按 `mcp_queries.md` 执行
- 若不可用 → 回退到 `data_protocol.md` 中的 P2-P5 降级链

---

## 财报分析/排雷

```
1. company_financials(identifier, period="annual", years=3)
   → 获取营收、净利润、经营现金流、总资产、总负债
2. company_profile(identifier)
   → 获取行业、市值、估值指标（PE/PS/PB）
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

```
1. company_financials(target)
   → 目标公司财务数据
2. competitor_compare(target)
   → 获取对标公司列表及关键指标
3. company_financials(peer_1, years=3)
   company_financials(peer_2, years=3)
   → 对标公司详细财务数据
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

```
1. company_financials(identifier, period="annual", years=5)
   → 获取 5 年历史数据，用于趋势推演
2. market_data(industry, region)
   → 行业增长预测、市场规模
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

```
1. market_data(industry, region)
   → TAM/SAM/SOM 估算
2. competitor_compare(identifier)
   → 竞争格局和市场份额
3. company_financials(identifier)
   → 资源配置评估（收入结构、利润率）
4. news_search(industry + "政策", limit=3)
   → 监管环境变化
```

---

## 商业模式/单位经济评估

```
1. company_financials(identifier, years=3)
   → 收入结构、成本结构、利润率趋势
2. company_profile(identifier)
   → 行业定位、估值
3. competitor_compare(identifier)
   → 同行单位经济对比
```

---

## PMF/增长诊断

```
1. company_financials(identifier, period="quarterly", years=2)
   → 季度收入趋势、增速变化
2. news_search(identifier + "用户增长", limit=3)
   → 用户增长动态
3. competitor_compare(identifier)
   → 同行增速对比
```

---

## 降级处理

| 场景 | 处理 |
|------|------|
| MCP server 未配置 | 跳过 P1，从 P2 开始 |
| MCP 工具调用超时（>10秒） | 切到 P2 |
| MCP 返回 `success: false` | 切到 P2，标记该数据已尝试 |
| MCP 返回部分数据 | 用已获取部分 + P2 补充缺失 |
| eastmoney 不可用 | MCP 内部自动降级到 akshare → yfinance |
| 所有 MCP 源失败 | 提示用户数据获取受限，建议 WebSearch 补充 |

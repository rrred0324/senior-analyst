# 估值分析 Playbook

适用于任务类型：**估值分析**

---

## 适用场景

- 用户问"这家公司值多少钱""估值怎么看""贵不贵"
- 投资决策需要内在价值参考
- 战略选择需要量化对比

## 估值方法组合

| 方法 | 适用场景 | 核心输入 | 局限 |
|------|---------|---------|------|
| **DCF** | 增长可见、FCF 稳定 | FCF + WACC + 增长率 | 对假设极度敏感 |
| **Comps** | 有成熟对标上市 | 同行 PE/PS/EV-EBITDA | 受市场情绪影响 |
| **DDM** | 稳定分红（银行/公用事业） | 股息 + 增长率 + 折现率 | 不适用不分红公司 |

**默认组合**：DCF（权重 60%）+ Comps（权重 40%），DDM 仅在股息率 >2% 时辅助使用。

## 标准流程

### Step 1: 确定估值方法组合

```
稳定盈利 + FCF 可见    → DCF 为主
有成熟对标上市公司     → Comps 验证
稳定分红（yield>2%）   → DDM 辅助
早期/亏损公司          → Comps（PS/EV-Revenue）为主，DCF 不适用
```

### Step 2: 采集估值参数

**MCP 查询序列（并行）**：

```
1. company_valuation(identifier, method="all")
   → WACC 组件、增长率、FCF、同行倍数
2. company_financials(identifier, period="annual", years=5)
   → 5 年财务数据（历史趋势）
3. company_profile(identifier)
   → beta、市值、行业定位
4. competitor_compare(identifier)
   → 同行 PE/PS/EV-EBITDA
5. macro_data(indicator="interest_rate", region=region)
   → 无风险利率（可选，company_valuation 已含）
```

**数据充分性检查**：
- DCF 必需：FCF ≥2 年 + WACC + 增长率假设
- Comps 必需：≥3 家可比公司倍数
- DDM 必需：≥3 年股息历史 + 增长率

### Step 3: 执行 DCF 估值

#### 3.1 关键假设设定

| 参数 | 来源 | 说明 |
|------|------|------|
| FCF₀ | company_financials 最新年 | 基期自由现金流 |
| 增长率 g | company_valuation.revenue_cagr + 调整 | 预测期 5-10 年 |
| WACC | company_valuation.wacc | 或自行计算 |
| 永续增长率 gₜ | 经验值 2-3% | 不超过名义 GDP 增速 |

#### 3.2 三情景假设

| 参数 | Bull | Base | Bear |
|------|------|------|------|
| FCF 增长率 | cagr + 2pp | cagr | cagr - 2pp |
| WACC | wacc - 1pp | wacc | wacc + 1pp |
| 永续增长率 | 3% | 2.5% | 2% |

#### 3.3 计算框架

```
预测期价值 = Σ FCF_i / (1+WACC)^i, i=1..n
终值 TV = FCF_n × (1+gₜ) / (WACC-gₜ)
企业价值 = 预测期价值 + TV/(1+WACC)^n
股权价值 = 企业价值 - 净负债
每股价值 = 股权价值 / 股数
```

#### 3.4 敏感性矩阵

必须输出 WACC × 增长率矩阵（至少 5×5），标注当前市值对应的价值交叉点。

### Step 4: 执行 Comps 估值

1. 从 `competitor_compare` 选取 3-5 家可比公司
2. 计算同行 PE/PS/EV-EBITDA 中位数
3. 适用倍数选择：
   - 盈利稳定 → PE
   - 增长型 → PS 或 EV/Revenue
   - 重资产 → EV/EBITDA
4. 推算目标公司价值区间

### Step 5: 执行 DDM 估值（如适用）

```
P = D₁ / (r - g)
D₁ = D₀ × (1 + g)
r = 无风险利率 + beta × ERP
g = 股息增长率（5 年 CAGR 或保守估计）
```

### Step 6: 综合估值

| 方法 | 权重 | 低 | 中 | 高 |
|------|------|-----|-----|-----|
| DCF | 60% | ... | ... | ... |
| Comps | 40% | ... | ... | ... |
| 加权合计 | 100% | ... | ... | ... |

与当前市值对比 → 溢价/折价判断 → 安全边际评估。

### Step 7: 输出估值报告

按 `templates/valuation_report.md` 格式输出。

---

## 关键规则

1. **禁止单一方法估值**：必须至少 2 种方法交叉验证
2. **DCF 必须做敏感性矩阵**：WACC × 增长率 5×5 矩阵
3. **三情景必须覆盖**：Bull/Base/Bear 缺一不可
4. **假设必须标注来源**：每个关键假设说明来自哪里（数据/经验/推断）
5. **结论必须含安全边际**：明确当前价位的安全边际是否充足
6. **数据不足时降级**：FCF 不稳定时，DCF 权重降低，Comps 权重提升

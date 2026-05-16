# 数据源矩阵 (v1.7+)

senior_analyst 支持的所有数据源、能力范围、API key 需求与降级关系。

---

## 一、按 Tier 分级

### Tier 0 — 零配置可用

无需任何 API key，安装后立即可用。

| 源 | 后端类型 | 主要 endpoint | 速率上限 | 中国大陆可用 |
|----|---------|------------|---------|------------|
| **yfinance** | Python 库 | Yahoo Finance | ~3 秒/请求（内部限速） | ❌ 受限 |
| **akshare** | Python 库 | 多个公开数据接口 | 由各上游决定 | ✅ |
| **eastmoney** | HTTP scrape | push2.eastmoney.com 等 | 不公开但宽 | ✅ |
| **stats_gov_cn** *(v1.7)* | akshare 包装 | NBS、PBOC、MOFCOM、海关 | 由 akshare 决定 | ✅ |
| **worldbank** *(v1.7)* | REST API | api.worldbank.org/v2 | 软限制（>1000 req/day 可能限流） | ✅ |
| **coingecko** *(v1.7)* | REST API | api.coingecko.com/api/v3 | 30 req/min（公共） | ✅ |

### Tier 1 — 需要 API key

#### 免费 key

| 源 | 用途 | 申请地址 | 免费额度 |
|----|------|---------|---------|
| **FRED** *(v1.7)* | 美国宏观经济（高频） | https://fredaccount.stlouisfed.org/apikey | 120 req/min，无日上限 |
| **Alpha Vantage** | 全球股票基本面 | https://www.alphavantage.co/support/#api-key | 25 req/day |
| **NewsAPI** | 英文新闻搜索 | https://newsapi.org/register | 100 req/day（仅 dev） |

#### 付费 key

| 源 | 用途 | 入门价 | 必要性 |
|----|------|------|------|
| **FMP** | 全球公司财报增强 + 同业推荐 | $14/月 | 可选；显著提升美股/全球财务数据 |
| **CoinGecko Pro** | 加密高级数据 | $129/月起 | 可选；公共 API 已覆盖头部币种 |

---

## 二、按 MCP 工具映射

| MCP 工具 | Tier 0 源（按优先级） | Tier 1 源（如有 key） |
|---------|--------------------|--------------------|
| company_financials | eastmoney → akshare → yfinance | FMP（首位）→ Alpha Vantage |
| company_profile | eastmoney → akshare → yfinance | FMP（首位）→ Alpha Vantage |
| competitor_compare | yfinance | FMP（首位） |
| market_data | eastmoney → akshare | FMP（首位） |
| news_search | akshare → eastmoney | NewsAPI（首位）→ Alpha Vantage → FMP |
| industry_data | eastmoney → akshare | FMP（首位） |
| stock_news | akshare → eastmoney | NewsAPI（首位）→ Alpha Vantage → FMP |
| **macro_data** *(v1.7)* | stats_gov_cn (CN) → worldbank (其他) | FRED（首位，仅 US） |
| **crypto_data** *(v1.7)* | coingecko | （Pro key 仅扩限速，不切源） |

---

## 三、宏观经济指标支持矩阵

### FRED（美国，需 key）

| indicator | series_id | 频率 | 单位 |
|-----------|-----------|-----|------|
| `gdp` | GDP | 季度 | USD billion |
| `gdp_real` | GDPC1 | 季度 | USD billion (chained 2017) |
| `cpi` | CPIAUCSL | 月度 | index 1982-1984=100 |
| `cpi_yoy` | CPIAUCSL (transformed) | 月度 | % YoY |
| `ppi` | PPIACO | 月度 | index 1982=100 |
| `unemployment` | UNRATE | 月度 | % |
| `interest_rate` | FEDFUNDS | 月度 | % |
| `treasury_10y` | DGS10 | 日 | % |
| `treasury_2y` | DGS2 | 日 | % |
| `m2` | M2SL | 月度 | USD billion |
| `retail_sales` | RSAFS | 月度 | USD million |
| `industrial_production` | INDPRO | 月度 | index 2017=100 |
| `housing_starts` | HOUST | 月度 | thousands |
| `consumer_sentiment` | UMCSENT | 月度 | index |
| `fx_dxy` | DTWEXBGS | 日 | index |

### stats_gov_cn（中国，无需 key）

| indicator | period | 来源 | 单位 |
|-----------|--------|-----|------|
| `gdp` | annual / quarterly | NBS | % YoY 或亿元 |
| `cpi` | monthly / annual | NBS | % 或 index |
| `ppi` | monthly | NBS | % |
| `pmi` | monthly | NBS | index |
| `m2` | monthly | PBOC | % YoY 或亿元 |
| `interest_rate` | (LPR) | PBOC | % |
| `unemployment` | monthly | NBS | % |
| `retail_sales` | monthly | NBS | 亿元 |
| `fx` | (FX 储备 + 黄金) | PBOC | USD bn |
| `fdi` | monthly | MOFCOM | USD bn |
| `exports` | monthly | 海关 | % YoY |
| `imports` | monthly | 海关 | % YoY |
| `housing_price` | monthly | NBS | index |
| `industrial_production` | monthly | NBS | % YoY |

### World Bank（全球，无需 key，年度数据）

支持 region: `US`, `CN`, `EU`, `JP`, `UK`, `DE`, `FR`, `IN`, `global` 等。

| indicator | code | 单位 |
|-----------|------|------|
| `gdp` | NY.GDP.MKTP.CD | USD |
| `gdp_growth` | NY.GDP.MKTP.KD.ZG | % |
| `gdp_per_capita` | NY.GDP.PCAP.CD | USD |
| `cpi` | FP.CPI.TOTL | index 2010=100 |
| `cpi_yoy` | FP.CPI.TOTL.ZG | % |
| `unemployment` | SL.UEM.TOTL.ZS | % |
| `interest_rate` | FR.INR.RINR | % |
| `population` | SP.POP.TOTL | persons |
| `trade_balance` | NE.RSB.GNFS.CD | USD |
| `fdi` | BX.KLT.DINV.CD.WD | USD |
| `exports` | NE.EXP.GNFS.CD | USD |
| `imports` | NE.IMP.GNFS.CD | USD |
| `current_account` | BN.CAB.XOKA.CD | USD |
| `gov_debt_pct_gdp` | GC.DOD.TOTL.GD.ZS | % of GDP |

---

## 四、加密资产支持

`crypto_data(identifier=...)` 支持以下输入形式：
- 大写 symbol：`BTC`, `ETH`, `SOL`, `BNB`, `USDT`, `USDC`, `XRP`, `ADA`, ... （详见 `sources/coingecko_source.py:SYMBOL_TO_ID`）
- CoinGecko 原生 id：`bitcoin`, `ethereum`, `binancecoin`, `avalanche-2`, ...

返回字段：`symbol`, `name`, `coingecko_id`, `price_usd`, `market_cap_usd`, `volume_24h_usd`, `price_change_24h_pct`, `circulating_supply`, `max_supply`, `rank`。

---

## 五、交叉验证 & 置信度评分（v1.8+）

### validate_financials 工具

```
validate_financials(identifier, period="annual", years=3)
```

输出：
- **交叉验证**：对比 2 个数据源同字段数值，偏差 >10% 标记 warning，>25% 标记 critical
- **三表勾稽**：
  - 资产负债验证：Assets > Liabilities（负权益标记）
  - 毛利合理性：Gross Profit ≤ Revenue
  - 现金流质量：OCF/NI 关系
- **异常检测**：
  - 营收环比 >50% → warning
  - 毛利率环比变动 >5pp → warning
  - OCF/NI < 0.5 持续 2 期 → critical
- **置信度**：综合评分 0.0-1.0

### 置信度评分算法

```
confidence = 0.4 × source_agreement
           + 0.2 × data_freshness
           + 0.2 × completeness
           - 0.2 × anomaly_penalty
```

| 因子 | 取值范围 | 说明 |
|------|---------|------|
| source_agreement | 0-1 | 多源一致率；单源默认 1.0 |
| data_freshness | 0.3-1.0 | 实时=1.0, 缓存=0.8, 过期=0.5 |
| completeness | 0-1 | revenue + net_income 为必要字段 |
| anomaly_penalty | 0-0.5 | 每条异常扣 0.1，上限 0.5 |

### company_financials 自动验证

`company_financials` 工具自动附加：
- `confidence` 字段：置信度评分
- `cross_validation` 字段：双源偏差分析（若多源可用）

---

## 六、Council 模式 — 对抗性审查 + 多视角分析（v1.9+）

### 设计理念

借鉴 Karpathy llm-council 三阶段架构（独立回答 → 匿名评审 → 主席仲裁），映射到商业分析场景。同一 LLM 扮演多个角色，通过对抗性审查和多视角分析提升结论可信度和分析深度。

**v1.8 解决"数据对不对"，Council 解决"结论该不该下"和"有什么没看到"。**

### 三角色

| 角色 | 职责 | L2 | L3 |
|------|------|----|----|
| **Analyst** | 标准分析流程，产出报告 | ✅ | ✅ |
| **Red Team** | 证伪结论、暴露隐性假设、找遗漏变量 | 5 项快速审查 | 7 类谬误全覆盖 |
| **Bull/Bear** | 乐观/悲观推演，显性化方向性假设 | 1-2 个关键判断 | 全覆盖 |
| **Chairman** | 仲裁分歧 | — | 事实分歧回查数据源，判断分歧不强行统一 |

### 7 类分析谬误检查

| 谬误类型 | 检查点 | L2 | L3 |
|---------|--------|----|----|
| 叙事谬误 | 是否把随机结果硬套因果？ | ✅ | ✅ |
| 锚定效应 | 是否过度依赖初始数据点？ | ✅ | ✅ |
| 确认偏误 | 是否只找支持结论的证据？ | ✅ | ✅ |
| 线性外推 | 是否假设趋势无限延续？ | ✅ | ✅ |
| 假设脆弱性 | 结论最依赖哪个未验证假设？ | ✅ | ✅ |
| 幸存者偏差 | 是否只看成功案例？ | ❌ | ✅ |
| 单一归因 | 是否用单一原因解释复杂结果？ | ❌ | ✅ |
| 范围忽视 | 是否忽略行业/阶段/地域约束？ | ❌ | ✅ |

### L3 触发拓宽

以下场景即使无"深度""尽调"等显式信号，也默认推荐 L3：行业商业建模、商业模式评估、战略选择、投资判断、竞争对手对比。

### Council 与置信度交互

| 数据置信度 | Council 结果 | 综合判断 |
|-----------|-------------|---------|
| ≥0.9 | 无分歧 | 结论可信，直接引用 |
| ≥0.9 | 有分歧 | 数据可靠但解读有争议 — 标注分歧 |
| <0.7 | 无分歧 | 数据弱但逻辑一致 — 标注数据风险 |
| <0.7 | 有分歧 | 最弱组合 — 标注双重风险 |

---

## 六、配置 API key

### 交互式（推荐）

```bash
./bin/senior_analyst-setup-keys
# 选择 1-5 选择服务；按提示粘贴 key；自动验证
```

### 命令行直接配置

```bash
./bin/senior_analyst-setup-keys --service fred       # 配置 FRED
./bin/senior_analyst-setup-keys --service fmp        # 配置 FMP
./bin/senior_analyst-setup-keys --service av         # 配置 Alpha Vantage
./bin/senior_analyst-setup-keys --service newsapi    # 配置 NewsAPI
./bin/senior_analyst-setup-keys --service coingecko  # 配置 CoinGecko Pro
```

### 查看当前状态

```bash
./bin/senior_analyst-setup-keys --list
```

### 手动配置（高级）

直接编辑 `~/.config/senior_analyst/.env`（chmod 600）：

```bash
SENIOR_ANALYST_FRED_KEY="your-fred-key"
SENIOR_ANALYST_FMP_KEY="your-fmp-key"
SENIOR_ANALYST_AV_KEY="your-av-key"
SENIOR_ANALYST_NEWSAPI_KEY="your-newsapi-key"
SENIOR_ANALYST_COINGECKO_KEY="your-coingecko-pro-key"
```

也可在项目根目录放 `.env`（优先级低于 `~/.config/senior_analyst/.env`），或直接通过 shell 环境变量传入。

---

## 七、健康自检

```bash
./bin/senior_analyst-doctor
```

输出内容：
1. 工具→源优先级矩阵
2. 每个 Tier 0 源逐个 ping 测试（latency + 数据样本）
3. 每个 Tier 1 源 key 状态（已配置则 ping 测试，未配置给出申请引导）
4. 缓存使用情况
5. 推荐下一步操作

**何时运行**：
- 首次安装后
- 数据返回异常时
- 升级后
- 用户报告"数据不准确"时（第一步）

# Senior Analyst — 商业分析专家

Claude Code 的商业分析 skill，输入 `/senior_analyst` 即可触发。

> **v1.8.0 升级要点（2026-05）**
> - **交叉验证引擎**：`company_financials` 自动双源比对，偏差 >10% 标记 discrepancy
> - **置信度评分**：每个 MCP 响应附带 0-1 置信度，基于源一致率、数据新鲜度、完整度、异常数
> - **三表勾稽验证**：`validate_financials` 新工具 — 资产负债验证 + 现金流质量 + 毛利合理性
> - **异常检测**：营收环比异常、毛利率突变、OCF/NI 持续低位自动标记
>
> **v1.7.0 升级要点**
> - **新增 2 个 MCP 工具**：`macro_data`（宏观经济）+ `crypto_data`（加密资产）
> - **5 个新数据源**：FRED / World Bank / stats_gov_cn / CoinGecko
> - **新增 CLI**：`senior_analyst-doctor` + `senior_analyst-setup-keys`
> - **港股别名扩充 30+** / **免费 key 即可工作**

## 功能

### 数据工具（MCP 服务器，自动调用）
- **company_financials** — 财务数据（营收、利润、现金流、资产负债）
- **company_profile** — 公司画像（行业、市值、PE/PS/PB）
- **competitor_compare** — 竞品对比（同行业公司财务指标）
- **market_data** — 行业数据（市场规模、增长率）
- **news_search** — 新闻搜索（公司/行业/事件相关新闻）
- **industry_data** — 行业分类与成分股（申万/东方财富行业板块）
- **stock_news** — 个股新闻与公告
- **macro_data** *(v1.7+)* — 宏观经济（GDP/CPI/PMI/失业率/利率/M2，覆盖中/美/欧/全球）
- **crypto_data** *(v1.7+)* — 加密资产（价格/市值/24h 量/流通量，CoinGecko）
- **validate_financials** *(v1.8+)* — 财务交叉验证（三表勾稽 + 异常检测 + 置信度评分）

### CLI 工具（v1.7+）
- **senior_analyst-doctor** — 数据源健康自检；显示 Tier 0/Tier 1 状态、延迟、缓存使用
- **senior_analyst-setup-keys** — 交互式 API key 配置；存储到 `~/.config/senior_analyst/.env`（chmod 600）

### 数据源分层

| Tier | 数据源 | 是否需 key | 适用范围 |
|------|--------|----------|---------|
| Tier 0 | yfinance / akshare / eastmoney / **worldbank** / **stats_gov_cn** / **coingecko** | 否 | 财务/市场/中国宏观/全球宏观/加密 |
| Tier 1 (free key) | **FRED** / Alpha Vantage / NewsAPI | 是（免费） | 美国宏观 / 全球股票 / 英文新闻 |
| Tier 1 (paid) | FMP / CoinGecko Pro | 是（付费） | 全球财报增强 / 加密高级 |

### 交叉验证 & 置信度（v1.8+）

**置信度评分**：每个 MCP 响应附带 `confidence` 字段（0.0-1.0），基于：
- 多源一致率（双源一致 → 加分，偏差 >10% → 扣分）
- 数据新鲜度（实时 > 缓存 > 过期）
- 字段完整度（revenue + net_income 为必要字段）
- 异常数量（每条扣 0.1）

| 置信度 | 含义 | 使用建议 |
|-------|------|---------|
| ≥ 0.9 | 多源一致，无异常 | 直接引用 |
| 0.7-0.89 | 单源或有小偏差 | 可引用，标注置信度 |
| 0.5-0.69 | 存在异常或大偏差 | 需补充验证 |
| < 0.5 | 数据不可信 | 不引用 |

**异常检测**：营收环比 >50%、毛利率突变 >5pp、OCF/NI <0.5 持续 2 期 → 自动标记

### 分析框架（skill 层，9 类任务）
- 指标异动诊断
- 商业模式/单位经济评估
- PMF/增长诊断
- 战略选择/规划
- 流程优化
- 财报分析/排雷
- 竞争对手对比分析
- 情景/敏感性分析
- 行业商业建模

## 行业商业建模能力

### 标准化分析框架

所有行业分析遵循统一的母模板体系，确保跨行业可比、口径一致：

**母模板体系（5 份标准参考）**
- 商业建模总模板 — 行业本质 → 价值链 → 商业模式 → 收入成本 → 核心指标 → 竞争格局 → 风险 → 财务重点 → 市场空间 → 快速分析卡
- 投资尽调总模板 — 业务理解 → 产品 → 市场 → 客户验证 → 增长运营 → 核心数据 → 财务 → 团队 → 竞争壁垒 → 风险 → 投委会输出
- 公司对比总模板 — 商业模式对比 → 市场客户 → 经营数据 → 单位经济 → 财务质量 → 产品交付 → 壁垒 → 风险 → 综合评分 → 结论
- 写作规范 — 统一结构、口径、粒度、输出标准
- 改造规则 — 旧文件迁移到母模板的统一标准

每份行业模板按母模板结构展开，包含完整的：行业定义、商业本质、价值链条、商业模式分类、收入公式、成本模型、核心指标体系（9 层分层）、竞争格局与壁垒、风险分析（含风险信号）、财务分析重点、市场空间测算、尽调问题库、快速分析卡。

### 行业覆盖（28 个行业）

| 行业 | 一句话本质 | 核心收入公式 | 关键风险 |
|------|----------|------------|---------|
| 金融 | 风险定价+杠杆经营+期限管理 | 生息资产×NIM+手续费 | 监管+信用周期+流动性 |
| 金融科技 | 监管+技术+场景三重驱动 | 交易额×费率+服务费 | 牌照+合规+政策 |
| SaaS | 持续订阅嵌入业务流程 | 客户数×ACV×续费率 | 留存<续费<扩单 |
| 电商 | 供需匹配+交易撮合+履约 | GMV×take rate | 流量成本+履约+竞争 |
| AI | 模型能力嵌入真实工作流 | 调用量×单价+订阅 | 留存弱+同质化+成本高 |
| 游戏 | 爆款概率+生命周期变现 | DAU×付费率×ARPPU | 版号+爆款失败率+买量ROI |
| 传媒广告 | 流量聚合+广告匹配+ROI | 流量×加载率×eCPM | 流量见顶+隐私+竞争 |
| 物流与供应链 | 空间效用+时间效用+规模密度 | 票量×单票收入 | 路由密度+末端成本 |
| 消费电子 | 产品定义+供应链+品牌渠道 | 销量×ASP | 存货+产品周期+渠道压货 |
| 新能源 | 政策驱动+技术降本双轮 | 装机量×单价/发电量×电价 | 政策退坡+产能过剩 |
| 半导体 | 高壁垒技术+供应链→核心器件 | 出货量×ASP | 良率+客户导入+周期性 |
| 教育 | 知识传递+能力培养+认证 | 学员数×客单价 | 政策+获客成本+续费 |
| 企业服务 | 企业效率提升+经营数字化 | 客户数×ACV×续费率 | 交付重+客户集中+标准化难 |
| 医疗健康 | 诊疗能力+药物/器械+支付 | 客户数×ACV/销量×ASP | 监管慢+回款长+采购弱 |
| 房地产 | 空间开发+资产经营+服务 | 销售额/租金收入/服务费 | 周期性+资金链+政策 |
| 汽车出行 | 出行工具+智能终端+服务生态 | 销量×ASP/订单量×客单价 | 产能周期+政策+竞争 |
| 消费 | 品牌驱动+渠道效率+供应链 | 销量×ASP | 品牌力衰减+渠道变革 |
| 本地生活 | 线下场景数字化+即时履约 | GMV×take rate+配送费 | 单城模型+履约成本 |
| 餐饮 | 食品制作+场景体验+供应链 | 门店数×单店收入 | 单店模型+食材成本+人力 |
| 旅游 | 体验交付+资源整合+信任中介 | 订单量×客单价/间夜×房价 | 季节性+突发事件+复购 |
| 文娱内容 | 内容生产+分发+IP运营 | 用户数×ARPU/IP授权收入 | 爆款不确定+版权+盗版 |
| 美妆个护 | 品牌心智+产品力+渠道触达 | 销量×ASP | 品牌衰减+成分内卷+渠道 |
| 母婴 | 人口趋势+信任链+成长周期 | 用户数×ARPU | 人口下降+信任成本+周期短 |
| 宠物 | 情感驱动+陪伴需求+消费升级 | 用户数×ARPU | 情感溢价+复购+监管 |
| 家居家装 | 空间改造+功能+审美 | 客单价×客户数 | 低频+重交付+增项失控 |
| 出海 | 本地化+合规+全球化运营 | 海外收入×区域结构 | 本地化+合规+文化差异 |
| 工业自动化 | 产线效率+成本节约+质量提升 | 部署规模×单点位价值 | 定制化+ROI验证+回款长 |
| Web3/加密经济 | 去中心化信任机制降低价值流转中介成本 | CEX:交易量×费率; 稳定币:发行量×储备收益率; DeFi:TVL×费率-代币激励 | 监管禁止+智能合约安全+代币经济不可持续 |

### 行业知识库层级

```
L1 速查卡（skill 实时输出，<5秒）
  ↓ 需要深入？
L2 精简版知识库（skill 运行时加载，5-10KB/行业，28 个行业）
  ↓ 需要完整参考？
L3 完整版行业建模（docs/industry_models/，20-80KB/行业，28 个行业）
    - 标准化商业建模（按母模板展开的完整 14 节）
    - 投资尽调模板
    - 公司对比模板
    - 行业专属增强章节与实操参考（如 Web3 的合法性矩阵、数据平台指南、CEX 操作指南）
```

完整行业建模文件位于 `docs/industry_models/` 目录，可直接用于：
- 快速了解一个行业的商业本质和分析框架
- 作为投资尽调或行业研究的标准化起点
- 跨行业横向比较（统一结构、统一口径）

### 新行业快速建模

不在模板库中的行业，用十步法从零建模：
1. 定义行业边界 → 2. 画价值链 → 3. 分模式 → 4. 拆收入 → 5. 拆成本 → 6. 找约束 → 7. 建指标树 → 8. 看规模效应 → 9. 做公司对比 → 10. 形成结论

### 投资尽调框架

三层七步尽调链路：
- **行业建模**（6 问）：空间/增速/阶段/格局/利润池/变量
- **公司建模**（8 问）：产品/客户/价值/收入/成本/单位经济/优势/规模
- **财务建模**（8 问）：增长质量/毛利/费用/OCF/资本开支/营运资本/资产质量/红旗

输出：公司商业建模卡 + 投资决策备忘录

## 安装

```bash
git clone https://github.com/rrred0324/senior-analyst.git
cd senior-analyst
./setup.sh
```

安装后重启 Claude Code。

### 手动安装

如果 `setup.sh` 不适用：

```bash
# 1. 安装 Python 依赖
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# 2. 注册 MCP 服务器
claude mcp add -s user senior_analyst ./venv/bin/python $(pwd)/server.py

# 3. 复制 skill 文件
mkdir -p ~/.claude/skills/senior_analyst
cp -r skill/* ~/.claude/skills/senior_analyst/

# 4. 重启 Claude Code
```

### 可选：配置 API Key 增强数据源

默认零 API Key 即可使用。配置以下环境变量可解锁更高质量数据源：

```bash
# FMP — 免费tier 250次/天，美股/全球财务数据最佳
export SENIOR_ANALYST_FMP_KEY="your_key"

# Alpha Vantage — 免费tier 25次/天，含新闻情绪分析
export SENIOR_ANALYST_AV_KEY="your_key"

# NewsAPI — 免费tier 100次/天，专业新闻搜索
export SENIOR_ANALYST_NEWSAPI_KEY="your_key"
```

也可在项目目录创建 `.env` 文件：

```
SENIOR_ANALYST_FMP_KEY=your_key
SENIOR_ANALYST_AV_KEY=your_key
SENIOR_ANALYST_NEWSAPI_KEY=your_key
```

## 在线升级

当 GitHub 上有新版本发布时，在 Claude Code 中直接升级：

```
/senior_analyst --upgrade
```

升级流程：
1. 从 GitHub 拉取最新代码
2. 比较版本号，如已是最新则跳过
3. 更新 skill 文件和 VERSION
4. 更新 Python 依赖和 MCP 注册
5. 重启 Claude Code 使更新生效

也可以手动升级：

```bash
cd senior-analyst    # 进入原 clone 目录
git pull
./upgrade.sh
```

查看当前版本：`/senior_analyst --version`

## 使用

### 三级深度模式

Senior Analyst 根据用户意图自动判断深度级别，从框架速览到深度报告，响应速度匹配需求：

| 深度级别 | 触发信号 | 响应时间 | 说明 |
|---------|---------|---------|------|
| **L1 框架速览** | "入门""框架""指标""概述" | <5 秒 | 直接输出行业速查卡，不触发网络请求 |
| **L2 定量分析** | 包含具体公司名/股票代码 | 10-20 秒 | MCP 必查项并行查询，按需补查 |
| **L3 深度报告** | "深度""尽调""全面" | 30-60 秒 | 完整查询序列+全流程分析 |

L1 输出后自动追问是否升级到 L2/L3，渐进式深入。

### 用法示例

```
# L1 框架速览（<5秒，无网络请求）
/senior_analyst 即时零售 入门      → 输出行业速查卡
/senior_analyst 游戏 分析框架      → 输出游戏分析框架
/senior_analyst --quick 金融行业    → 强制 L1 模式

# L2 定量分析（10-20秒，MCP 并行查询）
/senior_analyst 腾讯              → 分析腾讯
/senior_analyst 对比 滴滴 Uber     → 竞品对比
/senior_analyst 看看网易的财报      → 财报分析

# L3 深度报告（30-60秒，完整流程）
/senior_analyst 叮咚买菜投资尽调    → 全流程深度报告
/senior_analyst --deep 游戏行业     → 完整行业建模

# 行业建模模式
/senior_analyst 金融 平安          → 行业建模，分析金融行业
/senior_analyst --industry 信贷     → 显式行业建模模式

# 升级与版本
/senior_analyst --upgrade           → 在线升级到最新版本
/senior_analyst --version           → 查看当前版本

# 引导模式
/senior_analyst                    → 询问分析对象和意图
```

### L1 速查卡输出示例

行业速查卡包含：一句话本质 → 收入公式 → 子赛道拆分 → 关键指标（Top 5-8）→ 分析起点 → 行业特有风险 → 延伸方向

通用框架速查卡包含：核心问题 → 分析步骤 → 关键指标 → 常见陷阱 → 延伸方向

## 数据源

| 源 | 类型 | 覆盖 | 中国可用 | API Key | Tier |
|----|------|------|---------|---------|------|
| 东方财富 (eastmoney) | HTTP API | A 股财务、行业板块、新闻 | ✅ | 无 | 0 |
| akshare | Python 库 | A 股、港股、宏观、行业 | ✅ | 无 | 0 |
| yfinance | Python 库 | 美股、港股、全球市场 | ❌ 大陆不可用 | 无 | 0 |
| **stats_gov_cn** *(v1.7)* | Python 库 | 中国 NBS / PBOC / 海关宏观 | ✅ | 无 | 0 |
| **World Bank** *(v1.7)* | REST API | 全球 200+ 国家宏观（年度） | ✅ | 无 | 0 |
| **CoinGecko** *(v1.7)* | REST API | 加密资产价格、市值、量 | ✅ | 无（Pro 可选） | 0 |
| **FRED** *(v1.7)* | REST API | 美国宏观（高频，GDP/CPI/利率） | ✅ | **免费 key** | 1 |
| FMP | REST API | 美股/全球财务、同行、行业 | ✅ | 付费 | 1 |
| Alpha Vantage | REST API | 财务、估值、新闻情绪 | ✅ | 免费 key | 1 |
| NewsAPI | REST API | 专业新闻搜索（中英文） | ✅ | 免费 key | 1 |

默认降级链（零 API Key）：**eastmoney → akshare → yfinance**

宏观降级链：**FRED（美/有 key）→ stats_gov_cn（中）→ World Bank（其他/兜底）**

新闻搜索降级链：**NewsAPI（可选）→ akshare → 东方财富搜索 API → Alpha Vantage（可选）**

## 健康自检 & API key 配置（v1.7+）

```bash
# 一键自检所有数据源
./bin/senior_analyst-doctor

# 交互式配置 API key（推荐配 FRED）
./bin/senior_analyst-setup-keys

# 直接配置单个服务
./bin/senior_analyst-setup-keys --service fred

# 仅显示当前 key 状态
./bin/senior_analyst-setup-keys --list
```

key 存储在 `~/.config/senior_analyst/.env`（chmod 600）。配置后需重启 Claude Code 让 MCP server 重新读取。

## 要求

- Python 3.10+
- Claude Code CLI
- 零 API Key 即可使用基础功能

## License

MIT

# Web3 公开数据平台使用指南

> 适用对象：Web3 行业研究者、投资分析师、链上数据分析师、开发者
> 更新日期：2026-05

---

## 一、平台全景概览

| 平台 | 核心定位 | 数据类型 | 技术门槛 | 定价模式 | 适合谁 |
|------|---------|---------|---------|---------|-------|
| **Dune** | 链上SQL查询+可视化 | 原始链上数据+解码数据 | 中（需SQL） | Freemium（免费起步） | 数据分析师、研究员 |
| **Nansen** | 聪明钱追踪+地址标签 | 地址行为+标签+资金流 | 低（UI驱动） | 付费为主 | 交易者、投资研究员 |
| **Flipside** | 企业级链上分析+AI Agent | 精选链上数据+AI | 低-中 | 企业级（联系销售） | 企业团队、专业分析师 |
| **Etherscan** | 区块浏览器 | 交易/合约/地址原始数据 | 低（UI查询） | Freemium（API付费） | 所有人（入门必用） |
| **DefiLlama** | DeFi TVL+收益+费用 | 协议级聚合数据 | 低（UI+API） | 免费+高级订阅 | DeFi研究者、投资者 |
| **Token Terminal** | 加密项目财务指标 | 传统财务指标映射 | 低-中 | Freemium | 投资分析师、VC |
| **The Graph** | 链上数据索引协议 | 结构化链上索引 | 高（需开发） | 按查询量付费 | 开发者、dApp团队 |

### 数据层级关系

```
原始链上数据（Etherscan等浏览器）
    ↓ 索引/解码
结构化索引（The Graph）
    ↓ 聚合/建模
聚合数据层（Dune / Flipside）
    ↓ 标签/分析
标签+行为数据（Nansen）
    ↓ 财务化
财务指标层（Token Terminal / DefiLlama）
```

---

## 二、Dune — 链上数据SQL查询平台

### 2.1 是什么

Dune 是一个**链上数据查询与可视化平台**，用户用 SQL 直接查询 100+ 条区块链的原始数据和解码数据，并将结果制作成可视化仪表盘。核心价值：**让任何人都能像查数据库一样查链上数据**。

已索引 100+ 条链、3+ PB 数据、拥有 200K+ 公开仪表盘。

### 2.2 核心产品线

| 产品 | 用途 | 用户 |
|------|------|------|
| **Data Hub** | Web版SQL编辑器+仪表盘构建器 | 分析师 |
| **Spellbook** | 社区驱动的数据建模层（Web3版dbt） | 分析师 |
| **API** | 程序化访问查询结果 | 开发者 |
| **Sim** | 亚秒级延迟API（余额/交易/DeFi仓位） | dApp开发者 |
| **Catalyst** | 链/基金会数据分发工具 | 链团队 |
| **Datashare** | 数据流至Snowflake/BigQuery/Databricks | 数据团队 |
| **MCP** | AI Agent通过MCP协议访问Dune数据 | AI开发者 |

### 2.3 支持的主要链

| 链 | 查询数 | 仪表盘数 | 数据集数 |
|----|-------|---------|---------|
| Ethereum | 45K+ | 93K+ | 312K+ |
| Arbitrum | 12K+ | 23K+ | 112K+ |
| Polygon | 10K+ | 22K+ | 86K+ |
| BNB Chain | 9K+ | 25K+ | 82K+ |
| Base | 8K+ | 11K+ | 78K+ |
| Optimism | 8K+ | 31K+ | 86K+ |
| Solana | 5K+ | 11K+ | 58K+ |
| Bitcoin | 1K+ | 3K+ | 16K+ |

另有：Avalanche, ZKsync, Scroll, Linea, Sui, TON, Monad, Tron, Cosmos, Near, Aptos 等数十条链。

### 2.4 定价

| | Free | Analyst | Plus | Enterprise |
|---|---|---|---|---|
| **月费（年付）** | $0 | $65/mo | $349/mo | Custom |
| **Credits/月** | 2,500 | 4,000 | 25,000 | 100,000+ |
| **Seats** | 1 | 3 | 10 | Unlimited |
| **角色管理** | Admin | Admin | Admin/Editor/Viewer | 自定义 |
| **数据存储** | 100 MB | 1 GB | 15 GB | 200 GB+ |
| **并发SQL查询** | 1 | 1 | 3 | Custom |
| **查询超时** | 2分钟 | 30分钟 | 30分钟 | Custom |
| **API调用/分钟** | 20 | 40 | 200 | Custom |
| **私有查询** | -- | -- | 30 | Custom |
| **私有仪表盘** | -- | -- | 5 | Custom |
| **计划查询过期** | 3个月后 | 3个月后 | 不过期 | 不过期 |
| **CSV导出** | -- | -- | 支持 | 支持 |
| **AI功能** | 10 credits/动作 | 10 credits/动作 | 10 credits/动作 | 10 credits/动作 |

**查询引擎级别**：
- **Small**：120s超时，1x计算，标准队列（~3.27 credits）
- **Medium**：延长超时，1x计算，优先队列（仅付费，~8.46 credits）
- **Large**：延长超时，2x计算，优先队列（仅付费，~18.72 credits）

### 2.5 免费用户能做什么

- 访问所有链上数据（100+链，无限制）
- 创建无限查询和公开仪表盘
- 使用Dune MCP和API
- 创建物化视图（Materialized Views）
- 上传自定义数据
- AI功能（10 credits/动作）
- 1个Alert

### 2.6 免费用户不能做什么

- 私有查询/仪表盘
- 超过2分钟超时的查询
- Medium/Large引擎
- CSV导出
- 团队协作空间
- 不过期的计划查询

### 2.7 典型使用场景

**场景1：查询某协议的日活用户**
```sql
SELECT
  block_date,
  COUNT(DISTINCT from) AS active_users
FROM dex.trades
WHERE project = 'uniswap'
  AND block_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY block_date
ORDER BY block_date
```

**场景2：追踪巨鲸地址持仓变化**
```sql
SELECT
  block_time,
  token_symbol,
  amount_usd
FROM erc20.token_transfers
WHERE "from" = 0x...目标地址
   OR "to" = 0x...目标地址
ORDER BY block_time DESC
LIMIT 100
```

**场景3：监控某链DEX交易量趋势**
- 搜索现有仪表盘 → fork到自己账户 → 修改查询条件 → 设定Alert

### 2.8 新手上手步骤

```
1. 注册 dune.com（GitHub/Google登录）
2. 浏览热门仪表盘，理解数据呈现方式
3. Fork一个现有仪表盘到自己账户
4. 修改SQL查询，观察结果变化
5. 尝试创建自己的查询和图表
6. 组合多个查询为一个仪表盘
7. 设置Alert，定期监控关键指标
```

### 2.9 与其他平台的关系

- **Dune vs Flipside**：Dune偏SQL查询自由度，Flipside偏精选数据+AI+赏金
- **Dune vs Nansen**：Dune无地址标签，需自己写SQL；Nansen有标签但不可自定义查询
- **Dune vs Etherscan**：Dune做聚合分析；Etherscan查单笔交易/合约

---

## 三、Nansen — 聪明钱追踪与链上交易平台

### 3.1 是什么

Nansen 是**链上地址标签+聪明钱追踪+交易执行平台**。2026年定位为"Agentic Trading with Onchain Intelligence"，核心价值在于对 5亿+ 地址进行标签分类（如"Jump Crypto""三箭资本""MEV Bot"等），让用户能追踪"聪明钱"的实时操作，并可直接在平台内执行交易。

成立2020年，总部新加坡，创始人Alex Svanevik和Lars Roug。累计融资约$88M（A+B轮），投资方包括a16z和Tiger Global。

**重要趋势**：Nansen正从"纯分析"向"分析+交易"转型——内置非托管钱包，集成Jupiter/OKX/LI.FI聚合路由，实现"信号到交易"闭环。

### 3.2 核心功能

| 功能 | 说明 | 价值 |
|------|------|------|
| **Smart Money追踪** | 追踪5亿+标注地址的实时操作 | 发现早期趋势 |
| **地址标签** | 基金、交易所、MEV Bot、VC等分类标签 | 识别交易对手 |
| **钱包画像** | 输入地址查看持仓、历史PnL、风险评分 | 尽调工具 |
| **链上交易** | 内置非托管钱包（Privy），聚合Jupiter/OKX/LI.FI路由 | 信号到交易闭环 |
| **Token God Mode** | 单一代币的全链路数据（持有者、交易流） | 代币深度研究 |
| **组合追踪** | 跨链组合监控，实时PnL和风险评分 | 资产管理 |
| **AI研究助手** | 24/7 AI驱动的链上研究，可提问+执行 | 效率提升 |
| **研究报吿** | 团队产出的链上研究报告 | 行业洞察 |
| **NXP积分** | 使用平台获得积分，解锁奖励和特权 | 激励体系 |
| **NFT追踪** | NFT项目持有者分析、鲸鱼追踪 | NFT交易参考 |

### 3.3 定价

Nansen 采用付费订阅模式，免费功能极其有限：

| 层级 | 参考月费 | 核心能力 |
|------|---------|---------|
| **Free** | $0 | Solana免费探索；基础钱包查看；延迟的Smart Money数据 |
| **Pioneer** | ~$150/mo | 实时Smart Money标签、Token分析、多链支持 |
| **VIP** | ~$1,000/mo | 全部标签、研究报吿、API访问、高级画像、AI研究 |
| **Alpha/Enterprise** | 定制 | 全API、定制研究、团队功能 |

> 年付有折扣。Solana链数据免费开放。具体价格以 app.nansen.ai/account/switch-plans 为准。

### 3.4 支持的链

40+ 条链，包括：
- **EVM系**：Ethereum, Base, Arbitrum, Optimism, Polygon, BSC, Avalanche, Fantom, Celo
- **非EVM**：Solana（免费重点推广）
- **L2新链**：zkSync, Linea, Scroll, Blast, Mode, Mantle, Merlin 等

### 3.5 免费用户 vs 付费用户

| 功能 | Free | Paid |
|------|------|------|
| Solana钱包/代币追踪 | 免费开放 | 支持 |
| Smart Money标签（受限） | 部分展示/有延迟 | 全量实时 |
| 链上交易 | 受限 | 支持 |
| 跨链分析 | 仅Solana免费 | 全链支持 |
| 研究报吿 | 不可 | VIP+ |
| API访问 | 不可 | VIP+ |
| AI研究助手 | 受限 | 完整功能 |
| 钱包画像 | 基础查看 | 完整PnL画像 |

### 3.6 典型使用场景

**场景1：发现聪明钱买入的新代币**
```
Smart Money → Token → 查看最近7天聪明钱净买入排名
→ 发现某代币聪明钱集中买入
→ 进一步查看持仓分布和交易流
→ 在Nansen内直接执行交易
```

**场景2：分析某地址身份**
```
输入地址 → Nansen标签识别
→ "这是Jump Trading的热钱包"
→ 查看其持仓、PnL和近期操作
```

**场景3：空投 farming 研判**
```
查找Smart Money资金流入的协议
→ 判断哪些协议可能有空投
→ 提前布局交互
```

**场景4：组合风险监控**
```
Portfolio → 输入自己的多链地址
→ 查看跨链组合总览
→ 风险评分和集中度分析
```

### 3.7 与Dune的关键差异

| 维度 | Nansen | Dune |
|------|--------|------|
| **标签数据** | 5亿+地址标签，核心壁垒 | 无标签系统 |
| **查询自由度** | 预设界面，不可自定义SQL | 完全自定义SQL |
| **上手门槛** | 低（UI驱动） | 中（需SQL） |
| **价格** | 较贵（$150+/mo起步） | 免费起步 |
| **数据深度** | 标签+行为，侧重"谁在做什么" | 原始数据，侧重"发生了什么" |
| **交易执行** | 内置钱包+聚合路由，可交易 | 无交易功能 |
| **适用场景** | 聪明钱跟单、地址识别、交易 | 自定义分析、协议监控 |

---

## 四、Flipside — 企业级链上分析+AI Agent平台

### 4.1 是什么

Flipside 是一个**企业级链上数据分析平台**，由PhD数据科学团队精选和标准化链上数据，并提供AI Agent能力。成立于2017年，8年数据标准化经验。

**重要变化**：Flipside 在2025-2026年间完成战略转型，从社区驱动的赏金平台转向**企业级数据+AI Agent公司**。旧的赏金计划（Bounty Program）和FLIP代币奖励已被弱化或取消，新定位为"Enterprise-grade blockchain data curated by PhD data scientists" + "Agents-as-a-Service"。

核心差异化：
1. **精选数据（Curated Data）**：PhD数据科学团队预建模和标准化，数据质量更高
2. **AI Agent基础设施**：Agents-as-a-Service，可嵌入工作流
3. **MCP原生集成**：支持Claude Code、Cursor、GitHub Copilot、Windsurf等IDE

### 4.2 核心功能（Flipspace Platform）

| 功能 | 说明 |
|------|------|
| **Data Explorer** | 可视化数据浏览，支持SQL查询 30+链 |
| **AI Chat** | 自然语言提问，AI生成查询和图表 |
| **Specialized Agents** | 专业化AI Agent（DeFi分析、异常检测、dbt管道生成） |
| **AI Automations** | 自动化数据监控和告警（确定性执行） |
| **Reports** | 分析报告生成和团队分享 |
| **Predictive Scoring** | 统计模型，日评分数亿实体 |
| **Labels & Tags** | 7亿+地址标签 |
| **Snowflake Data Shares** | 企业级数据共享（无需自建仓库） |
| **MCP Integration** | 从CLI/IDE查询数据和运行Agent |
| **API Access** | 程序化数据访问 |
| **Slack Integration** | 团队工作流中的自定义Bot |

### 4.3 支持的链

30+ 条链，包括：Ethereum, Solana, Bitcoin, Base, Tron, BSC, Arbitrum, Optimism, Polygon, Avalanche, HyperCore, HyperEVM 等。

特色数据集：
- **跨链查询**：11条链统一SQL查询
- **稳定币**：213种稳定币，36条链
- **余额**：每条链上每个钱包的余额

### 4.4 定价

Flipside 采用**企业级销售模式**，无公开自助定价。

| 层级 | 价格 | 能力 |
|------|------|------|
| **Enterprise Data** | 联系销售 | Snowflake数据访问、API、精选数据 |
| **Agents-as-a-Service** | 联系销售 | AI Agent订阅、MCP集成 |
| **Custom Solutions** | 联系销售 | 定制化数据+Agent方案 |

> 访问 flipsidecrypto.xyz/request-demo/ 申请演示。旧版免费社区层已不对外开放。

### 4.5 Flipside vs Dune 关键差异

| 维度 | Flipside | Dune |
|------|----------|------|
| **定位** | 企业优先，销售驱动 | 社区优先，自助服务 |
| **定价** | 企业级（联系销售） | Free + 付费层（$65-$349/mo） |
| **数据质量** | PhD科学家精选标准化 | 社区解码，原始+精选混合 |
| **AI/Agent** | 核心产品：Agents-as-a-Service | AI查询助手（辅助功能） |
| **数据交付** | Snowflake仓库、Data Share | API、Datashare、dbt连接器 |
| **社区模式** | 赏金已弱化，转向企业 | 200K+仪表盘，6.5M+查询 |
| **MCP/CLI** | 原生集成Claude Code/Cursor/Copilot | API优先 |
| **链覆盖** | 30+链 | 100+链 |
| **地址标签** | 7亿+标签 | 无标签系统 |

### 4.6 典型使用场景

**场景1：机构级链上监控**
- 银行/基金合规团队通过Flipside Agent自动监控链上异常交易

**场景2：AI Agent嵌入工作流**
- 通过MCP在Claude Code/Cursor中直接查询链上数据，无需切换平台

**场景3：跨链统一分析**
- 一个SQL查询同时覆盖11条链，无需逐链分析

**场景4：企业数据仓库集成**
- 通过Snowflake Data Shares将Flipside数据接入内部BI系统

---

## 五、Etherscan — 区块浏览器

### 5.1 是什么

Etherscan 是**以太坊区块浏览器**，Web3最基础的数据查询工具。核心功能：查看交易详情、合约代码、地址余额、代币信息、Gas费用等。是所有链上数据查询的起点。

### 5.2 核心功能

| 功能 | 说明 | 使用场景 |
|------|------|---------|
| **交易查询** | 输入tx hash查看交易详情 | 确认转账状态 |
| **地址查询** | 输入地址查看余额、代币、交易历史 | 钱包审计 |
| **合约验证** | 查看合约源码和ABI | 合约审计 |
| **代币追踪** | ERC-20/ERC-721/ERC-1155代币信息 | 代币研究 |
| **Gas Tracker** | 实时Gas费用估算 | 交易时机 |
| **Input Data Decoder** | 解码交易输入数据 | 理解交易行为 |
| **标签** | 地址标签（交易所、DeFi协议等） | 识别交易对手 |
| **API** | 程序化访问链上数据 | 开发集成 |

### 5.3 同系浏览器

Etherscan 团队运营多链浏览器：

| 浏览器 | 链 | 网址 |
|--------|-----|------|
| Etherscan | Ethereum | etherscan.io |
| BscScan | BNB Smart Chain | bscscan.com |
| Polygonscan | Polygon | polygonscan.com |
| SnowTrace | Avalanche | snowtrace.io |
| ArbScan | Arbitrum | arbiscan.io |
| OpScan | Optimism | optimisticscan.io |
| BaseScan | Base | basescan.org |

> 习惯：查哪条链就用对应的 Scan，接口和用法完全一致。

### 5.4 API定价

| 层级 | 月费 | 调用速率 | 日调用量 | Pro端点 | 地址元数据 |
|------|------|---------|---------|---------|-----------|
| **Free** | $0 | 3次/秒 | 100,000 | 部分 | -- |
| **Lite** | $49/mo | 5次/秒 | 100,000 | -- | -- |
| **Standard** | $199/mo | 10次/秒 | 200,000 | 支持 | -- |
| **Advanced** | $299/mo | 20次/秒 | 500,000 | 支持 | -- |
| **Professional** | $399/mo | 30次/秒 | 1,000,000 | 支持 | -- |
| **Pro Plus** | $899/mo | 30次/秒 | 1,500,000 | 支持 | 支持 |
| **Enterprise** | 定制 | 不限 | 不限 | 支持 | 支持 |

年付约85折，季付约9折。

### 5.5 典型使用场景

**场景1：确认一笔交易是否成功**
```
复制交易哈希 → 粘贴到Etherscan搜索栏
→ 查看 Status: Success / Fail
→ 查看 Gas Used、Block Number、Timestamp
```

**场景2：查看合约是否开源**
```
搜索合约地址 → Contract标签页
→ 绿色 = 已验证（可看源码）
→ 灰色 = 未验证（只能看字节码）
```

**场景3：查看某地址持有的代币**
```
搜索地址 → Token Holdings标签页
→ 列出所有ERC-20/ERC-721代币及余额
```

**场景4：使用API监控大额转账**
```python
import requests

# 查询某地址最新交易
url = "https://api.etherscan.io/api"
params = {
    "module": "account",
    "action": "txlist",
    "address": "0x...",
    "sort": "desc",
    "apikey": "YOUR_API_KEY"
}
response = requests.get(url, params=params)
```

### 5.6 Etherscan与其他平台的关系

Etherscan 是**最底层的原始数据源**，其他平台（Dune/Nansen/DefiLlama）的数据本质上都来自节点/浏览器这类原始数据源。区别：
- Etherscan：查**单笔交易/单地址/单合约**
- Dune：查**批量聚合数据**
- Nansen：在Etherscan数据基础上加**标签层**
- DefiLlama：在Etherscan数据基础上做**协议级聚合**

---

## 六、DefiLlama — DeFi数据聚合平台

### 6.1 是什么

DefiLlama 是**DeFi领域最全面的数据聚合平台**，核心追踪指标是TVL（Total Value Locked，总锁仓量），同时提供费用收入、DEX交易量、收益率、稳定币市值、RWA等多维度数据。最大优势：**免费、全面、更新快**。

当前DeFi总TVL约 $856亿，覆盖 3000+ 协议。

### 6.2 核心功能模块

| 模块 | 网址路径 | 数据内容 |
|------|---------|---------|
| **TVL Dashboard** | / | 各链/协议TVL及变化 |
| **Chains** | /chains | 各链TVL排名 |
| **Yields** | /yields | DeFi收益率池（APY/APR） |
| **Stablecoins** | /stablecoins | 稳定币市值、流通量、链分布 |
| **RWA** | /rwa | 真实世界资产代币化数据 |
| **Fees** | /fees | 协议费用收入排名 |
| **DEXs Volume** | /dexs | DEX交易量排名 |
| **ETF Inflows** | /etfs | BTC/ETH ETF资金流入流出 |
| **Unlocks** | /unlocks | 代币解锁日程 |
| **Protocol** | /protocol/xxx | 单协议深度数据 |
| **Metrics** | /metrics | 自定义指标看板 |
| **Tools** | /tools | 工具集（链比较等） |

### 6.3 协议排名维度

DefiLlama 的协议排名表支持 45+ 列指标，核心维度：

| 维度 | 指标 |
|------|------|
| **规模** | TVL、1d/7d/30d变化率 |
| **收入** | Fees 24h/7d/30d/1Y、Revenue 24h/7d/30d/1Y |
| **估值** | Market Cap、Mcap/TVL、P/F（Price/Fees）、P/S（Price/Revenue） |
| **盈利** | Earnings 24h/7d/30d/1Y |
| **激励** | Incentives（代币激励支出） |
| **交易** | Spot Volume 24h/7d |
| **累计** | Cumulative Fees/Revenue/Earnings |

### 6.4 附加工具

| 工具 | 说明 |
|------|------|
| **LlamaSwap** | DEX聚合器，零手续费兑换 |
| **LlamaSearch** | 查找项目官方链接（防钓鱼） |
| **LlamaFeed** | 加密信息流 |
| **LlamaAI** | AI驱动的DeFi数据问答 |
| **Custom Dashboards** | 自定义仪表盘（Premium） |
| **Sheets** | Google Sheets插件（Premium） |
| **API** | 免费API，访问所有数据 |
| **MCP** | Model Context Protocol，AI Agent可接入 |

### 6.5 定价

**重要变化**：DefiLlama与Token Terminal已深度整合，高级功能共享Token Terminal的付费体系。

| 层级 | 价格 | 能力 |
|------|------|------|
| **Free** | $0 | 所有核心数据（TVL/Fees/Yields/Stablecoins等）、3个自定义仪表盘、Sheets/Excel插件、MCP、CSV导出、团队访问 |
| **Pro** | $350/mo | 无限自定义仪表盘 |
| **API** | 定制 | REST API（250K请求/日）、Python/TypeScript SDK、状态页、创业公司折扣 |
| **Data Room** | 定制 | 原始链上数据、BigQuery/Snowflake共享、专属SLA支持 |

> DefiLlama核心浏览数据完全免费。Premium主要为自定义仪表盘、API和高级下载功能。

### 6.6 典型使用场景

**场景1：比较Lido vs Aave vs Maker的TVL趋势**
```
首页 → 搜索Lido/Aave/Sky → 查看TVL走势图
→ 切换1d/7d/30d/1Y时间范围
→ 对比Mcap/TVL估值倍数
```

**场景2：寻找高APY的流动性池**
```
Yields → 筛选链/协议/TVL范围
→ 按APY排序
→ 查看池子详情（TVL、7d趋势、风险等级）
```

**场景3：追踪稳定币市场格局**
```
Stablecoins → 查看USDT/USDC/DAI市值
→ 查看各链分布
→ 查看供应量变化趋势
```

**场景4：通过API获取协议数据**
```bash
# 获取Aave协议数据
curl https://api.llama.fi/protocol/aave

# 获取所有链TVL
curl https://api.llama.fi/v2/chains
```

### 6.7 DefiLlama的独特价值

1. **免费+全面**：核心数据全免费，覆盖面最广
2. **社区驱动**：开源项目，社区贡献协议适配
3. **中立性**：不做交易，不推项目，纯数据
4. **更新速度**：新协议通常1-2天内被收录
5. **API免费**：所有数据可通过API免费获取

---

## 七、Token Terminal — 加密项目财务指标平台

### 7.1 是什么

Token Terminal 是**将传统金融分析方法论映射到加密项目的数据平台**，核心价值：用传统金融指标（P/S、P/E、Revenue、Earnings等）评估加密协议，让传统投资者能"看懂"加密项目。

**重要变化**：Token Terminal与DefiLlama已深度整合，共享付费基础设施。DefiLlama的Pro/API/Data Room定价实际由Token Terminal体系支撑。两个平台在数据层面互补——DefiLlama擅长DeFi原生指标（TVL/Yields），Token Terminal擅长传统财务指标（P/S/P/E/Earnings）。

### 7.2 核心指标体系

| 类别 | 指标 | 说明 |
|------|------|------|
| **收入** | Revenue, Fees | 协议收入和费用 |
| **盈利** | Earnings, Net Income | 扣除成本后的利润 |
| **估值** | P/S, P/E, P/TVL | 市销率、市盈率、TVL倍数 |
| **用户** | DAU/MAU, Transaction Count | 活跃用户和交易量 |
| **链上** | TVL, Staking Rate | 锁仓量和质押率 |
| **代币** | Supply, Market Cap, FDV | 供应量和估值 |
| **治理** | Proposal Count, Voter Participation | 治理活跃度 |

### 7.3 定价

| 层级 | 月费 | 核心能力 |
|------|------|---------|
| **Free** | $0 | 全历史数据、3个自定义仪表盘、Sheets/Excel插件、MCP、CSV导出、团队访问 |
| **Pro** | $350/mo | 无限自定义仪表盘 |
| **API** | 定制 | REST API（250K请求/日）、状态页、创业公司折扣 |
| **Data Room** | 定制 | 全部API功能 + 原始链上数据 + BigQuery/Snowflake共享 + 专属SLA |

### 7.4 Token Terminal的独特价值

1. **传统财务框架**：P/S、P/E、Earnings等指标，传统投资者直接可用
2. **跨项目对比**：同赛道协议的标准化对比
3. **Sheets/Excel插件**：直接在Excel/Google Sheets中拉取数据
4. **MCP支持**：AI Agent可通过MCP协议访问数据
5. **全历史数据**：Free层即可访问完整历史

### 7.5 典型使用场景

**场景1：比较L1链的估值**
```
Dashboard → Layer 1s → 按P/S排序
→ 查看Ethereum/Solana/Avalanche的P/S对比
→ 判断哪条链"更贵"
```

**场景2：追踪某协议的收入趋势**
```
搜索Uniswap → Revenue标签
→ 查看月度/季度收入变化
→ 对比费用（Fees）vs 收入（Revenue）的差距
```

**场景3：在Excel中做加密投资分析**
```
安装Token Terminal Excel插件
→ 使用函数拉取数据：=TT_REVENUE("uniswap", "2025-01")
→ 在Excel中构建自己的估值模型
```

### 7.6 与DefiLlama的差异

| 维度 | Token Terminal | DefiLlama |
|------|---------------|-----------|
| **方法论** | 传统财务指标映射 | DeFi原生指标（TVL为主） |
| **核心指标** | P/S, P/E, Earnings | TVL, Fees, Volume |
| **免费层** | 3个仪表盘 | 几乎全免费 |
| **Excel集成** | 原生插件 | Sheets插件（Premium） |
| **受众** | 传统投资者、VC | DeFi研究者、散户 |
| **覆盖面** | 精选项目 | 3000+协议（更广） |

---

## 八、The Graph — 链上数据索引协议

### 8.1 是什么

The Graph 是一个**去中心化的链上数据索引协议**，核心功能：让开发者通过GraphQL API高效查询链上数据，而无需自己运行节点或构建索引。它是Web3数据基础设施层，很多dApp（如Uniswap、Aave）的前端数据查询都依赖The Graph。

### 8.2 核心概念

| 概念 | 说明 |
|------|------|
| **Subgraph** | 开发者定义的数据索引规则（即"怎么从链上提取什么数据"），类似数据库的索引 |
| **Indexer** | 运行节点、索引数据、响应查询的参与者，质押GRT获得查询费用 |
| **Curator** | 质押GRT为优质Subgraph发信号，引导Indexer去索引 |
| **Delegator** | 将GRT委托给Indexer，分享查询收益 |
| **GRT** | The Graph的原生代币，用于质押、支付查询费用 |
| **Substreams** | 高性能数据流处理，比Subgraph更快更灵活 |
| **Token API** | 即时代币数据API（余额、价格等），无需构建Subgraph |

### 8.3 工作原理

```
区块链原始数据
    ↓ Subgraph定义索引规则
Indexer节点（运行索引）
    ↓ GraphQL API
dApp / 开发者（查询数据）
    ↓ 支付GRT查询费
Indexer（获得激励）
```

### 8.4 The Graph在数据栈中的位置

```
Layer 4: 应用层（Uniswap前端、钱包App）
    ↑ 查询
Layer 3: 索引层（The Graph / 自建索引）  ← The Graph在这里
    ↑ 读取
Layer 2: 节点层（Alchemy / Infura / 自建节点）
    ↑ 同步
Layer 1: 区块链（Ethereum / BSC / Polygon等）
```

**关键理解**：The Graph 是Dune/Nansen/DefiLlama等分析平台的**底层基础设施之一**，但定位不同——The Graph服务开发者构建dApp，Dune等服务平台用户做分析。

### 8.5 定价

| 方案 | 价格 | 能力 |
|------|------|------|
| **Free Plan** | $0 | 100,000次/月免费查询，Subgraph Studio测试 |
| **Growth Plan** | 按量付费 | 含Free Plan额度 + 超额部分按量计费 |

**付费方式**：
- 信用卡（Stripe月结）
- GRT代币（需在Arbitrum上持有GRT + ETH做Gas）
- 可预付多月，按实际使用扣费，余额可随时提回

### 8.6 典型使用场景

**场景1：开发者构建dApp数据查询**
```graphql
# 查询Uniswap V3的交易对信息
{
  pools(orderBy: totalValueLockedUSD, orderDirection: desc, first: 10) {
    id
    token0 { symbol }
    token1 { symbol }
    totalValueLockedUSD
    volumeUSD
  }
}
```

**场景2：部署自定义Subgraph**
```
1. 编写subgraph.yaml（定义数据源和事件监听）
2. 编写schema.graphql（定义数据结构）
3. 编写mapping.ts（定义事件处理逻辑）
4. 部署到Subgraph Studio
5. 测试查询
6. 发布到主网
```

**场景3：作为Indexer参与网络**
```
1. 质押GRT代币
2. 运行Indexer节点
3. 选择要索引的Subgraph
4. 响应查询请求
5. 赚取查询费用
```

### 8.7 The Graph vs Dune 的关键差异

| 维度 | The Graph | Dune |
|------|-----------|------|
| **用户** | 开发者 | 分析师 |
| **查询语言** | GraphQL | SQL |
| **用途** | 构建dApp后端 | 链上数据分析 |
| **数据模型** | 自定义Subgraph | 预建数据表 |
| **部署** | 需要编写和部署Subgraph | 直接写SQL查询 |
| **延迟** | 亚秒级（实时索引） | 分钟级（批量查询） |
| **定位** | 基础设施 | 分析工具 |

---

## 九、平台选择决策树

```
你的需求是什么？
│
├─ 查单笔交易/地址/合约 → Etherscan（免费）
│
├─ 查DeFi协议TVL/费用/收益率 → DefiLlama（免费）
│
├─ 查加密项目财务估值指标 → Token Terminal / DefiLlama Pro（免费起步）
│
├─ 追踪聪明钱/地址标签 → Nansen（付费，$150+/mo）
│
├─ 自定义链上数据分析
│   ├─ 会SQL → Dune（免费起步，$0-349/mo）
│   ├─ 不会SQL → DefiLlama LlamaAI / Dune AI（免费/低价）
│   ├─ 需要企业级数据+AI Agent → Flipside（联系销售）
│   └─ 需要数据仓库集成 → Dune Datashare / Flipside Snowflake
│
├─ 构建dApp数据查询 → The Graph
│
└─ 不确定 → 先用Etherscan + DefiLlama（免费+低门槛）
```

---

## 十、平台组合使用策略

### 10.1 入门组合（零成本）

| 场景 | 工具 | 操作 |
|------|------|------|
| 确认交易状态 | Etherscan | 搜索交易哈希 |
| 查看协议TVL | DefiLlama | 浏览协议排名 |
| 查看Gas费用 | Etherscan Gas Tracker | 实时估算 |
| 搜索链上数据 | Dune Free | 写SQL查询 |
| 查稳定币市场 | DefiLlama Stablecoins | 市值/分布 |
| 查DeFi收益率 | DefiLlama Yields | 按APY排序 |

### 10.2 研究组合（月费 ~$65-350）

| 场景 | 工具 | 操作 |
|------|------|------|
| 协议财务分析 | Token Terminal Free / DefiLlama | 查P/S、Revenue、Fees |
| 聪明钱追踪 | Nansen Pioneer ($150/mo) | 看Smart Money操作 |
| 自定义分析 | Dune Analyst ($65/mo) | SQL查询+团队协作 |
| DeFi深度研究 | DefiLlama + Token Terminal | 交叉验证数据 |

### 10.3 专业组合（月费 $500+）

| 场景 | 工具 | 操作 |
|------|------|------|
| 全链路研究 | Nansen VIP ($1K/mo) + Dune Plus ($349/mo) | 标签+自定义查询+交易 |
| 投资决策 | DefiLlama Pro / Token Terminal Pro ($350/mo) | 估值模型+仪表盘+API |
| 开发集成 | The Graph + Etherscan API ($199/mo) | 索引+原始数据 |
| 企业级数据 | Dune Enterprise / Flipside | 数据仓库+AI Agent |
| AI驱动分析 | Flipside MCP + Dune MCP | 从IDE直接查询链上数据 |

---

## 十一、关键概念速查

| 概念 | 含义 | 在哪个平台看 |
|------|------|------------|
| **TVL** | Total Value Locked，协议锁仓总价值 | DefiLlama |
| **Fees** | 用户使用协议支付的总费用 | DefiLlama, Token Terminal |
| **Revenue** | 协议实际获得的收入（Fees的子集） | DefiLlama, Token Terminal |
| **Earnings** | Revenue - 代币激励 - 运营成本 | DefiLlama, Token Terminal |
| **P/S** | Price/Sales，市值/年收入 | Token Terminal |
| **P/F** | Price/Fees，市值/年费用 | DefiLlama, Token Terminal |
| **Mcap/TVL** | 市值/TVL比值 | DefiLlama |
| **APY** | Annual Percentage Yield，年化收益率 | DefiLlama Yields |
| **Smart Money** | 聪明钱，指业绩优秀的交易者/机构 | Nansen |
| **Subgraph** | 链上数据索引定义 | The Graph |
| **Spellbook** | Dune的数据建模层（Web3版dbt） | Dune |
| **MCP** | Model Context Protocol，AI Agent接入协议 | Dune, Token Terminal, DefiLlama |

---

## 十二、注意事项与风险提示

### 12.1 数据准确性

- **所有平台的数据都可能有延迟**，通常5-30分钟
- **不同平台对同一指标的定义可能不同**（如"Revenue"是否包含代币激励）
- **Etherscan是唯一的事实来源**，其他平台数据如有疑问应回溯验证

### 12.2 成本控制

- Dune的Credit消耗与查询复杂度成正比，复杂JOIN查询消耗大
- Etherscan API免费层日限10万次调用，开发时需注意限流
- Nansen价格较贵，建议先用免费替代方案（Dune+DefiLlama）验证需求后再购买
- The Graph超额查询自动计费，需设置预算上限

### 12.3 合规提醒

- 在中国大陆，使用这些平台进行链上数据分析本身不违法
- 但基于分析结果进行加密货币交易，需注意中国对加密货币交易的监管政策
- Nansen等平台的交易功能在中国大陆不可用/不应使用

### 12.4 隐私注意

- 链上数据是公开的，任何人都可查看
- 不要在公开Dune仪表盘中暴露自己或他人的完整地址
- 使用Etherscan时，浏览器会记录你的查询历史
- Nansen的内置钱包是非托管的，但平台仍能看到你的查询行为

---

## 附录：平台网址汇总

| 平台 | 网址 | 免费层 |
|------|------|-------|
| Dune | dune.com | 支持（有限额） |
| Nansen | nansen.ai | 极有限 |
| Flipside | flipsidecrypto.xyz | 支持 |
| Etherscan | etherscan.io | 支持 |
| BscScan | bscscan.com | 支持 |
| Polygonscan | polygonscan.com | 支持 |
| DefiLlama | defillama.com | 核心全免费 |
| Token Terminal | tokenterminal.com | 支持（3仪表盘） |
| The Graph | thegraph.com | 10万次/月免费查询 |

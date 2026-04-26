# Senior Analyst — 企业经营分析专家

Claude Code 的企业经营分析 skill，输入 `/senior_analyst` 即可触发。

## 功能

### 数据工具（MCP 服务器，自动调用）
- **company_financials** — 财务数据（营收、利润、现金流、资产负债）
- **company_profile** — 公司画像（行业、市值、PE/PS/PB）
- **competitor_compare** — 竞品对比（同行业公司财务指标）
- **market_data** — 行业数据（市场规模、增长率）
- **news_search** — 新闻搜索（公司/行业/事件相关新闻）

### 分析框架（skill 层，9 类任务）
- 指标异动诊断
- 商业模式/单位经济评估
- PMF/增长诊断
- 战略选择/规划
- 流程优化
- 财报分析/排雷
- 竞争对手对比分析
- 情景/敏感性分析
- **行业商业建模**（新增）

## 行业建模能力

### 5 大行业模板

| 行业 | 商业本质 | 核心收入公式 | 关键风险 |
|------|----------|-------------|----------|
| 金融（银行/保险/信贷） | 风险定价+杠杆经营+资金期限管理 | 银行:生息资产×NIM; 保险:保费+投资收益; 信贷:放款×综合收益率 | 监管变动、信用风险、流动性 |
| 物流与供应链 | 空间效用+时间效用+规模密度 | 票量×单票收入; 订单量×履约费 | 路由密度、末端成本、季节波动 |
| 游戏 | 内容产品+流量获取+生命周期运营 | DAU×付费率×ARPPU; 广告展示×eCPM | 爆款依赖、买量ROI恶化、版号 |
| 互联网广告 | 流量变现+广告匹配+广告主ROI | 流量×加载率×填充率×eCPM | 流量见顶、广告负载过高、隐私政策 |
| 消费电子 | 产品定义+供应链效率+品牌/渠道 | 销量×ASP | 存货积压、产品周期、渠道压货 |

### 商业建模五层结构

```
行业层  → 行业本质、价值链、关键约束
公司层  → 商业模式、收入来源、客户结构
经营层  → 核心指标、经营杠杆、单位经济
财务层  → 财务映射、资产质量、现金流特征
决策层  → 投资判断、战略选择、风险与证伪
```

### 新行业快速建模十步法

面对不在模板库中的行业，按十步法从零建模：
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

## 使用

```
/senior_analyst 腾讯         → 直接分析腾讯
/senior_analyst 金融 平安     → 行业建模模式，分析金融行业
/senior_analyst 保险 中国人寿 → 行业建模模式，分析保险行业
/senior_analyst --industry 信贷 → 显式行业建模模式
/senior_analyst             → 引导模式，询问分析对象
```

## 数据源

| 源 | 类型 | 覆盖 | 中国可用 | API Key |
|----|------|------|---------|---------|
| 东方财富 (eastmoney) | HTTP API | A 股、港股财务数据 | ✅ | 无 |
| akshare | Python 库 | A 股、港股、宏观经济 | ✅ | 无 |
| yfinance | Python 库 | 美股、港股、全球 | ❌ 大陆不可用 | 无 |

降级链：**eastmoney → akshare → yfinance**，确保中国大陆网络优先使用可访问源。

新闻搜索降级链：**akshare(stock_news_em) → 东方财富搜索 API → 新浪财经**

## 要求

- Python 3.10+
- Claude Code CLI
- 零 API Key

## License

MIT

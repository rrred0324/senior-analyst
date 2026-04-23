# Senior Analyst — 企业经营分析专家

Claude Code 的企业经营分析 skill，输入 `/senior_analyst` 即可触发。

## 功能

### 数据工具（MCP 服务器，自动调用）
- **company_financials** — 财务数据（营收、利润、现金流、资产负债）
- **company_profile** — 公司画像（行业、市值、PE/PS/PB）
- **competitor_compare** — 竞品对比（同行业公司财务指标）
- **market_data** — 行业数据（市场规模、增长率）
- **news_search** — 新闻搜索（公司/行业/事件相关新闻）

### 分析框架（skill 层，8 类任务）
- 指标异动诊断
- 商业模式/单位经济评估
- PMF/增长诊断
- 战略选择/规划
- 流程优化
- 财报分析/排雷
- 竞争对手对比分析
- 情景/敏感性分析

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
/senior_analyst 滴滴    → 直接分析滴滴
/senior_analyst         → 引导模式，询问分析对象
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

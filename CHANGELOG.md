# Changelog

All notable changes to Senior Analyst will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-06-14

### Added
- **执行门控（Execution Gates）** — 财报分析5步顺序变为强制前置门控，数据不可得时留空位标注缺口，不可跳步（SKILL.md 规则#30）
- **投资者回报分析（IRR矩阵）** — 估值分析必须输出3轴IRR矩阵（入场价×持有期×情景）+ 概率加权IRR + 使IRR转正的最低入场价（SKILL.md 规则#31）
- **治理评级** — 上市公司分析必须包含六维度A+~F治理评级，映射到治理折价建议（SKILL.md 规则#32）
- **数据置信度L1-L6分层** — 从一手文档（L1，95%+）到训练数据（L6，30%），与证据等级交叉标注；关键决策依赖L4及以下时标注数据风险（SKILL.md 规则#33）
- **驱动因子分解法** — 概率赋值必须使用驱动因子分解法+隐含概率反推法，禁止无锚主观赋值（scenario playbook）
- **双轨修复规则** — 发现分析缺口时必须同时修复内容层（具体报告）和方法论层（技能文件），不可只补内容（SKILL.md 规则#35）
- **IPO分析Playbook** — 新增 `playbooks/ipo_analysis.md`（七步法 + S-1提取模板 + 创始人控制型评估）
- **IPO路由规则** — router.md 新增IPO/新上市公司关键词触发、上市不满1年自动附加、L3强制治理分析

### Changed
- **财报分析Playbook** — 5步强制门控标注、现金流向图模板、勾稽验证四项检查协议、治理评级章节、客户集中度分析
- **估值Playbook** — IRR矩阵模板、Comps按业务板块分拆强制执行、稀释影响建模、叙事溢价量化、隐含概率反推法
- **商业分析Playbook** — 收入质量五维度A+~F评分标准、UE完整推导过程模板、客户分段UE对比
- **情景分析Playbook** — 驱动因子分解法流程、隐含概率反推法对比模板
- **数据协议** — L1-L6置信度体系、数据缺口清单强制输出模板
- **证据等级** — 新增L5（无锚推断）和L6（训练数据），与置信度交叉标注规则
- **估值报告模板** — 重构：Comps分段表、IRR矩阵、概率依据表、稀释分析、叙事溢价分析、数据置信度分布、数据缺口清单
- **商业模式评估模板** — 重构：收入质量评级、UE推导过程、客户分段对比、数据置信度分布、数据缺口清单
- **财报风险报告模板** — 重构：门控标注、现金流向图、勾稽4项、治理评级表、客户集中度分析、数据置信度分布、数据缺口清单
- **完整性检查清单** — 扩展：估值7项、上市公司4项、数据质量3项、持续跟踪3项

### Prohibited（新增禁止事项）
- ❌ 严禁跳步输出（playbook定义的步骤顺序是前置门控）
- ❌ 严禁估值分析不给IRR矩阵
- ❌ 严禁上市公司分析跳过治理评级
- ❌ 严禁混淆不同置信度等级的数据
- ❌ 严禁L3深度报告省略持续跟踪框架
- ❌ 严禁概率赋值使用无锚主观判断
- ❌ 严禁发现缺口只补内容不修方法论

## [2.1.0] - 2026-05-17

### Added
- **Codex CLI support** via `adapters/codex/` — parallel entry point for Codex users
- **references/ sub-mode routing** — Codex-native pattern for mode switching (quantitative, quick-mode, industry-modeling, onboarding)
- **Unified installer** — `install.sh` with platform detection (`bash install.sh codex` or `bash install.sh claude`)
- **Automatic path substitution** — Codex MCP config uses sed-based placeholder replacement (no manual env var needed)

### Changed
- **Upgrade mechanism** moved from SKILL.md to README (both platforms)
- **Version query** simplified to 5-line natural language trigger in SKILL.md

### Maintained
- **setup.sh** remains official Claude Code installer (no deprecation, backward compatible forever)
- **Existing Claude users** see zero changes — `skill/` directory untouched

### Technical
- MCP path portability: `__SENIOR_ANALYST_HOME__` placeholder replaced by `install.sh` at install time
- Hardcopy deployment: `playbooks/`, `rubrics/`, `knowledge/`, `templates/` copied to both `~/.claude/skills/` and `~/.agents/skills/`
- Overlay architecture: `adapters/codex/` added without touching existing `skill/` directory

## [2.0.0] - 2026-05-XX

### Added
- **Valuation model** — DCF + Comps dual-method cross-validation
- **WACC × growth rate sensitivity matrix** for DCF robustness testing
- **MCP response caching** — repeat queries < 100ms
- **Lazy loading** — on-demand playbook/knowledge/template loading to save context
- **Watchlist tracking** (`--track` mode) — auto-compare with last snapshot, mark Δ changes
- **Lite industry knowledge base** — 27 industries × ~3KB lightweight versions for L2 analysis

### Changed
- Context management optimized for long conversations
- Playbook loading strategy: load only 1 playbook per task (not all 10)

## [1.9.0] - 2026-05-XX

### Added
- **Council mode** — adversarial review + multi-perspective analysis (inspired by Karpathy llm-council)
- **Red Team review** — 7 types of analysis fallacies auto-checked (narrative fallacy, anchoring, confirmation bias, linear extrapolation, survivorship bias, single attribution, scope neglect)
- **Bull/Bear multi-perspective** — optimistic/pessimistic scenarios for key judgments
- **L2 lightweight Council** — 5 quick checks + 1-2 Bull/Bear scenarios
- **L3 full Council** — 7 fallacy types + full Bull/Bear coverage + Chairman arbitration
- **L3 trigger expansion** — industry modeling/business model/strategy/investment/competitive scenarios default to L3
- **L2→L3 upgrade prompt** — auto-suggest upgrade when L2 Council finds significant divergence

## [1.8.0] - 2026-04-XX

### Added
- **Cross-validation engine** — `company_financials` auto dual-source comparison, flag discrepancy if deviation > 10%
- **Confidence scoring** — each MCP response includes 0-1 confidence score based on source consistency, data freshness, completeness, anomaly count
- **Three-statement reconciliation** — `validate_financials` new tool: balance sheet validation + cash flow quality + gross margin reasonableness
- **Anomaly detection** — auto-flag revenue QoQ > 50%, gross margin shift > 5pp, OCF/NI < 0.5 for 2+ periods

## [1.7.0] - 2026-03-XX

### Added
- **2 new MCP tools** — `macro_data` (macroeconomic indicators) + `crypto_data` (crypto assets)
- **5 new data sources** — FRED / World Bank / stats_gov_cn / CoinGecko / enhanced akshare
- **2 new CLI tools** — `senior_analyst-doctor` (data source health check) + `senior_analyst-setup-keys` (interactive API key config)
- **30+ HK stock aliases** — expanded ticker recognition
- **Free-tier operation** — basic functionality works without any API keys

### Changed
- Data source tiering: Tier 0 (no key) / Tier 1 free (free key) / Tier 1 paid (paid key)
- Macro data priority: FRED (US, if key) → stats_gov_cn (CN) → World Bank (global fallback)

## [1.6.0] - 2026-02-XX

### Added
- **Multi-source MCP** — 9 data sources integrated (FMP, Alpha Vantage, NewsAPI, yfinance, akshare, eastmoney, World Bank, stats_gov_cn, CoinGecko)
- **Standardized industry modeling** — 27 industries with unified framework
- **3-tier knowledge system** — industry knowledge base (lite/standard/deep)

## [1.5.0] - 2026-01-XX

### Added
- **Industry knowledge base enrichment** — 27 industries × 3 tiers
- **Cross-industry routing** — auto-select appropriate playbook based on industry characteristics

### Fixed
- Audit fixes from internal review
- Industry modeling consistency improvements

## [1.0.0] - 2025-12-XX

### Added
- Initial release
- Core MCP tools: `company_financials`, `company_profile`, `competitor_compare`, `market_data`, `news_search`, `industry_data`, `stock_news`
- 9 analysis frameworks: data analysis, strategy, product ops, business, process, finance/industry, competitive, scenario/sensitivity, valuation
- 18 work principles
- 6-step workflow (problem identification, framework selection, data collection, analysis, review, output)

---

## Version Numbering

- **Major (X.0.0)**: Breaking changes, major feature additions
- **Minor (x.Y.0)**: New features, backward compatible
- **Patch (x.y.Z)**: Bug fixes, minor improvements

## Links

- [GitHub Repository](https://github.com/rrred0324/senior-analyst)
- [Installation Guide](README.md#安装)
- [Usage Examples](README.md#使用)

# 示例：财报红旗扫描

## 用户输入
"帮我看看 XX 公司的财报有没有问题。"

## Skill 响应

### Step 1: 路由识别
关键词：财报 → 触发「财报分析」
调用：`playbooks/finance_industry_analysis.md`
模板：`templates/finance_risk_report.md`

### Step 2: 强制顺序
1. 先看现金流（日子）
2. 再看资产负债（底子）
3. 最后看利润（面子）
4. 勾稽验证
5. 红旗扫描

### Step 3: 红旗清单检查
使用 `rubrics/red_flag_checklist.md` 逐项检查。

### Step 4: 输出
按 `finance_risk_report.md` 模板输出，按"宁可错杀"原则处理异常信号。
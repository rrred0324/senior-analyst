# 导出协议

## 导出触发

当用户使用 `--export` 标志时，在 Step 5 输出完成后执行导出。

## 导出格式

### Markdown（默认）

- 路径：`~/Desktop/{公司名}_analysis_{YYYYMMDD}.md`
- 内容：完整的 Step 5 输出内容，包含所有章节
- 编码：UTF-8
- 文件名中的公司名需处理特殊字符（/ → _）

### CSV

- 路径：`~/Desktop/{公司名}_financials_{YYYYMMDD}.csv`
- 内容：仅财务数据表格（年度 × 指标矩阵）
- 编码：UTF-8 with BOM（Excel 兼容）
- 包含字段：year, revenue, gross_profit, net_income, operating_cash_flow, total_assets, total_liabilities, eps, ebitda, free_cash_flow, dividends

## 执行方式

Claude 在生成分析后，如用户指定了 `--export`：
1. 确定导出格式（md/csv）和目标路径
2. 使用 Write 工具将分析结果写入文件
3. 输出确认信息：`分析已导出至 ~/Desktop/腾讯_analysis_20260516.md`

## 错误处理

- 路径不可写时，尝试当前目录
- 文件已存在时，添加序号后缀（_2, _3...）
- 导出失败不影响主分析输出

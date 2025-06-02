# 批量新聞下載與 URL 分析工具

這個工具包提供了兩個主要功能：
1. **批量新聞下載器** (`batch_download_news.py`) - 支援指定公司和時間範圍的批量下載
2. **URL 分析器** (`crawl4ai_url_analyzer.py`) - 分析爬取數據中的 URL 信息

## 🚀 批量新聞下載器

### 功能特性

- ✅ 支援指定公司代碼和時間範圍
- ✅ 按月份分批下載，避免 API 限制
- ✅ 進度保存與恢復功能
- ✅ 詳細日誌記錄
- ✅ 錯誤處理和重試機制
- ✅ 可選的 LLM 提取策略
- ✅ 靈活的參數配置

### 基本使用

```bash
# 下載 AAPL 2023年全年的新聞
python batch_download_news.py --symbol AAPL --from-date 2023-01-01 --to-date 2023-12-31

# 下載 TSLA 最近半年的新聞，每月最多50篇
python batch_download_news.py --symbol TSLA --from-date 2024-07-01 --to-date 2024-12-31 --max-articles-per-month 50

# 使用自定義 API 金鑰和輸出目錄
python batch_download_news.py --symbol NVDA --from-date 2024-01-01 --to-date 2024-06-30 --api-key YOUR_API_KEY --output-dir nvda_news_data

# 使用 LLM 提取策略（需要 OpenAI API 金鑰）
python batch_download_news.py --symbol AAPL --from-date 2024-01-01 --to-date 2024-03-31 --use-llm

# 重新開始下載（不恢復進度）
python batch_download_news.py --symbol AAPL --from-date 2023-01-01 --to-date 2023-12-31 --no-resume
```

### 參數說明

| 參數 | 類型 | 必需 | 說明 |
|------|------|------|------|
| `--symbol` | str | ✅ | 公司股票代碼 (例如: AAPL, TSLA, NVDA) |
| `--from-date` | str | ✅ | 開始日期 (YYYY-MM-DD格式) |
| `--to-date` | str | ✅ | 結束日期 (YYYY-MM-DD格式) |
| `--api-key` | str | ❌ | Finnhub API 金鑰 |
| `--output-dir` | str | ❌ | 輸出目錄 (預設: batch_news_data) |
| `--use-llm` | flag | ❌ | 使用 LLM 提取策略 |
| `--delay` | float | ❌ | 請求間隔秒數 (預設: 2.0) |
| `--max-articles-per-month` | int | ❌ | 每月最大文章數量限制 |
| `--no-resume` | flag | ❌ | 不恢復進度，重新開始 |

### 輸出結構

```
batch_news_data/
├── download_progress.json          # 進度文件
├── download_log.txt               # 詳細日誌
├── download_report_AAPL_YYYYMMDD_HHMMSS.json  # 下載報告
└── aapl_news_20230101_20231231/   # 統一的公司新聞目錄
    ├── raw_html/                  # 原始 HTML（所有月份的文章）
    ├── processed_articles/        # 處理後文章（所有月份的文章）
    ├── json_data/                # JSON 數據（所有月份的文章）
    └── logs/                     # 日誌
```

**注意**: 所有下載的文章現在都會保存在同一個資料夾中，不再按月份分別創建子目錄。這樣更方便管理和分析數據。

### 進度恢復

如果下載過程中斷，可以使用相同的參數重新運行腳本，它會自動恢復進度：

```bash
# 如果之前的下載中斷了，重新運行相同命令即可恢復
python batch_download_news.py --symbol AAPL --from-date 2023-01-01 --to-date 2023-12-31
```

## 🔍 URL 分析器

### 功能特性

- ✅ 分析 Crawl4AI 爬取的 URL 數據
- ✅ 統計原始和最終域名
- ✅ 檢測 URL 重定向
- ✅ 生成詳細報告
- ✅ 支援多種輸出格式
- ✅ 查找特定域名的文章

### 基本使用

```bash
# 分析預設目錄中的數據
python crawl4ai_url_analyzer.py

# 分析指定目錄中的數據
python crawl4ai_url_analyzer.py /path/to/your/data

# 生成文本報告並保存
python crawl4ai_url_analyzer.py --output url_analysis_report.txt

# 生成 JSON 格式的詳細報告
python crawl4ai_url_analyzer.py --json-output detailed_report.json

# 查找特定域名的文章
python crawl4ai_url_analyzer.py --domain www.nasdaq.com

# 顯示前 20 個最常見域名
python crawl4ai_url_analyzer.py --top 20
```

### 參數說明

| 參數 | 類型 | 說明 |
|------|------|------|
| `data_dir` | str | 數據目錄路徑 (預設: batch_news_data) |
| `--output` / `-o` | str | 文本報告輸出路徑 |
| `--json-output` | str | JSON 詳細報告輸出路徑 |
| `--domain` | str | 查找特定域名的文章 |
| `--top` | int | 顯示前 N 個最常見域名 (預設: 10) |

### 報告格式

#### 文本報告範例
```
=== 分析摘要 ===
處理文件總數: 1250
錯誤文件數: 15
原始域名數: 1
最終域名數: 85

=== 原始 URL 域名 ===
@https://finnhub.io (1250)

=== 最終 URL 域名 (重定向後) ===
@https://www.nasdaq.com (245)
@https://www.cnbc.com (180)
@https://www.reuters.com (95)
...

=== 域名重定向 ===
finnhub.io -> www.nasdaq.com
finnhub.io -> www.cnbc.com
...
```

## 📋 完整工作流程範例

### 1. 下載 AAPL 2024年的新聞

```bash
# 下載 AAPL 2024年全年新聞
python batch_download_news.py \
    --symbol AAPL \
    --from-date 2024-01-01 \
    --to-date 2024-12-31 \
    --output-dir aapl_2024_data \
    --delay 3.0 \
    --max-articles-per-month 100
```

### 2. 分析下載的 URL 數據

```bash
# 分析 URL 數據並生成報告
python crawl4ai_url_analyzer.py aapl_2024_data \
    --output aapl_2024_url_report.txt \
    --json-output aapl_2024_detailed_report.json \
    --top 20
```

### 3. 查找特定域名的文章

```bash
# 查找 NASDAQ 網站的文章
python crawl4ai_url_analyzer.py aapl_2024_data --domain www.nasdaq.com
```

## ⚙️ 環境設定

### 1. 設定 API 金鑰

```bash
# 方法 1: 環境變數
export FINNHUB_API_KEY="your_finnhub_api_key"

# 方法 2: 使用命令列參數
python batch_download_news.py --api-key your_api_key ...

# 如果要使用 LLM 功能
export OPENAI_API_KEY="your_openai_api_key"
```

### 2. 安裝依賴

```bash
pip install -r requirements.txt
playwright install
```

## 🛠️ 故障排除

### 常見問題

1. **API 金鑰錯誤**
   ```
   ❌ 請設定有效的 Finnhub API 金鑰
   ```
   - 檢查 API 金鑰是否正確
   - 確認 API 配額是否充足

2. **日期格式錯誤**
   ```
   ❌ 無效的開始日期格式: 2024/01/01
   ```
   - 使用正確的日期格式：YYYY-MM-DD

3. **數據目錄不存在**
   ```
   ❌ 數據目錄不存在: batch_news_data
   ```
   - 確認數據目錄路徑正確
   - 先運行批量下載器生成數據

4. **下載中斷**
   - 使用相同參數重新運行即可恢復進度
   - 檢查網路連接和 API 配額

### 性能優化建議

1. **調整請求間隔**
   - 如果遇到 API 限制，增加 `--delay` 參數
   - 建議值：2-5 秒

2. **限制文章數量**
   - 使用 `--max-articles-per-month` 限制每月文章數
   - 避免下載過多數據

3. **分批處理**
   - 對於大時間範圍，建議分年或分季度下載
   - 例如：2020-2024 可以分成 5 個年度任務

## 📊 與原版工具的比較

| 功能 | 原版 (download_aapl_news.sh) | 新版 (batch_download_news.py) |
|------|------------------------------|--------------------------------|
| 公司代碼 | 固定 AAPL | 任意公司代碼 |
| 時間範圍 | 固定 2010-2024 | 任意時間範圍 |
| 進度恢復 | ✅ | ✅ |
| 錯誤處理 | 基本 | 完善 |
| 日誌記錄 | 基本 | 詳細 |
| 輸出格式 | 單一 | 多種格式 |
| LLM 支援 | ❌ | ✅ |
| URL 分析 | 需要額外工具 | 內建支援 |

## 📝 開發說明

### 擴展功能

1. **添加新的數據源**
   - 修改 `NewsCrawler` 類
   - 添加新的 API 支援

2. **自定義分析邏輯**
   - 修改 `Crawl4AIUrlAnalyzer` 類
   - 添加新的統計指標

3. **集成數據庫**
   - 添加數據庫存儲功能
   - 支援數據查詢和分析

### 貢獻指南

歡迎提交 Issue 和 Pull Request 來改進這些工具！

## 📄 授權

本項目基於原始項目的授權條款。 
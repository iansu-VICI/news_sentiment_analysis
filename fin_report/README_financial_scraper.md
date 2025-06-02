# 財報數據抓取器使用說明

## 概述
這個工具使用 Finnhub API 自動抓取 `comp.txt` 中列出的所有公司的基本財報資料。

## 功能特性

### 📊 抓取的數據類型
1. **公司基本資料** - 公司名稱、行業、國家、市值等
2. **基本財務數據** - 收入、利潤、資產負債表等關鍵財務指標
3. **公司指標** - 各種財務比率和績效指標
4. **財報日程** - 未來財報發布時間表

### 🏢 支持的公司
- **主要股票**: ASML, TSM, NVDA, V, GOOG, ISRG, ILMN, LYV, SPGI, ADBE
- **競爭對手**: 每個主要股票對應的競爭對手公司
- **總計**: 39 個公司的完整財報數據

## 快速開始

### 1. 環境準備
```bash
# 激活虛擬環境
source ../.venv/bin/activate

# 安裝依賴
pip install -r requirements_financial.txt
```

### 2. 測試單個公司
```bash
# 測試 Apple 公司
python3 test_single_company.py AAPL

# 測試其他公司
python3 test_single_company.py NVDA
```

### 3. 批量抓取所有公司
```bash
# 抓取所有公司數據
python3 financial_data_scraper.py
```

## 輸出結構

程序會在 `financial_reports/` 目錄下創建以下結構：

```
financial_reports/
├── company_profiles/      # 公司基本資料
│   ├── AAPL_profile.json
│   ├── NVDA_profile.json
│   └── ...
├── basic_financials/      # 基本財務數據
│   ├── AAPL_financials.json
│   ├── NVDA_financials.json
│   └── ...
├── metrics/              # 公司指標
│   ├── AAPL_metrics.json
│   ├── NVDA_metrics.json
│   └── ...
├── earnings/             # 財報日程
│   ├── AAPL_earnings.json
│   ├── NVDA_earnings.json
│   └── ...
├── raw_data/            # 完整原始數據
│   ├── AAPL_complete.json
│   ├── NVDA_complete.json
│   └── ...
├── companies_summary.csv # CSV 格式摘要
└── scrape_summary.json  # 抓取結果摘要
```

## 數據示例

### 公司基本資料 (company_profiles)
```json
{
  "symbol": "ADBE",
  "name": "Adobe Inc",
  "country": "US",
  "currency": "USD",
  "exchange": "NASDAQ NMS - GLOBAL MARKET",
  "industry": "Technology",
  "market_cap": 173757.4773456572,
  "share_outstanding": 426.2,
  "logo": "https://static2.finnhub.io/file/publicdatany/finnhubimage/stock_logo/ADBE.png",
  "weburl": "https://www.adobe.com/",
  "phone": "14085366000",
  "ipo": "1986-08-20"
}
```

### 基本財務數據 (basic_financials)
```json
{
  "symbol": "ADBE",
  "metric_type": "all",
  "data": {
    "metric": {
      "10DayAverageTradingVolume": 2.5234,
      "52WeekHigh": 638.25,
      "52WeekLow": 433.97,
      "marketCapitalization": 173757.48,
      "peBasicExclExtraTTM": 42.8571,
      "revenuePerShareTTM": 71.4286
    },
    "series": {
      "annual": {
        "currentRatio": [
          {"period": "2023-12-01", "v": 1.1234},
          {"period": "2022-12-01", "v": 1.0987}
        ]
      }
    }
  }
}
```

## 使用技巧

### 1. 自定義抓取範圍
編輯 `financial_data_scraper.py` 中的主函數：
```python
# 只抓取主要股票，不包含競爭對手
scraper.scrape_all_companies(
    comp_file="comp.txt",
    delay=2.0,
    include_competitors=False  # 設為 False
)
```

### 2. 調整請求頻率
```python
# 增加延迟避免 API 限制
scraper.scrape_all_companies(
    delay=5.0  # 5秒間隔
)
```

### 3. 單獨抓取特定公司
```python
from financial_data_scraper import FinancialDataScraper

scraper = FinancialDataScraper()
result = scraper.scrape_single_company("TSLA", delay=1.0)
```

## 數據分析

### 查看 CSV 摘要
```bash
# 使用 pandas 分析
python3 -c "
import pandas as pd
df = pd.read_csv('financial_reports/companies_summary.csv')
print(df[['Symbol', 'Company_Name', 'Industry', 'Market_Cap']].head(10))
"
```

### 查看成功率
```bash
# 查看抓取摘要
cat financial_reports/scrape_summary.json | grep -E '"total_companies"|"successful"|"success_rate"'
```

## 故障排除

### 1. API 限制錯誤
```
FinnhubAPIException(status_code: 403): You don't have access to this resource.
```
**解決方案**: 某些數據需要付費 API 計劃，這是正常的。程序會跳過這些數據並繼續處理其他部分。

### 2. 網絡連接問題
**解決方案**: 檢查網絡連接，增加延遲時間：
```python
scraper.scrape_all_companies(delay=5.0)
```

### 3. 依賴缺失
```bash
pip install -r requirements_financial.txt
```

## 預期執行時間

- **單個公司**: 5-10 秒
- **所有 39 個公司**: 約 5-8 分鐘
- **總數據量**: 約 10-50MB

## 數據更新頻率

建議的更新頻率：
- **公司基本資料**: 每季度
- **財務數據**: 每季度（財報發布後）
- **財報日程**: 每月
- **市場指標**: 每日

## API 配額管理

Finnhub 免費計劃限制：
- 每分鐘 60 次請求
- 每月 1000 次請求

程序已設置 2 秒延遲來遵守限制。

## 進階功能

### 1. 添加新公司
編輯 `comp.txt` 文件：
```yaml
main_tickers:
  - ASML
  - TSM
  - NVDA
  - TSLA  # 新增公司

competitors:
  TSLA: [F, GM, NIO]  # 新增競爭對手
```

### 2. 自定義輸出格式
修改 `save_company_data` 方法來支持其他格式（如 Excel、CSV 等）。

### 3. 數據驗證
程序會自動驗證數據完整性並在摘要中報告。

---

**注意**: 請遵守 Finnhub API 的使用條款和限制。某些高級數據可能需要付費訂閱。 
# SP500 增強版財務數據抓取器

## 🆕 新功能特點

### 完整同行公司數據抓取
- **基本資料**: `company_profiles/`
- **財務數據**: `basic_financials/` - 包含完整的財務指標和時間序列
- **財報日程**: `earnings/` - 包含財報發布時間和預測數據

### 按公司分組的目錄結構
每個 SP500 公司都有獨立的資料夾，包含該公司及其同行的所有數據：

```
sp500_financial_reports/
├── AAPL/                     # Apple Inc 及其同行
│   ├── company_profiles/     # AAPL + 同行公司資料
│   │   ├── AAPL_profile.json
│   │   ├── DELL_profile.json
│   │   ├── HPQ_profile.json
│   │   └── ...
│   ├── basic_financials/     # AAPL + 同行公司財務數據
│   │   ├── AAPL_financials.json
│   │   ├── DELL_financials.json
│   │   ├── HPQ_financials.json
│   │   └── ...
│   ├── earnings/            # AAPL + 同行公司財報日程
│   │   ├── AAPL_earnings.json
│   │   ├── DELL_earnings.json
│   │   └── ...
│   ├── peers/               # AAPL 同行公司列表
│   │   └── AAPL_peers.json
│   └── raw_data/            # AAPL 完整原始數據
│       └── AAPL_complete.json
├── MSFT/                    # Microsoft Corp 及其同行
│   └── (同樣結構)
└── ... (每個 SP500 股票)
```

## 📊 數據量統計

- **SP500 主公司**: 506 個
- **同行公司**: 每個主公司最多 5 個同行
- **總預期公司數**: 約 3,000+ 個
- **數據檔案數**: 約 15,000+ 個 JSON 檔案
- **預計數據量**: 5-10 GB

## 🚀 使用方法

### 1. 快速開始
```bash
source /home/new/Desktop/.venv/bin/activate
cd /home/new/Desktop/fin_report
python run_sp500_scraper.py
```

### 2. 測試模式
```bash
python test_sp500_enhanced.py
```

### 3. 自定義抓取
```python
from sp500_financial_scraper import SP500FinancialScraper

scraper = SP500FinancialScraper(output_dir="my_output")
scraper.scrape_sp500_companies(
    sp500_file="sp500.json",
    delay=1.5,
    max_companies=10,  # 限制數量
    include_peers=True  # 包含同行完整數據
)
```

## 📈 增強功能詳情

### 同行公司完整財務數據
現在會抓取每個同行公司的：
1. **公司基本資料** - 包含行業、市值、公司資訊
2. **基本財務數據** - 包含所有財務指標和 40年歷史數據
3. **財報發布日程** - 包含過去和未來的財報時間

### CSV 摘要增強
增加了 `Peers_Data_Count` 欄位，顯示成功獲取完整數據的同行公司數量：

```csv
Symbol,Success,Company_Name,Industry,Peers_Count,Peers_Data_Count,...
AAPL,True,Apple Inc,Technology,10,4,...
```

### API 使用優化
- **請求延遲**: 預設 1.5-2.0 秒間隔
- **錯誤處理**: 個別同行公司失敗不影響整體抓取
- **進度顯示**: 詳細的抓取進度和成功率統計

## 🔍 數據分析應用

### 同行比較分析
現在可以在單一資料夾中比較一家公司和其同行：

```python
import json
from pathlib import Path

# 比較 Apple 和其同行的市值
aapl_dir = Path("sp500_financial_reports/AAPL/company_profiles")
companies = {}

for profile_file in aapl_dir.glob("*_profile.json"):
    with open(profile_file) as f:
        data = json.load(f)
        companies[data['symbol']] = data['market_cap']

# 排序顯示
sorted_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)
for symbol, market_cap in sorted_companies:
    print(f"{symbol}: ${market_cap:.1f}M")
```

### 行業財務指標分析
```python
# 比較同行業公司的財務指標
financials_dir = Path("sp500_financial_reports/AAPL/basic_financials")
pe_ratios = {}

for financial_file in financials_dir.glob("*_financials.json"):
    with open(financial_file) as f:
        data = json.load(f)
        symbol = data['symbol']
        pe = data['data']['metric'].get('peTTM')
        if pe:
            pe_ratios[symbol] = pe

print("P/E 比率比較:")
for symbol, pe in sorted(pe_ratios.items(), key=lambda x: x[1]):
    print(f"{symbol}: {pe:.2f}")
```

## ⚠️ 注意事項

1. **API 限制**: 完整抓取需要 2-4 小時
2. **數據品質**: 部分同行公司可能無財報日程數據（如港股）
3. **儲存空間**: 確保有足夠的磁碟空間（推薦 15GB 以上）
4. **網路穩定**: 長時間抓取需要穩定的網路連接

## 📋 測試結果

最近測試結果（2 個公司樣本）：
- **成功率**: 100%
- **同行數據**: 平均每家主公司獲取 4-5 個同行的完整數據
- **數據完整性**: 基本資料、財務數據、財報日程全部成功
- **文件數量**: 每家主公司生成 15-20 個數據檔案

## 🔄 升級說明

相較於原版本的主要改進：
1. ✅ 同行公司現在包含完整財務數據（非僅基本資料）
2. ✅ 按公司分組的目錄結構，便於分析
3. ✅ 增強的 CSV 摘要報告
4. ✅ 更詳細的進度顯示和錯誤處理
5. ✅ 保持向後兼容性 
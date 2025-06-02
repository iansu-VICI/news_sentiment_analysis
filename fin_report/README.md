# 財務數據抓取工具集

這個工具集提供完整的財務數據抓取解決方案，支援單一公司和S&P 500批量數據獲取。

## 📋 工具概覽

### 🔧 主要工具

| 工具 | 功能 | 適用場景 |
|------|------|----------|
| `financial_data_scraper.py` | 基礎財務數據抓取器 | 小規模公司數據抓取 |
| `sp500_financial_scraper.py` | S&P 500批量抓取器 | 大規模數據抓取，包含同行分析 |
| `get_sp500.py` | S&P 500公司列表獲取 | 更新公司代碼列表 |
| `check_progress.py` | 進度檢查工具 | 監控抓取進度 |

### 📄 配置文件

- `comp.txt` - 自定義公司列表（YAML格式）
- `sp500.json` - S&P 500公司代碼列表

### 📚 說明文件

- `README_financial_scraper.md` - 基礎抓取器詳細說明
- `README_SP500_Enhanced.md` - S&P 500增強版說明
- `financial_reports_schema.md` - 數據結構說明
- `sp500_financial_reports_schema.md` - S&P 500數據結構

## 🚀 快速開始

### 1. 環境準備
```bash
# 激活虛擬環境
source ../../.venv/bin/activate

# 安裝依賴
pip install finnhub-python pandas pyyaml
```

### 2. API 配置
在 `financial_data_scraper.py` 和 `sp500_financial_scraper.py` 中設定API金鑰：
```python
API_KEY = "您的_FINNHUB_API_金鑰"
```

### 3. 選擇抓取方式

#### 🔹 小規模抓取（推薦新手）
```bash
# 抓取comp.txt中指定的公司（約39家）
python financial_data_scraper.py
```

#### 🔹 大規模抓取（推薦專業用戶）
```bash
# 抓取完整S&P 500公司數據（約3000+家公司含同行）
python sp500_financial_scraper.py
```

#### 🔹 進度監控
```bash
# 檢查抓取進度
python check_progress.py
```

## 📊 數據類型

### 抓取的財務數據
1. **公司基本資料** - 名稱、行業、市值、聯絡信息
2. **基本財務數據** - 損益表、資產負債表、現金流量表
3. **財務指標** - P/E比率、ROE、債務比率等
4. **財報日程** - 未來財報發布時間
5. **同行公司數據** - 競爭對手完整數據（僅S&P 500版本）

### 輸出結構

#### 基礎版本輸出 (`financial_data_scraper.py`)
```
financial_reports/
├── company_profiles/     # 公司基本資料
├── basic_financials/     # 財務數據
├── metrics/             # 財務指標
├── earnings/            # 財報日程
├── raw_data/           # 完整原始數據
└── companies_summary.csv # CSV摘要
```

#### S&P 500版本輸出 (`sp500_financial_scraper.py`)
```
sp500_financial_reports/
├── AAPL/               # 按公司分組
│   ├── company_profiles/   # AAPL + 同行資料
│   ├── basic_financials/   # AAPL + 同行財務
│   ├── earnings/          # AAPL + 同行財報
│   ├── peers/            # 同行列表
│   └── raw_data/         # 完整數據
├── MSFT/
└── ... (每個S&P 500公司)
```

## ⭐ 功能特色

### 🔹 基礎版特色
- ✅ 支援自定義公司列表
- ✅ 完整的財務數據抓取
- ✅ 自動重試和錯誤處理
- ✅ CSV和JSON雙格式輸出
- ✅ 詳細的進度顯示

### 🔹 S&P 500增強版特色
- ✅ 自動獲取同行公司數據
- ✅ 按公司分組的目錄結構
- ✅ 支援斷點續傳
- ✅ 更詳細的成功率統計
- ✅ 同行比較分析功能

## 📈 使用場景

### 👨‍🎓 學術研究
```bash
# 獲取特定行業公司數據
# 編輯comp.txt添加目標公司
python financial_data_scraper.py
```

### 💼 投資分析
```bash
# 獲取完整市場數據進行同行比較
python sp500_financial_scraper.py
```

### 📊 數據科學
```bash
# 大規模數據集用於機器學習
python sp500_financial_scraper.py
```

## ⚠️ 重要注意事項

1. **API限制**: Finnhub免費版有請求限制（60次/分鐘，1000次/月）
2. **執行時間**: 
   - 基礎版：約10-15分鐘
   - S&P 500版：約2-4小時
3. **存儲空間**: 
   - 基礎版：約50MB
   - S&P 500版：約5-10GB
4. **網絡需求**: 長時間穩定的網絡連接

## 🔧 故障排除

### 常見問題
- **API錯誤**: 檢查API金鑰和配額
- **網絡中斷**: 腳本支援斷點續傳
- **數據缺失**: 部分公司可能無完整數據（正常現象）

### 監控和恢復
```bash
# 檢查當前進度
python check_progress.py

# 重新運行失敗的部分（自動跳過已完成）
python sp500_financial_scraper.py
```

## 📖 詳細說明

- [基礎抓取器說明](README_financial_scraper.md) - 適合新手的詳細教學
- [S&P 500增強版說明](README_SP500_Enhanced.md) - 專業用戶完整功能指南
- [數據結構說明](financial_reports_schema.md) - 輸出數據格式詳解

---

💡 **建議流程**: 先用基礎版測試 → 確認API正常 → 再使用S&P 500版本進行大規模抓取 
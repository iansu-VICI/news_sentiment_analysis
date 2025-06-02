# 新聞情感分析工具集

這是一個完整的金融新聞情感分析工具集，提供從數據收集、處理到分析的端到端解決方案。

## 📋 項目結構

```
news_sentiment_analysis/
├── finnhub_newsdata/          # 🔥 核心新聞爬取工具
├── crawl_news/                # 📰 批量新聞內容抓取
├── crawl4ai_test/             # 🤖 AI增強爬蟲測試
├── fin_report/                # 💰 財務數據抓取工具
├── news_sentiment_labeling/   # 🏷️ 新聞情感標註流程
├── requirements.txt           # 📦 項目依賴
└── README.md                  # 📖 本文件
```

## 🚀 各工具模組介紹

### 🔥 [finnhub_newsdata/](finnhub_newsdata/) - 核心新聞爬取工具
**最重要的模組，提供完整的新聞數據獲取解決方案**

#### 主要功能
- 📊 **新聞數據抓取**: 使用Finnhub API獲取金融新聞
- 🕷️ **智能爬蟲**: 多種爬取策略（Playwright、Crawl4AI）
- 📈 **批量處理**: 支援S&P 500公司新聞批量下載
- 🔍 **URL分析**: 新聞來源域名統計和分析

#### 快速開始
```bash
cd finnhub_newsdata
python news.py --symbol AAPL --from-date 2024-01-01 --to-date 2024-12-31
```

---

### 📰 [crawl_news/](crawl_news/) - 批量新聞內容抓取
**專業級新聞內容抓取工具，支援大規模並發處理**

#### 主要功能
- ⚡ **異步爬取**: 高效並發處理
- 🔄 **斷點續傳**: 自動恢復中斷的抓取
- 📊 **進度監控**: 詳細的抓取統計
- 🎯 **智能重試**: 自動處理失敗情況

#### 快速開始
```bash
cd crawl_news
chmod +x run.sh
./run.sh AAPL 2024-01-01 2024-12-31
```

---

### 🤖 [crawl4ai_test/](crawl4ai_test/) - AI增強爬蟲測試
**下一代AI驅動的爬蟲技術測試平台**

#### 主要功能
- 🧠 **LLM集成**: 支援ChatGPT等大語言模型
- 📝 **智能提取**: 自動識別和提取關鍵內容
- 🔧 **簡化配置**: 更少的代碼，更強的功能
- 🎨 **多格式輸出**: HTML、Markdown、JSON等

#### 快速開始
```bash
cd crawl4ai_test
source crawl4ai_env/bin/activate
python crawl4ai_nasdaq_scraper.py
```

---

### 💰 [fin_report/](fin_report/) - 財務數據抓取工具
**完整的財務數據獲取解決方案**

#### 主要功能
- 📈 **基礎財務數據**: 損益表、資產負債表、現金流量表
- 🏢 **S&P 500支援**: 批量抓取500強公司數據
- 👥 **同行分析**: 自動獲取競爭對手數據
- 📊 **多格式輸出**: JSON、CSV格式

#### 快速開始
```bash
cd fin_report
python financial_data_scraper.py  # 小規模測試
python sp500_financial_scraper.py # 大規模抓取
```

---

### 🏷️ [news_sentiment_labeling/](news_sentiment_labeling/) - 新聞情感標註流程
**專業的新聞情感分析數據準備工具**

#### 主要功能
- 📊 **超額收益計算**: 基於股價變化的新聞標註
- 📈 **yfinance整合**: 自動獲取股價數據
- 🔄 **兩步驟流程**: 
  - Step 1: 計算新聞超額收益並標註
  - Step 2: 爬取新聞內容
- 📋 **CSV輸出**: 結構化的訓練數據

#### 快速開始
```bash
cd news_sentiment_labeling
./run_step1.sh    # 計算超額收益並標註
./run_step2.sh    # 爬取新聞內容
```

## 🔧 環境設定

### 1. 虛擬環境
```bash
# 創建虛擬環境（在項目根目錄）
python3 -m venv .venv
source .venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 2. API配置
```bash
# 設定Finnhub API金鑰
export FINNHUB_API_KEY="您的API金鑰"

# 或在相應的Python文件中直接設定
API_KEY = "您的API金鑰"
```

### 3. 瀏覽器安裝（用於爬蟲）
```bash
playwright install
```

## 🎯 推薦使用流程

### 📊 新手入門
1. **測試API連接**
   ```bash
   cd finnhub_newsdata
   python news.py --symbol AAPL
   ```

2. **小規模數據收集**
   ```bash
   python crawl_50.py --symbol AAPL --from-date 2024-01-01 --to-date 2024-01-31
   ```

### 🚀 專業用戶
1. **批量新聞URL收集**
   ```bash
   cd finnhub_newsdata
   ./download_aapl_news.sh
   ```

2. **大規模內容抓取**
   ```bash
   cd crawl_news
   python batch_download_news.py --symbol AAPL --start-date 2024-01-01 --end-date 2024-12-31
   ```

3. **情感標註流程**
   ```bash
   cd news_sentiment_labeling
   ./run_complete_pipeline.sh
   ```

### 🔬 研究開發
1. **測試新技術**
   ```bash
   cd crawl4ai_test
   python test_crawl4ai_simple.py
   ```

2. **財務數據整合**
   ```bash
   cd fin_report
   python sp500_financial_scraper.py
   ```

## 📈 數據流程圖

```
[Finnhub API] → [新聞URL列表] → [內容爬取] → [情感標註] → [訓練數據]
      ↓              ↓              ↓            ↓            ↓
[fin_report]  [finnhub_newsdata] [crawl_news] [yfinance] [labeled_csv]
```

## 💡 使用建議

### 🎯 目標明確
- **學術研究**: 使用`finnhub_newsdata` + `news_sentiment_labeling`
- **投資分析**: 使用`fin_report` + `crawl_news`
- **技術測試**: 使用`crawl4ai_test`
- **大規模分析**: 使用所有模組的完整流程

### ⚡ 效率優化
- **並發控制**: 適當設定併發數量避免被封IP
- **API配額**: 監控Finnhub API使用量
- **存儲管理**: 定期清理和壓縮數據
- **網絡穩定**: 使用穩定的網絡環境

## ⚠️ 重要注意事項

1. **API限制**: Finnhub免費版有請求限制
2. **法律合規**: 遵守網站robots.txt和使用條款
3. **數據質量**: 注意處理重複和無效數據
4. **系統資源**: 大規模爬取需要足夠的內存和存儲空間

## 🛠️ 故障排除

### 常見問題
- **導入錯誤**: 檢查虛擬環境和依賴安裝
- **API錯誤**: 驗證API金鑰和配額
- **爬蟲失敗**: 檢查網絡連接和反爬蟲策略
- **數據缺失**: 確認輸入參數和文件路徑

### 支援資源
- 各模組都有詳細的README文件
- 查看`*.log`文件了解詳細錯誤
- 使用測試腳本驗證環境配置

---

📧 **需要協助?** 請查看各個子目錄的README文件獲取詳細說明
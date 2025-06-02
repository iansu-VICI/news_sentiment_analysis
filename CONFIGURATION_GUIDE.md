# 配置指南 - Finnhub API 金鑰設定

## 🔧 API 金鑰配置變更說明

所有使用 Finnhub API 的文件已經更新為從 `.env` 文件讀取 API 金鑰，而非在代碼中硬編碼。這樣做的好處包括：

- ✅ **安全性提升**: API 金鑰不會被意外提交到版本控制
- ✅ **易於管理**: 統一的配置文件
- ✅ **環境隔離**: 不同環境可使用不同的 API 金鑰

## 📋 已修改的文件清單

### 核心工具文件
- `finnhub_newsdata/utils.py` - 主要工具函數庫
- `finnhub_newsdata/news.py` - 新聞查詢工具
- `finnhub_newsdata/stock.py` - 股票數據查詢工具
- `finnhub_newsdata/crawl_50.py` - 進階新聞爬取工具
- `finnhub_newsdata/analyze_finnhub_news_urls.py` - URL 分析工具

### 財務數據工具
- `fin_report/financial_data_scraper.py` - 基礎財務數據抓取器
- `fin_report/sp500_financial_scraper.py` - S&P 500 批量抓取器

### 新聞爬取工具
- `crawl_news/utils.py` - 爬取工具函數庫
- `crawl_news/batch_download_news.py` - 批量新聞下載器

### 情感標註工具
- `news_sentiment_labeling/count_sp500_news.py` - 通過 utils 自動使用新配置

### 其他文件
- `requirements.txt` - 添加了 `python-dotenv` 依賴
- `README.md` - 更新了環境設定說明

## 🚀 使用方法

### 1. 安裝依賴
```bash
# 確保安裝新的依賴
pip install python-dotenv

# 或重新安裝所有依賴
pip install -r requirements.txt
```

### 2. 設定 API 金鑰
```bash
# 複製範例文件
cp .env.example .env

# 編輯 .env 文件
nano .env
# 或
vim .env
```

在 `.env` 文件中，將 `your_finnhub_api_key_here` 替換為您的實際 API 金鑰：
```
FINNHUB_API_KEY=您的實際金鑰
```

### 3. 驗證設定
```bash
# 測試 API 連接
cd finnhub_newsdata
python news.py --symbol AAPL

# 如果設定正確，應該能正常獲取新聞
# 如果設定錯誤，會顯示明確的錯誤訊息
```

## 🔍 錯誤處理

### 常見錯誤訊息

1. **未設定 API 金鑰**:
   ```
   ❌ 錯誤：請在 .env 文件中設定 FINNHUB_API_KEY
   請創建 .env 文件並添加: FINNHUB_API_KEY=your_api_key_here
   ```
   **解決方法**: 按照上面的步驟創建並配置 `.env` 文件

2. **API 金鑰無效**:
   ```
   獲取公司新聞時發生錯誤: API key is invalid
   ```
   **解決方法**: 檢查 API 金鑰是否正確，或到 [Finnhub](https://finnhub.io/register) 重新申請

3. **API 配額用盡**:
   ```
   API call frequency is the issue or exceeded the quota
   ```
   **解決方法**: 等待配額重置，或升級到付費方案

## 📝 檔案結構

```
news_sentiment_analysis/
├── .env                    # 您的 API 金鑰配置（不會被提交）
├── .env.example           # 配置範例文件
├── .gitignore            # 確保 .env 不被提交
├── requirements.txt      # 包含 python-dotenv
├── CONFIGURATION_GUIDE.md # 本文件
└── 各個模組目錄...
```

## 🔐 安全注意事項

1. **永遠不要提交 `.env` 文件**: 此文件已加入 `.gitignore`
2. **定期更換 API 金鑰**: 如果懷疑洩露，立即更換
3. **使用最小權限原則**: 僅給予必要的 API 權限

## 🆘 獲取幫助

如果遇到問題：
1. 檢查 `.env` 文件是否正確設定
2. 確認 API 金鑰有效性
3. 查看相關模組的 README 文件
4. 檢查是否安裝了所有依賴

---

🎉 **配置完成後，所有工具都會自動使用新的 API 金鑰配置！** 
# 並行化腳本使用指南

這裡提供了完整的並行化版本，大幅提升新聞情感分析流程的處理速度。

## ✅ 問題已解決

經過修正，所有並行化腳本現在都能正常運行：

### 🔧 已修正的問題
- **Step1**: 修正了模組導入路徑問題
- **Step2**: 修正了 crawl4ai 模組導入問題
- **並發控制**: 優化了超時和錯誤處理

## 🚀 快速開始

### 方案一：一鍵執行完整流程 (推薦)
```bash
# 進入目錄
cd news_sentiment_analysis/news_sentiment_labeling/

# 執行完整並行化流程
./run_complete_pipeline_parallel.sh complete
```

### 方案二：互動式模式
```bash
# 執行互動式工具
./run_complete_pipeline_parallel.sh

# 然後選擇對應選項：
# 1) 執行完整流程 (Step1 → Step2)
# 2) 只執行 Step1 (並行版本)
# 3) 只執行 Step2 (並行版本)
# 4) 顯示目前進度
# 5) 清理所有進度文件
```

### 方案三：分步執行
```bash
# Step1: 計算 excess return（4個並發）
./run_step1_parallel.sh

# Step2: 爬取新聞內容（3個並發）
./run_step2_parallel.sh
```

## 📋 腳本說明

### 🔥 主要腳本

| 腳本名稱 | 功能 | 並發數 | 建議使用場景 |
|----------|------|--------|-------------|
| `run_complete_pipeline_parallel.sh` | **完整流程管理工具** | 動態 | 🌟 推薦，一鍵執行完整流程 |
| `run_step1_parallel.sh` | Step1 並行版本 | 4 | 只需要計算 excess return |
| `run_step2_parallel.sh` | Step2 並行版本 | 3 | 只需要爬取新聞內容 |

### 🔧 原始腳本（作為備用）

| 腳本名稱 | 功能 | 使用場景 |
|----------|------|----------|
| `run_step1.sh` | Step1 原始版本 | 如果並行版本有問題時使用 |
| `run_step2.sh` | Step2 原始版本 | 如果並行版本有問題時使用 |

## ⚡ 性能優化

### Step1 並行化優勢
- **智能優化**: 同一公司同一天的新聞只計算一次 excess return
- **並發處理**: 4個公司同時處理
- **進度追蹤**: 已完成的公司自動跳過
- **API 效率**: 減少重複 API 調用

### Step2 並行化優勢
- **並發爬取**: 3個公司同時爬取新聞內容
- **智能延遲**: 避免過度負載目標網站
- **容錯處理**: 失敗的任務可以重新運行
- **詳細統計**: 爬取成功率和內容長度統計

## 🔧 環境需求

### 必需依賴
```bash
# GNU parallel（並行處理）
sudo apt-get install parallel

# Python 依賴（虛擬環境）
source ../../.venv/bin/activate
pip install crawl4ai pandas yfinance numpy beautifulsoup4 aiohttp asyncio
```

### 可選優化
```bash
# 安裝 Playwright 瀏覽器（自動安裝）
playwright install
```

## 📊 實際測試結果

### Step1 測試結果
```
=== 處理完成 ===
總文件數: 120
成功處理: 71
失敗: 49
優化效果: 大幅減少API調用次數
```

### Step2 測試結果
```
✅ DHR: 成功爬取 1/1 篇文章
結果保存到: ./news_content/dhr_content.csv
統計結果:
  總文章數: 1
  成功: 1
  失敗: 0
  跳過: 0
```

## 🛡️ 故障排除

### 常見問題

1. **模組導入錯誤**
   - ✅ 已修正：路徑設定問題
   - 確保在正確目錄執行腳本

2. **並發數過高**
   - 可以調整 `MAX_JOBS` 參數
   - Step1: 推薦 4 個並發
   - Step2: 推薦 3 個並發

3. **網絡超時**
   - Step1: 300秒超時
   - Step2: 600秒超時
   - 可以根據網絡情況調整

### 重新運行
```bash
# 清理進度文件，重新開始
rm -f step1_progress.txt step2_progress.txt

# 或者讓腳本自動跳過已完成的公司
./run_step1_parallel.sh  # 自動跳過已完成的
```

## 📈 監控和日誌

### 實時監控
```bash
# 查看 Step1 進度
tail -f step1_parallel_log.txt

# 查看 Step2 進度  
tail -f step2_parallel_log.txt

# 查看並行作業統計
cat step1_parallel_joblog.txt
cat step2_parallel_joblog.txt
```

### 結果檢查
```bash
# 檢查 Step1 結果
ls -la news_data/*.csv

# 檢查 Step2 結果
ls -la news_content/*.csv

# 檢查內容質量
head -n 5 news_content/dhr_content.csv
```

## 🎯 下一步

完成並行化處理後，您可以：

1. **分析爬取結果**
   ```bash
   # 統計成功率
   find news_content/ -name "*.csv" | wc -l
   ```

2. **進行情感分析**
   - 使用爬取的新聞內容
   - 建立機器學習模型

3. **優化參數**
   - 根據實際性能調整並發數
   - 根據網站響應調整延遲時間

---

**🚀 現在您已經擁有了一個完全並行化的新聞情感分析工具集！** 
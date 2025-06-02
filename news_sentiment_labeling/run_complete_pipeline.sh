#!/bin/bash

# 完整的新聞標註流程
# 包含step1（計算excess return）和step2（抓取新聞內容）

echo "======================================="
echo "    新聞標註完整流程"
echo "======================================="
echo "目標：標註S&P500公司2021-2025的新聞資料"
echo "流程："
echo "  Step1: 計算excess return並標註"
echo "  Step2: 抓取新聞內容"
echo ""
echo "開始時間: $(date)"
echo "======================================="

# 檢查必要的輸入數據
if [ ! -d "../finnhub_newsdata/sp500_news_urls" ]; then
    echo "❌ 錯誤: 找不到 ../finnhub_newsdata/sp500_news_urls 目錄"
    echo "請先執行新聞URL抓取步驟"
    exit 1
fi

# 檢查是否有JSON文件
json_count=$(ls -1 ../finnhub_newsdata/sp500_news_urls/*.json 2>/dev/null | wc -l)
if [ $json_count -eq 0 ]; then
    echo "❌ 錯誤: sp500_news_urls目錄中沒有JSON文件"
    echo "請先執行新聞URL抓取步驟"
    exit 1
fi

echo "✅ 找到 $json_count 個新聞JSON文件"
echo ""

# Step1: 計算excess return並標註
echo "======================================="
echo "執行 Step1: 計算excess return並標註"
echo "======================================="

if ./run_step1.sh; then
    echo "✅ Step1 完成"
else
    echo "❌ Step1 失敗，停止執行"
    exit 1
fi

echo ""

# Step2: 抓取新聞內容
echo "======================================="
echo "執行 Step2: 抓取新聞內容"
echo "======================================="

if ./run_step2.sh; then
    echo "✅ Step2 完成"
else
    echo "❌ Step2 失敗"
    exit 1
fi

echo ""
echo "======================================="
echo "    完整流程執行完成"
echo "======================================="
echo "結束時間: $(date)"
echo ""
echo "輸出文件："
echo "  - Step1 結果: ./news_data/*_labeled.csv"
echo "  - Step2 結果: ./news_content/*_content.csv"
echo ""
echo "可以開始分析標註好的新聞數據了！" 
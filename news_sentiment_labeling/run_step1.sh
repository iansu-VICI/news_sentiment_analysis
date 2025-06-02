#!/bin/bash

# Step1: 計算excess return並標註新聞
# 使用yfinance抓取新聞發布後三個交易日的價格並計算excess return
# 優化版本：同一公司同一天的新聞只計算一次excess return

echo "=== Step1: 計算excess return並標註新聞 ==="
echo "開始時間: $(date)"
echo ""
echo "💡 優化說明:"
echo "   同一家公司在同一天的新聞，其後三個交易日excess return相同"
echo "   所以只需要為每個唯一的(公司,日期)組合計算一次"
echo "   大幅減少API調用次數，提升處理速度"
echo ""

echo "執行Step1腳本..."
python step1_calculate_excess_return.py

echo ""
echo "Step1完成時間: $(date)"
echo "結果已保存到 ./news_data/ 目錄中" 
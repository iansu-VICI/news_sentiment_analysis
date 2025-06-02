#!/bin/bash

# Step2: 使用crawl4ai抓取新聞內容
# 根據step1產生的CSV檔案，抓取其最終URL的新聞內容

echo "=== Step2: 使用crawl4ai抓取新聞內容 ==="
echo "開始時間: $(date)"
echo ""

# 檢查是否已執行step1
if [ ! -d "./news_data" ] || [ -z "$(ls -A ./news_data/*.csv 2>/dev/null)" ]; then
    echo "錯誤: 未找到step1生成的CSV文件"
    echo "請先執行step1: ./run_step1.sh"
    exit 1
fi

# 檢查虛擬環境
if [ ! -d "./venv" ]; then
    echo "創建虛擬環境..."
    python3 -m venv venv
fi

# 激活虛擬環境
source ./venv/bin/activate

# 安裝依賴
echo "安裝必要的Python套件..."
pip install crawl4ai pandas aiohttp asyncio

# 安裝playwright瀏覽器
echo "安裝playwright瀏覽器..."
playwright install

echo ""
echo "執行Step2腳本..."
python step2_crawl_news_content.py

echo ""
echo "Step2完成時間: $(date)"
echo "結果已保存到 ./news_content/ 目錄中" 
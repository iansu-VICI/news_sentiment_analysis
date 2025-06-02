#!/bin/bash

# Step2 並行版本: 使用crawl4ai抓取新聞內容
# 根據step1產生的CSV檔案，並行抓取其最終URL的新聞內容

# 設定參數
MAX_JOBS=3  # 最大並發數量，避免過度負載網站
PROGRESS_FILE="./step2_progress.txt"
LOG_FILE="./step2_parallel_log.txt"
VENV_PATH="../../.venv"
INPUT_DIR="./news_data"
OUTPUT_DIR="./news_content"

# 檢查 GNU parallel 是否安裝
if ! command -v parallel &> /dev/null; then
    echo "❌ 需要安裝 GNU parallel"
    echo "Ubuntu/Debian: sudo apt-get install parallel"
    echo "CentOS/RHEL: sudo yum install parallel"
    echo ""
    echo "或者使用 xargs 版本: ./run_step2_xargs.sh"
    exit 1
fi

# 檢查是否已執行step1
if [ ! -d "$INPUT_DIR" ] || [ -z "$(ls -A $INPUT_DIR/*.csv 2>/dev/null)" ]; then
    echo "❌ 錯誤: 未找到step1生成的CSV文件"
    echo "請先執行step1: ./run_step1_parallel.sh 或 ./run_step1.sh"
    exit 1
fi

# 檢查虛擬環境
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ 錯誤: 找不到虛擬環境 $VENV_PATH"
    exit 1
fi

# 創建輸出目錄
mkdir -p "$OUTPUT_DIR"

echo "=== Step2 並行版本: 使用crawl4ai抓取新聞內容 ==="
echo "開始時間: $(date)"
echo "輸入目錄: $INPUT_DIR"
echo "輸出目錄: $OUTPUT_DIR"
echo "並發數量: $MAX_JOBS"
echo ""
echo "💡 優化說明:"
echo "   使用GNU parallel按公司並行處理"
echo "   每個公司的新聞內容獨立爬取"
echo "   控制並發數量避免過度負載目標網站"
echo "========================================================"

# 初始化日誌文件
echo "Step2 並行處理開始時間: $(date)" > "$LOG_FILE"

# 函數：檢查是否已經處理過某個公司
is_company_completed() {
    local symbol="$1"
    if [ -f "$PROGRESS_FILE" ]; then
        grep -q "^COMPLETED:$symbol$" "$PROGRESS_FILE"
        return $?
    fi
    return 1
}

# 函數：標記公司為已完成
mark_company_completed() {
    local symbol="$1"
    echo "COMPLETED:$symbol" >> "$PROGRESS_FILE"
}

# 函數：記錄日誌（支援並發寫入）
log_message() {
    local message="$1"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    (
        flock -x 200
        echo "$timestamp: $message" >> "$LOG_FILE"
        echo "$timestamp: $message"
    ) 200>>"$LOG_FILE.lock"
}

# 函數：處理單個公司（將被 parallel 調用）
process_single_company() {
    local csv_file="$1"
    local symbol=$(basename "$csv_file" .csv)
    
    # 檢查是否已經處理過這個公司
    if is_company_completed "$symbol"; then
        log_message "[SKIP] 跳過已完成的公司: $symbol"
        return 0
    fi
    
    log_message "[START] 開始處理公司: $symbol"
    
    # 創建臨時Python腳本來處理單個公司
    local temp_script="/tmp/process_company_step2_${symbol}_$$.py"
    cat > "$temp_script" << 'EOF'
#!/usr/bin/env python3
import os
import sys
import asyncio

# 添加當前目錄到Python路徑
current_dir = os.getcwd()
sys.path.insert(0, current_dir)

# 獲取命令行參數
if len(sys.argv) != 3:
    print("使用方法: python script.py <csv_file> <output_dir>")
    sys.exit(1)

csv_file = sys.argv[1]
output_dir = sys.argv[2]

async def process_single_csv():
    try:
        # 導入step2的類
        from step2_crawl_news_content import NewsContentCrawler
        
        # 創建爬蟲實例（降低並發數以避免過載）
        crawler = NewsContentCrawler(max_concurrent=2, delay=1.5)
        
        # 處理CSV文件
        success = await crawler.process_csv_file(csv_file, output_dir)
        
        # 輸出統計
        print(f"\n統計結果:")
        print(f"  總文章數: {crawler.stats['total_articles']}")
        print(f"  成功: {crawler.stats['successful_articles']}")
        print(f"  失敗: {crawler.stats['failed_articles']}")
        print(f"  跳過: {crawler.stats['skipped_articles']}")
        
        return success
        
    except Exception as e:
        print(f"處理過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

# 執行處理
try:
    result = asyncio.run(process_single_csv())
    sys.exit(0 if result else 1)
except Exception as e:
    print(f"執行失敗: {e}")
    sys.exit(1)
EOF
    
    # 使用虛擬環境執行處理
    local current_dir=$(pwd)
    if timeout 600 bash -c "source '$VENV_PATH/bin/activate' && cd '$current_dir' && python '$temp_script' '$csv_file' '$OUTPUT_DIR'" 2>&1; then
        mark_company_completed "$symbol"
        log_message "[SUCCESS] ✅ 成功完成 $symbol"
        rm -f "$temp_script"
        return 0
    else
        log_message "[FAILED] ❌ 失敗 $symbol (可能超時或其他錯誤)"
        rm -f "$temp_script"
        return 1
    fi
}

# 導出函數和變量，讓 parallel 可以使用
export -f process_single_company
export -f is_company_completed
export -f mark_company_completed
export -f log_message
export INPUT_DIR OUTPUT_DIR PROGRESS_FILE LOG_FILE VENV_PATH

# 找到所有CSV文件
csv_files=$(find "$INPUT_DIR" -name "*.csv" -type f)

if [ -z "$csv_files" ]; then
    echo "❌ 在 $INPUT_DIR 中找不到CSV文件"
    exit 1
fi

# 計算總文件數量
total_files=$(echo "$csv_files" | wc -l)
log_message "總公司數量: $total_files"

echo "找到 $total_files 個公司的CSV文件"

# 檢查crawl4ai是否安裝
echo "檢查crawl4ai安裝狀態..."
if ! bash -c "source '$VENV_PATH/bin/activate' && python -c 'import crawl4ai'" 2>/dev/null; then
    echo "安裝crawl4ai和相關依賴..."
    bash -c "source '$VENV_PATH/bin/activate' && pip install crawl4ai pandas aiohttp asyncio"
    
    echo "安裝playwright瀏覽器..."
    bash -c "source '$VENV_PATH/bin/activate' && playwright install"
fi

echo "開始並行處理..."

# 使用 GNU parallel 並行處理
echo "$csv_files" | parallel -j "$MAX_JOBS" --progress --joblog step2_parallel_joblog.txt process_single_company {}

# 計算最終統計
successful_companies=$(grep "^COMPLETED:" "$PROGRESS_FILE" 2>/dev/null | wc -l || echo 0)
failed_companies=$((total_files - successful_companies))
final_success_rate=0
if [ $total_files -gt 0 ]; then
    final_success_rate=$(echo "scale=2; $successful_companies * 100 / $total_files" | bc -l)
fi

log_message ""
log_message "========================================================"
log_message "Step2 並行處理完成！"
log_message "總共公司數量: $total_files"
log_message "成功公司: $successful_companies"
log_message "失敗公司: $failed_companies"
log_message "成功率: ${final_success_rate}%"
log_message "結果已保存到: $OUTPUT_DIR"
log_message "完成時間: $(date)"
log_message "========================================================"

# 顯示 parallel 的作業日誌統計
if [ -f "step2_parallel_joblog.txt" ]; then
    echo ""
    echo "並行處理統計:"
    echo "作業日誌: step2_parallel_joblog.txt"
    awk 'NR>1 {
        if ($7 == 0) success++; else failed++;
        total_time += $4
    } END {
        print "並行成功: " success
        print "並行失敗: " failed  
        print "總執行時間: " total_time " 秒"
        if (NR > 1) print "平均每個作業: " total_time/(NR-1) " 秒"
    }' step2_parallel_joblog.txt
fi

echo ""
echo "如果需要重新運行失敗的公司，只需再次執行此腳本。"
echo "腳本會自動跳過已成功完成的公司。"
echo "詳細日誌請查看: $LOG_FILE"

# 清理鎖定文件
rm -f "$LOG_FILE.lock"

# 顯示完成的結果目錄
if [ $successful_companies -gt 0 ]; then
    echo ""
    echo "🎉 Step2完成！新聞內容已保存到: $OUTPUT_DIR"
    echo ""
    echo "下一步可以進行:"
    echo "   1. 查看爬取的新聞內容"
    echo "   2. 進行情感分析"
    echo "   3. 建立機器學習模型"
fi 
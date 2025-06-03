#!/bin/bash

# 並行抓取 S&P 500 公司新聞從 2021年1月1日 到 2025年5月23日
# 只抓取新聞的原始URL、最終URL和發布日期，不下載內容
# 使用 GNU parallel 進行並發處理

# 設定參數
SP500_FILE="sp500.json"
OUTPUT_DIR="./sp500_news_urls"
START_DATE="2021-01-01"
END_DATE="2021-01-01"  # 擴展到完整時間範圍
PROGRESS_FILE="./download_progress.txt"
LOG_FILE="./download_log.txt"
VENV_PATH="../../.venv"
MAX_JOBS=4  # 最大並發數量，避免API限制

# 檢查 GNU parallel 是否安裝
if ! command -v parallel &> /dev/null; then
    echo "❌ 錯誤: 需要安裝 GNU parallel"
    echo "Ubuntu/Debian: sudo apt-get install parallel"
    echo "CentOS/RHEL: sudo yum install parallel"
    exit 1
fi

# 創建輸出目錄
mkdir -p "$OUTPUT_DIR"

# 檢查虛擬環境是否存在
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ 錯誤: 找不到虛擬環境 $VENV_PATH"
    exit 1
fi

# 檢查 sp500.json 是否存在
if [ ! -f "$SP500_FILE" ]; then
    echo "❌ 錯誤: 找不到 $SP500_FILE 文件"
    exit 1
fi

# 初始化日誌文件
echo "並行版本開始時間: $(date)" > "$LOG_FILE"

echo "=== 並行抓取 S&P 500 公司新聞資料 ==="
echo "時間範圍: $START_DATE 到 $END_DATE"
echo "輸出目錄: $OUTPUT_DIR"
echo "並發數量: $MAX_JOBS"
echo "進度文件: $PROGRESS_FILE"
echo "日誌文件: $LOG_FILE"
echo "虛擬環境: $VENV_PATH"
echo "========================================================"

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
    # 使用 flock 確保日誌寫入的原子性
    (
        flock -x 200
        echo "$timestamp: $message" >> "$LOG_FILE"
        echo "$timestamp: $message"
    ) 200>>"$LOG_FILE.lock"
}

# 函數：處理單個公司（將被 parallel 調用）
process_single_company() {
    local symbol="$1"
    
    # 檢查是否已經處理過這個公司
    if is_company_completed "$symbol"; then
        log_message "[SKIP] 跳過已完成的公司: $symbol"
        return 0
    fi
    
    log_message "[START] 開始處理公司: $symbol"
    
    # 激活虛擬環境
    source "$VENV_PATH/bin/activate"
    
    # 執行爬蟲程式
    if timeout 300 python crawl_50.py --type company --symbol "$symbol" --from-date "$START_DATE" --to-date "$END_DATE" --output-dir "$OUTPUT_DIR" 2>/dev/null; then
        mark_company_completed "$symbol"
        log_message "[SUCCESS] ✅ 成功完成 $symbol"
        return 0
    else
        log_message "[FAILED] ❌ 失敗 $symbol (可能超時或其他錯誤)"
        return 1
    fi
}

# 導出函數和變量，讓 parallel 可以使用
export -f process_single_company
export -f is_company_completed
export -f mark_company_completed
export -f log_message
export SP500_FILE OUTPUT_DIR START_DATE END_DATE PROGRESS_FILE LOG_FILE VENV_PATH

# 激活虛擬環境並讀取公司列表
source "$VENV_PATH/bin/activate"

companies=$(python3 -c "
import json
with open('$SP500_FILE', 'r') as f:
    symbols = json.load(f)
for symbol in symbols:
    print(symbol)
")

# 計算總公司數量
total_companies=$(echo "$companies" | wc -l)
echo "總公司數量: $total_companies"
log_message "總公司數量: $total_companies"

echo ""
echo "開始並行處理..."
echo "注意: 如果時間範圍跨越多個月，建議使用月份循環版本以提高成功率"

# 使用 GNU parallel 並行處理
echo "$companies" | parallel -j "$MAX_JOBS" --progress --joblog parallel_joblog.txt process_single_company {}

# 計算最終統計
successful_companies=$(grep "^COMPLETED:" "$PROGRESS_FILE" 2>/dev/null | wc -l || echo 0)
failed_companies=$((total_companies - successful_companies))
final_success_rate=0
if [ $total_companies -gt 0 ]; then
    final_success_rate=$(echo "scale=2; $successful_companies * 100 / $total_companies" | bc -l)
fi

echo ""
echo "========================================================"
echo "並行抓取完成！"
echo "總共公司數量: $total_companies"
echo "成功公司: $successful_companies"
echo "失敗公司: $failed_companies"
echo "成功率: ${final_success_rate}%"
echo "所有資料已保存到: $OUTPUT_DIR"
echo "完成時間: $(date)"
echo "========================================================"

# 記錄最終統計到日誌
log_message ""
log_message "========================================================"
log_message "並行抓取完成！"
log_message "總共公司數量: $total_companies"
log_message "成功公司: $successful_companies"
log_message "失敗公司: $failed_companies"
log_message "成功率: ${final_success_rate}%"
log_message "所有資料已保存到: $OUTPUT_DIR"
log_message "完成時間: $(date)"
log_message "========================================================"

# 顯示 parallel 的作業日誌統計
if [ -f "parallel_joblog.txt" ]; then
    echo ""
    echo "並行處理統計:"
    echo "作業日誌: parallel_joblog.txt"
    awk 'NR>1 {
        if ($7 == 0) success++; else failed++;
        total_time += $4
    } END {
        print "並行成功: " success
        print "並行失敗: " failed  
        print "總執行時間: " total_time " 秒"
        if (NR > 1) print "平均每個作業: " total_time/(NR-1) " 秒"
    }' parallel_joblog.txt
fi

echo ""
echo "如果需要重新運行失敗的公司，只需再次執行此腳本。"
echo "腳本會自動跳過已成功完成的公司。"
echo "詳細日誌請查看: $LOG_FILE"

# 清理鎖定文件
rm -f "$LOG_FILE.lock" 
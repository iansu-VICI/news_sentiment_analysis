#!/bin/bash

# Step1 並行版本: 計算excess return並標註新聞
# 使用GNU parallel按公司並行處理，大幅提升處理速度

# 設定參數

MAX_JOBS=4  # 最大並發數量，避免API限制
PROGRESS_FILE="./step1_progress.txt"
LOG_FILE="./step1_parallel_log.txt"
VENV_PATH="../../.venv"
INPUT_DIR="../finnhub_newsdata/sp500_news_urls"
OUTPUT_DIR="./news_data"

# 檢查 GNU parallel 是否安裝
if ! command -v parallel &> /dev/null; then
    echo "❌ 需要安裝 GNU parallel"
    echo "Ubuntu/Debian: sudo apt-get install parallel"
    echo "CentOS/RHEL: sudo yum install parallel"
    echo ""
    echo "或者使用 xargs 版本: ./run_step1_xargs.sh"
    exit 1
fi

# 檢查輸入目錄
if [ ! -d "$INPUT_DIR" ]; then
    echo "❌ 錯誤: 找不到輸入目錄 $INPUT_DIR"
    echo "請先執行 finnhub_newsdata 中的抓取腳本"
    exit 1
fi

# 檢查虛擬環境
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ 錯誤: 找不到虛擬環境 $VENV_PATH"
    exit 1
fi

# 創建輸出目錄
mkdir -p "$OUTPUT_DIR"

echo "=== Step1 並行版本: 計算excess return並標註新聞 ==="
echo "開始時間: $(date)"
echo "輸入目錄: $INPUT_DIR"
echo "輸出目錄: $OUTPUT_DIR"
echo "並發數量: $MAX_JOBS"
echo ""
echo "💡 優化說明:"
echo "   使用GNU parallel按公司並行處理"
echo "   同一家公司在同一天的新聞，其後三個交易日excess return相同"
echo "   所以只需要為每個唯一的(公司,日期)組合計算一次"
echo "   大幅減少API調用次數，提升處理速度"
echo "========================================================"

# 初始化日誌文件
echo "Step1 並行處理開始時間: $(date)" > "$LOG_FILE"

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
    local json_file="$1"
    local symbol=$(basename "$json_file" .json)
    
    # 檢查是否已經處理過這個公司
    if is_company_completed "$symbol"; then
        log_message "[SKIP] 跳過已完成的公司: $symbol"
        return 0
    fi
    
    log_message "[START] 開始處理公司: $symbol"
    
    # 創建臨時Python腳本來處理單個公司
    local temp_script="/tmp/process_company_${symbol}_$$.py"
    cat > "$temp_script" << 'EOF'
#!/usr/bin/env python3
import os
import sys

# 添加當前目錄到Python路徑
current_dir = os.getcwd()
sys.path.insert(0, current_dir)

# 導入step1模組
try:
    from step1_calculate_excess_return import process_company_news
except ImportError as e:
    print(f"無法導入step1模組: {e}")
    sys.exit(1)

# 獲取命令行參數
if len(sys.argv) != 3:
    print("使用方法: python script.py <json_file> <output_dir>")
    sys.exit(1)

json_file = sys.argv[1]
output_dir = sys.argv[2]

# 處理公司
try:
    success = process_company_news(json_file, output_dir)
    sys.exit(0 if success else 1)
except Exception as e:
    print(f"處理失敗: {e}")
    sys.exit(1)
EOF
    
    # 使用虛擬環境執行處理
    local current_dir=$(pwd)
    if timeout 300 bash -c "source '$VENV_PATH/bin/activate' && cd '$current_dir' && python '$temp_script' '$json_file' '$OUTPUT_DIR'" 2>&1; then
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

# 找到所有JSON文件
json_files=$(find "$INPUT_DIR" -name "*.json" -type f)

if [ -z "$json_files" ]; then
    echo "❌ 在 $INPUT_DIR 中找不到JSON文件"
    exit 1
fi

# 計算總文件數量
total_files=$(echo "$json_files" | wc -l)
log_message "總公司數量: $total_files"

echo "找到 $total_files 個公司的JSON文件"
echo "開始並行處理..."

# 使用 GNU parallel 並行處理
echo "$json_files" | parallel -j "$MAX_JOBS" --progress --joblog step1_parallel_joblog.txt process_single_company {}

# 計算最終統計
successful_companies=$(grep "^COMPLETED:" "$PROGRESS_FILE" 2>/dev/null | wc -l || echo 0)
failed_companies=$((total_files - successful_companies))
final_success_rate=0
if [ $total_files -gt 0 ]; then
    final_success_rate=$(echo "scale=2; $successful_companies * 100 / $total_files" | bc -l)
fi

log_message ""
log_message "========================================================"
log_message "Step1 並行處理完成！"
log_message "總共公司數量: $total_files"
log_message "成功公司: $successful_companies"
log_message "失敗公司: $failed_companies"
log_message "成功率: ${final_success_rate}%"
log_message "結果已保存到: $OUTPUT_DIR"
log_message "完成時間: $(date)"
log_message "========================================================"

# 顯示 parallel 的作業日誌統計
if [ -f "step1_parallel_joblog.txt" ]; then
    echo ""
    echo "並行處理統計:"
    echo "作業日誌: step1_parallel_joblog.txt"
    awk 'NR>1 {
        if ($7 == 0) success++; else failed++;
        total_time += $4
    } END {
        print "並行成功: " success
        print "並行失敗: " failed  
        print "總執行時間: " total_time " 秒"
        if (NR > 1) print "平均每個作業: " total_time/(NR-1) " 秒"
    }' step1_parallel_joblog.txt
fi

echo ""
echo "如果需要重新運行失敗的公司，只需再次執行此腳本。"
echo "腳本會自動跳過已成功完成的公司。"
echo "詳細日誌請查看: $LOG_FILE"

# 清理鎖定文件
rm -f "$LOG_FILE.lock"

# 檢查是否有成功的結果，如果有則可以繼續Step2
if [ $successful_companies -gt 0 ]; then
    echo ""
    echo "🚀 Step1完成！可以繼續執行Step2："
    echo "   ./run_step2_parallel.sh  (推薦，並行版本)"
    echo "   ./run_step2.sh           (原版本)"
fi 
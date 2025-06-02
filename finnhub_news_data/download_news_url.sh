#!/bin/bash

# 抓取 S&P 500 公司新聞從 2021年1月1日 到 2025年5月23日
# 只抓取新聞的原始URL、最終URL和發布日期，不下載內容

# 設定參數
SP500_FILE="a.json"
OUTPUT_DIR="./sp500_news_urls"
START_DATE="2021-01-01"
END_DATE="2021-06-30"
PROGRESS_FILE="./download_progress.txt"
LOG_FILE="./download_log.txt"
VENV_PATH="../../.venv"

# 創建輸出目錄
mkdir -p "$OUTPUT_DIR"

# 檢查虛擬環境是否存在
if [ ! -d "$VENV_PATH" ]; then
    echo "錯誤: 找不到虛擬環境 $VENV_PATH"
    exit 1
fi

# 檢查 sp500.json 是否存在
if [ ! -f "$SP500_FILE" ]; then
    echo "錯誤: 找不到 $SP500_FILE 文件"
    exit 1
fi

# 計數器
total_companies=0
successful_companies=0
failed_companies=0
skipped_companies=0

# 初始化日誌文件
echo "開始時間: $(date)" > "$LOG_FILE"

echo "開始抓取 S&P 500 公司新聞資料從 $START_DATE 到 $END_DATE"
echo "輸出目錄: $OUTPUT_DIR"
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

# 函數：記錄日誌
log_message() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $message" >> "$LOG_FILE"
    echo "$message"
}

# 從 sp500.json 中讀取所有公司代碼
companies=$(source "$VENV_PATH/bin/activate" && python3 -c "
import json
with open('$SP500_FILE', 'r') as f:
    symbols = json.load(f)
for symbol in symbols:
    print(symbol)
")

# 處理每個公司
for symbol in $companies; do
    total_companies=$((total_companies + 1))
    
    # 檢查是否已經處理過這個公司
    if is_company_completed "$symbol"; then
        log_message "跳過已完成的公司: $symbol"
        skipped_companies=$((skipped_companies + 1))
        continue
    fi
    
    log_message "處理公司: $symbol ($total_companies/503)"
    
    # 執行爬蟲程式（使用虛擬環境）
    if bash -c "source '$VENV_PATH/bin/activate' && python crawl_50.py --type company --symbol '$symbol' --from-date '$START_DATE' --to-date '$END_DATE' --output-dir '$OUTPUT_DIR'" 2>> "$LOG_FILE"; then
        successful_companies=$((successful_companies + 1))
        mark_company_completed "$symbol"
        log_message "  ✅ 成功完成 $symbol"
    else
        failed_companies=$((failed_companies + 1))
        log_message "  ❌ 失敗 $symbol (可能超時或其他錯誤)"
    fi
    
    # 在每次請求之間添加短暫延遲，避免API限制
    sleep 2
    
    # 每處理10個公司顯示一次進度
    if [ $((($successful_companies + $failed_companies) % 10)) -eq 0 ]; then
        processed=$((successful_companies + failed_companies))
        current_success_rate=0
        if [ $processed -gt 0 ]; then
            current_success_rate=$(echo "scale=1; $successful_companies * 100 / $processed" | bc -l)
        fi
        log_message "  進度更新: 已處理 $processed 個公司，成功 $successful_companies 個 (${current_success_rate}%)"
    fi
done

# 計算最終統計
total_processed=$((successful_companies + failed_companies))
final_success_rate=0
if [ $total_processed -gt 0 ]; then
    final_success_rate=$(echo "scale=2; $successful_companies * 100 / $total_processed" | bc -l)
fi

log_message ""
log_message "========================================================"
log_message "抓取完成！"
log_message "總共公司數量: $((total_companies))"
log_message "跳過已完成公司: $skipped_companies"
log_message "實際處理公司: $total_processed"
log_message "成功公司: $successful_companies"
log_message "失敗公司: $failed_companies"
log_message "成功率: ${final_success_rate}%"
log_message "所有資料已保存到: $OUTPUT_DIR"
log_message "完成時間: $(date)"
log_message "========================================================"

echo ""
echo "如果需要重新運行失敗的公司，只需再次執行此腳本。"
echo "腳本會自動跳過已成功完成的公司。"
echo "詳細日誌請查看: $LOG_FILE" 
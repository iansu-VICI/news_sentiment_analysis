#!/bin/bash

# 平行化抓取 S&P 500 公司新聞從 2021年1月1日 到 2025年5月23日
# 使用 GNU parallel 進行並發處理 + 按月循環處理（解決單月限制問題）
# 
# 🔥 新功能：自動按月份分割時間範圍
# - 將4年多的時間範圍分割成53個月份單獨處理
# - 每個公司每個月份獨立抓取，然後自動合併
# - 避免了 crawl_50.py 單次只能處理一個月的限制

# 設定參數
SP500_FILE="sp500.json"
OUTPUT_DIR="./sp500_news_urls"
START_DATE="2021-01-01"
END_DATE="2025-05-23"
PROGRESS_FILE="./download_progress.txt"
LOG_FILE="./download_log.txt"
VENV_PATH="../../.venv"
MAX_JOBS=4  # 最大並發數量，避免API限制

# 檢查 GNU parallel 是否安裝
if ! command -v parallel &> /dev/null; then
    echo "錯誤: 需要安裝 GNU parallel"
    echo "Ubuntu/Debian: sudo apt-get install parallel"
    echo "CentOS/RHEL: sudo yum install parallel"
    exit 1
fi

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

# 初始化日誌文件
echo "開始時間 (並行版本): $(date)" > "$LOG_FILE"

echo "開始並行抓取 S&P 500 公司新聞資料"
echo "時間範圍: $START_DATE 到 $END_DATE"
echo "輸出目錄: $OUTPUT_DIR"
echo "並發數量: $MAX_JOBS"
echo ""
echo "🔥 月份循環處理模式已啟動"
echo "   - 自動將時間範圍分割成月份處理"
echo "   - 每個公司處理 53 個月份 (2021-01 到 2025-05)"
echo "   - 月份數據自動合併成最終文件"
echo "   - 支援中斷後重新執行（跳過已完成的公司）"
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

# 函數：生成月份範圍列表
generate_monthly_ranges() {
    local start_date="$1"
    local end_date="$2"
    
    python3 -c "
import datetime
from dateutil.relativedelta import relativedelta

start = datetime.datetime.strptime('$start_date', '%Y-%m-%d')
end = datetime.datetime.strptime('$end_date', '%Y-%m-%d')

current = start
while current <= end:
    # 計算當月的結束日期
    next_month = current + relativedelta(months=1)
    month_end = min(next_month - relativedelta(days=1), end)
    
    print(f'{current.strftime(\"%Y-%m-%d\")}:{month_end.strftime(\"%Y-%m-%d\")}')
    current = next_month
"
}

# 函數：合併JSON文件
merge_json_files() {
    local symbol="$1"
    local temp_dir="$2"
    local final_output="$3"
    
    python3 -c "
import json
import glob
import os

symbol = '$symbol'
temp_dir = '$temp_dir'
final_output = '$final_output'

# 查找所有該公司的臨時JSON文件
temp_files = glob.glob(os.path.join(temp_dir, f'{symbol}_*.json'))
temp_files.sort()

if not temp_files:
    print(f'未找到 {symbol} 的臨時文件')
    exit(1)

# 合併所有文件
all_news_data = []
first_file_meta = None

for temp_file in temp_files:
    try:
        with open(temp_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if first_file_meta is None:
            first_file_meta = {k: v for k, v in data.items() if k != 'news_data'}
            
        if 'news_data' in data:
            all_news_data.extend(data['news_data'])
            
    except Exception as e:
        print(f'讀取 {temp_file} 時出錯: {e}')

# 創建最終的合併文件
if first_file_meta and all_news_data:
    final_data = first_file_meta.copy()
    final_data['news_data'] = all_news_data
    final_data['total_news_fetched'] = len(all_news_data)
    final_data['valid_news'] = len(all_news_data)
    final_data['processed_count'] = len(all_news_data)
    
    # 更新時間範圍
    final_data['from_date'] = '$START_DATE'
    final_data['to_date'] = '$END_DATE'
    final_data['generated_time'] = '$(date +'%Y-%m-%d %H:%M:%S')'
    
    with open(final_output, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f'✅ 成功合併 {len(all_news_data)} 條新聞到 {final_output}')
    
    # 刪除臨時文件
    for temp_file in temp_files:
        os.remove(temp_file)
        
else:
    print(f'❌ 未找到有效數據來合併 {symbol}')
    exit(1)
"
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
    
    # 創建臨時目錄存放月份數據
    local temp_dir="$OUTPUT_DIR/temp_$symbol"
    mkdir -p "$temp_dir"
    
    # 生成月份範圍
    local monthly_ranges
    monthly_ranges=$(source "$VENV_PATH/bin/activate" && generate_monthly_ranges "$START_DATE" "$END_DATE")
    
    if [ -z "$monthly_ranges" ]; then
        log_message "[ERROR] ❌ 無法生成月份範圍 $symbol"
        return 1
    fi
    
    local total_months=$(echo "$monthly_ranges" | wc -l)
    local successful_months=0
    local month_count=0
    
    log_message "[INFO] $symbol: 需要處理 $total_months 個月份"
    
    # 逐月處理
    while IFS=':' read -r month_start month_end; do
        ((month_count++))
        local temp_output="$temp_dir/${symbol}_${month_start}.json"
        
        log_message "[MONTH] $symbol: 處理月份 $month_count/$total_months ($month_start 到 $month_end)"
        
        # 執行單月爬蟲程式
        if timeout 120 bash -c "source '$VENV_PATH/bin/activate' && python crawl_50.py --type company --symbol '$symbol' --from-date '$month_start' --to-date '$month_end' --output-dir '$temp_dir'" 2>/dev/null; then
            
            # 檢查是否生成了文件
            if [ -f "$temp_dir/${symbol}.json" ]; then
                mv "$temp_dir/${symbol}.json" "$temp_output"
                ((successful_months++))
                log_message "[MONTH-OK] $symbol: 月份 $month_start 成功"
            else
                log_message "[MONTH-EMPTY] $symbol: 月份 $month_start 無數據"
            fi
        else
            log_message "[MONTH-FAIL] $symbol: 月份 $month_start 失敗"
        fi
        
        # 短暫休息避免API限制
        sleep 1
        
    done <<< "$monthly_ranges"
    
    # 合併所有月份的數據
    if [ $successful_months -gt 0 ]; then
        log_message "[MERGE] $symbol: 開始合併 $successful_months 個月份的數據"
        
        if source "$VENV_PATH/bin/activate" && merge_json_files "$symbol" "$temp_dir" "$OUTPUT_DIR/${symbol}.json"; then
            mark_company_completed "$symbol"
            log_message "[SUCCESS] ✅ 成功完成 $symbol (處理了 $successful_months/$total_months 個月份)"
            
            # 清理臨時目錄
            rm -rf "$temp_dir"
            return 0
        else
            log_message "[MERGE-FAIL] ❌ $symbol: 合併失敗"
            return 1
        fi
    else
        log_message "[FAILED] ❌ 失敗 $symbol (所有月份都失敗)"
        rm -rf "$temp_dir"
        return 1
    fi
}

# 導出函數和變量，讓 parallel 可以使用
export -f process_single_company
export -f is_company_completed
export -f mark_company_completed
export -f log_message
export SP500_FILE OUTPUT_DIR START_DATE END_DATE PROGRESS_FILE LOG_FILE VENV_PATH

# 從 sp500.json 中讀取所有公司代碼
companies=$(source "$VENV_PATH/bin/activate" && python3 -c "
import json
with open('$SP500_FILE', 'r') as f:
    symbols = json.load(f)
for symbol in symbols:
    print(symbol)
")

# 計算總公司數量
total_companies=$(echo "$companies" | wc -l)
log_message "總公司數量: $total_companies"

# 使用 GNU parallel 並行處理
echo "$companies" | parallel -j "$MAX_JOBS" --progress --joblog parallel_joblog.txt process_single_company {}

# 計算最終統計
successful_companies=$(grep "^COMPLETED:" "$PROGRESS_FILE" 2>/dev/null | wc -l || echo 0)
failed_companies=$((total_companies - successful_companies))
final_success_rate=0
if [ $total_companies -gt 0 ]; then
    final_success_rate=$(echo "scale=2; $successful_companies * 100 / $total_companies" | bc -l)
fi

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
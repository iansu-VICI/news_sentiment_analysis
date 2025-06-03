#!/bin/bash

# 並行抓取 S&P 500 公司新聞（月份循環版本）
# 解決長時間範圍的超時問題，按月份分割處理後自動合併
# 使用 GNU parallel 進行並發處理

# 設定參數
SP500_FILE="sp500.json"
OUTPUT_DIR="./sp500_news_urls"
START_DATE="2021-01-01"
END_DATE="2025-05-23"
PROGRESS_FILE="./monthly_parallel_progress.txt"
LOG_FILE="./monthly_parallel_log.txt"
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
echo "並行月份循環版本開始時間: $(date)" > "$LOG_FILE"

echo "=== 並行抓取 S&P 500 公司新聞資料（月份循環版本）==="
echo "時間範圍: $START_DATE 到 $END_DATE"
echo "處理方式: 按月份循環 + 並行處理"
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

# 函數：檢查某個公司的某個月份是否已經處理完成
is_month_completed() {
    local symbol="$1"
    local month_start="$2"
    if [ -f "$PROGRESS_FILE" ]; then
        grep -q "^MONTH_COMPLETED:$symbol:$month_start$" "$PROGRESS_FILE"
        return $?
    fi
    return 1
}

# 函數：標記某個月份為已完成
mark_month_completed() {
    local symbol="$1"
    local month_start="$2"
    echo "MONTH_COMPLETED:$symbol:$month_start" >> "$PROGRESS_FILE"
}

# 函數：獲取某個公司已完成的月份數量
get_completed_months_count() {
    local symbol="$1"
    if [ -f "$PROGRESS_FILE" ]; then
        grep "^MONTH_COMPLETED:$symbol:" "$PROGRESS_FILE" | wc -l
    else
        echo 0
    fi
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
    
    # 生成月份範圍
    local monthly_ranges
    monthly_ranges=$(python3 -c "
import datetime
from dateutil.relativedelta import relativedelta

start = datetime.datetime.strptime('$START_DATE', '%Y-%m-%d')
end = datetime.datetime.strptime('$END_DATE', '%Y-%m-%d')

current = start
while current <= end:
    next_month = current + relativedelta(months=1)
    month_end = min(next_month - relativedelta(days=1), end)
    
    print(f'{current.strftime(\"%Y-%m-%d\")}:{month_end.strftime(\"%Y-%m-%d\")}')
    current = next_month
")
    
    if [ -z "$monthly_ranges" ]; then
        log_message "[ERROR] ❌ 無法生成月份範圍 $symbol"
        return 1
    fi
    
    local total_months=$(echo "$monthly_ranges" | wc -l)
    local successful_months=0
    local month_count=0
    local temp_files=()
    local symbol_lower=$(echo "$symbol" | tr '[:upper:]' '[:lower:]')
    
    # 檢查已完成的月份數量
    local completed_months_count=$(get_completed_months_count "$symbol")
    
    log_message "[INFO] $symbol: 需要處理 $total_months 個月份，已完成 $completed_months_count 個月份"
    
    # 逐月處理並收集所有新聞資料
    while IFS=':' read -r month_start month_end; do
        ((month_count++))
        
        # 檢查這個月份是否已經完成
        if is_month_completed "$symbol" "$month_start"; then
            log_message "[MONTH-SKIP] $symbol: 跳過已完成的月份 $month_count/$total_months ($month_start)"
            echo "跳過已完成的 $symbol 月份 $month_count/$total_months ($month_start)..."
            
            # 檢查是否有對應的臨時文件需要添加到列表中
            local temp_month_file="$OUTPUT_DIR/${symbol_lower}_${month_start}.json"
            if [ -f "$temp_month_file" ]; then
                temp_files+=("$temp_month_file")
            fi
            ((successful_months++))
            continue
        fi
        
        # 執行單月爬蟲程式，直接輸出到最終目錄
        # 設定合理的超時時間：每個月份最多10分鐘
        local estimated_time=600  # 10 分鐘
        
        log_message "[MONTH] $symbol: 處理月份 $month_count/$total_months ($month_start 到 $month_end，最多 $estimated_time 秒)"
        
        # 顯示處理進度
        echo "正在處理 $symbol 月份 $month_count/$total_months ($month_start)..."
        
        if python crawl_50.py --type company --symbol "$symbol" --from-date "$month_start" --to-date "$month_end" --output-dir "$OUTPUT_DIR"; then
            
            # 檢查是否生成了文件（使用小寫符號名稱）
            local month_file="$OUTPUT_DIR/${symbol_lower}.json"
            
            if [ -f "$month_file" ]; then
                if [ $total_months -eq 1 ]; then
                    # 如果只有一個月份，直接使用這個文件
                    mark_month_completed "$symbol" "$month_start"
                    log_message "[MONTH-OK] $symbol: 月份 $month_start 成功 (單月份，直接使用)"
                    ((successful_months++))
                else
                    # 多月份時重命名為臨時文件
                    local temp_month_file="$OUTPUT_DIR/${symbol_lower}_${month_start}.json"
                    mv "$month_file" "$temp_month_file"
                    temp_files+=("$temp_month_file")
                    mark_month_completed "$symbol" "$month_start"
                    ((successful_months++))
                    log_message "[MONTH-OK] $symbol: 月份 $month_start 成功"
                fi
            else
                log_message "[MONTH-EMPTY] $symbol: 月份 $month_start 無數據"
            fi
        else
            log_message "[MONTH-FAIL] $symbol: 月份 $month_start 失敗"
        fi
        
        # 短暫休息避免API限制
        sleep 5
        
    done <<< "$monthly_ranges"
    
    # 處理結果
    if [ $successful_months -gt 0 ]; then
        local final_output="$OUTPUT_DIR/${symbol_lower}.json"
        
        if [ $total_months -eq 1 ]; then
            # 單月份情況：檔案已經存在且正確命名，無需額外處理
            mark_company_completed "$symbol"
            log_message "[SUCCESS] ✅ 成功完成 $symbol (單月份處理)"
            return 0
        else
            # 多月份情況：需要合併所有月份的檔案到最終檔案
            log_message "[MERGE] $symbol: 開始合併 $successful_months 個月份的數據到 $final_output"
            
            # 使用 Python 合併 JSON 文件
            python3 -c "
import json
import os
from datetime import datetime

symbol = '$symbol'
symbol_lower = '${symbol_lower}'
final_output = '$final_output'
temp_files = $(printf "'%s' " "${temp_files[@]}")
start_date = '$START_DATE'
end_date = '$END_DATE'

temp_file_list = temp_files.strip().split() if temp_files.strip() else []

if not temp_file_list:
    print(f'❌ 未找到 {symbol} 的臨時文件')
    exit(1)

# 合併所有文件
all_news_data = []
first_file_meta = None
total_fetched = 0
total_filtered = 0

for temp_file in temp_file_list:
    if not temp_file:
        continue
        
    try:
        with open(temp_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if first_file_meta is None:
            # 保存第一個文件的元數據作為模板
            first_file_meta = {k: v for k, v in data.items() if k != 'news_data'}
            
        if 'news_data' in data:
            all_news_data.extend(data['news_data'])
            
        # 累計統計數據
        total_fetched += data.get('total_news_fetched', 0)
        total_filtered += data.get('filtered_out', 0)
            
    except Exception as e:
        print(f'❌ 讀取 {temp_file} 時出錯: {e}')

# 創建最終的合併文件
if first_file_meta and all_news_data:
    final_data = first_file_meta.copy()
    final_data['news_data'] = all_news_data
    final_data['total_news_fetched'] = total_fetched
    final_data['filtered_out'] = total_filtered
    final_data['valid_news'] = len(all_news_data)
    final_data['processed_count'] = len(all_news_data)
    
    # 更新時間範圍和處理信息
    final_data['from_date'] = start_date
    final_data['to_date'] = end_date
    final_data['generated_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    final_data['processed_months'] = $successful_months
    final_data['total_months'] = $total_months
    
    with open(final_output, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f'✅ 成功合併 {len(all_news_data)} 條新聞到 {final_output}')
    print(f'   總獲取: {total_fetched} 條，過濾: {total_filtered} 條，有效: {len(all_news_data)} 條')
    
    # 刪除臨時文件
    for temp_file in temp_file_list:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
            print(f'🗑️  已刪除臨時文件: {temp_file}')
        
else:
    print(f'❌ 未找到有效數據來合併 {symbol}')
    exit(1)
"
            
            if [ $? -eq 0 ]; then
                mark_company_completed "$symbol"
                log_message "[SUCCESS] ✅ 成功完成 $symbol (合併了 $successful_months/$total_months 個月份)"
                return 0
            else
                log_message "[MERGE-FAIL] ❌ $symbol: 合併失敗"
                return 1
            fi
        fi
    else
        log_message "[FAILED] ❌ 失敗 $symbol (所有月份都失敗)"
        return 1
    fi
}

# 導出函數和變量，讓 parallel 可以使用
export -f process_single_company
export -f is_company_completed
export -f mark_company_completed
export -f is_month_completed
export -f mark_month_completed
export -f get_completed_months_count
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
echo "開始並行月份循環處理..."

# 使用 GNU parallel 並行處理
echo "$companies" | parallel -j "$MAX_JOBS" --progress --joblog monthly_parallel_joblog.txt process_single_company {}

# 計算最終統計
successful_companies=$(grep "^COMPLETED:" "$PROGRESS_FILE" 2>/dev/null | wc -l || echo 0)
failed_companies=$((total_companies - successful_companies))
final_success_rate=0
if [ $total_companies -gt 0 ]; then
    final_success_rate=$(echo "scale=2; $successful_companies * 100 / $total_companies" | bc -l)
fi

echo ""
echo "========================================================"
echo "並行月份循環處理完成！"
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
log_message "並行月份循環處理完成！"
log_message "總共公司數量: $total_companies"
log_message "成功公司: $successful_companies"
log_message "失敗公司: $failed_companies"
log_message "成功率: ${final_success_rate}%"
log_message "所有資料已保存到: $OUTPUT_DIR"
log_message "完成時間: $(date)"
log_message "========================================================"

# 顯示 parallel 的作業日誌統計
if [ -f "monthly_parallel_joblog.txt" ]; then
    echo ""
    echo "並行處理統計:"
    echo "作業日誌: monthly_parallel_joblog.txt"
    awk 'NR>1 {
        if ($7 == 0) success++; else failed++;
        total_time += $4
    } END {
        print "並行成功: " success
        print "並行失敗: " failed  
        print "總執行時間: " total_time " 秒"
        if (NR > 1) print "平均每個作業: " total_time/(NR-1) " 秒"
    }' monthly_parallel_joblog.txt
fi

echo ""
echo "如果需要重新運行失敗的公司，只需再次執行此腳本。"
echo "腳本會自動跳過已成功完成的公司。"
echo "詳細日誌請查看: $LOG_FILE"

# 清理鎖定文件
rm -f "$LOG_FILE.lock" 
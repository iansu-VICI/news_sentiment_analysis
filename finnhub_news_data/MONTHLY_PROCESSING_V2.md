# 月份級別進度追蹤版本 - 使用指南

## 概述

這個升級版的月份處理系統提供了**月份級別的進度追蹤**，可以避免重複處理已完成的月份，大幅提升恢復處理效率。

## 主要功能

### 1. 雙層進度追蹤
- **公司級別**: 跳過已完全完成的公司
- **月份級別**: 跳過已完成的特定月份

### 2. 智能恢復
- 腳本被中斷後，重新運行會自動跳過已處理的月份
- 只處理未完成的月份，節省大量時間

### 3. 進度監控工具
- 提供詳細的進度報告
- 可查看個別公司的月份處理狀態

## 主要腳本

### 1. `download_news_url_monthly_parallel.sh`
主要的並行處理腳本，具備月份級別進度追蹤。

```bash
# 基本使用
./download_news_url_monthly_parallel.sh

# 腳本會自動：
# - 跳過已完成的公司
# - 跳過已完成的月份
# - 繼續處理未完成的部分
```

**關鍵改進**:
- 每完成一個月份會立即記錄進度
- 可以精確恢復到月份級別
- 顯示更詳細的處理狀態

### 2. `check_monthly_progress.py`
進度檢查和管理工具。

```bash
# 查看總體進度
python check_monthly_progress.py

# 查看特定公司進度
python check_monthly_progress.py --company AAPL

# 清除某公司進度（重新處理）
python check_monthly_progress.py --clear-company AAPL
```

### 3. `merge_monthly_files.py`
合併工具（原有功能保持不變）。

```bash
# 合併單一公司
python merge_monthly_files.py AAPL

# 合併所有公司
python merge_monthly_files.py --all
```

## 進度文件格式

進度記錄在 `monthly_parallel_progress.txt` 文件中：

```
COMPLETED:AAPL                    # 公司完全完成
MONTH_COMPLETED:MSFT:2021-01-01   # 特定月份完成
MONTH_COMPLETED:MSFT:2021-02-01
MONTH_COMPLETED:MSFT:2021-03-01
...
```

## 使用場景

### 場景 1: 首次運行
```bash
./download_news_url_monthly_parallel.sh
```
- 從頭開始處理所有公司和月份
- 每完成一個月份就記錄進度

### 場景 2: 中斷後恢復
```bash
# 腳本被中斷（Ctrl+C 或系統問題）
# 重新運行同樣的命令
./download_news_url_monthly_parallel.sh
```
- 自動跳過已完成的公司和月份
- 只處理剩餘部分
- 顯示 "跳過已完成的月份" 訊息

### 場景 3: 檢查進度
```bash
# 查看總體進度
python check_monthly_progress.py
```
輸出範例：
```
=== 月份級別處理進度報告 ===
時間範圍: 2021-01-01 到 2025-05-23
總公司數: 500
每公司月份數: 53
總月份任務數: 26500

=== 總體統計 ===
完全完成的公司: 45/500 (9.0%)
部分完成的公司: 23
未開始的公司: 432
完成的月份任務: 3420/26500 (12.9%)
```

### 場景 4: 檢查特定公司
```bash
python check_monthly_progress.py --company AAPL
```
輸出範例：
```
=== AAPL 詳細進度 ===
總月份數: 53
已完成: 15
剩餘: 38
進度: 28.3%

月份狀態:
   1. 2021-01-01 ✅
   2. 2021-02-01 ✅
   3. 2021-03-01 ⏳
   ...
```

### 場景 5: 重新處理某公司
```bash
# 清除進度記錄
python check_monthly_progress.py --clear-company AAPL

# 重新運行腳本，會重新處理AAPL
./download_news_url_monthly_parallel.sh
```

## 性能提升

### 時間節省
假設有 500 家公司，每家 53 個月份：
- **總任務數**: 26,500 個月份任務
- **中斷在 50% 進度**: 傳統方法需重新開始，新方法只處理剩餘 50%
- **節省時間**: 約 50% 的處理時間

### 精確恢復
- **月份級別**: 精確到每個月份的完成狀態
- **即時記錄**: 每完成一個月份立即保存進度
- **容錯性強**: 即使在月份處理中途中斷，也不會丟失已完成的部分

## 文件結構

```
finnhub_news_data/
├── download_news_url_monthly_parallel.sh    # 主處理腳本
├── check_monthly_progress.py                # 進度檢查工具
├── merge_monthly_files.py                   # 合併工具
├── monthly_parallel_progress.txt            # 進度記錄（自動生成）
├── monthly_parallel_log.txt                 # 詳細日誌（自動生成）
├── monthly_parallel_joblog.txt              # Parallel作業日誌（自動生成）
└── sp500_news_urls/                         # 輸出目錄
    ├── aapl.json                            # 合併後的最終文件
    ├── msft_2021-01-01.json                 # 臨時月份文件（處理中）
    └── ...
```

## 注意事項

1. **進度文件保護**: 不要手動編輯 `monthly_parallel_progress.txt`
2. **並發安全**: 使用 flock 確保進度記錄的原子性
3. **存儲空間**: 臨時月份文件會在合併後自動刪除
4. **API限制**: 仍需遵守 Finnhub API 的請求限制

## 故障排除

### 進度記錄錯亂
```bash
# 檢查進度文件
cat monthly_parallel_progress.txt

# 如果需要，清除特定公司
python check_monthly_progress.py --clear-company SYMBOL
```

### 臨時文件殘留
```bash
# 查找殘留的月份文件
ls sp500_news_urls/*_20*.json

# 使用合併工具清理
python merge_monthly_files.py --all
```

### 重新開始
```bash
# 清空所有進度（慎用！）
rm -f monthly_parallel_progress.txt
rm -f monthly_parallel_log.txt
rm -f monthly_parallel_joblog.txt
```

## 效益總結

✅ **精確恢復**: 月份級別的進度追蹤  
✅ **時間節省**: 避免重複處理已完成的部分  
✅ **狀態透明**: 詳細的進度報告和監控  
✅ **容錯性強**: 支援各種中斷情況的恢復  
✅ **向下兼容**: 保持與原有工作流程的兼容性 
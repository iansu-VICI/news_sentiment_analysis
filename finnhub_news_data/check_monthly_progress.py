#!/usr/bin/env python3
"""
檢查月份級別的處理進度
"""

import argparse
import json
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

def parse_progress_file(progress_file="./monthly_parallel_progress.txt"):
    """解析進度文件"""
    completed_companies = set()
    completed_months = {}  # symbol -> [month_dates]
    
    if not os.path.exists(progress_file):
        return completed_companies, completed_months
    
    with open(progress_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("COMPLETED:"):
                symbol = line.split(":", 1)[1]
                completed_companies.add(symbol)
            elif line.startswith("MONTH_COMPLETED:"):
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    symbol = parts[1]
                    month_date = parts[2]
                    if symbol not in completed_months:
                        completed_months[symbol] = []
                    completed_months[symbol].append(month_date)
    
    return completed_companies, completed_months

def generate_monthly_ranges(start_date="2021-01-01", end_date="2025-05-23"):
    """生成月份範圍列表"""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    ranges = []
    current = start
    while current <= end:
        next_month = current + relativedelta(months=1)
        month_end = min(next_month - relativedelta(days=1), end)
        ranges.append(current.strftime('%Y-%m-%d'))
        current = next_month
    
    return ranges

def load_sp500_symbols(sp500_file="sp500.json"):
    """載入S&P 500公司列表"""
    try:
        with open(sp500_file, 'r') as f:
            return json.load(f)
    except:
        return []

def check_progress(start_date="2021-01-01", end_date="2025-05-23", 
                  progress_file="./monthly_parallel_progress.txt",
                  sp500_file="sp500.json"):
    """檢查整體進度"""
    
    # 載入數據
    symbols = load_sp500_symbols(sp500_file)
    completed_companies, completed_months = parse_progress_file(progress_file)
    monthly_ranges = generate_monthly_ranges(start_date, end_date)
    
    if not symbols:
        print("❌ 無法載入S&P 500公司列表")
        return
    
    total_companies = len(symbols)
    total_months_per_company = len(monthly_ranges)
    total_month_tasks = total_companies * total_months_per_company
    
    # 計算完成統計
    fully_completed_companies = len(completed_companies)
    partially_completed_companies = 0
    total_completed_month_tasks = 0
    
    print("=== 月份級別處理進度報告 ===")
    print(f"時間範圍: {start_date} 到 {end_date}")
    print(f"總公司數: {total_companies}")
    print(f"每公司月份數: {total_months_per_company}")
    print(f"總月份任務數: {total_month_tasks}")
    print("")
    
    # 分析每家公司的進度
    for symbol in symbols:
        company_completed_months = completed_months.get(symbol, [])
        completed_count = len(company_completed_months)
        total_completed_month_tasks += completed_count
        
        if symbol in completed_companies:
            # 完全完成的公司
            continue
        elif completed_count > 0:
            # 部分完成的公司
            partially_completed_companies += 1
    
    # 顯示總體統計
    print("=== 總體統計 ===")
    print(f"完全完成的公司: {fully_completed_companies}/{total_companies} ({fully_completed_companies/total_companies*100:.1f}%)")
    print(f"部分完成的公司: {partially_completed_companies}")
    print(f"未開始的公司: {total_companies - fully_completed_companies - partially_completed_companies}")
    print(f"完成的月份任務: {total_completed_month_tasks}/{total_month_tasks} ({total_completed_month_tasks/total_month_tasks*100:.1f}%)")
    print("")
    
    return {
        'total_companies': total_companies,
        'fully_completed': fully_completed_companies,
        'partially_completed': partially_completed_companies,
        'total_month_tasks': total_month_tasks,
        'completed_month_tasks': total_completed_month_tasks,
        'completed_companies': completed_companies,
        'completed_months': completed_months
    }

def show_company_detail(symbol, start_date="2021-01-01", end_date="2025-05-23",
                       progress_file="./monthly_parallel_progress.txt"):
    """顯示特定公司的詳細進度"""
    
    completed_companies, completed_months = parse_progress_file(progress_file)
    monthly_ranges = generate_monthly_ranges(start_date, end_date)
    
    symbol = symbol.upper()
    print(f"=== {symbol} 詳細進度 ===")
    
    if symbol in completed_companies:
        print("✅ 此公司已完全完成")
        return
    
    company_completed_months = set(completed_months.get(symbol, []))
    total_months = len(monthly_ranges)
    completed_count = len(company_completed_months)
    
    print(f"總月份數: {total_months}")
    print(f"已完成: {completed_count}")
    print(f"剩餘: {total_months - completed_count}")
    print(f"進度: {completed_count/total_months*100:.1f}%")
    print("")
    
    print("月份狀態:")
    for i, month_start in enumerate(monthly_ranges, 1):
        status = "✅" if month_start in company_completed_months else "⏳"
        print(f"  {i:2d}. {month_start} {status}")

def clear_company_progress(symbol, progress_file="./monthly_parallel_progress.txt"):
    """清除特定公司的進度（用於重新處理）"""
    
    if not os.path.exists(progress_file):
        print(f"進度文件不存在: {progress_file}")
        return
    
    symbol = symbol.upper()
    lines_to_keep = []
    removed_lines = 0
    
    with open(progress_file, 'r') as f:
        for line in f:
            line = line.strip()
            if (line.startswith(f"COMPLETED:{symbol}") or 
                line.startswith(f"MONTH_COMPLETED:{symbol}:")):
                removed_lines += 1
            else:
                lines_to_keep.append(line)
    
    # 重寫文件
    with open(progress_file, 'w') as f:
        for line in lines_to_keep:
            if line:  # 避免空行
                f.write(line + '\n')
    
    print(f"已清除 {symbol} 的進度記錄，移除了 {removed_lines} 行")

def main():
    parser = argparse.ArgumentParser(description='檢查月份級別的處理進度')
    parser.add_argument('--start-date', default='2021-01-01', help='起始日期')
    parser.add_argument('--end-date', default='2025-05-23', help='結束日期')
    parser.add_argument('--progress-file', default='./monthly_parallel_progress.txt', help='進度文件路徑')
    parser.add_argument('--sp500-file', default='sp500.json', help='S&P 500文件路徑')
    parser.add_argument('--company', help='顯示特定公司的詳細進度')
    parser.add_argument('--clear-company', help='清除特定公司的進度記錄')
    
    args = parser.parse_args()
    
    if args.clear_company:
        clear_company_progress(args.clear_company, args.progress_file)
    elif args.company:
        show_company_detail(args.company, args.start_date, args.end_date, args.progress_file)
    else:
        check_progress(args.start_date, args.end_date, args.progress_file, args.sp500_file)

if __name__ == "__main__":
    main() 
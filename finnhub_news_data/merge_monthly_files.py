#!/usr/bin/env python3
"""
合併按月份分開的新聞JSON檔案到單一檔案
"""

import json
import os
import glob
import argparse
from datetime import datetime

def merge_monthly_files(symbol, output_dir="./sp500_news_urls"):
    """合併指定公司的所有月份檔案"""
    symbol_lower = symbol.lower()
    
    # 尋找所有該公司的月份檔案
    pattern = os.path.join(output_dir, f"{symbol_lower}_*.json")
    monthly_files = sorted(glob.glob(pattern))
    
    if not monthly_files:
        print(f"❌ 未找到 {symbol} 的月份檔案")
        return False
    
    print(f"找到 {len(monthly_files)} 個 {symbol} 的月份檔案:")
    for f in monthly_files:
        print(f"  - {os.path.basename(f)}")
    
    # 合併所有檔案
    all_news_data = []
    first_file_meta = None
    total_fetched = 0
    total_filtered = 0
    
    for monthly_file in monthly_files:
        try:
            with open(monthly_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if first_file_meta is None:
                # 保存第一個檔案的元數據作為模板
                first_file_meta = {k: v for k, v in data.items() if k != 'news_data'}
            
            if 'news_data' in data:
                all_news_data.extend(data['news_data'])
            
            # 累計統計數據
            total_fetched += data.get('total_news_fetched', 0)
            total_filtered += data.get('filtered_out', 0)
            
        except Exception as e:
            print(f"❌ 讀取 {monthly_file} 時出錯: {e}")
            continue
    
    if not first_file_meta or not all_news_data:
        print(f"❌ 未找到有效數據來合併 {symbol}")
        return False
    
    # 計算日期範圍
    if all_news_data:
        timestamps = [news.get('datetime', 0) for news in all_news_data if news.get('datetime')]
        if timestamps:
            min_timestamp = min(timestamps)
            max_timestamp = max(timestamps)
            from_date = datetime.fromtimestamp(min_timestamp).strftime('%Y-%m-%d')
            to_date = datetime.fromtimestamp(max_timestamp).strftime('%Y-%m-%d')
        else:
            from_date = first_file_meta.get('from_date', '未知')
            to_date = first_file_meta.get('to_date', '未知')
    else:
        from_date = first_file_meta.get('from_date', '未知')
        to_date = first_file_meta.get('to_date', '未知')
    
    # 創建最終的合併檔案
    final_data = {
        'symbol': symbol,
        'from_date': from_date,
        'to_date': to_date,
        'total_news_fetched': total_fetched,
        'filtered_out': total_filtered,
        'valid_news': len(all_news_data),
        'processed_count': len(all_news_data),
        'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'processed_files': len(monthly_files),
        'source_files': [os.path.basename(f) for f in monthly_files],
        'merged_by': 'merge_monthly_files.py',
        'news_data': all_news_data
    }
    
    # 保存合併後的檔案
    final_output = os.path.join(output_dir, f"{symbol_lower}.json")
    
    with open(final_output, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 成功合併 {symbol} 的 {len(monthly_files)} 個月份檔案")
    print(f"   總獲取: {total_fetched} 條，過濾: {total_filtered} 條，有效: {len(all_news_data)} 條")
    print(f"   日期範圍: {from_date} 到 {to_date}")
    print(f"   輸出檔案: {final_output}")
    
    # 刪除原始月份檔案
    for monthly_file in monthly_files:
        os.remove(monthly_file)
        print(f"🗑️  已刪除: {os.path.basename(monthly_file)}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='合併按月份分開的新聞JSON檔案')
    parser.add_argument('symbol', nargs='?', help='公司股票代碼（如 AAPL, MSFT）')
    parser.add_argument('--output-dir', default='./sp500_news_urls', help='輸出目錄')
    parser.add_argument('--all', action='store_true', help='處理輸出目錄中所有的月份檔案')
    
    args = parser.parse_args()
    
    if args.all:
        # 找出所有有月份檔案的公司
        pattern = os.path.join(args.output_dir, "*_????-??-??.json")
        all_monthly_files = glob.glob(pattern)
        
        if not all_monthly_files:
            print("❌ 未找到任何月份檔案")
            return
        
        # 提取所有公司符號
        symbols = set()
        for f in all_monthly_files:
            basename = os.path.basename(f)
            symbol = basename.split('_')[0].upper()
            symbols.add(symbol)
        
        print(f"找到 {len(symbols)} 家公司的月份檔案: {', '.join(sorted(symbols))}")
        
        for symbol in sorted(symbols):
            print(f"\n處理 {symbol}...")
            merge_monthly_files(symbol, args.output_dir)
    else:
        if not args.symbol:
            parser.error("需要提供公司符號，或使用 --all 處理所有檔案")
        merge_monthly_files(args.symbol.upper(), args.output_dir)

if __name__ == "__main__":
    main() 
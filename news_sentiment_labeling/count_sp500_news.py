#!/usr/bin/env python3
"""
統計S&P 500公司新聞數量
計算sp500.json中各公司2021-01-01到2025-05-23的新聞數量
"""

import os
import sys
import json
import pandas as pd
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pathlib import Path

# 添加finnhub_newsdata目錄到路徑以使用utils
sys.path.append("../finnhub_newsdata")

try:
    from utils import get_company_news, finnhub_client
except ImportError:
    print("❌ 無法導入utils模組，請確認finnhub_newsdata目錄中有utils.py")
    sys.exit(1)

def load_sp500_companies(sp500_file):
    """
    從sp500.json文件中讀取公司列表
    
    Args:
        sp500_file: sp500.json文件路徑
    
    Returns:
        list: 公司股票代碼列表
    """
    try:
        with open(sp500_file, 'r', encoding='utf-8') as f:
            companies = json.load(f)
        
        if isinstance(companies, list):
            print(f"✅ 成功讀取 {len(companies)} 家S&P 500公司")
            return companies
        else:
            print("❌ sp500.json格式不正確，應該是公司代碼數組")
            return []
            
    except FileNotFoundError:
        print(f"❌ 找不到文件: {sp500_file}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析錯誤: {e}")
        return []
    except Exception as e:
        print(f"❌ 讀取文件時出錯: {e}")
        return []

def count_company_news(symbol, from_date, to_date, max_retries=3):
    """
    計算單個公司在指定期間的新聞數量
    API一次只能抓一個月，所以需要分月處理
    
    Args:
        symbol: 公司股票代碼
        from_date: 開始日期 (YYYY-MM-DD)
        to_date: 結束日期 (YYYY-MM-DD)
        max_retries: 最大重試次數
    
    Returns:
        int: 新聞數量，如果失敗返回None
    """
    try:
        # 轉換日期
        start_date = datetime.strptime(from_date, "%Y-%m-%d")
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        
        total_news_count = 0
        current_date = start_date
        
        # 分月處理
        while current_date <= end_date:
            # 計算當月的結束日期
            month_end = current_date + relativedelta(months=1) - timedelta(days=1)
            if month_end > end_date:
                month_end = end_date
            
            # 格式化日期
            month_start_str = current_date.strftime("%Y-%m-%d")
            month_end_str = month_end.strftime("%Y-%m-%d")
            
            # 獲取當月新聞
            for attempt in range(max_retries):
                try:
                    news_data = get_company_news(symbol, month_start_str, month_end_str)
                    
                    if news_data is not None:
                        month_count = len(news_data)
                        total_news_count += month_count
                        break
                    else:
                        if attempt == max_retries - 1:
                            print(f"    警告: {symbol} {month_start_str} 無新聞數據")
                        
                except Exception as e:
                    if attempt == max_retries - 1:
                        print(f"    錯誤: 獲取 {symbol} {month_start_str} 新聞時出錯: {e}")
                    
                if attempt < max_retries - 1:
                    time.sleep(1)
            
            # 移到下一個月
            current_date = current_date + relativedelta(months=1)
            
            # 短暫延遲避免API頻率限制
            time.sleep(0.2)
        
        return total_news_count
        
    except Exception as e:
        print(f"    嚴重錯誤: 處理 {symbol} 日期範圍時出錯: {e}")
        return None

def save_results(results, output_file):
    """
    保存結果到CSV文件
    
    Args:
        results: 結果列表
        output_file: 輸出文件路徑
    """
    try:
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✅ 結果已保存到: {output_file}")
        
        # 顯示統計信息
        total_companies = len(df)
        successful_companies = len(df[df['news_count'].notna()])
        total_news = df['news_count'].sum()
        
        print(f"\n📊 統計摘要:")
        print(f"  總公司數: {total_companies}")
        print(f"  成功獲取數據: {successful_companies}")
        print(f"  總新聞數量: {int(total_news):,}")
        print(f"  平均每家公司: {total_news/successful_companies:.1f} 條新聞")
        
        # 顯示新聞數量最多的前10家公司
        top_companies = df[df['news_count'].notna()].nlargest(10, 'news_count')
        print(f"\n🏆 新聞數量排行榜 (前10名):")
        for i, row in top_companies.iterrows():
            print(f"  {row['rank']:2d}. {row['symbol']:5s}: {int(row['news_count']):,} 條新聞")
            
    except Exception as e:
        print(f"❌ 保存結果時出錯: {e}")

def main():
    """主函數"""
    print("=== S&P 500公司新聞數量統計 ===")
    print("日期範圍: 2021-01-01 到 2025-05-23")
    print("=" * 50)
    
    # 設定參數
    sp500_file = "../sp500.json"
    from_date = "2021-01-01"
    to_date = "2025-05-23"
    output_file = "./sp500_news_count.csv"
    
    # 讀取S&P 500公司列表
    companies = load_sp500_companies(sp500_file)
    if not companies:
        return
    
    print(f"\n開始統計 {len(companies)} 家公司的新聞數量...")
    print(f"時間範圍: {from_date} 到 {to_date}")
    print("-" * 50)
    
    # 統計結果
    results = []
    successful_count = 0
    failed_count = 0
    
    # 處理每個公司
    for i, symbol in enumerate(companies, 1):
        print(f"[{i:3d}/{len(companies):3d}] 處理 {symbol}...", end=" ", flush=True)
        
        # 獲取新聞數量
        news_count = count_company_news(symbol, from_date, to_date)
        
        if news_count is not None:
            print(f"✅ {news_count:,} 條新聞")
            successful_count += 1
            status = "success"
        else:
            print(f"❌ 失敗")
            failed_count += 1
            status = "failed"
        
        # 記錄結果
        results.append({
            'rank': i,
            'symbol': symbol,
            'news_count': news_count,
            'status': status,
            'date_range': f"{from_date} to {to_date}",
            'processed_time': datetime.now().isoformat()
        })
        
        # 避免API頻率限制
        if i % 10 == 0:
            print(f"    已處理 {i} 家公司，暫停2秒...")
            time.sleep(2)
        else:
            time.sleep(0.5)
    
    print("-" * 50)
    print(f"處理完成！成功: {successful_count}, 失敗: {failed_count}")
    
    # 保存結果
    if results:
        save_results(results, output_file)
    else:
        print("❌ 無結果可保存")

if __name__ == "__main__":
    main() 
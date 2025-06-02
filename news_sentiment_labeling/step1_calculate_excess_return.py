#!/usr/bin/env python3
"""
Step1: 計算新聞發布後三個交易日的excess return並進行標註
"""

import os
import sys
import json
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import glob
from pathlib import Path

def get_market_data(symbol, start_date, end_date, max_retries=3):
    """
    獲取股票和市場數據
    
    Args:
        symbol: 股票代碼
        start_date: 開始日期
        end_date: 結束日期
        max_retries: 最大重試次數
    
    Returns:
        tuple: (stock_data, market_data) 或 (None, None) 如果失敗
    """
    for attempt in range(max_retries):
        try:
            # 獲取股票數據
            stock = yf.Ticker(symbol)
            stock_data = stock.history(start=start_date, end=end_date)
            
            # 獲取市場數據 (使用SPY作為市場基準)
            market = yf.Ticker("SPY")
            market_data = market.history(start=start_date, end=end_date)
            
            if len(stock_data) > 0 and len(market_data) > 0:
                return stock_data, market_data
            else:
                print(f"  警告: {symbol} 在 {start_date} 到 {end_date} 期間無數據 (嘗試 {attempt + 1}/{max_retries})")
                
        except Exception as e:
            print(f"  錯誤: 獲取 {symbol} 數據時出錯: {e} (嘗試 {attempt + 1}/{max_retries})")
            
        if attempt < max_retries - 1:
            print(f"  等待2秒後重試...")
            import time
            time.sleep(2)
    
    return None, None

def calculate_excess_return(stock_data, market_data, news_date, trading_days=3):
    """
    計算新聞發布後指定交易日的excess return
    
    Args:
        stock_data: 股票價格數據
        market_data: 市場價格數據  
        news_date: 新聞發布日期
        trading_days: 計算的交易日數
    
    Returns:
        float: excess return (股票收益率 - 市場收益率)，如果計算失敗返回None
    """
    try:
        # 智能處理時區信息
        if stock_data.index.tz is not None:
            stock_data.index = stock_data.index.tz_localize(None)
        if market_data.index.tz is not None:
            market_data.index = market_data.index.tz_localize(None)
        
        # 確保索引是datetime類型
        stock_data.index = pd.to_datetime(stock_data.index)
        market_data.index = pd.to_datetime(market_data.index)
        
        # 轉換新聞日期
        news_date = pd.to_datetime(news_date)
        if news_date.tz is not None:
            news_date = news_date.tz_localize(None)
        
        # 找到新聞發布日期或之後的第一個交易日
        # 將新聞日期也轉換為datetime對象進行比較
        news_datetime = pd.to_datetime(news_date)
        available_dates = stock_data.index[stock_data.index >= news_datetime]
        if len(available_dates) == 0:
            return None
            
        start_date = available_dates[0]
        
        # 找到結束日期（start_date後的第trading_days個交易日）
        future_dates = stock_data.index[stock_data.index > start_date]
        if len(future_dates) < trading_days:
            return None
            
        end_date = future_dates[trading_days - 1]
        
        # 計算股票收益率
        start_price = stock_data.loc[start_date, 'Close']
        end_price = stock_data.loc[end_date, 'Close']
        stock_return = (end_price - start_price) / start_price
        
        # 計算市場收益率
        market_start_price = market_data.loc[start_date, 'Close']
        market_end_price = market_data.loc[end_date, 'Close']
        market_return = (market_end_price - market_start_price) / market_start_price
        
        # 計算excess return
        excess_return = stock_return - market_return
        
        return excess_return
        
    except Exception as e:
        print(f"    計算excess return時出錯: {e}")
        return None

def process_company_news(json_file_path, output_dir):
    """
    處理單個公司的新聞JSON文件
    優化版本：只抓取一次股價數據，為每個唯一日期計算一次excess return
    
    Args:
        json_file_path: JSON文件路徑
        output_dir: 輸出目錄
    
    Returns:
        bool: 是否成功處理
    """
    try:
        # 讀取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        symbol = data['symbol']
        news_data = data['news_data']
        
        if not news_data:
            print(f"  {symbol}: 無新聞數據")
            return False
        
        print(f"\n處理 {symbol}，共 {len(news_data)} 條新聞...")
        
        # 準備結果列表
        results = []
        
        # 獲取所有新聞的發布日期
        all_dates = []
        for news in news_data:
            publish_date = pd.to_datetime(news['publish_date']).date()
            all_dates.append(publish_date)
        
        # 找出唯一的發布日期
        unique_dates = list(set(all_dates))
        unique_dates.sort()
        
        print(f"  發現 {len(unique_dates)} 個唯一的發布日期")
        
        # 確定需要的股價數據範圍
        min_date = min(unique_dates) - timedelta(days=5)  # 提前幾天以確保有基準數據
        max_date = max(unique_dates) + timedelta(days=10)  # 延後10天確保有足夠的交易日
        
        # 一次性獲取股票和市場數據
        print(f"  獲取 {symbol} 從 {min_date} 到 {max_date} 的股價數據...")
        stock_data, market_data = get_market_data(symbol, min_date, max_date)
        
        if stock_data is None or market_data is None:
            print(f"  跳過 {symbol}: 無法獲取價格數據")
            return False
        
        # 為每個唯一日期計算excess return
        date_to_excess_return = {}
        print(f"  計算各日期的excess return...")
        
        for unique_date in unique_dates:
            publish_date_str = unique_date.strftime('%Y-%m-%d %H:%M:%S')  # 轉換為字符串格式
            excess_return = calculate_excess_return(stock_data, market_data, publish_date_str)
            date_to_excess_return[unique_date] = excess_return
            
            if excess_return is not None:
                print(f"    {unique_date}: {excess_return:.4f}")
            else:
                print(f"    {unique_date}: 計算失敗")
        
        # 處理每條新聞，使用預計算的excess return
        processed_count = 0
        
        for i, news in enumerate(news_data):
            try:
                publish_date = news['publish_date']
                publish_date_obj = pd.to_datetime(publish_date).date()
                
                # 從預計算的結果中獲取excess return
                excess_return = date_to_excess_return.get(publish_date_obj)
                
                if excess_return is not None:
                    # 進行標註：1 if excess_return > 0, 0 if excess_return <= 0
                    label = 1 if excess_return > 0 else 0
                    
                    # 添加到結果
                    results.append({
                        'symbol': symbol,
                        'headline': news['headline'],
                        'source': news['source'],
                        'publish_date': publish_date,
                        'original_url': news['original_url'],
                        'final_url': news['final_url'],
                        'is_yahoo_finance': news['is_yahoo_finance'],
                        'has_continue_reading': news['has_continue_reading'],
                        'excess_return_3days': excess_return,
                        'label': label
                    })
                    
                    processed_count += 1
                
            except Exception as e:
                print(f"    處理新聞 {i+1} 時出錯: {e}")
                continue
        
        # 保存結果到CSV
        if results:
            df = pd.DataFrame(results)
            output_file = os.path.join(output_dir, f"{symbol.lower()}_labeled.csv")
            df.to_csv(output_file, index=False, encoding='utf-8')
            
            print(f"  ✅ {symbol}: 成功處理 {len(results)} 條新聞，保存到 {output_file}")
            
            # 顯示標註統計
            positive_count = len(df[df['label'] == 1])
            negative_count = len(df[df['label'] == 0])
            print(f"    標註統計: 正面 {positive_count}, 負面 {negative_count}")
            print(f"    優化效果: 只計算了 {len(unique_dates)} 次excess return，而不是 {len(news_data)} 次")
            
            return True
        else:
            print(f"  ❌ {symbol}: 無有效數據")
            return False
            
    except Exception as e:
        print(f"處理 {json_file_path} 時出錯: {e}")
        return False

def main():
    """主函數"""
    print("=== Step1: 計算excess return並標註新聞 ===\n")
    
    # 設定路徑
    json_dir = "../finnhub_newsdata/sp500_news_urls"
    output_dir = "./news_data"
    
    # 創建輸出目錄
    os.makedirs(output_dir, exist_ok=True)
    
    # 查找所有JSON文件
    json_files = glob.glob(os.path.join(json_dir, "*.json"))
    
    if not json_files:
        print(f"錯誤: 在 {json_dir} 中未找到JSON文件")
        return
    
    print(f"找到 {len(json_files)} 個JSON文件")
    
    # 處理統計
    total_files = len(json_files)
    successful_files = 0
    
    # 處理每個JSON文件
    for i, json_file in enumerate(json_files):
        filename = os.path.basename(json_file)
        print(f"\n--- 處理文件 {i+1}/{total_files}: {filename} ---")
        
        if process_company_news(json_file, output_dir):
            successful_files += 1
    
    # 顯示最終統計
    print(f"\n=== 處理完成 ===")
    print(f"總文件數: {total_files}")
    print(f"成功處理: {successful_files}")
    print(f"失敗: {total_files - successful_files}")
    print(f"所有結果已保存到: {output_dir}")

if __name__ == "__main__":
    main() 
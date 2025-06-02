#!/usr/bin/env python3
"""
檢查S&P 500新聞統計進度
"""

import os
import json
import pandas as pd
from datetime import datetime

def check_progress():
    """檢查統計進度"""
    
    # 檢查輸出文件是否存在
    output_file = "./sp500_news_count.csv"
    sp500_file = "../sp500.json"
    
    if not os.path.exists(output_file):
        print("❌ 完整統計尚未開始或輸出文件不存在")
        return
    
    # 讀取完整的S&P 500列表
    try:
        with open(sp500_file, 'r') as f:
            all_companies = json.load(f)
        total_companies = len(all_companies)
    except:
        total_companies = 500  # 預估值
    
    # 讀取當前結果
    try:
        df = pd.read_csv(output_file)
        processed_companies = len(df)
        successful_companies = len(df[df['status'] == 'success'])
        failed_companies = len(df[df['status'] == 'failed'])
        
        # 計算進度
        progress_percent = (processed_companies / total_companies) * 100
        
        print(f"📊 S&P 500新聞統計進度報告")
        print(f"=" * 40)
        print(f"總公司數: {total_companies}")
        print(f"已處理: {processed_companies}")
        print(f"進度: {progress_percent:.1f}%")
        print(f"成功: {successful_companies}")
        print(f"失敗: {failed_companies}")
        
        if successful_companies > 0:
            # 計算統計數據
            successful_df = df[df['status'] == 'success']
            total_news = successful_df['news_count'].sum()
            avg_news = successful_df['news_count'].mean()
            
            print(f"\n📈 統計數據 (基於已成功處理的公司):")
            print(f"總新聞數: {int(total_news):,}")
            print(f"平均每家公司: {avg_news:.1f} 條新聞")
            
            # 預估完整結果
            if processed_companies > 0:
                estimated_total = (total_news / successful_companies) * total_companies
                print(f"預估總新聞數: {int(estimated_total):,}")
        
        # 顯示最近處理的公司
        print(f"\n🔄 最近處理的5家公司:")
        recent = df.tail(5)
        for _, row in recent.iterrows():
            status = "✅" if row['status'] == 'success' else "❌"
            if row['status'] == 'success':
                print(f"  {status} {row['symbol']:5s}: {int(row['news_count']):,} 條新聞")
            else:
                print(f"  {status} {row['symbol']:5s}: 失敗")
        
        if processed_companies < total_companies:
            print(f"\n⏳ 統計仍在進行中...")
        else:
            print(f"\n🎉 統計已完成！")
            
    except Exception as e:
        print(f"❌ 讀取進度時出錯: {e}")

if __name__ == "__main__":
    check_progress() 
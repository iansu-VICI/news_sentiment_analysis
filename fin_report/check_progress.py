#!/usr/bin/env python3
"""
財報抓取進度檢查器
"""

import os
import json
from pathlib import Path

def check_progress():
    """檢查財報抓取進度"""
    
    # 預期的公司列表
    expected_companies = [
        "005930.KS", "ADBE", "ADSK", "AMD", "ANSS", "ASML", "AVGO", "AXP", 
        "BIDU", "CAJ", "CMCSA", "CRM", "DFS", "DHR", "EB", "GFS", "GOOG", 
        "ICE", "ILMN", "INTC", "ISRG", "JNJ", "LRCX", "LYV", "MA", "MCO", 
        "MDT", "META", "MSCI", "MSFT", "MSGE", "NINOY", "NVDA", "PACB", 
        "SPGI", "SYK", "TMO", "TSM", "V"
    ]
    
    total_expected = len(expected_companies)
    
    # 檢查各個目錄
    base_dir = Path("financial_reports")
    
    if not base_dir.exists():
        print("❌ financial_reports 目錄不存在")
        return
    
    # 統計各類數據
    profiles_dir = base_dir / "company_profiles"
    financials_dir = base_dir / "basic_financials"
    metrics_dir = base_dir / "metrics"
    earnings_dir = base_dir / "earnings"
    
    profiles_count = len(list(profiles_dir.glob("*.json"))) if profiles_dir.exists() else 0
    financials_count = len(list(financials_dir.glob("*.json"))) if financials_dir.exists() else 0
    metrics_count = len(list(metrics_dir.glob("*.json"))) if metrics_dir.exists() else 0
    earnings_count = len(list(earnings_dir.glob("*.json"))) if earnings_dir.exists() else 0
    
    print("=== 財報抓取進度報告 ===")
    print(f"總預期公司數: {total_expected}")
    print(f"公司資料: {profiles_count}/{total_expected} ({profiles_count/total_expected*100:.1f}%)")
    print(f"財務數據: {financials_count}/{total_expected} ({financials_count/total_expected*100:.1f}%)")
    print(f"公司指標: {metrics_count}/{total_expected} ({metrics_count/total_expected*100:.1f}%)")
    print(f"財報日程: {earnings_count}/{total_expected} ({earnings_count/total_expected*100:.1f}%)")
    
    # 檢查已完成的公司
    completed_companies = []
    if profiles_dir.exists():
        for file in profiles_dir.glob("*.json"):
            symbol = file.stem.replace("_profile", "")
            completed_companies.append(symbol)
    
    completed_companies.sort()
    
    print(f"\n已完成的公司 ({len(completed_companies)}):")
    for i, company in enumerate(completed_companies):
        if i % 6 == 0:
            print()
        print(f"{company:>10}", end="  ")
    
    # 檢查未完成的公司
    remaining_companies = [c for c in expected_companies if c not in completed_companies]
    
    if remaining_companies:
        print(f"\n\n待處理的公司 ({len(remaining_companies)}):")
        for i, company in enumerate(remaining_companies):
            if i % 6 == 0:
                print()
            print(f"{company:>10}", end="  ")
    
    # 檢查摘要文件
    summary_file = base_dir / "scrape_summary.json"
    if summary_file.exists():
        try:
            with open(summary_file, 'r') as f:
                summary = json.load(f)
            print(f"\n\n=== 最新摘要 ===")
            print(f"抓取時間: {summary.get('scrape_timestamp', 'N/A')}")
            print(f"成功: {summary.get('successful', 0)}")
            print(f"失敗: {summary.get('failed', 0)}")
            print(f"成功率: {summary.get('success_rate', 'N/A')}")
        except:
            print("\n⚠️  無法讀取摘要文件")
    
    print("\n")

if __name__ == "__main__":
    check_progress() 
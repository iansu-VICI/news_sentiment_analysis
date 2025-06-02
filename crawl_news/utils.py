#!/usr/bin/env python3
"""
工具函數 - 新聞爬蟲
"""

import finnhub
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv

# 載入 .env 文件
load_dotenv()

def get_api_key() -> str:
    """獲取 Finnhub API 金鑰，優先從環境變數讀取"""
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        print("❌ 錯誤：請在 .env 文件中設定 FINNHUB_API_KEY")
        print("請創建 .env 文件並添加: FINNHUB_API_KEY=your_api_key_here")
        exit(1)
    return api_key

def create_finnhub_client(api_key: str = None) -> finnhub.Client:
    """
    創建 Finnhub 客戶端
    
    Args:
        api_key: API 金鑰，如果為 None 則使用預設值
        
    Returns:
        Finnhub 客戶端實例
    """
    if api_key is None:
        api_key = get_api_key()
    
    return finnhub.Client(api_key=api_key)

def get_company_news(symbol: str, from_date: str, to_date: str, api_key: str = None) -> List[Dict]:
    """
    獲取指定公司的新聞
    
    Args:
        symbol: 公司股票代碼
        from_date: 開始日期 (YYYY-MM-DD)
        to_date: 結束日期 (YYYY-MM-DD)
        api_key: API 金鑰
        
    Returns:
        新聞列表
    """
    try:
        client = create_finnhub_client(api_key)
        return client.company_news(symbol, from_date, to_date)
    except Exception as e:
        print(f"獲取公司新聞時發生錯誤: {e}")
        return []

def get_market_news(category: str = "general", api_key: str = None) -> List[Dict]:
    """
    獲取市場新聞
    
    Args:
        category: 新聞類別
        api_key: API 金鑰
        
    Returns:
        新聞列表
    """
    try:
        client = create_finnhub_client(api_key)
        return client.general_news(category=category)
    except Exception as e:
        print(f"獲取市場新聞時發生錯誤: {e}")
        return []

def format_news_summary(news_list: List[Dict], max_display: int = 5) -> str:
    """
    格式化新聞摘要
    
    Args:
        news_list: 新聞列表
        max_display: 最大顯示數量
        
    Returns:
        格式化的摘要字符串
    """
    if not news_list:
        return "未獲取到新聞"
    
    summary = f"共獲取 {len(news_list)} 條新聞\n"
    summary += "=" * 50 + "\n"
    
    for i, news_item in enumerate(news_list[:max_display], 1):
        headline = news_item.get('headline', 'N/A')
        source = news_item.get('source', 'N/A')
        url = news_item.get('url', 'N/A')
        
        # 轉換時間戳
        timestamp = news_item.get('datetime', 0)
        if timestamp:
            news_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        else:
            news_time = 'N/A'
        
        summary += f"\n新聞 {i}:\n"
        summary += f"  標題: {headline}\n"
        summary += f"  來源: {source}\n"
        summary += f"  時間: {news_time}\n"
        summary += f"  URL: {url}\n"
        summary += "-" * 30 + "\n"
    
    if len(news_list) > max_display:
        summary += f"\n... 還有 {len(news_list) - max_display} 條新聞未顯示\n"
    
    return summary

def save_news_list(news_list: List[Dict], filename: str) -> bool:
    """
    保存新聞列表到 JSON 文件
    
    Args:
        news_list: 新聞列表
        filename: 文件名
        
    Returns:
        是否保存成功
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "total_count": len(news_list),
                "export_timestamp": datetime.now().isoformat(),
                "news_list": news_list
            }, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存新聞列表時發生錯誤: {e}")
        return False

def load_news_list(filename: str) -> List[Dict]:
    """
    從 JSON 文件載入新聞列表
    
    Args:
        filename: 文件名
        
    Returns:
        新聞列表
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('news_list', [])
    except Exception as e:
        print(f"載入新聞列表時發生錯誤: {e}")
        return []

def get_date_range(days_back: int = 7) -> tuple:
    """
    獲取日期範圍
    
    Args:
        days_back: 往前推幾天
        
    Returns:
        (from_date, to_date) 元組
    """
    today = datetime.now()
    from_date = (today - timedelta(days=days_back)).strftime('%Y-%m-%d')
    to_date = today.strftime('%Y-%m-%d')
    
    return from_date, to_date

def validate_date_format(date_str: str) -> bool:
    """
    驗證日期格式
    
    Args:
        date_str: 日期字符串
        
    Returns:
        是否為有效格式
    """
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def filter_news_by_source(news_list: List[Dict], sources: List[str]) -> List[Dict]:
    """
    按來源過濾新聞
    
    Args:
        news_list: 新聞列表
        sources: 來源列表
        
    Returns:
        過濾後的新聞列表
    """
    return [news for news in news_list if news.get('source', '').lower() in [s.lower() for s in sources]]

def filter_news_by_keywords(news_list: List[Dict], keywords: List[str]) -> List[Dict]:
    """
    按關鍵詞過濾新聞
    
    Args:
        news_list: 新聞列表
        keywords: 關鍵詞列表
        
    Returns:
        過濾後的新聞列表
    """
    filtered_news = []
    for news in news_list:
        headline = news.get('headline', '').lower()
        summary = news.get('summary', '').lower()
        
        # 檢查是否包含任一關鍵詞
        if any(keyword.lower() in headline or keyword.lower() in summary for keyword in keywords):
            filtered_news.append(news)
    
    return filtered_news

# 常用的新聞來源列表
POPULAR_NEWS_SOURCES = [
    'Reuters',
    'Bloomberg',
    'MarketWatch',
    'Yahoo Finance',
    'CNBC',
    'Financial Times',
    'Wall Street Journal',
    'Seeking Alpha',
    'The Motley Fool',
    'Benzinga'
]

# 常用的股票代碼列表
POPULAR_SYMBOLS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
    'META', 'NVDA', 'NFLX', 'ADBE', 'CRM',
    'ORCL', 'INTC', 'AMD', 'QCOM', 'AVGO'
] 
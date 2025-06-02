import datetime
from urllib.parse import urlparse
from collections import Counter
import time # 為了請求之間的延遲

import finnhub
import os
import requests # <--- 新增匯入

# --- 配置 API 金鑰 (真實 API 使用) ---
FINNHUB_API_KEY = "d0mplk1r01qi78nge0agd0mplk1r01qi78nge0b0" # 請使用您自己的有效金鑰
if not FINNHUB_API_KEY:
    print("錯誤：請設定 FINNHUB_API_KEY 環境變數或直接在腳本中提供。")
    # exit(1) 
finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

def get_domain_from_url(url_string):
    """從 URL 字串中提取網域名稱。"""
    if not url_string:
        return None
    try:
        parsed_url = urlparse(url_string)
        netloc = parsed_url.netloc
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception as e:
        print(f"警告：無法解析 URL \'{url_string}\': {e}")
        return None

def get_final_url(url, timeout=10, max_retries=1, retry_delay=2):
    """
    獲取 URL 的最終跳轉地址。
    """
    headers = { # 模擬瀏覽器請求
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    current_url = url
    retries = 0
    while retries <= max_retries:
        try:
            # allow_redirects=True 是 requests 的預設行為，但明確寫出更好
            response = requests.get(current_url, headers=headers, timeout=timeout, allow_redirects=True, stream=True)
            # response.url 會是最後跳轉的 URL
            # 關閉 stream 連接
            response.close()
            return response.url
        except requests.exceptions.Timeout:
            print(f"  請求超時：{current_url}")
        except requests.exceptions.TooManyRedirects:
            print(f"  過多重定向：{current_url}")
        except requests.exceptions.RequestException as e:
            print(f"  請求錯誤 ({type(e).__name__})：{current_url} - {e}")
        
        retries += 1
        if retries <= max_retries:
            print(f"  正在重試 ({retries}/{max_retries}) URL: {current_url} (延遲 {retry_delay} 秒)")
            time.sleep(retry_delay)
            
    print(f"  警告：多次嘗試後仍無法獲取 {url} 的最終 URL。將使用原始 URL。")
    return url # 如果所有嘗試都失敗，返回原始 URL

def analyze_news_urls(symbol, start_year, start_month, end_year, end_month):
    """
    抓取指定股票在特定日期範圍內的新聞，並分析新聞來源 URL (跳轉後) 的網域。
    """
    all_final_urls = [] # 改為儲存最終 URL
    
    current_year = start_year
    current_month = start_month

    print(f"開始分析股票 {symbol} 的新聞 URL (將追蹤重定向)")
    print(f"日期範圍：{start_year:04d}-{start_month:02d} 至 {end_year:04d}-{end_month:02d}")
    print("--------------------------------------------------")

    request_count_this_month = 0
    MAX_REQUESTS_PER_MINUTE_FINNHUB = 55 # Finnhub 免費方案通常有每分鐘請求限制 (例如60，保守設55)
                                     # 付費方案限制不同，請依您的方案調整
    # 注意: requests.get 也算請求，如果大量 URL 來自 Finnhub 且需要跳轉，這本身不會計入 Finnhub API call
    # 但如果 Finnhub URL 跳轉到另一個 Finnhub URL，則可能需要考慮

    total_api_calls = 0

    while current_year < end_year or \
          (current_year == end_year and current_month <= end_month):
        
        from_date_obj = datetime.date(current_year, current_month, 1)
        from_date_str = from_date_obj.strftime("%Y-%m-%d")
        
        if current_month == 12:
            next_month_first_day_obj = datetime.date(current_year + 1, 1, 1)
        else:
            next_month_first_day_obj = datetime.date(current_year, current_month + 1, 1)
        
        to_date_obj = next_month_first_day_obj - datetime.timedelta(days=1)
        to_date_str = to_date_obj.strftime("%Y-%m-%d")

        print(f"處理月份：{current_year:04d}-{current_month:02d} (從 {from_date_str} 到 {to_date_str})")

        news_list = []
        try:
            # Finnhub API call
            print(f"  正在呼叫 Finnhub API ({total_api_calls + 1})...")
            news_list = finnhub_client.company_news(symbol, _from=from_date_str, to=to_date_str)
            total_api_calls += 1
        except finnhub.FinnhubAPIException as e:
            print(f"  Finnhub API 錯誤：{e}")
        except Exception as e:
            print(f"  獲取 Finnhub 新聞時發生未知錯誤：{e}")

        urls_this_month = 0
        if news_list:
            # 移除之前用於印出原始 API URL 的範例程式碼
            # print("部分原始 API 回應範例：")
            # for i, news_item in enumerate(news_list[:3]): 
            #     if isinstance(news_item, dict) and 'url' in news_item:
            #         print(f"  範例 URL {i+1}: {news_item['url']}")
            
            print(f"  本月從 API 獲得 {len(news_list)} 條新聞。開始處理 URL 並追蹤重定向...")
            for i, news_item in enumerate(news_list):
                if isinstance(news_item, dict) and 'url' in news_item and news_item['url']:
                    original_url = news_item['url']
                    # print(f"    處理原始 URL ({i+1}/{len(news_list)}): {original_url}")
                    final_url = get_final_url(original_url) # <--- 獲取最終 URL
                    if final_url:
                        all_final_urls.append(final_url)
                        urls_this_month += 1
                    # 在每個外部請求後加入少量延遲，避免對目標伺服器造成過大負載
                    time.sleep(0.5) # 0.5 秒延遲，可以調整
                else:
                    print(f"    項目 {i+1} 沒有有效的 URL。")
            
            print(f"  本月成功獲取並處理 {urls_this_month} 個最終 URL。累計最終 URL {len(all_final_urls)} 個。")
        else:
            print("  本月未獲得新聞或 API 呼叫失敗。")
        
        if current_month == 12:
            current_month = 1
            current_year += 1
        else:
            current_month += 1
        
        # Finnhub API 請求之間的延遲 (基於每分鐘限制)
        if total_api_calls > 0 and total_api_calls % MAX_REQUESTS_PER_MINUTE_FINNHUB == 0:
            print(f"  已達到 Finnhub API 每分鐘請求限制 ({MAX_REQUESTS_PER_MINUTE_FINNHUB} 次)，等待 65 秒...")
            time.sleep(65) # 等待超過1分鐘以確保限制已重置

    print("--------------------------------------------------")
    if not all_final_urls:
        print("在指定日期範圍內沒有找到任何新聞 URL 或無法獲取最終 URL。")
        return

    print(f"總共收集到 {len(all_final_urls)} 個最終 URL。")

    domain_counts = Counter()
    for url_to_analyze in all_final_urls:
        domain = get_domain_from_url(url_to_analyze) # 使用最終 URL 進行分析
        if domain: 
            domain_counts[domain] += 1

    print("\n網域分析結果 (按數量降序排列):")
    if not domain_counts:
        print("無法從收集到的最終 URL 中解析出任何網域。")
        return
        
    for domain, count in domain_counts.most_common():
        print(f"@{domain} ({count})")

if __name__ == "__main__":
    SYMBOL_TO_ANALYZE = "TSLA"
    ANALYSIS_START_YEAR = 2024
    ANALYSIS_START_MONTH = 1 
    ANALYSIS_END_YEAR = 2025  
    ANALYSIS_END_MONTH = 12 # 為了測試，先縮小範圍到1個月

    analyze_news_urls(
        SYMBOL_TO_ANALYZE,
        ANALYSIS_START_YEAR,
        ANALYSIS_START_MONTH,
        ANALYSIS_END_YEAR,
        ANALYSIS_END_MONTH
    )

    print("\n分析完成。")
    # 更新提醒訊息
    print("提醒：此腳本現在會嘗試追蹤 URL 重定向。")
    print("請確保您已安裝 'requests' 函式庫 (pip install requests)。")
    print(f"Finnhub API 金鑰: {'已設定' if FINNHUB_API_KEY else '未設定或為空'}") 
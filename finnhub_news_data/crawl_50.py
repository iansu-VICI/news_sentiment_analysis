from utils import get_company_news, finnhub_client, API_KEY
import argparse
from datetime import datetime, timedelta
import requests
import os
import re
from bs4 import BeautifulSoup
import time
from readability import Document
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
import random
import json
from urllib.parse import urlparse
import urllib.parse

# --- Helper: Define a list of common User-Agents ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7103.25 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
]

# --- Helper: Define common "load more" button texts/selectors ---
COMMON_LOAD_MORE_SELECTORS_TEXTS = [
    "[id*='show-more']",
    "[class*='load-more']",
    "[class*='show-more']",
    "[data-testid*='load-more']",
    "button:has-text('Show more')",
    "button:has-text('Load more')",
    "button:has-text('Read more')",
    "a:has-text('Continue reading')",
    "a.more-link"
]

def get_random_user_agent():
    """Selects a random User-Agent string."""
    return random.choice(USER_AGENTS)


def check_final_url_and_continue_reading(original_url, max_retries=3, timeout=10):
    """
    檢查原始URL的最終URL，並確認是否為Yahoo Finance頁面且有Continue Reading按鈕
    
    Args:
        original_url: 原始新聞URL
        max_retries: 最大重試次數
        timeout: 頁面載入timeout秒數
        
    Returns:
        dict: {
            'final_url': 最終URL,
            'is_yahoo_finance': 是否為Yahoo Finance頁面,
            'has_continue_reading': 是否有Continue Reading按鈕,
            'status': 'success' or 'error',
            'error_message': 錯誤訊息(如果有)
        }
    """
    result = {
        'final_url': original_url,
        'is_yahoo_finance': False,
        'has_continue_reading': False,
        'status': 'error',
        'error_message': None
    }
    
    try:
        # 如果是Finnhub API URL，先獲取真正的新聞URL
        if "finnhub.io/api/news" in original_url:
            print(f"檢測到Finnhub API URL，嘗試獲取真正的新聞URL...")
            
            try:
                # 使用requests獲取API響應（性能優化：降低timeout）
                headers = {
                    'User-Agent': get_random_user_agent(),
                    'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                }
                
                response = requests.get(original_url, headers=headers, timeout=5, allow_redirects=True)  # 降低timeout從10到5
                
                if response.status_code == 200:
                    # 檢查是否是JSON響應
                    content_type = response.headers.get('content-type', '').lower()
                    if 'application/json' in content_type:
                        # 如果是JSON，可能包含真正的URL
                        try:
                            json_data = response.json()
                            # 查找可能的URL字段
                            real_url = None
                            for key in ['url', 'link', 'href', 'source_url', 'original_url']:
                                if key in json_data and json_data[key]:
                                    real_url = json_data[key]
                                    break
                            
                            if real_url and real_url.startswith('http'):
                                print(f"從API響應中獲取真正的新聞URL: {real_url}")
                                result['final_url'] = real_url
                            else:
                                print(f"API響應中未找到有效的URL")
                                result['error_message'] = "API響應中未找到有效的URL"
                                return result
                        except Exception as e:
                            print(f"解析API JSON響應時出錯: {e}")
                            result['error_message'] = f"解析API JSON響應時出錯: {e}"
                            return result
                    else:
                        # 如果不是JSON，檢查是否是HTML重定向頁面
                        if response.url != original_url:
                            print(f"API URL重定向到: {response.url}")
                            result['final_url'] = response.url
                        else:
                            # 解析HTML中的重定向或鏈接
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # 查找meta重定向
                            meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
                            if meta_refresh and 'content' in meta_refresh.attrs:
                                content = meta_refresh['content']
                                if 'url=' in content:
                                    redirect_url = content.split('url=')[1]
                                    print(f"從meta refresh獲取重定向URL: {redirect_url}")
                                    result['final_url'] = redirect_url
                                    
                            # 查找可能的鏈接
                            if result['final_url'] == original_url:
                                links = soup.find_all('a', href=True)
                                for link in links:
                                    href = link['href']
                                    if href.startswith('http') and 'finnhub.io' not in href:
                                        print(f"從HTML中找到外部鏈接: {href}")
                                        result['final_url'] = href
                                        break
                else:
                    print(f"API請求失敗，狀態碼: {response.status_code}")
                    result['error_message'] = f"API請求失敗，狀態碼: {response.status_code}"
                    return result
                    
            except Exception as e:
                print(f"處理Finnhub API URL時出錯: {e}")
                result['error_message'] = f"處理Finnhub API URL時出錯: {e}"
                return result
        
        # 如果獲取到了真正的新聞URL，或者原本就不是API URL，繼續檢查
        target_url = result['final_url']
        
        # 檢查是否為Yahoo Finance頁面（即使不能訪問也可以判斷）
        parsed_url = urlparse(target_url)
        result['is_yahoo_finance'] = 'finance.yahoo.com' in parsed_url.netloc
        
        # 如果不是Yahoo Finance頁面，可以跳過瀏覽器檢查，因為我們主要關心Yahoo Finance的Continue Reading按鈕
        if not result['is_yahoo_finance']:
            print(f"非Yahoo Finance頁面: {target_url}")
            result['status'] = 'success'
            result['has_continue_reading'] = False
            return result
        
        # 只有Yahoo Finance頁面才使用瀏覽器檢查Continue Reading按鈕
        print(f"檢測到Yahoo Finance頁面，檢查Continue Reading按鈕...")
        
        with sync_playwright() as p:
            # 性能優化：瀏覽器配置
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ]
            )
            context = browser.new_context(
                user_agent=get_random_user_agent(),
                viewport={'width': 1280, 'height': 720},  # 降低解析度以提升性能
                ignore_https_errors=True,  # 忽略SSL錯誤
                java_script_enabled=True  # 確保JS啟用（某些頁面需要）
            )
            page = context.new_page()
            
            # 性能優化：阻擋不必要的資源載入
            page.route('**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,eot}', lambda route: route.abort())
            page.route('**/*.css', lambda route: route.abort())  # 阻擋CSS（如果不影響功能的話）
            
            for attempt in range(max_retries):
                try:
                    print(f"嘗試訪問Yahoo Finance URL: {target_url}")
                    
                    # 導航到頁面（性能優化：使用動態timeout）
                    response = page.goto(target_url, wait_until='domcontentloaded', timeout=timeout*1000)  # 轉換為毫秒
                    
                    if response is None:
                        result['error_message'] = f"無法導航到URL (嘗試 {attempt + 1}/{max_retries})"
                        continue
                    
                    # 更新最終URL
                    result['final_url'] = page.url
                    print(f"Yahoo Finance最終URL: {result['final_url']}")
                    
                    # 性能優化：縮短等待時間（使用動態timeout）
                    try:
                        page.wait_for_load_state('networkidle', timeout=max(3000, timeout*300))  # 最少3秒，或timeout的30%
                    except:
                        # 如果等待超時，嘗試等待DOM穩定
                        try:
                            page.wait_for_timeout(min(1000, timeout*100))  # 等待時間不超過timeout的10%
                        except:
                            pass
                    
                    # 改善：增加額外等待時間確保頁面完全載入
                    print(f"等待頁面完全載入...")
                    try:
                        # 等待任何潛在的AJAX請求完成
                        page.wait_for_timeout(2000)  # 額外等待2秒
                        
                        # 等待特定元素出現（Yahoo Finance特有的元素）
                        try:
                            page.wait_for_selector("main, article, .content, .story", timeout=5000)
                        except:
                            print("未找到主要內容元素，但繼續處理...")
                    except:
                        pass
                    
                    # 改善：先調試頁面內容
                    print(f"調試頁面內容...")
                    try:
                        # 檢查頁面標題
                        title = page.title()
                        print(f"頁面標題: {title}")
                        
                        # 檢查是否有任何包含 'continue' 或 'reading' 的元素
                        debug_elements = page.locator("*:has-text('Continue'), *:has-text('Reading'), *:has-text('continue'), *:has-text('reading')")
                        debug_count = debug_elements.count()
                        print(f"包含 'continue/reading' 文字的元素數量: {debug_count}")
                        
                        if debug_count > 0:
                            for i in range(min(debug_count, 5)):  # 只檢查前5個
                                try:
                                    element = debug_elements.nth(i)
                                    tag_name = element.evaluate("el => el.tagName.toLowerCase()")
                                    text_content = element.inner_text()[:50]
                                    class_name = element.get_attribute('class') or ''
                                    print(f"  元素 {i+1}: <{tag_name}> class='{class_name}' text='{text_content}'")
                                except:
                                    continue
                    except Exception as debug_e:
                        print(f"調試時出錯: {debug_e}")
                    
                    # 檢查Continue Reading按鈕（改善：根據真實HTML結構）
                    continue_reading_selectors = [
                        # 根據用戶提供的真實HTML結構優化的選擇器
                        "a.continue-reading-button",  # 最精確匹配
                        ".continue-reading-button",  # class匹配
                        "a[class*='continue-reading-button']",  # 包含該class的a標籤
                        "a.secondary-btn-link.continue-reading-button",  # 多class匹配
                        "a[data-ylk*='Continue%20Reading']",  # data-ylk屬性匹配
                        "a[data-ylk*='Continue Reading']",  # data-ylk屬性匹配（未編碼）
                        
                        # 精確的屬性匹配
                        "a[aria-label='Continue Reading']",
                        "a[title='Continue Reading']",
                        "[aria-label='Continue Reading']",
                        "[title='Continue Reading']",
                        
                        # 較寬鬆的選擇器
                        "a[aria-label*='Continue Reading']",
                        "a[title*='Continue Reading']",
                        "a:has-text('Continue Reading')",
                        "a:has-text('Continue reading')",
                        
                        # 通用文字匹配
                        ":text('Continue Reading')",
                        ":text-is('Continue Reading')",
                        "*:has-text('Continue Reading'):not(script):not(style)",
                        
                        # 更寬泛的選擇器（備用）
                        ".continue-reading",
                        "[class*='continue-reading']",
                        "button:has-text('Continue Reading')",
                        "button[aria-label*='Continue Reading']",
                        "text='Continue Reading'",
                        "text='Read More'"
                    ]
                    
                    continue_button = None
                    found_selector = None
                    for selector in continue_reading_selectors:
                        try:
                            continue_button = page.locator(selector).first
                            if continue_button.count() > 0:
                                found_selector = selector
                                print(f"✅ 找到Continue Reading按鈕: {selector}")
                                
                                # 詳細記錄按鈕屬性（用於調試）
                                try:
                                    tag_name = continue_button.evaluate("el => el.tagName.toLowerCase()")
                                    class_name = continue_button.get_attribute('class') or ''
                                    aria_label = continue_button.get_attribute('aria-label') or ''
                                    title = continue_button.get_attribute('title') or ''
                                    href = continue_button.get_attribute('href') or ''
                                    print(f"   標籤: {tag_name}")
                                    print(f"   Class: {class_name}")
                                    print(f"   Aria-label: {aria_label}")
                                    print(f"   Title: {title}")
                                    print(f"   Href: {href[:100]}..." if len(href) > 100 else f"   Href: {href}")
                                except Exception as debug_e:
                                    print(f"   無法獲取按鈕詳細信息: {debug_e}")
                                
                                break
                        except Exception as e:
                            continue
                    
                    has_continue_reading = continue_button and continue_button.count() > 0
                    
                    # 如果找到Continue Reading按鈕，嘗試提取href
                    if has_continue_reading:
                        try:
                            # 檢查是否是<a>標籤並有href屬性
                            href = continue_button.get_attribute('href')
                            if href:
                                # HTML 解碼 (處理 &amp; 等實體)
                                import html
                                href = html.unescape(href)
                                
                                # 將相對URL轉換為絕對URL
                                if href.startswith('/'):
                                    base_url = f"https://{urllib.parse.urlparse(result['final_url']).netloc}"
                                    href = urllib.parse.urljoin(base_url, href)
                                elif href.startswith('http'):
                                    # 已經是完整URL
                                    pass
                                else:
                                    # 相對路徑
                                    base_url = f"https://{urllib.parse.urlparse(result['final_url']).netloc}"
                                    href = urllib.parse.urljoin(base_url, href)
                                
                                print(f"🔗 Continue Reading按鈕指向: {href}")
                                # 更新最終URL為Continue Reading的目標
                                result['final_url'] = href
                                print(f"✅ 已更新最終URL為真正的文章頁面")
                                # 注意：這裡不再重新訪問頁面，因為我們只需要URL
                        except Exception as e:
                            print(f"❌ 提取Continue Reading href失敗: {e}")
                    else:
                        print(f"📄 未找到Continue Reading按鈕（測試了 {len(continue_reading_selectors)} 個選擇器）")
                    
                    result['has_continue_reading'] = has_continue_reading
                    status = "📰 Yahoo Finance" if 'yahoo.com' in result['final_url'] else "🌐 其他網站"
                    continue_status = "📖 有Continue Reading" if has_continue_reading else "📄 無Continue Reading"
                    
                    result['status'] = 'success'
                    break
                    
                except Exception as e:
                    result['error_message'] = f"嘗試 {attempt + 1}/{max_retries} 失敗: {str(e)}"
                    if attempt == max_retries - 1:
                        # 即使瀏覽器檢查失敗，如果我們已經確定了URL，也算部分成功
                        if result['final_url'] != original_url:
                            result['status'] = 'partial_success'
                            print(f"雖然無法完全訪問頁面，但已成功獲取最終URL")
                        break
                    time.sleep(1)  # 重試前等待
            
            browser.close()
            
    except Exception as e:
        result['error_message'] = f"瀏覽器操作失敗: {str(e)}"
        # 即使出現異常，如果已經獲取了final_url，也標記為部分成功
        if result['final_url'] != original_url:
            result['status'] = 'partial_success'
    
    return result

def display_company_news(symbol, from_date=None, to_date=None, download_articles=False, output_dir="downloaded_articles", headless=True, batch_size=10, yahoo_delay=0.3, other_delay=0.1, max_retries=3, timeout=10):
    """
    取得並顯示特定公司的新聞，只保存基本資訊到JSON文件
    
    Args:
        symbol: 公司股票代碼
        from_date: 起始日期 (YYYY-MM-DD格式)
        to_date: 結束日期 (YYYY-MM-DD格式)
        download_articles: 此參數在新版本中被忽略
        output_dir: JSON文件保存目錄
        headless: 是否使用無頭模式運行瀏覽器
        batch_size: 進度報告批次大小
        yahoo_delay: Yahoo Finance頁面處理間隔秒數
        other_delay: 其他頁面處理間隔秒數
        max_retries: URL檢查最大重試次數
        timeout: 頁面載入timeout秒數
    """
    # 如果未指定日期範圍，預設為2021-01-01到2025-05-28
    if from_date is None or to_date is None:
        from_date = from_date or '2021-01-01'
        to_date = to_date or '2025-05-28'
    
    print(f"\n--- 正在獲取 {symbol} 從 {from_date} 到 {to_date} 的公司新聞 ---")
    company_news = get_company_news(symbol, from_date, to_date)
    
    if company_news:
        print(f"共獲取 {len(company_news)} 條新聞。")
        
        # 創建輸出目錄
        os.makedirs(output_dir, exist_ok=True)
        
        # 準備新聞資料列表
        news_data = []
        
        print(f"\n開始處理新聞資料...")
        processed_count = 0
        filtered_count = 0  # 被過濾掉的數量
        error_count = 0  # 錯誤數量統計
        
        # 性能優化：批次處理和進度報告
        start_time = time.time()
        
        for i, news_item in enumerate(company_news):
            original_url = news_item.get('url')
            if not original_url:
                continue
            
            # 性能優化：進度報告
            if i % batch_size == 0 and i > 0:
                elapsed_time = time.time() - start_time
                avg_time_per_item = elapsed_time / i
                remaining_items = len(company_news) - i
                estimated_remaining_time = avg_time_per_item * remaining_items
                print(f"\n📊 進度報告 ({i}/{len(company_news)})")
                print(f"   已處理: {processed_count} | 過濾: {filtered_count} | 錯誤: {error_count}")
                print(f"   平均處理時間: {avg_time_per_item:.2f}秒/項")
                print(f"   預估剩餘時間: {estimated_remaining_time/60:.1f}分鐘")
                
            print(f"\n處理新聞 {i+1}/{len(company_news)}: {original_url[:80]}...")
            
            try:
                # 檢查最終URL和Continue Reading按鈕
                url_check_result = check_final_url_and_continue_reading(original_url, max_retries, timeout)
                
                # 檢查是否成功解析出不同的final_url
                if url_check_result['final_url'] == original_url:
                    filtered_count += 1
                    print(f"  ⚠️  跳過：original_url與final_url相同，可能解析失敗")
                    continue
                
                # 準備新聞資料
                news_info = {
                    'headline': news_item.get('headline'),
                    'source': news_item.get('source'),
                    'datetime': news_item.get('datetime'),
                    'publish_date': datetime.fromtimestamp(news_item.get('datetime')).strftime('%Y-%m-%d %H:%M:%S'),
                    'original_url': original_url,
                    'final_url': url_check_result['final_url'],
                    'is_yahoo_finance': url_check_result['is_yahoo_finance'],
                    'has_continue_reading': url_check_result['has_continue_reading'],
                    'url_check_status': url_check_result['status'],
                    'url_check_error': url_check_result.get('error_message')
                }
                
                news_data.append(news_info)
                processed_count += 1
                
                # 顯示處理結果
                status_msg = "✅" if url_check_result['status'] == 'success' else "🔄" if url_check_result['status'] == 'partial_success' else "❌"
                yahoo_msg = "📰 Yahoo Finance" if url_check_result['is_yahoo_finance'] else "🌐 其他網站"
                continue_msg = "📖 有Continue Reading" if url_check_result['has_continue_reading'] else "📄 無Continue Reading"
                
                print(f"  {status_msg} {yahoo_msg}, {continue_msg}")
                
            except Exception as e:
                error_count += 1
                print(f"  ❌ 處理新聞時發生錯誤: {e}")
                continue
            
            # 性能優化：減少等待時間，只在Yahoo Finance檢查時等待
            if url_check_result.get('is_yahoo_finance', False):
                time.sleep(yahoo_delay)
            else:
                time.sleep(other_delay)
        
        # 保存到JSON文件
        output_file = os.path.join(output_dir, f"{symbol.lower()}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'symbol': symbol,
                'from_date': from_date,
                'to_date': to_date,
                'total_news_fetched': len(company_news),
                'filtered_out': filtered_count,
                'valid_news': len(news_data),
                'processed_count': processed_count,
                'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'news_data': news_data
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n新聞資料處理完成。")
        print(f"  總獲取新聞: {len(company_news)}")
        print(f"  成功解析: {processed_count}")
        print(f"  過濾掉: {filtered_count} (original_url與final_url相同)")
        print(f"資料已保存到: {output_file}")
        
        # 顯示統計資訊
        yahoo_finance_count = sum(1 for news in news_data if news['is_yahoo_finance'])
        continue_reading_count = sum(1 for news in news_data if news['has_continue_reading'])
        
        print(f"\n統計資訊:")
        print(f"  有效新聞數: {len(news_data)}")
        print(f"  Yahoo Finance 新聞: {yahoo_finance_count}")
        print(f"  有 Continue Reading 按鈕: {continue_reading_count}")
        
    else:
        print("未能獲取公司新聞，或該時段內無新聞。")
    
    return company_news

def get_market_news(category="general", min_id=0):
    """
    獲取一般市場新聞。

    :param category: 新聞類別 (例如 general, forex, crypto, merger)
    :param min_id: (用於分頁) 只獲取 ID 大於 min_id 的新聞
    :return: 新聞列表 (JSON)
    """
    try:
        # 使用正確的方法名稱，即 general_news 而非 market_news
        if category in ["general", "forex", "crypto", "merger"]:
            return finnhub_client.general_news(category=category)
        elif category == "crypto":
            # 獲取加密貨幣特定新聞
            # 注意：如果 general_news 已支援 crypto，這部分可能重複
            crypto_news = []
            
            # 嘗試獲取加密貨幣特定的新聞（如果有專用API）
            try:
                crypto_news = finnhub_client.crypto_news()
            except:
                # 如果沒有專用API，回退到使用 general_news 的 crypto 類別
                crypto_news = finnhub_client.general_news(category="crypto")
                
            return crypto_news
        else:
            return finnhub_client.general_news(category="general")
    except Exception as e:
        print(f"獲取市場新聞時發生錯誤: {e}")
        return None

def display_market_news(category="general", min_id=0):
    """顯示市場新聞"""
    print(f"\n--- 正在獲取{category}市場新聞 ---")
    market_news_data = get_market_news(category=category, min_id=min_id)
    
    if market_news_data:
        print(f"共獲取 {len(market_news_data)} 條市場新聞。")
        for i, news_item in enumerate(market_news_data[:3]): # 只顯示前3條
            news_datetime = datetime.fromtimestamp(news_item.get('datetime')).strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n市場新聞 {i+1}:")
            print(f"  標題: {news_item.get('headline')}")
            print(f"  來源: {news_item.get('source')}")
            print(f"  發布時間: {news_datetime}")
    else:
        print("未能獲取市場新聞。")
    
    return market_news_data

def parse_args():
    """解析命令列參數"""
    parser = argparse.ArgumentParser(description='獲取金融新聞（優化版）')
    parser.add_argument('--type', type=str, choices=['company', 'market'], default='company',
                      help='新聞類型: company (公司新聞) 或 market (市場新聞)')
    parser.add_argument('--symbol', type=str, default='NVDA',
                      help='公司股票代碼 (預設: AAPL)')
    parser.add_argument('--from-date', type=str, default='2021-05-01',
                      help='起始日期 (YYYY-MM-DD格式，預設: 2025-03-01)')
    parser.add_argument('--to-date', type=str, default='2021-05-30',
                      help='結束日期 (YYYY-MM-DD格式，預設: 2025-04-01)')
    parser.add_argument('--category', type=str, default='general',
                      choices=['general', 'forex', 'crypto', 'merger'],
                      help='市場新聞類別 (預設: general)')
    parser.add_argument('--min-id', type=int, default=0,
                      help='市場新聞最小ID (用於分頁，預設: 0)')
    parser.add_argument('--download-articles', action='store_true',
                      help='下載文章內容 (預設: False)')
    parser.add_argument('--output-dir', type=str, default='downloaded_articles',
                      help='文章保存目錄 (預設: downloaded_articles)')
    parser.add_argument('--no-headless', action='store_true',
                      help='使用有頭模式運行瀏覽器 (預設: 無頭模式)')
    
    # 性能優化參數
    parser.add_argument('--batch-size', type=int, default=10,
                      help='進度報告批次大小 (預設: 10)')
    parser.add_argument('--yahoo-delay', type=float, default=0.3,
                      help='Yahoo Finance頁面處理間隔秒數 (預設: 0.3)')
    parser.add_argument('--other-delay', type=float, default=0.1,
                      help='其他頁面處理間隔秒數 (預設: 0.1)')
    parser.add_argument('--max-retries', type=int, default=3,
                      help='URL檢查最大重試次數 (預設: 3)')
    parser.add_argument('--timeout', type=int, default=10,
                      help='頁面載入timeout秒數 (預設: 10)')
    
    # 測試參數
    parser.add_argument('--test-continue-reading', action='store_true',
                      help='測試 Continue Reading 按鈕檢測功能')
    
    args = parser.parse_args()
    
    # 轉換no-headless到headless
    args.headless = not args.no_headless
    
    # 檢查X server是否可用，如果不可用但要求有頭模式則顯示警告
    if args.no_headless and not os.environ.get('DISPLAY'):
        print("\n警告: 你請求了有頭模式 (--no-headless)，但沒有檢測到X server。")
        print("你有兩個選擇:")
        print("  1. 移除 --no-headless 參數，使用無頭模式運行")
        print("  2. 安裝並使用xvfb: sudo apt-get install xvfb")
        print("     然後運行: xvfb-run python crawl_50.py [其他參數] --no-headless")
        print("\n自動切換到無頭模式繼續執行...\n")
        args.headless = True
    
    return args

# --- 測試函數 ---
def test_continue_reading_detection():
    """測試 Continue Reading 按鈕檢測功能"""
    test_urls = [
        # 已知包含 Continue Reading 按鈕的 Yahoo Finance URL
        "https://finance.yahoo.com/m/727d6b2f-4189-33bc-a491-8ea5cdc6cb33/forget-electric-vehicle.html",
        "https://finance.yahoo.com/news/nvidia-latest-dip-offers-pre-154224134.html"
    ]
    
    print("🧪 測試 Continue Reading 按鈕檢測功能...")
    
    for test_url in test_urls:
        print(f"\n測試URL: {test_url}")
        result = check_final_url_and_continue_reading(test_url, max_retries=2, timeout=15)
        
        print(f"結果:")
        print(f"  最終URL: {result['final_url']}")
        print(f"  是Yahoo Finance: {result['is_yahoo_finance']}")
        print(f"  有Continue Reading: {result['has_continue_reading']}")
        print(f"  狀態: {result['status']}")
        if result.get('error_message'):
            print(f"  錯誤: {result['error_message']}")

# --- 使用範例 ---
if __name__ == "__main__":
    if API_KEY == "YOUR_FINNHUB_API_KEY":
        print("請先在程式碼中設定您的 API_KEY")
        exit(1)
    else:
        # 解析命令列參數
        args = parse_args()
        
        try:
            # 測試模式
            if args.test_continue_reading:
                test_continue_reading_detection()
                exit(0)
            
            # 根據新聞類型調用相應的函式
            if args.type == 'company':
                result = display_company_news(
                    symbol=args.symbol, 
                    from_date=args.from_date, 
                    to_date=args.to_date, 
                    download_articles=args.download_articles, 
                    output_dir=args.output_dir, 
                    headless=args.headless,
                    batch_size=args.batch_size,
                    yahoo_delay=args.yahoo_delay,
                    other_delay=args.other_delay,
                    max_retries=args.max_retries,
                    timeout=args.timeout
                )
                
                # 檢查結果並決定退出碼
                if result is not None and len(result) > 0:
                    # 檢查是否有成功生成的輸出文件
                    import os
                    output_file = os.path.join(args.output_dir, f"{args.symbol.lower()}.json")
                    if os.path.exists(output_file):
                        print(f"✅ 成功完成處理，輸出文件: {output_file}")
                        exit(0)  # 成功
                    else:
                        print(f"❌ 雖然獲取了新聞但未生成輸出文件")
                        exit(1)  # 失敗
                else:
                    print(f"❌ 未獲取到任何新聞資料")
                    exit(1)  # 失敗
            else:  # market news
                result = display_market_news(args.category, args.min_id)
                if result is not None:
                    exit(0)  # 成功
                else:
                    exit(1)  # 失敗
                    
        except Exception as e:
            print(f"❌ 程式執行時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            exit(1)  # 失敗
#!/usr/bin/env python3
"""
Step2: 使用crawl4ai抓取新聞內容
根據step1產生的CSV檔案，抓取其最終URL的新聞內容
"""

import os
import sys
import pandas as pd
import asyncio
import aiohttp
import glob
import json
from pathlib import Path
from datetime import datetime
import time

# 添加crawl_news目錄到路徑
sys.path.append("../crawl_news")

try:
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.extraction_strategy import LLMExtractionStrategy
except ImportError:
    print("❌ 請先安裝crawl4ai: pip install crawl4ai")
    sys.exit(1)

class NewsContentCrawler:
    """新聞內容爬取器"""
    
    def __init__(self, max_concurrent=3, delay=1.0, use_llm=False):
        self.max_concurrent = max_concurrent
        self.delay = delay
        self.use_llm = use_llm
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # 統計
        self.stats = {
            'total_articles': 0,
            'successful_articles': 0,
            'failed_articles': 0,
            'skipped_articles': 0
        }
    
    async def crawl_single_article(self, url, title="", session_id=None):
        """
        爬取單篇文章內容
        
        Args:
            url: 文章URL
            title: 文章標題
            session_id: 用於日誌的會話ID
        
        Returns:
            dict: 包含文章內容的字典
        """
        async with self.semaphore:
            try:
                async with AsyncWebCrawler(verbose=True) as crawler:
                    print(f"  [{session_id}] 爬取: {url[:80]}...")
                    
                    # 配置爬取策略
                    extraction_strategy = None
                    if self.use_llm:
                        extraction_strategy = LLMExtractionStrategy(
                            provider="ollama/llama3.2",
                            api_token="dummy",
                            schema={
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "description": "Article title"},
                                    "content": {"type": "string", "description": "Main article content"},
                                    "summary": {"type": "string", "description": "Article summary"},
                                    "author": {"type": "string", "description": "Article author"},
                                    "publish_date": {"type": "string", "description": "Publication date"}
                                }
                            },
                            extraction_type="schema",
                            instruction="Extract the main article content, title, summary, author, and publication date."
                        )
                    
                    # 執行爬取
                    result = await crawler.arun(
                        url=url,
                        extraction_strategy=extraction_strategy,
                        bypass_cache=True,
                        js_code="window.scrollTo(0, document.body.scrollHeight);",
                        wait_for=2
                    )
                    
                    if result.success:
                        # 準備返回數據
                        article_data = {
                            'url': url,
                            'title': title,
                            'crawl_success': True,
                            'markdown_content': result.markdown,
                            'cleaned_html': result.cleaned_html,
                            'extracted_content': result.extracted_content if self.use_llm else None,
                            'crawl_timestamp': datetime.now().isoformat(),
                            'content_length': len(result.markdown) if result.markdown else 0
                        }
                        
                        print(f"    ✅ 成功: {len(result.markdown) if result.markdown else 0} 字符")
                        self.stats['successful_articles'] += 1
                        return article_data
                    else:
                        print(f"    ❌ 爬取失敗: {result.error_message}")
                        self.stats['failed_articles'] += 1
                        return {
                            'url': url,
                            'title': title,
                            'crawl_success': False,
                            'error_message': result.error_message,
                            'crawl_timestamp': datetime.now().isoformat()
                        }
                        
            except Exception as e:
                print(f"    ❌ 異常: {str(e)}")
                self.stats['failed_articles'] += 1
                return {
                    'url': url,
                    'title': title,
                    'crawl_success': False,
                    'error_message': str(e),
                    'crawl_timestamp': datetime.now().isoformat()
                }
            finally:
                # 延遲以避免過於頻繁的請求
                if self.delay > 0:
                    await asyncio.sleep(self.delay)
    
    async def process_csv_file(self, csv_file_path, output_dir):
        """
        處理單個CSV文件，爬取其中的新聞內容
        
        Args:
            csv_file_path: CSV文件路徑
            output_dir: 輸出目錄
        
        Returns:
            bool: 是否成功處理
        """
        try:
            # 讀取CSV文件
            df = pd.read_csv(csv_file_path)
            
            if df.empty:
                print(f"  CSV文件為空: {csv_file_path}")
                return False
            
            symbol = df['symbol'].iloc[0] if 'symbol' in df.columns else 'unknown'
            print(f"\n處理 {symbol}，共 {len(df)} 條新聞...")
            
            # 準備任務列表
            tasks = []
            for idx, row in df.iterrows():
                final_url = row.get('final_url', '')
                headline = row.get('headline', '')
                
                if not final_url or pd.isna(final_url):
                    print(f"  跳過第 {idx+1} 條：無有效URL")
                    self.stats['skipped_articles'] += 1
                    continue
                
                # 檢查是否是有問題的URL
                if 'finnhub.io' in final_url:
                    print(f"  跳過第 {idx+1} 條：仍為Finnhub API URL")
                    self.stats['skipped_articles'] += 1
                    continue
                
                session_id = f"{symbol}-{idx+1}"
                task = self.crawl_single_article(final_url, headline, session_id)
                tasks.append((idx, row, task))
                self.stats['total_articles'] += 1
            
            if not tasks:
                print(f"  {symbol}: 無有效文章可爬取")
                return False
            
            print(f"  開始爬取 {len(tasks)} 篇文章...")
            
            # 執行並發爬取
            results = []
            for i in range(0, len(tasks), self.max_concurrent):
                batch = tasks[i:i + self.max_concurrent]
                batch_tasks = [task for _, _, task in batch]
                
                print(f"    處理批次 {i//self.max_concurrent + 1}: {len(batch_tasks)} 篇文章")
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # 處理結果
                for j, (idx, row, _) in enumerate(batch):
                    if j < len(batch_results) and not isinstance(batch_results[j], Exception):
                        article_result = batch_results[j]
                        
                        # 合併原始數據和爬取結果
                        combined_result = {
                            **row.to_dict(),
                            **article_result
                        }
                        results.append(combined_result)
                    else:
                        # 處理異常情況
                        error_result = {
                            **row.to_dict(),
                            'crawl_success': False,
                            'error_message': str(batch_results[j]) if j < len(batch_results) else 'Unknown error',
                            'crawl_timestamp': datetime.now().isoformat()
                        }
                        results.append(error_result)
                        self.stats['failed_articles'] += 1
            
            # 保存結果
            if results:
                output_df = pd.DataFrame(results)
                output_file = os.path.join(output_dir, f"{symbol.lower()}_content.csv")
                output_df.to_csv(output_file, index=False, encoding='utf-8')
                
                # 統計成功率
                successful = len([r for r in results if r.get('crawl_success', False)])
                total = len(results)
                
                print(f"  ✅ {symbol}: 成功爬取 {successful}/{total} 篇文章")
                print(f"    結果保存到: {output_file}")
                
                return True
            else:
                print(f"  ❌ {symbol}: 無結果")
                return False
                
        except Exception as e:
            print(f"處理CSV文件時出錯 {csv_file_path}: {e}")
            return False

async def main():
    """主函數"""
    print("=== Step2: 使用crawl4ai抓取新聞內容 ===\n")
    
    # 設定路徑
    csv_dir = "./news_data"
    output_dir = "./news_content"
    
    # 創建輸出目錄
    os.makedirs(output_dir, exist_ok=True)
    
    # 查找所有CSV文件
    csv_files = glob.glob(os.path.join(csv_dir, "*_labeled.csv"))
    
    if not csv_files:
        print(f"錯誤: 在 {csv_dir} 中未找到 *_labeled.csv 文件")
        print("請先執行Step1生成標註的CSV文件")
        return
    
    print(f"找到 {len(csv_files)} 個CSV文件")
    
    # 創建爬取器
    crawler = NewsContentCrawler(
        max_concurrent=3,  # 可調整並發數
        delay=1.0,         # 請求間延遲
        use_llm=False      # 是否使用LLM提取結構化內容
    )
    
    # 處理統計
    total_files = len(csv_files)
    successful_files = 0
    
    # 處理每個CSV文件
    for i, csv_file in enumerate(csv_files):
        filename = os.path.basename(csv_file)
        print(f"\n--- 處理文件 {i+1}/{total_files}: {filename} ---")
        
        if await crawler.process_csv_file(csv_file, output_dir):
            successful_files += 1
    
    # 顯示最終統計
    print(f"\n=== Step2 處理完成 ===")
    print(f"總文件數: {total_files}")
    print(f"成功處理: {successful_files}")
    print(f"失敗: {total_files - successful_files}")
    print(f"\n文章統計:")
    print(f"  總文章數: {crawler.stats['total_articles']}")
    print(f"  成功爬取: {crawler.stats['successful_articles']}")
    print(f"  失敗: {crawler.stats['failed_articles']}")
    print(f"  跳過: {crawler.stats['skipped_articles']}")
    print(f"\n所有結果已保存到: {output_dir}")

if __name__ == "__main__":
    asyncio.run(main()) 
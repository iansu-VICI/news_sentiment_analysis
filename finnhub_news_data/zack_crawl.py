import asyncio
import random
import time
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

class ZacksScraper:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

    def get_random_ua(self):
        return random.choice(self.user_agents)

    async def bypass_cloudflare(self, url):
        """正確的 Crawl4AI 配置"""
        
        # 瀏覽器配置
        browser_config = BrowserConfig(
            headless=True,
            user_agent=self.get_random_ua(),
            viewport_width=1920,
            viewport_height=1080,
            extra_args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security", 
                "--disable-features=VizDisplayCompositor",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-plugins"
            ]
        )

        # 爬取運行配置
        crawler_config = CrawlerRunConfig(
            cache_mode="bypass",
            wait_for="css:body",
            delay_before_return_html=3.0,
            js_code="window.scrollTo(0, document.body.scrollHeight);",
            screenshot=False,
            verbose=True
        )

        async with AsyncWebCrawler(config=browser_config, verbose=True) as crawler:
            try:
                result = await crawler.arun(url=url, config=crawler_config)
                
                if result.success:
                    return self.process_content(result)
                else:
                    print(f"爬取失敗: {result.error_message}")
                    return None
                    
            except Exception as e:
                print(f"爬取過程中發生錯誤: {e}")
                return None

    def process_content(self, result):
        """處理爬取結果 - 修正切片錯誤"""
        # 安全地處理 links 屬性
        links = []
        try:
            if hasattr(result, 'links') and result.links is not None:
                if isinstance(result.links, (list, tuple)):
                    links = list(result.links)[:5]  # 取前5個連結
                else:
                    print(f"Warning: result.links 不是列表類型: {type(result.links)}")
        except Exception as e:
            print(f"處理 links 時發生錯誤: {e}")
        
        # 安全地處理其他屬性
        try:
            title = result.metadata.get("title", "") if hasattr(result, 'metadata') and result.metadata else ""
            content = result.markdown if hasattr(result, 'markdown') else ""
            html_length = len(result.html) if hasattr(result, 'html') and result.html else 0
            status_code = result.status_code if hasattr(result, 'status_code') else 0
            url = result.url if hasattr(result, 'url') else ""
            success = result.success if hasattr(result, 'success') else False
            
        except Exception as e:
            print(f"處理結果屬性時發生錯誤: {e}")
            return None
        
        return {
            "url": url,
            "title": title,
            "content": content,
            "html_length": html_length,
            "success": success,
            "status_code": status_code,
            "links": links
        }

async def main():
    scraper = ZacksScraper()
    
    # 測試基本連接
    print("測試 Zacks 首頁...")
    homepage_result = await scraper.bypass_cloudflare("https://www.zacks.com/")
    
    if homepage_result:
        print(f"✅ 首頁爬取成功: {homepage_result['title']}")
        print(f"HTML 長度: {homepage_result['html_length']}")
        print(f"狀態碼: {homepage_result['status_code']}")
        print(f"連結數量: {len(homepage_result['links'])}")
        
        # 等待一段時間後爬取目標文章
        await asyncio.sleep(random.uniform(3, 6))
        
        target_url = "https://www.zacks.com/commentary/2478426/4-pollution-control-stocks-to-watch-despite-industry-headwinds"
        print(f"\n爬取目標文章...")
        
        article_result = await scraper.bypass_cloudflare(target_url)
        
        if article_result:
            print(f"✅ 文章爬取成功: {article_result['title']}")
            print(f"內容長度: {len(article_result['content'])}")
            print(f"內容預覽: {article_result['content'][:300]}...")
            
            # 保存結果
            with open("zacks_article.md", "w", encoding="utf-8") as f:
                f.write(f"# {article_result['title']}\n\n")
                f.write(f"**URL:** {article_result['url']}\n\n")
                f.write(f"**狀態碼:** {article_result['status_code']}\n\n")
                f.write("---\n\n")
                f.write(article_result['content'])
            
            print("✅ 文章已保存到 zacks_article.md")
        else:
            print("❌ 文章爬取失敗")
    else:
        print("❌ 首頁爬取失敗")

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Nasdaq 文章爬取器 - 使用 Crawl4AI
用于爬取 Nasdaq 网站的文章内容
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.extraction_strategy import LLMExtractionStrategy
    from crawl4ai.chunking_strategy import RegexChunking
except ImportError:
    print("错误: 未安装 crawl4ai 库")
    print("请运行: pip install crawl4ai")
    exit(1)

class NasdaqCrawler:
    """Nasdaq 网站爬虫类"""
    
    def __init__(self, output_dir: str = "nasdaq_articles"):
        """
        初始化爬虫
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        self.raw_dir = self.output_dir / "raw_html"
        self.processed_dir = self.output_dir / "processed_articles"
        self.json_dir = self.output_dir / "json_data"
        
        for dir_path in [self.raw_dir, self.processed_dir, self.json_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def extract_article_id(self, url: str) -> str:
        """从URL中提取文章ID"""
        # 从URL中提取文章标识符
        match = re.search(r'/articles/([^/]+)', url)
        if match:
            return match.group(1)
        
        # 如果没有找到，使用URL的最后部分
        return url.split('/')[-1].replace('.html', '').replace('.htm', '')
    
    async def crawl_article(self, url: str, use_llm: bool = False) -> Dict[str, Any]:
        """
        爬取单篇文章
        
        Args:
            url: 文章URL
            use_llm: 是否使用LLM提取策略
            
        Returns:
            包含文章数据的字典
        """
        print(f"开始爬取: {url}")
        
        # 配置爬虫参数
        crawler_config = {
            "headless": True,
            "verbose": True,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "wait_for": "networkidle",
            "timeout": 30000,  # 30秒超时
        }
        
        # 提取策略配置
        extraction_strategy = None
        if use_llm:
            # 使用LLM提取策略（需要配置API密钥）
            extraction_strategy = LLMExtractionStrategy(
                provider="openai",  # 或其他支持的提供商
                api_token=os.getenv("OPENAI_API_KEY"),
                instruction="""
                请提取以下信息：
                1. 文章标题
                2. 发布日期
                3. 作者
                4. 文章正文内容
                5. 关键词/标签
                6. 文章摘要
                
                请以JSON格式返回结果。
                """
            )
        
        async with AsyncWebCrawler(**crawler_config) as crawler:
            try:
                # 执行爬取
                result = await crawler.arun(
                    url=url,
                    extraction_strategy=extraction_strategy,
                    chunking_strategy=RegexChunking(),
                    bypass_cache=True,
                    remove_overlay_elements=True,
                    simulate_user=True,
                    override_navigator=True
                )
                
                if result.success:
                    print(f"✅ 成功爬取: {url}")
                    
                    # 提取文章ID
                    article_id = self.extract_article_id(url)
                    
                    # 保存原始HTML
                    raw_file = self.raw_dir / f"{article_id}.html"
                    with open(raw_file, 'w', encoding='utf-8') as f:
                        f.write(result.html)
                    
                    # 处理提取的数据
                    article_data = {
                        "url": url,
                        "article_id": article_id,
                        "title": result.metadata.get("title", ""),
                        "crawl_timestamp": datetime.now().isoformat(),
                        "success": True,
                        "markdown_content": result.markdown,
                        "cleaned_html": result.cleaned_html,
                        "links": result.links,
                        "media": result.media,
                        "metadata": result.metadata
                    }
                    
                    # 如果使用了LLM提取，添加提取的数据
                    if use_llm and result.extracted_content:
                        try:
                            llm_data = json.loads(result.extracted_content)
                            article_data["llm_extracted"] = llm_data
                        except json.JSONDecodeError:
                            article_data["llm_extracted_raw"] = result.extracted_content
                    
                    # 手动提取一些基本信息
                    article_data.update(self.extract_basic_info(result.cleaned_html))
                    
                    # 保存JSON数据
                    json_file = self.json_dir / f"{article_id}.json"
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(article_data, f, ensure_ascii=False, indent=2)
                    
                    # 保存处理后的文章文本
                    text_file = self.processed_dir / f"{article_id}.txt"
                    with open(text_file, 'w', encoding='utf-8') as f:
                        f.write(f"标题: {article_data.get('title', 'N/A')}\n")
                        f.write(f"URL: {url}\n")
                        f.write(f"爬取时间: {article_data['crawl_timestamp']}\n")
                        f.write(f"发布日期: {article_data.get('publish_date', 'N/A')}\n")
                        f.write(f"作者: {article_data.get('author', 'N/A')}\n")
                        f.write("-" * 80 + "\n\n")
                        f.write(result.markdown)
                    
                    return article_data
                    
                else:
                    print(f"❌ 爬取失败: {url}")
                    print(f"错误信息: {result.error_message}")
                    
                    return {
                        "url": url,
                        "success": False,
                        "error": result.error_message,
                        "crawl_timestamp": datetime.now().isoformat()
                    }
                    
            except Exception as e:
                print(f"❌ 爬取异常: {url}")
                print(f"异常信息: {str(e)}")
                
                return {
                    "url": url,
                    "success": False,
                    "error": str(e),
                    "crawl_timestamp": datetime.now().isoformat()
                }
    
    def extract_basic_info(self, html_content: str) -> Dict[str, Any]:
        """
        从HTML中提取基本信息
        
        Args:
            html_content: 清理后的HTML内容
            
        Returns:
            提取的信息字典
        """
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        info = {}
        
        # 提取发布日期
        date_selectors = [
            'time[datetime]',
            '.timestamp',
            '.publish-date',
            '.article-date',
            '[data-module="ArticleDateTime"]'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = date_elem.get('datetime') or date_elem.get_text().strip()
                info['publish_date'] = date_text
                break
        
        # 提取作者
        author_selectors = [
            '.author',
            '.byline',
            '.article-author',
            '[data-module="ArticleAuthor"]',
            '.writer'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                info['author'] = author_elem.get_text().strip()
                break
        
        # 提取摘要
        summary_selectors = [
            '.article-summary',
            '.summary',
            '.excerpt',
            '.lead'
        ]
        
        for selector in summary_selectors:
            summary_elem = soup.select_one(selector)
            if summary_elem:
                info['summary'] = summary_elem.get_text().strip()
                break
        
        return info
    
    async def crawl_multiple_articles(self, urls: list, use_llm: bool = False, delay: float = 2.0):
        """
        爬取多篇文章
        
        Args:
            urls: URL列表
            use_llm: 是否使用LLM提取
            delay: 请求间隔（秒）
        """
        results = []
        
        for i, url in enumerate(urls, 1):
            print(f"\n进度: {i}/{len(urls)}")
            
            result = await self.crawl_article(url, use_llm=use_llm)
            results.append(result)
            
            # 添加延迟避免被封
            if i < len(urls):
                print(f"等待 {delay} 秒...")
                await asyncio.sleep(delay)
        
        # 保存汇总结果
        summary_file = self.output_dir / "crawl_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_urls": len(urls),
                "successful": sum(1 for r in results if r.get("success", False)),
                "failed": sum(1 for r in results if not r.get("success", False)),
                "results": results,
                "crawl_timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n爬取完成！结果保存在: {self.output_dir}")
        return results

async def main():
    """主函数"""
    # 示例URL
    test_url = "https://www.nasdaq.com/articles/are-pelotons-bikes-just-loss-leaders-2021-02-28"
    
    # 创建爬虫实例
    crawler = NasdaqCrawler()
    
    print("=== Nasdaq 文章爬虫 ===")
    print(f"目标URL: {test_url}")
    
    # 爬取单篇文章
    result = await crawler.crawl_article(test_url, use_llm=False)
    
    if result.get("success"):
        print("\n✅ 爬取成功！")
        print(f"文章标题: {result.get('title', 'N/A')}")
        print(f"文章ID: {result.get('article_id', 'N/A')}")
        print(f"输出目录: {crawler.output_dir}")
    else:
        print("\n❌ 爬取失败！")
        print(f"错误信息: {result.get('error', 'Unknown error')}")
    
    # 如果需要爬取多个URL，可以使用以下代码：
    urls = [
        "https://www.nasdaq.com/articles/are-pelotons-bikes-just-loss-leaders-2021-02-28"        # 添加更多URL...
    ]
    results = await crawler.crawl_multiple_articles(urls, delay=3.0)

if __name__ == "__main__":
    # 运行爬虫
    asyncio.run(main()) 
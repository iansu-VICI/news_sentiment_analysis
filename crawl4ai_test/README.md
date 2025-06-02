# Crawl4AI Nasdaq 爬虫 - 快速开始

## 简介
使用 [Crawl4AI](https://github.com/unclecode/crawl4ai) 爬取 Nasdaq 网站文章的专用工具。

## 快速安装（推荐）

### 自动安装（Ubuntu/Debian）
```bash
# 运行自动安装脚本
./setup_crawl4ai.sh
```

### 手动安装
```bash
# 1. 创建虚拟环境
python3 -m venv crawl4ai_env
source crawl4ai_env/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装 Playwright 浏览器
playwright install chromium
playwright install-deps

# 4. 运行测试
python test_crawl4ai_simple.py
```

## 使用方法

### 1. 爬取单篇文章
```bash
# 激活环境
source crawl4ai_env/bin/activate

# 运行爬虫
python crawl4ai_nasdaq_scraper.py
```

### 2. 自定义目标 URL
编辑 `crawl4ai_nasdaq_scraper.py` 文件中的 `test_url` 变量：
```python
test_url = "https://www.nasdaq.com/articles/your-target-article"
```

### 3. 批量爬取
取消注释主函数中的批量爬取代码：
```python
urls = [
    "https://www.nasdaq.com/articles/article1",
    "https://www.nasdaq.com/articles/article2",
    # 添加更多 URL...
]
results = await crawler.crawl_multiple_articles(urls, delay=3.0)
```

## 输出文件

程序会在 `nasdaq_articles/` 目录下创建：

```
nasdaq_articles/
├── raw_html/              # 原始 HTML 文件
├── processed_articles/    # 处理后的文本文件  
├── json_data/            # JSON 格式数据
└── crawl_summary.json    # 爬取汇总
```

## 主要特性

- ✅ **异步爬取** - 高效的并发处理
- ✅ **智能提取** - 自动提取标题、内容、日期等
- ✅ **多格式输出** - HTML、Markdown、JSON、纯文本
- ✅ **反爬虫处理** - 模拟真实用户行为
- ✅ **错误恢复** - 自动重试和错误处理
- ✅ **可配置** - 灵活的参数配置

## 与现有爬虫的对比

| 特性 | Crawl4AI 版本 | 原有 Playwright 版本 |
|------|---------------|---------------------|
| 安装复杂度 | 简单 | 复杂 |
| 代码量 | 少 | 多 |
| 维护性 | 高 | 中等 |
| 功能丰富度 | 高 | 中等 |
| 性能 | 优秀 | 良好 |
| LLM 集成 | 支持 | 不支持 |

## 故障排除

### 常见问题

1. **导入错误**
   ```bash
   pip install crawl4ai
   ```

2. **Playwright 安装失败**
   ```bash
   playwright install chromium
   playwright install-deps
   ```

3. **权限错误**
   ```bash
   chmod +x *.py
   ```

### 测试安装
```bash
python test_crawl4ai_simple.py
```

## 高级配置

### 使用代理
```python
crawler_config = {
    "proxy": "http://proxy-server:port"
}
```

### 启用 LLM 提取
```python
# 设置 API 密钥
export OPENAI_API_KEY="your_key"

# 在代码中启用
result = await crawler.crawl_article(url, use_llm=True)
```

### 自定义延迟
```python
results = await crawler.crawl_multiple_articles(urls, delay=5.0)
```

## 文件说明

- `crawl4ai_nasdaq_scraper.py` - 主爬虫程序
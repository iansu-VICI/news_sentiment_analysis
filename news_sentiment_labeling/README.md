# 新聞標註
## 目標:標註S&P500 公司2021-2025的新聞資料
## 流程 (建立在news_sentiment_labeling資料夾中)


### step1
對step1抓下來sp500中各公司的發布日期，其存在sp500_news_urls/*.json中
使用yfinance抓取新聞發布後(publish_date)三個交易日的價格
並計算其excess return，然後進行標註:
1: 新聞發布後三個交易日excess return > 0%
0: 新聞發布後三個交易日excess return < 0%
並將結果存成csv檔

### step2
使用crawl_news/run.sh, crawl_news/batch_download_news.py的作法來用crawl4ai抓取step1獲得的json檔中其最終url的新聞內容，並存成csv檔


## 備註
- 盡量用shell來執行流程
- 股價的資訊請你從yfinance中抓取
- step1, step2的shell分開執行
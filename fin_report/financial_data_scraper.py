#!/usr/bin/env python3
"""
財報數據抓取器 - 使用 Finnhub API
用於抓取 comp.txt 中列出的公司基本財報資料
"""

import finnhub
import json
import yaml
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

# 載入 .env 文件
load_dotenv()

# 從環境變量獲取 API 金鑰
API_KEY = os.getenv("FINNHUB_API_KEY")

if not API_KEY:
    print("❌ 錯誤：請在 .env 文件中設定 FINNHUB_API_KEY")
    print("請創建 .env 文件並添加: FINNHUB_API_KEY=your_api_key_here")
    exit(1)

# 初始化 Finnhub 客戶端
finnhub_client = finnhub.Client(api_key=API_KEY)

class FinancialDataScraper:
    """財報數據抓取器類"""
    
    def __init__(self, output_dir: str = "financial_reports"):
        """
        初始化抓取器
        
        Args:
            output_dir: 輸出目錄
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 創建子目錄
        self.basic_financials_dir = self.output_dir / "basic_financials"
        self.company_profiles_dir = self.output_dir / "company_profiles"
        self.metrics_dir = self.output_dir / "metrics"
        self.earnings_dir = self.output_dir / "earnings"
        self.raw_data_dir = self.output_dir / "raw_data"
        
        for dir_path in [self.basic_financials_dir, self.company_profiles_dir, 
                        self.metrics_dir, self.earnings_dir, self.raw_data_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def load_company_list(self, comp_file: str = "comp.txt") -> dict:
        """
        從 comp.txt 文件載入公司列表
        
        Args:
            comp_file: 公司列表文件路徑
            
        Returns:
            包含主要股票和競爭對手的字典
        """
        try:
            with open(comp_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            print(f"✅ 成功載入公司列表: {comp_file}")
            print(f"主要股票: {len(data['main_tickers'])} 個")
            print(f"競爭對手組: {len(data['competitors'])} 組")
            
            return data
        except Exception as e:
            print(f"❌ 載入公司列表失敗: {e}")
            return None
    
    def get_company_profile(self, symbol: str) -> dict:
        """
        獲取公司基本資料
        
        Args:
            symbol: 股票代碼
            
        Returns:
            公司基本資料字典
        """
        try:
            print(f"正在獲取 {symbol} 的公司資料...")
            profile = finnhub_client.company_profile2(symbol=symbol)
            
            if profile:
                print(f"✅ 成功獲取 {symbol} 公司資料")
                return {
                    "symbol": symbol,
                    "name": profile.get("name", "N/A"),
                    "country": profile.get("country", "N/A"),
                    "currency": profile.get("currency", "N/A"),
                    "exchange": profile.get("exchange", "N/A"),
                    "industry": profile.get("finnhubIndustry", "N/A"),
                    "market_cap": profile.get("marketCapitalization", 0),
                    "share_outstanding": profile.get("shareOutstanding", 0),
                    "logo": profile.get("logo", ""),
                    "weburl": profile.get("weburl", ""),
                    "phone": profile.get("phone", ""),
                    "ipo": profile.get("ipo", ""),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"⚠️  {symbol} 公司資料為空")
                return None
                
        except Exception as e:
            print(f"❌ 獲取 {symbol} 公司資料失敗: {e}")
            return None
    
    def get_basic_financials(self, symbol: str, metric: str = "all") -> dict:
        """
        獲取基本財務數據
        
        Args:
            symbol: 股票代碼
            metric: 指標類型 (all, annual, quarterly)
            
        Returns:
            基本財務數據字典
        """
        try:
            print(f"正在獲取 {symbol} 的基本財務數據...")
            financials = finnhub_client.company_basic_financials(symbol, metric)
            
            if financials:
                print(f"✅ 成功獲取 {symbol} 基本財務數據")
                return {
                    "symbol": symbol,
                    "metric_type": metric,
                    "data": financials,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"⚠️  {symbol} 基本財務數據為空")
                return None
                
        except Exception as e:
            print(f"❌ 獲取 {symbol} 基本財務數據失敗: {e}")
            return None
    
    def get_company_metrics(self, symbol: str, date: str = None) -> dict:
        """
        獲取公司關鍵指標
        
        Args:
            symbol: 股票代碼
            date: 日期 (YYYY-MM-DD)，默認為當前日期
            
        Returns:
            公司指標字典
        """
        try:
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')
            
            print(f"正在獲取 {symbol} 的公司指標 ({date})...")
            # 使用正確的方法名稱
            metrics = finnhub_client.company_basic_financials(symbol, 'all')
            
            if metrics:
                print(f"✅ 成功獲取 {symbol} 公司指標")
                return {
                    "symbol": symbol,
                    "date": date,
                    "data": metrics,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"⚠️  {symbol} 公司指標為空")
                return None
                
        except Exception as e:
            print(f"❌ 獲取 {symbol} 公司指標失敗: {e}")
            return None
    
    def get_earnings_calendar(self, symbol: str, from_date: str = None, to_date: str = None) -> dict:
        """
        獲取財報發布日程
        
        Args:
            symbol: 股票代碼
            from_date: 開始日期
            to_date: 結束日期
            
        Returns:
            財報日程字典
        """
        try:
            if from_date is None:
                from_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            if to_date is None:
                to_date = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
            
            print(f"正在獲取 {symbol} 的財報日程 ({from_date} 到 {to_date})...")
            earnings = finnhub_client.earnings_calendar(from_date, to_date, symbol, international=False)
            
            if earnings and earnings.get('earningsCalendar'):
                print(f"✅ 成功獲取 {symbol} 財報日程")
                return {
                    "symbol": symbol,
                    "from_date": from_date,
                    "to_date": to_date,
                    "data": earnings,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"⚠️  {symbol} 財報日程為空")
                return None
                
        except Exception as e:
            print(f"❌ 獲取 {symbol} 財報日程失敗: {e}")
            return None
    
    def scrape_single_company(self, symbol: str, delay: float = 1.0) -> dict:
        """
        抓取單一公司的所有財報數據
        
        Args:
            symbol: 股票代碼
            delay: 請求間隔（秒）
            
        Returns:
            包含所有數據的字典
        """
        print(f"\n=== 開始抓取 {symbol} 的財報數據 ===")
        
        company_data = {
            "symbol": symbol,
            "scrape_timestamp": datetime.now().isoformat(),
            "profile": None,
            "basic_financials": None,
            "metrics": None,
            "earnings": None,
            "success": False
        }
        
        try:
            # 1. 獲取公司基本資料
            company_data["profile"] = self.get_company_profile(symbol)
            time.sleep(delay)
            
            # 2. 獲取基本財務數據
            company_data["basic_financials"] = self.get_basic_financials(symbol)
            time.sleep(delay)
            
            # 3. 獲取公司指標
            company_data["metrics"] = self.get_company_metrics(symbol)
            time.sleep(delay)
            
            # 4. 獲取財報日程
            company_data["earnings"] = self.get_earnings_calendar(symbol)
            time.sleep(delay)
            
            # 檢查是否至少獲取到一些數據
            if any([company_data["profile"], company_data["basic_financials"], 
                   company_data["metrics"], company_data["earnings"]]):
                company_data["success"] = True
                print(f"✅ {symbol} 數據抓取完成")
            else:
                print(f"⚠️  {symbol} 未獲取到任何數據")
            
            # 保存單個公司的數據
            self.save_company_data(company_data)
            
        except Exception as e:
            print(f"❌ 抓取 {symbol} 數據時發生錯誤: {e}")
            company_data["error"] = str(e)
        
        return company_data
    
    def save_company_data(self, company_data: dict):
        """
        保存單個公司的數據到文件
        
        Args:
            company_data: 公司數據字典
        """
        symbol = company_data["symbol"]
        
        try:
            # 保存完整的原始數據
            raw_file = self.raw_data_dir / f"{symbol}_complete.json"
            with open(raw_file, 'w', encoding='utf-8') as f:
                json.dump(company_data, f, ensure_ascii=False, indent=2)
            
            # 分別保存各類數據
            if company_data["profile"]:
                profile_file = self.company_profiles_dir / f"{symbol}_profile.json"
                with open(profile_file, 'w', encoding='utf-8') as f:
                    json.dump(company_data["profile"], f, ensure_ascii=False, indent=2)
            
            if company_data["basic_financials"]:
                financials_file = self.basic_financials_dir / f"{symbol}_financials.json"
                with open(financials_file, 'w', encoding='utf-8') as f:
                    json.dump(company_data["basic_financials"], f, ensure_ascii=False, indent=2)
            
            if company_data["metrics"]:
                metrics_file = self.metrics_dir / f"{symbol}_metrics.json"
                with open(metrics_file, 'w', encoding='utf-8') as f:
                    json.dump(company_data["metrics"], f, ensure_ascii=False, indent=2)
            
            if company_data["earnings"]:
                earnings_file = self.earnings_dir / f"{symbol}_earnings.json"
                with open(earnings_file, 'w', encoding='utf-8') as f:
                    json.dump(company_data["earnings"], f, ensure_ascii=False, indent=2)
            
            print(f"💾 {symbol} 數據已保存到文件")
            
        except Exception as e:
            print(f"❌ 保存 {symbol} 數據失敗: {e}")
    
    def scrape_all_companies(self, comp_file: str = "comp.txt", delay: float = 2.0, include_competitors: bool = True):
        """
        抓取所有公司的財報數據
        
        Args:
            comp_file: 公司列表文件
            delay: 請求間隔（秒）
            include_competitors: 是否包含競爭對手
        """
        print("=== 開始批量抓取財報數據 ===")
        
        # 載入公司列表
        company_data = self.load_company_list(comp_file)
        if not company_data:
            return
        
        # 收集所有需要抓取的股票代碼
        all_symbols = set(company_data["main_tickers"])
        
        if include_competitors:
            for competitors in company_data["competitors"].values():
                all_symbols.update(competitors)
        
        all_symbols = sorted(list(all_symbols))
        print(f"\n總共需要抓取 {len(all_symbols)} 個股票的數據")
        print(f"股票列表: {', '.join(all_symbols)}")
        
        # 開始抓取
        results = []
        successful = 0
        failed = 0
        
        for i, symbol in enumerate(all_symbols, 1):
            print(f"\n進度: {i}/{len(all_symbols)} - {symbol}")
            
            result = self.scrape_single_company(symbol, delay)
            results.append(result)
            
            if result["success"]:
                successful += 1
            else:
                failed += 1
            
            # 顯示進度
            print(f"當前進度: 成功 {successful}, 失敗 {failed}")
        
        # 保存匯總結果
        summary = {
            "scrape_timestamp": datetime.now().isoformat(),
            "total_companies": len(all_symbols),
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful/len(all_symbols)*100):.1f}%",
            "companies": all_symbols,
            "results": results
        }
        
        summary_file = self.output_dir / "scrape_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # 創建 CSV 摘要
        self.create_csv_summary(results)
        
        print(f"\n=== 抓取完成 ===")
        print(f"總計: {len(all_symbols)} 個公司")
        print(f"成功: {successful} 個")
        print(f"失敗: {failed} 個")
        print(f"成功率: {(successful/len(all_symbols)*100):.1f}%")
        print(f"結果保存在: {self.output_dir}")
    
    def create_csv_summary(self, results: list):
        """
        創建 CSV 格式的摘要報告
        
        Args:
            results: 抓取結果列表
        """
        try:
            summary_data = []
            
            for result in results:
                row = {
                    "Symbol": result["symbol"],
                    "Success": result["success"],
                    "Company_Name": "",
                    "Industry": "",
                    "Country": "",
                    "Market_Cap": "",
                    "Has_Profile": bool(result.get("profile")),
                    "Has_Financials": bool(result.get("basic_financials")),
                    "Has_Metrics": bool(result.get("metrics")),
                    "Has_Earnings": bool(result.get("earnings")),
                    "Error": result.get("error", "")
                }
                
                # 如果有公司資料，填入詳細信息
                if result.get("profile"):
                    profile = result["profile"]
                    row["Company_Name"] = profile.get("name", "")
                    row["Industry"] = profile.get("industry", "")
                    row["Country"] = profile.get("country", "")
                    row["Market_Cap"] = profile.get("market_cap", "")
                
                summary_data.append(row)
            
            # 保存為 CSV
            df = pd.DataFrame(summary_data)
            csv_file = self.output_dir / "companies_summary.csv"
            df.to_csv(csv_file, index=False, encoding='utf-8')
            
            print(f"📊 CSV 摘要已保存: {csv_file}")
            
        except Exception as e:
            print(f"❌ 創建 CSV 摘要失敗: {e}")

def main():
    """主函數"""
    print("=== Finnhub 財報數據抓取器 ===")
    
    # 創建抓取器實例
    scraper = FinancialDataScraper()
    
    # 檢查 comp.txt 文件是否存在
    comp_file = "comp.txt"
    if not os.path.exists(comp_file):
        print(f"❌ 找不到 {comp_file} 文件")
        print("請確保 comp.txt 文件在當前目錄中")
        return
    
    # 開始抓取所有公司數據
    scraper.scrape_all_companies(
        comp_file=comp_file,
        delay=2.0,  # 2秒間隔避免API限制
        include_competitors=True  # 包含競爭對手
    )

if __name__ == "__main__":
    main() 
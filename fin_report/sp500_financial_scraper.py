#!/usr/bin/env python3
"""
SP500 財報數據抓取器 - 使用 Finnhub API
用於抓取 sp500.json 中列出的股票及其同行的完整財報資料
每個 SP500 公司和其同行公司放在同一個資料夾中
"""

import finnhub
import json
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

class SP500FinancialScraper:
    """SP500 財報數據抓取器類"""
    
    def __init__(self, output_dir: str = "sp500_financial_reports"):
        """
        初始化抓取器
        
        Args:
            output_dir: 輸出目錄
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def load_sp500_list(self, sp500_file: str = "sp500.json") -> list:
        """
        從 sp500.json 文件載入股票列表
        
        Args:
            sp500_file: SP500 股票列表文件路徑
            
        Returns:
            股票代碼列表
        """
        try:
            with open(sp500_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 過濾掉明顯不是股票代碼的項目（太長或包含空格）
            valid_tickers = []
            for ticker in data:
                valid_tickers.append(ticker.upper())
            
            print(f"✅ 成功載入 SP500 股票列表: {sp500_file}")
            print(f"原始項目數: {len(data)}")
            print(f"有效股票代碼: {len(valid_tickers)} 個")
            
            return sorted(valid_tickers)
        except Exception as e:
            print(f"❌ 載入 SP500 股票列表失敗: {e}")
            return []
    
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
    
    def get_company_peers(self, symbol: str) -> dict:
        """
        獲取公司同行列表
        
        Args:
            symbol: 股票代碼
            
        Returns:
            同行公司列表
        """
        try:
            print(f"正在獲取 {symbol} 的同行公司...")
            peers = finnhub_client.company_peers(symbol)
            
            if peers:
                print(f"✅ 成功獲取 {symbol} 同行公司: {len(peers)} 個")
                return {
                    "symbol": symbol,
                    "peers": peers,
                    "peers_count": len(peers),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"⚠️  {symbol} 同行公司列表為空")
                return None
                
        except Exception as e:
            print(f"❌ 獲取 {symbol} 同行公司失敗: {e}")
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
            
            print(f"正在獲取 {symbol} 的財報日程...")
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
    
    def save_json(self, file_path: Path, data: dict):
        """
        保存 JSON 數據到文件
        
        Args:
            file_path: 文件路徑
            data: 要保存的數據
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def scrape_single_company(self, symbol: str, delay: float = 1.0, include_peers: bool = True) -> dict:
        """
        抓取單一公司的所有財報數據，包括同行公司的完整財務數據
        
        Args:
            symbol: 股票代碼
            delay: 請求間隔（秒）
            include_peers: 是否包含同行公司數據
            
        Returns:
            包含所有數據的字典
        """
        print(f"\n=== 開始抓取 {symbol} 的財報數據 ===")
        
        company_data = {
            "symbol": symbol,
            "scrape_timestamp": datetime.now().isoformat(),
            "profile": None,
            "basic_financials": None,
            "earnings": None,
            "peers": None,
            "peers_data": {},
            "success": False
        }
        
        try:
            # 1. 獲取主公司基本資料
            company_data["profile"] = self.get_company_profile(symbol)
            time.sleep(delay)
            
            # 2. 獲取主公司基本財務數據
            company_data["basic_financials"] = self.get_basic_financials(symbol)
            time.sleep(delay)
            
            # 3. 獲取主公司財報日程
            company_data["earnings"] = self.get_earnings_calendar(symbol)
            time.sleep(delay)
            
            # 4. 獲取同行公司列表
            if include_peers:
                company_data["peers"] = self.get_company_peers(symbol)
                time.sleep(delay)
                
                # 5. 獲取同行公司的完整財務數據（限制數量避免API限制）
                if company_data["peers"] and company_data["peers"]["peers"]:
                    peers_list = company_data["peers"]["peers"][:]  # 只取前5個同行
                    print(f"正在獲取 {symbol} 的同行公司完整財務數據...")
                    
                    for peer in peers_list:
                        if peer != symbol:  # 避免重複抓取自己
                            print(f"  正在抓取同行公司 {peer} 的數據...")
                            peer_data = {}
                            
                            # 同行公司基本資料
                            peer_data["profile"] = self.get_company_profile(peer)
                            time.sleep(delay)
                            
                            # 同行公司財務數據
                            peer_data["basic_financials"] = self.get_basic_financials(peer)
                            time.sleep(delay)
                            
                            # 同行公司財報日程
                            peer_data["earnings"] = self.get_earnings_calendar(peer)
                            time.sleep(delay)
                            
                            if any([peer_data["profile"], peer_data["basic_financials"], peer_data["earnings"]]):
                                company_data["peers_data"][peer] = peer_data
                                print(f"  ✅ 成功獲取同行公司 {peer} 的數據")
                            else:
                                print(f"  ⚠️  同行公司 {peer} 未獲取到任何數據")
            
            # 檢查是否至少獲取到一些數據
            if any([company_data["profile"], company_data["basic_financials"], 
                   company_data["earnings"], company_data["peers"]]):
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
        保存公司數據到對應的公司資料夾中，每個 SP500 公司和其同行放在同一個資料夾
        
        Args:
            company_data: 公司完整數據
        """
        symbol = company_data["symbol"]
        
        try:
            # 創建該公司的專屬資料夾
            company_dir = self.output_dir / symbol
            company_dir.mkdir(exist_ok=True)
            
            # 在公司資料夾中創建子目錄
            profiles_dir = company_dir / "company_profiles"
            financials_dir = company_dir / "basic_financials"
            earnings_dir = company_dir / "earnings"
            peers_dir = company_dir / "peers"
            raw_data_dir = company_dir / "raw_data"
            
            for dir_path in [profiles_dir, financials_dir, earnings_dir, peers_dir, raw_data_dir]:
                dir_path.mkdir(exist_ok=True)
            
            # 保存主公司基本資料
            if company_data["profile"]:
                profile_file = profiles_dir / f"{symbol}_profile.json"
                self.save_json(profile_file, company_data["profile"])
            
            # 保存主公司基本財務數據
            if company_data["basic_financials"]:
                financials_file = financials_dir / f"{symbol}_financials.json"
                self.save_json(financials_file, company_data["basic_financials"])
            
            # 保存主公司財報日程
            if company_data["earnings"]:
                earnings_file = earnings_dir / f"{symbol}_earnings.json"
                self.save_json(earnings_file, company_data["earnings"])
            
            # 保存同行公司列表
            if company_data["peers"]:
                peers_file = peers_dir / f"{symbol}_peers.json"
                self.save_json(peers_file, company_data["peers"])
            
            # 保存同行公司的完整財務數據
            for peer_symbol, peer_data in company_data["peers_data"].items():
                # 同行公司基本資料
                if peer_data.get("profile"):
                    peer_profile_file = profiles_dir / f"{peer_symbol}_profile.json"
                    self.save_json(peer_profile_file, peer_data["profile"])
                
                # 同行公司財務數據
                if peer_data.get("basic_financials"):
                    peer_financials_file = financials_dir / f"{peer_symbol}_financials.json"
                    self.save_json(peer_financials_file, peer_data["basic_financials"])
                
                # 同行公司財報日程
                if peer_data.get("earnings"):
                    peer_earnings_file = earnings_dir / f"{peer_symbol}_earnings.json"
                    self.save_json(peer_earnings_file, peer_data["earnings"])
            
            # 保存完整原始數據
            raw_file = raw_data_dir / f"{symbol}_complete.json"
            self.save_json(raw_file, company_data)
            
            print(f"💾 已保存 {symbol} 及其同行公司的所有數據到 {company_dir}")
            
        except Exception as e:
            print(f"❌ 保存 {symbol} 數據時發生錯誤: {e}")
    
    def scrape_sp500_companies(self, sp500_file: str = "sp500.json", delay: float = 2.0, 
                              max_companies: int = None, include_peers: bool = True):
        """
        抓取 SP500 公司的財報數據
        
        Args:
            sp500_file: SP500 股票列表文件
            delay: 請求間隔（秒）
            max_companies: 最大抓取公司數量（用於測試）
            include_peers: 是否包含同行公司
        """
        print("=== 開始批量抓取 SP500 財報數據 ===")
        
        # 載入 SP500 股票列表
        sp500_symbols = self.load_sp500_list(sp500_file)
        if not sp500_symbols:
            return
        
        # 限制抓取數量（如果指定）
        if max_companies:
            sp500_symbols = sp500_symbols[:max_companies]
            print(f"限制抓取數量: {max_companies} 個公司")
        
        print(f"\n總共需要抓取 {len(sp500_symbols)} 個股票的數據")
        print(f"股票列表: {', '.join(sp500_symbols[:10])}{'...' if len(sp500_symbols) > 10 else ''}")
        
        # 開始抓取
        results = []
        successful = 0
        failed = 0
        
        for i, symbol in enumerate(sp500_symbols, 1):
            print(f"\n進度: {i}/{len(sp500_symbols)} - {symbol}")
            
            result = self.scrape_single_company(symbol, delay, include_peers)
            results.append(result)
            
            if result["success"]:
                successful += 1
            else:
                failed += 1
            
            # 顯示進度
            print(f"當前進度: 成功 {successful}, 失敗 {failed}")
            
            # 每10個公司顯示一次詳細進度
            if i % 10 == 0:
                success_rate = (successful / i) * 100
                print(f"階段性統計: 已處理 {i} 個公司，成功率 {success_rate:.1f}%")
        
        # 保存匯總結果
        summary = {
            "scrape_timestamp": datetime.now().isoformat(),
            "total_companies": len(sp500_symbols),
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful/len(sp500_symbols)*100):.1f}%",
            "companies": sp500_symbols,
            "include_peers": include_peers,
            "results": results
        }
        
        summary_file = self.output_dir / "scrape_summary.json"
        self.save_json(summary_file, summary)
        
        # 創建 CSV 摘要
        self.create_csv_summary(results)
        
        print(f"\n=== 抓取完成 ===")
        print(f"總計: {len(sp500_symbols)} 個公司")
        print(f"成功: {successful} 個")
        print(f"失敗: {failed} 個")
        print(f"成功率: {(successful/len(sp500_symbols)*100):.1f}%")
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
                    "Peers_Count": 0,
                    "Peers_Data_Count": len(result.get("peers_data", {})),
                    "Has_Profile": bool(result.get("profile")),
                    "Has_Financials": bool(result.get("basic_financials")),
                    "Has_Earnings": bool(result.get("earnings")),
                    "Has_Peers": bool(result.get("peers")),
                    "Error": result.get("error", "")
                }
                
                # 如果有公司資料，填入詳細信息
                if result.get("profile"):
                    profile = result["profile"]
                    row["Company_Name"] = profile.get("name", "")
                    row["Industry"] = profile.get("industry", "")
                    row["Country"] = profile.get("country", "")
                    row["Market_Cap"] = profile.get("market_cap", "")
                
                # 如果有同行資料，填入數量
                if result.get("peers"):
                    row["Peers_Count"] = result["peers"].get("peers_count", 0)
                
                summary_data.append(row)
            
            # 保存為 CSV
            df = pd.DataFrame(summary_data)
            csv_file = self.output_dir / "sp500_companies_summary.csv"
            df.to_csv(csv_file, index=False, encoding='utf-8')
            
            print(f"📊 CSV 摘要已保存: {csv_file}")
            
        except Exception as e:
            print(f"❌ 創建 CSV 摘要失敗: {e}")

def main():
    """主函數"""
    print("=== SP500 Finnhub 財報數據抓取器 ===")
    
    # 創建抓取器實例
    scraper = SP500FinancialScraper()
    
    # 檢查 sp500.json 文件是否存在
    sp500_file = "sp500.json"
    if not os.path.exists(sp500_file):
        print(f"❌ 找不到 {sp500_file} 文件")
        print("請確保 sp500.json 文件在當前目錄中")
        return
    
    # 詢問是否要限制抓取數量（用於測試）
    print("\n選擇抓取模式:")
    print("1. 測試模式 (前10個公司)")
    print("2. 小批量模式 (前50個公司)")
    print("3. 完整模式 (所有SP500公司)")
    
    try:
        choice = input("請選擇 (1/2/3): ").strip()
        
        if choice == "1":
            max_companies = 10
        elif choice == "2":
            max_companies = 50
        elif choice == "3":
            max_companies = None
        else:
            print("無效選擇，使用測試模式")
            max_companies = 10
        
        # 開始抓取
        scraper.scrape_sp500_companies(
            sp500_file=sp500_file,
            delay=2.0,  # 2秒間隔
            max_companies=max_companies,
            include_peers=True
        )
        
    except KeyboardInterrupt:
        print("\n用戶中斷操作")
    except Exception as e:
        print(f"執行錯誤: {e}")

if __name__ == "__main__":
    main() 
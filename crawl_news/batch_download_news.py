#!/usr/bin/env python3
"""
批量新聞下載器 (升級版) - 使用 Crawl4AI 平行下載
-------------------------------------------------
1. 透過 asyncio + Semaphore 實現 *跨月份* 平行抓取
2. 保留 NewsCrawler 內部的單月文章抓取邏輯
3. 新增 CLI 參數 --max-concurrent-months / --max-concurrent-articles
4. 自動保存進度，可在中斷後續接續
"""

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
from threading import Lock

# 將當前目錄加入 import 路徑
sys.path.append(str(Path(__file__).parent))

try:
    from crawl4ai_news_scraper import NewsCrawler
except ImportError:
    print("❌ 找不到 crawl4ai_news_scraper 模組，請確認該檔案與本腳本位於同一資料夾")
    sys.exit(1)

try:
    from utils import get_api_key, validate_date_format
except ImportError:
    # 後備實作 (僅供測試)
    def get_api_key():
        return os.getenv("FINNHUB_API_KEY", "YOUR_FINNHUB_API_KEY")

    def validate_date_format(date_str: str) -> bool:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False


class BatchNewsDownloader:
    """批量新聞下載器 (支援跨月份並發)"""

    def __init__(
        self,
        api_key: str,
        output_base_dir: str = "batch_news_data",
        max_concurrent: int = 3,
        max_concurrent_articles: int = 5,
    ):
        self.api_key = api_key
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(exist_ok=True)

        # 並發控制 (月份層級)
        self.max_concurrent = max_concurrent
        self.month_semaphore = asyncio.Semaphore(max_concurrent)

        # 文章層級並發 (傳入 NewsCrawler)
        self.max_concurrent_articles = max_concurrent_articles

        # 進度與日誌
        self.progress_file = self.output_base_dir / "download_progress.json"
        self.log_file = self.output_base_dir / "download_log.txt"

        self.stats = {
            "total_months": 0,
            "successful_months": 0,
            "failed_months": 0,
            "skipped_months": 0,
            "total_articles": 0,
            "successful_articles": 0,
            "failed_articles": 0,
        }
        self.stats_lock = Lock()
        self._init_log()

    # ----------------------------------------
    # 公用工具
    # ----------------------------------------
    def _init_log(self):
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write(f"批量新聞下載開始時間: {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")

    def _log(self, msg: str, console: bool = True):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
        if console:
            print(msg)

    def _load_progress(self) -> Dict:
        if self.progress_file.exists():
            try:
                return json.loads(self.progress_file.read_text(encoding="utf-8"))
            except Exception as e:
                self._log(f"載入進度失敗: {e}")
        return {"completed_months": []}

    def _save_progress(self, completed_months: List[str]):
        data = {
            "completed_months": completed_months,
            "stats": self.stats,
            "last_update": datetime.now().isoformat(),
        }
        try:
            self.progress_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            self._log(f"保存進度時發生錯誤: {e}")

    def _update_stats(self, **delta):
        with self.stats_lock:
            for k, v in delta.items():
                if k in self.stats:
                    self.stats[k] += v

    # ----------------------------------------
    # 核心流程
    # ----------------------------------------
    @staticmethod
    def _month_iter(start_dt: datetime, end_dt: datetime):
        cur_year, cur_month = start_dt.year, start_dt.month
        while (cur_year < end_dt.year) or (
            cur_year == end_dt.year and cur_month <= end_dt.month
        ):
            first_day = f"{cur_year}-{cur_month:02d}-01"
            # 下一個月
            next_year = cur_year + (cur_month // 12)
            next_month = 1 if cur_month == 12 else cur_month + 1
            last_day_dt = datetime(next_year, next_month, 1) - timedelta(days=1)
            last_day = last_day_dt.strftime("%Y-%m-%d")
            yield cur_year, cur_month, first_day, last_day
            cur_year, cur_month = next_year, next_month

    async def _bounded_month_task(
        self,
        symbol: str,
        year: int,
        month: int,
        from_date: str,
        to_date: str,
        use_llm: bool,
        delay: float,
        max_articles: int,
        output_dir_name: str,
    ):
        async with self.month_semaphore:
            return await self._download_month_news(
                symbol,
                year,
                month,
                from_date,
                to_date,
                use_llm,
                delay,
                max_articles,
                output_dir_name,
            )

    async def _download_month_news(
        self,
        symbol: str,
        year: int,
        month: int,
        from_date: str,
        to_date: str,
        use_llm: bool,
        delay: float,
        max_articles: int,
        output_dir_name: str,
    ) -> Dict:
        month_key = f"{year}-{month:02d}"
        self._log(f"開始下載 {symbol} {month_key} ({from_date} ~ {to_date})")

        month_dir = self.output_base_dir / output_dir_name
        month_dir.mkdir(parents=True, exist_ok=True)
        try:
            crawler = NewsCrawler(api_key=self.api_key, output_dir=str(month_dir))
            results = await crawler.crawl_company_news(
                symbol=symbol,
                from_date=from_date,
                to_date=to_date,
                use_llm=use_llm,
                delay=delay,
                max_articles=max_articles,
            )
            ok = sum(1 for r in results if r.get("success"))
            fail = len(results) - ok
            self._update_stats(
                total_articles=len(results),
                successful_articles=ok,
                failed_articles=fail,
            )
            self._log(f"✅ {month_key} 完成: {ok}/{len(results)} 成功")
            return {
                "month": month_key,
                "success": True,
                "total_articles": len(results),
                "successful_articles": ok,
                "failed_articles": fail,
                "output_dir": str(month_dir),
            }
        except Exception as e:
            self._log(f"❌ {month_key} 失敗: {e}")
            return {
                "month": month_key,
                "success": False,
                "error": str(e),
                "total_articles": 0,
                "successful_articles": 0,
                "failed_articles": 0,
            }

    async def batch_download(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        use_llm: bool = False,
        delay: float = 0.5,
        max_articles_per_month: int | None = None,
        resume: bool = True,
    ) -> Dict:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        months = list(self._month_iter(start_dt, end_dt))
        self.stats["total_months"] = len(months)

        self._log(f"共 {len(months)} 個月份，將使用 {self.max_concurrent} 並行數")
        completed_months = set()
        if resume:
            completed_months = set(self._load_progress().get("completed_months", []))
            if completed_months:
                self._log(f"恢復下載，已完成 {len(completed_months)} 個月份")

        output_dir_name = f"{symbol.lower()}_news_{start_date.replace('-', '')}_{end_date.replace('-', '')}"

        # 建立 Task 清單
        tasks: list[asyncio.Task] = []
        for y, m, f, t in months:
            key = f"{y}-{m:02d}"
            if key in completed_months:
                self._log(f"跳過 {key} (已完成)")
                self._update_stats(skipped_months=1)
                continue
            coro = self._bounded_month_task(
                symbol,
                y,
                m,
                f,
                t,
                use_llm,
                delay,
                max_articles_per_month,
                output_dir_name,
            )
            tasks.append(asyncio.create_task(coro))

        results: List[Dict] = []
        idx = 0
        for task in asyncio.as_completed(tasks):
            idx += 1
            res = await task
            results.append(res)
            if res["success"]:
                self._update_stats(successful_months=1)
                completed_months.add(res["month"])
            else:
                self._update_stats(failed_months=1)
            self._save_progress(list(completed_months))
            success_rate = (
                self.stats["successful_months"]
                / max(1, self.stats["successful_months"] + self.stats["failed_months"])
                * 100
            )
            self._log(f"進度 {idx}/{self.stats['total_months']}，成功率 {success_rate:.1f}%")

        return self._final_report(symbol, start_date, end_date, results)

    # ----------------------------------------
    # 報告
    # ----------------------------------------
    def _final_report(self, symbol: str, start_date: str, end_date: str, results: List[Dict]):
        total_months_done = self.stats["successful_months"] + self.stats["failed_months"]
        month_rate = (
            self.stats["successful_months"] / max(1, total_months_done) * 100
        )
        article_rate = (
            self.stats["successful_articles"] / max(1, self.stats["total_articles"]) * 100
        )
        report = {
            "symbol": symbol,
            "date_range": f"{start_date}~{end_date}",
            "summary_time": datetime.now().isoformat(),
            "month_stats": {
                **{k: self.stats[k] for k in [
                    "total_months",
                    "successful_months",
                    "failed_months",
                    "skipped_months",
                ]},
                "success_rate": f"{month_rate:.2f}%",
            },
            "article_stats": {
                "total_articles": self.stats["total_articles"],
                "successful_articles": self.stats["successful_articles"],
                "failed_articles": self.stats["failed_articles"],
                "success_rate": f"{article_rate:.2f}%",
            },
            "output": str(self.output_base_dir),
            "details": results,
        }
        rpt_file = self.output_base_dir / f"report_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        rpt_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        self._log("=" * 60)
        self._log(f"批量下載完成，報告存於 {rpt_file}")
        self._log("=" * 60)
        return report


# --------------------------------------------
# CLI 區段
# --------------------------------------------

def _parse_args():
    p = argparse.ArgumentParser(description="批量新聞下載器 - Crawl4AI")
    p.add_argument("--symbol", required=True, help="公司股票代碼，如 AAPL")
    p.add_argument("--from-date", required=True, help="開始日期 YYYY-MM-DD")
    p.add_argument("--to-date", required=True, help="結束日期 YYYY-MM-DD")

    p.add_argument("--api-key", help="Finnhub API Key，預設讀取環境變數 FINNHUB_API_KEY")
    p.add_argument("--output-dir", default="batch_news_data", help="輸出資料夾")
    p.add_argument("--use-llm", action="store_true", help="額外使用 LLM 萃取")
    p.add_argument("--delay", type=float, default=0.5, help="API 呼叫間隔秒數")
    p.add_argument("--max-articles-per-month", type=int, help="單月最多文章數")

    p.add_argument(
        "--max-concurrent-months", type=int, default=3, help="同時並行下載月份數")
    p.add_argument(
        "--max-concurrent-articles", type=int, default=5, help="單月內並行文章數")

    p.add_argument("--no-resume", action="store_true", help="忽略先前進度")
    return p.parse_args()


async def _main():
    args = _parse_args()

    if not validate_date_format(args.from_date) or not validate_date_format(args.to_date):
        print("❌ 日期格式錯誤，請使用 YYYY-MM-DD")
        return

    start_dt = datetime.strptime(args.from_date, "%Y-%m-%d")
    end_dt = datetime.strptime(args.to_date, "%Y-%m-%d")
    if start_dt > end_dt:
        print("❌ 開始日期不能晚於結束日期")
        return

    api_key = args.api_key or get_api_key()
    if not api_key or api_key == "YOUR_FINNHUB_API_KEY":
        print("❌ 請設定有效的 Finnhub API Key (FINNHUB_API_KEY)")
        return

    print("🚀 開始批量下載：", args.symbol)
    downloader = BatchNewsDownloader(
        api_key=api_key,
        output_base_dir=args.output_dir,
        max_concurrent=args.max_concurrent_months,
        max_concurrent_articles=args.max_concurrent_articles,
    )

    try:
        await downloader.batch_download(
            symbol=args.symbol,
            start_date=args.from_date,
            end_date=args.to_date,
            use_llm=args.use_llm,
            delay=args.delay,
            max_articles_per_month=args.max_articles_per_month,
            resume=not args.no_resume,
        )
    except KeyboardInterrupt:
        print("⏹️ 中斷輸出，已保存進度，可下次恢復")


if __name__ == "__main__":
    asyncio.run(_main())
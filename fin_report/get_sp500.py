import requests, pandas as pd, json, re

URL = "https://www.slickcharts.com/sp500"
HEADERS = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
}
OUTPUT = "sp500.json"

def fetch_sp500_codes() -> list[str]:
    # 1️⃣ 先用 requests 帶 UA 取 HTML
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    html = resp.text

    # 2️⃣ 用 pandas 解析第一張表
    df = pd.read_html(html)[0]        # Slickcharts 只有一張表
    if "Symbol" not in df.columns:
        raise RuntimeError("找不到 Symbol 欄位，Slickcharts layout 可能變了")

    codes = []
    seen = set()
    for s in df["Symbol"]:
        s = str(s).strip().upper()
        if re.fullmatch(r"[A-Z0-9\.-]{1,7}", s) and s not in seen:
            codes.append(s)
            seen.add(s)
    return codes      # 應該 = 503

def main():
    tickers = fetch_sp500_codes()
    print(f"抓到 {len(tickers)} 檔 S&P 500 成分股")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(tickers, f, indent=2)
    print(f"已輸出到 {OUTPUT}")

if __name__ == "__main__":
    main()

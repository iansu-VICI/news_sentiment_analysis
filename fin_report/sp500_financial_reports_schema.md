# SP500 Financial Reports 數據結構 Schema (增強版)

> **🆕 增強版特點**: 包含同行公司完整財務數據，按公司分組的目錄結構

## 📁 目錄結構概覽

```
sp500_financial_reports/
├── AAPL/                     # Apple Inc 及其同行公司數據
│   ├── company_profiles/     # 公司基本資料 (AAPL + 同行公司)
│   ├── basic_financials/     # 基本財務數據 (AAPL + 同行公司)
│   ├── earnings/            # 財報發布日程 (AAPL + 同行公司)
│   ├── peers/               # AAPL 的同行公司列表
│   └── raw_data/            # AAPL 的完整原始數據
├── MSFT/                    # Microsoft Corp 及其同行公司數據
│   ├── company_profiles/     # 公司基本資料 (MSFT + 同行公司)
│   ├── basic_financials/     # 基本財務數據 (MSFT + 同行公司)
│   ├── earnings/            # 財報發布日程 (MSFT + 同行公司)
│   ├── peers/               # MSFT 的同行公司列表
│   └── raw_data/            # MSFT 的完整原始數據
├── ... (每個 SP500 股票都有獨立資料夾)
├── sp500_companies_summary.csv # CSV 格式摘要
└── scrape_summary.json     # 抓取結果摘要
```

### 資料夾結構特點

每個 SP500 公司都有一個以其股票代碼命名的獨立資料夾，包含：
- **主公司數據**: 該 SP500 公司的完整財務數據
- **同行公司數據**: 最多 5 個同行公司的完整財務數據
- **統一管理**: 相關公司的數據集中在同一個資料夾中，便於比較分析

---

## 📊 各數據類型詳細 Schema

### 1. 公司基本資料 (company_profiles/)

**文件命名**: 
- `{SP500_SYMBOL}_profile.json` - SP500 主公司資料
- `{PEER_SYMBOL}_profile.json` - 同行公司資料

```json
{
  "symbol": "string",           // 股票代碼 (例: "AAPL", "MSFT")
  "name": "string",            // 公司全名 (例: "Apple Inc", "Microsoft Corporation")
  "country": "string",         // 註冊國家代碼 (例: "US", "CA", "CN")
  "currency": "string",        // 交易貨幣 (例: "USD", "CAD")
  "exchange": "string",        // 交易所名稱 (例: "NASDAQ NMS - GLOBAL MARKET", "NYSE")
  "industry": "string",        // 行業分類 (例: "Technology", "Healthcare", "Financial Services")
  "market_cap": "number",      // 市值 (百萬美元)
  "share_outstanding": "number", // 流通股數 (百萬股)
  "logo": "string",           // 公司 Logo URL
  "weburl": "string",         // 公司官網 URL
  "phone": "string",          // 公司電話號碼
  "ipo": "string",            // IPO 日期 (YYYY-MM-DD)
  "timestamp": "string"       // 數據抓取時間戳 (ISO 8601)
}
```

**包含數據**:
- **SP500 主要股票**: 所有 506 個 SP500 成分股的公司資料
- **同行公司**: 每個 SP500 股票的前 5 個同行公司資料
- **總計**: 約 3,000+ 個公司的完整財務資料
- **分散存放**: 每個 SP500 公司資料夾包含該公司及其同行的資料

**行業分布** (主要類別):
- Technology: 軟體、硬體、半導體公司
- Healthcare: 製藥、生技、醫療設備公司
- Financial Services: 銀行、保險、投資公司
- Consumer Cyclical: 零售、汽車、媒體公司
- Communication Services: 電信、網路服務公司
- Industrial: 製造業、航空、運輸公司
- Consumer Defensive: 食品、飲料、日用品公司
- Energy: 石油、天然氣、再生能源公司
- Utilities: 電力、水務、公用事業公司
- Real Estate: 房地產投資信託 (REITs)
- Materials: 化學、金屬、建材公司

---

### 2. 基本財務數據 (basic_financials/)

**文件命名**: 
- `{SP500_SYMBOL}_financials.json` - SP500 主公司財務數據
- `{PEER_SYMBOL}_financials.json` - 同行公司財務數據

```json
{
  "symbol": "string",          // SP500 股票代碼
  "metric_type": "string",     // 指標類型 ("all")
  "data": {
    "metric": {
      // === 市場表現指標 ===
      "10DayAverageTradingVolume": "number",    // 10日平均交易量 (百萬股)
      "3MonthAverageTradingVolume": "number",   // 3個月平均交易量 (百萬股)
      "52WeekHigh": "number",                   // 52週最高價 (美元)
      "52WeekHighDate": "string",               // 52週最高價日期 (YYYY-MM-DD)
      "52WeekLow": "number",                    // 52週最低價 (美元)
      "52WeekLowDate": "string",                // 52週最低價日期 (YYYY-MM-DD)
      "52WeekPriceReturnDaily": "number",       // 52週價格回報率 (%)
      "26WeekPriceReturnDaily": "number",       // 26週價格回報率 (%)
      "13WeekPriceReturnDaily": "number",       // 13週價格回報率 (%)
      "5DayPriceReturnDaily": "number",         // 5日價格回報率 (%)
      "yearToDatePriceReturnDaily": "number",   // 年初至今價格回報率 (%)
      "3MonthADReturnStd": "number",            // 3個月調整後回報標準差
      "beta": "number",                         // Beta 係數 (市場風險指標)
      
      // === SP500 特有估值指標 ===
      "marketCapitalization": "number",         // 市值 (百萬美元)
      "enterpriseValue": "number",              // 企業價值 (百萬美元)
      "peBasicExclExtraTTM": "number",         // 本益比 (TTM, 不含特殊項目)
      "peTTM": "number",                       // 本益比 (TTM)
      "pbAnnual": "number",                    // 股價淨值比 (年度)
      "pbQuarterly": "number",                 // 股價淨值比 (季度)
      "psAnnual": "number",                    // 股價營收比 (年度)
      "psTTM": "number",                       // 股價營收比 (TTM)
      "ptbvAnnual": "number",                  // 股價有形淨值比 (年度)
      "ptbvQuarterly": "number",               // 股價有形淨值比 (季度)
      
      // === 大型股特有每股指標 ===
      "epsAnnual": "number",                   // 每股盈餘 (年度)
      "epsBasicExclExtraItemsAnnual": "number", // 基本每股盈餘 (年度, 不含特殊項目)
      "epsBasicExclExtraItemsTTM": "number",   // 基本每股盈餘 (TTM, 不含特殊項目)
      "epsExclExtraItemsAnnual": "number",     // 每股盈餘 (年度, 不含特殊項目)
      "epsExclExtraItemsTTM": "number",        // 每股盈餘 (TTM, 不含特殊項目)
      "epsNormalizedAnnual": "number",         // 標準化每股盈餘 (年度)
      "bookValuePerShareAnnual": "number",     // 每股淨值 (年度)
      "bookValuePerShareQuarterly": "number",  // 每股淨值 (季度)
      "tangibleBookValuePerShareAnnual": "number", // 每股有形淨值 (年度)
      "tangibleBookValuePerShareQuarterly": "number", // 每股有形淨值 (季度)
      "cashFlowPerShareAnnual": "number",      // 每股現金流 (年度)
      "cashFlowPerShareQuarterly": "number",   // 每股現金流 (季度)
      "cashFlowPerShareTTM": "number",         // 每股現金流 (TTM)
      "cashPerSharePerShareAnnual": "number",  // 每股現金 (年度)
      "cashPerSharePerShareQuarterly": "number", // 每股現金 (季度)
      "revenuePerShareAnnual": "number",       // 每股營收 (年度)
      "revenuePerShareTTM": "number",          // 每股營收 (TTM)
      
      // === 大型股成長率指標 ===
      "epsGrowth3Y": "number",                 // 每股盈餘 3年成長率 (%)
      "epsGrowth5Y": "number",                 // 每股盈餘 5年成長率 (%)
      "epsGrowthQuarterlyYoy": "number",       // 每股盈餘季度年增率 (%)
      "epsGrowthTTMYoy": "number",             // 每股盈餘 TTM 年增率 (%)
      "revenueGrowth3Y": "number",             // 營收 3年成長率 (%)
      "revenueGrowth5Y": "number",             // 營收 5年成長率 (%)
      "revenueGrowthQuarterlyYoy": "number",   // 營收季度年增率 (%)
      "revenueGrowthTTMYoy": "number",         // 營收 TTM 年增率 (%)
      "bookValueShareGrowth5Y": "number",      // 每股淨值 5年成長率 (%)
      "capexCagr5Y": "number",                 // 資本支出 5年複合成長率 (%)
      "ebitdaCagr5Y": "number",                // EBITDA 5年複合成長率 (%)
      "ebitdaInterimCagr5Y": "number",         // EBITDA 中期 5年複合成長率 (%)
      
      // === 獲利能力指標 ===
      "ebitdPerShareAnnual": "number",         // 每股 EBITDA (年度)
      "ebitdPerShareTTM": "number",            // 每股 EBITDA (TTM)
      "ebitdaMargin5Y": "number",              // EBITDA 利潤率 5年平均 (%)
      "ebitdaMarginAnnual": "number",          // EBITDA 利潤率 (年度, %)
      "ebitdaMarginTTM": "number",             // EBITDA 利潤率 (TTM, %)
      "grossMargin5Y": "number",               // 毛利率 5年平均 (%)
      "grossMarginAnnual": "number",           // 毛利率 (年度, %)
      "grossMarginTTM": "number",              // 毛利率 (TTM, %)
      "netIncomeEmployeeAnnual": "number",     // 每員工淨利 (年度)
      "netIncomeEmployeeTTM": "number",        // 每員工淨利 (TTM)
      "netMargin5Y": "number",                 // 淨利率 5年平均 (%)
      "netMarginAnnual": "number",             // 淨利率 (年度, %)
      "netMarginTTM": "number",                // 淨利率 (TTM, %)
      "operatingMargin5Y": "number",           // 營業利潤率 5年平均 (%)
      "operatingMarginAnnual": "number",       // 營業利潤率 (年度, %)
      "operatingMarginTTM": "number",          // 營業利潤率 (TTM, %)
      "pretaxMargin5Y": "number",              // 稅前利潤率 5年平均 (%)
      "pretaxMarginAnnual": "number",          // 稅前利潤率 (年度, %)
      "pretaxMarginTTM": "number",             // 稅前利潤率 (TTM, %)
      
      // === 回報率指標 ===
      "roaRfy": "number",                      // 資產回報率 (RFY, %)
      "roaTTM": "number",                      // 資產回報率 (TTM, %)
      "roaa5Y": "number",                      // 平均資產回報率 5年 (%)
      "roae5Y": "number",                      // 平均股東權益回報率 5年 (%)
      "roaeTTM": "number",                     // 股東權益回報率 (TTM, %)
      "roeRfy": "number",                      // 股東權益回報率 (RFY, %)
      "roeTTM": "number",                      // 股東權益回報率 (TTM, %)
      "roi5Y": "number",                       // 投資回報率 5年平均 (%)
      "roiAnnual": "number",                   // 投資回報率 (年度, %)
      "roiTTM": "number",                      // 投資回報率 (TTM, %)
      
      // === 營運效率指標 ===
      "assetTurnoverAnnual": "number",         // 資產周轉率 (年度)
      "assetTurnoverTTM": "number",            // 資產周轉率 (TTM)
      "inventoryTurnoverAnnual": "number",     // 存貨周轉率 (年度)
      "inventoryTurnoverTTM": "number",        // 存貨周轉率 (TTM)
      "paymentTurnoverAnnual": "number",       // 應付款項周轉率 (年度)
      "paymentTurnoverTTM": "number",          // 應付款項周轉率 (TTM)
      "receivablesTurnoverAnnual": "number",   // 應收款項周轉率 (年度)
      "receivablesTurnoverTTM": "number",      // 應收款項周轉率 (TTM)
      "revenueEmployeeAnnual": "number",       // 每員工營收 (年度)
      "revenueEmployeeTTM": "number",          // 每員工營收 (TTM)
      
      // === 財務健康指標 ===
      "currentRatioAnnual": "number",          // 流動比率 (年度)
      "currentRatioQuarterly": "number",       // 流動比率 (季度)
      "quickRatioAnnual": "number",            // 速動比率 (年度)
      "quickRatioQuarterly": "number",         // 速動比率 (季度)
      "longTermDebt/equityAnnual": "number",   // 長期負債權益比 (年度)
      "longTermDebt/equityQuarterly": "number", // 長期負債權益比 (季度)
      "totalDebt/totalEquityAnnual": "number", // 總負債權益比 (年度)
      "totalDebt/totalEquityQuarterly": "number", // 總負債權益比 (季度)
      
      // === 股息指標 (SP500 成熟公司特有) ===
      "currentDividendYieldTTM": "number|null", // 當前股息殖利率 (TTM, %)
      "dividendGrowthRate5Y": "number|null",   // 股息成長率 5年 (%)
      "dividendPerShare2Y": "number|null",     // 每股股息 2年
      "dividendPerShareAnnual": "number|null", // 每股股息 (年度)
      "dividendPerShareTTM": "number|null",    // 每股股息 (TTM)
      "dividendYield5Y": "number|null",        // 股息殖利率 5年平均 (%)
      "dividendYieldIndicatedAnnual": "number|null", // 預期年股息殖利率 (%)
      
      // === 現金流指標 ===
      "currentEv/freeCashFlowAnnual": "number", // 當前企業價值/自由現金流 (年度)
      "currentEv/freeCashFlowTTM": "number",   // 當前企業價值/自由現金流 (TTM)
      "freeCashFlowLTMGrowth": "number",       // 自由現金流 LTM 成長率 (%)
      "freeCashFlowAnnual": "number",          // 自由現金流 (年度)
      "freeCashFlowPerShareTTM": "number",     // 每股自由現金流 (TTM)
      "freeCashFlowTTM": "number",             // 自由現金流 (TTM)
      
      // === 其他指標 ===
      "totalDebtCagr5Y": "number"              // 總負債 5年複合成長率 (%)
    },
    "series": {
      "annual": {
        // 年度時間序列數據 (1985-2025, 40年歷史)
        "bookValue": [                         // 淨值
          {
            "period": "YYYY-MM-DD",            // 財報期間
            "v": "number"                      // 數值
          }
        ],
        "cashRatio": [...],                    // 現金比率
        "currentRatio": [...],                 // 流動比率
        "ebitPerShare": [...],                 // 每股 EBIT
        "eps": [...],                          // 每股盈餘
        "ev": [...],                           // 企業價值
        "fcfMargin": [...],                    // 自由現金流利潤率
        "fcfPerShareTTM": [...],               // 每股自由現金流 TTM
        "freeCashFlowPerShare": [...],         // 每股自由現金流
        "grossMargin": [...],                  // 毛利率
        "inventoryTurnoverTTM": [...],         // 存貨周轉率 TTM
        "longtermDebtTotalCapital": [...],     // 長期負債佔總資本比
        "netDebtToTotalCapital": [...],        // 淨負債佔總資本比
        "netMargin": [...],                    // 淨利率
        "operatingMargin": [...],              // 營業利潤率
        "payoutRatioTTM": [...],               // 股息支付率 TTM
        "pb": [...],                           // 股價淨值比
        "pretaxMargin": [...],                 // 稅前利潤率
        "ps": [...],                           // 股價營收比
        "ptbv": [...],                         // 股價有形淨值比
        "quickRatio": [...],                   // 速動比率
        "receivablesTurnoverTTM": [...],       // 應收款項周轉率 TTM
        "roa": [...],                          // 資產回報率
        "roe": [...],                          // 股東權益回報率
        "salesPerShare": [...],                // 每股營收
        "tangibleBookValuePerShare": [...],    // 每股有形淨值
        "totalDebtToEquity": [...],            // 總負債權益比
        "totalDebtToTotalAsset": [...],        // 總負債佔總資產比
        "totalDebtToTotalCapital": [...]       // 總負債佔總資本比
      },
      "quarterly": {
        // 季度時間序列數據 (最近10年季度數據)
        // 結構同 annual，但時間間隔為季度
      }
    }
  },
  "timestamp": "string"                        // 數據抓取時間戳
}
```

**SP500 特有指標說明**:

#### 大型股估值指標
- **市值範圍**: 通常 > 10億美元，多數 > 100億美元
- **流動性**: 高交易量，低買賣價差
- **機構持股**: 高機構投資者持股比例

#### 成熟公司特徵
- **股息政策**: 多數公司有穩定股息政策
- **財務穩定**: 較低的財務槓桿，穩定現金流
- **長期數據**: 完整的 40年歷史財務數據

---

### 3. 財報發布日程 (earnings/)

**文件命名**: 
- `{SP500_SYMBOL}_earnings.json` - SP500 主公司財報日程
- `{PEER_SYMBOL}_earnings.json` - 同行公司財報日程

```json
{
  "symbol": "string",          // SP500 股票代碼
  "from_date": "string",      // 查詢開始日期 (過去90天)
  "to_date": "string",        // 查詢結束日期 (未來90天)
  "data": {
    "earningsCalendar": [
      {
        "date": "string",           // 財報發布日期 (YYYY-MM-DD)
        "epsActual": "number|null", // 實際每股盈餘 (發布後才有)
        "epsEstimate": "number",    // 預期每股盈餘 (分析師預測)
        "hour": "string",           // 發布時間 ("amc"=盤後, "bmo"=盤前)
        "quarter": "number",        // 財報季度 (1-4)
        "revenueActual": "number|null", // 實際營收 (百萬美元, 發布後才有)
        "revenueEstimate": "number",    // 預期營收 (百萬美元, 分析師預測)
        "symbol": "string",         // 股票代碼
        "year": "number"            // 財報年度
      }
    ]
  },
  "timestamp": "string"         // 數據抓取時間戳
}
```

**SP500 財報特點**:
- **高關注度**: 市場高度關注，媒體廣泛報導
- **分析師覆蓋**: 多位分析師追蹤，預測相對準確
- **即時影響**: 業績公布對股價有顯著短期影響
- **季度規律**: 嚴格按季度發布，時間可預測

---

### 4. 同行公司列表 (peers/)

**文件命名**: `{SP500_SYMBOL}_peers.json` - 僅 SP500 主公司的同行列表

```json
{
  "symbol": "string",          // SP500 主股票代碼
  "peers": ["string"],        // 同行公司股票代碼列表 (最多10個)
  "peers_count": "number",    // 同行公司數量
  "timestamp": "string"       // 數據抓取時間戳
}
```

**SP500 同行分析特點**:
- **同業競爭**: 通常包含其他 SP500 成分股
- **全球競爭**: 可能包含國際大型競爭對手
- **行業領導者**: 多為各行業的頭部公司
- **可比性高**: 規模和業務模式相近

**常見同行關係**:
- **科技股**: AAPL, MSFT, GOOGL, META 互為同行
- **金融股**: JPM, BAC, WFC, C 等大型銀行
- **醫藥股**: JNJ, PFE, MRK, ABBV 等製藥巨頭
- **消費股**: PG, KO, PEP, WMT 等消費品牌

---

### 5. 完整原始數據 (raw_data/)

**文件命名**: `{SP500_SYMBOL}_complete.json` - 僅 SP500 主公司的完整原始數據

```json
{
  "symbol": "string",              // SP500 股票代碼
  "scrape_timestamp": "string",    // 抓取時間戳
  "profile": {                     // 公司基本資料
    // ... 完整的 profile 數據
  },
  "basic_financials": {            // 基本財務數據
    // ... 完整的 financials 數據
  },
  "earnings": {                    // 財報日程
    // ... 完整的 earnings 數據
  },
  "peers": {                       // 同行公司列表
    // ... 完整的 peers 數據
  },
  "peers_data": {                  // 同行公司完整數據
    "PEER1": {                     // 同行公司1的完整財務數據
      "profile": {                 // 基本資料
        // ... profile 數據
      },
      "basic_financials": {        // 財務數據
        // ... financials 數據
      },
      "earnings": {                // 財報日程
        // ... earnings 數據
      }
    },
    "PEER2": {                     // 同行公司2的完整財務數據
      // ... 同樣結構
    }
    // ... 最多5個同行公司
  },
  "success": "boolean",            // 抓取是否成功
  "error": "string|undefined"      // 錯誤信息 (如果有)
}
```

**數據完整性**:
- **主要數據**: SP500 股票的完整財務數據
- **同行數據**: 每個股票最多5個同行的完整財務數據（包含 basic_financials, earnings）
- **數據量**: 每個 SP500 公司資料夾約 10-50MB（包含同行數據）
- **檔案分布**: 每個公司資料夾包含 15-25 個 JSON 檔案

---

### 6. CSV 格式摘要 (sp500_companies_summary.csv)

```csv
Symbol,Success,Company_Name,Industry,Country,Market_Cap,Peers_Count,Peers_Data_Count,Has_Profile,Has_Financials,Has_Earnings,Has_Peers,Error
AAPL,True,Apple Inc,Technology,US,2916518.840395,10,4,True,True,True,True,
MSFT,True,Microsoft Corporation,Technology,US,2845123.456789,8,5,True,True,True,True,
GOOGL,True,Alphabet Inc,Communication Services,US,1654321.123456,9,4,True,True,True,True,
AMZN,True,Amazon.com Inc,Consumer Cyclical,US,1543210.987654,7,5,True,True,True,True,
...
```

**欄位說明**:
- `Symbol`: SP500 股票代碼
- `Success`: 該股票數據抓取是否成功
- `Company_Name`: 公司全名
- `Industry`: 行業分類 (11個主要 GICS 行業)
- `Country`: 註冊國家 (主要為 US)
- `Market_Cap`: 市值 (百萬美元)
- `Peers_Count`: 找到的同行公司數量
- `Peers_Data_Count`: 成功獲取完整財務數據的同行公司數量
- `Has_Profile`: 是否成功獲取公司基本資料
- `Has_Financials`: 是否成功獲取財務數據
- `Has_Earnings`: 是否成功獲取財報日程
- `Has_Peers`: 是否成功獲取同行列表
- `Error`: 錯誤信息 (如果有)

**統計預期**:
- **總行數**: 506 行 (SP500 成分股)
- **成功率**: 預期 > 95%
- **平均市值**: 約 200-300 億美元
- **同行數量**: 平均 8-10 個同行公司

---

### 7. 抓取結果摘要 (scrape_summary.json)

```json
{
  "scrape_timestamp": "string",    // 完整抓取完成時間戳
  "total_companies": 506,          // SP500 成分股總數
  "successful": "number",          // 成功抓取的公司數量
  "failed": "number",             // 失敗的公司數量
  "success_rate": "string",       // 成功率百分比 (例: "96.8%")
  "companies": ["string"],        // 所有 SP500 股票代碼列表
  "include_peers": true,          // 是否包含同行公司數據
  "results": [                    // 每個公司的詳細結果
    {
      "symbol": "string",         // SP500 股票代碼
      "scrape_timestamp": "string", // 該股票抓取時間戳
      "profile": "object|null",   // 公司資料抓取結果
      "basic_financials": "object|null", // 財務數據抓取結果
      "earnings": "object|null",  // 財報日程抓取結果
      "peers": "object|null",     // 同行列表抓取結果
      "peers_data": "object",     // 同行公司資料 (字典格式)
      "success": "boolean",       // 該公司抓取是否成功
      "error": "string|undefined" // 錯誤信息 (如果有)
    }
  ]
}
```

**抓取統計預期**:
- **執行時間**: 約 4-8 小時 (取決於網路速度，包含同行數據)
- **API 請求數**: 約 8,000-12,000 次 (包含同行公司請求)
- **數據量**: 約 5-15 GB (包含同行完整財務數據)
- **文件數量**: 約 15,000+ 個 JSON 文件
- **資料夾數量**: 506 個 SP500 公司資料夾

---

## 🏢 SP500 行業分析指南

### 行業分類 (GICS Sectors)

1. **Information Technology (約 28%)**
   - 軟體公司: MSFT, ORCL, CRM, ADBE
   - 硬體公司: AAPL, DELL, HPQ
   - 半導體: NVDA, INTC, AMD, QCOM

2. **Healthcare (約 13%)**
   - 製藥: JNJ, PFE, MRK, ABBV
   - 生技: GILD, BIIB, AMGN
   - 醫療設備: ABT, MDT, SYK

3. **Financial Services (約 12%)**
   - 銀行: JPM, BAC, WFC, C
   - 保險: BRK.B, AIG, AFL
   - 投資服務: GS, MS, SPGI

4. **Communication Services (約 9%)**
   - 網路服務: GOOGL, META, NFLX
   - 電信: VZ, T, TMUS
   - 媒體: DIS, CMCSA

5. **Consumer Discretionary (約 11%)**
   - 電商: AMZN
   - 汽車: TSLA, F, GM
   - 零售: HD, MCD, SBUX

6. **Industrials (約 8%)**
   - 航空: BA, LMT, RTX
   - 運輸: UPS, FDX
   - 製造: CAT, DE, MMM

7. **Consumer Staples (約 6%)**
   - 食品飲料: KO, PEP, PG
   - 零售: WMT, COST
   - 菸草: PM, MO

8. **Energy (約 4%)**
   - 石油: XOM, CVX, COP
   - 天然氣: EOG, SLB
   - 再生能源: 相關 ETF

9. **Utilities (約 3%)**
   - 電力: NEE, SO, D
   - 天然氣: AEP, EXC

10. **Real Estate (約 3%)**
    - REITs: AMT, CCI, EQIX
    - 地產開發: 相關公司

11. **Materials (約 3%)**
    - 化學: LIN, DD, DOW
    - 金屬: NUE, FCX
    - 建材: SHW, PPG

---

## 🔍 SP500 數據使用指南

### 投資分析應用

1. **指數投資分析**
   - 使用完整 SP500 數據構建指數模型
   - 分析各行業權重和貢獻度
   - 追蹤指數成分股變化

2. **同行比較分析** ⭐ **新功能**
   - 在單一資料夾中比較主公司與同行
   - 分析相對估值和財務指標
   - 識別行業內的投資機會
   - 評估競爭優勢和市場地位

3. **行業輪動策略**
   - 比較 11 個 GICS 行業的表現
   - 分析行業間的相關性
   - 識別行業輪動機會
   - 利用同行數據驗證行業趨勢

4. **大型股價值投資**
   - 篩選低估值、高股息的成熟公司
   - 分析財務穩定性和現金流
   - 比較同行業公司的相對估值
   - 使用同行數據進行相對價值分析

5. **成長股分析**
   - 識別高成長率的科技和醫療股
   - 分析營收和盈利成長趨勢
   - 評估成長的可持續性
   - 與同行公司成長率比較

6. **ESG 投資**
   - 結合 ESG 評級數據
   - 篩選可持續發展的大型股
   - 構建責任投資組合
   - 比較同行業 ESG 表現

### 數據品質特點

- **覆蓋範圍**: 美國最大 500 家上市公司
- **數據完整性**: 高品質，機構級數據
- **歷史深度**: 40年歷史財務數據
- **更新頻率**: 實時市場數據，季度財務數據
- **國際性**: 包含跨國公司和外國公司

### 技術分析支持

- **市場指標**: 交易量、波動率、技術指標
- **相對強弱**: 個股相對於 SP500 指數表現
- **行業比較**: 同行業公司的相對表現
- **資金流向**: 機構投資者持股變化

### 注意事項

1. **市值偏向**: 數據偏向大型股，可能不代表整體市場
2. **美國市場**: 主要反映美國經濟，國際多元化有限
3. **行業集中**: 科技股權重較高，需注意行業風險
4. **數據延遲**: 財務數據有季度延遲，需結合實時數據分析
5. **同行數據品質**: 部分同行公司可能為國際股票，數據完整性可能不同
6. **儲存需求**: 包含同行數據後，總數據量顯著增加，需確保足夠儲存空間

### 🆕 增強版特有功能

#### 同行比較分析範例

```python
# 範例：比較 Apple 與同行的財務指標
import json
from pathlib import Path

def compare_peers_financials(company_symbol):
    """比較主公司與同行的財務指標"""
    company_dir = Path(f"sp500_financial_reports/{company_symbol}")
    
    # 讀取所有財務數據
    financials_dir = company_dir / "basic_financials"
    companies_data = {}
    
    for file in financials_dir.glob("*_financials.json"):
        with open(file) as f:
            data = json.load(f)
            symbol = data['symbol']
            metrics = data['data']['metric']
            
            companies_data[symbol] = {
                'pe_ratio': metrics.get('peTTM'),
                'market_cap': metrics.get('marketCapitalization'),
                'roe': metrics.get('roeTTM'),
                'gross_margin': metrics.get('grossMarginTTM')
            }
    
    # 顯示比較結果
    print(f"\n{company_symbol} 與同行財務指標比較:")
    print("-" * 60)
    print(f"{'公司':<8} {'P/E比率':<10} {'市值(M)':<12} {'ROE(%)':<8} {'毛利率(%)':<10}")
    print("-" * 60)
    
    for symbol, data in companies_data.items():
        pe = f"{data['pe_ratio']:.2f}" if data['pe_ratio'] else "N/A"
        cap = f"{data['market_cap']:.0f}" if data['market_cap'] else "N/A"
        roe = f"{data['roe']:.2f}" if data['roe'] else "N/A"
        margin = f"{data['gross_margin']:.2f}" if data['gross_margin'] else "N/A"
        
        marker = "📍" if symbol == company_symbol else "  "
        print(f"{marker}{symbol:<8} {pe:<10} {cap:<12} {roe:<8} {margin:<10}")

# 使用範例
compare_peers_financials("AAPL")
```

#### 行業分析範例

```python
def analyze_industry_trends():
    """分析各行業的財務趨勢"""
    sp500_dir = Path("sp500_financial_reports")
    industry_data = {}
    
    for company_dir in sp500_dir.iterdir():
        if company_dir.is_dir() and company_dir.name not in ['scrape_summary.json', 'sp500_companies_summary.csv']:
            # 讀取主公司資料
            profile_file = company_dir / "company_profiles" / f"{company_dir.name}_profile.json"
            financials_file = company_dir / "basic_financials" / f"{company_dir.name}_financials.json"
            
            if profile_file.exists() and financials_file.exists():
                with open(profile_file) as f:
                    profile = json.load(f)
                with open(financials_file) as f:
                    financials = json.load(f)
                
                industry = profile.get('industry', 'Unknown')
                pe_ratio = financials['data']['metric'].get('peTTM')
                
                if industry not in industry_data:
                    industry_data[industry] = []
                
                if pe_ratio:
                    industry_data[industry].append(pe_ratio)
    
    # 計算各行業平均 P/E 比率
    print("\n各行業平均 P/E 比率:")
    print("-" * 40)
    for industry, pe_ratios in industry_data.items():
        if pe_ratios:
            avg_pe = sum(pe_ratios) / len(pe_ratios)
            print(f"{industry:<30} {avg_pe:.2f}")

# 使用範例
analyze_industry_trends()
``` 
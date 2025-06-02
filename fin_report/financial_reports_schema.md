# Financial Reports 數據結構 Schema

## 📁 目錄結構概覽

```
financial_reports/
├── company_profiles/      # 公司基本資料
├── basic_financials/      # 基本財務數據
├── metrics/              # 公司關鍵指標
├── earnings/             # 財報發布日程
├── raw_data/            # 完整原始數據
├── companies_summary.csv # CSV 格式摘要
└── scrape_summary.json  # 抓取結果摘要
```

---

## 📊 各數據類型詳細 Schema

### 1. 公司基本資料 (company_profiles/)

**文件命名**: `{SYMBOL}_profile.json`

```json
{
  "symbol": "string",           // 股票代碼 (例: "ADBE")
  "name": "string",            // 公司全名 (例: "Adobe Inc")
  "country": "string",         // 註冊國家代碼 (例: "US", "JP", "KR")
  "currency": "string",        // 交易貨幣 (例: "USD", "KRW")
  "exchange": "string",        // 交易所名稱 (例: "NASDAQ NMS - GLOBAL MARKET")
  "industry": "string",        // 行業分類 (例: "Technology", "Semiconductors")
  "market_cap": "number",      // 市值 (百萬美元)
  "share_outstanding": "number", // 流通股數 (百萬股)
  "logo": "string",           // 公司 Logo URL
  "weburl": "string",         // 公司官網 URL
  "phone": "string",          // 公司電話號碼
  "ipo": "string",            // IPO 日期 (YYYY-MM-DD)
  "timestamp": "string"       // 數據抓取時間戳 (ISO 8601)
}
```

**欄位說明**:
- `market_cap`: 市值，單位為百萬美元，用於評估公司規模
- `share_outstanding`: 已發行股票數量，用於計算每股指標
- `industry`: 行業分類，用於同業比較分析
- `exchange`: 交易所信息，影響交易時間和監管要求

---

### 2. 基本財務數據 (basic_financials/)

**文件命名**: `{SYMBOL}_financials.json`

```json
{
  "symbol": "string",          // 股票代碼
  "metric_type": "string",     // 指標類型 ("all", "annual", "quarterly")
  "data": {
    "metric": {
      // === 交易相關指標 ===
      "10DayAverageTradingVolume": "number",    // 10日平均交易量 (百萬股)
      "3MonthAverageTradingVolume": "number",   // 3個月平均交易量 (百萬股)
      "52WeekHigh": "number",                   // 52週最高價
      "52WeekHighDate": "string",               // 52週最高價日期
      "52WeekLow": "number",                    // 52週最低價
      "52WeekLowDate": "string",                // 52週最低價日期
      "52WeekPriceReturnDaily": "number",       // 52週價格回報率 (%)
      "13WeekPriceReturnDaily": "number",       // 13週價格回報率 (%)
      "26WeekPriceReturnDaily": "number",       // 26週價格回報率 (%)
      "5DayPriceReturnDaily": "number",         // 5日價格回報率 (%)
      "3MonthADReturnStd": "number",            // 3個月調整後回報標準差
      "beta": "number",                         // Beta 係數 (市場風險指標)
      
      // === 估值指標 ===
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
      
      // === 每股指標 ===
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
      
      // === 成長率指標 ===
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
      "epsInclExtraItemsAnnual": "number",     // 每股盈餘 (年度, 含特殊項目)
      "epsInclExtraItemsTTM": "number",        // 每股盈餘 (TTM, 含特殊項目)
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
      
      // === 效率指標 ===
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
      
      // === 流動性指標 ===
      "currentRatioAnnual": "number",          // 流動比率 (年度)
      "currentRatioQuarterly": "number",       // 流動比率 (季度)
      "quickRatioAnnual": "number",            // 速動比率 (年度)
      "quickRatioQuarterly": "number",         // 速動比率 (季度)
      
      // === 槓桿指標 ===
      "longTermDebt/equityAnnual": "number",   // 長期負債權益比 (年度)
      "longTermDebt/equityQuarterly": "number", // 長期負債權益比 (季度)
      "totalDebt/totalEquityAnnual": "number", // 總負債權益比 (年度)
      "totalDebt/totalEquityQuarterly": "number", // 總負債權益比 (季度)
      
      // === 股息指標 ===
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
      "totalDebtCagr5Y": "number",             // 總負債 5年複合成長率 (%)
      "yearToDatePriceReturnDaily": "number"   // 年初至今價格回報率 (%)
    },
    "series": {
      "annual": {
        // 年度時間序列數據
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
        // 季度時間序列數據 (結構同 annual)
        // 包含最近幾年的季度數據
      }
    }
  },
  "timestamp": "string"                        // 數據抓取時間戳
}
```

**重要指標說明**:

#### 估值指標
- `peBasicExclExtraTTM`: 本益比，股價相對於每股盈餘的倍數，用於評估股票是否被高估或低估
- `pbAnnual`: 股價淨值比，股價相對於每股淨值的倍數，反映市場對公司資產的評價
- `psAnnual`: 股價營收比，股價相對於每股營收的倍數，適用於評估高成長但暫時虧損的公司

#### 獲利能力指標
- `roeRfy`: 股東權益回報率，衡量公司為股東創造利潤的效率
- `roaRfy`: 資產回報率，衡量公司運用資產創造利潤的效率
- `grossMarginAnnual`: 毛利率，反映公司產品或服務的基本獲利能力
- `netMarginAnnual`: 淨利率，反映公司最終的獲利能力

#### 成長性指標
- `epsGrowth5Y`: 每股盈餘 5年成長率，反映公司長期盈利成長趨勢
- `revenueGrowth5Y`: 營收 5年成長率，反映公司業務擴張能力

#### 財務健康指標
- `currentRatioAnnual`: 流動比率，衡量公司短期償債能力
- `totalDebt/totalEquityAnnual`: 負債權益比，衡量公司財務槓桿程度

---

### 3. 公司關鍵指標 (metrics/)

**文件命名**: `{SYMBOL}_metrics.json`

```json
{
  "symbol": "string",          // 股票代碼
  "date": "string",           // 查詢日期 (YYYY-MM-DD)
  "data": {
    // 結構與 basic_financials 相同
    // 包含相同的 metric 和 series 數據
  },
  "timestamp": "string"       // 數據抓取時間戳
}
```

**說明**: 此數據與 basic_financials 結構相同，提供相同的財務指標和時間序列數據。

---

### 4. 財報發布日程 (earnings/)

**文件命名**: `{SYMBOL}_earnings.json`

```json
{
  "symbol": "string",          // 股票代碼
  "from_date": "string",      // 查詢開始日期 (YYYY-MM-DD)
  "to_date": "string",        // 查詢結束日期 (YYYY-MM-DD)
  "data": {
    "earningsCalendar": [
      {
        "date": "string",           // 財報發布日期 (YYYY-MM-DD)
        "epsActual": "number|null", // 實際每股盈餘 (發布後才有)
        "epsEstimate": "number",    // 預期每股盈餘 (分析師預測)
        "hour": "string",           // 發布時間 ("amc"=盤後, "bmo"=盤前)
        "quarter": "number",        // 財報季度 (1-4)
        "revenueActual": "number|null", // 實際營收 (發布後才有)
        "revenueEstimate": "number",    // 預期營收 (分析師預測)
        "symbol": "string",         // 股票代碼
        "year": "number"            // 財報年度
      }
    ]
  },
  "timestamp": "string"         // 數據抓取時間戳
}
```

**欄位說明**:
- `epsEstimate` vs `epsActual`: 預期與實際每股盈餘的比較，用於評估公司業績是否符合預期
- `revenueEstimate` vs `revenueActual`: 預期與實際營收的比較
- `hour`: 財報發布時間，"amc" (after market close) 表示盤後，"bmo" (before market open) 表示盤前
- `quarter`: 財報季度，Q1-Q4 分別對應 1-4

---

### 5. 完整原始數據 (raw_data/)

**文件命名**: `{SYMBOL}_complete.json`

```json
{
  "symbol": "string",              // 股票代碼
  "scrape_timestamp": "string",    // 抓取時間戳
  "profile": {                     // 公司基本資料 (同 company_profiles)
    // ... 完整的 profile 數據
  },
  "basic_financials": {            // 基本財務數據 (同 basic_financials)
    // ... 完整的 financials 數據
  },
  "metrics": {                     // 公司指標 (同 metrics)
    // ... 完整的 metrics 數據
  },
  "earnings": {                    // 財報日程 (同 earnings)
    // ... 完整的 earnings 數據
  },
  "success": "boolean",            // 抓取是否成功
  "error": "string|undefined"      // 錯誤信息 (如果有)
}
```

**說明**: 包含單一公司的所有數據類型，是其他分類文件的完整集合。

---

### 6. CSV 格式摘要 (companies_summary.csv)

```csv
Symbol,Success,Company_Name,Industry,Country,Market_Cap,Has_Profile,Has_Financials,Has_Metrics,Has_Earnings,Error
ADBE,True,Adobe Inc,Technology,US,173757.4773456572,True,True,True,True,
NVDA,True,NVIDIA Corporation,Semiconductors,US,2916518.7854225663,True,True,True,True,
...
```

**欄位說明**:
- `Symbol`: 股票代碼
- `Success`: 整體抓取是否成功
- `Company_Name`: 公司名稱
- `Industry`: 行業分類
- `Country`: 註冊國家
- `Market_Cap`: 市值 (百萬美元)
- `Has_Profile`: 是否有公司基本資料
- `Has_Financials`: 是否有財務數據
- `Has_Metrics`: 是否有公司指標
- `Has_Earnings`: 是否有財報日程
- `Error`: 錯誤信息 (如果有)

---

### 7. 抓取結果摘要 (scrape_summary.json)

```json
{
  "scrape_timestamp": "string",    // 抓取完成時間戳
  "total_companies": "number",     // 總公司數量
  "successful": "number",          // 成功抓取的公司數量
  "failed": "number",             // 失敗的公司數量
  "success_rate": "string",       // 成功率百分比
  "companies": ["string"],        // 所有公司股票代碼列表
  "results": [                    // 每個公司的詳細結果
    {
      "symbol": "string",         // 股票代碼
      "scrape_timestamp": "string", // 抓取時間戳
      "profile": "object|null",   // 公司資料抓取結果
      "basic_financials": "object|null", // 財務數據抓取結果
      "metrics": "object|null",   // 指標抓取結果
      "earnings": "object|null",  // 財報日程抓取結果
      "success": "boolean",       // 該公司抓取是否成功
      "error": "string|undefined" // 錯誤信息 (如果有)
    }
  ]
}
```

---

## 🔍 數據使用指南

### 投資分析用途

1. **基本面分析**: 使用 `basic_financials` 中的財務比率和成長指標
2. **估值分析**: 重點關注 PE、PB、PS 等估值指標
3. **同業比較**: 利用 `industry` 欄位進行同行業公司比較
4. **趨勢分析**: 使用 `series` 中的時間序列數據分析長期趨勢
5. **財報追蹤**: 使用 `earnings` 數據追蹤財報發布時程

### 數據品質說明

- **時間範圍**: 1985-2025年，約40年歷史數據
- **更新頻率**: 數據抓取時間記錄在 `timestamp` 欄位
- **數據來源**: Finnhub API
- **完整性**: 39家公司，總體完整率 >95%

### 注意事項

1. **空值處理**: 某些指標可能為 `null`，特別是股息相關指標
2. **貨幣單位**: 財務數據主要以百萬美元為單位
3. **時間格式**: 所有日期均為 ISO 8601 格式 (YYYY-MM-DD)
4. **API限制**: 部分國際公司的某些數據可能受 API 權限限制 
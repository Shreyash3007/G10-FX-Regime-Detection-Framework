# config.py
# All configuration lives here. Change settings in one place, affects everything.

# ── DATE RANGE ──────────────────────────────────────────────
START_DATE = "2020-01-01"   # 5 years of history is enough for regime work
# END_DATE will be set dynamically to today in the pipeline

# ── FX TICKERS (Yahoo Finance format) ───────────────────────
FX_TICKERS = {
    "EURUSD": "EURUSD=X",   # Euro vs US Dollar
    "USDJPY": "JPY=X",      # US Dollar vs Japanese Yen
    "DXY":    "DX-Y.NYB",   # Dollar Index (basket of currencies vs USD)
}

# ── YIELD SOURCES ───────────────────────────────────────────
# US yields: FRED (daily)
FRED_SERIES = {
    "US_2Y":  "DGS2",    # US 2-Year Treasury Yield (daily)
    "US_10Y": "DGS10",   # US 10-Year Treasury Yield (daily)
}

# DE yields: ECB Yield Curve data (daily, eurozone government bonds)
# API: https://data-api.ecb.europa.eu/service/data/YC/...
# G_N_A = Government, Nominal, All issuers
# SV_C_YM = Svensson Continuous Yield to Maturity
ECB_SERIES = {
    "DE_2Y":  "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y",
    "DE_10Y": "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y",
}
ECB_BASE_URL = "https://data-api.ecb.europa.eu/service/data"

# JP yields: Ministry of Finance Japan (daily JGB yield curve)
# Historical: https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/historical/jgbcme_all.csv
# Current month: https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv
MOF_HISTORICAL_URL = "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/historical/jgbcme_all.csv"
MOF_CURRENT_URL = "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv"

# ── RATE DIFFERENTIAL PAIRS ──────────────────────────────────
# Format: (series_A, series_B, label)
# Differential = A minus B
# Positive = A pays more than B
DIFFERENTIALS = [
    ("US_2Y",  "DE_10Y", "US_DE_10Y_spread"),  # USD vs EUR driver (cross-maturity)
    ("US_2Y",  "DE_2Y",  "US_DE_2Y_spread"),   # USD vs EUR driver (same maturity)
    ("US_2Y",  "JP_10Y", "US_JP_10Y_spread"),  # USD vs JPY driver (cross-maturity)
    ("US_2Y",  "JP_2Y",  "US_JP_2Y_spread"),   # USD vs JPY driver (same maturity)
]
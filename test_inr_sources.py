# test_inr_sources.py
# tests all three INR data sources before building the pipeline
# run once, verify all three pass, then delete this file

import yfinance as yf
import requests
import pandas as pd
from io import StringIO
from datetime import datetime

print("=" * 55)
print("  INR DATA SOURCE TEST")
print("=" * 55)

# TEST 1: USD/INR price from yfinance
print("\n[1/3] testing USDINR=X from yfinance...")
try:
    data = yf.download("USDINR=X", period="5d", interval="1d",
                       progress=False, auto_adjust=True)
    if len(data) > 0:
        latest = float(data['Close'].iloc[-1])
        print(f"    OK  USD/INR = {latest:.4f}")
        print(f"    rows: {len(data)}, latest date: {data.index[-1].date()}")
    else:
        print("    FAIL: empty dataframe")
except Exception as e:
    print(f"    FAIL: {e}")

# TEST 2: IN 10Y yield from RBI DBIE
print("\n[2/3] testing IN 10Y from RBI DBIE...")
try:
    url = "https://dbie.rbi.org.in/DBIE/dbie.rbi?site=publications"
    # RBI DBIE direct CSV for 10Y G-Sec benchmark
    rbi_url = "https://api.rbi.org.in/api/v1/GetDataByTableName?TableName=FBIL_GSEC&FromDate=01-01-2024&ToDate=31-12-2026"
    r = requests.get(rbi_url, timeout=30)
    print(f"    status: {r.status_code}")
    if r.status_code == 200:
        print(f"    OK  RBI API responding")
        print(f"    response preview: {r.text[:200]}")
    else:
        print(f"    FAIL: status {r.status_code}")
except Exception as e:
    print(f"    FAIL: {e}")

# TEST 3: SEBI FPI flow data
print("\n[3/3] testing SEBI FPI flow data...")
try:
    sebi_url = "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=13"
    r = requests.get(sebi_url, timeout=30,
                    headers={"User-Agent": "Mozilla/5.0"})
    print(f"    status: {r.status_code}")
    if r.status_code == 200:
        print(f"    OK  SEBI responding, content length: {len(r.text)}")
    else:
        print(f"    FAIL: status {r.status_code}")
except Exception as e:
    print(f"    FAIL: {e}")

print("\n" + "=" * 55)
print("  paste results above back to Claude before proceeding")
print("=" * 55)

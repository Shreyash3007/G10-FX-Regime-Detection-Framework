# cot_pipeline.py
# pulls CFTC COT disaggregated futures data for EUR and JPY
# extracts leveraged money (hedge fund) net positioning
# calculates rolling percentile to detect crowded positions
# saves to data/cot_latest.csv and merges with master FX data
#
# run every friday after 3:30 PM EST when CFTC publishes new data
# on other days it uses the most recent available weekly file
# charts are handled separately by create_dashboards.py
#
# why leveraged money and not noncommercial:
#   leveraged money = hedge funds and CTAs only
#   noncommercial   = hedge funds + asset managers + retail speculators
#   hedge funds drive carry trades and react to rate differentials
#   asset managers move slowly for different reasons (equity hedging etc)
#   leveraged money gives a cleaner signal for regime detection
#
# data source: CFTC financial futures disaggregated report
# URL: https://www.cftc.gov/files/dea/history/fut_fin_txt_YYYY.zip

import os
import requests
import zipfile
import pandas as pd
from io import BytesIO
from datetime import datetime

TODAY      = datetime.today().strftime('%Y-%m-%d')
CURRENT_YR = datetime.today().year

# years of history to pull for percentile calculation
# 3 years = 156 weekly observations = enough for meaningful percentiles
HISTORY_YEARS = 3

# exact market names as they appear in the CFTC file
TARGET_MARKETS = {
    "JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE": "JPY",
    "EURO FX - CHICAGO MERCANTILE EXCHANGE":      "EUR",
}

# columns we need -- everything else is discarded immediately to save memory
COLS_NEEDED = [
    "Market_and_Exchange_Names",
    "Report_Date_as_YYYY-MM-DD",
    "Lev_Money_Positions_Long_All",   # hedge fund longs
    "Lev_Money_Positions_Short_All",  # hedge fund shorts
    "Open_Interest_All",              # total open interest for normalization
]


# -- step 1: fetch one year of CFTC data ---------------------------------------

def fetch_cot_year(year):
    url = f"https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"

    try:
        r = requests.get(url, timeout=30)

        if r.status_code != 200:
            print(f"    FAILED {year} -- status {r.status_code}")
            return pd.DataFrame()

        z  = zipfile.ZipFile(BytesIO(r.content))
        df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)

        # filter immediately -- keeps only EUR and JPY rows
        mask = df["Market_and_Exchange_Names"].isin(TARGET_MARKETS.keys())
        df   = df[mask][COLS_NEEDED].copy()

        print(f"    OK  {year} -- {len(df)} rows")
        return df

    except Exception as e:
        print(f"    FAILED {year} -- {e}")
        return pd.DataFrame()


# -- step 2: fetch multiple years and combine ----------------------------------

def fetch_all_cot():
    print("\n[1/4] fetching CFTC COT data...")

    years  = range(CURRENT_YR - HISTORY_YEARS, CURRENT_YR + 1)
    frames = []

    for year in years:
        df = fetch_cot_year(year)
        if len(df) > 0:
            frames.append(df)

    if len(frames) == 0:
        print("    FAILED -- no data retrieved")
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    combined["Report_Date_as_YYYY-MM-DD"] = pd.to_datetime(
        combined["Report_Date_as_YYYY-MM-DD"]
    )
    combined = combined.sort_values("Report_Date_as_YYYY-MM-DD")
    combined = combined.drop_duplicates()

    print(f"    combined: {len(combined)} rows, "
          f"{years[0]} to {years[-1]}")
    return combined


# -- step 3: calculate net positioning and percentiles -------------------------
#
# net position = leveraged money longs minus shorts
#   positive = hedge funds net long (bullish on the currency)
#   negative = hedge funds net short (bearish, carry trade sellers)
#
# net % of open interest = net position / total open interest * 100
#   normalizes across time as market grows -- 43k contracts means
#   something different in 2020 vs 2026 depending on total market size
#
# percentile = where does this week rank vs all weeks in the history window
#   97th = more long than 97% of all weeks in past 3 years = extreme
#   3rd  = more short than 97% of all weeks = extreme short
#   50th = neutral, exactly in the middle of historical range
#
# crowding thresholds:
#   above 80th = crowded long -- limited upside, reversal risk
#   below 20th = crowded short -- limited downside, squeeze risk
#   these thresholds are judgment calls, not precise formulas

def calculate_positioning(raw_df):
    print("\n[2/4] calculating net positioning and percentiles...")

    results = {}

    for market_name, ticker in TARGET_MARKETS.items():
        df = raw_df[
            raw_df["Market_and_Exchange_Names"] == market_name
        ].copy()
        df = df.set_index("Report_Date_as_YYYY-MM-DD").sort_index()

        # convert to numeric -- CFTC files sometimes contain commas in numbers
        for col in [
            "Lev_Money_Positions_Long_All",
            "Lev_Money_Positions_Short_All",
            "Open_Interest_All"
        ]:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", ""),
                errors="coerce"
            )

        # net position in contracts
        df["net_position"] = (
            df["Lev_Money_Positions_Long_All"] -
            df["Lev_Money_Positions_Short_All"]
        )

        # net as percentage of open interest
        df["net_pct_oi"] = (
            df["net_position"] / df["Open_Interest_All"] * 100
        )

        # percentile rank vs full history window
        df["percentile"] = df["net_position"].rank(pct=True) * 100

        results[ticker] = df[[
            "net_position",
            "net_pct_oi",
            "percentile",
            "Lev_Money_Positions_Long_All",
            "Lev_Money_Positions_Short_All"
        ]].copy()

        latest    = df.iloc[-1]
        direction = "LONG" if latest["net_position"] > 0 else "SHORT"
        p         = latest["percentile"]

        print(f"    {ticker}:")
        print(f"        net position : {latest['net_position']:>+,.0f} "
              f"contracts ({direction})")
        print(f"        % of OI      : {latest['net_pct_oi']:>+.1f}%")
        print(f"        percentile   : {p:.0f}th (vs last {HISTORY_YEARS} years)")

        print(f"        regime       : ", end="")
        if p >= 80:
            print("CROWDED LONG -- limited upside, reversal risk")
        elif p <= 20:
            print("CROWDED SHORT -- squeeze risk if catalyst appears")
        else:
            print("NEUTRAL -- no crowding signal")

    return results


# -- step 4: save COT data -----------------------------------------------------

def save_cot(positioning_dict):
    os.makedirs("data", exist_ok=True)

    frames = []
    for ticker, df in positioning_dict.items():
        renamed = df.rename(columns={
            "net_position":                 f"{ticker}_net_pos",
            "net_pct_oi":                   f"{ticker}_net_pct_oi",
            "percentile":                   f"{ticker}_percentile",
            "Lev_Money_Positions_Long_All": f"{ticker}_lev_long",
            "Lev_Money_Positions_Short_All":f"{ticker}_lev_short",
        })
        frames.append(renamed)

    cot_df = pd.concat(frames, axis=1)
    cot_df.index.name = "date"

    cot_df.to_csv("data/cot_latest.csv")
    print(f"\n    saved: data/cot_latest.csv")
    print(f"    rows: {len(cot_df)}, "
          f"from {cot_df.index[0].date()} to {cot_df.index[-1].date()}")

    return cot_df


# -- step 4: merge COT with FX master ------------------------------------------
#
# COT is weekly (published every friday)
# master is daily (trading calendar)
# solution: reindex COT onto daily dates using forward fill
# each trading day gets the most recent weekly COT reading
# this is valid -- positioning doesn't change day to day between publications

def merge_with_master(cot_df):
    print("\n[4/4] merging COT with FX master data...")

    master_path = "data/latest.csv"
    if not os.path.exists(master_path):
        print("    WARNING -- data/latest.csv not found")
        print("    run pipeline.py first, then cot_pipeline.py")
        return

    master    = pd.read_csv(master_path, index_col=0, parse_dates=True)
    cot_daily = cot_df.reindex(master.index, method='ffill')

    for col in cot_daily.columns:
        master[col] = cot_daily[col]

    master.to_csv("data/latest_with_cot.csv")
    print(f"    saved: data/latest_with_cot.csv")
    print(f"    shape: {master.shape[0]} rows x {master.shape[1]} columns")


# -- main ----------------------------------------------------------------------

def main():
    print("=" * 62)
    print(f"  COT POSITIONING PIPELINE -- {TODAY}")
    print("=" * 62)

    raw_df     = fetch_all_cot()
    positioning = calculate_positioning(raw_df)

    print("\n[3/4] saving data...")
    cot_df = save_cot(positioning)
    merge_with_master(cot_df)

    # final summary
    print("\n" + "=" * 62)
    print("  COT SUMMARY")
    print("=" * 62)

    for ticker, df in positioning.items():
        latest      = df.iloc[-1]
        latest_date = df.index[-1].date()
        direction   = "LONG" if latest["net_position"] > 0 else "SHORT"
        p           = latest["percentile"]
        net         = latest["net_position"]

        if p >= 80:
            regime = "CROWDED LONG -- limited upside, watch for reversal"
        elif p <= 20:
            regime = "CROWDED SHORT -- squeeze risk if catalyst appears"
        elif net > 0:
            regime = f"MODERATELY LONG ({p:.0f}th pct) -- no crowding signal"
        elif net < 0:
            regime = f"MODERATELY SHORT ({p:.0f}th pct) -- no crowding signal"
        else:
            regime = "NEUTRAL"

        print(f"\n  {ticker} (as of {latest_date}):")
        print(f"    net position : {net:>+,.0f} contracts ({direction})")
        print(f"    % of OI      : {latest['net_pct_oi']:>+.1f}%")
        print(f"    percentile   : {p:.0f}th (vs last {HISTORY_YEARS} years)")
        print(f"    regime       : {regime}")

    print("\n" + "=" * 62)
    print("  run create_dashboards.py for charts")
    print("=" * 62)


if __name__ == "__main__":
    main()
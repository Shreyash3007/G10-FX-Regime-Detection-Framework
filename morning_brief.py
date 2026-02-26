# morning_brief.py
# generates a clean, desk-readable FX regime brief
# reads from data/latest_with_cot.csv (run pipeline.py and cot_pipeline.py first)
# outputs to terminal and saves to /briefs/brief_YYYYMMDD.txt
#
# run every morning after run_all.py
# target: readable in 60 seconds by someone on an FX desk

import os
import pandas as pd
from datetime import datetime

TODAY     = datetime.today().strftime('%Y-%m-%d')
TODAY_FMT = datetime.today().strftime('%A, %d %B %Y')


# -- helpers -------------------------------------------------------------------

def _pct(val):
    """Format a percentage change with sign and two decimals."""
    if pd.isna(val):
        return "  n/a  "
    return f"{val:>+.2f}%"


def _pp(val):
    """Format a basis point / pp change with sign and two decimals."""
    if pd.isna(val):
        return "  n/a  "
    return f"{val:>+.2f}pp"


def _net(val):
    """Format net contracts with sign and comma separator."""
    if pd.isna(val):
        return "n/a"
    return f"{val:>+,.0f}"


def _regime_label(percentile, net):
    """Return a short regime string."""
    if pd.isna(percentile):
        return "NO DATA"
    if percentile >= 80:
        return f"CROWDED LONG  ({percentile:.0f}th pct)"
    elif percentile <= 20:
        return f"CROWDED SHORT ({percentile:.0f}th pct)"
    elif net > 0:
        return f"NEUTRAL LONG  ({percentile:.0f}th pct)"
    else:
        return f"NEUTRAL SHORT ({percentile:.0f}th pct)"


def _divergence_flag(lev_net, assetmgr_net):
    """Return divergence flag if Lev Money and Asset Manager point in opposite directions."""
    if pd.isna(lev_net) or pd.isna(assetmgr_net):
        return ""
    
    lev_sign = lev_net > 0
    am_sign = assetmgr_net > 0
    
    if lev_sign != am_sign:
        return "  >> DIVERGENCE: Leveraged Money and Asset Manager opposing — signal reliability reduced"
    return ""


def _eur_interpretation(spread_10y, spread_10y_12m, eur_pct, eur_net):
    """One-line plain English read on EUR/USD regime."""
    # direction from spread
    if spread_10y_12m < -0.10:
        direction = "spread compression supports EUR strength"
    elif spread_10y_12m > 0.10:
        direction = "spread widening supports USD strength"
    else:
        direction = "spreads flat, no directional signal from differentials"

    # crowding overlay
    if eur_pct >= 80:
        crowding = "positioning crowded — asymmetric reversal risk, easy move likely priced"
    elif eur_pct <= 20:
        crowding = "positioning crowded short — squeeze risk if EUR catalyst appears"
    else:
        crowding = "positioning neutral — no crowding distortion"

    return f"{direction}; {crowding}."


def _jpy_interpretation(spread_10y, spread_10y_12m, jpy_pct, jpy_net):
    """One-line plain English read on USD/JPY regime."""
    if spread_10y_12m < -0.10:
        direction = "spread compression favors lower USD/JPY"
    elif spread_10y_12m > 0.10:
        direction = "spread widening favors higher USD/JPY"
    else:
        direction = "spreads flat, no directional signal"

    if jpy_pct <= 20:
        crowding = "yen shorts crowded — unwind/squeeze risk elevated"
    elif jpy_pct >= 80:
        crowding = "yen longs crowded — reversal risk if BoJ disappoints"
    elif jpy_net < 0:
        crowding = f"carry trade partially intact ({jpy_pct:.0f}th pct) — BoJ path is key variable"
    else:
        crowding = f"carry trade unwound, net long yen ({jpy_pct:.0f}th pct) — watch BoJ forward guidance"

    return f"{direction}; {crowding}."


# -- build the brief -----------------------------------------------------------

def build_brief(df):
    # use last row that has both FX prices and COT data
    row = df.dropna(subset=["EURUSD", "USDJPY"]).iloc[-1]
    as_of = df.dropna(subset=["EURUSD", "USDJPY"]).index[-1].date()

    # -- pull all values --
    eurusd      = row.get("EURUSD",             float('nan'))
    usdjpy      = row.get("USDJPY",             float('nan'))
    dxy         = row.get("DXY",                float('nan'))

    eur_1d      = row.get("EURUSD_chg_1D",      float('nan'))
    eur_12m     = row.get("EURUSD_chg_12M",     float('nan'))
    jpy_1d      = row.get("USDJPY_chg_1D",      float('nan'))
    jpy_12m     = row.get("USDJPY_chg_12M",     float('nan'))
    dxy_1d      = row.get("DXY_chg_1D",         float('nan'))
    dxy_12m     = row.get("DXY_chg_12M",        float('nan'))

    de10_today  = row.get("US_DE_10Y_spread",   float('nan'))
    de10_1d     = row.get("US_DE_10Y_spread_chg_1D",  float('nan'))
    de10_12m    = row.get("US_DE_10Y_spread_chg_12M", float('nan'))

    de2_today   = row.get("US_DE_2Y_spread",    float('nan'))
    de2_1d      = row.get("US_DE_2Y_spread_chg_1D",   float('nan'))
    de2_12m     = row.get("US_DE_2Y_spread_chg_12M",  float('nan'))

    jp10_today  = row.get("US_JP_10Y_spread",   float('nan'))
    jp10_1d     = row.get("US_JP_10Y_spread_chg_1D",  float('nan'))
    jp10_12m    = row.get("US_JP_10Y_spread_chg_12M", float('nan'))

    jp2_today   = row.get("US_JP_2Y_spread",    float('nan'))
    jp2_1d      = row.get("US_JP_2Y_spread_chg_1D",   float('nan'))
    jp2_12m     = row.get("US_JP_2Y_spread_chg_12M",  float('nan'))

    eur_net     = row.get("EUR_net_pos",         float('nan'))
    eur_pct_oi  = row.get("EUR_net_pct_oi",      float('nan'))
    eur_pct     = row.get("EUR_percentile",      float('nan'))

    jpy_net     = row.get("JPY_net_pos",         float('nan'))
    jpy_pct_oi  = row.get("JPY_net_pct_oi",      float('nan'))
    jpy_pct     = row.get("JPY_percentile",      float('nan'))

    # EUR Asset Manager
    eur_am_net  = row.get("EUR_assetmgr_net",    float('nan'))
    eur_am_pct_oi = row.get("EUR_assetmgr_pct_oi", float('nan'))
    eur_am_pct  = row.get("EUR_assetmgr_percentile", float('nan'))

    # EUR NonCommercial
    eur_nc_net  = row.get("EUR_noncom_net",      float('nan'))
    eur_nc_pct_oi = row.get("EUR_noncom_pct_oi", float('nan'))
    eur_nc_pct  = row.get("EUR_noncom_percentile", float('nan'))

    # JPY Asset Manager
    jpy_am_net  = row.get("JPY_assetmgr_net",    float('nan'))
    jpy_am_pct_oi = row.get("JPY_assetmgr_pct_oi", float('nan'))
    jpy_am_pct  = row.get("JPY_assetmgr_percentile", float('nan'))

    # JPY NonCommercial
    jpy_nc_net  = row.get("JPY_noncom_net",      float('nan'))
    jpy_nc_pct_oi = row.get("JPY_noncom_pct_oi", float('nan'))
    jpy_nc_pct  = row.get("JPY_noncom_percentile", float('nan'))

    # COT data is weekly -- find the actual COT date (last non-NaN)
    cot_date = "n/a"
    if os.path.exists("data/cot_latest.csv"):
        cot_raw = pd.read_csv("data/cot_latest.csv", index_col=0, parse_dates=True)
        cot_date = str(cot_raw.index[-1].date())

    # -- interpretations --
    eur_read = _eur_interpretation(de10_today, de10_12m, eur_pct, eur_net)
    jpy_read = _jpy_interpretation(jp10_today, jp10_12m, jpy_pct, jpy_net)

    W = 70  # total line width

    lines = []
    lines.append("=" * W)
    lines.append(f"  G10 FX MORNING BRIEF")
    lines.append(f"  {TODAY_FMT}")
    lines.append(f"  data as of: {as_of}  |  COT as of: {cot_date}")
    lines.append("=" * W)

    # ── PRICES ────────────────────────────────────────────────────────────────
    lines.append("")
    lines.append("  PRICES")
    lines.append(f"  {'pair':<10} {'price':>9}  {'1D':>8}  {'12M':>8}")
    lines.append(f"  {'-'*48}")
    lines.append(f"  {'EUR/USD':<10} {eurusd:>9.4f}  {_pct(eur_1d):>8}  {_pct(eur_12m):>8}")
    lines.append(f"  {'USD/JPY':<10} {usdjpy:>9.4f}  {_pct(jpy_1d):>8}  {_pct(jpy_12m):>8}")
    lines.append(f"  {'DXY':<10} {dxy:>9.4f}  {_pct(dxy_1d):>8}  {_pct(dxy_12m):>8}")

    # ── RATE DIFFERENTIALS ────────────────────────────────────────────────────
    lines.append("")
    lines.append("  RATE DIFFERENTIALS  (narrowing = foreign currency should strengthen)")
    lines.append(f"  {'spread':<22} {'today':>7}  {'1D chg':>8}  {'12M chg':>8}")
    lines.append(f"  {'-'*52}")
    lines.append(f"  {'US-DE 10Y (cross)':<22} {de10_today:>6.2f}%  {_pp(de10_1d):>8}  {_pp(de10_12m):>8}")
    lines.append(f"  {'US-DE 2Y  (same) ':<22} {de2_today:>6.2f}%  {_pp(de2_1d):>8}  {_pp(de2_12m):>8}")
    lines.append(f"  {'US-JP 10Y (cross)':<22} {jp10_today:>6.2f}%  {_pp(jp10_1d):>8}  {_pp(jp10_12m):>8}")
    lines.append(f"  {'US-JP 2Y  (same) ':<22} {jp2_today:>6.2f}%  {_pp(jp2_1d):>8}  {_pp(jp2_12m):>8}")

    # ── POSITIONING ───────────────────────────────────────────────────────────
    lines.append("")
    lines.append(f"  COT POSITIONING (as of {cot_date})")
    lines.append(f"  {'-'*66}")

    # EUR/USD positioning - all three categories
    lines.append("")
    lines.append(f"  EUR/USD:")

    # Leveraged Money
    eur_lev_net_str = _net(eur_net)
    eur_lev_oi_str  = f"{eur_pct_oi:>+.1f}% OI" if not pd.isna(eur_pct_oi) else "n/a"
    eur_lev_regime  = _regime_label(eur_pct, eur_net)
    lines.append(f"    Leveraged Money   : {eur_lev_net_str:>+,} contracts | {eur_lev_oi_str:>+6} | {eur_lev_regime}")

    # Asset Manager
    eur_am_net_str  = _net(eur_am_net)
    eur_am_oi_str   = f"{eur_am_pct_oi:>+.1f}% OI" if not pd.isna(eur_am_pct_oi) else "n/a"
    eur_am_regime   = _regime_label(eur_am_pct, eur_am_net)
    lines.append(f"    Asset Manager     : {eur_am_net_str:>+,} contracts | {eur_am_oi_str:>+6} | {eur_am_regime}")

    # NonCommercial
    eur_nc_net_str  = _net(eur_nc_net)
    eur_nc_oi_str   = f"{eur_nc_pct_oi:>+.1f}% OI" if not pd.isna(eur_nc_pct_oi) else "n/a"
    eur_nc_regime   = _regime_label(eur_nc_pct, eur_nc_net)
    lines.append(f"    NonCommercial     : {eur_nc_net_str:>+,} contracts | {eur_nc_oi_str:>+6} | {eur_nc_regime}")

    # Divergence flag for EUR
    eur_div = _divergence_flag(eur_net, eur_am_net)
    if eur_div:
        lines.append(eur_div)

    # USD/JPY positioning - all three categories
    lines.append("")
    lines.append(f"  USD/JPY:")

    # Leveraged Money
    jpy_lev_net_str = _net(jpy_net)
    jpy_lev_oi_str  = f"{jpy_pct_oi:>+.1f}% OI" if not pd.isna(jpy_pct_oi) else "n/a"
    jpy_lev_regime  = _regime_label(jpy_pct, jpy_net)
    lines.append(f"    Leveraged Money   : {jpy_lev_net_str:>+,} contracts | {jpy_lev_oi_str:>+6} | {jpy_lev_regime}")

    # Asset Manager
    jpy_am_net_str  = _net(jpy_am_net)
    jpy_am_oi_str   = f"{jpy_am_pct_oi:>+.1f}% OI" if not pd.isna(jpy_am_pct_oi) else "n/a"
    jpy_am_regime   = _regime_label(jpy_am_pct, jpy_am_net)
    lines.append(f"    Asset Manager     : {jpy_am_net_str:>+,} contracts | {jpy_am_oi_str:>+6} | {jpy_am_regime}")

    # NonCommercial
    jpy_nc_net_str  = _net(jpy_nc_net)
    jpy_nc_oi_str   = f"{jpy_nc_pct_oi:>+.1f}% OI" if not pd.isna(jpy_nc_pct_oi) else "n/a"
    jpy_nc_regime   = _regime_label(jpy_nc_pct, jpy_nc_net)
    lines.append(f"    NonCommercial     : {jpy_nc_net_str:>+,} contracts | {jpy_nc_oi_str:>+6} | {jpy_nc_regime}")

    # Divergence flag for JPY
    jpy_div = _divergence_flag(jpy_net, jpy_am_net)
    if jpy_div:
        lines.append(jpy_div)

    # ── REGIME READS ──────────────────────────────────────────────────────────
    lines.append("")
    lines.append("  REGIME READ")
    lines.append(f"  {'-'*66}")

    # wrap long interpretation lines at W-4 chars
    def _wrap(prefix, text, width=W - 4):
        import textwrap
        wrapped = textwrap.fill(text, width=width - len(prefix))
        indented = wrapped.replace("\n", "\n  " + " " * len(prefix))
        return f"  {prefix}{indented}"

    lines.append(_wrap("EUR/USD  ", eur_read))
    lines.append("")
    lines.append(_wrap("USD/JPY  ", jpy_read))

    lines.append("")
    lines.append("=" * W)
    lines.append("")

    return "\n".join(lines)


# -- main ----------------------------------------------------------------------

def main():
    master_path = "data/latest_with_cot.csv"
    if not os.path.exists(master_path):
        print("ERROR: data/latest_with_cot.csv not found")
        print("Run pipeline.py then cot_pipeline.py first")
        return

    df = pd.read_csv(master_path, index_col=0, parse_dates=True)

    brief = build_brief(df)

    # print to terminal
    print(brief)

    # save to /briefs
    os.makedirs("briefs", exist_ok=True)
    filepath = f"briefs/brief_{TODAY.replace('-', '')}.txt"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(brief)

    print(f"  saved: {filepath}")


if __name__ == "__main__":
    main()
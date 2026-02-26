# create_dashboards.py
# generates two pair-specific dashboards combining price + spread + positioning
# run after both pipeline.py and cot_pipeline.py have updated their CSVs

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import os
from datetime import datetime

TODAY = datetime.today().strftime('%Y-%m-%d')

# -- professional styling constants --
GRID_COLOR    = '#ecf0f1'
GRID_LW       = 0.5
GRID_ALPHA     = 0.7
SUBTITLE_SIZE  = 9
SUBTITLE_COLOR = '#4a4a4a'
AXIS_BG        = '#fafafa'
FIG_BG         = '#ffffff'
SPREAD_BLUE    = '#2980b9'
SPREAD_ORANGE  = '#e67e22'
BAR_GREEN      = '#27ae60'
BAR_RED        = '#e74c3c'
PCT_LINE_COLOR = '#1a1a2e'
THRESH_RED     = '#c0392b'
THRESH_GREEN   = '#1e8449'
ZERO_LINE_CLR  = '#2c3e50'


def _style_axis(ax):
    """Apply consistent professional styling to an axis."""
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_facecolor(AXIS_BG)
    ax.grid(color=GRID_COLOR, linewidth=GRID_LW, alpha=GRID_ALPHA)


def load_data():
    master_path = "data/latest_with_cot.csv"
    if not os.path.exists(master_path):
        print("ERROR: data/latest_with_cot.csv not found")
        print("Run pipeline.py then cot_pipeline.py first")
        return None

    df = pd.read_csv(master_path, index_col=0, parse_dates=True)
    print(f"loaded: {len(df)} rows, {df.shape[1]} columns")
    print(f"date range: {df.index[0].date()} to {df.index[-1].date()}")
    return df


def create_pair_dashboard(df, pair_config):
    """
    Creates a 3-panel dashboard for one FX pair.

    Panel 1: FX price line
    Panel 2: Dual rate differential lines (10Y cross-maturity + 2Y same-maturity)
    Panel 3: Net positioning bars (green/red) + percentile line on secondary axis
    """

    # filter to lookback window
    cutoff = pd.Timestamp(TODAY) - pd.DateOffset(
        months=pair_config["lookback_months"]
    )
    d = df[df.index >= cutoff].copy()

    # drop rows where price or primary spread is missing
    d = d.dropna(subset=[pair_config["price_col"], pair_config["spread_col_10y"]])

    # -- Fix 14: figure background --
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), facecolor=FIG_BG)
    # -- Fix 12: main title fontsize=13 --
    fig.suptitle(
        f"{pair_config['title']} -- {TODAY}",
        fontsize=13, fontweight='bold', y=0.98
    )

    # shared x formatter
    fmt = mdates.DateFormatter('%b %y')

    # =========================================================================
    # PANEL 1: PRICE
    # =========================================================================
    ax1 = axes[0]
    _style_axis(ax1)

    ax1.plot(
        d.index,
        d[pair_config["price_col"]],
        color=pair_config["color_price"],
        linewidth=1.5
    )
    # -- Fix 12: subtitle styling --
    ax1.set_title(
        f"{pair_config['price_label']}  |  {pair_config['price_desc']}",
        fontsize=SUBTITLE_SIZE, color=SUBTITLE_COLOR
    )
    ax1.set_ylabel(pair_config["price_label"])
    ax1.xaxis.set_major_formatter(fmt)
    ax1.tick_params(axis='x', rotation=30)

    # -- Fix 9: price annotation with bbox --
    latest_price = d[pair_config["price_col"]].iloc[-1]
    ax1.annotate(
        f"{latest_price:.4f}",
        xy=(d.index[-1], latest_price),
        xytext=(10, 0), textcoords='offset points',
        fontsize=11, color=pair_config["color_price"],
        fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                  alpha=0.85, edgecolor='none')
    )

    # =========================================================================
    # PANEL 2: DUAL SPREAD LINES
    # =========================================================================
    ax2 = axes[1]
    _style_axis(ax2)

    spread_10y = d[pair_config["spread_col_10y"]]
    spread_2y  = d[pair_config["spread_col_2y"]]

    # -- Fix 6: clean blue/orange, linewidth=1.8 --
    ax2.plot(
        d.index, spread_10y,
        color=SPREAD_BLUE, linewidth=1.8,
        label=pair_config["spread_10y_label"]
    )
    ax2.plot(
        d.index, spread_2y,
        color=SPREAD_ORANGE, linewidth=1.8,
        label=pair_config["spread_2y_label"]
    )

    # -- Fix 7: prominent zero/parity line --
    ax2.axhline(y=0, color=ZERO_LINE_CLR, linewidth=1.2,
                linestyle='--', alpha=0.6)
    ax2.text(d.index[0], 0, '  parity', fontsize=7, color=ZERO_LINE_CLR,
             va='bottom', alpha=0.7)

    # -- Fix 12: subtitle styling --
    ax2.set_title(
        f"Rate Differentials (pp)  |  {pair_config['spread_desc']}",
        fontsize=SUBTITLE_SIZE, color=SUBTITLE_COLOR
    )
    ax2.set_ylabel("spread (pp)")
    ax2.xaxis.set_major_formatter(fmt)
    ax2.tick_params(axis='x', rotation=30)
    ax2.legend(fontsize=8, loc='best')

    # -- Fix 8: annotations matching line colors, fontsize=10, edge bbox --
    latest_10y = spread_10y.iloc[-1]
    latest_2y  = spread_2y.iloc[-1]

    bbox_10y = dict(boxstyle='round,pad=0.2', facecolor='white',
                    alpha=0.85, edgecolor=SPREAD_BLUE)
    bbox_2y  = dict(boxstyle='round,pad=0.2', facecolor='white',
                    alpha=0.85, edgecolor=SPREAD_ORANGE)

    if latest_10y >= latest_2y:
        offset_10y, offset_2y = (5, 8), (5, -14)
    else:
        offset_10y, offset_2y = (5, -14), (5, 8)

    ax2.annotate(
        f"{latest_10y:.2f}%",
        xy=(d.index[-1], latest_10y),
        xytext=offset_10y, textcoords='offset points',
        fontsize=10, color=SPREAD_BLUE, fontweight='bold',
        bbox=bbox_10y
    )
    ax2.annotate(
        f"{latest_2y:.2f}%",
        xy=(d.index[-1], latest_2y),
        xytext=offset_2y, textcoords='offset points',
        fontsize=10, color=SPREAD_ORANGE, fontweight='bold',
        bbox=bbox_2y
    )

    # =========================================================================
    # PANEL 3: POSITIONING BARS + PERCENTILE LINE
    # =========================================================================
    ax3 = axes[2]
    _style_axis(ax3)

    pct_col = pair_config.get("pct_col")
    net_col = pair_config.get("net_col")

    has_net = net_col and net_col in d.columns and d[net_col].notna().sum() > 5
    has_pct = pct_col and pct_col in d.columns and d[pct_col].notna().sum() > 5

    if has_net or has_pct:

        # -- bar chart for net position on primary axis --
        if has_net:
            net_vals = d[net_col].dropna()
            # -- Fix 5: professional bar colors --
            colors = np.where(net_vals >= 0, BAR_GREEN, BAR_RED)
            ax3.bar(
                net_vals.index, net_vals,
                color=colors, width=2.0, alpha=0.7
            )
            ax3.set_ylabel("net position (contracts)")
            ax3.axhline(y=0, color='black', linewidth=0.6, alpha=0.4)

            # 20% padding above max and below min
            net_max = net_vals.max()
            net_min = net_vals.min()
            net_range = net_max - net_min if net_max != net_min else abs(net_max) or 1
            ax3.set_ylim(net_min - 0.2 * net_range, net_max + 0.2 * net_range)

        # -- percentile lines on secondary axis --
        if has_pct:
            pct_vals = d[pct_col].dropna()

            ax3_r = ax3.twinx()

            # LEVERAGED MONEY percentile (primary line)
            # -- Fix 1: navy color, zorder=5, linewidth=2.0 --
            ax3_r.plot(
                pct_vals.index, pct_vals,
                color=PCT_LINE_COLOR, linewidth=2.0,
                label='Lev Money Percentile (3Y)', zorder=5
            )

            # ASSET MANAGER percentile (secondary line, dashed purple)
            assetmgr_pct_col = pair_config.get("assetmgr_pct_col")
            if assetmgr_pct_col and assetmgr_pct_col in d.columns and d[assetmgr_pct_col].notna().sum() > 5:
                am_pct_vals = d[assetmgr_pct_col].dropna()
                ax3_r.plot(
                    am_pct_vals.index, am_pct_vals,
                    color='#8e44ad', linewidth=1.8, linestyle='--',
                    label='Asset Manager Percentile (3Y)', zorder=4, alpha=0.8
                )

            # NONCOMMERCIAL percentile (tertiary line, dotted orange)
            # -- commented out to reduce chart clutter; kept in text brief only --
            # noncom_pct_col = pair_config.get("noncom_pct_col")
            # if noncom_pct_col and noncom_pct_col in d.columns and d[noncom_pct_col].notna().sum() > 5:
            #     nc_pct_vals = d[noncom_pct_col].dropna()
            #     ax3_r.plot(
            #         nc_pct_vals.index, nc_pct_vals,
            #         color='#e67e22', linewidth=1.6, linestyle=':',
            #         label='NonCommercial Percentile (3Y)', zorder=3, alpha=0.7
            #     )

            # -- Fix 2: deep red/green threshold lines, zorder=6 --
            ax3_r.axhline(
                y=80, color=THRESH_RED, linewidth=1.5,
                linestyle='--', alpha=0.7, label='80th (crowded long)',
                zorder=6
            )
            ax3_r.axhline(
                y=20, color=THRESH_GREEN, linewidth=1.5,
                linestyle='--', alpha=0.7, label='20th (crowded short)',
                zorder=6
            )
            ax3_r.axhline(
                y=50, color='gray', linewidth=0.8,
                linestyle='-', alpha=0.4
            )

            # -- Fix 4: shading alpha=0.08 --
            ax3_r.fill_between(
                pct_vals.index, 80, 100,
                alpha=0.08, color='red'
            )
            ax3_r.fill_between(
                pct_vals.index, 0, 20,
                alpha=0.08, color='green'
            )

            ax3_r.set_ylabel("percentile")
            ax3_r.set_ylim(0, 100)
            # -- Fix 10: remove right spine on secondary axis explicitly --
            # (twinx creates a new right spine that _style_axis won't catch)
            ax3_r.spines['top'].set_visible(False)
            # -- Fix 3: legend with only percentile + thresholds, no bars --
            ax3_r.legend(fontsize=7, loc='upper right')

            # regime background color
            latest_pct = pct_vals.iloc[-1]
            if latest_pct >= 80:
                regime_label = f"CROWDED LONG ({latest_pct:.0f}th pct) -- reversal risk"
                regime_color = '#ffcccc'
            elif latest_pct <= 20:
                regime_label = f"CROWDED SHORT ({latest_pct:.0f}th pct) -- squeeze risk"
                regime_color = '#ccffcc'
            else:
                regime_label = f"NEUTRAL ({latest_pct:.0f}th pct) -- no crowding signal"
                regime_color = '#f5f5f5'

            ax3.set_facecolor(regime_color)

            # annotate latest percentile
            ax3_r.annotate(
                f"{latest_pct:.0f}th",
                xy=(pct_vals.index[-1], latest_pct),
                xytext=(10, 0), textcoords='offset points',
                fontsize=9, color=PCT_LINE_COLOR, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                          alpha=0.85, edgecolor='none')
            )
        else:
            regime_label = "no percentile data"

        # -- Fix 12: subtitle styling --
        ax3.set_title(
            f"Positioning (3Y) — Lev Money (primary) + Asset Manager (dashed)  |  {regime_label}",
            fontsize=10, color='#2c3e50'
        )

    else:
        ax3.text(
            0.5, 0.5,
            "COT data not yet loaded\nRun cot_pipeline.py first",
            transform=ax3.transAxes,
            ha='center', va='center',
            fontsize=11, color='gray'
        )
        ax3.set_title("Positioning (3Y) — All three COT categories",
                       fontsize=10, color='#2c3e50')

    ax3.xaxis.set_major_formatter(fmt)
    ax3.tick_params(axis='x', rotation=30)

    # -- Fix 13: consistent spacing --
    plt.tight_layout(pad=2.0, h_pad=2.5)

    os.makedirs("charts", exist_ok=True)
    chart_path = f"charts/{pair_config['filename']}_{TODAY.replace('-','')}.png"
    plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor=FIG_BG)
    print(f"saved: {chart_path}")

    plt.show(block=False)
    plt.pause(2)
    plt.close()

    return chart_path


def main():
    print("=" * 55)
    print(f"  PAIR DASHBOARDS -- {TODAY}")
    print("=" * 55)

    df = load_data()
    if df is None:
        return

    # EUR/USD dashboard config
    eurusd_config = {
        "title":            "EUR/USD -- Price + Rate Differential + Positioning",
        "price_col":        "EURUSD",
        "spread_col_10y":   "US_DE_10Y_spread",
        "spread_col_2y":    "US_DE_2Y_spread",
        "spread_10y_label": "US 2Y - DE 10Y (cross-maturity)",
        "spread_2y_label":  "US 2Y - DE 2Y (same-maturity)",
        "spread_desc":      "narrowing = EUR/USD should rise",
        "pct_col":          "EUR_percentile",               # Leveraged Money percentile
        "assetmgr_pct_col": "EUR_assetmgr_percentile",     # Asset Manager percentile
        "noncom_pct_col":   "EUR_noncom_percentile",        # NonCommercial percentile
        "net_col":          "EUR_net_pos",
        "price_label":      "USD per 1 EUR",
        "price_desc":       "UP = euro stronger vs dollar",
        "color_price":      "#1f77b4",
        "filename":         "eurusd_dashboard",
        "lookback_months":  12,
    }

    # USD/JPY dashboard config
    usdjpy_config = {
        "title":            "USD/JPY -- Price + Rate Differential + Positioning",
        "price_col":        "USDJPY",
        "spread_col_10y":   "US_JP_10Y_spread",
        "spread_col_2y":    "US_JP_2Y_spread",
        "spread_10y_label": "US 2Y - JP 10Y (cross-maturity)",
        "spread_2y_label":  "US 2Y - JP 2Y (same-maturity)",
        "spread_desc":      "narrowing = USD/JPY should fall",
        "pct_col":          "JPY_percentile",               # Leveraged Money percentile
        "assetmgr_pct_col": "JPY_assetmgr_percentile",     # Asset Manager percentile
        "noncom_pct_col":   "JPY_noncom_percentile",        # NonCommercial percentile
        "net_col":          "JPY_net_pos",
        "price_label":      "JPY per 1 USD",
        "price_desc":       "UP = dollar stronger vs yen",
        "color_price":      "#ff7f0e",
        "filename":         "usdjpy_dashboard",
        "lookback_months":  12,
    }

    print("\n[1/2] creating EUR/USD dashboard...")
    eurusd_path = create_pair_dashboard(df, eurusd_config)

    print("\n[2/2] creating USD/JPY dashboard...")
    usdjpy_path = create_pair_dashboard(df, usdjpy_config)

    print("\n" + "=" * 55)
    print("  done. charts saved:")
    print(f"  {eurusd_path}")
    print(f"  {usdjpy_path}")
    print("=" * 55)


if __name__ == "__main__":
    main()

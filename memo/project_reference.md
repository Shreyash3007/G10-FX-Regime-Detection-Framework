# G10 FX REGIME DETECTION FRAMEWORK
# Project Reference Document
# Shreyash Sakhare | Updated February 2026

## PROJECT SUMMARY
Automated daily pipeline detecting FX regimes for EUR/USD and USD/JPY.
Two analytical layers: rate differentials + speculative positioning.
Goal: classify whether price is driven by fundamental rate differential 
forces or crowded positioning dynamics.

## FILE STRUCTURE
C:\Market Journey 2026\Code\fx_regime\
├── pipeline.py          # Layer 1: FX prices + yield data + spreads
├── cot_pipeline.py      # Layer 2: CFTC COT positioning data
├── create_dashboards.py # Visualization: pair-specific 3-panel charts
├── run_all.py           # Runs all three in sequence
├── config.py            # Configuration and constants
├── requirements.txt     # Python dependencies
├── .env                 # FRED API key (not in repo)
├── data/                # CSV outputs from each pipeline run
├── charts/              # Dashboard PNG files
├── memo/                # Daily memo text files
└── notebooks/           # Exploratory analysis

## DATA SOURCES
FX Prices: Yahoo Finance via yfinance
  - EURUSD=X, JPY=X, DX-Y.NYB (DXY)
  - GBP/USD removed from active tracking

US Yields: FRED API (daily, requires API key in .env)
  - US 2Y: DGS2
  - US 10Y: DGS10

German Yields: ECB Statistical Data Warehouse (daily, no API key)
  - DE 2Y: daily series
  - DE 10Y: daily series

Japan Yields: Ministry of Finance Japan (daily, no API key)
  - JP 2Y: daily JGB series
  - JP 10Y: daily JGB series

COT Positioning: CFTC Disaggregated Financial Futures
  - URL: https://www.cftc.gov/files/dea/history/fut_fin_txt_YYYY.zip
  - Category: Leveraged Money only
  - Pairs: EUR (Euro FX futures) and JPY (Japanese Yen futures)
  - Frequency: Weekly, published Friday 3:30pm EST
  - Reflects: Tuesday positioning (3-4 day lag)
  - Lookback: 3 years (~156 weekly observations)

## SPREADS CALCULATED
US_DE_10Y_spread: US 2Y minus DE 10Y (cross-maturity, original signal)
US_DE_2Y_spread:  US 2Y minus DE 2Y (same-maturity, policy rate signal)
US_JP_10Y_spread: US 2Y minus JP 10Y (cross-maturity, original signal)
US_JP_2Y_spread:  US 2Y minus JP 2Y (same-maturity, policy rate signal)
US_curve:         US 10Y minus US 2Y (yield curve steepness)

## CURRENT READINGS (as of 2026-02-26)
EUR/USD:  1.1775  (+12.31% 12M)
USD/JPY:  155.88  (+4.40% 12M)
DXY:      97.70   (-7.60% 12M)

US 2Y:    3.43%   (-0.53pp 12M)
US 10Y:   4.04%   (-0.18pp 12M)
DE 2Y:    2.01%   (+0.03pp 12M)
DE 10Y:   2.77%   (+0.21pp 12M)
JP 2Y:    1.22%   (+0.39pp 12M)
JP 10Y:   2.15%   (+0.73pp 12M)

US-DE 10Y spread: 0.66%  (-0.74pp 12M)
US-DE 2Y spread:  1.42%  (-0.56pp 12M)
US-JP 10Y spread: 1.28%  (-1.26pp 12M)
US-JP 2Y spread:  2.21%  (-0.92pp 12M)

EUR positioning: +43,549 contracts LONG | 97th percentile | CROWDED LONG
JPY positioning: -29,321 contracts SHORT | 67th percentile | NEUTRAL

## REGIME CLASSIFICATIONS
REGIME 1 - Rate Differential Dominant:
  Conditions: positioning neutral, vol low, central bank paths clear
  Current example: EUR/USD past 12 months (spread narrowed, EUR rose)

REGIME 2 - Positioning Dominant:
  Conditions: crowded positioning overriding fundamentals
  Current example: EUR/USD today (97th pct, direction right but crowded)
  Past example: USD/JPY mid-2025 (carry trade overrode spread signal)

REGIME 3 - Risk Sentiment Dominant:
  Conditions: vol spike, forced liquidations, correlations break
  Example: August 2024 yen carry unwind

## KEY ANALYTICAL FINDINGS
EUR/USD: Rate differential signal confirmed. Spread compressed 74bp in
12 months. EUR rose 12.31%. But positioning at 97th percentile means
the trade is crowded consensus. Asymmetric reversal risk despite correct
fundamental direction.

USD/JPY: Rate differential prediction failed in 2025. Spread compressed
126bp but USD/JPY rose 4.4% instead of falling. COT data explains why:
carry trade was being built with positioning reaching near -100,000
contracts extreme short yen. Now partially unwinding to -29,321.
Framework correctly identified the regime failure through positioning data.

## KNOWN LIMITATIONS
1. COT 3-4 day publication lag (Tuesday data published Friday)
2. 3-year percentile window = 156 observations only
3. Maturity mismatch: US 2Y vs foreign 10Y (deliberate but impure)
4. No volatility layer yet (next build priority)
5. No catalyst/macro calendar layer
6. Direction signal only, no magnitude estimate
7. No cross-asset context (equities, credit spreads)

## DELIBERATE DESIGN CHOICES AND RATIONALE
Why US 2Y not US 10Y:
  2Y most sensitive to Fed policy expectations, drives capital flows
  over typical FX holding periods. Defensible but acknowledge critique.

Why Leveraged Money not NonCommercial:
  Asset managers buy currency for equity hedging (mechanical, not macro).
  Leveraged money reflects macro thesis crowding specifically.
  NonCommercial mixes both signals.

Why 3 year percentile window:
  Pre-2022 zero-rate environment is structurally different regime.
  3 years captures current rate cycle only. Tradeoff: fewer observations.

Why not USD/INR:
  No equivalent CFTC COT public data for USD/INR.
  RBI manages capital account differently from G10.
  Would require different architecture: RBI intervention proxy,
  oil price correlation, SEBI FPI flow data as positioning substitute.

## NEXT BUILD PRIORITIES
1. morning_brief.py: Clean formatted .txt output, desk-readable 60 seconds
2. Multiple COT categories: Add NonCommercial + Asset Manager alongside
   Leveraged Money for wider positioning picture
3. Volatility layer: 30-day realized vol from existing price data,
   flag when above 75th percentile of own history
4. USD/INR extension: Modified architecture for emerging market pair

## MACRO CONTEXT
Fed: 3.5-3.75%, pausing. Two cuts expected 2026.
     Kevin Warsh replacing Powell in May 2026.
     Inflation at ~3% PCE, above 2% target.
     Next cut probability: June 2026 per futures market.

BoJ: 0.75% (highest since 1995, hiked December 2025).
     Next hike: second half 2026, likely October per ING.
     Terminal rate: 1.0-1.5% by end 2026 (analyst consensus).
     Shunto wage negotiations March 2026 = key catalyst to watch.
     Real rates still deeply negative even at 0.75%.

ECB: Germany broke debt brake for defense spending.
     Fiscal expansion putting upward pressure on DE yields.
     Structural EUR/USD fundamental support intact.

## CAREER CONTEXT
HSBC call: Vishal Prithiani, AVP FX and Liabilities, JBIMS 2023.
           Reached out via LinkedIn, scheduled via work email.
           Call rescheduled to Friday 2pm (food poisoning).
           Formal professional interaction, corporate Zoom.
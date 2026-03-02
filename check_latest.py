import pandas as pd

master = pd.read_csv('data/latest.csv', index_col=0, parse_dates=True)
print('columns with vol:', [c for c in master.columns if 'vol' in c])
print(master[['EURUSD_vol30','EURUSD_vol_pct','USDJPY_vol30','USDJPY_vol_pct']].tail())

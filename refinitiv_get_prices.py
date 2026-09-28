# refinitiv_get_prices.py — run this inside Refinitiv Workspace's CodeBook
# (Jupyter). Paste into one cell and run, or upload as a notebook cell.
# Writes prices.csv in CodeBook's file browser -> download it into your HF folder.

import refinitiv.data as rd
import pandas as pd

rd.open_session()  # in CodeBook this connects automatically to your Workspace login

START = "2024-01-02"
TICKERS = ["UPS","CNH","VMI","AGCO","GXO","R","DE","CHRW","JBHT","LNN","EXPD","CTVA",
           "SPY","IYT","MOO","NVDA","MSFT","GOOGL","AMD","AVGO","PLTR"]
SUFFIXES = [".N", ".OQ", ".P", ".K", ".Z", ""]  # NYSE, Nasdaq, Arca, Cboe...

series, failed = {}, []
for t in TICKERS:
    got = False
    for sfx in SUFFIXES:
        ric = t + sfx
        try:
            h = rd.get_history(universe=ric, fields="TRDPRC_1",
                               interval="daily", start=START)
            if h is not None and len(h) > 50:          # sanity: real history
                s = h.iloc[:, 0]
                s.name = t                              # plain ticker for backtest.py
                series[t] = s
                print(f"{t:6s} <- {ric:9s} {len(s)} days")
                got = True
                break
        except Exception:
            continue
    if not got:
        failed.append(t)

if failed:
    print("\nFAILED (find the right RIC via Workspace search, then add it manually):", failed)

px = pd.concat(series.values(), axis=1).sort_index()
px.index = pd.to_datetime(px.index)
px.index.name = "Date"
px.reset_index().to_csv("prices.csv", index=False)
print(f"\nWrote prices.csv: {len(px)} trading days x {len(px.columns)} tickers.")
print("Download prices.csv from the CodeBook file browser into your HF folder,")
print("then run locally:  python3 backtest.py")

# Note for the write-up: TRDPRC_1 history is split-adjusted close. For a
# dividend-inclusive (total-return) series later, pull TR.TotalReturn fields
# and compare — differences over ~2.7 years are small but worth footnoting.

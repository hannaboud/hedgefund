"""
compare_screen.py - control test: does the SCREEN add value beyond the UNIVERSE?
Every portfolio is sector-neutral: each stock is hedged dollar-for-dollar with
its own sector ETF (logistics -> IYT, agriculture -> MOO).

Portfolios compared:
  A. Screened 12, score-weighted   (the actual fund)
  B. Screened 12, equal-weighted   (same names, removes the weighting effect)
  C. Rejected 10, equal-weighted   (what the screen said no to)
  D. All 22, equal-weighted        (no screen: universe only)
  E. Spread: B minus C             (pure screen effect)

Needs: scoring_sheet_computed.csv, portfolio.csv, prices.csv with all 22 names.
Run:   python3 compare_screen.py
"""
import pandas as pd

HEDGE_ETF = {"logistics": "IYT", "agriculture": "MOO"}

scores = pd.read_csv("scoring_sheet_computed.csv")
port = pd.read_csv("portfolio.csv")
px = pd.read_csv("prices.csv", parse_dates=["Date"]).set_index("Date").sort_index()

universe = list(scores.ticker)
needed = universe + ["IYT", "MOO"]
missing = [t for t in needed if t not in px.columns]
if missing:
    raise SystemExit(f"prices.csv is missing: {missing}\n"
                     "Run the CodeBook cell that adds the 10 rejected names, then re-download.")

px = px[needed].apply(pd.to_numeric, errors="coerce")
first_full = px.dropna().index[0]
px = px.loc[first_full:].ffill()
r = px.pct_change().dropna()
sector_of = scores.set_index("ticker").sector

# each stock's daily return minus its own sector ETF
excess = pd.DataFrame({t: r[t] - r[HEDGE_ETF[sector_of[t]]] for t in universe})

held = list(port.ticker)
rejected = [t for t in universe if t not in held]
w_score = pd.Series(port.weight.values, index=port.ticker)
eq = lambda names: pd.Series(1 / len(names), index=names)

books = {
    "A. Screened 12, score-weighted": excess[held] @ w_score,
    "B. Screened 12, equal-weighted": excess[held] @ eq(held),
    "C. Rejected 10, equal-weighted": excess[rejected] @ eq(rejected),
    "D. All 22, equal-weighted (no screen)": excess[universe] @ eq(universe),
}
books["E. Screen effect (B minus C)"] = books["B. Screened 12, equal-weighted"] - books["C. Rejected 10, equal-weighted"]
daily = pd.DataFrame(books)
curves = (1 + daily).cumprod()
yrs = len(daily) / 252

stats = pd.DataFrame({
    "total_return": curves.iloc[-1] - 1,
    "ann_return": curves.iloc[-1] ** (1 / yrs) - 1,
    "ann_vol": daily.std() * 252 ** 0.5,
    "max_drawdown": curves.apply(lambda c: (c / c.cummax() - 1).min()),
})
stats["ret_per_vol"] = stats.ann_return / stats.ann_vol
print(f"Window: {first_full.date()} -> {px.index[-1].date()} ({len(px)} trading days)")
print("All portfolios sector-neutral (each stock hedged with its own sector ETF)\n")
print(stats.to_string(float_format=lambda x: f"{x:,.3f}"))

print("\nBy calendar year:")
print(daily.groupby(daily.index.year).apply(lambda d: (1 + d).prod() - 1)
      .to_string(float_format=lambda x: f"{x:+.1%}"))

# per-stock view across the whole universe: does score predict excess return?
tot_excess = {t: (1 + r[t]).prod() / (1 + r[HEDGE_ETF[sector_of[t]]]).prod() - 1 for t in universe}
tab = scores.set_index("ticker")[["sector", "composite"]].copy()
tab["excess_vs_own_etf"] = pd.Series(tot_excess)
tab["held"] = tab.index.isin(held)
tab = tab.sort_values("composite", ascending=False)
rho = tab.composite.rank().corr(tab.excess_vs_own_etf.rank())
print("\nAll 22 names, by score:")
print(tab.to_string(float_format=lambda x: f"{x:+.3f}"))
print(f"\nScore vs outcome across all 22 (rank correlation): {rho:+.2f}")
print(f"Beat own sector ETF: held {int((tab[tab.held].excess_vs_own_etf > 0).sum())}/{len(held)}, "
      f"rejected {int((tab[~tab.held].excess_vs_own_etf > 0).sum())}/{len(rejected)}")
print("\nNote: price returns, no dividends, no borrow or trading costs.")

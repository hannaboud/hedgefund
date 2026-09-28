"""
backtest.py - v2, SECTOR-NEUTRAL (Decision 10).
Long the screened portfolio, short each name's sector ETF dollar-for-dollar
(logistics -> IYT, agriculture -> MOO). Also reports the unhedged long book,
benchmarks, and per-stock contribution.

Needs: portfolio.csv (from compute_scores.py), prices.csv (Refinitiv export)
Run:   python3 backtest.py
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HEDGE_ETF = {"logistics": "IYT", "agriculture": "MOO"}
AI_BASKET = ["NVDA", "MSFT", "GOOGL", "AMD", "AVGO", "PLTR"]

port = pd.read_csv("portfolio.csv")
px = pd.read_csv("prices.csv", parse_dates=["Date"]).set_index("Date").sort_index()

needed = list(port.ticker) + AI_BASKET + ["SPY", "IYT", "MOO"]
missing = [t for t in needed if t not in px.columns]
if missing:
    raise SystemExit(f"prices.csv is missing columns: {missing}")
px = px[needed].apply(pd.to_numeric, errors="coerce")
first_full = px.dropna().index[0]
px = px.loc[first_full:].ffill()
r = px.pct_change().dropna()
print(f"Backtest window: {first_full.date()} -> {px.index[-1].date()} ({len(px)} trading days)\n")

w = pd.Series(port.weight.values, index=port.ticker)
sector_of = pd.Series(port.sector.values, index=port.ticker)
long_book = r[w.index] @ w
hedge_w = w.groupby(sector_of.map(HEDGE_ETF)).sum()          # $ short per ETF
hedge = r[hedge_w.index] @ hedge_w
neutral = long_book - hedge

daily = pd.DataFrame({
    "Sector-neutral fund": neutral,
    "Long book (unhedged)": long_book,
    "SPY": r.SPY,
    "Sector hedge (IYT/MOO)": hedge,
    "AI basket": r[AI_BASKET].mean(axis=1),
})
curves = (1 + daily).cumprod()
yrs = len(daily) / 252

stats = pd.DataFrame({
    "total_return": curves.iloc[-1] - 1,
    "ann_return": curves.iloc[-1] ** (1 / yrs) - 1,
    "ann_vol": daily.std() * 252 ** 0.5,
    "max_drawdown": curves.apply(lambda c: (c / c.cummax() - 1).min()),
})
stats["sharpe_ish"] = stats.ann_return / stats.ann_vol
stats["corr_to_SPY"] = daily.corrwith(daily.SPY)
print(stats.to_string(float_format=lambda x: f"{x:,.3f}"))

print("\nSector-neutral fund by calendar year:")
for y, s in neutral.groupby(neutral.index.year):
    print(f"  {y}: {(1 + s).prod() - 1:+.1%}")

# per-stock contribution to the neutral book: weight x (stock - its hedge ETF), compounded simply
contrib = {}
for t in w.index:
    etf = HEDGE_ETF[sector_of[t]]
    excess = (1 + r[t]).prod() / (1 + r[etf]).prod() - 1
    contrib[t] = (w[t], excess, w[t] * excess)
c = pd.DataFrame(contrib, index=["weight", "excess_vs_own_etf", "approx_contribution"]).T
c = c.sort_values("approx_contribution", ascending=False)
print("\nPer-stock: return relative to own sector ETF, and approx contribution:")
print(c.to_string(float_format=lambda x: f"{x:+.3f}"))
gross_pos = c.approx_contribution.clip(lower=0).sum()
top2 = c.approx_contribution.head(2).sum()
print(f"\nBreadth: {(c.excess_vs_own_etf > 0).sum()}/{len(c)} names beat their sector ETF; "
      f"top 2 winners = {top2/gross_pos:.0%} of all positive contribution.")
comp = pd.Series(port.composite.values, index=port.ticker)
rho = comp.rank().corr(c.excess_vs_own_etf.rank())
print(f"Score vs outcome (rank correlation, composite vs excess return): {rho:+.2f}")

ax = curves[["Sector-neutral fund", "Long book (unhedged)", "SPY", "Sector hedge (IYT/MOO)"]].plot(
    figsize=(10, 6), linewidth=1.6,
    title=f"AI Shadow Beneficiaries — growth of $1 since {first_full.date()}")
ax.axhline(1, color="grey", linewidth=0.8)
ax.set_ylabel("Growth of $1")
plt.tight_layout()
plt.savefig("backtest.png", dpi=150)
print("\nSaved chart -> backtest.png  (AI basket omitted from chart for scale; see table)")
print("Note: price returns, no dividends, no short-borrow or trading costs.")

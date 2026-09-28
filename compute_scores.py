"""
compute_scores.py - FULL pipeline (v3): data_sheet.csv + rubric.yaml
  -> composite scores for all 22 names (scoring_sheet_computed.csv)
  -> score-weighted portfolio with cap    (portfolio.csv)
Run:  python3 compute_scores.py     (then backtest.py once prices.csv exists)
"""
import pandas as pd, yaml

rubric = yaml.safe_load(open("rubric.yaml"))
raw = pd.read_csv("data_sheet.csv")

def pct(s, mx, inv=False):
    r = s.rank(pct=True)
    if inv: r = 1 - r + 1/len(s.dropna())
    return (r*mx).round(1)

out = raw[["ticker","company","sector","subindustry"]].copy()
# Cost structure (35): labor+SG&A+R&D % of value added; sub-industry automatability; rev/employee
out["labor_sga_share"] = pct(pd.to_numeric(raw.labor_pct_va, errors="coerce"), 15)
out["automatability"] = raw.subindustry.map(rubric["automatability_map"])
out["rev_per_employee_gap"] = pct(pd.to_numeric(raw.revenue_musd)/pd.to_numeric(raw.employees), 5, inv=True)
# Adoption (30): intensity 0-2 -> 16 pts; named vendor/tech deal -> 14 pts
ai = pd.to_numeric(raw.ai_intensity)
out["deployed_use_cases"] = (ai/2*16).round(1)
out["vendor_capex"] = pd.to_numeric(raw.vendor_deal)*14
# Not crowded (20): cheap vs universe; absent from AI ETFs; low AI press
out["valuation_vs_peers"] = pct(pd.to_numeric(raw.fwd_pe), 8, inv=True)
out["absent_from_baskets"] = (1-pd.to_numeric(raw.in_ai_etf))*6
out["no_sellside_ai"] = ((2-pd.to_numeric(raw.press_ai_volume))/2*6).round(1)
# Industry structure (15): adoption rank within sector; pricing power
out["adoption_lead"] = ai.groupby(raw.sector).transform(lambda s: (s.rank(pct=True)*8)).round(1)
out["pricing_power"] = (pd.to_numeric(raw.gross_margin_score)/2*7).round(1)
out["ai_priced"] = pd.to_numeric(raw.ai_priced)
# GXO/Ryder: labor not separable (see data_sheet notes) -> neutral midpoint on that one signal
out.loc[out.labor_sga_share.isna(), "labor_sga_share"] = 7.5

sig = [c for c in out.columns if c not in ("ticker","company","sector","subindustry","ai_priced")]
mult = out.ai_priced.map(lambda f: rubric["crowding_penalty"]["multiplier"] if f==1 else 1.0)
out["composite"] = (out[sig].sum(axis=1)*mult).round(1)
out.to_csv("scoring_sheet_computed.csv", index=False)
print("=== COMPOSITE RANKING ===")
print(out.sort_values("composite", ascending=False)[["ticker","sector","composite"]].to_string(index=False))

p = rubric["portfolio"]
q = out[out.composite >= p["inclusion_threshold"]].copy()
if q.empty:
    print("\nNo names met the threshold."); raise SystemExit
q["weight"] = q.composite/q.composite.sum()
cap = p["max_position"]
for _ in range(20):
    ov = q.weight > cap+1e-9
    if not ov.any(): break
    ex = (q.loc[ov,"weight"]-cap).sum(); q.loc[ov,"weight"] = cap
    q.loc[~ov,"weight"] += ex*q.loc[~ov,"weight"]/q.loc[~ov,"weight"].sum()
q = q.sort_values("weight", ascending=False)
q.to_csv("portfolio.csv", index=False)
print(f"\n=== PORTFOLIO ({len(q)} names, formed {rubric['formation_date']}) ===")
print(q[["ticker","company","composite","weight"]].to_string(index=False, float_format=lambda x: f"{x:,.3f}"))
print("\nNOTE: provisional cells flagged [verify] in data_sheet.csv (valuations, pricing power,")
print("~10 adoption scores). Replace with Refinitiv data + team ratifications, rerun this script.")

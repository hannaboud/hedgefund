# AI Shadow Beneficiaries Fund — pilot toolkit (v2, hybrid systematic)

Thesis: buy companies whose OPERATIONS benefit from AI adoption before the
market prices it in. AI users, not AI suppliers.

## Decision log (every choice = PM team's, with rationale)
1. Pilot sectors: logistics/transport + agriculture (comparative pilot;
   includes deliberate "should-fail" controls: railroads, commodity processors)
2. Formation date: 2024-01-02 (point-in-time discipline; all evidence pre-dates it)
3. Benchmarks: SPY + sector legs (IYT/MOO 50-50) + custom AI-supplier basket
   frozen Jan-2024 (NVDA MSFT GOOGL AMD AVGO PLTR, equal weight)
4. Criteria weights 35/30/20/15: cost structure > adoption evidence >
   not-crowded > industry structure
5. AI-priced names: 0.5 composite multiplier, not excluded
6. Portfolio: all names >= 55/100, score-weighted, 15% position cap
7. Model: HYBRID SYSTEMATIC — scores computed mechanically from data
   (percentile ranks), automatability set once per sub-industry by the team,
   top names sanity-checked by PMs before inclusion. ai_hiring signal cut
   (weak historical data); its 8 pts redistributed within adoption evidence.
8. Cost-structure denominator: labor/SG&A as % of VALUE ADDED (gross profit /
   revenue net of pass-through inputs: purchased transportation, fuel, COGS).
   Rationale: commodity/pass-through inputs are exogenous to the AI thesis.
   Universe: curated 22 for the pilot; production methodology = rule-based
   (Russell 1000, GICS transport + ag sub-industries, mcap > $2B, Jan-2024).

## Files & pipeline (run in this order)
1. data_sheet.csv          — raw point-in-time metrics, one row per company,
                             every figure source-cited; [approx, verify] flags
                             mark cells to re-pull from WRDS/Compustat.
                             STATUS: financials complete 22/22; adoption /
                             crowding / margin-history passes pending.
2. compute_scores.py       — converts raw metrics -> rubric points via
                             percentile ranks; writes scoring_sheet_computed.csv
3. (manual)                — fill remaining signal columns after the adoption
                             and crowding data passes; PM sanity-check top names
4. score_portfolio.py      — validates, applies crowding penalty, builds
                             score-weighted portfolio -> portfolio.csv
5. backtest.py             — needs prices.csv (Date + adj close for portfolio
                             tickers, SPY, IYT, MOO, NVDA, MSFT, GOOGL, AMD,
                             AVGO, PLTR since 2024-01-02); outputs stats incl.
                             beta-to-AI-basket + backtest.png
rubric.yaml                — all decisions as config; edit here, code adapts.
scoring_sheet.csv          — blank discretionary template (kept for reference).

## Known integrity flags (be upfront in class)
- Approximated cells: AGCO/CNH/NTR/BG/ADM/FMC SG&A + gross profit; several
  headcounts. All flagged in data_sheet sources column.
- GXO & Ryder: labor not separable from direct costs -> automatability
  industry score carries their cost-structure ranking.
- Deere: SA&G excludes R&D ($2.2B); including it lifts DE 26%->38% on the
  value-added metric. Open team decision.
- Valuation data found via search is current-vintage until replaced with
  Jan-2024 WRDS numbers.
- 3-year AI sample; analog (cloud-era) backtest is the mechanism test.

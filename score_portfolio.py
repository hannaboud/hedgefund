"""
AI Shadow Beneficiaries Fund — scoring + portfolio construction.
Reads rubric.yaml (decisions) + scoring_sheet.csv (analyst scores).
Outputs composite scores and score-weighted portfolio weights.

Usage: python score_portfolio.py
"""
import sys
import pandas as pd
import yaml

RUBRIC_PATH = "rubric.yaml"
SHEET_PATH = "scoring_sheet.csv"
OUT_PATH = "portfolio.csv"


def load_rubric(path=RUBRIC_PATH):
    with open(path) as f:
        return yaml.safe_load(f)


def validate(df, rubric):
    """Fail loudly on missing scores or out-of-range points."""
    problems = []
    for crit, spec in rubric["criteria"].items():
        for sig, meta in spec["signals"].items():
            if sig not in df.columns:
                problems.append(f"Missing column: {sig}")
                continue
            bad = df[(df[sig] < 0) | (df[sig] > meta["max"])]
            for _, r in bad.iterrows():
                problems.append(f"{r.ticker}: {sig}={r[sig]} outside 0-{meta['max']}")
            missing = df[df[sig].isna()]
            for _, r in missing.iterrows():
                problems.append(f"{r.ticker}: {sig} not scored yet")
    no_src = df[df["evidence_sources_pre_2024"].isna()]
    for _, r in no_src.iterrows():
        problems.append(f"{r.ticker}: no pre-2024 evidence sources listed (lookahead firewall)")
    return problems


def composite_scores(df, rubric):
    df = df.copy()
    for crit, spec in rubric["criteria"].items():
        cols = list(spec["signals"].keys())
        df[crit] = df[cols].sum(axis=1)
    crit_cols = list(rubric["criteria"].keys())
    df["composite_raw"] = df[crit_cols].sum(axis=1)  # rubric sums to 100
    mult = rubric["crowding_penalty"]["multiplier"]
    df["composite"] = df["composite_raw"] * df["ai_priced"].fillna(0).map(
        lambda flag: mult if flag == 1 else 1.0
    )
    return df


def build_portfolio(df, rubric):
    p = rubric["portfolio"]
    qual = df[df["composite"] >= p["inclusion_threshold"]].copy()
    if qual.empty:
        print("No names met the inclusion threshold.")
        return qual
    qual["weight"] = qual["composite"] / qual["composite"].sum()
    # apply position cap iteratively, renormalizing the remainder
    cap = p["max_position"]
    for _ in range(20):
        over = qual["weight"] > cap + 1e-9
        if not over.any():
            break
        excess = (qual.loc[over, "weight"] - cap).sum()
        qual.loc[over, "weight"] = cap
        under = ~over
        if qual.loc[under, "weight"].sum() > 0:
            qual.loc[under, "weight"] += (
                excess * qual.loc[under, "weight"] / qual.loc[under, "weight"].sum()
            )
        else:
            break
    return qual.sort_values("weight", ascending=False)


def main():
    rubric = load_rubric()
    df = pd.read_csv(SHEET_PATH)
    problems = validate(df, rubric)
    if problems:
        print("SHEET INCOMPLETE — fix before trusting output:")
        for p in problems[:30]:
            print("  -", p)
        print(f"({len(problems)} issues total)\n")
    scored = composite_scores(df, rubric)
    cols = ["ticker", "company", "sector"] + list(rubric["criteria"].keys()) + [
        "composite_raw", "ai_priced", "composite"]
    print(scored[cols].sort_values("composite", ascending=False).to_string(index=False))
    port = build_portfolio(scored, rubric)
    if not port.empty:
        print("\n=== PORTFOLIO (formed", rubric["formation_date"], ") ===")
        print(port[["ticker", "company", "sector", "composite", "weight"]]
              .to_string(index=False, float_format=lambda x: f"{x:,.3f}"))
        port.to_csv(OUT_PATH, index=False)
        print(f"\nSaved -> {OUT_PATH}")


if __name__ == "__main__":
    main()

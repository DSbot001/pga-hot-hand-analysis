"""Ordered and multinomial logit for the next-hole outcome.

Reads the `analysis` view from pga_2025.sqlite and writes
results/ordinal_results.md.

Next-hole outcome (ordered, best to worst):
    0 eagle+   1 birdie   2 par   3 bogey   4 double+

Previous-hole state (reference = par): birdie+, par, bogey+

Controls:
    player_skill             player's average to_par in other events
    hole_diff                leave-one-out field mean to_par on the same
                             event x round x course x hole
    field_birdie, field_bogey  leave-one-out field share of birdie-or-better /
                             bogey-or-worse on that same hole. In 03_model.py,
                             hole fixed effects showed that a hole's average
                             is not enough: its birdie and bogey rates matter
                             too. Fixed effects are impractical in a logit, so
                             these shares stand in for them.

Models (SEs clustered by player):
    Ordered logit       one coefficient per previous state. A negative value
                        shifts the whole next-hole distribution toward better
                        scores (momentum). Assumes a parallel shift.
    Multinomial logit   separate coefficients for each outcome vs par. Allows
                        both birdie and bogey to rise together (a change in
                        variance or style), which the ordered model cannot.
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.miscmodels.ordinal_model import OrderedModel

DB = "pga_2025.sqlite"
OUT = Path("results")
OUT.mkdir(exist_ok=True)

LEVELS = ["eagle+", "birdie", "par", "bogey", "double+"]
PREV = ["birdie+", "par", "bogey+"]
CONTROLS = ["player_skill", "hole_diff", "field_birdie", "field_bogey"]


def load():
    with sqlite3.connect(DB) as con:
        df = pd.read_sql_query(
            """
            SELECT player_id, event_query, round, course_key, hole,
                   to_par, prev_to_par, hole_diff, player_skill
            FROM analysis
            """,
            con,
        )

    # Leave-one-out field shares per hole cell, computed on all players
    # (including holes 1 and 10) before dropping rows.
    cell = ["event_query", "round", "course_key", "hole"]
    df["is_birdie"] = (df.to_par <= -1).astype(float)
    df["is_bogey"] = (df.to_par >= 1).astype(float)
    g = df.groupby(cell)
    n = g.to_par.transform("size")
    df["field_birdie"] = (g.is_birdie.transform("sum") - df.is_birdie) / (n - 1)
    df["field_bogey"] = (g.is_bogey.transform("sum") - df.is_bogey) / (n - 1)

    df = df.dropna(subset=["prev_to_par", "player_skill"]).reset_index(drop=True)
    df["y"] = np.select(
        [df.to_par <= -2, df.to_par == -1, df.to_par == 0, df.to_par == 1],
        [0, 1, 2, 3], 4,
    )
    df["prev_cat"] = np.select(
        [df.prev_to_par <= -1, df.prev_to_par == 0], ["birdie+", "par"], "bogey+"
    )
    df["prev_birdie"] = (df.prev_cat == "birdie+").astype(float)
    df["prev_bogey"] = (df.prev_cat == "bogey+").astype(float)
    return df


def design(df, prev=None):
    """Regressors. If prev is given, set every row's previous state to it."""
    X = df[CONTROLS].copy()
    if prev is None:
        X.insert(0, "prev_bogey", df.prev_bogey)
        X.insert(0, "prev_birdie", df.prev_birdie)
    else:
        X.insert(0, "prev_bogey", float(prev == "bogey+"))
        X.insert(0, "prev_birdie", float(prev == "birdie+"))
    return X


def predicted_dist(predict, df):
    """Average predicted next-hole distribution for each previous state."""
    rows = {p: predict(design(df, p)).mean(axis=0) for p in PREV}
    return pd.DataFrame(rows, index=LEVELS).T.loc[PREV]


def main():
    df = load()
    clusters = df.player_id.to_numpy()

    # ---- Ordered logit -------------------------------------------------
    oy = pd.Series(pd.Categorical.from_codes(df.y, LEVELS, ordered=True))
    om = OrderedModel(oy, design(df), distr="logit")
    ores = om.fit(method="bfgs", maxiter=500, disp=False,
                  cov_type="cluster", cov_kwds={"groups": clusters})
    o_coef = pd.DataFrame({
        "coef": ores.params, "se": ores.bse,
        "odds_ratio": np.exp(ores.params), "p_value": ores.pvalues,
    }).loc[["prev_birdie", "prev_bogey"] + CONTROLS]
    o_pred = predicted_dist(lambda X: np.asarray(ores.model.predict(ores.params, exog=X)), df)

    # ---- Multinomial logit (base = par) --------------------------------
    # MNLogit uses the lowest code as base, so recode so par = 0.
    order = ["par", "eagle+", "birdie", "bogey", "double+"]
    my = df.y.map({2: 0, 0: 1, 1: 2, 3: 3, 4: 4})
    mm = sm.MNLogit(my, sm.add_constant(design(df)))
    mres = mm.fit(method="newton", maxiter=100, disp=False,
                  cov_type="cluster", cov_kwds={"groups": clusters})
    m_rows = []
    for j, outcome in enumerate(order[1:]):
        for v in ["prev_birdie", "prev_bogey"]:
            b, se = mres.params.loc[v, j], mres.bse.loc[v, j]
            m_rows.append({
                "outcome vs par": outcome, "previous hole": v.replace("prev_", "") + "+",
                "coef": b, "se": se, "rel_risk_ratio": np.exp(b),
                "p_value": mres.pvalues.loc[v, j],
            })
    m_coef = pd.DataFrame(m_rows)

    def m_predict(X):
        p = np.asarray(mres.predict(sm.add_constant(X, has_constant="add")))
        return p[:, [1, 2, 0, 3, 4]]  # back to eagle+, birdie, par, bogey, double+

    m_pred = predicted_dist(m_predict, df)

    # Change vs previous par, in percentage points
    def diff_pp(pred):
        return (pred.loc[["birdie+", "bogey+"]] - pred.loc["par"]) * 100

    observed = (pd.crosstab(df.prev_cat, pd.Categorical.from_codes(df.y, LEVELS),
                            normalize="index").loc[PREV])

    md = [
        "# Ordered and multinomial logit (2025 PGA TOUR)",
        "",
        f"Sample: {len(df):,} holes, {df.player_id.nunique():,} players. "
        "Next-hole outcome: eagle+ < birdie < par < bogey < double+. "
        "Previous hole reference: par. Controls: player_skill, hole_diff, "
        "field_birdie, field_bogey. SEs clustered by player.",
        "",
        "## 0. Observed transition matrix (no controls)",
        "",
        "Rows: previous hole. Columns: share of next-hole outcomes.",
        "",
        observed.to_markdown(floatfmt=".4f"),
        "",
        "## 1. Ordered logit",
        "",
        "Positive coef = shift toward worse scores. Odds ratio > 1 = higher odds "
        "of a worse category.",
        "",
        o_coef.to_markdown(floatfmt=".4f"),
        "",
        "Adjusted next-hole distribution:",
        "",
        o_pred.to_markdown(floatfmt=".4f"),
        "",
        "Change vs previous par (percentage points):",
        "",
        diff_pp(o_pred).to_markdown(floatfmt=".3f"),
        "",
        "## 2. Multinomial logit (base outcome = par)",
        "",
        "rel_risk_ratio > 1 = that outcome becomes more likely relative to par.",
        "",
        m_coef.to_markdown(index=False, floatfmt=".4f"),
        "",
        "Adjusted next-hole distribution:",
        "",
        m_pred.to_markdown(floatfmt=".4f"),
        "",
        "Change vs previous par (percentage points):",
        "",
        diff_pp(m_pred).to_markdown(floatfmt=".3f"),
        "",
        "## Fit",
        "",
        f"Ordered logit: log-likelihood {ores.llf:,.1f}, {len(ores.params)} parameters, "
        f"AIC {ores.aic:,.1f}",
        "",
        f"Multinomial logit: log-likelihood {mres.llf:,.1f}, {mres.params.size} parameters, "
        f"AIC {mres.aic:,.1f}",
        "",
    ]
    (OUT / "ordinal_results.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()

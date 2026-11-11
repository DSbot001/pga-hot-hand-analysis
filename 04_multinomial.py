"""Multinomial logit for the next-hole outcome.

Reads the `analysis` view from pga_2025.sqlite; writes CSV tables to results/
for pga_hot_hand_report.qmd.

Outcome:  0 eagle+  1 birdie  2 par  3 bogey  4 double+
Previous hole (ref = par):  birdie+, par, bogey+

Controls:
    player_skill   strokes gained per hole in other events
    hole_diff      leave-one-out field mean to_par, same event x round x
                   course proxy x hole
    field_birdie,  leave-one-out field share of birdie+ / bogey+ on that hole;
    field_bogey    together with hole_diff they stand in for hole fixed
                   effects, which are impractical in a logit. Two holes with
                   the same average can still differ in how often they give
                   up birdies and bogeys.

Multinomial logit with player-clustered SEs: each outcome gets its own
coefficients vs par, so birdies and bogeys can rise together (a variance /
style shift), not just move in one direction.
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

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
                   to_par, prev_cat, hole_diff, player_skill
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

    df = df.dropna(subset=["prev_cat", "player_skill"]).reset_index(drop=True)
    df["y"] = np.select(
        [df.to_par <= -2, df.to_par == -1, df.to_par == 0, df.to_par == 1],
        [0, 1, 2, 3], 4,
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

    # Multinomial logit (base = par). MNLogit uses the lowest code as base,
    # so recode to par 0, eagle+ 1, birdie 2, bogey 3, double+ 4.
    my = df.y.map({2: 0, 0: 1, 1: 2, 3: 3, 4: 4})
    mm = sm.MNLogit(my, sm.add_constant(design(df)))
    mres = mm.fit(method="newton", maxiter=100, disp=False,
                  cov_type="cluster", cov_kwds={"groups": clusters})

    def m_predict(X):
        p = np.asarray(mres.predict(sm.add_constant(X, has_constant="add")))
        return p[:, [1, 2, 0, 3, 4]]  # back to eagle+, birdie, par, bogey, double+

    m_pred = predicted_dist(m_predict, df)

    # Change vs previous par, in percentage points
    def diff_pp(pred):
        return (pred.loc[["birdie+", "bogey+"]] - pred.loc["par"]) * 100

    # Formal tests 
    # Wald tests on the multinomial coefficients with player-clustered SEs.

    names = list(mres.cov_params().index)

    def wald(vars_):
        idx = [i for i, (_, v) in enumerate(names) if v in vars_]
        R = np.zeros((len(idx), len(names)))
        R[np.arange(len(idx)), idx] = 1
        w = mres.wald_test(R, scalar=True)
        return {"df": len(idx), "chi2": float(w.statistic), "p_value": float(w.pvalue)}

    tests = pd.DataFrame({
        "H0: previous hole has no effect on any outcome": wald(["prev_birdie", "prev_bogey"]),
        "H0: previous birdie+ has no effect": wald(["prev_birdie"]),
        "H0: previous bogey+ has no effect": wald(["prev_bogey"]),
    }).T

    # CSVs read by the Results section of pga_hot_hand_report.qmd
    diff_pp(m_pred).to_csv(OUT / "multinomial_change_pp.csv", index_label="previous_hole")
    tests.to_csv(OUT / "wald_tests.csv", index_label="hypothesis")


if __name__ == "__main__":
    main()

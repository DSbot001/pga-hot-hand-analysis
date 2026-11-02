"""Next-hole analysis: does the previous hole's result predict the next one?

Reads the `analysis` view from pga_2025.sqlite (built by 02_build_database.R)
and writes results/model_results.md.

Previous-hole state (prev_cat), reference = par:
    birdie+  previous hole birdie or better (to_par <= -1)
    par      previous hole par
    bogey+   previous hole bogey or worse (to_par >= 1)

Outcomes on the next hole:
    to_par       strokes relative to par
    birdie_next  1 if birdie or better
    bogey_next   1 if bogey or worse

Models (OLS, linear probability for the 0/1 outcomes, SEs clustered by player):
    A. outcome ~ prev_cat + hole_diff + player_skill
    B. same, with player fixed effects instead of player_skill
       (robustness: absorbs all stable differences between players)
    C. hole fixed effects (event x round x course x hole) + player_skill.
       hole_diff only controls a hole's average score. For the 0/1 outcomes
       a hole's birdie and bogey rates matter too, and those depend on
       course layout (which hole follows which). The fixed effect compares
       players on the exact same hole in the same round. This is the
       strictest spec and the one to trust most.
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

DB = "pga_2025.sqlite"
OUT = Path("results")
OUT.mkdir(exist_ok=True)

OUTCOMES = {
    "to_par": "Next-hole to_par",
    "birdie_next": "P(birdie or better next)",
    "bogey_next": "P(bogey or worse next)",
}
CATS = ["birdie+", "par", "bogey+"]


def load():
    with sqlite3.connect(DB) as con:
        df = pd.read_sql_query(
            """
            SELECT player_id, event_query, round, course_key, hole, par, to_par,
                   prev_to_par, hole_diff, player_skill
            FROM analysis
            WHERE prev_to_par IS NOT NULL
            """,
            con,
        )
    df["prev_cat"] = np.select(
        [df.prev_to_par <= -1, df.prev_to_par == 0], ["birdie+", "par"], "bogey+"
    )
    df["prev_detail"] = pd.cut(
        df.prev_to_par,
        [-np.inf, -2, -1, 0, 1, np.inf],
        labels=["eagle+", "birdie", "par", "bogey", "double+"],
    )
    df["birdie_next"] = (df.to_par <= -1).astype(int)
    df["bogey_next"] = (df.to_par >= 1).astype(int)
    return df


def raw_table(df, by):
    t = df.groupby(by, observed=True).agg(
        n=("to_par", "size"),
        mean_to_par=("to_par", "mean"),
        p_birdie_next=("birdie_next", "mean"),
        p_bogey_next=("bogey_next", "mean"),
        mean_hole_diff=("hole_diff", "mean"),
        mean_player_skill=("player_skill", "mean"),
    )
    return t.round(4)


def fit(df, y, controls):
    f = f"{y} ~ C(prev_cat, Treatment('par')) + {controls}"
    return smf.ols(f, data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df.player_id}
    )


def fit_fe(df, y, groups, control):
    """One-way fixed effects via within-group demeaning."""
    d = pd.DataFrame({
        "y": df[y],
        "birdie": (df.prev_cat == "birdie+").astype(float),
        "bogey": (df.prev_cat == "bogey+").astype(float),
        control: df[control],
    })
    d = d - d.groupby(groups).transform("mean")
    return smf.ols(f"y ~ 0 + birdie + bogey + {control}", data=d).fit(
        cov_type="cluster", cov_kwds={"groups": df.player_id}
    )


def row(model, name, label, outcome, spec):
    est, se = model.params[name], model.bse[name]
    return {
        "outcome": outcome, "spec": spec, "previous hole": label,
        "estimate": est, "se": se,
        "ci_low": est - 1.96 * se, "ci_high": est + 1.96 * se,
        "p_value": model.pvalues[name],
    }


def main():
    df = load()
    main_df = df.dropna(subset=["player_skill"])  # needs >= 2 events

    rows, preds = [], []
    for y, label in OUTCOMES.items():
        m = fit(main_df, y, "hole_diff + player_skill")
        for cat, nm in [("birdie+", "C(prev_cat, Treatment('par'))[T.birdie+]"),
                        ("bogey+", "C(prev_cat, Treatment('par'))[T.bogey+]")]:
            rows.append(row(m, nm, cat, label, "A: controls"))

        # Adjusted levels: everyone's controls held at their actual values,
        # previous-hole state switched to each category in turn.
        for cat in CATS:
            p = m.predict(main_df.assign(prev_cat=cat)).mean()
            preds.append({"outcome": label, "previous hole": cat, "adjusted mean": p})

        fe = fit_fe(df, y, df.player_id, "hole_diff")
        rows.append(row(fe, "birdie", "birdie+", label, "B: player FE"))
        rows.append(row(fe, "bogey", "bogey+", label, "B: player FE"))

        hole_cell = (main_df.event_query + "|" + main_df["round"].astype(str) + "|"
                     + main_df.course_key + "|" + main_df.hole.astype(str))
        hfe = fit_fe(main_df, y, hole_cell, "player_skill")
        rows.append(row(hfe, "birdie", "birdie+", label, "C: hole FE"))
        rows.append(row(hfe, "bogey", "bogey+", label, "C: hole FE"))

    effects = pd.DataFrame(rows)
    adjusted = pd.DataFrame(preds).pivot(
        index="previous hole", columns="outcome", values="adjusted mean"
    ).loc[CATS, list(OUTCOMES.values())]

    raw3 = raw_table(df, "prev_cat").loc[CATS]
    raw5 = raw_table(df, "prev_detail")

    fmt = lambda x: f"{x:.4f}"
    md = [
        "# Next-hole results (2025 PGA TOUR)",
        "",
        f"Sample: {len(df):,} holes with a previous hole "
        f"({df.player_id.nunique():,} players, {df.event_query.nunique()} events). "
        f"Model A uses the {len(main_df):,} with `player_skill` available.",
        "",
        "## 1. Raw next-hole outcomes by previous hole",
        "",
        raw3.to_markdown(),
        "",
        "Finer split:",
        "",
        raw5.to_markdown(),
        "",
        "## 2. Effects relative to a previous par (OLS, player-clustered SEs)",
        "",
        "A = controls for `hole_diff` and `player_skill`. "
        "B = player fixed effects + `hole_diff`. "
        "C = hole fixed effects (event x round x course x hole) + `player_skill` "
        "(strictest, preferred). "
        "Probability estimates are proportions: -0.0084 = -0.84 percentage points.",
        "",
        effects.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## 3. Adjusted next-hole levels (model A)",
        "",
        adjusted.to_markdown(floatfmt=".4f"),
        "",
    ]
    (OUT / "model_results.md").write_text("\n".join(md))
    effects.to_csv(OUT / "effects.csv", index=False)
    print("\n".join(md))


if __name__ == "__main__":
    main()

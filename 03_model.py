"""Next-hole analysis: does the previous hole's result predict the next one?

Reads the `analysis` view from pga_2025.sqlite (built by 02_build_database.R)
and writes results/model_results.md and results/effects.csv.

Previous-hole state (prev_cat), reference = par:
    birdie+  previous hole birdie or better (to_par <= -1)
    par      previous hole par
    bogey+   previous hole bogey or worse (to_par >= 1)

Outcomes on the next hole:
    to_par       strokes relative to par
    birdie_next  1 if birdie or better
    bogey_next   1 if bogey or worse

Model (OLS, linear probability for the 0/1 outcomes, SEs clustered by player):

    outcome ~ prev_cat + hole fixed effects + player_skill

    Hole fixed effects (one per event x round x course proxy x hole) compare
    players on the exact same hole in the same round, so they control the
    hole's average score and also its birdie and bogey rates.
    player_skill is strokes gained per hole in the player's other events
    (see analysis.sql). It is measured outside the current event, so it does
    not contain the scores being modeled.

    Player fixed effects are not used. With a lagged outcome they bias the
    previous-hole coefficients downward, most for players with few events.
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


def fit_main(df, y, hole_cell):
    """Hole fixed effects (within-hole demeaning) + player_skill."""
    d = pd.DataFrame({
        "y": df[y],
        "birdie": (df.prev_cat == "birdie+").astype(float),
        "bogey": (df.prev_cat == "bogey+").astype(float),
        "player_skill": df.player_skill,
    })
    d = d - d.groupby(hole_cell).transform("mean")
    return smf.ols("y ~ 0 + birdie + bogey + player_skill", data=d).fit(
        cov_type="cluster", cov_kwds={"groups": df.player_id}
    )


def row(model, name, label, outcome):
    est, se = model.params[name], model.bse[name]
    return {
        "outcome": outcome, "previous hole": label,
        "estimate": est, "se": se,
        "ci_low": est - 1.96 * se, "ci_high": est + 1.96 * se,
        "p_value": model.pvalues[name],
    }


def main():
    df = load()
    model_df = df.dropna(subset=["player_skill"])  # needs >= 2 events
    hole_cell = model_df.groupby(
        ["event_query", "round", "course_key", "hole"], sort=False
    ).ngroup()

    rows = []
    for y, label in OUTCOMES.items():
        m = fit_main(model_df, y, hole_cell)
        rows.append(row(m, "birdie", "birdie+", label))
        rows.append(row(m, "bogey", "bogey+", label))
        rows.append(row(m, "player_skill", "player_skill", label))
    effects = pd.DataFrame(rows)

    raw3 = raw_table(df, "prev_cat").loc[CATS]
    raw5 = raw_table(df, "prev_detail")

    md = [
        "# Next-hole results (2025 PGA TOUR)",
        "",
        f"Sample: {len(df):,} holes with a previous hole "
        f"({df.player_id.nunique():,} players, {df.event_query.nunique()} events). "
        f"The model uses the {len(model_df):,} holes with `player_skill` available "
        f"({model_df.player_id.nunique():,} players who played at least two events).",
        "",
        "## 1. Raw next-hole outcomes by previous hole",
        "",
        raw3.to_markdown(),
        "",
        "Finer split:",
        "",
        raw5.to_markdown(),
        "",
        "## 2. Effects relative to a previous par",
        "",
        "OLS with hole fixed effects (event x round x course proxy x hole) and "
        "`player_skill` (strokes gained per hole in the player's other events). "
        "Standard errors are clustered by player. "
        "Probability estimates are proportions: -0.0084 = -0.84 percentage points. "
        "The `player_skill` rows show the effect of one stroke gained per hole.",
        "",
        effects.to_markdown(index=False, floatfmt=".4f"),
        "",
    ]
    (OUT / "model_results.md").write_text("\n".join(md))
    effects.to_csv(OUT / "effects.csv", index=False)
    print("\n".join(md))


if __name__ == "__main__":
    main()

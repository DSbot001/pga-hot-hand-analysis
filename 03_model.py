"""Next-hole model: does the previous hole's result predict the next one?

Input:  `analysis` view in pga_2025.sqlite (built by 02_build_database.R)
Output: results/effects.csv, results/skill_robustness.csv
        (read by PGA Tour Project.qmd)

Model (OLS, linear probability for the 0/1 outcomes):
    outcome ~ prev_cat + hole fixed effects + player_skill
    Hole = event x round x course proxy x hole. SEs clustered by player.
    No player fixed effects: with a lagged outcome they bias the estimates.
    See the report for details.
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


def load():
    with sqlite3.connect(DB) as con:
        df = pd.read_sql_query(
            """
            SELECT player_id, event_query, round, course_key, hole, to_par,
                   prev_to_par, player_skill
            FROM analysis
            WHERE prev_to_par IS NOT NULL
            """,
            con,
        )
    df["prev_cat"] = np.select(
        [df.prev_to_par <= -1, df.prev_to_par == 0], ["birdie+", "par"], "bogey+"
    )
    df["birdie_next"] = (df.to_par <= -1).astype(int)
    df["bogey_next"] = (df.to_par >= 1).astype(int)
    return df


def fit_main(df, y, hole_cell, controls=("player_skill",)):
    """Hole fixed effects (within-hole demeaning) + controls."""
    d = pd.DataFrame({
        "y": df[y],
        "birdie": (df.prev_cat == "birdie+").astype(float),
        "bogey": (df.prev_cat == "bogey+").astype(float),
    })
    for c in controls:
        d[c] = df[c]
    d = d - d.groupby(hole_cell).transform("mean")
    return smf.ols("y ~ 0 + birdie + bogey + " + " + ".join(controls), data=d).fit(
        cov_type="cluster", cov_kwds={"groups": df.player_id}
    )


def row(model, name, label, outcome):
    """One coefficient with its SE, 95% confidence interval (est ± 1.96 SE)
    and p-value."""
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

    effects.to_csv(OUT / "effects.csv", index=False)

    # Robustness: player_skill is noisier for players with few events, which
    # shrinks its coefficient toward zero. Refit to_par keeping only players
    # with at least k events and check if the momentum estimates change.
    # First row (k = 1): add back one-event players, with player_skill set to 0
    # and a one_event indicator that estimates their average level.
    full = df.assign(one_event=df.player_skill.isna().astype(float),
                     player_skill=df.player_skill.fillna(0))
    cell = full.groupby(["event_query", "round", "course_key", "hole"], sort=False).ngroup()
    r = fit_main(full, "to_par", cell, ("player_skill", "one_event"))
    
    robust = [{
        "min events": 1, "players": full.player_id.nunique(), "holes": len(full),
        "player_skill": r.params["player_skill"],
        "birdie+": r.params["birdie"], "bogey+": r.params["bogey"],
        "one_event": r.params["one_event"],
    }]
    n_events = model_df.groupby("player_id").event_query.transform("nunique")
    for k in [2, 5, 10, 15, 20]:
        d = model_df[n_events >= k]
        cell = d.groupby(["event_query", "round", "course_key", "hole"], sort=False).ngroup()
        r = fit_main(d, "to_par", cell)
        robust.append({
            "min events": k, "players": d.player_id.nunique(), "holes": len(d),
            "player_skill": r.params["player_skill"],
            "birdie+": r.params["birdie"], "bogey+": r.params["bogey"],
        })
    pd.DataFrame(robust).to_csv(OUT / "skill_robustness.csv", index=False)


if __name__ == "__main__":
    main()

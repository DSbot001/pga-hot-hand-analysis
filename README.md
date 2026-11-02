# PGA Tour Momentum

Does a birdie carry over? This project asks whether making **birdie or better
on one hole is associated with a better score on the next hole**, after
accounting for player ability and hole difficulty. It uses 2025 PGA TOUR
hole-by-hole data.

Pipeline: **R** (download with the `golfastr` package) → **SQLite / SQL**
(cleaning and features) → **Python** (modeling, next step).

## Files

| File | What it does |
|---|---|
| `00_check_seasons.R` | Probes 2015–2026 to see which seasons golfastr has hole data for (for future multi-season work). Not needed for the main pipeline. |
| `01_download.R` | Downloads every 2025 event with `load_holes()` and saves the list to `holes_2025_raw.rds`. Optional, since the `.rds` is already in the repo. |
| `holes_2025_raw.rds` | Raw data: a list of 49 events (the Ryder Cup returned nothing). One row = one player, one hole, one round. |
| `02_build_database.R` | Loads the `.rds` into `pga_2025.sqlite` as table `all_holes`, then runs `analysis.sql`. |
| `analysis.sql` | Builds the cleaning and feature views (see below). |
| `03_model.py` | Python models: next-hole `to_par`, P(birdie+), and P(bogey+) after a birdie+, par, or bogey+, with three control specs. Writes `results/model_results.md`. |
| `04_ordinal.py` | Ordered and multinomial logit for the full next-hole outcome (eagle+ / birdie / par / bogey / double+), with field birdie and bogey rates as hole controls. Writes `results/ordinal_results.md`. |
| `PGA Tour Project.qmd` | Full report: research question, data checks, results, and conclusion. |

`pga_2025.sqlite` is generated locally and is git-ignored.

## How to run

Open `PGA-Tour-Project.Rproj` in RStudio and install `DBI`, `RSQLite`, and `dplyr`
if needed. Then:

```r
source("02_build_database.R")   # builds pga_2025.sqlite
```

Then run the models (needs `pandas`, `statsmodels`, `tabulate`), which write their tables to `results/`:

```bash
python 03_model.py
python 04_ordinal.py   # about 1 minute
```

Finally, render `PGA Tour Project.qmd`. It has the data checks plus a Results and Conclusion section that reads the tables in `results/`.

Read the features from Python:

```python
import sqlite3
import pandas as pd

with sqlite3.connect("pga_2025.sqlite") as con:
    analysis = pd.read_sql_query("SELECT * FROM analysis", con)
```

## SQL views (`analysis.sql`)

1. **`clean`**: drops 4 events. The Zurich Classic is a team event, Q-School is
   a qualifier, and the Hero World Challenge is an unofficial invitational. The
   Barracuda Championship is scored in Stableford, so golfastr's `score` holds
   points, not strokes.
2. **`complete_rounds`**: keeps rounds 1–4 with exactly 18 rows per player-round.
   Round 5 is playoff holes.
3. **`round_courses`**: `course_key` is the 18-hole par sequence. It is a proxy
   that separates multi-course events (Pebble Beach, Farmers, AmEx, RSM).
4. **`scored_holes`**: `to_par = score - par` and `nine` (front or back).
5. **`lagged_holes`**: `prev_to_par`, the previous hole within the same nine.
   Holes 1 and 10 have none.
6. **`analysis`**: final modeling table.

| Column | Meaning |
|---|---|
| `to_par` | Outcome: strokes relative to par on this hole |
| `prev_birdie` | 1 if the previous hole was birdie or better, 0 otherwise, NULL on holes 1 and 10 |
| `hole_diff` | Leave-one-out field average `to_par` on the same event, round, course, and hole (lower = easier) |
| `player_skill` | The player's average `to_par` in *other* events (lower = better). NULL if he played only one event |

Current sample: 44 events and 303,786 player-holes, of which about 270k have a
previous hole.

## Known limitations

- `course_key` can, in principle, match two different courses with the same par sequence.
- Hole number is not always playing order (for example, two-tee starts). Resetting at
  hole 10 avoids linking the two nines but drops those transitions.
- `player_skill` is a simple average, not a full ability model.

## Findings so far

- **No hot hand in scoring**: the previous hole does not change the expected next-hole score.
- **A small style effect**: after a birdie the next hole is slightly more likely to be a par
  (fewer birdies *and* fewer bogeys). After a bogey it is slightly less likely (more of both).
  Each shift is under 1 percentage point.

## Status

- [x] Data download, cleaning, and features
- [x] Data quality checks (round completeness, course proxies, score labels)
- [x] First models (`03_model.py`): no momentum in average score. Small variance-type
  effects mostly disappear with hole fixed effects (see `results/model_results.md`)
- [x] Ordered and multinomial logit (`04_ordinal.py`): no overall shift. Formal tests (clustered
  Wald tests, plus P(par) with hole fixed effects) show a small but significant style effect: next-hole
  par is about +0.6 pp more likely after a birdie+ (p = 0.03) and about 0.6 pp less likely after a bogey+ (p = 0.02)
- [ ] Streaks (last k holes), player heterogeneity, hidden Markov model
- [ ] Extend to more seasons (see `00_check_seasons.R`)

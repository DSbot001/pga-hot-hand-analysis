# PGA Hot Hand Analysis

Does playing well on one hole help a golfer play better on the next?

In the world of golf, players often feel that one good hole can build confidence and lead to another. As both an NCAA Division I golfer and a data science student, I wanted to see whether this “hot hand” feeling shows up in the data, or whether apparent streaks can be explained by player ability and hole difficulty.

The project uses 2025 PGA TOUR hole-by-hole data retrieved through the R package golfastr. It tests whether scoring a birdie or better, meaning completing a hole in fewer strokes than par, is associated with a better score on the next hole after accounting for those differences.

## Pipeline

The workflow starts in **R**, using the `golfastr` package to download the golf data. The data is then stored in a **SQLite** database, where **SQL** cleans the records and creates the variables used in the analysis. **Python** fits the statistical models and saves the results for the final report.

## Files

The numbered scripts follow the main workflow, from creating database to fitting the models. The saved raw data is included, so you can start with `02_build_database.R` without downloading it again.

| File | Purpose |
|---|---|
| `01_download.R` | Uses `golfastr` to download the 2025 tournament data and save it as an R data file. |
| `holes_2025_raw.rds` | Contains the downloaded data. Each hole record represents one player’s score on one hole in one round. |
| `02_build_database.R` | Combines the downloaded tournament data, loads it into SQLite, and runs `analysis.sql` to prepare the analysis dataset. |
| `analysis.sql` | Excludes unsuitable events, keeps complete rounds, links each hole to the previous hole, and calculates measures of player ability and hole difficulty. |
| `03_model.py` | Tests whether the previous hole’s result predicts the next hole’s score or the probability of a birdie or bogey. Compares several ways of accounting for player and hole differences. |
| `04_ordinal.py` | Examines all five next-hole score categories together and tests whether the previous result changes the overall distribution or the chance of making par. |
| `results/` | Stores the model results as readable summaries and CSV tables used by the report. |
| `PGA Tour Project.qmd` | Contains the full report, including the research background, data checks, model results, and conclusions. Renders to HTML. |
| `PGA-Tour-Project.Rproj` | Opens the project in RStudio so the scripts run from the correct folder. |

Running `02_build_database.R` creates `pga_2025.sqlite` locally. This generated database is excluded from Git because it can be rebuilt from the saved raw data and SQL script.


## How to run

Run the steps below from the project folder. The raw data is already included, so there is no need to download it again.

You will need R with `DBI`, `RSQLite`, and `dplyr`, Python with `numpy`, `pandas`, `statsmodels`, and `tabulate`, and Quarto to render the report.

### 1. Build the database

Run in R to load the saved data and prepare the analysis variables.

```r
source("02_build_database.R")
```

This creates `pga_2025.sqlite`.

### 2. Run the models

Run in a terminal to fit the models and save their results in `results/`.

```bash
python 03_model.py
python 04_ordinal.py
```

### 3. Render the report

Run in a terminal to generate the HTML report using the saved results.

```bash
quarto render "PGA Tour Project.qmd"
```

To download a fresh copy of the raw data, install the R package `golfastr` and run `01_download.R` before these steps.



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

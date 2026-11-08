# PGA Hot Hand Analysis

Does playing well on one hole help a golfer play better on the next?

In the world of golf, players often feel that one good hole can build confidence and lead to another. As both an NCAA Division I golfer and a data science student, I wanted to see whether this “hot hand” feeling shows up in the data, or whether apparent streaks can be explained by player ability and hole difficulty.

The project uses 2025 PGA TOUR hole-by-hole data retrieved through the R package golfastr. It tests whether scoring a birdie or better, meaning completing a hole in fewer strokes than par, is associated with a better score on the next hole after accounting for those differences.

## Pipeline

- **R** downloads the tournament data with `golfastr` and loads the saved records into SQLite.
- **SQL** cleans the records and creates the variables used in the analysis.
- **Python** fits the statistical models and saves the results for the final report.

## Files

The numbered scripts follow the main workflow, from creating database to fitting the models. The saved raw data is included, so you can start with `02_build_database.R` without downloading it again.

| File | Purpose |
|---|---|
| `01_download.R` | Uses `golfastr` to download the 2025 tournament data and save it as an R data file. |
| `holes_2025_raw.rds` | Contains the downloaded data. Each hole record represents one player’s score on one hole in one round. |
| `02_build_database.R` | Combines the downloaded tournament data, loads it into SQLite, and runs `analysis.sql` to prepare the analysis dataset. |
| `analysis.sql` | Excludes unsuitable events, keeps complete rounds, links each hole to the previous hole, and calculates measures of player ability and hole difficulty. |
| `03_model.py` | Tests whether the previous hole’s result predicts the next hole’s score or the probability of a birdie or bogey. Compares several ways of accounting for player and hole differences. |
| `04_multinomial.py` | Examines all five next-hole score categories together and tests whether the previous result changes the mix of outcomes or the chance of making par. |
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
python 04_multinomial.py
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
6. **`field_totals`**: number of players and summed `to_par` on each hole
   (event, round, course proxy, hole).
7. **`strokes_gained`**: `hole_diff`, the other players' average `to_par` on the
   same hole; `sg = hole_diff - to_par`, strokes gained on the hole; and each
   player's season and per-event strokes gained totals.
8. **`analysis`**: final modeling table. Adds `player_skill`, average strokes
   gained per hole in the player's other events.


## Variables

The key variables in the `analysis` view are listed below. Each row represents one player's score on one hole in one tournament round.

| Variable | Definition | How to interpret it |
|---|---|---|
| `score` | The player's recorded number of strokes on the current hole. | Compare with `par` to calculate the score relative to par. |
| `par` | The reference number of strokes for the current hole. | A score below par is better than par. |
| `to_par` | `score - par` on the current hole. | Lower is better. A birdie is -1, par is 0, and a bogey is +1. |
| `prev_to_par` | The player's `to_par` on the preceding hole within the same nine. | Lower means a better previous-hole result. Missing on holes 1 and 10. |
| `prev_birdie` | An indicator for whether `prev_to_par` is -1 or lower. | 1 means birdie or better, including eagles. 0 means par or worse. Missing on holes 1 and 10. |
| `hole_diff` | The average `to_par` of the other players in the analysis sample on the same event, round, course proxy, and hole. The current player's score is excluded. | Higher means harder relative to par. Negative values mean the other players averaged below par, and positive values mean they averaged above par. Missing if no other player is available for comparison. |
| `player_skill` | The player's strokes gained per hole in their other included events, where strokes gained on a hole is `hole_diff - to_par`. The entire current event is excluded. | Higher is better: strokes better than the field per hole. Missing if the player has no observations in other included events. |
| `course_key` | The sequence of pars for holes 1 through 18 in a player-round. | A proxy used to distinguish courses within an event, not a guaranteed unique course identifier. |
| `nine` | The group of nine holes containing the current hole. | 1 for holes 1-9 and 2 for holes 10-18. Previous-hole comparisons do not cross between these groups. |

For example, `player_skill = +0.10` means the player beat the field by 0.10 strokes per hole in his other events. A `hole_diff` of `+0.30` indicates a harder hole relative to par than `-0.30`.

Current sample: 44 events and 303,786 player-holes, of which about 270k have a
previous hole.

## Known limitations

- `course_key` can, in principle, match two different courses with the same par sequence.
- Hole number is not always playing order (for example, two-tee starts). Resetting at
  hole 10 avoids linking the two nines but drops those transitions.
- `player_skill` is strokes gained from other events. It does not capture form that changes during the season.

## Findings so far

- **No hot hand in scoring**: the previous hole does not change the expected next-hole score.
- **A small style effect**: after a birdie the next hole is slightly more likely to be a par
  (fewer birdies *and* fewer bogeys). After a bogey it is slightly less likely (more of both).
  Each shift is under 1 percentage point.

## Status

- [x] Data download, cleaning, and features
- [x] Data quality checks (round completeness, course proxies, score labels)
- [x] Main model (`03_model.py`): hole fixed effects + strokes-gained `player_skill`. No momentum in
  average score or in birdie/bogey chances (see `results/effects.csv`). Player fixed effects
  are not used because they bias lagged-outcome estimates downward.
- [x] Multinomial logit (`04_multinomial.py`). Formal tests (clustered
  Wald tests, plus P(par) with hole fixed effects) show a small but significant style effect: next-hole
  par is about +0.6 pp more likely after a birdie+ (p = 0.03) and about 0.6 pp less likely after a bogey+ (p = 0.02)
- [ ] Player heterogeneity, hidden Markov model


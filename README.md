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
| `03_model.py` | Main model. Tests whether the previous hole’s result predicts the next hole’s score or the probability of a birdie or bogey, using hole fixed effects and `player_skill`. Also runs the robustness check on the skill measure. |
| `04_multinomial.py` | Examines all five next-hole score categories together and tests whether the previous result changes the mix of outcomes. |
| `results/` | Stores the model results as CSV tables read by the report. |
| `PGA Tour Project.qmd` | Contains the full report, including the research background, data checks, model results, and conclusions. Renders to HTML. |
| `PGA-Tour-Project.Rproj` | Opens the project in RStudio so the scripts run from the correct folder. |

Running `02_build_database.R` creates `pga_2025.sqlite` locally. This generated database is excluded from Git because it can be rebuilt from the saved raw data and SQL script.


## How to run

Run the steps below from the project folder. The raw data is already included, so there is no need to download it again.

You will need R with `DBI`, `RSQLite`, and `dplyr`, Python with `numpy`, `pandas`, and `statsmodels`, and Quarto to render the report.

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


## Models

**Main model (`03_model.py`).** For each next-hole outcome (strokes relative to par,
birdie or better, bogey or worse), an OLS regression with hole fixed effects:

    outcome ~ birdie+_prev + bogey+_prev + hole fixed effects + player_skill

- **Hole fixed effects** (event × round × course proxy × hole) compare players on the
  exact same hole in the same round, controlling for its difficulty.
- **`player_skill`** controls for ability, measured from the player's other events.
- A previous par is the reference, and standard errors are clustered by player.
- Player fixed effects are not used: with a lagged outcome they bias the
  previous-hole estimates downward, most for players with few events.

**Robustness check (`03_model.py`).** Refits the main model keeping only players with
at least 2, 5, 10, 15, or 20 events, and once adding back one-event players with an
indicator.

**Multinomial logit (`04_multinomial.py`).** Models all five next-hole results
(eagle or better, birdie, par, bogey, double bogey or worse) at once, with the hole's
field average, birdie rate, and bogey rate plus `player_skill` as controls. Clustered
Wald tests check whether the previous hole changes the mix of outcomes.



## Conclusions

- **No hot hand.** After accounting for hole difficulty and player skill, the next-hole score
  after a birdie or better differs from the score after a par by less than 0.002 strokes, and no
  change in birdie or bogey chances is statistically significant.
- **A small change in style.** After a birdie, players seem to play slightly safer and make
  about 0.8 percentage points more pars. After a bogey, they seem to play more aggressively,
  with fewer pars and more birdies and bogeys. The shift is significant (Wald p < 0.01) but
  small, and scores alone cannot show what players intended.

## Limitations

- One season of PGA TOUR data. Results could differ in other years, on other tours, or at
  amateur and college levels.
- `course_key` (the par sequence) is only a proxy for the course, and hole number is not always
  playing order. Transitions between the two nines are not used.
- `player_skill` is estimated from a limited number of holes, so it contains noise and misses
  changes in form during the season. Players with only one event enter only the robustness check.
- Only the previous hole is considered, not longer streaks.
- Confidence, feel, and how well a player is striking the ball that day cannot be measured from
  scores, so the results describe an association between consecutive holes, not the effect of
  the previous hole alone.

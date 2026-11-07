# Next-hole results (2025 PGA TOUR)

Sample: 270,032 holes with a previous hole (692 players, 44 events). The model uses the 256,992 holes with `player_skill` available (354 players who played at least two events).

## 1. Raw next-hole outcomes by previous hole

| prev_cat   |      n |   mean_to_par |   p_birdie_next |   p_bogey_next |   mean_hole_diff |   mean_player_skill |
|:-----------|-------:|--------------:|----------------:|---------------:|-----------------:|--------------------:|
| birdie+    |  58101 |       -0.0406 |          0.2087 |         0.155  |          -0.0349 |              0.0061 |
| par        | 168598 |       -0.0446 |          0.2212 |         0.1613 |          -0.0446 |              0.0041 |
| bogey+     |  43333 |       -0.016  |          0.2149 |         0.1791 |          -0.0236 |              0.0003 |

Finer split:

| prev_detail   |      n |   mean_to_par |   p_birdie_next |   p_bogey_next |   mean_hole_diff |   mean_player_skill |
|:--------------|-------:|--------------:|----------------:|---------------:|-----------------:|--------------------:|
| eagle+        |   1477 |       -0.0034 |          0.1808 |         0.1584 |          -0.0113 |              0.0072 |
| birdie        |  56624 |       -0.0415 |          0.2094 |         0.1549 |          -0.0355 |              0.0061 |
| par           | 168598 |       -0.0446 |          0.2212 |         0.1613 |          -0.0446 |              0.0041 |
| bogey         |  38481 |       -0.0206 |          0.216  |         0.1766 |          -0.0252 |              0.0009 |
| double+       |   4852 |        0.0202 |          0.2059 |         0.1995 |          -0.0112 |             -0.0048 |

## 2. Effects relative to a previous par

OLS with hole fixed effects (event x round x course proxy x hole) and `player_skill` (strokes gained per hole in the player's other events). Standard errors are clustered by player. Probability estimates are proportions: -0.0084 = -0.84 percentage points. The `player_skill` rows show the effect of one stroke gained per hole.

| outcome                  | previous hole   |   estimate |     se |   ci_low |   ci_high |   p_value |
|:-------------------------|:----------------|-----------:|-------:|---------:|----------:|----------:|
| Next-hole to_par         | birdie+         |    -0.0019 | 0.0032 |  -0.0082 |    0.0044 |    0.5583 |
| Next-hole to_par         | bogey+          |     0.0016 | 0.0038 |  -0.0057 |    0.0090 |    0.6621 |
| Next-hole to_par         | player_skill    |    -0.7390 | 0.0443 |  -0.8257 |   -0.6522 |    0.0000 |
| P(birdie or better next) | birdie+         |    -0.0028 | 0.0020 |  -0.0066 |    0.0011 |    0.1579 |
| P(birdie or better next) | bogey+          |     0.0028 | 0.0023 |  -0.0017 |    0.0072 |    0.2199 |
| P(birdie or better next) | player_skill    |     0.2823 | 0.0218 |   0.2396 |    0.3249 |    0.0000 |
| P(bogey or worse next)   | birdie+         |    -0.0028 | 0.0019 |  -0.0065 |    0.0009 |    0.1367 |
| P(bogey or worse next)   | bogey+          |     0.0034 | 0.0021 |  -0.0007 |    0.0074 |    0.1002 |
| P(bogey or worse next)   | player_skill    |    -0.3408 | 0.0240 |  -0.3878 |   -0.2938 |    0.0000 |

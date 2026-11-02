# Next-hole results (2025 PGA TOUR)

Sample: 270,032 holes with a previous hole (692 players, 44 events). Model A uses the 256,992 with `player_skill` available.

## 1. Raw next-hole outcomes by previous hole

| prev_cat   |      n |   mean_to_par |   p_birdie_next |   p_bogey_next |   mean_hole_diff |   mean_player_skill |
|:-----------|-------:|--------------:|----------------:|---------------:|-----------------:|--------------------:|
| birdie+    |  58101 |       -0.0406 |          0.2087 |         0.155  |          -0.0349 |             -0.0468 |
| par        | 168598 |       -0.0446 |          0.2212 |         0.1613 |          -0.0446 |             -0.0452 |
| bogey+     |  43333 |       -0.016  |          0.2149 |         0.1791 |          -0.0236 |             -0.041  |

Finer split:

| prev_detail   |      n |   mean_to_par |   p_birdie_next |   p_bogey_next |   mean_hole_diff |   mean_player_skill |
|:--------------|-------:|--------------:|----------------:|---------------:|-----------------:|--------------------:|
| eagle+        |   1477 |       -0.0034 |          0.1808 |         0.1584 |          -0.0113 |             -0.048  |
| birdie        |  56624 |       -0.0415 |          0.2094 |         0.1549 |          -0.0355 |             -0.0468 |
| par           | 168598 |       -0.0446 |          0.2212 |         0.1613 |          -0.0446 |             -0.0452 |
| bogey         |  38481 |       -0.0206 |          0.216  |         0.1766 |          -0.0252 |             -0.0417 |
| double+       |   4852 |        0.0202 |          0.2059 |         0.1995 |          -0.0112 |             -0.0353 |

## 2. Effects relative to a previous par (OLS, player-clustered SEs)

A = controls for `hole_diff` and `player_skill`. B = player fixed effects + `hole_diff`. C = hole fixed effects (event x round x course x hole) + `player_skill` (strictest, preferred). Probability estimates are proportions: -0.0084 = -0.84 percentage points.

| outcome                  | spec         | previous hole   |   estimate |     se |   ci_low |   ci_high |   p_value |
|:-------------------------|:-------------|:----------------|-----------:|-------:|---------:|----------:|----------:|
| Next-hole to_par         | A: controls  | birdie+         |    -0.0016 | 0.0031 |  -0.0078 |    0.0045 |    0.6030 |
| Next-hole to_par         | A: controls  | bogey+          |     0.0043 | 0.0037 |  -0.0030 |    0.0116 |    0.2505 |
| Next-hole to_par         | B: player FE | birdie+         |    -0.0003 | 0.0031 |  -0.0063 |    0.0057 |    0.9143 |
| Next-hole to_par         | B: player FE | bogey+          |    -0.0014 | 0.0036 |  -0.0085 |    0.0057 |    0.6937 |
| Next-hole to_par         | C: hole FE   | birdie+         |    -0.0031 | 0.0032 |  -0.0095 |    0.0032 |    0.3335 |
| Next-hole to_par         | C: hole FE   | bogey+          |     0.0033 | 0.0038 |  -0.0041 |    0.0107 |    0.3777 |
| P(birdie or better next) | A: controls  | birdie+         |    -0.0084 | 0.0019 |  -0.0122 |   -0.0047 |    0.0000 |
| P(birdie or better next) | A: controls  | bogey+          |     0.0068 | 0.0022 |   0.0024 |    0.0112 |    0.0023 |
| P(birdie or better next) | B: player FE | birdie+         |    -0.0102 | 0.0018 |  -0.0138 |   -0.0066 |    0.0000 |
| P(birdie or better next) | B: player FE | bogey+          |     0.0065 | 0.0021 |   0.0022 |    0.0107 |    0.0027 |
| P(birdie or better next) | C: hole FE   | birdie+         |    -0.0023 | 0.0020 |  -0.0061 |    0.0016 |    0.2500 |
| P(birdie or better next) | C: hole FE   | bogey+          |     0.0021 | 0.0023 |  -0.0024 |    0.0065 |    0.3622 |
| P(bogey or worse next)   | A: controls  | birdie+         |    -0.0078 | 0.0018 |  -0.0113 |   -0.0042 |    0.0000 |
| P(bogey or worse next)   | A: controls  | bogey+          |     0.0092 | 0.0021 |   0.0051 |    0.0133 |    0.0000 |
| P(bogey or worse next)   | B: player FE | birdie+         |    -0.0080 | 0.0018 |  -0.0115 |   -0.0046 |    0.0000 |
| P(bogey or worse next)   | B: player FE | bogey+          |     0.0041 | 0.0020 |   0.0001 |    0.0081 |    0.0453 |
| P(bogey or worse next)   | C: hole FE   | birdie+         |    -0.0034 | 0.0019 |  -0.0070 |    0.0003 |    0.0740 |
| P(bogey or worse next)   | C: hole FE   | bogey+          |     0.0041 | 0.0021 |   0.0001 |    0.0082 |    0.0453 |

## 3. Adjusted next-hole levels (model A)

| previous hole   |   Next-hole to_par |   P(birdie or better next) |   P(bogey or worse next) |
|:----------------|-------------------:|---------------------------:|-------------------------:|
| birdie+         |            -0.0486 |                     0.2128 |                   0.1516 |
| par             |            -0.0469 |                     0.2213 |                   0.1594 |
| bogey+          |            -0.0427 |                     0.2281 |                   0.1686 |

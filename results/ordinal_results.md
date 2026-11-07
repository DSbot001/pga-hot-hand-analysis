# Ordered and multinomial logit (2025 PGA TOUR)

Sample: 256,992 holes, 354 players. Next-hole outcome: eagle+ < birdie < par < bogey < double+. Previous hole reference: par. Controls: player_skill, hole_diff, field_birdie, field_bogey. SEs clustered by player.

## 0. Observed transition matrix (no controls)

Rows: previous hole. Columns: share of next-hole outcomes.

| prev_cat   |   eagle+ |   birdie |    par |   bogey |   double+ |
|:-----------|---------:|---------:|-------:|--------:|----------:|
| birdie+    |   0.0052 |   0.2054 | 0.6368 |  0.1370 |    0.0156 |
| par        |   0.0062 |   0.2181 | 0.6180 |  0.1397 |    0.0181 |
| bogey+     |   0.0064 |   0.2128 | 0.6070 |  0.1524 |    0.0214 |

## 1. Ordered logit

Positive coef = shift toward worse scores. Odds ratio > 1 = higher odds of a worse category.

|              |    coef |     se |   odds_ratio |   p_value |
|:-------------|--------:|-------:|-------------:|----------:|
| prev_birdie  | -0.0006 | 0.0097 |       0.9994 |    0.9516 |
| prev_bogey   |  0.0107 | 0.0119 |       1.0108 |    0.3691 |
| player_skill | -1.9198 | 0.1255 |       0.1466 |    0.0000 |
| hole_diff    |  1.2657 | 0.1691 |       3.5455 |    0.0000 |
| field_birdie | -2.3885 | 0.1806 |       0.0918 |    0.0000 |
| field_bogey  |  1.3747 | 0.2065 |       3.9538 |    0.0000 |

Adjusted next-hole distribution:

|         |   eagle+ |   birdie |    par |   bogey |   double+ |
|:--------|---------:|---------:|-------:|--------:|----------:|
| birdie+ |   0.0061 |   0.2169 | 0.6189 |  0.1401 |    0.0180 |
| par     |   0.0061 |   0.2169 | 0.6189 |  0.1402 |    0.0180 |
| bogey+  |   0.0060 |   0.2153 | 0.6192 |  0.1413 |    0.0182 |

Change vs previous par (percentage points):

|         |   eagle+ |   birdie |    par |   bogey |   double+ |
|:--------|---------:|---------:|-------:|--------:|----------:|
| birdie+ |    0.000 |    0.009 | -0.002 |  -0.006 |    -0.001 |
| bogey+  |   -0.006 |   -0.157 |  0.028 |   0.116 |     0.019 |

## 2. Multinomial logit (base outcome = par)

rel_risk_ratio > 1 = that outcome becomes more likely relative to par.

| outcome vs par   | previous hole   |    coef |     se |   rel_risk_ratio |   p_value |
|:-----------------|:----------------|--------:|-------:|-----------------:|----------:|
| eagle+           | birdie+         | -0.0587 | 0.0717 |           0.9430 |    0.4130 |
| eagle+           | bogey+          |  0.1090 | 0.0790 |           1.1152 |    0.1676 |
| birdie           | birdie+         | -0.0302 | 0.0130 |           0.9703 |    0.0201 |
| birdie           | bogey+          |  0.0277 | 0.0150 |           1.0281 |    0.0650 |
| bogey            | birdie+         | -0.0289 | 0.0152 |           0.9715 |    0.0574 |
| bogey            | bogey+          |  0.0438 | 0.0165 |           1.0448 |    0.0080 |
| double+          | birdie+         | -0.1276 | 0.0406 |           0.8802 |    0.0017 |
| double+          | bogey+          |  0.0798 | 0.0388 |           1.0831 |    0.0398 |

Adjusted next-hole distribution:

|         |   eagle+ |   birdie |    par |   bogey |   double+ |
|:--------|---------:|---------:|-------:|--------:|----------:|
| birdie+ |   0.0057 |   0.2115 | 0.6278 |  0.1387 |    0.0163 |
| par     |   0.0060 |   0.2148 | 0.6201 |  0.1409 |    0.0182 |
| bogey+  |   0.0065 |   0.2174 | 0.6116 |  0.1451 |    0.0194 |

Change vs previous par (percentage points):

|         |   eagle+ |   birdie |    par |   bogey |   double+ |
|:--------|---------:|---------:|-------:|--------:|----------:|
| birdie+ |   -0.023 |   -0.333 |  0.774 |  -0.223 |    -0.195 |
| bogey+  |    0.055 |    0.258 | -0.851 |   0.417 |     0.120 |

## 3. Formal tests

Wald tests on the multinomial coefficients (player-clustered):

|                                                |     df |    chi2 |   p_value |
|:-----------------------------------------------|-------:|--------:|----------:|
| H0: previous hole has no effect on any outcome | 8.0000 | 37.7530 |    0.0000 |
| H0: previous birdie+ has no effect             | 4.0000 | 16.8262 |    0.0021 |
| H0: previous bogey+ has no effect              | 4.0000 | 15.3885 |    0.0040 |

Style test: change in P(par on next hole) vs previous par, with hole fixed effects + player_skill (linear probability model, player-clustered SEs):

|             |   change_pp |   se_pp |   p_value |
|:------------|------------:|--------:|----------:|
| prev_birdie |      0.5574 |  0.2536 |    0.0280 |
| prev_bogey  |     -0.6158 |  0.2668 |    0.0210 |

## Fit

Ordered logit: log-likelihood -240,323.1, 10 parameters, AIC 480,666.1

Multinomial logit: log-likelihood -238,604.0, 28 parameters, AIC 477,264.0

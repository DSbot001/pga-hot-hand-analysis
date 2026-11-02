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
| prev_birdie  | -0.0027 | 0.0098 |       0.9973 |    0.7831 |
| prev_bogey   |  0.0133 | 0.0120 |       1.0133 |    0.2679 |
| player_skill |  1.2215 | 0.1326 |       3.3923 |    0.0000 |
| hole_diff    |  1.2471 | 0.1687 |       3.4801 |    0.0000 |
| field_birdie | -2.4140 | 0.1803 |       0.0895 |    0.0000 |
| field_bogey  |  1.3636 | 0.2062 |       3.9102 |    0.0000 |

Adjusted next-hole distribution:

|         |   eagle+ |   birdie |    par |   bogey |   double+ |
|:--------|---------:|---------:|-------:|--------:|----------:|
| birdie+ |   0.0061 |   0.2172 | 0.6188 |  0.1399 |    0.0180 |
| par     |   0.0061 |   0.2168 | 0.6189 |  0.1402 |    0.0180 |
| bogey+  |   0.0060 |   0.2149 | 0.6193 |  0.1416 |    0.0182 |

Change vs previous par (percentage points):

|         |   eagle+ |   birdie |    par |   bogey |   double+ |
|:--------|---------:|---------:|-------:|--------:|----------:|
| birdie+ |    0.002 |    0.039 | -0.007 |  -0.029 |    -0.005 |
| bogey+  |   -0.008 |   -0.194 |  0.035 |   0.144 |     0.023 |

## 2. Multinomial logit (base outcome = par)

rel_risk_ratio > 1 = that outcome becomes more likely relative to par.

| outcome vs par   | previous hole   |    coef |     se |   rel_risk_ratio |   p_value |
|:-----------------|:----------------|--------:|-------:|-----------------:|----------:|
| eagle+           | birdie+         | -0.0553 | 0.0716 |           0.9462 |    0.4400 |
| eagle+           | bogey+          |  0.1061 | 0.0791 |           1.1119 |    0.1797 |
| birdie           | birdie+         | -0.0285 | 0.0130 |           0.9719 |    0.0282 |
| birdie           | bogey+          |  0.0255 | 0.0150 |           1.0258 |    0.0891 |
| bogey            | birdie+         | -0.0305 | 0.0152 |           0.9699 |    0.0451 |
| bogey            | bogey+          |  0.0458 | 0.0166 |           1.0469 |    0.0057 |
| double+          | birdie+         | -0.1299 | 0.0406 |           0.8782 |    0.0014 |
| double+          | bogey+          |  0.0828 | 0.0388 |           1.0864 |    0.0329 |

Adjusted next-hole distribution:

|         |   eagle+ |   birdie |    par |   bogey |   double+ |
|:--------|---------:|---------:|-------:|--------:|----------:|
| birdie+ |   0.0058 |   0.2118 | 0.6278 |  0.1385 |    0.0163 |
| par     |   0.0060 |   0.2148 | 0.6201 |  0.1409 |    0.0182 |
| bogey+  |   0.0065 |   0.2170 | 0.6116 |  0.1454 |    0.0195 |

Change vs previous par (percentage points):

|         |   eagle+ |   birdie |    par |   bogey |   double+ |
|:--------|---------:|---------:|-------:|--------:|----------:|
| birdie+ |   -0.021 |   -0.305 |  0.770 |  -0.245 |    -0.199 |
| bogey+  |    0.054 |    0.220 | -0.845 |   0.446 |     0.126 |

## Fit

Ordered logit: log-likelihood -240,446.6, 10 parameters, AIC 480,913.2

Multinomial logit: log-likelihood -238,731.6, 28 parameters, AIC 477,519.3

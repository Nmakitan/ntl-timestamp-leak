# Experiment 2: timestamp-only baseline

Single feature t = smallest leaked IAT value in the row (0 if none).

| split | model | acc (all) | macro-F1 (all) | acc (leaked) | macro-F1 (leaked) | n test | n leaked |
|---|---|---|---|---|---|---|---|
| random | most_frequent | 0.5404 | 0.0780 | 0.5262 | 0.0766 | 1087225 | 398418 |
| random | stratified | 0.3598 | 0.1113 | 0.3648 | 0.1019 | 1087225 | 398418 |
| random | tree | 0.4153 | 0.3688 | 0.9517 | 0.5462 | 1087225 | 398418 |
| temporal | most_frequent | 0.5404 | 0.0780 | 0.5482 | 0.0787 | 1087223 | 359693 |
| temporal | stratified | 0.3600 | 0.1115 | 0.3678 | 0.1030 | 1087223 | 359693 |
| temporal | tree | 0.2687 | 0.1327 | 0.6109 | 0.1898 | 1087223 | 359693 |

Per-class recall (all test rows):

| split | model | Benign | Bot | Brute_Force_Web | Brute_Force_XSS | DDoS_HOIC | DDoS_LOIC_HTTP | DoS_HULK | DoS_SlowHTTP | SQL_Injection |
|---|---|---|---|---|---|---|---|---|---|---|
| random | most_frequent | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| random | stratified | 0.541 | 0.067 | 0.000 | 0.000 | 0.230 | 0.065 | 0.073 | 0.025 | 0.000 |
| random | tree | 0.324 | 0.500 | 0.463 | 0.293 | 0.502 | 0.999 | 0.011 | 1.000 | 0.269 |
| temporal | most_frequent | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| temporal | stratified | 0.540 | 0.067 | 0.000 | 0.000 | 0.231 | 0.067 | 0.073 | 0.025 | 0.000 |
| temporal | tree | 0.330 | 0.004 | 0.015 | 0.034 | 0.080 | 1.000 | 0.002 | 0.195 | 0.538 |

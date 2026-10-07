# Executive summary

Status 2026-10-03, 09:15 (all runs finished, including the overnight KNN runs). Sections refer to Parts B (sections 0-11) and C (section 12) of this file.

## The defect

1. **Bug (section 1).** NTLFlowLyzer writes the flow's absolute start time (Unix epoch, seconds) into every IAT
   statistic of a direction that holds exactly one packet (`features/utils.py:20-27`, `calculate_IAT`). Reproduced
   from a 21-packet synthetic pcap on upstream commit `d99cd53`; the author's fork gives byte-identical output.
   A second, already-reported bug (upstream issue #29) splits the closing ACK of a FIN exchange into its own
   1-packet "ghost" flow, which then also leaks.
2. **Not reported before (section 10).** No upstream issue, PR or publication found mentions the IAT timestamp leak
   (GitHub fully checked; literature check partial).

## How much of the published data is affected

| dataset | rows | leaked rows | % | rule violations | leaked values on capture day |
|---|---:|---:|---:|---:|---|
| BCCC-CSE-CIC-IDS2018 | 48,182,782 | 17,108,403 | 35.5 | 0 | yes (per attack file, own window) |
| BCCC-CIC-IDS-2017 | 2,438,052 | 939,324 | 38.5 | 0 | 100.00% |
| BCCC-cPacket-Cloud-DDoS-2024 | 700,774 | 458,427 | 65.4 | 0 | 100.00% |
| BCCC-DLLayer-IDS-2025 | not NTLFlowLyzer output | - | - | - | no timestamps |

- 0 violations of the rule "leak ⇔ exactly one packet in that direction" in 51.3M rows: the datasets were built with
  the buggy code. Every leaked value is the flow's true UTC start time (sections 2, 9; D2-D7).
- **Leak rate depends strongly on class**: from 0.05% (2017 DDoS_LOIT) or 0.07% (2018 LOIC) to 100% (2018 FTP and
  SlowHTTP, 2017 Port_Scan 99.9%). Most leaked attack rows are fragments split off real sessions (lone RST/ACK,
  ghost ACKs) with no attack content; exceptions where the leaked rows are the attack itself: 2017 Port_Scan,
  Botnet_ARES and cPacket BYPass-V1 (section 9, D4, D6).
- Units check (12.2a): every leaked cell sits in one narrow epoch band per dataset (Jul 2017, Feb 2018, Dec 2023);
  legitimate IATs top out near 3e4 s and no cell lies between 1e6 and 1e9, so the 1e9 threshold is clean.

## Is the leak exploitable?

- **Timestamp alone (section 9, Experiment 2).** On a random split, a pre-specified decision tree on the timestamp
  alone recovers the attack rows that carry it: mean attack-class recall 0.80 (2018), 0.90 (2017), 0.98 (cPacket) on
  leaked test rows. On a temporal split it mostly fails (0.13-0.23).
- **Existing 2018 models (section 4, Experiment 1).** Changing only the leaked timestamps in the test set:
  the shipped RF loses 20,381 correct attack detections that depended only on the timestamp; **KNN and the
  soft-voting ensemble fall from 0.993 to 0.871**, i.e. their whole advantage over the RF came from the leak
  (scaled ~1.5e9 values dominate the distance, so "nearest neighbour" becomes "nearest in time").

## Does it change results? Retraining with and without the leak

- **RF, 2018, 4 seeds (section 6).** Random split: the leak inflates accuracy by 4.4 points (0.998 vs 0.953).
  Temporal split: it *hurts* by 7.3 points (0.892 vs 0.965), because learned capture windows do not carry over.
- **RF, 2017 replication (section 11).** Random split inflation replicates and is larger (+11.6 points). The temporal
  sign reverses overall (+10.7 for the leaky model): benign fragments are only separable by time of day.
- **Where it happens.** On multi-packet flows all variants are equal (~0.99-1.00) on both datasets: the whole
  effect, in either direction, sits in the 1-packet rows.
- **Seven model families × three datasets (section 12).** Accuracy, leaky − fixA, all test rows:

  | model | 2018 random | 2018 temporal | 2017 random | 2017 temporal | cPacket random | cPacket temporal |
  |---|---:|---:|---:|---:|---:|---:|
  | DecisionTree | +0.045 | −0.028 | +0.061 | +0.043 | +0.090 | −0.057 |
  | XGBoost | +0.048 | +0.048 | +0.063 | +0.091 | +0.083 | +0.018 |
  | RandomForest | +0.165 | +0.023 | +0.098 | +0.093 | +0.144 | −0.016 |
  | LogReg | +0.115 | +0.002 | +0.003 | +0.004 | +0.000 | +0.001 |
  | MLP | −0.000 | −0.000 | +0.000 | +0.000 | +0.003 | +0.006 |
  | **KNN** | **+0.116** | **+0.090** | **+0.100** | **+0.056** | **+0.183** | **+0.011** |
  | GaussianNB (broken baseline) | +0.032 | −0.005 | −0.007 | +0.055 | +0.192 | +0.190 |

  - All three tree models (DT, XGBoost, RF) are inflated by the leak on every random split (+0.045 to +0.165); on
    temporal splits the sign is mixed, as in sections 6 and 11. Mean attack recall shows the same pattern (inflation up to +0.26 on cPacket).
  - **KNN is inflated on every dataset and both splits, temporal included** (+0.011 to +0.183 accuracy; mean attack
    recall +0.04 to +0.20), unlike the trees, whose temporal-split sign is mixed. This is the section 4.2 mechanism
    at scale: after scaling, a ~1.5e9 IAT dominates the distance, so the nearest neighbours are the flows nearest in
    time, and "nearest in time" still works for test flows just after the training window. On leaked test rows
    (2018 both splits, 2017 random), leaky KNN's mean attack recall is 0.85-0.91; with timestamps moved 8 years it
    falls to 0.15-0.20, below the retrained fixA model (0.37-0.64): it recognises leaked attack rows almost only by time.
  - **The retrained KNN reproduces the shipped one.** 2018 temporal split (the original pipeline's split): leaky
    0.993, +8y 0.871; the shipped ONNX KNN in section 4.2 gave 0.993 and 0.871 on a 20k sample.
  - Moving leaked timestamps 8 years (no retrain) costs the trees up to 0.44 accuracy on cPacket and 0.12-0.15 on
    2018 random: they rely on exact capture times.
  - Paired bootstrap 95% CIs (B = 1,000): for the five models other than GaussianNB and KNN, 49 of 60 leaky − fixA
    differences (accuracy and mean attack recall) exclude 0; for KNN, all 12 do. Accuracy CIs are at most 0.006 wide because the test sets are large, so even
    tiny differences come out "significant": judge them by size, not by the star. They cover test sampling only, not training randomness (single seed).
  - MLP and LogReg show little leaky−fixA difference, but both are under-trained (MLP early-stopped after 14-47
    epochs, no class weights; LogReg at the iteration limit in 9 of 12 runs), and setting leaked cells to 0 still costs
    MLP 0.04-0.08 accuracy, so it does use those features. Do not read them as immune.

## Possible impact on published work (Part F)

- OpenAlex full-text search (2026-10-03) for the exact dataset names: about 40 distinct works name a BCCC
  NTLFlowLyzer dataset; **at least 20 report experiments on one in their abstracts** (2024-2026), several with
  accuracy or F1 at or above 99% (e.g. 99.90% on BCCC-CIC-IDS-2017, 99.58% F1 on BCCC-CSE-CIC-IDS2018, up to
  99.99% on cPacket). The cPacket dataset paper has 48 citing works in Semantic Scholar.
- No study was reproduced. The claim is that the conditions for inflated results exist and are met by common
  practice (IAT features kept, random split or k-fold CV), so these results warrant re-examination.

## Validity of the fixed baseline (fixA)

A reviewer's main concern: fixA sets leaked cells to 0, and since leaking is class-dependent, "cell = 0" could
itself be a leak flag. Two checks (sections 12.1 and 12.2b):

- **Mask-only models:** a tree trained only on fixA's zero pattern beats one trained on legitimate zeros alone by at
  most 0.012 macro F1, and mean attack recall moves by −0.03 to +0.01. Legitimate exact zeros are common (up to 65% of
  IAT cells, depending on class), which hides the flag.
- **Drop-IAT control (36 new runs):** retraining with every IAT column removed gives the same results as fixA for
  DT, XGBoost, MLP and GaussianNB on every dataset and split (within 0.02 accuracy, ±0.01 mean attack recall; 31 of 48 such differences have CIs excluding 0, i.e. detectable
  but tiny). KNN (6 more runs) agrees within 0.001 accuracy everywhere; its mean attack recall is +0.03 higher
  with fixA on 2017 only (both splits), within ±0.002 elsewhere.
  Only RF on 2018 differs (+0.047 random, −0.033 temporal); the sign flips between splits and the gap traces to how
  that RF assigns 1-packet rows that are identical across HOIC, Bot and Benign: a tie-break, not a leak.
- **Conclusion: fixA is a valid leak-free baseline.**

## Model coverage

| model | where | datasets | conditions |
|---|---|---|---|
| RF (shipped ONNX) | section 4 | 2018 | timestamp changes only (no retrain) |
| KNN, soft-voting ensemble (shipped ONNX) | section 4.2 | 2018 | timestamp changes only, 20,001-row stratified sample |
| RF retrain | sections 6, 11 | 2018 (4 seeds), 2017 (1 seed) | leaky, fixA, fixB (+ 1-packet rows dropped) |
| Timestamp-only tree | sections 5, 9 | 2018, 2017, cPacket | balanced (pre-specified) and unweighted |
| GaussianNB, DT, LogReg, XGBoost, RF, MLP, KNN | section 12 | 2018, 2017, cPacket | leaky, +8y, zero, fixA; dropIAT (all but LogReg); full test sets |

KNN in section 12 is retrained (StandardScaler + distance-weighted 5-NN, as the shipped model) and scored on the full
test sets (overnight, 2026-10-02/03; up to 1 h 51 min per run on 2018). Not covered: the soft-voting ensemble was
not retrained. LinearSVC was dropped from section 12 (> 2.5 h per run). LightGBM and MinMax-scaled MLP were
planned as optional and not run.

## Caveats

- Single training seed in sections 11 and 12 (2018 RF seed-to-seed std was ≤ 0.002 accuracy in section 6).
- Tiny classes (2017 Heartbleed 3 test rows, Web_SQL_Injection 6; 2018 SQL_Injection 26, XSS 58): per-class
  counts for them are anecdotal.
- Accuracy on leaked rows is not comparable to all-row accuracy (different class mix); use mean attack recall.
- Section 12 trains on 600k-row stratified subsamples; the 2018 RF there scores below the full-training-set RF of
  section 6 (fixA random 0.831 vs 0.953).
- Timings in section 12 come from two machines; compare only within one machine.
- Laptop disk incident (2026-10-02): 60 scikit-learn files on the laptop were corrupted on disk and repaired from
  the PC; its data caches were checksum-identical, a laptop XGBoost run reproduced exactly on the PC, and a recheck
  after the overnight runs found everything still identical. Results are unaffected; the laptop's hard disk
  (Seagate ST1000LM035) should be checked (`smartctl`).
- Feature sets differ: 313 features (30 IAT) on 2018 and cPacket, 114 (15 IAT) on 2017.

## Open items (updates to section 8)

- Section 8 items 1 (Gate 1 comparison), 3 (possible duplicate benign rows), 4 (bulk-rate artifact),
  5 (upstream issue), 7 (disk check): status not recorded since the main report; check before publishing.
- Item 6 (generality): done for three datasets (sections 9, 11) and extended to six model families (section 12).
- KNN retrain: done (section 12). New: LogReg with more iterations if it is to be reported; MLP with class weights
  and more epochs if MLP robustness is to be claimed; systematic literature check (section 10).

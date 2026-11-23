# Results and limits

Every test below was written down before it was scored: the data it uses, the pass bar and the alarm level. The held-back data was scored once. We publish the tests that fell short next to the ones that passed.

Farms: Kelmarsh (6 Senvion MM92), Penmanshiel (14 Senvion MM82), Hill of Towie (21 Siemens SWT-2.3).

## 1. Detect: what is the turbine doing?

### Stops

**Question:** did this turbine stop for 60 minutes or more at a wind speed of 4 m/s or more, on this day?

**Design:** trained on the two Senvion farms. The alarm level was set on Senvion validation days only. Tested on the Siemens farm, which the model never saw in training.

| Test | Turbine-days | Stops | Language model (OpenTSLM + fusion adapter, 3 seeds) | Gradient boosting |
|---|---|---|---|---|
| Confirmation, Hill of Towie 2016–2021, scored once | 37,899 | 2,556 | **2,341 caught (91.6%), 8 false alarms** | 1,870 caught (73.2%), 5 false alarms |
| Hill of Towie 2023–2024 | 9,983 | 796 | **758 caught, 2 false alarms** | |

- The fusion adapter lifts average precision on the unseen farm from 0.90 to 0.99.
- The confirmation met its rule, which was set in advance: against gradient boosting, the interval for extra stops caught lies above 0, and the interval for extra false alarms includes 0. The false-alarm part passed at its edge, with an interval of [0, +8].

**Limits:**
- Gradient boosting ranks stop days slightly better (average precision 0.996 vs 0.989). Our edge is an alarm level that carries over to another maker.
- Stops under 60 minutes are not in the test. With them, false alarms on 2023–24 rise from 2 to 60.

### Curtailment

**Question:** was this turbine told to cut its output?

**Design:** a detector trained without one real curtailment label, frozen, then tested against the grid operator's dispatch records.

| Test | Result |
|---|---|
| Hill of Towie 2025–26, 768 turbine-days on 37 dispatch dates | 96.6% caught [93.9, 98.7]; 8.1% of clean days alarmed |
| Senvion, logged curtailment (test A) | 83.8% caught |
| Senvion, later logged days | 42.5% caught. Most of those days show no drop in power, and the freeze rule failed on that interval |

**Language model, first run (one seed):**
- It is on par with a tree given the same inputs: average precision +0.013 [−0.017, +0.128] on test A and +0.039 [−0.033, +0.118] on Hill of Towie.
- It stays below the best tree, which sees farm-wide context: 152 of 768 dispatch days caught against 504.
- It failed its pre-set bar.

## 2. Explain: where did the energy go?

### Lost energy per stop

- Against the operator's own lost-energy figure, over 1,338 stops: correlation 0.988, total within −4.7%.
- On the fresh 2023–24 stops: correlation 0.996.

### Cause: weather or the turbine side (fault, maintenance, requested)

**Design:** a gradient-boosting tree trained on 2019–2022 stops, frozen, then tested once on 2023–24. The bar was set in advance: macro F1 of 0.8 or more and an energy-share error of 5 points or less, at both farms.

| Farm | Stops (lost energy) | Macro F1 | Weather energy-share error |
|---|---|---|---|
| Kelmarsh | 103 (1,143 MWh) | 1.000 [0.500, 1.000] | 0.0 points |
| Penmanshiel | 210 (2,394 MWh) | 0.993 [0.969, 1.000] | 3.4 points |

Result: **HOLDS.** 312 of 313 stops are right, where the cause is the one stated in the operator's comment. In 2022, the weather share of lost energy was 13.7% true against 12.2% predicted at Kelmarsh, and 16.1% against 16.5% at Penmanshiel.

**Limits:**
- Kelmarsh had only 4 weather stops in the fresh test, so its interval is wide.
- With a third class (grid or park), Kelmarsh drops to a macro F1 of 0.718.

### Cause on a maker it never saw: the language model beats the tree

**Design:** both models were trained on Senvion stops (2019–2024), then frozen and scored once on Hill of Towie (Siemens). Nothing was trained or tuned on Hill of Towie. The bar was set in advance: the language model's F1 at least the tree's minus 0.05, and its energy-share error at most the tree's plus 5 points.

| Hill of Towie, 2016–2024 | Our language model | Tree | Difference [95% interval] |
|---|---|---|---|
| All 1,741 stops | **0.838** | 0.766 | +0.072 [+0.032, +0.116] |
| Stops whose label agrees with ERA5 weather | **0.910** | 0.832 | +0.078 [+0.029, +0.134] |

- Guessing the most common answer scores 0.33.
- The language model found 748 of 876 weather stops, the tree 635. Most of the gain is icing.
- It leads in 8 of 9 years; 2016 is a tie.
- Energy-share error: 6.7 points against the tree's 3.1, inside the allowance.

**Limits:**
- It's one Siemens farm.
- The labels come from the controller's stop timers, whose meaning isn't officially documented.
- There's no maintenance class, so "turbine-side" means faults only.
- Both models call about half the turbine-side stops during storms "weather"; part of that is a labelling difference.
- **At home the tree stays the answer.** The same language model failed its once-scored 2016–2018 Senvion test: Kelmarsh F1 0.518 against the tree's 0.918. Almost all of that failure is in windows where pitch wasn't recorded, which the model barely saw in training and the tree handles natively.

### Checking the labels

Every label was checked against an independent source: raw status logs, grid dispatch records, the turbine's second wind sensor and operator comments.

- **Stop minutes:** recomputed from the raw logs for 29,218 turbine-days, with 0 mismatches.
- **Dispatch records:** in the slots where the grid operator instructed a cut, output was near zero 82% of the time, against 1% otherwise (140,142 slots).
- **"Underperformance" days:** 28 of 56 were a broken anemometer, found with the turbine's second wind sensor.
- **"Icing" stops:** a run of them at one Penmanshiel turbine was a faulty sensor, not ice.

## 3. Verify: did the fix work?

**First real case:** the AeroUp blade upgrade on Hill of Towie turbine 13, installed on 24–29 September 2021.

**Design:**
- The turbine's daily energy is compared with two independent expected-energy references, each against a baseline from before the install.
- The bar was set in advance: both references show a gain between +1.5% and +7%, the 90% interval is above 0, and there is no loss flag.

| Reference | Gain over 53 days | 90% interval |
|---|---|---|
| B | +6.9% | [−4.1, +9.6] |
| A | +8.0% | [+6.7, +13.3] |

**Result:** not yet confirmed by our bar. Both references see a gain and 0 of 106 window-days were flagged as a loss, but the interval for reference B still includes 0.

**Limits:**
- December's baseline already contains October 2021, after the install, so December slightly understates the gain.

## Running below its power curve

Faults were injected into real turbine data (a digital twin) so there is a known answer; real running-low faults have no ground truth.

- **Rule-based detector:** works on the Senvion farms but failed its pre-set Hill of Towie test (30-day false alarms 7.7–13.7%).
- **Our language model, first run:** trained on Kelmarsh, Penmanshiel and Hill of Towie, validated on Fuhrländer, tested on EDP (never used to choose).
  - **Fuhrländer validation: failed its bar.** It found 70% of losses against the tree's 92%, with cause F1 0.53 against 0.64, at the same 3% false-alarm level. The tree stays the detector.
  - **EDP, the Fuhrländer alarm level carried over unchanged:**

    | EDP | Our model | Tree |
    |---|---|---|
    | Real ordinary windows flagged (target 3%) | **4.5%** | 18% |
    | Ranking of losses (AP) | 0.995 | 0.989 |
    | Cause F1, 7 classes | 0.783 | 0.779 |
    | Losses found, both held to 3% of real windows | 50% | **77%** |

  - **Reading:** the model's alarm level carries over to a new farm, and the tree's doesn't. Held to the same false-alarm budget, the tree finds more. On the new farms, ordinary windows look like faults to the model, because heading and rotor signals wander more there than on the training farms.
- **Our language model, second run (per-turbine noise scaling, heading-sensor cases):**
  - **Fuhrländer validation: failed its bar again.** It found 68% of losses against the tree's 97%, with cause F1 0.41 against 0.72.
  - Its false alarms are fixed: 4.5% of EDP's real ordinary windows flagged. But many losses are now called sensor faults, the most common answer in its training rows.
  - The tree stays the detector for this question.

## One model for every question

One OpenTSLM model trained on all four questions at once: stops, cause, curtailment and running low. **These are validation results, not held-out ones.** Each bar was set before the run.

- **First joint run (v1): failed its gate.** It learned all four questions, but it read calm-wind standstills as stops (53 validation false alarms) and called one storm's weather stops turbine faults. The separate models stayed the answer.
- **Second joint run (v2, 22 November 2026):** it starts from our confirmed stops model, the cause question reads the signals through its own path (as its separate model does), and calm-wind standstill days count for more in training. One seed, 5 epochs, last-epoch weights, all fixed before the run.

| Validation | v2 | v1 | Separate model | Bar |
|---|---|---|---|---|
| Stops: average precision · false alarms (Senvion 2021 H2, 3,070 days) | **0.9876** · 0 | 0.9605 · 53 | 0.9811 · 0 | ≥ 0.9761 |
| Cause: macro F1 · energy-share error in points (134 stops, threshold 0.35) | **0.850** · 0.4 | 0.701 · 35.5 | 0.855 · 0.7 | ≥ 0.805 · ≤ 5.7 |
| Curtailment: AUC · caught (one logged grid event, 14 turbine rows) | 0.888 · 5 | 0.890 · 2 | 0.942 · 11 | ≥ 0.89 |
| Running low: losses found · cause F1 (Fuhrländer) | **0.813** · 0.694 | 0.839 · 0.670 | 0.684 · 0.408 | ≥ 0.654 · ≥ 0.378 |

- **Three of four questions meet their bar.** Stops' false alarms fell from 53 to 0 (136 of 142 stops caught at the 95% alarm level). Storm Arwen's weather stops found: 17 of 21, against 4 for v1. Running low's cause F1 (0.694) is at least the tree's (0.678) on this set for the first time; the tree still finds more losses (0.981).
- **Curtailment is 0.002 short, and the whole shortfall is one row.** The validation holds one grid event: a farm-wide cut of a single 10-minute step at Penmanshiel on 14 December 2021. Turbine 04 lost the least energy on the farm while its wind was falling, so its dip reads like the wind dropping; the model scored it 0.014. Without that row the AUC would be 0.94; the reported result stays 0.888. The model's six signals don't include the power setpoint, the direct record of a cut, which all three farms log.
- **As written, the gate is not passed.** It also asked at least one question to beat its separate model with a 95% interval above 0. Stops: +0.0065 average precision, interval −0.002 to +0.023; cause: −0.005. Running low is not like for like with its separate model.

**Limits:**
- A re-test, not a clean check: v2's fixes were designed from v1's misses on these same validation days, and three changes went in at once.
- One seed. Curtailment is validated on a single grid event.
- The one-time Hill of Towie comparison for v2 is not scored yet. Until v2 holds there, the separate models stay the answer.
- v2's weights are open on [Hugging Face](https://huggingface.co/gsoulja/Llama-3.2-1B-OpenTSLM-wind-joint) (`v2/`), next to v1's.

## Sources for the problem

- The −9% median and the 14% that meet or beat their estimate: Hendrickson study of European onshore projects (via WindESCo); Hammond & Simley, Wind Energy Science 2026.

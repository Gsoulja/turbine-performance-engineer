# Turbine Performance Engineer

Detect, explain, verify: a performance engineer for every wind turbine, from the raw turbine signals, across turbine makers, scored in public.

TimeNet Online Hackathon, Round 1 · team sololeveling

- **Live site:** https://turbine-performance-engineer.vercel.app
- **Pitch video:** [media/pitch-video.mp4](media/pitch-video.mp4) (4:46; German subtitles in [media/pitch-video.de.vtt](media/pitch-video.de.vtt))
- **Pitch slides:** [pitch.html](pitch.html) (←/→ to move, N for speaker notes, F for full screen)
- **Monitor demo:** [demo/](demo/?model=/feeds/towie-2023-07-stops-model.json) (a replay of real data with the models' answers; on Hill of Towie's real rows, the live view runs on the trained stops model's real answers from [feeds/](feeds/))
- **Results and limits:** [RESULTS.md](RESULTS.md)
- **Bring your own data:** in the demo, *Add a farm* loads your own 10-minute SCADA CSVs in the browser, with nothing uploaded (tutorial on the [site](https://turbine-performance-engineer.vercel.app/#own-data))
- **Connect a model:** [connect/bridge.py](connect/bridge.py) feeds any model's answers into the demo (guide on the [site](https://turbine-performance-engineer.vercel.app/#connect); message contract in [demo/MODEL_FEED.md](demo/MODEL_FEED.md))
- **Trained models:** [Hugging Face collection](https://huggingface.co/collections/gsoulja/sololeveling-wind-turbine-performance-engineer-6b031e0b75d3cb2072628436)
- **Dataset in TimeNet:** [OpenTSLM/TimeNet PR #838](https://github.com/OpenTSLM/TimeNet/pull/838)

## The problem

European onshore wind farms produce a median of about 9% less energy than they were financed on, and only about 14% meet or beat their estimate. Today's tools find the loss and name a cause, but the cause comes from each maker's alarm codes and is scored on private fleets. It can't be checked or compared from outside, and it doesn't carry over to a new maker.

## What we built

We answer the three questions an asset manager asks, from six raw 10-minute signals (power, wind speed, rotor speed, pitch, nacelle direction, temperature):

1. **Detect.** What is the turbine doing: stopped or curtailed?
2. **Explain.** Where did the energy go: how many megawatt-hours did each stop cost, and was it the weather or the turbine?
3. **Verify.** Did the fix work: did an upgrade bring energy back?

The answers close a loop. The monitor ranks what to fix first, and every verdict an engineer gives in it is saved as a training label for the next round.

- **Dataset:** three UK wind farms added to TimeNet: Kelmarsh (6 Senvion MM92), Penmanshiel (14 Senvion MM82) and Hill of Towie (21 Siemens SWT-2.3). That is 41 turbines and two makers, with a labelled state for every turbine-day, each label checked against an independent source.
- **Model:** OpenTSLM-SP on a frozen Llama-3.2-1B, with a fusion adapter we added that mixes the six signals at each time step.
- **Monitor:** a 3D view of the farm on real terrain, with each turbine's state, the lost energy by cause, the before/after check and a verdict button.

## Headline results (held out, scored once)

| Question | Test | Result |
|---|---|---|
| Stops of 60 minutes or more | Trained on Senvion, tested on Siemens turbines it never saw, 2016–2021 (37,899 turbine-days) | 91.6% of 2,556 stops caught with 8 false alarms. Gradient boosting: 73.2% with 5 |
| Cause on a maker it never saw | Trained on Senvion, scored once on Hill of Towie (1,741 stops) | F1 83.8% against the tree's 76.6% |
| Curtailment | Grid-dispatch days on Hill of Towie 2025–26 (768 turbine-days) | 96.6% caught; 8.1% of clean days alarmed |
| Lost energy per stop | Against the operator's own figure, 1,338 stops | Pearson correlation 0.988 |
| Cause: weather or turbine side | Frozen tree, fresh 2023–24 test, bar set in advance | 312 of 313 stops right |
| Fix check: AeroUp blades, turbine 13 | Two independent references, bar set in advance | +6.9% and +8.0%, not yet confirmed by our bar |

Every test was written down before it was scored, including the ones that fell short. At home, gradient-boosting trees match or beat the language model, and two of our language models missed their pre-set bars. [RESULTS.md](RESULTS.md) has the full numbers and limits.

## What this repository contains

The website: the one-page overview (`index.html`), the pitch slides and video, the monitor demo with its data files, and the results. The trained models are open on Hugging Face (link above). The labelling and training code are not published.

To run it locally, serve the folder and open it in a browser:

```
python3 -m http.server 8000
# then open http://localhost:8000/
```

## Data and credits

The demo files contain excerpts and values derived from these datasets, all under CC BY 4.0:

- Kelmarsh wind farm data, Cubico Sustainable Investments: https://zenodo.org/records/16807551
- Penmanshiel wind farm data, Cubico Sustainable Investments: https://zenodo.org/records/16807304
- Hill of Towie open dataset, RES on behalf of TRIG: https://doi.org/10.5281/zenodo.14870021

The 3D view: imagery © Esri, Maxar, Earthstar Geographics and the GIS user community; elevation from Mapzen/Tilezen terrain tiles (SRTM, NED, EU-DEM and others).

Built with:

- [OpenTSLM](https://github.com/OpenTSLM/OpenTSLM) (MIT licence)
- [TimeNet](https://github.com/OpenTSLM/TimeNet) (MIT licence)
- Llama 3.2. **Built with Llama.** Llama 3.2 is licensed under the Llama 3.2 Community License, Copyright © Meta Platforms, Inc. All Rights Reserved.

## Rights

© 2026 sololeveling. All rights reserved: no licence is granted to reuse the code in this repository. The trained models on Hugging Face carry their own licence (Llama 3.2 Community License). The third-party data and imagery above stay under their own licences.

# Landslide Early Warning for Kaski, Nepal

A local prototype that estimates **3-day landslide risk** from rainfall forecasts for Kaski district, near Pokhara. Built for Anuka, whose family travels a road in the district.

>  **This is not an official warning.** Follow [DHM](https://www.dhm.gov.np) and local authorities.

Built for the Hacktoberfest 2026 Weekend Challenge: *Build for a Friend*.

## What it does

- **District picker** covering 10 Gandaki districts, with Kaski as the default.
- **Risk percentage** from a Monte Carlo simulation over 122 pooled forecast ensemble members (ECMWF 51, GFS 31, ICON 40).
- **Driver breakdown** showing which rainfall window (3, 7 or 14 days) is pushing the risk up.
- **Forwardable message** in English (written by Gemma 3 4B through Ollama) and in Nepali (a fixed template).
- **Fallback chain** for when phones are down: SMS, Viber group, community volunteer, siren or flag.
- **A fixed footer** on every screen: "This is not an official warning. Follow DHM and local authorities."

## Results

I tested whether a tabular foundation model beats simple rainfall rules, using a time-based split (train on earlier years, test on 2022 to 2024). **No method wins clearly.** All bootstrap 95% F1 intervals overlap.

| Rule | F1 | 95% interval |
|---|---|---|
| 3-day rain > 77 mm (tuned on test years, so optimistic) | 0.31 | 0.17 to 0.45 |
| 3-day rain (tuned on train years) | 0.13 | 0.00 to 0.27 |
| I-D line, as published | 0.27 | 0.17 to 0.36 |
| **I-D line, recalibrated (used in the app)** | **0.29** | 0.12 to 0.44 |
| API (antecedent precipitation index), as quoted | 0.23 | 0.15 to 0.32 |
| API, tuned on train years | 0.22 | 0.06 to 0.39 |
| TabPFN v2, richer features | 0.33 | 0.17 to 0.49 |

### Why TabPFN is not in the shipped app

TabPFN v2 had the highest nominal F1 (0.33), but I chose not to ship it:

- **The result came from one year.** Per-year F1 was 0.00 in 2022, 0.11 in 2023 and 0.58 in 2024.
- **Cross-validated AUC inside the training years was 0.45**, below chance.
- **Serving would need soil moisture** from a different source than the one used in training.

The app uses the recalibrated I-D line instead. It fires on about 6% of monsoon days, versus about 28% for the published version, so it raises fewer false alarms.

## How it works

```
BIPAD incidents (filtered to Kaski)  ──►  one label per calendar day
Open-Meteo archive + forecast        ──►  daily rain, then 3d / 7d / 14d windows
Rainfall features                    ──►  recalibrated I-D rule
Ensemble members (122)               ──►  1,000 Monte Carlo samples  ──►  risk %
Risk + driver                        ──►  Gemma (English) / template (Nepali)
Streamlit                            ──►  badges, messages, fallback chain, footer
```

## Project layout

```
landslide-early-warning/
├── app.py                  Streamlit UI
├── build_dataset.py        Joins BIPAD incidents with Open-Meteo rainfall, one row per day
├── features.py             Rain windows (3d, 7d, 14d), API, month
├── pull_hourly.py          Hourly rainfall for the ensemble spread
├── thresholds.py           I-D and API rule definitions
├── baseline.py             Simple rain_3d > X threshold sweep
├── train_tabpfn.py         TabPFN v2 on basic features
├── train_tabpfn_rich.py    TabPFN v2 with antecedent rain, soil moisture, lagged rain
├── compare.py              Baseline vs TabPFN on the same split
├── compare_thresholds.py   Three rainfall rules, seven variants
├── significance.py         Bootstrap 95% confidence intervals
├── forecast_gap.py         Archive rainfall vs forecast rainfall
├── predict.py              Loads the saved model, returns risk label and probability
├── mc.py                   Monte Carlo sampling over ensemble members
├── message.py              Gemma prompt, validator, template fallback
├── save_artifacts.py       Writes model, feature order and thresholds
├── models/                 Saved artifacts (tabpfn, tabpfn_rich, rule, calibration, meta)
├── data/raw/               BIPAD incidents, rainfall, ensemble members
├── docs/                   Post draft, Anuka script and questions
└── requirements.txt
```

## Run it

**Requirements:** Python 3.10+, [Ollama](https://ollama.com) with `gemma3:4b`, and an internet connection for the forecast fetch.

```bash
pip install -r requirements.txt

# One-time: download the model
ollama pull gemma3:4b

# Start Ollama (leave it running in its own terminal)
ollama serve

# In another terminal, run the app
streamlit run landslide-early-warning/app.py
```

The app opens at <http://localhost:8501>.

## Limitations

- **Not road-level.** Rainfall comes from one grid cell at the district centroid (about 1,615 m), not from rain gauges or the road itself.
- **Not offline.** The forecast fetch needs internet. The offline part is the fallback chain: people who can pass a warning on when phones and the app cannot.
- **Not validated outside Kaski.** The other 9 districts reuse the Kaski model, and the app says so.
- **Incident data is incomplete.** BIPAD only records reported landslides, so small events are missing from the labels.
- **Rainfall only.** It cannot predict events that rain does not cause, such as the August 2026 rock-ice avalanche in Rasuwa.
- **Not reviewed by a native speaker.** Neither the Gemma English output nor the Nepali template has been checked by a native speaker.
- **Not an official warning.** Follow DHM and local authorities.

## Built with

- [TabPFN v2](https://github.com/PriorLabs/TabPFN) by Prior Labs (evaluated, not shipped; see above)
- [Gemma 3 4B](https://ai.google.dev/gemma) through Ollama
- [Open-Meteo](https://open-meteo.com) archive, forecast and ensemble APIs (no key needed)
- [Streamlit](https://streamlit.io)
- [BIPAD portal](https://bipadportal.gov.np), Nepal's national disaster information system
- I-D threshold from the Kanti Roadway study in Bagmati Province

## License

MIT License. Copyright (c) 2026 Siddhartha Bhattarai.
Permission is granted, free of charge, to use, copy, modify, merge, publish, distribute, sublicense and/or sell copies of this software, provided the copyright notice and this permission notice are included. The software is provided "as is", without warranty of any kind.

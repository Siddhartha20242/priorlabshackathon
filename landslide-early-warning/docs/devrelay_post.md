# A 3-day rain check for a road near Pokhara

#devchallenge #weekendchallenge #hf26challenge

## Who it's for
My friend Anuka and her family use a road in Kaski, near Pokhara. [One line about the road, in Anuka's words.] In the monsoon the practical question is whether it is worth travelling in the next few days. I built a small tool that reads rainfall forecasts and writes a short message, in English and Nepali, that can be forwarded on Viber or WhatsApp.

## What the app does
Pick a district, press "Check next 3 days", and the app fetches the rainfall forecast. It runs 1,000 rainfall scenarios, drawn from 122 pooled ensemble members (ECMWF, GFS and ICON), through an intensity-duration rule and shows, for each of the three days, a line like "Risk: 68% (680 of 1,000 forecast scenarios)". That number is the share of scenarios that cross the rain level linked to reported landslides. It is not the chance of a landslide: in the 2022-2024 monsoons, on the days the rule fired, a landslide was reported in Kaski on 35% of them (8 of 23), against 9% of all monsoon days.

Below that is a message in English and Nepali, under 60 words each. If the warning is high, the app opens a fallback chain: SMS, then a Viber group, then a Community Disaster Management Committee volunteer, then a siren or flag. A "Network available?" toggle switches the app to showing only that chain, because the forecast cannot update without a network. A fixed footer reads: "This is not an official warning. Follow DHM and local authorities." The English message is written by Gemma 3 4B running locally through Ollama; the Nepali message is a fixed template I wrote. Neither has been reviewed by a native speaker, and the app says so.

## The honest result
I compared three kinds of rainfall rule against landslide days reported for Kaski on Nepal's BIPAD portal: cumulative 3-day rain, antecedent precipitation (API), and an intensity-duration (I-D) line published for the Kanti Roadway. Each was tried as published or with a simple threshold, and again with parameters tuned on training years only (monsoon seasons 2015-2021, 854 days, 41 landslide days). All were scored on the 2022-2024 monsoons (366 days, 33 landslide days). The Kanti study is from Bagmati Province, not Kaski.

| Rule | F1 | 95% bootstrap interval |
|---|---|---|
| 3-day rain > 77 mm (threshold picked on the test years) | 0.31 | 0.17 - 0.45 |
| 3-day rain, threshold tuned on training years | 0.13 | 0.00 - 0.27 |
| I-D line as published | 0.27 | 0.17 - 0.36 |
| I-D line, intercept recalibrated on training years (used in the app) | 0.29 | 0.12 - 0.44 |
| API, as quoted (77 mm; decay assumed) | 0.23 | 0.15 - 0.32 |
| API, tuned on training years | 0.22 | 0.06 - 0.39 |
| TabPFN v2, richer features | 0.33 | 0.17 - 0.49 |

No method wins. The intervals all overlap, running from about 0.00 to 0.49 on 33 landslide days. The 77 mm rule's score is flattered because its threshold was chosen on the test years; tuned on training years it falls to 0.13, and moving it from 183 mm to 186 mm changes F1 from 0.17 to 0.13. The published I-D line fires on about 28% of Kaski monsoon days and stays on for about two weeks after a big storm, so I recalibrated it. The version in the app fires on about 6% of monsoon days. I picked it because it raises fewer false alarms, not because it scored higher.

TabPFN v2 on richer features (antecedent rainfall, soil moisture, lagged rain) had the highest nominal F1, 0.33, and for a while it looked like a win. It did not survive checking. Its F1 was 0.00 in 2022, 0.11 in 2023 and 0.58 in 2024, so the whole result came from one year. Its cross-validated AUC inside the training years was 0.45, which is below chance. It would also need soil moisture from a different source at serving time than at training time. So the app does not use it. I used TabPFN v2; the newer versions' license acceptance did not register on my account and I did not use them. Built with TabPFN v2 (Prior Labs).

## Why open and local mattered
The rule and the message layer run on a laptop. The rainfall data and ensemble forecasts come from Open-Meteo, which needs no key. The English message is written by Gemma 3 4B through Ollama on the same machine, with nothing leaving the device. The Nepali message is a fixed template, because Gemma's Nepali was unreliable in my tests (invented words, wrong month names). The interface is a local Streamlit prototype. Fetching the forecast needs internet, so this tool does not work offline in the hills. The offline part is the human chain in the fallback list: people who can pass a warning on when phones and the app cannot.

## Limits
- It only looks at rain. The August event was an ice-rock avalanche, which a rainfall model is not built to predict.
- Incident data is reported events on BIPAD, not every landslide. Eight of the 124 Kaski landslide days fall outside June-September and were excluded.
- The test set has 33 landslide days. I did not compute confidence intervals for the app's live output.
- Rainfall is reanalysis for a grid cell at about 1,615 m near the district centroid, not gauge data and not the road. The ensemble spread likely understates real forecast error: day-ahead forecasts differed from reanalysis by about 5 to 8 mm a day on average in the periods I checked.
- The app has only been tested on live off-season (October) forecasts and on synthetic and forced high-risk cases, because it is not monsoon season.
- Other districts reuse the Kaski model and are not validated. The app says so.
- Neither the English (Gemma 3 4B) nor the Nepali (fixed template) has been reviewed by a native speaker. Gemma's English is checked automatically for length, the exact disclaimer and wording, but it can still be imprecise, for example calling 2 mm of rain "heavy". Two of four test calls failed those checks and fell back to the fixed template.
- This is not an official warning. Follow DHM and local authorities.

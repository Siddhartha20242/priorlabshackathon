# A 3-day rain check for a road near Pokhara

#devchallenge #weekendchallenge #hf26challenge

## Who it's for
My friend Anuka and her family use a road in Kaski, near Pokhara. The road has been hit by landslides before. In the monsoon the practical question is whether it is worth travelling in the next few days. I built a small tool that reads rainfall forecasts and writes a short message, in English and Nepali. You can forward it on Viber or WhatsApp.

## What the app does
Pick a district and press "Check next 3 days". That's it. For each of the next three days the app shows a risk percentage, like "Risk: 68% (680 of 1,000 forecast scenarios)". It gets that number by running 1,000 rainfall scenarios, drawn from 122 pooled ensemble members (ECMWF 51, GFS 31, ICON 40), through a rainfall rule. Below that you get a forwardable message in English and Nepali and a fallback chain of SMS, Viber group, community volunteer, and siren or flag. There is also a "Network available?" toggle that shows only the chain when phones are down. A fixed footer says "This is not an official warning. Follow DHM and local authorities."

## The honest result
I compared three kinds of rainfall rule against landslide days reported for Kaski on Nepal's BIPAD portal. The first is cumulative 3-day rain. The second is antecedent precipitation (API). The third is an intensity-duration (I-D) line published for the Kanti Roadway. I tried each as published or with a simple threshold, and again with parameters tuned on training years only (monsoon seasons 2015-2021, 854 days, 41 landslide days). Then I scored them all on the 2022-2024 monsoons (366 days, 33 landslide days). The Kanti study was done in Bagmati Province, a different province from Kaski.

The risk percentage is the share of scenarios that cross the rain level linked to reported landslides. It doesn't tell you the chance of a landslide. In the 2022-2024 monsoons, a landslide was reported in Kaski on 35% of the days the rule fired (8 of 23). Across all monsoon days it was 9%.

| Rule | F1 | 95% bootstrap interval |
|---|---|---|
| 3-day rain > 77 mm (threshold picked on the test years) | 0.31 | 0.17 - 0.45 |
| 3-day rain, threshold tuned on training years | 0.13 | 0.00 - 0.27 |
| I-D line as published | 0.27 | 0.17 - 0.36 |
| I-D line, intercept recalibrated on training years (used in the app) | 0.29 | 0.12 - 0.44 |
| API, as quoted (77 mm; decay assumed) | 0.23 | 0.15 - 0.32 |
| API, tuned on training years | 0.22 | 0.06 - 0.39 |
| TabPFN v2, richer features | 0.33 | 0.17 - 0.49 |

No method wins. The intervals all overlap, running from about 0.00 to 0.49 on 33 landslide days. The 77 mm rule's score is flattered, because I chose its threshold on the test years. Tuned on training years it falls to 0.13. Moving it from 183 mm to 186 mm changes F1 from 0.17 to 0.13. The published I-D line fires on about 28% of Kaski monsoon days and stays on for about two weeks after a big storm, so I recalibrated it. The version in the app fires on about 6% of monsoon days. I picked it because it raises fewer false alarms. Its score wasn't the reason.

TabPFN v2 on richer features (antecedent rainfall, soil moisture, lagged rain) had the highest nominal F1, 0.33. For a while it looked like the winner. It wasn't. The apparent win was a one-year artifact. Its F1 was 0.00 in 2022, 0.11 in 2023 and 0.58 in 2024, so the whole result came from 2024. Inside the training years its cross-validated AUC was 0.45, below chance. At serving time it would also need soil moisture from a different source than the one it was trained on. So I left it out of the app. I used TabPFN v2, and I did not use the newer versions because their license acceptance never registered on my account. Built with TabPFN v2 (Prior Labs).

## Why open and local mattered
The rule and the message layer run on a laptop. The rainfall data and ensemble forecasts come from Open-Meteo, which needs no key. The English message is written by Gemma 3 4B through Ollama on the same machine, with nothing leaving the device. The Nepali message is a fixed template. Gemma's Nepali was unreliable in my tests, with invented words and wrong month names. The interface is a local Streamlit prototype. Fetching the forecast needs internet, so this tool does not work offline in the hills. The offline part is the human chain in the fallback list, the people who can pass a warning on when phones and the app can't.

## Limits
- I only used rain. The August event was an ice-rock avalanche, and a rainfall model isn't built to predict that.
- I used reported events from BIPAD, which doesn't cover every landslide. Eight of the 124 Kaski landslide days fall outside June-September, and I left those out.
- My test set only has 33 landslide days. I also didn't compute confidence intervals for the app's live output.
- I used reanalysis rainfall for a grid cell at about 1,615 m near the district centroid. It isn't gauge data, and it doesn't describe the road itself. The ensemble spread likely understates real forecast error, since day-ahead forecasts differed from reanalysis by about 5 to 8 mm a day on average in the periods I checked.
- I only tested it on live off-season (October) forecasts and on synthetic and forced high-risk cases, because it isn't monsoon season.
- The other districts reuse the Kaski model, and I haven't validated them. The app says so.
- I haven't had a native speaker review either the English (Gemma 3 4B) or the Nepali (fixed template). Early on, Gemma's English made errors, including inventing and inverting a risk percentage. Now the app accepts Gemma's English only if its risk percentages match the numbers on screen exactly, it ends with the exact disclaimer, and it stays under 60 words. Otherwise it shows a fixed template. About a dozen final test calls passed. That's a small sample, and the wording can still be stilted.
- This is not an official warning. Follow DHM and local authorities.

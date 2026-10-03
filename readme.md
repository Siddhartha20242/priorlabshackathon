# Landslide Early Warning — Kaski, Nepal

A local prototype that estimates 3-day landslide risk from rainfall forecasts for Kaski district, near Pokhara. Built for Anuka, whose family travels a road in the district.

## What it does
- Streamlit app with a district dropdown (10 Gandaki districts)
- Monte Carlo risk percentage from 122 pooled ensemble members (ECMWF, GFS, ICON)
- Driver breakdown, English and Nepali message, fallback chain
- Footer: not an official warning

## Results
No threshold method wins on the 2022–2024 holdout. TabPFN v2 achieved the highest nominal F1 (0.333) but was rejected — its per-year F1 was 0.00 (2022), 0.11 (2023), 0.58 (2024), so the result came from one year, and its cross-validated AUC inside training years was 0.45, below chance.

## Run it
pip install -r requirements.txt
streamlit run landslide-early-warning/app.py

## Not
- Not road-level. District centroid grid cell, ~1,615 m.
- Not offline. Forecast fetch needs internet.
- Not an official warning. Follow DHM.
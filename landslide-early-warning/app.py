import json
import pathlib
import pandas as pd
import streamlit as st
from warning_tool import DISTRICTS, check_district
from message import make_message

HERE = pathlib.Path(__file__).parent
RULE = json.loads((HERE / "models/rule.json").read_text())
FOOTER = "This is not an official warning. Follow DHM and local authorities."
DISTRICT_BANNER = "Model trained on Kaski. Other districts use the same model and are not validated."
TABPFN_NOTE = ("TabPFN v2 was tested against the rainfall rules on a 2022–2024 holdout, including a version with richer features "
               "(antecedent rainfall, soil moisture, lagged rain). Its F1 was nominally the highest (0.33) but not reliably: its 95% "
               "interval overlaps every rule, it scored 0.00 in 2022 and 0.58 in 2024, and cross-validation inside the training years "
               "was below chance. The app therefore uses the simple I-D rule. Details in the write-up.")
FORECAST_NOTE = "Risk uses forecast rainfall. Forecast error reduces accuracy, and the spread between forecast scenarios understates it."
SEASON_NOTE = "The rule was set using June-September data only, so results outside the monsoon are less meaningful."
FALLBACK_CHAIN = [
    ("1. SMS", "Send a short text to the people who use the road or live below the slope."),
    ("2. Viber group", "Post in the ward or neighbourhood Viber group and ask for confirmation from people on the ground."),
    ("3. CDMC volunteer", "Ask a Community Disaster Management Committee member to go door to door in exposed households."),
    ("4. Siren or flag", "Use the local siren, whistle or flag if one exists."),
]

st.set_page_config(page_title="Landslide Early Warning", page_icon="🌧️", layout="centered")
st.markdown(
    f"""<style>
    .block-container {{ padding-bottom: 5rem; }}
    .fixed-footer {{ position: fixed; left: 0; right: 0; bottom: 0; z-index: 999; padding: .6rem 1rem;
        text-align: center; font-size: .9rem; font-weight: 600; background: var(--secondary-background-color, #f0f2f6);
        border-top: 1px solid rgba(128,128,128,.4); }}
    .risk {{ font-size: 1.05rem; font-weight: 700; }}
    </style><div class="fixed-footer">{FOOTER}</div>""",
    unsafe_allow_html=True,
)


def fallback_chain():
    st.markdown("**If this warning fires, here is the fallback chain:**")
    for step, text in FALLBACK_CHAIN:
        st.markdown(f"- **{step}**: {text}")
    st.caption("The CDMC contact list is community-maintained and is not in this app. Agree the real chain and names with your ward "
               "and CDMC in advance; the order and tools above are a template, not an instruction from any authority.")


def comparison_table() -> pd.DataFrame:
    t = pd.read_csv(HERE / "data/threshold_comparison.csv").set_index("method")[["precision", "recall", "f1", "roc_auc"]]
    r = json.loads((HERE / "data/tabpfn_rich_results.json").read_text())
    t.loc["TabPFN v2, richer features (threshold from training years)"] = [r["precision"], r["recall"], r["f1"], r["roc_auc"]]
    return t.round(2).rename(columns={"precision": "Precision", "recall": "Recall", "f1": "F1", "roc_auc": "ROC-AUC"})


st.title("Landslide early warning")
st.caption("Gandaki Province · rain-based risk for the next 3 days")

district = st.selectbox("District", DISTRICTS, index=DISTRICTS.index("Kaski"))
if district != "Kaski":
    st.warning(DISTRICT_BANNER)

network = st.toggle("Network available?", value=True,
                    help="Turn off when phones and internet are down. The forecast cannot update without a network.")
if not network:
    st.info("No network, so no forecast is shown: it cannot update offline. Use the human chain below. "
            "An app is not the offline signal; the people are.")
    fallback_chain()
    st.stop()

with st.expander("About this tool"):
    st.write(f"The rule: the Kanti Roadway intensity-duration line, I = 19.37 x D^-0.6215 (I in mm/h, D in hours, D from 48 to 308), "
             f"with its intercept multiplied by {RULE['id_scale']} so that it fits Kaski's training years (2015-2021). "
             "The Kanti study is from Bagmati Province, not Kaski, and the published line fires on about 28% of Kaski monsoon days, so I recalibrated it.")
    st.write(TABPFN_NOTE)
with st.expander("How the rules compared (2022-2024 monsoon test years)"):
    st.dataframe(comparison_table(), width="stretch")
    st.caption("33 landslide days in the test years, so differences of a few points are noise. The 77 mm rule's threshold was picked "
               "on the test years themselves. Lines with 'train' were tuned on 2015-2021 only. 'As published' lines were not tuned on Kaski data.")

if st.button("Check next 3 days", type="primary"):
    try:
        with st.spinner("Fetching rainfall forecasts..."):
            risks = check_district(district)
    except Exception as e:  # network / API problems should not crash the page
        st.error("Could not get the rainfall forecast right now. Check your internet connection and try again in a minute. "
                 "Nothing has been checked, so do not treat this as 'no risk'.")
        with st.expander("Technical detail"):
            st.code(f"{type(e).__name__}: {e}")
        fallback_chain()
        st.stop()

    cols = st.columns(3)
    for col, r in zip(cols, risks):
        with col:
            st.markdown(f"**{r['date']}**")
            st.markdown(f"<div class='risk'>Risk: {r['pct']}% ({r['n_fire']:,} of {r['n']:,} forecast scenarios)</div>", unsafe_allow_html=True)
            st.progress(r["pct"] / 100)
            st.caption(f"Central forecast rain that day: {r['central_rain_mm']} mm")

    st.caption(f"Scenario source: {risks[0]['source']}.")
    st.caption(f"What the percentage means: the share of 1,000 forecast rainfall scenarios that cross the rain level linked to reported "
               f"landslides in Kaski. It is not the chance of a landslide. In the 2022-2024 monsoons, on days this rule fired, a landslide "
               f"was reported in Kaski on {RULE['precision']:.0%} of them ({RULE['hits']} of {RULE['fired_days']}), against {RULE['base_rate']:.0%} of all "
               f"monsoon days, and the rule caught {RULE['recall']:.0%} of landslide days.")
    info = FORECAST_NOTE
    if any(not 6 <= int(r["date"][5:7]) <= 9 for r in risks):
        info += " " + SEASON_NOTE
    st.info(info)

    with st.expander("If this warning fires: fallback chain", expanded=any(r["pct"] >= 50 for r in risks)):
        fallback_chain()

    with st.spinner("Writing message..."):
        msg = make_message(district, risks)
    st.subheader("Message to forward")
    en, ne = st.tabs(["English", "नेपाली"])
    en.write(msg["en"])
    ne.write(msg["ne"])
    ne.warning("This Nepali text is a fixed template, not written by Gemma, and it has not been reviewed by a Nepali speaker. "
               "Check it before forwarding.")
    if msg["source"] == "template":
        st.caption("English source: fixed template (Gemma not running or failed its checks) · Nepali source: fixed template")
    else:
        st.caption(f"English source: {msg['source']} · Nepali source: fixed template")
        st.caption("The English was generated by a small language model (Gemma 3 4B). It can be inaccurate and has not been reviewed by a native speaker.")
    if msg["note"]:
        with st.expander("Gemma is not available - how to start it"):
            st.code(msg["note"])

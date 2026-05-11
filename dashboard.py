import streamlit as st
import pandas as pd
from predictor import LotteryForecastEngine
from auto_fetcher import fetch_lotteryusa_results, sample_data, STATE_SLUGS

st.set_page_config(page_title="Lottery Forecast Engine Pro", layout="wide")

st.title("Lottery Forecast Engine Pro")
st.caption("Auto-fetch previous results, analyze patterns, and rank next-draw picks.")

mode = st.radio(
    "Choose data mode",
    ["Auto Results Mode", "CSV Upload Backup"],
    horizontal=True
)

col1, col2, col3 = st.columns(3)

with col1:
    state = st.selectbox("State", sorted(STATE_SLUGS.keys()), index=sorted(STATE_SLUGS.keys()).index("SC"))

with col2:
    game = st.selectbox("Game", ["pick3", "pick4"])

with col3:
    draw = st.selectbox("Draw", ["both", "midday", "evening"])

top_n = st.slider("How many straight picks?", 10, 100, 25, 5)

df = None

if mode == "Auto Results Mode":
    if st.button("Fetch Results & Predict", type="primary"):
        with st.spinner("Fetching previous results and building prediction model..."):
            try:
                df = fetch_lotteryusa_results(state, game=game, draw=draw, limit=120)
                if df is None or len(df) < 10:
                    st.warning("Auto fetch did not return enough results. Showing built-in sample data so the app still runs.")
                    df = sample_data(state, game)
            except Exception as e:
                st.warning(f"Auto fetch failed: {e}")
                st.info("Using built-in sample data as a fallback. For real predictions, try again or use CSV Upload Backup.")
                df = sample_data(state, game)

elif mode == "CSV Upload Backup":
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)

if df is not None:
    st.subheader("Previous Results Used")
    st.dataframe(df, use_container_width=True)

    try:
        engine = LotteryForecastEngine(df, game=game, state=state, draw=draw)

        straight = engine.predict(top_n=top_n)
        boxed = engine.boxed(top_n=15)
        backtest = engine.backtest(top_n=top_n)

        c1, c2, c3 = st.columns(3)
        c1.metric("Results Loaded", len(engine.numbers))
        c2.metric("Straight Backtest", f"{backtest['straight_hit_rate']}%")
        c3.metric("Boxed Backtest", f"{backtest['boxed_hit_rate']}%")

        st.subheader("Top Straight Picks")
        st.dataframe(
            pd.DataFrame(straight, columns=["Number", "Score"]),
            use_container_width=True
        )

        st.subheader("Top Boxed Picks")
        st.dataframe(
            pd.DataFrame(boxed, columns=["Box", "Score"]),
            use_container_width=True
        )

        st.subheader("How To Read The Score")
        st.write(
            "The score ranks numbers against each other using digit strength, position strength, pairs, sums, root sums, gaps, repeats, and transition patterns. It is not a guaranteed win percentage."
        )

    except Exception as e:
        st.error(f"Prediction failed: {e}")
else:
    st.info("Choose Auto Results Mode and press Fetch Results & Predict, or upload a CSV backup.")
# Lottery Forecast Engine Pro - Auto Results Version

This version lets you select a state, game, and draw, then automatically attempts to pull recent public lottery results before generating ranked predictions.

## Run locally
pip install -r requirements.txt
streamlit run dashboard.py

## Deploy on Streamlit
Main file path:
dashboard.py

## Notes
Auto results depend on public websites being reachable and keeping the same page structure. If auto fetch fails, use CSV upload mode as backup.
import streamlit as st
import pandas as pd
from utils import fetch_alpaca_data, calculate_threshold_probability, calculate_streak_probability

st.set_page_config(page_title="Conditional Probabilities", page_icon="📊", layout="wide")

st.title("📊 Conditional Probability & Streak Analysis")
st.markdown("Evaluate historical next-day price probabilities following specific return thresholds and consecutive streaks.")

st.divider()

# --- MAIN BODY CONTROL PANEL ---
st.subheader("⚙️ Configuration & Parameters")

col1, col2 = st.columns([2, 3])

with col1:
    symbol = st.text_input("Stock Ticker", value="AAPL").upper()

with col2:
    interval = st.selectbox("Data Interval", ["daily", "weekly", "monthly"])

st.divider()

# --- FETCH DATA ---
with st.spinner(f"Fetching {interval} data for {symbol}..."):
    df, _, _ = fetch_alpaca_data(symbol, interval=interval)

if df.empty:
    st.error(f"Could not load data for {symbol}. Check API credentials or ticker symbol.")
else:
    st.subheader(f"Probability Analysis for: {symbol}")
    
    # Thresholds setup (Tasks 7-14)
    pos_thresholds = [2.0, 3.0, 4.0, 5.0, 6.0]
    neg_thresholds = [-2.0, -3.0, -4.0, -5.0, -6.0]
    
    col_pos, col_neg = st.columns(2)
    
    with col_pos:
        st.markdown("#### After Positive Return Thresholds")
        pos_data = []
        for t in pos_thresholds:
            prob = calculate_threshold_probability(df, threshold=t, direction="positive")
            pos_data.append({"Threshold": f"+{t}%", "Next-Day Win Prob (%)": prob})
        st.dataframe(pd.DataFrame(pos_data), hide_index=True, use_container_width=True)
        
    with col_neg:
        st.markdown("#### After Negative Return Thresholds")
        neg_data = []
        for t in neg_thresholds:
            prob = calculate_threshold_probability(df, threshold=t, direction="negative")
            neg_data.append({"Threshold": f"{t}%", "Next-Day Loss/Drop Prob (%)": prob})
        st.dataframe(pd.DataFrame(neg_data), hide_index=True, use_container_width=True)
        
    st.divider()
    
    # Streak Probabilities setup (Tasks 20-21)
    st.subheader("Consecutive Streak Probabilities")
    streak_lengths = [2, 3, 4, 5, 6]
    
    streak_col1, streak_col2 = st.columns(2)
    
    with streak_col1:
        st.markdown("#### After Consecutive Positive Days")
        pos_streak_data = []
        for s in streak_lengths:
            prob = calculate_streak_probability(df, streak_length=s, direction="positive")
            pos_streak_data.append({"Streak Length": f"{s} Days", "Next-Day Positive Prob (%)": prob})
        st.dataframe(pd.DataFrame(pos_streak_data), hide_index=True, use_container_width=True)
        
    with streak_col2:
        st.markdown("#### After Consecutive Negative Days")
        neg_streak_data = []
        for s in streak_lengths:
            prob = calculate_streak_probability(df, streak_length=s, direction="negative")
            neg_streak_data.append({"Streak Length": f"{s} Days", "Next-Day Negative Prob (%)": prob})
        st.dataframe(pd.DataFrame(neg_streak_data), hide_index=True, use_container_width=True)
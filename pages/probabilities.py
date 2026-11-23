# Conditional Probabilities & Streak Analysis

import streamlit as st
import pandas as pd

from sidebar import render_sidebar
from utils.loader import fetch_alpaca_data
from utils.analytics import threshold_success, streak_success

st.set_page_config(page_title="Conditional Probabilities", layout="wide")
render_sidebar("Probability Analysis")

st.title("Conditional Probability & Streak Analysis")
st.write(
    "Probabilities are calculated from historical price data for the selected interval. "
    "For thresholds, this measures how often the next interval continued in the same direction "
    "after a return of at least ±X%. For streaks, this measures how often the next interval "
    "was positive (or negative) after X consecutive intervals in that direction. "
    "Results show both the occurrence count and the resulting percentage."
)

st.subheader("Configuration")

col1, col2 = st.columns([2, 2])
with col1:
    symbol = st.text_input("Stock ticker", value="AAPL").upper().strip()
with col2:
    interval = st.selectbox("Data interval", ["daily", "weekly", "monthly"])

thresholds = st.multiselect(
    "Thresholds / streak lengths",
    options=[1, 2, 3, 4, 5, 6, 7, 8, 10],
    default=[2, 3, 4, 5, 6],
    help="Used as +X% / -X% return thresholds and as X-period streak lengths.",
)

period_label = {"daily": "Day", "weekly": "Week", "monthly": "Month"}[interval]


def build_table(rows, value_col, success_col, prob_col):
    """Small helper so the four tables stay consistent."""
    return pd.DataFrame(rows, columns=[value_col, "Occurrences", success_col, prob_col])


if st.button("Run analysis", type="primary"):
    if not symbol:
        st.warning("Enter a ticker.")
        st.stop()
    if not thresholds:
        st.warning("Select at least one threshold / streak length.")
        st.stop()

    with st.spinner(f"Fetching {interval} data for {symbol}…"):
        df, _, _ = fetch_alpaca_data(symbol, interval=interval)

    if df is None or df.empty:
        st.error(f"Could not load data for {symbol}.")
        st.stop()

    st.subheader(f"Probability analysis for {symbol} ({interval})")
    st.caption(
        f"Occurrences = number of times the condition was met. "
        f"Closed Higher/Lower = how many of those were followed by an up/down {period_label.lower()}. "
        f"Probability = Closed Higher (or Lower) ÷ Occurrences."
    )

    # Threshold tables
    col_pos, col_neg = st.columns(2)

    with col_pos:
        st.markdown("#### After positive return thresholds")
        rows = []
        for t in sorted(thresholds):
            success = threshold_success(df, threshold=float(t), direction="positive")
            n = len(success)
            higher = int(success.sum()) if n else 0
            prob = round(higher / n * 100, 2) if n else 0.0
            rows.append([f"+{t}%", n, higher, prob])
        st.dataframe(
            build_table(rows, "Threshold", "Closed Higher", f"Next {period_label} Up Prob (%)"),
            hide_index=True,
            use_container_width=True,
        )

    with col_neg:
        st.markdown("#### After negative return thresholds")
        rows = []
        for t in sorted(thresholds):
            success = threshold_success(df, threshold=float(-t), direction="negative")
            n = len(success)
            lower = int(success.sum()) if n else 0
            prob = round(lower / n * 100, 2) if n else 0.0
            rows.append([f"-{t}%", n, lower, prob])
        st.dataframe(
            build_table(rows, "Threshold", "Closed Lower", f"Next {period_label} Down Prob (%)"),
            hide_index=True,
            use_container_width=True,
        )

    # Streak tables
    st.divider()
    st.subheader("Consecutive streak probabilities")
    st.caption(
        f"Same calculation as above, except the condition is a run of consecutive "
        f"up or down {period_label.lower()}s instead of a single interval return threshold."
    )

    streak_col1, streak_col2 = st.columns(2)

    with streak_col1:
        st.markdown(f"#### After consecutive positive {period_label.lower()}s")
        rows = []
        for s in sorted(thresholds):
            success = streak_success(df, streak_length=int(s), direction="positive")
            n = len(success)
            higher = int(success.sum()) if n else 0
            prob = round(higher / n * 100, 2) if n else 0.0
            rows.append([f"{s} {period_label}s", n, higher, prob])
        st.dataframe(
            build_table(rows, "Streak length", "Closed Higher", f"Next {period_label} Up Prob (%)"),
            hide_index=True,
            use_container_width=True,
        )

    with streak_col2:
        st.markdown(f"#### After consecutive negative {period_label.lower()}s")
        rows = []
        for s in sorted(thresholds):
            success = streak_success(df, streak_length=int(s), direction="negative")
            n = len(success)
            lower = int(success.sum()) if n else 0
            prob = round(lower / n * 100, 2) if n else 0.0
            rows.append([f"{s} {period_label}s", n, lower, prob])
        st.dataframe(
            build_table(rows, "Streak length", "Closed Lower", f"Next {period_label} Down Prob (%)"),
            hide_index=True,
            use_container_width=True,
        )
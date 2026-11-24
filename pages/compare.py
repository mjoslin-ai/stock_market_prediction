# Multi Stock Comparison & Correlation Analysis


import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

from sidebar import render_sidebar
from utils.loader import fetch_alpaca_data, alpaca_client


st.set_page_config(page_title="Multi-Stock Comparison", layout="wide")
render_sidebar("Performance Comparison")

st.title("Multi-Stock Comparison & Correlation Analysis")
st.write(
    "Compare price performance across multiple equities, analyze normalized returns, "
    "and inspect return correlations. Data is limited to the selected lookback window "
    "(default 1 year)."
)


def is_common_stock(symbol: str) -> bool:
    s = symbol.upper()
    if any(s.endswith(suf) for suf in ("W", "R", "U", "WS", "WT")):
        return False
    return "." not in s and "-" not in s


@st.cache_data(ttl=3600)
def load_common_stock_symbols() -> list[str]:
    """Sorted list of active common-stock symbols from Alpaca."""
    api = alpaca_client()
    assets = api.stock.assets.get_all(status="active")
    if isinstance(assets, pd.DataFrame):
        df = assets
    else:
        df = pd.DataFrame(
            [a.__dict__ if hasattr(a, "__dict__") else a for a in assets]
        )

    if "symbol" not in df.columns:
        return []

    symbols = df["symbol"].dropna().astype(str).str.upper()
    return sorted(s for s in symbols if is_common_stock(s))


st.subheader("Configuration")

ticker_options = load_common_stock_symbols()
default_tickers = [
    t for t in ["AAPL", "AMZN", "GOOGL", "META", "NVDA"] if t in ticker_options
]

col1, col2, col3 = st.columns([3, 1.5, 1.5])

with col1:
    selected_tickers = st.multiselect(
        "Select tickers (2–5)",
        options=ticker_options,
        default=default_tickers,
        max_selections=5,
    )

with col2:
    interval = st.selectbox("Data interval", ["daily", "weekly", "monthly"])

with col3:
    lookback_years = st.selectbox(
        "Lookback",
        options=[1, 2, 3, 5],
        index=0,
        format_func=lambda y: f"{y} year{'s' if y > 1 else ''}",
    )


if st.button("Compare", type="primary"):
    if len(selected_tickers) < 2:
        st.warning("Select at least 2 stocks.")
        st.stop()

    cutoff = datetime.now() - timedelta(days=lookback_years * 365)
    price_data = {}

    with st.spinner("Fetching historical data…"):
        for ticker in selected_tickers:
            df, _, _ = fetch_alpaca_data(ticker, interval=interval)
            if df is None or df.empty or "close" not in df.columns:
                continue
            df = df[df.index >= cutoff]
            if not df.empty:
                price_data[ticker] = df["close"]

    if not price_data:
        st.error("Could not retrieve data for the selected tickers.")
        st.stop()

    combined_df = pd.DataFrame(price_data).dropna()
    if combined_df.empty:
        st.error("No overlapping data in the selected lookback window.")
        st.stop()

    # Normalized performance
    st.subheader("Normalized Price Performance")
    st.caption("Prices rescaled to start at 100 for easier comparison.")

    normalized_df = combined_df.div(combined_df.iloc[0]).mul(100)

    fig_norm = go.Figure()
    for ticker in normalized_df.columns:
        fig_norm.add_trace(
            go.Scatter(x=normalized_df.index, y=normalized_df[ticker], name=ticker, mode="lines")
        )

    fig_norm.update_layout(
        title="Normalized Stock Prices (Base = 100)",
        xaxis_title="Date",
        yaxis_title="Normalized Value",
        template="plotly_white",
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_norm, use_container_width=True)

    # Summary table
    st.subheader("Summary")
    summary = pd.DataFrame({
        "Ticker": combined_df.columns,
        "Start Price ($)": combined_df.iloc[0].round(2).values,
        "Latest Price ($)": combined_df.iloc[-1].round(2).values,
        "Total Return (%)": (
            (combined_df.iloc[-1] / combined_df.iloc[0] - 1) * 100
        ).round(2).values,
    })
    st.dataframe(summary, hide_index=True, use_container_width=True)

    # Correlation 
    st.subheader("Return Correlation")
    st.caption(
        "Pearson correlation of lookback-period returns. "
        "Coefficients range from -1 (perfect negative) to +1 (perfect positive)."
    )

    returns_df = combined_df.pct_change().dropna()
    corr_matrix = returns_df.corr()
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    corr_lower = corr_matrix.mask(mask)

    fig_corr = px.imshow(
        corr_lower,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Return Correlation Matrix",
    )
    fig_corr.update_layout(template="plotly_white", height=450)
    st.plotly_chart(fig_corr, use_container_width=True)
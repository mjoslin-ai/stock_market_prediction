# utils/loader.py
# Load historic stock data from Alpaca via PyAlpacaAPI
from tracemalloc import start

import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from py_alpaca_api import PyAlpacaAPI

@st.cache_data(ttl=3600) # Cache the data for 1 hour
def fetch_alpaca_data(symbol, interval):
    """
    Pull daily or hourly data from Alpaca using PyAlpacaAPI.
    Supported intervals: "day", "week", "month"
    Lookback: 5 years for all intervals.
    """
    api_key = st.secrets["alpaca"]["api_key"]
    api_secret = st.secrets["alpaca"]["api_secret"]

    # Paper trading api
    api = PyAlpacaAPI(
        api_key=api_key,
        api_secret=api_secret,
        api_paper=True
    )

    # Interval mapping for Alpaca API
    interval = interval.lower().strip()
    if interval == "daily":
        timeframe = "1d"
    elif interval == "weekly":
        timeframe = "1w"
    elif interval == "monthly":
        timeframe = "1M"
    else:
        raise ValueError(f"Unsupported interval: '{interval}'. Use 'day', 'week', or 'month'.")

    # 5-year lookback for all intervals
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5*365)

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    # Use the free IEX feed
    df = api.stock.history.get_stock_data(
        symbol=symbol.upper(),
        start=start_str,
        end=end_str,
        timeframe=timeframe,
        feed="iex",
        adjustment="raw"
    )

    # Set date as index and sort
    if "date" in df.columns:
        df = df.set_index("date")
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    # Keep only relevant columns
    keep_cols = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
    df = df[keep_cols]

    for col in keep_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df
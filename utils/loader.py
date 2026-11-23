# utils/loader.py
# Load historic stock data from Alpaca via PyAlpacaAPI


import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from py_alpaca_api import PyAlpacaAPI
import yfinance as yf


def alpaca_client():
    """Create a PyAlpacaAPI client using Streamlit secrets."""
    api_key = st.secrets["alpaca"]["api_key"]
    api_secret = st.secrets["alpaca"]["api_secret"]

    return PyAlpacaAPI(
        api_key=api_key,
        api_secret=api_secret,
        api_paper=True
    )


def get_timeframe(interval):
    """Map user interval to Alpaca timeframe."""
    interval = interval.lower().strip()
    mapping = {
        "daily": "1d",
        "weekly": "1w",
        "monthly": "1M",
    }
    if interval not in mapping:
        raise ValueError(
            f"Unsupported interval: '{interval}'. Use 'day', 'week', or 'month'."
        )
    return mapping[interval]


def get_date_range(years):
    """Return start and end date strings for the lookback period."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    return (
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d"),
    )


def get_exchange(api, symbol):
    """Fetch the listed exchange for a symbol. Returns None on failure."""
    try:
        asset = api.stock.assets.get(symbol.upper())
        return asset.exchange
    except Exception as e:
        st.warning(f"Could not retrieve exchange for {symbol}: {e}")
        return None


def fetch_price_history(api, symbol, start, end, timeframe):
    """Fetch raw price history from Alpaca (IEX (free) feed). Adjustment is set to 'split' to account for stock splits."""
    try:
        return api.stock.history.get_stock_data(
            symbol=symbol.upper(),
            start=start,
            end=end,
            timeframe=timeframe,
            feed="iex",
            adjustment="split",
        )
    except Exception as e:
        st.warning(f"Could not retrieve price history for {symbol}: {e}")
        return None


def process_price_data(df):
    """Clean and standardize the price DataFrame."""
    if df is None or df.empty:
        return df

    if "date" in df.columns:
        df = df.set_index("date")
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    keep_cols = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
    df = df[keep_cols].copy()

    for col in keep_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def get_market_cap(symbol):
    """Fetch market cap from Yahoo Finance. Returns None on failure."""
    try:
        ticker = yf.Ticker(symbol.upper())
        market_cap = None

        # Try fast_info first
        try:
            market_cap = ticker.fast_info.get("market_cap")
        except Exception:
            pass

        # Fall back to the slower version
        if market_cap is None:
            try:
                info = ticker.info
                market_cap = info.get("marketCap") or info.get("market_cap")
            except Exception:
                pass

        return market_cap
    except Exception as e:
        st.warning(f"Could not retrieve market cap for {symbol}: {e}")
        return None


@st.cache_data(ttl=18000)  # Cache the data for 5 hours
def fetch_alpaca_data(symbol, interval):
    """
    Pull stock price, volume, listed exchange, and market cap data from Alpaca.

    Supported intervals: daily/weekly/monthly.
    Lookback: 5 years for all intervals.

    Returns:
        (df, exchange, market_cap) or (None, None, None) on failure.
    """
    api = alpaca_client()

    # Map interval and compute date range
    timeframe = get_timeframe(interval)
    start_str, end_str = get_date_range(years=5)

    # Exchange listing
    exchange = get_exchange(api, symbol)
    if exchange is None:
        return None, None, None

    # Price history
    raw_df = fetch_price_history(api, symbol, start_str, end_str, timeframe)
    if raw_df is None:
        return None, None, None

    df = process_price_data(raw_df)

    # Market cap (Yahoo Finance)
    market_cap = get_market_cap(symbol)

    return df, exchange, market_cap






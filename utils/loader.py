# Load data from Alpha Vantage API
import requests
import pandas as pd
import streamlit as st

@st.cache_data(ttl=3600) # Cache the data for 1 hour
def fetch_alpha_vantage_data(symbol, interval):
    """
    Pull daily or hourly data from Alpha Vantage.
    """
    api_key = st.secrets["alpha_vantage"]["api_key"]
    base_url = "https://www.alphavantage.co/query"


    if interval.lower() == "hourly":
        function = "TIME_SERIES_INTRADAY"
        time_key = "Time Series (60min)"
        params = {
            "function": function,
            "symbol": symbol.upper(),
            "interval": "60min",
            "apikey": api_key,
            "outputsize": "compact",
        }
    else:
        function = "TIME_SERIES_DAILY"
        time_key = "Time Series (Daily)"
        params = {
            "function": function,
            "symbol": symbol.upper(),
            "apikey": api_key,
            "outputsize": "compact",
        }

    response = requests.get(base_url, params=params)
    data = response.json()

    # Convert json data to DataFrame
    df = pd.DataFrame.from_dict(data[time_key], orient="index")

    # Rename columns
    df = df.rename(columns={
        "1. open": "open",
        "2. high": "high",
        "3. low": "low",
        "4. close": "close",
        "5. volume": "volume",
    })

    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col])

    return df


fetch_alpha_vantage_data("MSFT", "hourly").head()
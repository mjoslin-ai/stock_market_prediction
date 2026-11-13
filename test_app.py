# test_app.py
import streamlit as st
from utils.loader import fetch_alpha_vantage_data

st.title("Alpha Vantage Loader Test")

# Test ticker input
symbol = st.text_input("Enter Ticker", value="AAPL")
interval = st.selectbox("Select Interval", ["daily", "hourly"])

if st.button("Fetch Data"):
    with st.spinner(f"Fetching {interval} data for {symbol}..."):
        df = fetch_alpha_vantage_data(symbol, interval)
        
    if not df.empty:
        st.success(f"Successfully fetched {len(df)} rows!")
        st.dataframe(df.tail()) # Show most recent data
        st.line_chart(df["close"]) # Quick visual check
    else:
        st.error("Returned dataframe is empty. Check API limits or error messages above.")
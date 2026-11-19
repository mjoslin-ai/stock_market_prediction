import streamlit as st
import plotly.graph_objects as go
from utils import fetch_alpaca_data, calculate_moving_averages

st.set_page_config(page_title="Single Stock Analysis", page_icon="📈", layout="wide")

st.title("📈 Single Stock & Moving Average Analysis")
st.markdown("Analyze historical stock performance, 5-year trends, and moving average overlays using Alpaca data.")

st.divider()

# --- MAIN BODY CONTROL PANEL (NO SIDEBAR CONTROLS) ---
st.subheader("⚙️ Configuration & Parameters")

col1, col2, col3 = st.columns([1.5, 1.5, 3])

with col1:
    symbol = st.text_input("Stock Ticker", value="AAPL").upper()

with col2:
    # Supported intervals based on your Alpaca loader implementation
    interval = st.selectbox("Data Interval", ["daily", "weekly", "monthly"])

with col3:
    st.markdown("**Moving Average Overlays**")
    ma_col1, ma_col2, ma_col3 = st.columns(3)
    with ma_col1:
        show_sma20 = st.checkbox("SMA 20", value=True)
    with ma_col2:
        show_sma50 = st.checkbox("SMA 50", value=True)
    with ma_col3:
        show_sma150 = st.checkbox("SMA 150", value=False)

st.divider()

# --- DATA FETCHING & RENDERING ---
with st.spinner(f"Fetching {interval} data for {symbol} from Alpaca..."):
    df, _, _ = fetch_alpaca_data(symbol, interval=interval)

if df.empty:
    st.error(f"Could not load data for {symbol}. Verify the ticker symbol, check your Alpaca API credentials in `secrets.toml`, or check rate limits.")
else:
    # Calculate moving averages using the imported analytics function[cite: 1, 2]
    df_ma = calculate_moving_averages(df)
    
    # Build Plotly Chart
    fig = go.Figure()
    
    # Main close price line
    fig.add_trace(go.Scatter(
        x=df_ma.index, 
        y=df_ma['close'], 
        name=f"{symbol} Close", 
        line=dict(color='#2980b9', width=1.5)
    ))
    
    # Moving average overlays (Task 6)
    if show_sma20 and 'SMA_20' in df_ma.columns:
        fig.add_trace(go.Scatter(
            x=df_ma.index, 
            y=df_ma['SMA_20'], 
            name="SMA 20", 
            line=dict(color='#e67e22', width=1)
        ))
        
    if show_sma50 and 'SMA_50' in df_ma.columns:
        fig.add_trace(go.Scatter(
            x=df_ma.index, 
            y=df_ma['SMA_50'], 
            name="SMA 50", 
            line=dict(color='#27ae60', width=1)
        ))
        
    if show_sma150 and 'SMA_150' in df_ma.columns:
        fig.add_trace(go.Scatter(
            x=df_ma.index, 
            y=df_ma['SMA_150'], 
            name="SMA 150", 
            line=dict(color='#8e44ad', width=1)
        ))
        
    fig.update_layout(
        title=dict(text=f"{symbol} Price Action & Moving Average Overlays ({interval.capitalize()})", font=dict(size=18)),
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_dark",
        height=550,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent Data Preview Table
    with st.expander("View Raw Price Data Table"):
        st.dataframe(df.tail(20), use_container_width=True)
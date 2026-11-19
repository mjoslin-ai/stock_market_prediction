import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils import fetch_alpaca_data 

st.set_page_config(page_title="Multi-Stock Comparison", page_icon="📉", layout="wide")

st.title("📉 Multi-Stock Comparison & Correlation Analysis")
st.markdown("Compare price performance across multiple equities (such as FAANG + NVIDIA), analyze normalized returns, and inspect return correlations.")

st.divider()

# --- MAIN BODY CONTROL PANEL (NO SIDEBAR CONTROLS) ---
st.subheader("⚙️ Configuration & Parameters")

# Default basket covering FAANG + NVIDIA
default_tickers = ["AAPL", "AMZN", "GOOGL", "META", "NVDA", "NFLX"]

col1, col2 = st.columns([3, 2])

with col1:
    selected_tickers = st.multiselect(
        "Select Tickers (2 to 6 recommended)",
        options=["AAPL", "AMZN", "GOOGL", "META", "NVDA", "NFLX", "MSFT", "TSLA", "AMD"],
        default=default_tickers
    )

with col2:
    interval = st.selectbox("Data Interval", ["daily", "weekly", "monthly"])

st.divider()

if len(selected_tickers) < 2:
    st.warning("Please select at least 2 stocks to perform comparison and correlation analyses.")
else:
    # --- FETCH & COMBINE DATA ---
    price_data = {}
    with st.spinner("Fetching historical data for selected stocks from Alpaca..."):
        for ticker in selected_tickers:
            # Fetch data using your Alpaca loader utility[cite: 1, 3]
            df, _, _ = fetch_alpaca_data(ticker, interval=interval)  #[cite: 1, 3]
            if not df.empty and 'close' in df.columns:
                price_data[ticker] = df['close']

    if not price_data:
        st.error("Could not retrieve data for the selected tickers.")
    else:
        combined_df = pd.DataFrame(price_data).dropna()

        # --- TASKS 17, 18, 19: NORMALIZED COMPARISON CHART ---
        st.subheader("📈 Normalized Price Performance Comparison")
        st.markdown("Prices are rescaled starting at 100 to allow clear comparative analysis across stocks with different absolute share values[cite: 3].")

        # Normalize prices to start at 100
        normalized_df = (combined_df / combined_df.iloc[0]) * 100

        fig_norm = go.Figure()
        for ticker in normalized_df.columns:
            fig_norm.add_trace(go.Scatter(
                x=normalized_df.index,
                y=normalized_df[ticker],
                name=ticker,
                mode='lines'
            ))

        fig_norm.update_layout(
            title="Normalized Stock Prices (Base = 100)",
            xaxis_title="Date",
            yaxis_title="Normalized Value ($)",
            template="plotly_dark",
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_norm, use_container_width=True)

        # --- TASK 15: COMPARISON TABLE ---
        st.subheader("📊 Stock Summary & Comparison Table")
        
        summary_data = []
        for ticker in combined_df.columns:
            start_price = combined_df[ticker].iloc[0]
            end_price = combined_df[ticker].iloc[-1]
            total_return = ((end_price - start_price) / start_price) * 100
            summary_data.append({
                "Ticker": ticker,
                "Start Price ($)": round(start_price, 2),
                "Latest Price ($)": round(end_price, 2),
                "Total Return (%)": round(total_return, 2)
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, hide_index=True, use_container_width=True)

        st.divider()

        # --- TASK 16: CORRELATION / COLLINEARITY ANALYSIS ---
        st.subheader("🔗 Return Correlation & Collinearity Analysis")
        st.markdown("Calculates Pearson correlation coefficients of period returns across the selected asset basket.")

        returns_df = combined_df.pct_change().dropna()
        corr_matrix = returns_df.corr()

        # Plot correlation heatmap using Plotly Express
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1,
            title="Stock Return Correlation Matrix"
        )
        fig_corr.update_layout(template="plotly_dark", height=450)
        st.plotly_chart(fig_corr, use_container_width=True)
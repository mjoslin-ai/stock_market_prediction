# landing page: stock history plot
# run: streamlit run app.py

import plotly.graph_objects as go
import streamlit as st

from sidebar import render_sidebar
from utils.analytics import calculate_moving_averages, calculate_daily_returns
from utils.loader import fetch_alpaca_data

st.set_page_config(
    page_title="Stock Market Price Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)
render_sidebar("Market Trend")

st.title("Stock Market Price Analytics")
st.write(
    "Daily, weekly, and monthly closing prices with moving averages (5-year lookback). "
    "Data is sourced from [Alpaca](https://alpaca.markets/) paper trading API "
    "(split adjusted) and market cap information from "
    "[Yahoo Finance](https://pypi.org/project/yfinance/). "
    "Output is cached for 5 hours to reduce API calls."
)

# Session state defaults
defaults = {
    "loaded": False,
    "symbol": "",
    "df": None,
    "exchange": None,
    "market_cap": None,
    "chart_interval": "daily",
    "chart_range": "5Y",
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# Initial visible inputs
col_input, col_btn = st.columns([3, 1])
symbol_input = col_input.text_input(
    "Symbol",
    value=st.session_state.symbol,
    placeholder="Enter a ticker (e.g. AAPL)",
    label_visibility="collapsed",
).upper().strip()

load_clicked = col_btn.button("Load", type="primary", use_container_width=True)

if load_clicked and symbol_input:
    with st.spinner(f"Loading {symbol_input}…"):
        df, exchange, market_cap = fetch_alpaca_data(
            symbol_input, st.session_state.chart_interval
        )
    if df is None or df.empty:
        st.warning(f"No price data returned for {symbol_input}.")
        st.session_state.loaded = False
    else:
        st.session_state.symbol = symbol_input
        st.session_state.df = df
        st.session_state.exchange = exchange
        st.session_state.market_cap = market_cap
        st.session_state.loaded = True
        st.rerun()

if not st.session_state.loaded or st.session_state.df is None:
    st.stop()

df = st.session_state.df
symbol = st.session_state.symbol
exchange = st.session_state.exchange
market_cap = st.session_state.market_cap

# Controls
RANGES = {
    "1M": 30,
    "3M": 90,
    "6M": 180,
    "1Y": 365,
    "2Y": 365 * 2,
    "5Y": 365 * 5,
}

controls = st.columns([1.5, 1.2, 1.2])
interval_label = controls[0].radio(
    "Interval",
    ["Daily", "Weekly", "Monthly"],
    horizontal=True,
    index=["daily", "weekly", "monthly"].index(st.session_state.chart_interval),
)
chart_type = controls[1].selectbox("Plot", ["Candlestick", "Line"])
range_label = controls[2].selectbox(
    "Range",
    list(RANGES.keys()),
    index=list(RANGES.keys()).index(st.session_state.chart_range),
)

# Re acquire data if interval changed
new_interval = interval_label.lower()
if new_interval != st.session_state.chart_interval:
    with st.spinner(f"Reloading {symbol} ({new_interval})…"):
        df, exchange, market_cap = fetch_alpaca_data(symbol, new_interval)
    if df is not None and not df.empty:
        st.session_state.chart_interval = new_interval
        st.session_state.df = df
        st.session_state.exchange = exchange
        st.session_state.market_cap = market_cap
        st.rerun()
    else:
        st.warning(f"Could not load {new_interval} data for {symbol}.")
        st.stop()

st.session_state.chart_range = range_label

# Moving average toggles
ma_cols = st.columns(3)
show_sma20 = ma_cols[0].checkbox("SMA 20", value=False)
show_sma50 = ma_cols[1].checkbox("SMA 50", value=False)
show_sma150 = ma_cols[2].checkbox("SMA 150", value=False)

# Range filter
days = RANGES[range_label]
plot_df = df.iloc[-days:] if len(df) > days else df.copy()

# Calculations
plot_df = calculate_moving_averages(plot_df)
returns_df = calculate_daily_returns(plot_df)

day_change = None
if "daily_return" in returns_df.columns and returns_df["daily_return"].notna().any():
    day_change = returns_df["daily_return"].dropna().iloc[-1]

# Metrics
metrics = st.columns(2)
day_change_help = "Percentage change from the previous bar’s close price to the latest close."

metrics[0].metric(
    "Day change",
    f"{day_change:+.2f}%" if day_change is not None else "—",
    help=day_change_help,
)
metrics[1].metric(
    "Market cap",
    f"${market_cap / 1e9:,.1f}B" if market_cap else "—",
)

# Main chart
plot = plot_df.dropna(subset=["close"])
index = plot.index

figure = go.Figure()

if chart_type == "Candlestick":
    figure.add_trace(
        go.Candlestick(
            x=index,
            open=plot["open"],
            high=plot["high"],
            low=plot["low"],
            close=plot["close"],
            name="Price",
            increasing_line_color="#143d32",
            decreasing_line_color="#9c3b32",
        )
    )
else:
    figure.add_trace(
        go.Scatter(
            x=index,
            y=plot["close"],
            name="Close",
            line={"color": "#143d32", "width": 2},
        )
    )

ma_config = {
    "SMA_20": (show_sma20, "#1c1915"),
    "SMA_50": (show_sma50, "#9c3b32"),
    "SMA_150": (show_sma150, "#3d5a80"),
}
for col, (enabled, color) in ma_config.items():
    if enabled and col in plot.columns:
        figure.add_trace(
            go.Scatter(
                x=index,
                y=plot[col],
                name=col.replace("_", " "),
                line={"color": color, "width": 1.5},
            )
        )

figure.update_layout(
    height=560,
    margin={"l": 16, "r": 16, "t": 24, "b": 16},
    paper_bgcolor="#fffdf8",
    plot_bgcolor="#fffdf8",
    legend={"orientation": "h"},
    xaxis_rangeslider_visible=(chart_type == "Candlestick"),
    xaxis={"showgrid": False},
    yaxis={"showgrid": True, "gridcolor": "#e4dccf"},
)
st.plotly_chart(figure, use_container_width=True)
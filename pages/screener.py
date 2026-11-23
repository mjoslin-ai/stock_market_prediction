# Screens top trending stocks by daily % change

import streamlit as st
import pandas as pd
import concurrent.futures

from sidebar import render_sidebar
from utils.loader import alpaca_client, get_market_cap


st.set_page_config(page_title="Stock Market Price Analytics", layout="wide")
render_sidebar("Stock Screener")

st.title("Trending Stocks Screener")
st.write(
    "Fetches the top 200 gainers or losers from the API, then filters them by "
    "your selected exchanges and market-cap threshold. Results show the top 10 "
    "after filtering."
)


@st.cache_data(ttl=3600)
def load_assets():
    """Active US-equity assets as a DataFrame."""
    api = alpaca_client()
    assets = api.stock.assets.get_all(status="active")
    if isinstance(assets, pd.DataFrame):
        return assets
    return pd.DataFrame(
        [a.__dict__ if hasattr(a, "__dict__") else a for a in assets]
    )


def is_common_stock(symbol: str) -> bool:
    s = symbol.upper()
    if any(s.endswith(suf) for suf in ("W", "R", "U", "WS", "WT")):
        return False
    return "." not in s and "-" not in s


def normalize_screener_result(raw) -> pd.DataFrame:
    """Turn get_gainers / get_losers output into a consistent DataFrame."""
    if raw is None:
        return pd.DataFrame()

    if isinstance(raw, pd.DataFrame):
        df = raw.copy()
    elif isinstance(raw, (list, tuple)):
        rows = []
        for item in raw:
            if isinstance(item, dict):
                rows.append(item)
            elif hasattr(item, "__dict__"):
                rows.append(item.__dict__)
            else:
                rows.append({"symbol": str(item)})
        df = pd.DataFrame(rows)
    else:
        return pd.DataFrame()

    if df.empty:
        return df

    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

    if "change_percentage" in df.columns:
        df = df.rename(columns={"change_percentage": "change_pct"})
    elif "change" in df.columns and "change_pct" not in df.columns:
        df = df.rename(columns={"change": "change_pct"})
    elif "percent_change" in df.columns:
        df = df.rename(columns={"percent_change": "change_pct"})

    if "symbol" not in df.columns:
        return pd.DataFrame()

    df["symbol"] = df["symbol"].astype(str).str.upper()
    if "change_pct" in df.columns:
        df["change_pct"] = pd.to_numeric(df["change_pct"], errors="coerce")

    return df


assets_df = load_assets()
available_exchanges = (
    sorted(assets_df["exchange"].dropna().unique().tolist())
    if "exchange" in assets_df.columns
    else ["NASDAQ", "NYSE"]
)

selected = st.multiselect(
    "Exchanges",
    options=available_exchanges,
    default=(
        ["NASDAQ", "NYSE"]
        if {"NASDAQ", "NYSE"}.issubset(set(available_exchanges))
        else available_exchanges[:2]
    ),
)

cap_col1, cap_col2, cap_col3 = st.columns([2, 1, 1])
market_cap_input = cap_col1.number_input(
    "Market cap threshold (billions USD)",
    min_value=0.0,
    value=5.0,
    step=0.5,
    format="%.1f",
)
direction = cap_col2.radio("Market cap filter", ["Above", "Below"], horizontal=True)
mover_type = cap_col3.radio("Show", ["Gainers", "Losers"], horizontal=True)
threshold = market_cap_input * 1_000_000_000


if st.button("Run screen", type="primary"):
    if not selected:
        st.warning("Select at least one exchange.")
        st.stop()

    with st.spinner("Building universe…"):
        universe = assets_df[assets_df["exchange"].isin(selected)].copy()
        universe = universe[universe["symbol"].apply(is_common_stock)]
        symbol_to_name = (
            dict(zip(universe["symbol"], universe["name"]))
            if "name" in universe.columns
            else {}
        )
        symbol_to_exchange = (
            dict(zip(universe["symbol"], universe["exchange"]))
            if "exchange" in universe.columns
            else {}
        )
        valid_symbols = set(universe["symbol"])

    api = alpaca_client()
    TOP_N = 200

    with st.spinner(f"Fetching top {TOP_N} {mover_type.lower()}…"):
        try:
            if mover_type == "Gainers":
                raw_movers = api.stock.screener.get_gainers(top=TOP_N)
            else:
                raw_movers = api.stock.screener.get_losers(top=TOP_N)
        except AttributeError:
            if mover_type == "Gainers":
                raw_movers = api.stock.screener.gainers(total_gainers_returned=TOP_N)
            else:
                raw_movers = api.stock.screener.losers(total_losers_returned=TOP_N)
        except Exception as e:
            st.error(f"Screener call failed: {e}")
            st.stop()

    movers_df = normalize_screener_result(raw_movers)
    if movers_df.empty:
        st.warning("No movers returned from the screener.")
        st.stop()

    movers_df = movers_df[movers_df["symbol"].isin(valid_symbols)].copy()
    if movers_df.empty:
        st.info("No movers matched the selected exchanges.")
        st.stop()

    movers_df["name"] = movers_df["symbol"].map(symbol_to_name).fillna("")
    movers_df["exchange"] = movers_df["symbol"].map(symbol_to_exchange).fillna("")

    with st.spinner("Fetching market caps…"):
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            movers_df["market_cap"] = list(executor.map(get_market_cap, movers_df["symbol"]))

    if direction == "Above":
        filtered = movers_df[movers_df["market_cap"].fillna(0) >= threshold]
    else:
        filtered = movers_df[movers_df["market_cap"].fillna(0) <= threshold]

    if filtered.empty:
        st.info("No stocks matched the market-cap filter.")
        st.stop()

    top = (
        filtered.nlargest(10, "change_pct")
        if mover_type == "Gainers"
        else filtered.nsmallest(10, "change_pct")
    )

    display = top.rename(columns={
        "symbol": "Symbol",
        "name": "Name",
        "exchange": "Exchange",
        "change_pct": "Change %",
        "market_cap": "Market cap",
    })
    keep = ["Symbol", "Name", "Exchange", "Change %", "Market cap"]
    display = display[[c for c in keep if c in display.columns]]

    display["Change %"] = display["Change %"].map(
        lambda v: round(float(v), 2) if pd.notna(v) else None
    )
    display["Market cap"] = display["Market cap"].map(
        lambda v: f"${v / 1e9:,.1f}B" if pd.notna(v) and v else "—"
    )

    st.subheader(
        f"Top 10 {mover_type.lower()} "
        f"({direction.lower()} ${market_cap_input:.1f}B, {', '.join(selected)})"
    )
    st.dataframe(display, use_container_width=True, hide_index=True)
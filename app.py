import streamlit as st

# Configure the main landing page
st.set_page_config(
    page_title="Stock Analytics Suite",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LANDING PAGE HEADER ---
st.title("📊 Quantitative Stock Analytics & Screener Suite")
st.markdown("Welcome to your advanced financial analytics platform. Use the **sidebar navigation** on the left to explore the modules below.")

st.divider()

# --- MODULE OVERVIEW CARDS ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📈 1. Single Stock Analysis")
    st.markdown("""
    * **Features:** View historical daily, weekly, or monthly price action via Alpaca.
    * **Overlays:** Dynamic Simple Moving Average (SMA 20, SMA 50, SMA 150) crossovers.
    * **Interactive Charts:** Powered by Plotly with clean body-level controls.
    """)
    
    st.markdown("### 📉 3. Multi-Stock Comparison")
    st.markdown("""
    * **Basket Analysis:** Compare FAANG + NVIDIA or custom asset baskets.
    * **Normalized Performance:** Rescale asset prices to a base of 100 for clear relative performance tracking.
    * **Correlation Heatmaps:** Inspect return collinearity across equities.
    """)

with col2:
    st.markdown("### 📊 2. Conditional Probabilities & Streaks")
    st.markdown("""
    * **Return Thresholds:** Calculate historical next-day win/loss probabilities after $\pm2\%$ to $\pm6\%$ daily moves.
    * **Streak Probabilities:** Evaluate next-day outcomes following 2 to 6 consecutive positive or negative trading days.
    """)
    

st.divider()

# --- QUICK START FOOTER ---
st.info("💡 **Tip:** Select any page from the sidebar navigation menu on the left to begin your analysis.")
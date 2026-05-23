import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Set page layout to wide
st.set_page_config(layout="wide")

# 1. Mock Dataset of NYSE/NASDAQ Stocks for Demonstration
# In a production app, you can pull the full ticker lists dynamically
@st.cache_data
def get_stock_universe():
    data = {
        'Ticker': ['AAPL', 'NVDA', 'MSFT', 'TSLA', 'AMD', 'INTC', 'AMZN', 'META', 'NFLX', 'BABA', 'XOM', 'JPM', 'GE', 'F', 'BAC'],
        'Company': ['Apple Inc.', 'NVIDIA Corp.', 'Microsoft Corp.', 'Tesla Inc.', 'Advanced Micro Devices', 'Intel Corp.', 'Amazon.com Inc.', 'Meta Platforms', 'Netflix Inc.', 'Alibaba Group', 'Exxon Mobil Corp.', 'JPMorgan Chase', 'General Electric', 'Ford Motor Co.', 'Bank of America'],
        'Exchange': ['NASDAQ', 'NASDAQ', 'NASDAQ', 'NASDAQ', 'NASDAQ', 'NASDAQ', 'NASDAQ', 'NASDAQ', 'NASDAQ', 'NYSE', 'NYSE', 'NYSE', 'NYSE', 'NYSE', 'NYSE'],
        'MarketCap': [2910, 1150, 2750, 745, 280, 140, 1850, 1200, 260, 190, 480, 520, 170, 48, 290], # In Billions
        'Price': [175.20, 875.12, 420.55, 171.05, 180.20, 35.40, 178.15, 495.30, 610.10, 72.40, 118.50, 195.40, 155.20, 12.10, 37.15]
    }
    return pd.DataFrame(data)

df_universe = get_stock_universe()

# 2. Android-style Market Cap Slider
st.write("### Market Cap Threshold")
# Slider mimicking brightness control (0 to 3000 Billion / 3 Trillion)
min_market_cap = st.slider(
    label="Slide to filter out smaller market cap stocks (in Billions)",
    min_value=0,
    max_value=2000,
    value=100,
    step=50,
    format="$%d B"
)

st.markdown("---")

# 3. Main Prompt and Pattern Selection Grid
st.markdown("## What stocks would you like to see?")

# Create three columns to group patterns by family
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🔄 Reversal Patterns")
    pattern_rev = st.radio(
        "Select a Reversal Pattern:",
        ["None", "Head & Shoulders", "Inverse H&S", "Double Top", "Double Bottom", "Triple Top"]
    )

with col2:
    st.markdown("### 📈 Continuation Patterns")
    pattern_cont = st.radio(
        "Select a Continuation Pattern:",
        ["None", "Bull Flag", "Bear Flag", "Bull Pennant", "Cup & Handle"]
    )

with col3:
    st.markdown("### ↔️ Bilateral Patterns")
    pattern_bil = st.radio(
        "Select a Bilateral Pattern:",
        ["None", "Ascending Triangle", "Descending Triangle", "Symmetrical Triangle"]
    )

# Determine the active selected pattern
selected_pattern = "None"
for p in [pattern_rev, pattern_cont, pattern_bil]:
    if p != "None":
        selected_pattern = p

# 4. Pattern Recognition Logic Engine (Example: Simulating Screen Fits)
def screen_patterns(df, pattern, market_cap_limit):
    # First, apply the slider filter
    filtered_df = df[df['MarketCap'] >= market_cap_limit].copy()
    
    if pattern == "None":
        return filtered_df
        
    # Seed a pseudo-random matching logic based on the pattern text 
    # to simulate live algorithmic detection across the ticker universe
    np.random.seed(len(pattern))
    filtered_df['Match Confidence'] = np.random.randint(75, 99, size=len(filtered_df))
    filtered_df['Change %'] = np.random.uniform(-5.0, 5.0, size=len(filtered_df)).round(2)
    
    # Sub-select rows to simulate actual pattern matches
    sample_size = min(len(filtered_df), np.random.randint(2, 6))
    return filtered_df.sample(sample_size).sort_values(by='Match Confidence', ascending=False)

# 5. Live Data Output Table
if selected_pattern != "None":
    st.markdown(f"### 📊 Screen Results for: **{selected_pattern}** (Market Cap > ${min_market_cap}B)")
    results = screen_patterns(df_universe, selected_pattern, min_market_cap)
    
    if not results.empty:
        # Format columns for display
        display_df = results.copy()
        display_df['MarketCap'] = display_df['MarketCap'].apply(lambda x: f"${x}B")
        display_df['Price'] = display_df['Price'].apply(lambda x: f"${x:,.2f}")
        display_df['Match Confidence'] = display_df['Match Confidence'].apply(lambda x: f"{x}%")
        display_df['Change %'] = display_df['Change %'].apply(lambda x: f"+{x}%" if x > 0 else f"{x}%")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.warning("No stocks match the selected pattern within this Market Cap range.")
else:
    st.info("Select a chart pattern from the categories above to view matching tickers.")
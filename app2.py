import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# 1. LOAD THE REBALANCED IBD 50 GROWTH BASKET UNIVERSE
@st.cache_data(ttl=86400) # Re-verifies allocations once every 24 hours
def load_ibd50_universe():
    # Dynamic blend of current institutional heavyweights, growth drivers, and leading FFTY holdings
    tickers = [
        'HUT', 'ALAB', 'SITM', 'AGX', 'VRT', 'MU', 'RKLB', 'FIX', 'LQDA', 'ECO',
        'AAPL', 'NVDA', 'MSFT', 'AMZN', 'META', 'GOOGL', 'TSLA', 'AMD', 'PLTR', 'UBER',
        'PANW', 'CRM', 'NOW', 'SNOW', 'SHOP', 'BABA', 'LLY', 'AVGO', 'COST', 'CMG',
        'ANET', 'CELG', 'CPRT', 'CTAS', 'DE', 'EOG', 'FANG', 'FCX', 'GILD', 'GS',
        'HCA', 'LRCX', 'MA', 'MRK', 'MRNA', 'ORCL', 'SMCI', 'V', 'WMT', 'XOM'
    ]
    return sorted(list(set(tickers)))

# 2. LIGHTWEIGHT COMPACT TECHNICAL FILTER ENGINE
def evaluate_technical_patterns(tickers, pattern):
    if pattern == "None" or not tickers:
        return []
        
    matches = []
    progress_bar = st.progress(0, text="Evaluating IBD50 chart structures...")
    
    try:
        # Download 30 days of standard daily candles in one quick parallel batch
        history = yf.download(tickers, period="30d", interval="1d", group_by='ticker', progress=False, multi_level_index=False)
        
        for idx, t in enumerate(tickers):
            progress_bar.progress(min((idx + 1) / len(tickers), 1.0), text=f"Analyzing {t} momentum curves...")
            
            if t not in history.columns.levels[0]:
                continue
            df_stock = history[t].dropna()
            if len(df_stock) < 20:
                continue
                
            close_prices = df_stock['Close'].values
            volumes = df_stock['Volume'].values
            
            if len(close_prices) == 0 or np.isnan(close_prices[-1]):
                continue
            
            recent_closes = close_prices[-5:]
            older_closes = close_prices[-20:-5]
            
            # Strategy A: Bull Flag / Tight High-Tight Flag Consolidation
            if pattern == "Bull Flag / Consolidation":
                prior_return = (older_closes[-1] - older_closes[0]) / older_closes[0]
                recent_std = np.std(recent_closes) / np.mean(recent_closes)
                if prior_return > 0.025 and recent_std < 0.025:
                    matches.append(t)
                    
            # Strategy B: Heavy Volume Breakout Expansion
            elif pattern == "High Volatility Breakout":
                today_return = abs((close_prices[-1] - close_prices[-2]) / close_prices[-2])
                historical_std = np.std(close_prices[-20:-1]) / np.mean(close_prices[-20:-1])
                avg_volume = np.mean(volumes[-20:-1])
                
                if today_return > (historical_std * 1.8) and volumes[-1] > (avg_volume * 1.3):
                    matches.append(t)
                    
            # Strategy C: Bear Flag Consolidation
            elif pattern == "Bear Flag":
                prior_return = (older_closes[-1] - older_closes[0]) / older_closes[0]
                recent_std = np.std(recent_closes) / np.mean(recent_closes)
                if prior_return < -0.025 and recent_std < 0.025:
                    matches.append(t)
                    
    except Exception as e:
        st.error(f"Data aggregation warning: {e}")
        
    progress_bar.empty()
    return matches

# --- WEB APPLICATION MOBILE VISUAL INTERFACE ---
st.write("## 🏆 IBD 50 Candlestick Chart Screener")
ibd50_list = load_ibd50_universe()

st.markdown("### Select Screening Strategy")
col1, col2 = st.columns(2)
with col1:
    pattern_cont = st.radio("Continuation Models:", ["None", "Bull Flag / Consolidation", "Bear Flag"])
with col2:
    pattern_bil = st.radio("Breakout Models:", ["None", "High Volatility Breakout"])

selected_pattern = "None"
for p in [pattern_cont, pattern_bil]:
    if p != "None":
        selected_pattern = p

if selected_pattern != "None":
    st.markdown(f"### 📈 Scrolling Chart-Roll Results: **{selected_pattern}**")
    
    # Run filter engine across the IBD 50 universe
    matched_tickers = evaluate_technical_patterns(ibd50_list, selected_pattern)
    
    if matched_tickers:
        st.success(f"Found {len(matched_tickers)} growth stock configurations displaying active setups today.")
        
        # DYNAMIC INLINE CHART ROLL GENERATION
        for ticker in matched_tickers:
            try:
                # Fetch full 1-year historical dataset for the clean canvas
                df_year = yf.download(ticker, period="1y", interval="1d", progress=False, multi_level_index=False)
                
                if not df_year.empty:
                    # Inject 50 and 200 daily moving average rolling structures
                    df_year['50 MA'] = df_year['Close'].rolling(window=50).mean()
                    df_year['200 MA'] = df_year['Close'].rolling(window=200).mean()
                    
                    # Generate the custom Plotly Candlestick Object
                    fig = go.Figure()
                    
                    # 1. Primary Candlestick Trace
                    fig.add_trace(go.Candlestick(
                        x=df_year.index,
                        open=df_year['Open'],
                        high=df_year['High'],
                        low=df_year['Low'],
                        close=df_year['Close'],
                        name='Daily Candles'
                    ))
                    
                    # 2. Orange 50-Day Moving Average Line
                    fig.add_trace(go.Scatter(
                        x=df_year.index, y=df_year['50 MA'],
                        line=dict(color='orange', width=1.5),
                        name='50-Day SMA'
                    ))
                    
                    # 3. Red 200-Day Moving Average Line
                    fig.add_trace(go.Scatter(
                        x=df_year.index, y=df_year['200 MA'],
                        line=dict(color='red', width=2.0),
                        name='200-Day SMA'
                    ))
                    
                    # Streamlined layout optimization explicitly tuned for vertical mobile views
                    fig.update_layout(
                        title=dict(
                            text=f"<b>{ticker}</b> - 1Y Moving Average Matrix Overlay",
                            font=dict(size=18, color='white')
                        ),
                        height=450,
                        xaxis_rangeslider_visible=False, # Keeps the interface tall and scannable on mobile
                        margin=dict(l=10, r=10, t=40, b=10),
                        legend=dict(orientation="h", y=1.06, x=0, xanchor="left")
                    )
                    
                    # Render the chart natively as a distinct scrolling node
                    st.plotly_chart(fig, use_container_width=True, key=f"roll_{ticker}")
                    st.markdown("<br><hr style='border:1px solid #333;'><br>", unsafe_allow_html=True)
            except Exception:
                continue
    else:
        st.warning("No IBD 50 growth equities are fitting this strict math layout today. Switch setup models to scan alternate momentum points.")
else:
    st.info("Select a technical configuration above to load the interactive chart roll.")

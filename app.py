import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# 1. DOWNLOAD A LIQUID, HIGH-VOLUME MARKET UNIVERSE
@st.cache_data(ttl=86400)
def load_liquid_universe():
    tickers = [
        'AAPL', 'ABBV', 'ABT', 'ACN', 'ADB', 'ADI', 'ADM', 'ADP', 'ADSK', 'AIG', 
        'AMAT', 'AMD', 'AMGN', 'AMZN', 'ANET', 'APA', 'APTV', 'ASML', 'AVGO', 'AXP',
        'BA', 'BAC', 'BABA', 'BEN', 'BK', 'BKNG', 'BKR', 'BLY', 'BMY', 'BSX',
        'CAT', 'CELG', 'CHTR', 'CI', 'CL', 'CMG', 'CMI', 'CMS', 'CNC', 'COP',
        'COST', 'CPRT', 'CRM', 'CSCO', 'CSX', 'CTAS', 'CTSH', 'CVS', 'CVX', 'D',
        'DAL', 'DE', 'DFS', 'DG', 'DGX', 'DHI', 'DHR', 'DIS', 'DLR', 'DOV',
        'ED', 'EFX', 'EIX', 'EL', 'EMR', 'EOG', 'EPD', 'EQIX', 'EQT', 'ET',
        'ETN', 'EVRG', 'EW', 'EXC', 'EXPD', 'EXR', 'FANG', 'FAST', 'FCX', 'FDS',
        'FDX', 'FE', 'FIS', 'FISV', 'FITB', 'FLS', 'FMC', 'FOXA', 'FRT', 'FSLR',
        'GE', 'GILD', 'GIS', 'GL', 'GLW', 'GM', 'GOOGL', 'GPC', 'GPN', 'GRMN',
        'GS', 'GWW', 'HAL', 'HAS', 'HBAN', 'HCA', 'HD', 'HES', 'HIG', 'HII',
        'LLY', 'LMT', 'LOW', 'LRCX', 'LUV', 'MA', 'MAR', 'MCD', 'MCK', 'MCHP',
        'MDLZ', 'MDT', 'MET', 'META', 'MGM', 'MHK', 'MKC', 'MKTX', 'MLPX', 'MMC',
        'MMM', 'MNST', 'MO', 'MOH', 'MOS', 'MPC', 'MPWR', 'MRK', 'MRNA', 'MRO',
        'MS', 'MSCI', 'MSFT', 'MSI', 'MTB', 'MTD', 'MU', 'NKE', 'NFLX', 'NOW',
        'NVDA', 'PANW', 'PLTR', 'PYPL', 'QQQ', 'RSP', 'SBUX', 'SHOP', 'SNOW', 'SQ',
        'SPY', 'TSLA', 'UBER', 'UNH', 'V', 'WFC', 'WMT', 'XOM'
    ]
    return sorted(list(set(tickers)))

# 2. BACKEND SCAN ENGINE
def run_optimized_scan(all_tickers, pattern, market_cap_limit):
    if pattern == "None" or not all_tickers:
        return pd.DataFrame()
        
    matches = []
    progress_bar = st.progress(0, text="Downloading market data matrices...")
    
    chunk_size = 40
    total_tickers = len(all_tickers)
    
    for i in range(0, total_tickers, chunk_size):
        chunk = all_tickers[i:i+chunk_size]
        progress_bar.progress(min(i / total_tickers, 1.0), text=f"Analyzing setups {i}/{total_tickers}...")
        
        try:
            history = yf.download(chunk, period="30d", interval="1d", group_by='ticker', progress=False, multi_level_index=False)
            
            for t in chunk:
                if t not in history.columns.levels[0]:
                    continue
                df_stock = history[t].dropna()
                if len(df_stock) < 20:
                    continue
                    
                close_prices = df_stock['Close'].values
                if len(close_prices) == 0 or np.isnan(close_prices[-1]):
                    continue
                
                recent_closes = close_prices[-5:]
                older_closes = close_prices[-20:-5]
                
                if pattern == "Bull Flag / Consolidation":
                    prior_return = (older_closes[-1] - older_closes[0]) / older_closes[0]
                    recent_std = np.std(recent_closes) / np.mean(recent_closes)
                    if prior_return > 0.025 and recent_std < 0.025:
                        matches.append(t)
                        
                elif pattern == "High Volatility Breakout":
                    today_return = abs((close_prices[-1] - close_prices[-2]) / close_prices[-2])
                    historical_std = np.std(close_prices[-20:-1]) / np.mean(close_prices[-20:-1])
                    if today_return > (historical_std * 1.8):
                        matches.append(t)
                        
                elif pattern == "Bear Flag":
                    prior_return = (older_closes[-1] - older_closes[0]) / older_closes[0]
                    recent_std = np.std(recent_closes) / np.mean(recent_closes)
                    if prior_return < -0.025 and recent_std < 0.025:
                        matches.append(t)
                        
        except Exception:
            continue
            
    progress_bar.empty()
    if not matches:
        return pd.DataFrame()
        
    final_rows = []
    for ticker in matches:
        try:
            info = yf.Ticker(ticker).info
            mc_billions = round(info.get('marketCap', 0) / 1_000_000_000, 2)
            if mc_billions >= market_cap_limit:
                final_rows.append({
                    'Ticker': ticker,
                    'Company': info.get('longName', ticker),
                    'Price': info.get('currentPrice', 0)
                })
        except Exception:
            continue
            
    return pd.DataFrame(final_rows)

# 3. HIGH-DENSITY MINI CANDLESTICK GENERATOR
def draw_mini_candlestick(ticker_symbol):
    df_mini = yf.download(ticker_symbol, period="15d", interval="1d", progress=False, multi_level_index=False)
    if df_mini.empty:
        return None
        
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df_mini.index,
        open=df_mini['Open'], high=df_mini['High'],
        low=df_mini['Low'], close=df_mini['Close'],
        increasing_line_color='#00FFCC', decreasing_line_color='#FF3366',
        line_width=1.5
    ))
    fig.update_layout(
        height=130,
        margin=dict(l=2, r=2, t=2, b=2),
        xaxis=dict(visible=False, showgrid=False),
        yaxis=dict(visible=False, showgrid=False),
        showlegend=False, dragmode=False, template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# --- NAVIGATION CONTROLLER VIA QUERY PARAMS ---
query_params = st.query_params

if "view_ticker" in query_params:
    # --- DEEP-DIVE FULL CHART VIEW ---
    selected_ticker = query_params["view_ticker"]
    
    if st.button("⬅️ Back to Miniature Grid"):
        st.query_params.clear()
        st.rerun()
        
    st.markdown(f"## 📊 Candlestick Trend Profile: `{selected_ticker}`")
    
    with st.spinner("Generating 1-year candlestick framework..."):
        df_year = yf.download(selected_ticker, period="1y", interval="1d", progress=False, multi_level_index=False)
        if not df_year.empty:
            df_year['50 MA'] = df_year['Close'].rolling(window=50).mean()
            df_year['200 MA'] = df_year['Close'].rolling(window=200).mean()
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df_year.index, open=df_year['Open'], high=df_year['High'],
                low=df_year['Low'], close=df_year['Close'], name='Price'
            ))
            fig.add_trace(go.Scatter(x=df_year.index, y=df_year['50 MA'], line=dict(color='orange', width=1.5), name='50-Day SMA'))
            fig.add_trace(go.Scatter(x=df_year.index, y=df_year['200 MA'], line=dict(color='red', width=2.0), name='200-Day SMA'))
            
            fig.update_layout(
                height=550, xaxis_rangeslider_visible=False,
                margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(orientation="h", y=1.08, x=0),
                dragmode=False
            )
            st.plotly_chart(fig, use_container_width=True, config={'staticPlot': False, 'scrollZoom': False, 'displayModeBar': False})

else:
    # --- MASTER SCREENER DASHBOARD VIEW ---
    st.write("## 🔍 Visual Chart Pattern Screener")
    list_of_tickers = load_liquid_universe()
    
    min_market_cap = st.slider("Market Cap Threshold", min_value=0, max_value=500, value=10, step=5, format="$%d B")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        pattern_cont = st.radio("Continuation Setups:", ["None", "Bull Flag / Consolidation", "Bear Flag"])
    with col2:
        pattern_bil = st.radio("Breakout Setups:", ["None", "High Volatility Breakout"])
        
    selected_pattern = "None"
    for p in [pattern_cont, pattern_bil]:
        if p != "None":
            selected_pattern = p
            
    if selected_pattern != "None":
        st.markdown(f"### 📊 Active Structural Setups for: **{selected_pattern}**")
        
        state_key = f"results_{selected_pattern}_{min_market_cap}"
        if state_key not in st.session_state:
            st.session_state[state_key] = run_optimized_scan(list_of_tickers, selected_pattern, min_market_cap)
            
        screened_matches = st.session_state[state_key]
        
        if not screened_matches.empty:
            # Pair items into native layout rows cleanly
            for idx in range(0, len(screened_matches), 2):
                grid_cols = st.columns(2)
                
                # Box A
                if idx < len(screened_matches):
                    row_data = screened_matches.iloc[idx]
                    with grid_cols[0]:
                        with st.container(border=True):
                            st.markdown(f"**{row_data['Ticker']}** | ${row_data['Price']:.2f}")
                            fig_thumb = draw_mini_candlestick(row_data['Ticker'])
                            if fig_thumb:
                                st.plotly_chart(fig_thumb, use_container_width=True, config={'staticPlot': True})
                            if st.button(f"Zoom", key=f"btn_{row_data['Ticker']}", use_container_width=True):
                                st.query_params.view_ticker = row_data['Ticker']
                                st.rerun()
                                
                # Box B
                if (idx + 1) < len(screened_matches):
                    row_data = screened_matches.iloc[idx + 1]
                    with grid_cols[1]:
                        with st.container(border=True):
                            st.markdown(f"**{row_data['Ticker']}** | ${row_data['Price']:.2f}")
                            fig_thumb = draw_mini_candlestick(row_data['Ticker'])
                            if fig_thumb:
                                st.plotly_chart(fig_thumb, use_container_width=True, config={'staticPlot': True})
                            if st.button(f"Zoom", key=f"btn_{row_data['Ticker']}", use_container_width=True):
                                st.query_params.view_ticker = row_data['Ticker']
                                st.rerun()
        else:
            st.warning("No highly liquid stocks are hitting this strict math baseline today.")
else:
    st.info("Select a chart pattern strategy above to initiate the visual scan grid.")

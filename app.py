import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# 1. HARDCODED OFFICIAL HIGH-GROWTH IBD 50 WATCH LIST
@st.cache_data(ttl=86400)
def load_ibd50_universe():
    tickers = [
        'AIT', 'ANF', 'APA', 'APP', 'ASML', 'AVGO', 'AXON', 'AZTA', 'BCPC', 'BIIB',
        'BKNG', 'BOC', 'CELH', 'CMG', 'COST', 'COIN', 'CPRT', 'CRM', 'CRWD', 'DECK',
        'ELF', 'EME', 'FTNT', 'GE', 'GMM', 'HOOD', 'IBKR', 'INSM', 'IOT', 'KKR',
        'LRCX', 'MELI', 'META', 'MSFT', 'MU', 'NVR', 'NVDA', 'NXT', 'ONON', 'PANW',
        'PLTR', 'PTC', 'SCRM', 'SMCI', 'STRL', 'TDG', 'TSLA', 'TT', 'VRT', 'WST'
    ]
    return sorted(list(set(tickers)))

# 2. DEFENSIVE SCAN ENGINE (Forces clean 1D float vectors to bypass extraction errors)
def run_optimized_scan(all_tickers, pattern, market_cap_limit):
    if pattern == "None" or not all_tickers:
        return pd.DataFrame()
        
    matches = []
    progress_bar = st.progress(0, text="Synchronizing market matrices...")
    total_tickers = len(all_tickers)
    
    for idx, t in enumerate(all_tickers):
        progress_bar.progress(min((idx + 1) / total_tickers, 1.0), text=f"Scanning IBD 50 charts {idx+1}/{total_tickers}...")
        
        try:
            df_stock = yf.download(t, period="30d", interval="1d", progress=False)
            if df_stock.empty or len(df_stock) < 20:
                continue
                
            # FIX: Cleanly normalizes multi-index structures to flat strings
            if isinstance(df_stock.columns, pd.MultiIndex):
                df_stock.columns = [str(c[0]) for c in df_stock.columns]
            else:
                df_stock.columns = [str(c) for c in df_stock.columns]
            
            df_stock = df_stock.dropna()
            
            # FIX: Forces extraction of direct 1D float vectors to fix math evaluation
            close_prices = df_stock['Close'].astype(float).values.flatten()
            if len(close_prices) == 0 or np.isnan(close_prices[-1]):
                continue
            
            recent_closes = close_prices[-5:]
            older_closes = close_prices[-20:-5]
            
            if pattern == "Bull Flag / Consolidation":
                prior_return = (older_closes[-1] - older_closes[0]) / older_closes[0]
                recent_std = np.std(recent_closes) / np.mean(recent_closes)
                if prior_return > 0.025 and recent_std < 0.035:
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
                current_p = info.get('currentPrice') or info.get('regularMarketPrice') or 0
                final_rows.append({
                    'Ticker': ticker,
                    'Company': info.get('longName', ticker),
                    'Price': current_p
                })
        except Exception:
            continue
            
    return pd.DataFrame(final_rows)

# 3. 1-YEAR WIDE SPARKLINE GENERATOR
def draw_wide_trendline(ticker_symbol):
    df_mini = yf.download(ticker_symbol, period="1y", interval="1d", progress=False)
    if df_mini.empty:
        return None
        
    if isinstance(df_mini.columns, pd.MultiIndex):
        df_mini.columns = [str(c[0]) for c in df_mini.columns]
    else:
        df_mini.columns = [str(c) for c in df_mini.columns]
        
    close_vals = df_mini['Close'].astype(float).values.flatten()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_mini.index, y=close_vals,
        line=dict(color='#00FFCC', width=1.8),
        mode='lines'
    ))
    fig.update_layout(
        height=140, margin=dict(l=4, r=4, t=4, b=4),
        xaxis=dict(visible=False, showgrid=False),
        yaxis=dict(visible=False, showgrid=False),
        showlegend=False, dragmode=False, template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# --- ROUTER SYSTEM ---
target_view = st.query_params["view_ticker"] if "view_ticker" in st.query_params else None

if target_view is not None:
    # --- PAGE 1: FULLY INTERACTIVE DEEP-DIVE CANDLESTICK VIEW ---
    if st.button("⬅️ Back to IBD 50 List"):
        st.query_params.clear()
        st.rerun()
        
    st.markdown(f"## 📊 Candlestick Trend Profile: `{target_view}`")
    
    with st.spinner("Generating 1-year candlestick framework..."):
        df_year = yf.download(target_view, period="1y", interval="1d", progress=False)
        if not df_year.empty:
            if isinstance(df_year.columns, pd.MultiIndex):
                df_year.columns = [str(c[0]) for c in df_year.columns]
            else:
                df_year.columns = [str(c) for c in df_year.columns]
                
            close_y = df_year['Close'].astype(float).values.flatten()
            open_y = df_year['Open'].astype(float).values.flatten()
            high_y = df_year['High'].astype(float).values.flatten()
            low_y = df_year['Low'].astype(float).values.flatten()
            
            df_year_flat = pd.DataFrame(index=df_year.index)
            df_year_flat['Close'] = close_y
            df_year_flat['50 MA'] = df_year_flat['Close'].rolling(window=50).mean()
            df_year_flat['200 MA'] = df_year_flat['Close'].rolling(window=200).mean()
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df_year_flat.index, open=open_y, high=high_y, low=low_y, close=close_y, name='Price'
            ))
            fig.add_trace(go.Scatter(x=df_year_flat.index, y=df_year_flat['50 MA'], line=dict(color='orange', width=1.5), name='50-Day SMA'))
            fig.add_trace(go.Scatter(x=df_year_flat.index, y=df_year_flat['200 MA'], line=dict(color='red', width=2.0), name='200-Day SMA'))
            
            fig.update_layout(
                height=550, xaxis_rangeslider_visible=False,
                margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(orientation="h", y=1.08, x=0),
                dragmode="pan"
            )
            st.plotly_chart(fig, use_container_width=True, config={'staticPlot': False, 'scrollZoom': True, 'displayModeBar': True})

else:
    # --- PAGE 2: MAIN SINGLE-COLUMN DASHBOARD VIEW ---
    st.write("## 🔍 Visual IBD 50 Chart Pattern Screener")
    list_of_tickers = load_ibd50_universe()
    
    min_market_cap = st.slider("Market Cap Threshold", min_value=0, max_value=500, value=0, step=5, format="$%d B")
    
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
        st.markdown(f"### 📊 Active IBD 50 Setups for: **{selected_pattern}**")
        
        state_key = f"ibd50_results_{selected_pattern}_{min_market_cap}"
        if state_key not in st.session_state:
            st.session_state[state_key] = run_optimized_scan(list_of_tickers, selected_pattern, min_market_cap)
            
        screened_matches = st.session_state[state_key]
        
        if not screened_matches.empty:
            st.write("#### 📈 1-Year Structural Trend Profiles")
            
            for idx, row_data in screened_matches.iterrows():
                ticker_target = row_data['Ticker']
                company_name = row_data['Company']
                price_val = row_data['Price']
                
                with st.container(border=True):
                    col_left, col_right = st.columns([4, 1])
                    with col_left:
                        fig_thumb = draw_wide_trendline(ticker_target)
                        if fig_thumb:
                            st.plotly_chart(fig_thumb, use_container_width=True, config={'staticPlot': True})
                    with col_right:
                        st.markdown(f"### **{ticker_target}**")
                        st.markdown(f"`${price_val:.2f}`")
                        st.caption(company_name)
                        if st.button(f"Zoom", key=f"zoom_nav_{ticker_target}", use_container_width=True):
                            st.query_params["view_ticker"] = ticker_target
                            st.rerun()
        else:
            st.warning("No IBD 50 stocks are hitting this specific math layout today. Try adjusting your settings or selection criteria.")

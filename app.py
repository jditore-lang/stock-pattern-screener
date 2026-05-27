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

# 2. DEFENSIVE SCAN ENGINE (Extracts numbers using raw dictionary parsing to bypass column issues)
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
                
            # FIX: Force clean flat string arrays on the columns regardless of MultiIndex status
            if hasattr(df_stock.columns, 'get_level_values'):
                df_stock.columns = [str(col[0] if isinstance(col, tuple) else col) for col in df_stock.columns]
            
            df_stock = df_stock.dropna()
            
            # FIX: Use absolute location arrays (.loc) to extract pure numerical arrays
            close_prices = df_stock.loc[:, 'Close'].to_numpy().flatten()
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
                # Fallbacks to prevent missing key fields from dropping rows
                current_p = info.get('currentPrice') or info.get('regularMarketPrice') or 0
                final_rows.append({
                    'Ticker': ticker,
                    'Company': info.get('longName', ticker),
                    'Price': current_p
                })
        except Exception:
            continue
            
    return pd.DataFrame(final_rows)

# 3. 1-YEAR WIDE SPARKLINE GENERATOR (With pure numeric array conversion)
def draw_wide_trendline(ticker_symbol):
    df_mini = yf.download(ticker_symbol, period="1y", interval="1d", progress=False)
    if df_mini.empty:
        return None
        
    if hasattr(df_mini.columns, 'get_level_values'):
        df_mini.columns = [str(col[0] if isinstance(col, tuple) else col) for col in df_mini.columns]
        
    close_vals = df_mini.loc[:, 'Close'].to_numpy().flatten()
    
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
target_view = st.query_params.get("view_ticker", None)

if target_view is not None:
    # --- PAGE 1: FULLY INTERACTIVE DEEP-DIVE VIEW ---
    if st.button("⬅️ Back to IBD 50 List"):
        st.query_params.clear()
        st.rerun()
        
    st.markdown(f"## 📊 Candlestick Trend Profile: `{target_view}`")
    
    with st.spinner("Generating 1-year candlestick framework..."):
        df_year = yf.download(target_view, period="1y", interval="1d", progress=False)
        if not df_year.empty:
            if hasattr(df_year.columns, 'get_level_values'):
                df_year.columns = [str(col[0] if isinstance(col, tuple) else col) for col in df_year.columns]
                
            close_y = df_year.loc[:, 'Close'].to_numpy().flatten()
            open_y = df_year.loc[:, 'Open'].to_numpy().flatten()
            high_y = df_year.loc[:, 'High'].to_numpy().flatten()
            low_y = df_year.loc[:, 'Low'].to_numpy().flatten()
            
            df_year_flat = pd.DataFrame(index=df_year.index)
            df_year_flat['Close'] = close_y
            df_year_flat['50 MA'] = df_year_flat['Close'].rolling(window=50).mean()
            df_year_flat['200 MA'] = df

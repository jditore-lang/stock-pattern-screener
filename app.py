import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# 1. DOWNLOAD A LIQUID, HIGH-VOLUME MARKET UNIVERSE ACROSS THE ENTIRE ALPHABET
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

# 2. OPTIMIZED HIGH-SPEED SCAN ENGINE
def run_optimized_scan(tickers, pattern, market_cap_limit):
    if pattern == "None" or not tickers:
        return pd.DataFrame()
        
    matches = []
    progress_bar = st.progress(0, text="Downloading market data matrices...")
    
    chunk_size = 40
    total_tickers = len(tickers)
    
    for i in range(0, total_tickers, chunk_size):
        chunk = tickers[i:i+chunk_size]
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
                volumes = df_stock['Volume'].values
                
                if len(close_prices) == 0 or np.isnan(close_prices[-1]):
                    continue
                
                recent_closes = close_prices[-5:]
                older_closes = close_prices[-20:-5]
                
                if pattern == "Bull Flag / Consolidation":
                    prior_return = (older_closes[-1] - older_closes[0]) / older_closes[0]
                    recent_std = np.std(recent_closes) / np.mean(recent_closes)
                    if prior_return > 0.025 and recent_std < 0.025:
                        matches.append({'Ticker': t, 'Price': close_prices[-1], 'History': close_prices[-7:].tolist()})
                        
                elif pattern == "High Volatility Breakout":
                    today_return = abs((close_prices[-1] - close_prices[-2]) / close_prices[-2])
                    historical_std = np.std(close_prices[-20:-1]) / np.mean(close_prices[-20:-1])
                    avg_volume = np.mean(volumes[-20:-1])
                    
                    if today_return > (historical_std * 1.8) and volumes[-1] > (avg_volume * 1.3):
                        matches.append({'Ticker': t, 'Price': close_prices[-1], 'History': close_prices[-7:].tolist()})
                        
                elif pattern == "Bear Flag":
                    prior_return = (older_closes[-1] - older_closes[0]) / older_closes[0]
                    recent_std = np.std(recent_closes) / np.mean(recent_closes)
                    if prior_return < -0.025 and recent_std < 0.025:
                        matches.append({'Ticker': t, 'Price': close_prices[-1], 'History': close_prices[-7:].tolist()})
                        
        except Exception:
            continue
            
    progress_bar.empty()
    if not matches:
        return pd.DataFrame()
        
    final_rows = []
    for m in matches:
        try:
            info = yf.Ticker(m['Ticker']).info
            mc_bytes = info.get('marketCap', 0)
            mc_billions = round(mc_bytes / 1_000_000_000, 2) if mc_bytes else 0
            
            if mc_billions >= market_cap_limit:
                yesterday = m['History'][-2] if len(m['History']) > 1 else m['Price']
                chg_pct = round(((m['Price'] - yesterday) / yesterday) * 100, 2)
                
                final_rows.append({
                    'Ticker': m['Ticker'],
                    'Company': info.get('longName', m['Ticker']),
                    'Exchange': info.get('exchange', 'NYSE/NASDAQ'),
                    'MarketCap': mc_billions,
                    'Price': m['Price'],
                    'Daily Change %': chg_pct,
                    '7D Trend': m['History']
                })
        except Exception:
            continue
            
    return pd.DataFrame(final_rows)

# --- WEB APPLICATION INTERFACE ---
st.write("## 🔍 Technical Analysis Chart Pattern Screener")
list_of_tickers = load_liquid_universe()

st.write("### Market Cap Threshold")
min_market_cap = st.slider(
    label="Slide to filter out smaller market cap stocks",
    min_value=0, max_value=500, value=10, step=5, format="$%d B"
)

st.markdown("---")
st.markdown("### Select Pattern Strategy")

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
    st.markdown(f"### 📊 Live Screen Results for: **{selected_pattern}**")
    
    # Store results in Streamlit Session State memory to isolate it from line selection clicks
    state_key = f"results_{selected_pattern}_{min_market_cap}"
    if state_key not in st.session_state:
        st.session_state[state_key] = run

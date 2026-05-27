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
            if mc_billions >= market_cap_

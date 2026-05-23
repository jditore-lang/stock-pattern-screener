import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from ftplib import FTP
import io

st.set_page_config(layout="wide")

# 1. DYNAMICALLY FETCH EVERY ACTIVE TICKER FROM WALL STREET
@st.cache_data(ttl=86400) # Caches the master list cleanly for 24 hours
def get_all_live_tickers():
    try:
        # Connect to the official public Nasdaq Trader FTP server
        ftp = FTP('ftp.nasdaqtrader.com')
        ftp.login()
        
        # Download the latest Nasdaq Listed file
        nasdaq_buffer = io.BytesIO()
        ftp.retrbinary('RETR SymbolDirectory/nasdaqlisted.txt', nasdaq_buffer.write)
        nasdaq_buffer.seek(0)
        df_nasdaq = pd.read_csv(nasdaq_buffer, sep='|')
        
        # Download the latest Other Listed file (NYSE, AMEX, ARCA)
        other_buffer = io.BytesIO()
        ftp.retrbinary('RETR SymbolDirectory/otherlisted.txt', other_buffer.write)
        other_buffer.seek(0)
        df_other = pd.read_csv(other_buffer, sep='|')
        ftp.quit()
        
        # Clean and combine tickers, filtering out test symbols and warrants
        nasdaq_tickers = df_nasdaq[df_nasdaq['Test Issue'] == 'N']['Symbol'].dropna().tolist()
        other_tickers = df_other[(df_other['Test Issue'] == 'N') & (df_other['CQSSymbolFlip'] == 'N')]['ACT Symbol'].dropna().tolist()
        
        master_list = list(set(nasdaq_tickers + other_tickers))
        # Filter out weird characters/warrants (keeps clean tickers like AAPL, MSFT, etc.)
        master_list = [t for t in master_list if t.isalpha() and len(t) <= 5]
        return sorted(master_list)
    except Exception as e:
        # Fallback list if the FTP server times out temporarily
        return ['AAPL', 'NVDA', 'MSFT', 'AMZN', 'META', 'GOOGL', 'TSLA', 'AMD', 'JPM', 'XOM', 'LLY', 'WMT', 'PLTR', 'UBER']

# 2. BATCH SCAN ENGINE (Processes the market in chunks to prevent server timeouts)
def run_full_market_scan(all_tickers, pattern, market_cap_limit):
    if pattern == "None" or not list_of_tickers:
        return pd.DataFrame()
        
    matches = []
    progress_bar = st.progress(0, text="Scanning market volume metrics...")
    
    # Processes the first 500 liquid listings in chunks of 50 for execution speed
    chunk_size = 50
    total_tickers = len(all_tickers[:500]) 
    
    for i in range(0, total_tickers, chunk_size):
        chunk = all_tickers[i:i+chunk_size]
        progress_bar.progress(min(i / total_tickers, 1.0), text=f"Analyzing chart structures {i}/{total_tickers}...")
        
        try:
            # Download historical candles for the chunk
            history = yf.download(chunk, period="30d", interval="1d", group_by='ticker', progress=False)
            
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
                
                # PATTERN MATH A: Bull Flag / Consolidation
                if pattern == "Bull Flag / Consolidation":
                    prior_return = (older_closes[-1] - older_closes[0]) / older_closes[0]
                    recent_std = np.std(recent_closes) / np.mean(recent_closes)
                    if prior_return > 0.04 and recent_std < 0.012:
                        matches.append({'Ticker': t, 'Price': close_prices[-1], 'History': close_prices[-7:].tolist()})
                        
                # PATTERN MATH B: High Volatility Breakout
                elif pattern == "High Volatility Breakout":
                    today_return = abs((close_prices[-1] - close_prices[-2]) / close_prices[-2])
                    historical_std = np.std(close_prices[-20:-1]) / np.mean(close_prices[-20:-1])
                    avg_volume = np.mean(volumes[-20:-1])
                    
                    if today_return > (historical_std * 3.0) and volumes[-1] > (avg_volume * 2.0):
                        matches.append({'Ticker': t, 'Price': close_prices[-1], 'History': close_prices[-7:].tolist()})
                        
                # PATTERN MATH C: Bear Flag
                elif pattern == "Bear Flag":
                    prior_return = (older_closes[-1] - older_closes[0]) / older_closes[0]
                    recent_std = np.std(recent_closes) / np.mean(recent_closes)
                    if prior_return < -0.04 and recent_std < 0.012:
                        matches.append({'Ticker': t, 'Price': close_prices[-1], 'History': close_prices[-7:].tolist()})
                        
        except Exception:
            continue
            
    progress_bar.empty()
    if not matches:
        return pd.DataFrame()
        
    # Build results and pull final metadata for matches only (Saves massive bandwidth)
    final_rows = []
    for m in matches:
        try:
            info = yf.Ticker(m['Ticker']).info
            mc_billions = round(info.get('marketCap', 0) / 1_000_000_000, 2)
            
            if mc_billions >= market_cap_limit:
                yesterday = m['History'][-2] if len(m['History']) > 1 else m['Price']
                chg_pct = round(((m['Price'] - yesterday) / yesterday) * 100, 2)

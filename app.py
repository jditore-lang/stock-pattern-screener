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
    
    state_key = f"results_{selected_pattern}_{min_market_cap}"
    if state_key not in st.session_state:
        st.session_state[state_key] = run_optimized_scan(list_of_tickers, selected_pattern, min_market_cap)
        
    screened_matches = st.session_state[state_key]
    
    if not screened_matches.empty:
        display_df = screened_matches.copy()
        display_df['MarketCap'] = display_df['MarketCap'].apply(lambda x: f"${x:,.1f} B")
        display_df['Price'] = display_df['Price'].apply(lambda x: f"${x:,.2f}")
        display_df['Daily Change %'] = display_df['Daily Change %'].apply(lambda x: f"+{x}%" if x > 0 else f"{x}%")
        
        # Positioned the 7D Mini Chart thumbnail directly to the right of the stock symbol
        column_order = ["Ticker", "7D Trend", "Company", "Exchange", "MarketCap", "Price", "Daily Change %"]
        
        selected_rows = st.dataframe(
            display_df, use_container_width=True, hide_index=True, column_order=column_order,
            column_config={"7D Trend": st.column_config.LineChartColumn("7D Mini Chart")},
            on_select="rerun", selection_mode="single-row"
        )
        
        # FIX: Swapped out legacy index lookup logic for explicit attribute mapping
        if selected_rows and selected_rows.selection.rows:
            selected_index = selected_rows.selection.rows[0]
            clicked_ticker = display_df.iloc[selected_index]["Ticker"]
            clicked_name = display_df.iloc[selected_index]["Company"]
            
            st.markdown("---")
            st.markdown(f"## 📊 Candlestick Trend Profile: {clicked_name} (`{clicked_ticker}`)")
            
            with st.spinner(f"Generating 1-year candlestick framework..."):
                df_year = yf.download(clicked_ticker, period="1y", interval="1d", progress=False, multi_level_index=False)
                if not df_year.empty:
                    df_year['50 MA'] = df_year['Close'].rolling(window=50).mean()
                    df_year['200 MA'] = df_year['Close'].rolling(window=200).mean()
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Candlestick(
                        x=df_year.index,
                        open=df_year['Open'],
                        high=df_year['High'],
                        low=df_year['Low'],
                        close=df_year['Close'],
                        name='Price Action'
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=df_year.index, y=df_year['50 MA'],
                        line=dict(color='orange', width=1.5),
                        name='50-Day SMA'
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=df_year.index, y=df_year['200 MA'],
                        line=dict(color='red', width=2.0),
                        name='200-Day SMA'
                    ))
                    
                    fig.update_layout(
                        height=500,
                        xaxis_rangeslider_visible=False,
                        margin=dict(l=10, r=10, t=20, b=10),
                        legend=dict(orientation="h", y=1.08, x=0, xanchor="left")
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No highly liquid stocks are hitting this strict math baseline today. Try lowering your Market Cap Slider

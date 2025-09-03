import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import yfinance as yf
import time

# Configure the page
st.set_page_config(
    page_title="🔴 LIVE Share Market Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling with live indicators
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    .live-indicator {
        background: linear-gradient(45deg, #ff4444, #ff6666);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        font-weight: bold;
        animation: blink 1.5s infinite;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.5; }
    }
    
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    
    .price-up {
        color: #00ff00;
        font-weight: bold;
    }
    
    .price-down {
        color: #ff4444;
        font-weight: bold;
    }
    
    .last-updated {
        background-color: #e1f5fe;
        padding: 0.5rem;
        border-radius: 5px;
        font-style: italic;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for live updates
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'price_history' not in st.session_state:
    st.session_state.price_history = []
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True

# Main title with live indicator
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<h1 class="main-header">📈 Share Market Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<div class="live-indicator">🔴 LIVE</div>', unsafe_allow_html=True)

# Sidebar for user inputs
st.sidebar.header("🎛️ Dashboard Controls")

# Auto-refresh toggle
auto_refresh = st.sidebar.toggle(
    "🔄 Auto Refresh",
    value=st.session_state.auto_refresh,
    help="Automatically update data every 30 seconds"
)
st.session_state.auto_refresh = auto_refresh

# Refresh interval
if auto_refresh:
    refresh_interval = st.sidebar.slider(
        "Refresh Interval (seconds)",
        min_value=10,
        max_value=300,
        value=30,
        step=10
    )
else:
    refresh_interval = 30

# Manual refresh button
if st.sidebar.button("🔄 Refresh Now", type="primary"):
    st.rerun()

# Stock symbol input
default_stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX']
selected_stock = st.sidebar.selectbox(
    "📊 Select Stock Symbol",
    default_stocks + ['Custom'],
    index=0
)

if selected_stock == 'Custom':
    custom_stock = st.sidebar.text_input("Enter Stock Symbol (e.g., AAPL)")
    if custom_stock:
        selected_stock = custom_stock.upper()

# Time period selection
period_options = {
    '1 Day': '1d',
    '5 Days': '5d',
    '1 Month': '1mo',
    '3 Months': '3mo',
    '6 Months': '6mo',
    '1 Year': '1y'
}

selected_period = st.sidebar.selectbox(
    "📅 Select Time Period",
    list(period_options.keys()),
    index=2  # Default to 1 month
)

# Chart type selection
chart_type = st.sidebar.radio(
    "📈 Chart Type",
    ['Candlestick', 'Line Chart', 'Area Chart']
)

# Alert settings
st.sidebar.markdown("---")
st.sidebar.header("🚨 Price Alerts")
enable_alerts = st.sidebar.checkbox("Enable Price Alerts")

if enable_alerts:
    alert_price_high = st.sidebar.number_input(
        "Alert if price goes above:",
        min_value=0.0,
        value=0.0,
        step=0.01
    )
    alert_price_low = st.sidebar.number_input(
        "Alert if price goes below:",
        min_value=0.0,
        value=0.0,
        step=0.01
    )

# Function to calculate technical indicators
def calculate_technical_indicators(data):
    indicators = {}
    
    if len(data) > 0:
        # Moving averages
        if len(data) >= 20:
            indicators['ma_20'] = data['Close'].rolling(window=20).mean().iloc[-1]
        if len(data) >= 50:
            indicators['ma_50'] = data['Close'].rolling(window=50).mean().iloc[-1]
        
        # RSI calculation
        if len(data) >= 14:
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            indicators['rsi'] = 100 - (100 / (1 + rs.iloc[-1])) if not pd.isna(rs.iloc[-1]) else 50
        
        # 52-week high and low
        if len(data) >= 252:  # Approx trading days in a year
            indicators['52_week_high'] = data['High'].rolling(window=252).max().iloc[-1]
            indicators['52_week_low'] = data['Low'].rolling(window=252).min().iloc[-1]
        else:
            indicators['52_week_high'] = data['High'].max()
            indicators['52_week_low'] = data['Low'].min()
    
    return indicators

# Function to get live data
@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_live_stock_data(symbol, period):
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval='1m' if period in ['1d', '5d'] else '1d')
        info = stock.info
        
        # Calculate technical indicators
        additional_metrics = calculate_technical_indicators(data)
        
        return data, info, additional_metrics, None
    except Exception as e:
        return None, None, {}, str(e)

# Function to get real-time price
def get_realtime_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period='1d', interval='1m')
        if not data.empty:
            return data['Close'].iloc[-1], data.index[-1]
        return None, None
    except:
        return None, None

# Main content area
if selected_stock and selected_stock != 'Custom':
    # Create placeholder for live updates
    placeholder = st.empty()
    
    with placeholder.container():
        try:
            # Get current time
            current_time = datetime.now()
            
            # Fetch stock data
            with st.spinner(f'🔄 Loading live data for {selected_stock}...'):
                data, info, additional_metrics, error = get_live_stock_data(
                    selected_stock, period_options[selected_period]
                )
                current_price, price_timestamp = get_realtime_price(selected_stock)
            
            if error:
                st.error(f"❌ Error loading data: {error}")
            elif data is not None and not data.empty:
                # Update price history for live tracking
                if current_price:
                    st.session_state.price_history.append({
                        'time': current_time,
                        'price': current_price
                    })
                    
                    # Keep only last 100 price points
                    if len(st.session_state.price_history) > 100:
                        st.session_state.price_history = st.session_state.price_history[-100:]
                
                # Display last updated time
                st.markdown(f'<div class="last-updated">🕐 Last Updated: {current_time.strftime("%H:%M:%S")} | Market Status: {"🟢 Open" if current_time.hour >= 9 and current_time.hour < 16 else "🔴 Closed"}</div>', unsafe_allow_html=True)
                
                # Calculate price changes
                latest_price = current_price or data['Close'].iloc[-1]
                prev_price = data['Close'].iloc[-2] if len(data) > 1 else latest_price
                price_change = latest_price - prev_price
                price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
                
                # Price alerts
                if enable_alerts:
                    if alert_price_high > 0 and latest_price > alert_price_high:
                        st.success(f"🚨 ALERT: {selected_stock} price is above ${alert_price_high:.2f}!")
                    elif alert_price_low > 0 and latest_price < alert_price_low:
                        st.error(f"🚨 ALERT: {selected_stock} price is below ${alert_price_low:.2f}!")
                
                # Display enhanced key metrics
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                
                with col1:
                    st.metric(
                        label="💰 Current Price",
                        value=f"${latest_price:.2f}",
                        delta=f"{price_change:+.2f} ({price_change_pct:+.2f}%)"
                    )
                
                with col2:
                    volume = data['Volume'].iloc[-1] if not data.empty else 0
                    avg_volume = data['Volume'].mean() if not data.empty else 0
                    volume_ratio = (volume / avg_volume) if avg_volume > 0 else 1
                    st.metric(
                        label="📊 Volume",
                        value=f"{volume:,.0f}",
                        delta=f"{volume_ratio:.1f}x avg" if volume_ratio != 1 else None
                    )
                
                with col3:
                    week_52_high = additional_metrics.get('52_week_high', 0)
                    st.metric(
                        label="📈 52W High",
                        value=f"${week_52_high:.2f}" if week_52_high else "N/A"
                    )
                
                with col4:
                    week_52_low = additional_metrics.get('52_week_low', 0)
                    st.metric(
                        label="📉 52W Low", 
                        value=f"${week_52_low:.2f}" if week_52_low else "N/A"
                    )
                
                with col5:
                    ma_20 = additional_metrics.get('ma_20')
                    ma_signal = "Above" if ma_20 and latest_price > ma_20 else "Below" if ma_20 else "N/A"
                    st.metric(
                        label="📊 MA(20)",
                        value=f"${ma_20:.2f}" if ma_20 else "N/A",
                        delta=ma_signal if ma_20 else None
                    )
                
                with col6:
                    rsi = additional_metrics.get('rsi')
                    rsi_signal = "Overbought" if rsi and rsi > 70 else "Oversold" if rsi and rsi < 30 else "Neutral" if rsi else "N/A"
                    st.metric(
                        label="📊 RSI(14)",
                        value=f"{rsi:.1f}" if rsi else "N/A",
                        delta=rsi_signal if rsi else None
                    )
                
                # Live price movement chart (mini chart)
                if len(st.session_state.price_history) > 1:
                    st.subheader("🔴 Live Price Movement (Last Hour)")
                    price_df = pd.DataFrame(st.session_state.price_history)
                    live_fig = px.line(
                        price_df, 
                        x='time', 
                        y='price',
                        title=f"{selected_stock} Live Price Updates"
                    )
                    live_fig.update_layout(
                        height=300,
                        showlegend=False,
                        yaxis_title="Price ($)",
                        xaxis_title="Time"
                    )
                    live_fig.update_traces(line=dict(color='#00ff00', width=3))
                    st.plotly_chart(live_fig, use_container_width=True)
                
                # Main stock chart
                st.subheader(f"📈 {selected_stock} Stock Chart - {selected_period}")
                
                if chart_type == 'Candlestick':
                    fig = go.Figure(data=go.Candlestick(
                        x=data.index,
                        open=data['Open'],
                        high=data['High'],
                        low=data['Low'],
                        close=data['Close'],
                        name=selected_stock
                    ))
                    fig.update_layout(
                        title=f"{selected_stock} Candlestick Chart",
                        yaxis_title="Price ($)",
                        xaxis_title="Date/Time",
                        height=600
                    )
                    
                elif chart_type == 'Line Chart':
                    fig = px.line(
                        x=data.index, 
                        y=data['Close'],
                        title=f"{selected_stock} Price Movement"
                    )
                    fig.update_layout(
                        yaxis_title="Price ($)",
                        xaxis_title="Date/Time",
                        height=600
                    )
                    fig.update_traces(line=dict(color='#1f77b4', width=2))
                    
                else:  # Area Chart
                    fig = px.area(
                        x=data.index, 
                        y=data['Close'],
                        title=f"{selected_stock} Price Movement"
                    )
                    fig.update_layout(
                        yaxis_title="Price ($)",
                        xaxis_title="Date/Time",
                        height=600
                    )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Volume chart
                st.subheader("📊 Volume Analysis")
                vol_fig = px.bar(
                    x=data.index, 
                    y=data['Volume'],
                    title=f"{selected_stock} Trading Volume"
                )
                vol_fig.update_layout(
                    yaxis_title="Volume",
                    xaxis_title="Date/Time",
                    height=400
                )
                st.plotly_chart(vol_fig, use_container_width=True)
                
                # Real-time data table
                st.subheader("📋 Recent Live Data")
                recent_data = data.tail(10).round(2)
                recent_data.index = recent_data.index.strftime('%H:%M:%S' if selected_period in ['1d', '5d'] else '%Y-%m-%d')
                st.dataframe(recent_data, use_container_width=True)
                
                # Company info
                if info and 'longName' in info:
                    st.subheader("🏢 Company Information")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Company:** {info.get('longName', 'N/A')}")
                        st.write(f"**Sector:** {info.get('sector', 'N/A')}")
                        st.write(f"**Industry:** {info.get('industry', 'N/A')}")
                    
                    with col2:
                        market_cap = info.get('marketCap', 0)
                        if market_cap:
                            st.write(f"**Market Cap:** ${market_cap:,.0f}")
                        st.write(f"**P/E Ratio:** {info.get('trailingPE', 'N/A')}")
                        st.write(f"**Dividend Yield:** {info.get('dividendYield', 'N/A')}")
                
                st.session_state.last_update = current_time
                
            else:
                st.error(f"❌ No data found for symbol: {selected_stock}")
                
        except Exception as e:
            st.error(f"❌ Error loading live data: {str(e)}")
            st.info("Please check your internet connection and try again.")
    
    # Auto-refresh mechanism
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

else:
    # Welcome message
    st.info("👆 Please select a stock symbol from the sidebar to start live tracking!")
    
    # Demo live counter
    st.subheader("🔴 Live Demo Counter")
    demo_counter = st.empty()
    
    for i in range(10):
        demo_counter.metric("Live Counter", f"{i + 1}/10")
        time.sleep(1)
    
    st.success("✅ Live functionality is working! Select a stock to see real data.")

# Footer with live status
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**📊 Data Source:** Yahoo Finance")

with col2:
    st.markdown(f"**🕐 Server Time:** {datetime.now().strftime('%H:%M:%S')}")

with col3:
    status = "🟢 LIVE" if auto_refresh else "⏸️ PAUSED"
    st.markdown(f"**Status:** {status}")

st.markdown("**⚠️ Note:** Live updates depend on market hours and data availability.")

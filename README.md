# SM-Dashboard

📈 Share Market Dashboard

An interactive stock market dashboard built with Python and Streamlit. Visualize historical stock prices, trading volumes, key metrics, and company information with customizable charts.

Features

Stock Selection: Choose popular stocks or enter custom symbols.

Date Range: Analyze data from 1 day to 2 years.

Interactive Charts: Candlestick, Line, and Area charts.

Key Metrics: Current price, volume, 52-week high/low.

Volume Analysis: Interactive bar charts for trading volumes.

Recent Data Table: Last 10 days of trading data.

Company Info: Market cap, P/E ratio, sector, and industry.

Custom Styling: Clean dashboard with CSS-based metrics and headers.

Installation

Clone the repository:

git clone https://github.com/utkarshtripathy1030/SM-Dashboard.git
cd SM-Dashboard


Install dependencies:

pip install -r requirements.txt

Usage

Run the dashboard locally:

streamlit run app.py


Open the browser at http://localhost:8501.

Use the sidebar to select stocks, date range, and chart type.

View metrics, charts, volume, and company information interactively.

Requirements

Python 3.10+

Libraries:

streamlit==1.49.1
pandas==2.2.2
numpy==1.26.2
plotly==6.3.0
yfinance==0.2.65

Future Improvements

Multiple stock comparisons.

Technical indicators: SMA, EMA, RSI, Bollinger Bands.

Near real-time auto-refresh for live stock updates.

CSV/Excel export for historical data.

Dark/light theme toggle.

Disclaimer

Uses Yahoo Finance data, which may be delayed.

Not intended for live trading decisions.

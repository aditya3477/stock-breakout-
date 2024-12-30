import yfinance as yf
import pandas as pd
import streamlit as st

def calculate_breakouts(ticker, start_date, end_date, volume_threshold, price_threshold, holding_period):
    # Fetch historical data
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    
    # Debug: Print the raw data to ensure it's fetched
    if stock_data.empty:
        raise ValueError(f"No data available for ticker {ticker} in the specified date range.")
    print(stock_data.head())  # Debugging raw data

    # Ensure 'Volume' column exists
    if 'Volume' not in stock_data.columns:
        raise KeyError("'Volume' column is missing in the data. Check the data source or ticker.")
    
    # Calculate rolling average
    stock_data['20d_avg_volume'] = stock_data['Volume'].rolling(window=20).mean()
    
    # Debug: Confirm if the column is created
    if '20d_avg_volume' not in stock_data.columns:
        raise KeyError("Failed to create '20d_avg_volume' column. Check the rolling calculation logic.")
    print(stock_data[['Volume', '20d_avg_volume']].tail())  # Debugging rolling average

    # Drop rows with NaN values caused by the rolling calculation
    stock_data = stock_data.dropna(subset=['20d_avg_volume'])
    
    # Identify breakout days
    stock_data['Volume_Breakout'] = stock_data['Volume'] > (stock_data['20d_avg_volume'] * (volume_threshold / 100))
    stock_data['Price_Change'] = stock_data['Close'].pct_change() * 100
    stock_data['Price_Breakout'] = stock_data['Price_Change'] > price_threshold
    stock_data['Breakout'] = stock_data['Volume_Breakout'] & stock_data['Price_Breakout']
    
    # Calculate returns
    results = []
    for date, row in stock_data[stock_data['Breakout']].iterrows():
        buy_price = row['Close']
        try:
            sell_date = stock_data.index[stock_data.index.get_loc(date) + holding_period]
            sell_price = stock_data.loc[sell_date, 'Close']
            return_pct = ((sell_price - buy_price) / buy_price) * 100
            results.append((date, buy_price, sell_price, return_pct))
        except (IndexError, KeyError):
            continue
    
    # Convert results to DataFrame
    results_df = pd.DataFrame(results, columns=['Buy Date', 'Buy Price', 'Sell Price', 'Return (%)'])
    return results_df




# Streamlit UI
st.title("Stock Breakout Analyzer")
ticker = st.text_input("Ticker Symbol")
start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")
volume_threshold = st.number_input("Volume Threshold (%)", value=200)
price_threshold = st.number_input("Price Change Threshold (%)", value=2)
holding_period = st.number_input("Holding Period (days)", value=10)

if st.button("Generate Report"):
    if ticker and start_date and end_date:
        report = calculate_breakouts(ticker, start_date, end_date, volume_threshold, price_threshold, holding_period)
        st.write(report)
        report.to_csv(f"{ticker}_breakout_report.csv")
        st.download_button("Download CSV", data=report.to_csv(index=False), file_name="breakout_report.csv")
    else:
        st.error("Please fill all inputs!")

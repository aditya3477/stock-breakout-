import yfinance as yf
import pandas as pd
import streamlit as st

def calculate_breakouts(ticker, start_date, end_date, volume_threshold, price_threshold, holding_period):
    # Fetch historical data
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    stock_data['20d_avg_volume'] = stock_data['Volume'].rolling(window=20).mean()
    
    # Identify breakout days
    stock_data['Volume_Breakout'] = stock_data['Volume'] > (stock_data['20d_avg_volume'] * (volume_threshold / 100))
    stock_data['Price_Change'] = stock_data['Close'].pct_change() * 100
    stock_data['Price_Breakout'] = stock_data['Price_Change'] > price_threshold
    stock_data['Breakout'] = stock_data['Volume_Breakout'] & stock_data['Price_Breakout']
    
    # Calculate returns
    results = []
    for date, row in stock_data[stock_data['Breakout']].iterrows():
        buy_price = row['Close']
        sell_date = stock_data.index[stock_data.index.get_loc(date) + holding_period]
        if sell_date in stock_data.index:
            sell_price = stock_data.loc[sell_date, 'Close']
            return_pct = ((sell_price - buy_price) / buy_price) * 100
            results.append((date, buy_price, sell_price, return_pct))
    
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

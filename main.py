import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from PIL import Image

img = Image.open('oipluse.png')

st.set_page_config(page_title='OiPluse', page_icon=img)

# Upload Stock Data
st.title("Stock Data Analysis")
uploaded_file = st.file_uploader("Upload Stock Data (CSV)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, parse_dates=["time"])
    df.rename(columns={"time": "Date", "open": "Open", "high": "High", "low": "Low", "close": "Close"}, inplace=True)
    df["Time"] = df["Date"].dt.time
    
    # Filter data within 9:15 AM - 3:00 PM
    df = df[(df["Time"] >= pd.to_datetime("09:15").time()) & (df["Time"] <= pd.to_datetime("15:00").time())]
    
    st.write("### Raw Data", df.head())
    
    # Process Data for 2 Years
    df = df.sort_values("Date", ascending=False).head(2 * 252)  # Approx 2 years of trading days
    
    # Calculate Yesterday's Close Percentage Change
    df["Yesterday Close % Change"] = ((df["Close"] - df["Close"].shift(-1)) / df["Close"].shift(-1)) * 100
    
    # Calculate Today's Opening Gap Percentage
    df["Today's Opening Gap %"] = ((df["Open"] - df["Close"].shift(-1)) / df["Close"].shift(-1)) * 100
    
    # Calculate LTP Percentage Change
    df["LTP % Change"] = ((df["Close"] - df["Open"]) / df["Open"]) * 100
    
    st.write("### Processed Data with Conditions", df.head())
    
    # Get Actual Output (rows where conditions are met, adjust as needed)
    actual_output = df[(df["Yesterday Close % Change"].abs() > 1) | 
                       (df["Today's Opening Gap %"].abs() > 1) | 
                       (df["LTP % Change"].abs() > 1)]
    
    st.write("### Actual Output", actual_output.head())
    
    # Define Data Range
    def get_range(value):
        if pd.notna(value):
            return value * 1.1, value * 0.9
        return None, None
    
    ranges = actual_output["Close"].apply(get_range).dropna()
    if not ranges.empty:
        actual_output["Upper Range"], actual_output["Lower Range"] = zip(*ranges)
    else:
        actual_output["Upper Range"], actual_output["Lower Range"] = None, None
    
    st.write("### Data Range", actual_output[["Date", "Close", "Upper Range", "Lower Range"]].dropna().head())
    
    # Search Past Data within Range
    results = []
    for _, row in actual_output.dropna().iterrows():
        matches = df[(df["Close"] <= row["Upper Range"]) & (df["Close"] >= row["Lower Range"]) & (df["Date"] < row["Date"])]
        for _, match in matches.iterrows():
            results.append((match["Date"], row["Date"], match["Close"]))
    
    results_df = pd.DataFrame(results, columns=["Past Date", "Actual Date", "Close Price"])
    st.write("### Search Results", results_df.head())
    
    # Date Picker to Select Date Range for Graph
    start_date, end_date = st.date_input("Select Date Range", value=[df["Date"].min(), df["Date"].max()], min_value=df["Date"].min(), max_value=df["Date"].max())
    
    # Remove timezone from the Date column
    df["Date"] = df["Date"].dt.tz_localize(None)
    
    # Filter data based on selected date range
    filtered_df = df[(df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))]
    
    # Plot Candlestick Chart for selected range
    fig = go.Figure(data=[go.Candlestick(x=filtered_df["Date"],
                                         open=filtered_df["Open"],
                                         high=filtered_df["High"],
                                         low=filtered_df["Low"],
                                         close=filtered_df["Close"],
                                         name='Candlestick')])
    st.plotly_chart(fig)
    
    # Date Picker for Specific Date
    selected_date = st.date_input("Select a Specific Date", value=df["Date"].max(), min_value=df["Date"].min(), max_value=df["Date"].max())
    
    # Remove timezone from the Date column again
    selected_date = pd.to_datetime(selected_date).normalize()  # Normalize to midnight to avoid time comparison issues
    
    # Filter data for the selected specific date
    selected_data = df[df["Date"].dt.normalize() == selected_date]
    
    if not selected_data.empty:
        st.write(f"### Data for {selected_date.strftime('%Y-%m-%d')}", selected_data)
        
        # Plot Candlestick Chart for the selected date
        fig_selected_date = go.Figure(data=[go.Candlestick(x=selected_data["Date"],
                                                          open=selected_data["Open"],
                                                          high=selected_data["High"],
                                                          low=selected_data["Low"],
                                                          close=selected_data["Close"],
                                                          name='Candlestick')])
        st.plotly_chart(fig_selected_date)
    else:
        st.write(f"No data available for {selected_date.strftime('%Y-%m-%d')}")

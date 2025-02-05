import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
import time

img = Image.open('oipluse.png')
st.set_page_config(page_title='OiPulse', page_icon=img)

# Upload Stock Data
st.title("Stock Data Analysis")
uploaded_file = st.file_uploader("Upload Stock Data (CSV)", type=["csv"])

if uploaded_file:
    with st.spinner('Processing data...'):
        time.sleep(1)
        df = pd.read_csv(uploaded_file, parse_dates=["time"])
        df.rename(columns={"time": "Date", "open": "Open", "high": "High", "low": "Low", "close": "Close"}, inplace=True)
        df["Time"] = df["Date"].dt.time
        
        df = df[(df["Time"] >= pd.to_datetime("09:15").time()) & (df["Time"] <= pd.to_datetime("15:00").time())]
        
        st.write("### Raw Data", df)
        
        df = df.sort_values("Date", ascending=True)  
        
        df["Yesterday Close % Change"] = ((df["Close"] - df["Close"].shift(-1)) / df["Close"].shift(-1)) * 100
        df["Today's Opening Gap %"] = ((df["Open"] - df["Close"].shift(-1)) / df["Close"].shift(-1)) * 100
        df["LTP % Change"] = ((df["Close"] - df["Open"]) / df["Open"]) * 100
        
        st.write("### Actual Datas", df)
        
        # Single user-defined percentage for all conditions
        percentage = st.number_input("Enter Percentage for Conditions", value=10.0) / 100
        
        # Apply conditions to calculate ranges
        df["C1 Upper Range"] = df["Yesterday Close % Change"] * (1 + percentage)
        df["C1 Lower Range"] = df["Yesterday Close % Change"] * (1 - percentage)
        
        df["C2 Upper Range"] = df["Today's Opening Gap %"] * (1 + percentage)
        df["C2 Lower Range"] = df["Today's Opening Gap %"] * (1 - percentage)
        
        df["C3 Upper Range"] = df["LTP % Change"] * (1 + percentage)
        df["C3 Lower Range"] = df["LTP % Change"] * (1 - percentage)
        
        st.write("### Data Range with Conditions", df[["Date", "Time", "Yesterday Close % Change", "C1 Upper Range", "C1 Lower Range",
                                                      "Today's Opening Gap %", "C2 Upper Range", "C2 Lower Range",
                                                      "LTP % Change", "C3 Upper Range", "C3 Lower Range"]].dropna())
        
        # Select Specific Time
        selected_time = st.time_input("Select Time", value=pd.to_datetime("9:15").time())
        filtered_time_df = df[df["Time"] == selected_time]
        
        # Apply the conditions
        condition1 = (filtered_time_df["Yesterday Close % Change"] > filtered_time_df["C1 Upper Range"]) | (filtered_time_df["Yesterday Close % Change"] < filtered_time_df["C1 Lower Range"])
        condition2 = (filtered_time_df["Today's Opening Gap %"] > filtered_time_df["C2 Upper Range"]) | (filtered_time_df["Today's Opening Gap %"] < filtered_time_df["C2 Lower Range"])
        condition3 = (filtered_time_df["LTP % Change"] > filtered_time_df["C3 Upper Range"]) | (filtered_time_df["LTP % Change"] < filtered_time_df["C3 Lower Range"])
        
        final_filtered_df = filtered_time_df[condition1 & condition2 & condition3]
        
        st.write("### Filtered Data for Selected Time with Conditions", final_filtered_df)
        
        if not final_filtered_df.empty:
            unique_dates = final_filtered_df["Date"].dt.date.unique()
            selected_date = st.selectbox("Select a Date", unique_dates, index=0)
            
            raw_filtered_df = df[df["Date"].dt.date == selected_date]
            
            fig = go.Figure(data=[go.Candlestick(x=raw_filtered_df["Date"],
                                                 open=raw_filtered_df["Open"],
                                                 high=raw_filtered_df["High"],
                                                 low=raw_filtered_df["Low"],
                                                 close=raw_filtered_df["Close"],
                                                 name='Candlestick')])
            st.plotly_chart(fig)
        else:
            st.write("No matching data found for the selected time and conditions.")

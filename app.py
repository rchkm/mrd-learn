import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fitparse import FitFile
import numpy as np

st.set_page_config(layout="wide", page_title="Running Anomaly Tracker")
st.title("Cardiovascular Drift & Heat Anomaly Tracker")
st.write("Upload a raw `.fit` file from your smartwatch to analyze your second-by-second performance.")

# 1. Create a file uploader
uploaded_file = st.file_uploader("Drop your .fit file here", type=["fit"])

if uploaded_file is not None:
    # 2. Parse the uploaded .fit file
    with st.spinner("Extracting smartwatch telemetry..."):
        # fitparse can read the raw bytes directly from the Streamlit uploader
        fitfile = FitFile(uploaded_file.getvalue())
        
        data = []
        # 'record' messages contain the actual second-by-second GPS and sensor data
        for record in fitfile.get_messages('record'):
            record_data = {}
            for data_field in record:
                record_data[data_field.name] = data_field.value
            data.append(record_data)
            
        # Convert to a Pandas DataFrame for easy math
        raw_df = pd.DataFrame(data)
        
        # 3. Clean and Transform the Data
        df = pd.DataFrame()
        df['Date'] = pd.to_datetime(raw_df['timestamp'])
        
        # Heart Rate
        if 'heart_rate' in raw_df.columns:
            df['Heart Rate'] = raw_df['heart_rate']
        else:
            df['Heart Rate'] = np.nan
            
        # Temperature
        if 'temperature' in raw_df.columns:
            df['Temp'] = raw_df['temperature']
        else:
            df['Temp'] = np.nan
            
        # Pace: Watches record speed in meters/second. We must convert to min/km.
        if 'speed' in raw_df.columns:
            # Replace 0 speed with a tiny number to prevent division by zero errors
            speed_ms = raw_df['speed'].replace(0, 0.001) 
            df['Pace'] = (1000 / speed_ms) / 60
            # Cap the pace at 15 min/km so stopping at a red light doesn't ruin the graph
            df.loc[df['Pace'] > 15, 'Pace'] = 15 
        else:
            df['Pace'] = np.nan
            
        # Drop rows where we don't have GPS/Sensor data yet
        df = df.dropna(subset=['Date', 'Heart Rate'])

        # Smooth the data! 
        # Raw second-by-second data is too chaotic. Let's take a 30-second rolling average.
        df['Heart Rate'] = df['Heart Rate'].rolling(window=30).mean()
        df['Pace'] = df['Pace'].rolling(window=30).mean()
        df['Temp'] = df['Temp'].rolling(window=30).mean()
        
        # Calculate Anomaly (Z-Score)
        # If HR is 2 standard deviations higher than the run's average, flag it!
        df['HR_Z_Score'] = (df['Heart Rate'] - df['Heart Rate'].mean()) / df['Heart Rate'].std()
        df['Anomaly'] = df['HR_Z_Score'] > 2 

    # 4. Build the Graph
    st.success("Data successfully extracted!")
    
    # Safely calculate the Pace range to prevent Plotly crashing on empty GPS data
    if df['Pace'].notna().any():
        pace_max = df['Pace'].max() + 0.5
        pace_min = max(0, df['Pace'].min() - 0.5)
        # We put the MAX first and MIN second. This manually reverses the axis!
        pace_range = [pace_max, pace_min] 
    else:
        # Default range if the run had absolutely no speed data recorded
        pace_range = [15, 0]

    fig = go.Figure()

    # Add Pace Line (Blue)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Pace'], name='Pace (min/km)', 
                             yaxis='y1', line=dict(color='#3b82f6', width=2)))

    # Add Temp Line (Orange, dotted)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Temp'], name='Temp (°C)', 
                             yaxis='y2', line=dict(color='#f97316', dash='dot', width=2)))

    # Add HR Line (Red)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Heart Rate'], name='Heart Rate (bpm)', 
                             yaxis='y3', line=dict(color='#ef4444', width=3)))

    # Highlight Anomalies
    anomalies = df[df['Anomaly']]
    if not anomalies.empty:
        fig.add_trace(go.Scatter(x=anomalies['Date'], y=anomalies['Heart Rate'], mode='markers', 
                                 name='High HR Anomaly', marker=dict(color='black', size=10, symbol='x'), yaxis='y3'))

    # Configure the 3 Y-axes
    fig.update_layout(
        xaxis=dict(domain=[0.1, 0.9]),
        # Replaced titlefont with title_font
        yaxis=dict(title='Pace (min/km)', title_font=dict(color='#3b82f6'), tickfont=dict(color='#3b82f6'), range=pace_range),
        yaxis2=dict(title='Temp (°C)', title_font=dict(color='#f97316'), tickfont=dict(color='#f97316'), anchor='free', overlaying='y', side='left', position=0.0),
        yaxis3=dict(title='Heart Rate (bpm)', title_font=dict(color='#ef4444'), tickfont=dict(color='#ef4444'), anchor='x', overlaying='y', side='right'),
        height=600,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Waiting for data. Please upload a file to begin.")
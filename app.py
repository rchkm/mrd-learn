import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 1. Generate realistic dummy training data
dates = pd.date_range(start="2026-06-01", periods=20, freq="2D")
base_hr = np.random.normal(145, 4, 20)     # Easy HR around 145 bpm
base_pace = np.random.normal(8.5, 0.2, 20) # Easy pace around 8:30 min/km
base_temp = np.random.normal(32, 1.5, 20)  # Tropical heat around 32°C

df = pd.DataFrame({'Date': dates, 'Heart Rate': base_hr, 'Pace': base_pace, 'Temp': base_temp})

# Introduce a severe heat anomaly to test the Z-score logic
df.loc[15, 'Temp'] = 36.5
df.loc[15, 'Heart Rate'] = 172 # HR spikes due to heat
df.loc[15, 'Pace'] = 8.9       # Pace drops slightly

# 2. Calculate the Anomaly (Z-Score for HR)
# This flags any run where HR is mathematically way higher than normal
df['HR_Z_Score'] = (df['Heart Rate'] - df['Heart Rate'].mean()) / df['Heart Rate'].std()
df['Anomaly'] = df['HR_Z_Score'] > 2 

# 3. Build the Dashboard UI
st.set_page_config(layout="wide")
st.title("Ujicoba")
st.write("Visualizing the impact of temperature on easy run heart rates.")

# 4. Create the Multi-Axis Plotly Chart
fig = go.Figure()

# Add Pace Line (Blue)
fig.add_trace(go.Scatter(x=df['Date'], y=df['Pace'], name='Pace (min/km)', 
                         yaxis='y1', line=dict(color='#3b82f6', width=3)))

# Add Temp Line (Orange, dotted)
fig.add_trace(go.Scatter(x=df['Date'], y=df['Temp'], name='Avg Temp (°C)', 
                         yaxis='y2', line=dict(color='#f97316', dash='dot')))

# Add HR Line (Red)
fig.add_trace(go.Scatter(x=df['Date'], y=df['Heart Rate'], name='Avg HR (bpm)', 
                         yaxis='y3', line=dict(color='#ef4444', width=3)))

# Highlight the Anomalies with a black X
anomalies = df[df['Anomaly']]
fig.add_trace(go.Scatter(x=anomalies['Date'], y=anomalies['Heart Rate'], mode='markers', 
                         name='Anomaly Detected', marker=dict(color='black', size=14, symbol='x'), yaxis='y3'))

# Configure the three independent Y-axes
fig.update_layout(
    xaxis=dict(domain=[0.1, 0.9]),
    yaxis=dict(title='Pace (min/km)', titlefont=dict(color='#3b82f6'), tickfont=dict(color='#3b82f6')),
    yaxis2=dict(title='Temp (°C)', titlefont=dict(color='#f97316'), tickfont=dict(color='#f97316'), overlaying='y', side='left', position=0.0),
    yaxis3=dict(title='Heart Rate (bpm)', titlefont=dict(color='#ef4444'), tickfont=dict(color='#ef4444'), overlaying='y', side='right'),
    height=600,
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

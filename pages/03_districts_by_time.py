import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt

import matplotlib.pyplot as plt
import matplotlib as mpl
import plotly.graph_objs as go
#BigQuery imports
from google.cloud import bigquery

#Inialize BigQuery client
client = bigquery.Client()

# The code below is for the title and logo for this page.
st.set_page_config(page_title="Cohort for Food dataset", page_icon="🥡")



st.title("Viajes por `distrito` / `hora`")





@st.experimental_memo(ttl=12 * 60 * 60)#Update query every 12 hours(hour*min*seg)
def run_query_data1():
    #query= "SELECT timestamp_start AS date_time, latitud_start AS lat, longitud_start AS lon FROM `vacio-276411.mainDataset.trips_b` WHERE DATE(timestamp_start) = '2022-08-24'"
    query = "SELECT district AS distrito, EXTRACT (HOUR FROM dateandtime) as hora,trips AS viajes FROM `vacio-276411.mainDataset.V1_trips_grouped_all_hours`"
    query = "SELECT district AS distrito, EXTRACT (HOUR FROM dateandtime) as hora, SUM(trips) AS viajes FROM `vacio-276411.mainDataset.V1_trips_grouped_all_hours` GROUP BY distrito,hora"
    df_data = client.query(query).to_dataframe()
    return df_data

df = run_query_data1()



fig = go.Figure()

fig.add_heatmap(
    x=df.hora,
    y=df.distrito,
    z=df.viajes,
    # colorscale="Reds",
    # colorscale="Sunsetdark",
    colorscale="Redor"
    # colorscale="Viridis",
)

#fig.update_layout(title_text="Monthly cohorts showing retention rates", title_x=0.5)
fig.layout.xaxis.title = "hora"
fig.layout.yaxis.title = "Distrito"
fig["layout"]["title"]["font"] = dict(size=25)
fig.layout.plot_bgcolor = "#efefef"  # Set the background color to white
fig.layout.width = 750
fig.layout.height = 750
#fig.layout.xaxis.tickvals = df.columns
#fig.layout.yaxis.tickvals = df.index
fig.layout.margin.b = 100
fig

#Add sidebar
st.sidebar.markdown("[More visualization in Datastudio](https://datastudio.google.com/reporting/4627480c-1c6d-47d3-a55c-b2ab56812a8d)")
st.sidebar.markdown("[Code on github](https://github.com/Gull-mobility)")
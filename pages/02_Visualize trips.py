from urllib.error import URLError

import pandas as pd
import pydeck as pdk
import streamlit as st
#BigQuery imports
from google.cloud import bigquery

#Inialize BigQuery client
client = bigquery.Client()


#@st.experimental_memo(ttl=600) #Update query evry 10 minutes
@st.experimental_memo(ttl=12 * 60 * 60)#Update query every 12 hours(hour*min*seg)
def run_query_data1():
    #query= "SELECT timestamp_start AS date_time, latitud_start AS lat, longitud_start AS lon FROM `vacio-276411.mainDataset.trips_b` WHERE DATE(timestamp_start) = '2022-08-24'"
    query = "SELECT timestamp_start AS date_time, latitud_start AS lat_str, longitud_start AS lon_str, latitud_end AS lat_end, longitud_end AS lon_end FROM `vacio-276411.mainDataset.trips_a` WHERE DATE(timestamp_start) = '2021-05-14'"
    df_data = client.query(query).to_dataframe()
    df_data['lat_str'] = df_data['lat_str'].astype(str).astype(float)
    df_data['lon_str'] = df_data['lon_str'].astype(str).astype(float)
    df_data['lat_end'] = df_data['lat_end'].astype(str).astype(float)
    df_data['lon_end'] = df_data['lon_end'].astype(str).astype(float)
    return df_data


def mapping_demo():
    try:
        ALL_LAYERS = {
            "Show trips": pdk.Layer(
                "ArcLayer",
                #df_datadata=from_data_file("bart_path_stats.json"),
                data=filterdata(data, hour_selected),
                get_source_position=["lon_str", "lat_str"],
                get_target_position=["lon_end", "lat_end"],
                get_source_color=[200, 30, 0, 160],
                get_target_color=[154, 242, 161, 125],
                auto_highlight=True,
                width_scale=0.0001,
                get_width="outbound",
                width_min_pixels=3,
                width_max_pixels=30,
            ),
        }
        selected_layers = [
            layer
            for layer_name, layer in ALL_LAYERS.items()
            if st.sidebar.checkbox(layer_name, True)
        ]
        if selected_layers:
            st.pydeck_chart(
                pdk.Deck(
                    map_style="mapbox://styles/mapbox/light-v9",
                    initial_view_state={
                        "latitude": 40.4167,
                        "longitude": -3.7049,
                        "zoom": 11,
                        "pitch": 50,
                    },
                    layers=selected_layers,
                )
            )
        else:
            st.error("Please choose at least one layer above.")
    except URLError as e:
        st.error(
            """
            **This demo requires internet access.**
            Connection error: %s
        """
            % e.reason
        )

# IF THE SLIDER CHANGES, UPDATE THE QUERY PARAM
def update_query_params():
    hour_selected = st.session_state["date_time"]
    st.experimental_set_query_params(pickup_hour=hour_selected)

# FILTER DATA FOR A SPECIFIC HOUR, CACHE
@st.experimental_memo
def filterdata(df, hour_selected):
    return df[df["date_time"].dt.hour == hour_selected]



# SEE IF THERE'S A QUERY PARAM IN THE URL (e.g. ?pickup_hour=2)
# THIS ALLOWS YOU TO PASS A STATEFUL URL TO SOMEONE WITH A SPECIFIC HOUR SELECTED,
# E.G. https://share.streamlit.io/streamlit/demo-uber-nyc-pickups/main?pickup_hour=2
if not st.session_state.get("url_synced", False):
    try:
        pickup_hour = int(st.experimental_get_query_params()["pickup_hour"][0])
        st.session_state["pickup_hour"] = pickup_hour
        st.session_state["url_synced"] = True
    except KeyError:
        pass

# IF THE SLIDER CHANGES, UPDATE THE QUERY PARAM
def update_query_params():
    hour_selected = st.session_state["pickup_hour"]
    st.experimental_set_query_params(pickup_hour=hour_selected)

st.set_page_config(page_title="Visualize Trips", page_icon="🌍")
st.markdown("# Visualize trips")
st.write("This visualization show you trips made the 2021-05-14")
st.write("In red is the origin of the trip and in green the destiny.")
st.write("With this visualization you can touch with your hands and notice the increase of trips during the day.")

data = run_query_data1()

hour_selected = st.slider(
    "Selecciona the start hour of the trip", 0, 23, key="pickup_hour", on_change=update_query_params
)

mapping_demo()

st.sidebar.markdown("[More visualization in Datastudio](https://datastudio.google.com/reporting/4627480c-1c6d-47d3-a55c-b2ab56812a8d)")
st.sidebar.markdown("[Code on github](https://github.com/Gull-mobility)")
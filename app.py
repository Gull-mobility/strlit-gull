import altair as alt
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
#BigQuery imports
from google.cloud import bigquery
#Datetime
import datetime
#Geopandas
import geopandas as gpd
#Import KMZ
import fiona
#Impor models
import joblib

#Inialize BigQuery client
client = bigquery.Client()

# SETTING PAGE CONFIG TO WIDE MODE AND ADDING A TITLE AND FAVICON
st.set_page_config(layout="wide", page_title="Urban mobility prediction", page_icon=":taxi:")

#@st.experimental_memo(ttl=600) #Update query evry 10 minutes
@st.experimental_memo(ttl=12 * 60 * 60)#Update query every 12 hours(hour*min*seg)
#def run_query_data()
def run_query_data1():
    #query= "SELECT timestamp_start AS date_time, latitud_start AS lat, longitud_start AS lon FROM `vacio-276411.mainDataset.trips_b` WHERE DATE(timestamp_start) = '2022-08-24'"
    
    #query = "SELECT timestamp_start AS date_time, latitud_start AS lat, longitud_start AS lon FROM `vacio-276411.mainDataset.trips_a` WHERE DATE(timestamp_start) > '2022-08-20'"
    #df_data['lat'] = df_data['lat'].astype(str).astype(float)
    #df_data['lon'] = df_data['lon'].astype(str).astype(float)

    #Dont get geometry becouse is to big to recieve -       geoDistrict.geometry,
    
    #THis query is to use geolocations but now is not been used.
    query = """
WITH geoDistrict AS( SELECT
    name,
    idDistrito,
    geometry,
    ST_CENTROID(geometry) AS center,
    ST_X( ST_CENTROID(geometry) ) as lon,
    ST_Y( ST_CENTROID(geometry) ) as lat 
  FROM `vacio-276411.mainDataset.districts`
)

SELECT
      geoDistrict.name,
      alldata.district,
      alldata.dateandtime AS date_time,
      alldata.trips,
      geoDistrict.center,
      geoDistrict.lon,
      geoDistrict.lat,
  FROM `vacio-276411.mainDataset.V1E_trips_grouped_all_hours_onlythree` AS alldata
  LEFT JOIN geoDistrict
  ON alldata.district = geoDistrict.idDistrito
            """
    

    df_data = client.query(query).to_dataframe()
    df_data['lat'] = df_data['lat'].astype(str).astype(float)
    df_data['lon'] = df_data['lon'].astype(str).astype(float)
    df_data['elevation'] = df_data['trips']*100

    #Change name of long districts
    df_data["name"].replace({"Fuencarral - El Pardo": "Fuencarral", "Moncloa - Aravaca": "Moncloa"}, inplace=True)

    return df_data

def make_estimation(df_data):

    fname = 'model.pkl'
    model = joblib.load(open(fname, 'rb'))


    ##PREPARE  ESTIMATIONS
    #Shift method to create the lag variables
    df_data['trips_lag_28_days'] = df_data['trips'].shift(28*24) #28 days before same hour
    df_data['trips_lag_14_days'] = df_data['trips'].shift(14*24) #14 days before same hour
    df_data['trips_lag_7_days'] = df_data['trips'].shift(7*24) #7 days before same hour
    df_data['trips_lag_1_days'] = df_data['trips'].shift(1*24) # 1 day before same hour
    df_data['trips_lag_2_days'] = df_data['trips'].shift(2*24) # 2 days before same hour
    df_data['trips_lag_1_hours'] = df_data['trips'].shift(1) # 1 hour before
    df_data['trips_lag_2_hours'] = df_data['trips'].shift(1) # 2 hours before
    df_data.dropna(inplace=True)
    #Execute prediction
    prediction_rows = ['trips_lag_28_days','trips_lag_14_days','trips_lag_7_days','trips_lag_1_days','trips_lag_2_days','trips_lag_1_hours','trips_lag_2_hours']
    p = model.predict(df_data[prediction_rows])
    #Add predition to dataframe
    df_data = df_data.assign(prediction = p)
    #Add error
    df_data['error'] = abs(df_data['trips'] - df_data['prediction'])
    df_data['desviacionpercentage'] = df_data['error'] / df_data['trips']
    #Not accept Infinity
    df_data['desviacionpercentage'] = df_data['desviacionpercentage'].apply(lambda x: -1 if x > 1_000_000 else x)
    #Add if is acceptable
    df_data['aceptable'] = (df_data['desviacionpercentage'] < 0.3) | (df_data['error'] < 2)

    #Add a colum to show in map
    df_data['pred_elevation'] = df_data['prediction']*100

    return df_data

# FUNCTION FOR AIRPORT MAPS
def map(data, lat, lon, zoom, elevationColumn, dataColumn):
    st.pydeck_chart(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state={
                "latitude": lat,
                "longitude": lon,
                "zoom": zoom,
                "pitch": 60,
            },
            layers=[
                pdk.Layer(
                    "ColumnLayer",
                    data=data,
                    get_position=["lon", "lat"],
                    radius=200,
                    elevation_scale=1,
                    elevation_range=[0, 1000],
                    pickable=True,
                    extruded=True,
                    getElevation = elevationColumn * 100,
                    getFillColor = [255, 165, 0],
                ),
            ],
        )
        
    )

#get_fill_color='[255, 255, elevation * 255]',


# FILTER DATA FOR A SPECIFIC HOUR-DAY, CACHE
@st.experimental_memo
def filterdata(df, hour_selected,date_selected):
    return df[ (df["date_time"].dt.hour == hour_selected + adjust_hour) & (df['date_time'].dt.date == date_selected) ]

def roundnumbers(df):
    df['prediction'] = df['prediction'].map(lambda x: "{:,.1f}".format(x))
    df['error'] = df['error'].map(lambda x: "{:,.1f}".format(x))
    df['desviacionpercentage'] = df['desviacionpercentage'].map(lambda x: "{:,.2f}".format(x))
    return df


# STREAMLIT APP LAYOUT
data = run_query_data1()
data = make_estimation(data)

#The data is UTM, add 2 hours to fix - In the future move this to database
adjust_hour = -4

# LAYING OUT THE TOP SECTION OF THE APP
row1_1, row1_2 = st.columns((2, 3))

# SEE IF THERE'S A QUERY PARAM IN THE URL (e.g. ?predict_hour=2)
# THIS ALLOWS YOU TO PASS A STATEFUL URL TO SOMEONE WITH A SPECIFIC HOUR SELECTED,
if not st.session_state.get("url_synced", False):
    try:

        predict_hour = int(st.experimental_get_query_params()["predict_hour"][0])
        st.session_state["predict_hour"] = predict_hour

        #TODO: Date cant be recived as param - Workaroud use in different variables year-month-day


        st.session_state["url_synced"] = True
    except KeyError:
        pass

# IF THE SLIDER OR DATESELECT CHANGES, UPDATE THE QUERY PARAM
def update_query_params():
    date_selected = st.session_state["predict_date"]
    hour_selected = st.session_state["predict_hour"]
    st.experimental_set_query_params(
        predict_date=date_selected,
        predict_hour=hour_selected)

def set_next_hour():
    today = datetime.date.today()
    date_today = today.strftime("%Y-%m-%d")
    st.session_state["predict_date"]  = today

    hour = datetime.datetime.now()
    hour_now = int(hour.strftime("%H"))
    st.session_state["predict_hour"] = hour_now

    st.experimental_set_query_params(
        predict_date=date_today,
        predict_hour=hour_now)

def set_last_hour():
    today = datetime.date.today()
    date_today = today.strftime("%Y-%m-%d")
    st.session_state["predict_date"]  = today

    hour = datetime.datetime.now()
    hour_now = int(hour.strftime("%H")) -1
    st.session_state["predict_hour"] = hour_now

    st.experimental_set_query_params(
        predict_date=date_today,
        predict_hour=hour_now)


with row1_1:
    st.title("Urban mobility prediction")


with row1_2:
    st.write(
        """
    ##
    Here you can select a specific an hour and we will show the trips done and the trips that we had estimated. Also you can see the prediction por the next hour and check how we did it later.
    
    To make this prediction we use the services providers: car2go, emov, wible.

    Please select hours only between 4 and 23
    """
    )


# LAYING OUT THE SECTION 2
row2_1, row2_2, row2_3 = st.columns(3)

with row2_1:
    result =  st.button("Next hour", on_click=set_next_hour)
    result2 = st.button("Last hour", on_click=set_last_hour)

with row2_2:

    date_selected = st.date_input(
        "Select date",
        datetime.date.today(),
        key="predict_date",
        min_value= datetime.date(2022, 1, 20),
        max_value= datetime.date(2022, 9, 30),
        on_change=update_query_params
    )
    #st.write('Your birthday is:', d)


with row2_3:
    hour_selected = st.slider(
        "Select hour", 0, 23, key="predict_hour", on_change=update_query_params,
        value = int(datetime.datetime.now().strftime("%H"))
    )


# LAYING OUT THE MIDDLE SECTION OF THE APP WITH THE MAPS
row3_1, row3_2, row3_3 = st.columns((2, 2, 2))

# SETTING THE ZOOM LOCATIONS FOR THE AIRPORTS
la_guardia = [40.4167, -3.7049] 
jfk = [40.6650, -73.7821]
newark = [40.7090, -74.1805]
zoom_level = 12

midpoint = la_guardia

with row3_1:
    st.write(f"""Trips **done** from {hour_selected}:00 and {(hour_selected + 1) % 24}:00""")
    map(filterdata(data, hour_selected, date_selected), midpoint[0], midpoint[1], 12, ["elevation"], ["trips"])

with row3_2:
    st.write(f"""Trips **estimated** from {hour_selected}:00 and {(hour_selected + 1) % 24}:00""")
    map(filterdata(data, hour_selected, date_selected), la_guardia[0], la_guardia[1], zoom_level,["pred_elevation"], ["prediction"])

with row3_3:
    st.write("**Real VS Prediction**")
    #Not sow datetime becouse is the same
    st.dataframe((roundnumbers (filterdata(data, hour_selected, date_selected)) )[['name','trips','prediction','error','desviacionpercentage','aceptable']])
    #['district','trips','prediction']
    st.write("Here you can see: name of district, trips, trips estimated, absolut error and pertentage of error, if it's acceptable or not")
    st.write("A value is aceptable if error is less than 2 units or a 20%")

st.sidebar.markdown("[More visualization in Datastudio](https://datastudio.google.com/reporting/4627480c-1c6d-47d3-a55c-b2ab56812a8d)")
st.sidebar.markdown("[Code on github](https://github.com/Gull-mobility)")
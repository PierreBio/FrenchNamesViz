import altair as alt
import geopandas as gpd
import pandas as pd
import streamlit as st
import json

@st.cache_data
def load_data():
    return gpd.read_file('./data/departements-version-simplifiee.geojson')

depts = load_data()
st.write("Aperçu des données de départements :")
st.write(depts.head())

geojson_data = json.loads(depts.to_json())
geojson_features = alt.Data(values=geojson_data['features'])
map_chart = alt.Chart(geojson_features).mark_geoshape(
    fill='lightgray',
    stroke='white'
).encode(
    tooltip=[
        alt.Tooltip('properties.nom:N', title='Nom du Département'),
        alt.Tooltip('properties.code:N', title='Code du Département'),
        alt.Tooltip('properties.code:N', title='Code du Département')
    ]
).project(
    type='mercator'
).properties(
    width=800,
    height=600
).interactive()

points = pd.DataFrame({
    'x': [2.3522, 4.8357, -1.5528],
    'y': [48.8566, 45.7640, 47.2184],
    'label': ['Paris', 'Lyon', 'Nantes']
})

points_chart = alt.Chart(points).mark_point(color='red', size=100).encode(
    x='x:Q',
    y='y:Q',
    tooltip=['label:N']
)

combined_chart = alt.layer(map_chart, points_chart).configure_view(
    stroke=None
)

st.title("Carte Interactive de la France")
st.write("Carte interactive des noms par département en France.")

if st.button("Afficher la carte"):
    st.altair_chart(combined_chart)
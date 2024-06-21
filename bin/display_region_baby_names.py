import geopandas as gpd
import plotly.express as px
import streamlit as st

@st.cache_data
def load_data():
    return gpd.read_file('./data/departements-version-simplifiee.geojson')

depts = load_data()
st.write("Aperçu des données de départements :")
st.write(depts.head())

depts['id'] = depts['code']

fig = px.choropleth(depts,
                    geojson=depts.geometry,
                    locations=depts.index,
                    color="nom",
                    hover_name="nom",
                    hover_data=["code"],
                    title="Carte Interactive des Départements de France")

fig.update_geos(fitbounds="locations", visible=False)

st.title("Carte Interactive de la France")
st.write("Carte interactive des départements de France.")

if st.button("Afficher la carte"):
    st.plotly_chart(fig)

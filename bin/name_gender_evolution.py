import altair as alt
import pandas as pd
import streamlit as st

@st.cache_data
def load_name_data():
    names = pd.read_csv("./data/dpt2020.csv", sep=";")
    names.drop(names[names.preusuel == '_PRENOMS_RARES'].index, inplace=True)
    names.drop(names[names.dpt == 'XX'].index, inplace=True)
    return names

def get_name_evolution_chart(names, selected_name):
    name_evolution = names[names['preusuel'] == selected_name].groupby(['annais', 'sexe'])['nombre'].sum().reset_index()
    name_evolution['sexe'] = name_evolution['sexe'].map({1: 'Male', 2: 'Female'})
    
    color_scale = alt.Scale(
        domain=['Male', 'Female'],
        range=['#1f77b4', '#ff69b4']  # Blue for males, pink for females
    )
    
    area_chart = alt.Chart(name_evolution).mark_area().encode(
        x='annais:O',
        y='nombre:Q',
        color=alt.Color('sexe:N', scale=color_scale),
        tooltip=['annais:O', 'nombre:Q', 'sexe:N']
    ).properties(
        width=800,
        height=400,
        title=f"Evolution of the name '{selected_name}' by gender over years"
    )
    return area_chart

names = load_name_data()

st.title("Evolution des prénoms en France (1900-2020)")
st.subheader("Filtres")

name_counts = names.groupby('preusuel')['nombre'].sum().reset_index()
name_counts = name_counts.sort_values(by='nombre', ascending=False)
name_counts['rank'] = name_counts['nombre'].rank(method='min', ascending=False).astype(int)

name_list = name_counts.apply(lambda row: f"{row['preusuel']} ({row['nombre']}, #{row['rank']})", axis=1).tolist()

selected_name_display = st.selectbox('Sélectionnez un PRÉNOM (Attributions, #Rang)', name_list)
selected_name = selected_name_display.split(' ')[0]

st.subheader("Evolution du prénom dans le temps")

name_evolution_chart = get_name_evolution_chart(names, selected_name)
st.altair_chart(name_evolution_chart)

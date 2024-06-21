import altair as alt
import geopandas as gpd
import pandas as pd
import streamlit as st
import json

@st.cache_data
def load_geo_data():
    return gpd.read_file('./data/departements-version-simplifiee.geojson')

@st.cache_data
def load_name_data():
    names = pd.read_csv("./data/dpt2020.csv", sep=";")
    names.drop(names[names.preusuel == '_PRENOMS_RARES'].index, inplace=True)
    names.drop(names[names.dpt == 'XX'].index, inplace=True)
    return names

def get_top_bottom_names(filtered_names, top=True):
    result = {}
    for sex in [1, 2]:
        filtered_sex = filtered_names[filtered_names['sexe'] == sex]
        if top:
            agg_func = filtered_sex.groupby('dpt').apply(lambda x: x.nlargest(3, 'nombre')).reset_index(drop=True)
        else:
            agg_func = filtered_sex.groupby('dpt').apply(lambda x: x.nsmallest(3, 'nombre')).reset_index(drop=True)
        result[sex] = agg_func
    return result

depts = load_geo_data()
names = load_name_data()

year_list = names['annais'].unique().tolist()
year_list.sort()

st.title("Carte Interactive des prénoms en France (1900-2020)")
st.subheader("Filtres")

col1, col2 = st.columns(2)

with col1:
    selected_year = st.selectbox('Sélectionnez une année', year_list)

filtered_names_for_top = names[names['annais'] == selected_year]
names_dict_for_top = get_top_bottom_names(filtered_names_for_top, True)
for sex, sex_names in names_dict_for_top.items():
    sex_names['dpt'] = sex_names['dpt'].astype(str)
    if sex == 1:
        depts = depts.merge(sex_names.groupby('dpt')['preusuel'].apply(lambda x: ', '.join(x)).reset_index(),
                            left_on='code', right_on='dpt', how='left').rename(columns={'preusuel': 'top_masculins'})
    else:
        depts = depts.merge(sex_names.groupby('dpt')['preusuel'].apply(lambda x: ', '.join(x)).reset_index(),
                            left_on='code', right_on='dpt', how='left').rename(columns={'preusuel': 'top_feminins'})

namesin_year = names[names['annais'] == selected_year]
name_counts = namesin_year.groupby('preusuel')['nombre'].sum().reset_index()
name_counts = name_counts.sort_values(by='nombre', ascending=False)
name_counts['rank'] = name_counts['nombre'].rank(method='min', ascending=False).astype(int)

name_list = name_counts.apply(lambda row: f"{row['preusuel']} ({row['nombre']}, #{row['rank']})", axis=1).tolist()

with col2:
    selected_name_display = st.selectbox('Sélectionnez un PRÉNOM (Attributions, #Rang)', name_list)
selected_name = selected_name_display.split(' ')[0]

filtered_names = namesin_year[namesin_year['preusuel'] == selected_name]
name_counts__per_dept = filtered_names.groupby('dpt')['nombre'].sum().reset_index()

depts['code'] = depts['code'].astype(str)
name_counts__per_dept['dpt'] = name_counts__per_dept['dpt'].astype(str)
depts = depts.merge(name_counts__per_dept, left_on='code', right_on='dpt', how='left').rename(columns={'nombre': 'count_name'})
depts['count_name'] = depts['count_name'].fillna(0)

geojson_data = json.loads(depts.to_json())
geojson_features = alt.Data(values=geojson_data['features'])

color_scale = alt.Scale(domain=[0, 100, 500, 1000, 2000, 5000],
                        range=['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#2171b5'])

map_chart = alt.Chart(geojson_features).mark_geoshape().encode(
    color=alt.Color('properties.count_name:Q', scale=color_scale, legend=alt.Legend(title="Nombre d'attributions")),
    tooltip=[
        alt.Tooltip('properties.nom:N', title='Nom du Département'),
        alt.Tooltip('properties.code:N', title='Code du Département'),
        alt.Tooltip('properties.count_name:Q', title=f"{selected_name}"),
        alt.Tooltip('properties.top_masculins:N', title='Top 3 Masculins'),
        alt.Tooltip('properties.top_feminins:N', title='Top 3 Féminins')
    ]
).project(
    type='mercator'
).properties(
    width=800,
    height=600
).interactive()

points = pd.DataFrame({})

points_chart = alt.Chart(points).mark_point(color='red', size=100).encode(
    x='x:Q',
    y='y:Q',
    tooltip=['label:N'])

combined_chart = alt.layer(map_chart, points_chart).configure_view(stroke=None)

st.altair_chart(combined_chart)
import altair as alt
import geopandas as gpd
import pandas as pd
import streamlit as st
import json
from shapely.affinity import translate

@st.cache_data
def load_geo_data():
    depts = gpd.read_file('./data/departements-avec-outre-mer.geojson')

    # Déplacer les DOM-TOM sous la France Métropolitaine
    dom_tom_translation = {
        '971': (0, 0),  # Guadeloupe
        '972': (-28, -30),  # Martinique
        '973': (-26, -30),  # Guyane
        '974': (-24, -30),  # La Réunion
        '975': (-22, -30),  # Saint-Pierre-et-Miquelon
        '976': (-20, -30),  # Mayotte
        '977': (-18, -30),  # Saint-Barthélemy
        '978': (-16, -30),  # Saint-Martin
        '984': (-14, -30),  # Terres australes et antarctiques françaises
        '986': (-12, -30),  # Wallis-et-Futuna
        '987': (-10, -30),  # Polynésie française
        '988': (-8, -30)    # Nouvelle-Calédonie
    }

    for code, translation in dom_tom_translation.items():
        depts.loc[depts['code'] == code, 'geometry'] = depts.loc[depts['code'] == code, 'geometry'].apply(
            lambda geom: translate(geom, xoff=translation[0], yoff=translation[1])
        )

    return depts

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
    selected_years = st.multiselect('Sélectionnez deux années', year_list, default=[year_list[0], year_list[-1]], max_selections=2)

if len(selected_years) == 2:
    start_year, end_year = min(selected_years), max(selected_years)
    filtered_names_for_top = names[(names['annais'] >= start_year) & (names['annais'] <= end_year)]
else:
    filtered_names_for_top = names[names['annais'] == selected_years[0]]

names_dict_for_top = get_top_bottom_names(filtered_names_for_top, True)
for sex, sex_names in names_dict_for_top.items():
    sex_names['dpt'] = sex_names['dpt'].astype(str)
    if sex == 1:
        depts = depts.merge(sex_names.groupby('dpt')['preusuel'].apply(lambda x: ', '.join(x)).reset_index(),
                            left_on='code', right_on='dpt', how='left').rename(columns={'preusuel': 'top_masculins'})
    else:
        depts = depts.merge(sex_names.groupby('dpt')['preusuel'].apply(lambda x: ', '.join(x)).reset_index(),
                            left_on='code', right_on='dpt', how='left').rename(columns={'preusuel': 'top_feminins'})

namesin_years = filtered_names_for_top
name_counts = namesin_years.groupby('preusuel')['nombre'].sum().reset_index()
name_counts = name_counts.sort_values(by='nombre', ascending=False)
name_counts['rank'] = name_counts['nombre'].rank(method='min', ascending=False).astype(int)

name_list = name_counts.apply(lambda row: f"{row['preusuel']} ({row['nombre']}, #{row['rank']})", axis=1).tolist()

with col2:
    selected_name_display = st.selectbox('Sélectionnez un PRÉNOM (Attributions, #Rang)', name_list)
selected_name = selected_name_display.split(' ')[0]

filtered_names = namesin_years[namesin_years['preusuel'] == selected_name]
name_counts__per_dept = filtered_names.groupby('dpt')['nombre'].sum().reset_index()

depts['code'] = depts['code'].astype(str)
name_counts__per_dept['dpt'] = name_counts__per_dept['dpt'].astype(str)
depts = depts.merge(name_counts__per_dept, left_on='code', right_on='dpt', how='left').rename(columns={'nombre': 'count_name'})
depts['count_name'] = depts['count_name'].fillna(0)

geojson_data = json.loads(depts.to_json())
geojson_features = alt.Data(values=geojson_data['features'])

max_count = depts['count_name'].max()
color_scale = alt.Scale(domain=[0, max_count/5, max_count/2, max_count],
                        range=['#f7fbff', '#c6dbef', '#6baed6', '#08306b'])

map_chart = alt.Chart(geojson_features).mark_geoshape().encode(
    color=alt.Color('properties.count_name:Q', scale=color_scale, legend=alt.Legend(title=f"Attributions de {selected_name}")),
    tooltip=[
        alt.Tooltip('properties.nom:N', title='Nom du Département'),
        alt.Tooltip('properties.code:N', title='Code du Département'),
        alt.Tooltip('properties.count_name:Q', title=f"{selected_name}"),
        alt.Tooltip('properties.top_masculins:N', title='Top 3 Masculins'),
        alt.Tooltip('properties.top_feminins:N', title='Top 3 Féminins')
    ]
).project(
    type='mercator',
    scale=2500,
    center=[2, 46]
).properties(
    width=800,
    height=1000
).interactive()

points = pd.DataFrame({})

points_chart = alt.Chart(points).mark_point(color='red', size=100).encode(
    x='x:Q',
    y='y:Q',
    tooltip=['label:N'])

combined_chart = alt.layer(map_chart, points_chart).configure_view(stroke=None)

st.altair_chart(combined_chart)
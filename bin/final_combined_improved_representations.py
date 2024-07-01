import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy.signal import find_peaks
import requests
import logging
from datetime import datetime
import geopandas as gpd
import json
from shapely.affinity import translate

@st.cache_data
def load_name_data():
    names = pd.read_csv("./data/dpt2020.csv", sep=";")
    names.drop(names[names.preusuel == '_PRENOMS_RARES'].index, inplace=True)
    names.drop(names[names.dpt == 'XX'].index, inplace=True)
    return names

@st.cache_data
def load_geo_data():
    depts = gpd.read_file('./data/departements-avec-outre-mer.geojson')

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
        height=500,
        title=f"Evolution of the name '{selected_name}' by gender over years"
    )
    return area_chart


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


st.set_page_config(layout="wide")

names = load_name_data()
depts = load_geo_data()

year_list = names['annais'].unique().tolist()
year_list.sort()

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


col1, col2 = st.columns([1, 1], gap="small")

with col1:

    st.subheader("Evolution du prénom dans le temps")
    
    name_evolution_chart = get_name_evolution_chart(names, selected_name)
    st.altair_chart(name_evolution_chart)

with col2:

    
    st.subheader("Carte Interactive des prénoms par région")

    filtered_names_for_all = names[(names['annais'] >= start_year) & (names['annais'] <= end_year)]
    
    total_names_per_dept = filtered_names_for_all.groupby('dpt')['nombre'].sum().reset_index().rename(columns={'nombre': 'total_count'})

    name_counts_per_dept = filtered_names_for_all[filtered_names_for_all['preusuel'] == selected_name].groupby('dpt')['nombre'].sum().reset_index()

    name_counts_per_dept = name_counts_per_dept.merge(total_names_per_dept, on='dpt', how='right')
    
    name_counts_per_dept['nombre'] = name_counts_per_dept['nombre'].fillna(0)
    
    name_counts_per_dept['proportion'] = name_counts_per_dept['nombre'] / name_counts_per_dept['total_count']
    
    depts['code'] = depts['code'].astype(str)
    name_counts_per_dept['dpt'] = name_counts_per_dept['dpt'].astype(str)
    depts = depts.merge(name_counts_per_dept, left_on='code', right_on='dpt', how='left').rename(columns={'proportion': 'proportion_name'})
    depts['proportion_name'] = depts['proportion_name'].fillna(0)

    geojson_data = json.loads(depts.to_json())
    geojson_features = alt.Data(values=geojson_data['features'])

    max_proportion = depts['proportion_name'].max()
    color_scale = alt.Scale(domain=[0, max_proportion/5, max_proportion/2, max_proportion],
                            range=['#f7fbff', '#c6dbef', '#6baed6', '#08306b'])

    points = pd.DataFrame({})
    points_chart = alt.Chart(points).mark_point(color='red', size=100).encode(
        x=alt.X('x:Q', axis=alt.Axis(title=None)),
        y=alt.Y('y:Q', axis=alt.Axis(title=None)),
        tooltip=['label:N'])

    map_chart_france = alt.Chart(geojson_features).mark_geoshape().encode(
        color=alt.Color('properties.proportion_name:Q', scale=color_scale, legend=alt.Legend(title=f"Proportion de {selected_name}")),
        tooltip=[
            alt.Tooltip('properties.nom:N', title='Nom du Département'),
            alt.Tooltip('properties.code:N', title='Code du Département'),
            alt.Tooltip('properties.proportion_name:Q', title=f"Proportion de {selected_name}"),
        ]
    ).project(
        type='mercator',
        scale=1500,
        center=[2, 46]
    ).properties(
        width=750,
        height=500
    ).interactive()
    combined_chart_france = alt.layer(map_chart_france, points_chart).configure_view(stroke=None)

    st.altair_chart(combined_chart_france)
    
    
def detect_recent_popularity(names, start_year, end_year, min_threshold=50, max_threshold=10000):
    names['annais'] = pd.to_numeric(names['annais'], errors='coerce')  # Convertir en numériques, remplacer les erreurs par NaN
    recent_names = names[(names['annais'] >= start_year) & (names['annais'] <= end_year)]
    name_trends = recent_names.groupby(['annais', 'preusuel'])['nombre'].sum().unstack().fillna(0)
    
    popular_names = []
    for name in name_trends.columns:
        popularity = name_trends[name]
        if min_threshold <= popularity.max() <= max_threshold:  # Vérifier si le prénom atteint le seuil
            peaks, _ = find_peaks(popularity, height=min_threshold)
            if len(peaks) > 0:
                popular_names.append((name, peaks, popularity.iloc[peaks].values))
            
    return popular_names, name_trends

def get_wikidata_results(name):
    query = f"""
    SELECT DISTINCT ?item ?itemLabel ?description WHERE {{
      ?item ?label "{name}"@fr.
      OPTIONAL {{ ?item schema:description ?description. FILTER(LANG(?description) = "fr" || LANG(?description) = "en") }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en". }}
    }} LIMIT 90
    """
    
    url = "https://query.wikidata.org/sparql"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, params={'query': query, 'format': 'json'}, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        results = data.get("results", {}).get("bindings", [])
        return [f"{result['itemLabel']['value']} - {result['description']['value']}" if 'description' in result else f"{result['itemLabel']['value']} - No description available" for result in results]
    else:
        return []

def get_events_for_date(date):
    query = f"https://fr.wikipedia.org/w/api.php?action=query&list=search&srsearch={date}&format=json&prop=extracts&exintro&explaintext"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(query, headers=headers)
    if response.status_code == 200:
        data = response.json()
        events = data.get("query", {}).get("search", [])
        detailed_events = []
        for event in events:
            title = event.get('title', 'No title')
            snippet = event.get('snippet', 'No description available').replace('<span class="searchmatch">', '').replace('</span>', '')
            if "football" not in title.lower() and "football" not in snippet.lower():
                detailed_events.append(f"{title} - {snippet}")
        return detailed_events
    else:
        return []

names = load_name_data()

st.title("Analyse des Prénoms Populaires en France")
st.subheader("Prénoms qui sont devenus soudainement populaires")

start_year, end_year = st.select_slider(
    'Sélectionnez un créneau d\'années pour l\'analyse',
    options=list(range(1900, 2021)),
    value=(1990, 2020)
)

min_threshold, max_threshold = st.select_slider(
    'Sélectionnez l\'intervalle de seuil de popularité pour détecter les pics',
    options=list(range(500, 10001,500)),
    value=(6000, 10000)
)

logging.info(f"Années sélectionnées: {start_year}-{end_year}, seuils: {min_threshold}-{max_threshold}")

popular_names, name_trends = detect_recent_popularity(names, start_year, end_year, min_threshold, max_threshold)

st.write(f"**Nombre de prénoms détectés comme récemment populaires entre {start_year} et {end_year}. En voici la liste: {len(popular_names)}**")

st.markdown("### Prénoms détectés comme récemment populaires")
for name, peaks, values in popular_names:
    st.markdown(f"{name} - Pics en {', '.join([str(name_trends.index[p]) for p in peaks])} avec des valeurs {', '.join(map(str, values))}")

st.subheader("Graphique des tendances globales des prénoms populaires")

fig_global = go.Figure()

for name, peaks, _ in popular_names:
    fig_global.add_trace(go.Scatter(x=name_trends.index, y=name_trends[name], mode='lines', name=name))

fig_global.update_layout(
    title=f"Tendances globales des prénoms populaires en France ({start_year}-{end_year})",
    xaxis_title="Années",
    yaxis_title="Popularité",
    legend_title="Prénoms",
    hovermode="x unified"
)

st.plotly_chart(fig_global)

st.subheader("Graphique des tendances spécifiques d'un prénom populaire")

selected_name = st.selectbox("Sélectionnez un prénom populaire", [name for name, _, _ in popular_names])

fig_specific = go.Figure()

for name, peaks, _ in popular_names:
    if name == selected_name:
        fig_specific.add_trace(go.Scatter(x=name_trends.index, y=name_trends[name], mode='lines+markers', name=name))
        # Vérifier que les pics existent bien dans les indices
        valid_peaks = [p for p in peaks if p < len(name_trends)]
        logging.info(f"Prénom: {name}, Pics: {valid_peaks}, Valeurs: {[name_trends.iloc[p][name] for p in valid_peaks]}")
        if valid_peaks:
            fig_specific.add_trace(go.Scatter(
                x=[name_trends.index[p] for p in valid_peaks],
                y=[name_trends.iloc[p][name] for p in valid_peaks],
                mode='markers',
                marker=dict(color='red', size=10),
                name="Pics de popularité",
                text=[f"Année: {name_trends.index[p]}, Popularité: {name_trends.iloc[p][name]}" for p in valid_peaks],
                hoverinfo='text'
            ))
            st.write(f"Pics pour {name}: {[name_trends.index[p] for p in valid_peaks]}")

fig_specific.update_layout(
    title=f"Tendances spécifiques du prénom {selected_name} en France ({start_year}-{end_year})",
    xaxis_title="Années",
    yaxis_title="Popularité",
    legend_title="Prénoms",
    hovermode="x unified"
)

st.plotly_chart(fig_specific)

st.subheader("Corrélations avec des événements culturels ou médiatiques")

if valid_peaks:
    selected_peak = st.selectbox("Sélectionnez un pic pour voir les événements associés", [name_trends.index[p] for p in valid_peaks])
    events = get_events_for_date(selected_peak)
    if events:
        st.write(f"### Événements associés à l'année {selected_peak}")
        for event in events:
            st.write(f"- {event}")
    else:
        st.write(f"Aucun événement trouvé pour l'année {selected_peak}")

st.write(f"### Événements culturels ou médiatiques associés à {selected_name}")

st.write(f"### Recherche sur {selected_name} sur Wikipédia")
st.write(f"***[Recherche sur {selected_name} sur Wikipédia](https://fr.wikipedia.org/wiki/{selected_name})***")
st.write(f"### Articles de presse sur {selected_name}")
st.write(f"***[Articles de presse sur {selected_name}](https://www.google.com/search?q={selected_name}+actualité)***")

st.subheader(f"15 premiers Résultats sur Wikidata pour {selected_name}")

wikidata_results = get_wikidata_results(selected_name)
if wikidata_results:
    for result in wikidata_results[:15]:
        st.markdown(f"<div class='wikidata-result'>{result}</div>", unsafe_allow_html=True)
else:
    st.write(f"Aucun résultat trouvé sur Wikidata pour {selected_name}.")


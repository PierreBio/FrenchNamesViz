import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy.signal import find_peaks
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

@st.cache_data
def load_name_data():
    names = pd.read_csv("dpt2020.csv", sep=";")
    return names

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

# Sélecteur d'années et intervalle de seuil
start_year, end_year = st.select_slider(
    'Sélectionnez un créneau d\'années pour l\'analyse',
    options=list(range(1900, 2021)),
    value=(1990, 2020)
)

# Sélecteurs pour le seuil de popularité en utilisant un seul curseur avec plage
min_threshold, max_threshold = st.select_slider(
    'Sélectionnez l\'intervalle de seuil de popularité pour détecter les pics',
    options=list(range(500, 10001,500)),
    value=(6000, 10000)
)

logging.info(f"Années sélectionnées: {start_year}-{end_year}, seuils: {min_threshold}-{max_threshold}")

popular_names, name_trends = detect_recent_popularity(names, start_year, end_year, min_threshold, max_threshold)

st.write(f"**Nombre de prénoms détectés comme récemment populaires entre {start_year} et {end_year}. En voici la liste: {len(popular_names)}**")

# Afficher la liste des prénoms détectés
st.markdown("### Prénoms détectés comme récemment populaires")
for name, peaks, values in popular_names:
    st.markdown(f"{name} - Pics en {', '.join([str(name_trends.index[p]) for p in peaks])} avec des valeurs {', '.join(map(str, values))}")

# Premier graphique pour les tendances globales
st.subheader("Graphique des tendances globales des prénoms populaires")

fig_global = go.Figure()

for name, peaks, _ in popular_names:
    fig_global.add_trace(go.Scatter(x=name_trends.index, y=name_trends[name], mode='lines', name=name))

# Ajouter les titres et les légendes
fig_global.update_layout(
    title=f"Tendances globales des prénoms populaires en France ({start_year}-{end_year})",
    xaxis_title="Années",
    yaxis_title="Popularité",
    legend_title="Prénoms",
    hovermode="x unified"
)

st.plotly_chart(fig_global)

# Deuxième graphique pour les tendances spécifiques
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

# Ajouter les titres et les légendes
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

# Affichage des événements culturels ou médiatiques associés
st.write(f"### Événements culturels ou médiatiques associés à {selected_name}")

# Liens vers des ressources externes
st.write(f"### Recherche sur {selected_name} sur Wikipédia")
st.write(f"***[Recherche sur {selected_name} sur Wikipédia](https://fr.wikipedia.org/wiki/{selected_name})***")
st.write(f"### Articles de presse sur {selected_name}")
st.write(f"***[Articles de presse sur {selected_name}](https://www.google.com/search?q={selected_name}+actualité)***")

# Résultats de Wikidata pour le prénom sélectionné
st.subheader(f"15 premiers Résultats sur Wikidata pour {selected_name}")

# Afficher les résultats de Wikidata pour le prénom sélectionné
wikidata_results = get_wikidata_results(selected_name)
if wikidata_results:
    for result in wikidata_results[:15]:
        st.markdown(f"<div class='wikidata-result'>{result}</div>", unsafe_allow_html=True)
else:
    st.write(f"Aucun résultat trouvé sur Wikidata pour {selected_name}.")
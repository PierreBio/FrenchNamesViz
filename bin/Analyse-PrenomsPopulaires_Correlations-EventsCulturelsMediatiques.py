import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from scipy.signal import find_peaks
import requests

@st.cache_data
def load_name_data():
    names = pd.read_csv("dpt2020.csv", sep=";")
    return names

def detect_recent_popularity(names, threshold=50):
    names['annais'] = pd.to_numeric(names['annais'], errors='coerce')  # Convertir en numériques, remplacer les erreurs par NaN 	
    recent_names = names[names['annais'] >= 2000]
    name_trends = recent_names.groupby(['annais', 'preusuel'])['nombre'].sum().unstack().fillna(0)
    
    popular_names = []
    for name in name_trends.columns:
        popularity = name_trends[name]
        if popularity.max() >= threshold:  # Vérifier si le prénom atteint le seuil
            peaks, _ = find_peaks(popularity, height=threshold)
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

names = load_name_data()

st.title("Analyse des Prénoms Récemment Populaires en France (2000-2020)")
st.subheader("Prénoms qui sont devenus soudainement populaires")

threshold = st.slider('Sélectionnez le seuil de popularité pour détecter les pics', 2500, 10000, 5000)

popular_names, name_trends = detect_recent_popularity(names, threshold)

# Indiquer le nombre de prénoms qui atteignent le pic
st.write(f"**Nombre de prénoms détectés comme récemment populaires. En voici la liste: {len(popular_names)}**")

# Ajouter du CSS pour serrer les lignes
st.markdown("""
    <style>
    .popular-name {
        margin-bottom: 5px;
    }
    .wikidata-result {
        margin-bottom: 5px;
    }
    .extra-space {
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.write(f"Prénoms détectés comme récemment populaires (seuil = {threshold}):")
for name, peaks, values in popular_names:
    st.markdown(f"<div class='popular-name'>{name} - Pics en {', '.join([str(name_trends.index[p]) for p in peaks])} avec des valeurs {', '.join(map(str, values))}</div>", unsafe_allow_html=True)

# Tracer les tendances des prénoms populaires
plt.figure(figsize=(14, 8))

for name, peaks, _ in popular_names:
    plt.plot(name_trends.index, name_trends[name], label=name)
    plt.scatter(name_trends.index[peaks], name_trends[name].iloc[peaks], color='red')  # Marquer les pics

# Ajouter les titres et les légendes
plt.title("Tendances des prénoms récemment populaires en France (2000-2020)")
plt.xlabel("Années")
plt.ylabel("Popularité")
plt.legend(title="Prénoms")
plt.grid(True)

st.pyplot(plt)

st.subheader("Corrélations avec des événements culturels ou médiatiques")

# Sélecteur de prénom pour l'analyse qualitative
selected_popular_name = st.selectbox("Sélectionnez un prénom populaire pour voir les événements culturels ou médiatiques associés.", [name for name, _, _ in popular_names])

# Placeholder pour les informations contextuelles
st.write(f"### Événements culturels ou médiatiques associés à {selected_popular_name}")


# Exemple d'informations contextuelles et événements historiques
contextual_info = {
    "Emma": {
        "info": "Popularisé par la série TV 'Friends' avec le personnage Emma Geller-Green.",
        "events": {
            2002: "Naissance d'Emma, la fille de Ross et Rachel dans la série 'Friends'.",
            2006: "Sortie du film 'Emma' avec Gwyneth Paltrow."
        }
    },
}    
    # Ajouter d'autres prénoms et événements ici

if selected_popular_name in contextual_info:
    st.write(contextual_info[selected_popular_name]["info"])
    st.write("### Événements historiques associés")
    for year, event in contextual_info[selected_popular_name]["events"].items():
        st.write(f"{year}: {event}")
else:
   st.write("Aucune information contextuelle disponible pour ce prénom.")

# Liens vers des ressources externes
st.write("### Ressources externes")
st.write(f"***[Recherche sur {selected_popular_name} sur Wikipédia](https://fr.wikipedia.org/wiki/{selected_popular_name})***")

# Ajouter du CSS pour serrer les lignes
st.markdown("""
    <style>
    .wikidata-result {
        margin-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
st.markdown("<div class='extra-space'></div>", unsafe_allow_html=True)
st.write(f"***[Articles de presse sur {selected_popular_name}](https://www.google.com/search?q={selected_popular_name}+actualité)***")

# Résultats de Wikidata pour le prénom sélectionné
st.subheader(f"15 premiers Résultats sur Wikidata pour {selected_popular_name}")

# Afficher les résultats de Wikidata pour le prénom sélectionné
wikidata_results = get_wikidata_results(selected_popular_name)
if wikidata_results:
    for result in wikidata_results[:15]:
        st.markdown(f"<div class='wikidata-result'>{result}</div>", unsafe_allow_html=True)
else:
    st.write(f"Aucun résultat trouvé sur Wikidata pour {selected_popular_name}.")


# Limiter l'affichage aux 15 premiers résultats
#for result in wikidata_results[:15]:
#    st.markdown(f"<div class='wikidata-result'>{result}</div>", unsafe_allow_html=True)







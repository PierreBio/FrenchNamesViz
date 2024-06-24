import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from scipy.signal import find_peaks

@st.cache_data
def load_name_data():
    names = pd.read_csv("./data/dpt2020.csv", sep=";")
    return names

def detect_recent_popularity(names, threshold=1000):
    recent_names = names[names['annais'] >= 2000]
    name_trends = recent_names.groupby(['annais', 'preusuel'])['nombre'].sum().unstack().fillna(0)

    popular_names = []
    for name in name_trends.columns:
        popularity = name_trends[name]
        peaks, _ = find_peaks(popularity, height=threshold)
        if len(peaks) > 0:
            popular_names.append((name, peaks, popularity.iloc[peaks].values))

    return popular_names, name_trends

names = load_name_data()

st.title("Analyse des Prénoms Récemment Populaires en France (2000-2020)")
st.subheader("Prénoms qui sont devenus soudainement populaires")

threshold = st.slider('Sélectionnez le seuil de popularité pour détecter les pics', 100, 5000, 1000)

popular_names, name_trends = detect_recent_popularity(names, threshold)

st.write(f"Prénoms détectés comme récemment populaires (seuil = {threshold}):")
for name, peaks, values in popular_names:
    st.write(f"{name} - Pics en {', '.join([str(name_trends.index[p]) for p in peaks])} avec des valeurs {', '.join(map(str, values))}")

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
st.write("Sélectionnez un prénom pour voir les événements culturels ou médiatiques associés.")

# Sélecteur de prénom pour l'analyse qualitative
selected_popular_name = st.selectbox("Sélectionnez un prénom populaire", [name for name, _, _ in popular_names])

# Placeholder pour les informations contextuelles
st.write(f"### Événements culturels ou médiatiques associés à {selected_popular_name}")

''' Exemple d'informations contextuelles et événements historiques :
contextual_info = {
    "Emma": {
        "info": " ---------------------",
        "events": {
            année: " ----------------------"
        }
    },'''


if selected_popular_name in contextual_info:
    st.write(contextual_info[selected_popular_name]["info"])
    st.write("### Événements historiques associés")
    for year, event in contextual_info[selected_popular_name]["events"].items():
        st.write(f"{year}: {event}")
else:
    st.write("Aucune information contextuelle disponible pour ce prénom.")

# Liens vers des ressources externes
st.write("### Ressources externes")
st.write(f"[Recherche sur {selected_popular_name} sur Wikipédia](https://fr.wikipedia.org/wiki/{selected_popular_name})")
st.write(f"[Articles de presse sur {selected_popular_name}](https://www.google.com/search?q={selected_popular_name}+actualité)")

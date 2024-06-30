# French Names Visualization

![logo_france](https://github.com/PierreBio/FrenchNamesViz/assets/45881846/d6a793c5-1a36-445c-bb00-60feab42dd38)

This project is carried out in the context of the Artificial Intelligence Masters of **TelecomParis**. He was made by **Barthelemy Quentin**, **Billaud Pierre**, **Chenna Reda**, **Letort Yannick**.

<sub>Made with __Python__</sub>

## Project

Development of 3 visualizations showing under different angles how firstnames evolved in France from 1900 to 2020.

## How to setup?

- First, clone the repository:

```
git clone https://github.com/PierreBio/FrenchNamesViz.git
```

- Then go to the root of the project:

```
cd FrenchNamesViz
```

- Create a virtual environment:

```
py -m venv venv
```

- Activate your environment:

```
.\venv\Scripts\activate
```

- Install requirements:

```
pip install -r requirements.txt
```

## How to launch?

- Once the project is setup, you can launch scripts to visualize our 3 graphics (initial and improvedd implementations):

```
streamlit run .\bin\gender_name.py
```

```
streamlit run .\bin\popular_name_by_region.py

streamlit run .\bin\popular_name_by_region_improved.py
```

```
streamlit run .\bin\popular_name_by_events.py

streamlit run .\bin\popular_name_by_events_improved.py
```

## Ressources

- https://streamlit.io/
- https://altair-viz.github.io/

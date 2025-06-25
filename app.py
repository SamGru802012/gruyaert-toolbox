
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from itertools import permutations

# -------------------- CONFIG --------------------
st.set_page_config(layout="wide")
st.title("📦 Gruyaert Verpakking Optimalisatie")

# -------------------- INVOER --------------------
st.sidebar.header("Productafmetingen (mm)")
l = st.sidebar.number_input("Lengte", 1, 2000, 100)
b = st.sidebar.number_input("Breedte", 1, 2000, 80)
h = st.sidebar.number_input("Hoogte", 1, 2000, 60)

st.sidebar.header("Marges in omdoos (mm)")
m_l = st.sidebar.number_input("Marge lengte", 0, 100, 0)
m_b = st.sidebar.number_input("Marge breedte", 0, 100, 0)
m_h = st.sidebar.number_input("Marge hoogte", 0, 100, 0)

# -------------------- LADEN VAN DATA --------------------
# Data ingeladen vanuit json (latente opslag), voorbeelddata:
try:
    with open("standaard_omverpakkingen.json", "r") as f:
        doos_data = json.load(f)
except FileNotFoundError:
    doos_data = [
        {"ID": 1, "Referentie": "A1", "Binnen_L": 300, "Binnen_B": 200, "Binnen_H": 150},
        {"ID": 2, "Referentie": "A2", "Binnen_L": 320, "Binnen_B": 220, "Binnen_H": 170},
        {"ID": 3, "Referentie": "A3", "Binnen_L": 350, "Binnen_B": 240, "Binnen_H": 190},
        {"ID": 4, "Referentie": "A4", "Binnen_L": 370, "Binnen_B": 260, "Binnen_H": 210},
        {"ID": 5, "Referentie": "A5", "Binnen_L": 390, "Binnen_B": 280, "Binnen_H": 230},
    ]

data = pd.DataFrame(doos_data)

# -------------------- OPTIMALISATIE MET ROTATIE --------------------
afmetingen = (l, b, h)
rotaties = sorted(set(permutations(afmetingen)))

resultaten = []

for _, rij in data.iterrows():
    binnen_l = rij["Binnen_L"] - m_l
    binnen_b = rij["Binnen_B"] - m_b
    binnen_h = rij["Binnen_H"] - m_h

    beste_aantal = 0
    beste_rotatie = None
    beste_indeling = None

    # Voor elke mogelijke oriëntatie van het product
    for rot in rotaties:
        rijen = int(binnen_l // rot[0])
        kolommen = int(binnen_b // rot[1])
        lagen = int(binnen_h // rot[2])
        totaal = rijen * kolommen * lagen

        if totaal > beste_aantal:
            beste_aantal = totaal
            beste_rotatie = rot
            beste_indeling = (rijen, kolommen, lagen)

    if beste_aantal > 0:
        resultaten.append({
            "ID": rij["ID"],
            "Referentie": rij.get("Referentie", ""),
            "Rotatie": f"{beste_rotatie}",
            "Indeling": f"{beste_indeling}",
            "Aantal producten": beste_aantal
        })

# -------------------- OUTPUT --------------------
if resultaten:
    st.subheader("✅ Geoptimaliseerde verpakkingsresultaten")
    st.dataframe(pd.DataFrame(resultaten))
else:
    st.warning("❗Geen resultaten. Pas marges of productgrootte aan.")

# -------------------- TOEKOMSTIGE UITBREIDING --------------------
# - Visualisatie met kleuren per laag/kolom/rij
# - Opslaan favorieten
# - Palletisatie op basis van rotatie
# - CSV/JSON export
# - Latente opslag bewerkingen

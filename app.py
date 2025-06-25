
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from itertools import permutations

st.set_page_config(layout="wide")
st.title("📦 Gruyaert Verpakking Optimalisatie")

# Invoer product
st.sidebar.header("Productafmetingen (mm)")
l = st.sidebar.number_input("Lengte", 1, 1000, 100)
b = st.sidebar.number_input("Breedte", 1, 1000, 80)
h = st.sidebar.number_input("Hoogte", 1, 1000, 60)

# Invoer marges
st.sidebar.header("Marges in omverpakking (mm)")
m_l = st.sidebar.number_input("Marge lengte", 0, 100, 0)
m_b = st.sidebar.number_input("Marge breedte", 0, 100, 0)
m_h = st.sidebar.number_input("Marge hoogte", 0, 100, 0)

# Laad omdozenbestand (mockdata)
data = pd.DataFrame({
    "ID": range(1, 6),
    "Binnen_L": [300, 320, 350, 370, 390],
    "Binnen_B": [200, 220, 240, 260, 280],
    "Binnen_H": [150, 170, 190, 210, 230],
})

resultaten = []
afmetingen = (l, b, h)
alle_rotaties = sorted(set(permutations(afmetingen)))

for _, rij in data.iterrows():
    binnen_l = rij["Binnen_L"] - m_l
    binnen_b = rij["Binnen_B"] - m_b
    binnen_h = rij["Binnen_H"] - m_h

    beste_score = 0
    beste_rot = None
    beste_indeling = None

    for rot in alle_rotaties:
        rijen = int(binnen_l // rot[0])
        kolommen = int(binnen_b // rot[1])
        lagen = int(binnen_h // rot[2])
        aantal = rijen * kolommen * lagen
        if aantal > beste_score:
            beste_score = aantal
            beste_rot = rot
            beste_indeling = (rijen, kolommen, lagen)

    if beste_score > 0:
        resultaten.append({
            "Doos ID": rij["ID"],
            "Score": beste_score,
            "Rotatie": f"{beste_rot}",
            "Indeling (R×K×L)": f"{beste_indeling}"
        })

# Toon resultaten
if resultaten:
    st.subheader("📊 Beste verpakkingsopties per doos")
    st.dataframe(pd.DataFrame(resultaten))
else:
    st.warning("❗Geen geschikte verpakkingen gevonden voor dit product en marges.")

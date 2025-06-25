import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
from itertools import permutations

# === Applicatie-instellingen ===
st.set_page_config(page_title="Gruyaert Verpakkingstool", layout="wide")
st.title("📦 Gruyaert Verpakkingstool")
st.success("Applicatie succesvol geladen. Volledige functionaliteit wordt verwerkt.")

# === Parameters ===
marge_l = st.number_input("Extra marge in lengte (mm)", 0, 100, 0, 1)
marge_b = st.number_input("Extra marge in breedte (mm)", 0, 100, 0, 1)
marge_h = st.number_input("Extra marge in hoogte (mm)", 0, 100, 0, 1)

product_l = st.number_input("Lengte product (mm)", 1, 1000, 100)
product_b = st.number_input("Breedte product (mm)", 1, 1000, 80)
product_h = st.number_input("Hoogte product (mm)", 1, 1000, 60)

referentie = st.text_input("Productreferentie (optioneel)", "")

# === Laad dataset ===
with open("standaard_omverpakkingen.json", "r") as f:
    data = json.load(f)
df = pd.DataFrame(data)

# === Optimalisatie ===
resultaten = []
for idx, row in df.iterrows():
    binnen_l = row["Lengte"] - marge_l
    binnen_b = row["Breedte"] - marge_b
    binnen_h = row["Hoogte"] - marge_h

    best_score = 0
    best_rot = None
    best_dims = None

    for rot in set(permutations([product_l, product_b, product_h])):
        p_l, p_b, p_h = rot
        r = binnen_l // p_l
        k = binnen_b // p_b
        z = binnen_h // p_h
        score = r * k * z
        if score > best_score:
            best_score = score
            best_rot = rot
            best_dims = (r, k, z)

    if best_score > 0:
        resultaten.append({
            "DoosID": row["ID"],
            "Score": best_score,
            "Rotatie": best_rot,
            "Aantal (Rijen, Kolommen, Lagen)": best_dims
        })

# === Resultaat ===
if resultaten:
    res_df = pd.DataFrame(resultaten).sort_values("Score", ascending=False)
    st.dataframe(res_df)
else:
    st.warning("⚠ Geen resultaten voldoen aan de opgegeven filters en marges.")

# app.py - Volledige heropgebouwde versie van de Gruyaert Toolbox

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGINA CONFIG ---
st.set_page_config(page_title="Gruyaert Toolbox", layout="wide")
st.title("📦 Gruyaert Toolbox")

# --- INITIATIE ---
if "dataset" not in st.session_state:
    df = pd.read_csv("standaard_omverpakkingen_50st.csv")
    df.insert(0, "ID", range(1, len(df)+1))
    st.session_state.dataset = df.copy()
    st.session_state.favorieten = []

# --- TABS ---
tabs = st.tabs(["Optimalisatie", "⭐ Gekozen oplossingen", "🧱 Palletstapeling", "📁 Beheer omdozen"])

# ---------------------------------------------
# 🔧 OPTIMALISATIE
# ---------------------------------------------
with tabs[0]:
    st.header("🔧 Optimaliseer omverpakking")

    col1, col2, col3 = st.columns(3)
    with col1:
        ref = st.text_input("Referentie product")
        l = st.number_input("Lengte product (mm)", min_value=1)
        margin_l = st.number_input("Extra marge lengte (mm)", min_value=0, value=0)
    with col2:
        b = st.number_input("Breedte product (mm)", min_value=1)
        margin_b = st.number_input("Extra marge breedte (mm)", min_value=0, value=0)
    with col3:
        h = st.number_input("Hoogte product (mm)", min_value=1)
        margin_h = st.number_input("Extra marge hoogte (mm)", min_value=0, value=0)

    dikte = st.number_input("Dikte omdoos (mm)", min_value=0, value=3)
    max_rij = st.slider("Max. rijen", 0, 10, value=10)
    max_kol = st.slider("Max. kolommen", 0, 10, value=10)
    max_laag = st.slider("Max. lagen", 0, 10, value=10)

    if st.button("🔍 Optimaliseer"):
        resultaten = []
        for i, row in st.session_state.dataset.iterrows():
            binnen_l = row['Lengte'] - 2*dikte - margin_l
            binnen_b = row['Breedte'] - 2*dikte - margin_b
            binnen_h = row['Hoogte'] - 2*dikte - margin_h
            if binnen_l <= 0 or binnen_b <= 0 or binnen_h <= 0:
                continue

            max_aantallen = []
            for l1, b1, h1 in [(l,b,h),(l,h,b),(b,l,h),(b,h,l),(h,l,b),(h,b,l)]:
                rij = int(binnen_l // l1)
                kol = int(binnen_b // b1)
                laag = int(binnen_h // h1)
                rij = min(rij, max_rij) if max_rij > 0 else 0
                kol = min(kol, max_kol) if max_kol > 0 else 0
                laag = min(laag, max_laag) if max_laag > 0 else 0

                totaal = rij * kol * laag
                max_aantallen.append((totaal, rij, kol, laag, (l1,b1,h1)))

            beste = max(max_aantallen, key=lambda x: x[0])
            if beste[0] > 0:
                resultaten.append({
                    "Omdoos": row["Referentie"],
                    "Aantal": beste[0],
                    "Rijen": beste[1], "Kolommen": beste[2], "Lagen": beste[3],
                    "Afm product": beste[4],
                    "Afm omdoos": (row['Lengte'], row['Breedte'], row['Hoogte'])
                })

        if resultaten:
            df_res = pd.DataFrame(resultaten).sort_values(by="Aantal", ascending=False)
            st.dataframe(df_res, use_container_width=True)
            keuze = st.selectbox("Selecteer omdoos om te visualiseren", df_res["Omdoos"])
            sel = df_res[df_res["Omdoos"] == keuze].iloc[0]

            # Visualisatie
            lx, bx, hx = sel["Afm omdoos"]
            pl, pb, ph = sel["Afm product"]
            fig = go.Figure()
            colors = ["red", "green", "blue"]
            for z in range(sel["Lagen"]):
                for y in range(sel["Kolommen"]):
                    for x in range(sel["Rijen"]):
                        fig.add_trace(go.Mesh3d(
                            x=[x*pl, x*pl+pl]*4,
                            y=[y*pb, y*pb+pb]*4,
                            z=[z*ph]*8,
                            opacity=0.6,
                            color=colors[z%3],
                            showscale=False
                        ))
            fig.update_layout(
                title="Visualisatie vulling omdoos",
                scene=dict(
                    xaxis_title="Lengte",
                    yaxis_title="Breedte",
                    zaxis_title="Hoogte"
                )
            )
            st.plotly_chart(fig, use_container_width=True)

            if st.button("➕ Bewaar deze oplossing"):
                st.session_state.favorieten.append({"Referentie": ref, **sel})

        else:
            st.warning("⚠ Geen geldige configuraties gevonden.")


import streamlit as st
import pandas as pd
import numpy as np
from itertools import product
import plotly.graph_objects as go

st.set_page_config(page_title="Gruyaert Toolbox", layout="wide")

st.title("📦 Gruyaert Verpakkingsoptimalisatie")

# Invoer product
st.sidebar.header("📥 Productafmetingen")
prod_l = st.sidebar.number_input("Lengte (mm)", min_value=1, value=100)
prod_b = st.sidebar.number_input("Breedte (mm)", min_value=1, value=100)
prod_h = st.sidebar.number_input("Hoogte (mm)", min_value=1, value=100)
prod_ref = st.sidebar.text_input("Referentie", value="Product X")

# Marges in verpakking
st.sidebar.header("📐 Marges in omverpakking")
marge_l = st.sidebar.number_input("Marge lengte", min_value=0, value=0)
marge_b = st.sidebar.number_input("Marge breedte", min_value=0, value=0)
marge_h = st.sidebar.number_input("Marge hoogte", min_value=0, value=0)

# Max beperkingen
st.sidebar.header("📊 Verdeelbeperkingen")
max_rijen = st.sidebar.number_input("Max rijen", min_value=0, value=10)
max_kolommen = st.sidebar.number_input("Max kolommen", min_value=0, value=10)
max_lagen = st.sidebar.number_input("Max lagen", min_value=0, value=10)

# CSV of interactieve input
st.sidebar.header("📁 Omverpakking")
data_source = st.sidebar.radio("Gegevensbron", ["Upload CSV", "Invoer via app"])
csv_file = st.sidebar.file_uploader("CSV bestand", type="csv") if data_source == "Upload CSV" else None

# Invoerdata
if data_source == "Upload CSV" and csv_file:
    df = pd.read_csv(csv_file)
elif data_source == "Invoer via app":
    df = pd.DataFrame([
        {"DoosID": "Test1", "Lengte": 400, "Breedte": 300, "Hoogte": 200},
        {"DoosID": "Test2", "Lengte": 500, "Breedte": 350, "Hoogte": 300}
    ])
else:
    df = pd.DataFrame()

# Marges toepassen
if not df.empty:
    df["Binnen_L"] = df["Lengte"] - marge_l
    df["Binnen_B"] = df["Breedte"] - marge_b
    df["Binnen_H"] = df["Hoogte"] - marge_h
    st.subheader("📋 Overzicht omverpakking")
    st.dataframe(df)

    results = []
    for _, row in df.iterrows():
        binnen_l, binnen_b, binnen_h = row["Binnen_L"], row["Binnen_B"], row["Binnen_H"]
        best = {"DoosID": row["DoosID"], "Aantal": 0}
        for r in range(1, max_rijen+1):
            for k in range(1, max_kolommen+1):
                for z in range(1, max_lagen+1):
                    needed_l = r * prod_l
                    needed_b = k * prod_b
                    needed_h = z * prod_h
                    if needed_l <= binnen_l and needed_b <= binnen_b and needed_h <= binnen_h:
                        aantal = r * k * z
                        if aantal > best["Aantal"]:
                            best = {"DoosID": row["DoosID"], "Aantal": aantal, "Rijen": r, "Kolommen": k, "Lagen": z}
        results.append(best)

    df_results = pd.DataFrame(results)
    st.subheader("✅ Beste verpakkingsopties")
    st.dataframe(df_results)

    if not df_results.empty:
        gekozen = st.selectbox("Toon visualisatie voor:", df_results["DoosID"])
        selected = df_results[df_results["DoosID"] == gekozen].iloc[0]
        fig = go.Figure()
        kleuren = ["red", "green", "blue", "orange", "purple", "cyan", "magenta"]
        idx = 0
        for x in range(selected["Rijen"]):
            for y in range(selected["Kolommen"]):
                for z in range(selected["Lagen"]):
                    fig.add_trace(go.Mesh3d(
                        x=[x*prod_l, (x+1)*prod_l, (x+1)*prod_l, x*prod_l]*2,
                        y=[y*prod_b, y*prod_b, (y+1)*prod_b, (y+1)*prod_b]*2,
                        z=[z*prod_h]*4 + [(z+1)*prod_h]*4,
                        color=kleuren[idx % len(kleuren)],
                        opacity=0.7,
                        alphahull=0
                    ))
                    idx += 1
        fig.update_layout(scene=dict(
            xaxis_title="Lengte",
            yaxis_title="Breedte",
            zaxis_title="Hoogte"
        ), title="3D visualisatie van producten in omdoos")
        st.plotly_chart(fig)
else:
    st.info("📎 Upload een CSV of gebruik invoer via de app.")

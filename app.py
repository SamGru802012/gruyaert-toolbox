
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide", page_title="Gruyaert Toolbox")
st.title("📦 Gruyaert Toolbox – Omverpakking Optimalisatie")

# Standaarddata ingebed
default_data = pd.DataFrame([
    {"Referentie": "", "Lengte": 300, "Breedte": 200, "Hoogte": 150, "Dikte": 3, "Stock": 100},
    {"Referentie": "", "Lengte": 250, "Breedte": 180, "Hoogte": 140, "Dikte": 3, "Stock": 80},
    {"Referentie": "", "Lengte": 400, "Breedte": 300, "Hoogte": 200, "Dikte": 4, "Stock": 50},
    {"Referentie": "", "Lengte": 320, "Breedte": 210, "Hoogte": 160, "Dikte": 3, "Stock": 60},
    {"Referentie": "", "Lengte": 270, "Breedte": 190, "Hoogte": 170, "Dikte": 2, "Stock": 90}
])

default_data = default_data.astype({
    "Referentie": str, "Lengte": int, "Breedte": int, "Hoogte": int, "Dikte": int, "Stock": int
})

if "data_beheer" not in st.session_state:
    st.session_state.data_beheer = default_data.copy()

tab1, tab2 = st.tabs(["📊 Optimalisatie", "🗂️ Beheer omverpakking"])

with tab1:
    st.subheader("📐 Optimaliseer de omverpakking voor een product")
    ref = st.text_input("Referentie voor dit product")
    l = st.number_input("Lengte product (mm)", min_value=1)
    b = st.number_input("Breedte product (mm)", min_value=1)
    h = st.number_input("Hoogte product (mm)", min_value=1)
    marge_l = st.number_input("Marge in lengte (mm)", value=0)
    marge_b = st.number_input("Marge in breedte (mm)", value=0)
    marge_h = st.number_input("Marge in hoogte (mm)", value=0)

    max_r = st.slider("Max rijen", 0, 10, 10)
    max_k = st.slider("Max kolommen", 0, 10, 10)
    max_z = st.slider("Max lagen", 0, 10, 10)

    best_result = None
    best_score = 0

    for idx, row in st.session_state.data_beheer.iterrows():
        bin_l = row["Lengte"] - marge_l
        bin_b = row["Breedte"] - marge_b
        bin_h = row["Hoogte"] - marge_h
        dikte = row["Dikte"]
        inner_l, inner_b, inner_h = bin_l - 2*dikte, bin_b - 2*dikte, bin_h - 2*dikte
        beste = {"score": 0}

        for r in range(1, max_r + 1):
            for k in range(1, max_k + 1):
                for z in range(1, max_z + 1):
                    fits = (l * r <= inner_l) and (b * k <= inner_b) and (h * z <= inner_h)
                    if fits:
                        score = r * k * z
                        if score > beste["score"]:
                            beste = {
                                "doos_index": idx,
                                "score": score,
                                "rijen": r,
                                "kolommen": k,
                                "lagen": z,
                                "bin_dim": (inner_l, inner_b, inner_h),
                                "buiten_dim": (row["Lengte"], row["Breedte"], row["Hoogte"]),
                                "referentie": row["Referentie"]
                            }

        if beste["score"] > best_score:
            best_score = beste["score"]
            best_result = beste

    if best_result:
        st.success(f"🎯 Beste omverpakking: {best_result['buiten_dim']} → {best_result['score']} stuks ({best_result['rijen']}r x {best_result['kolommen']}k x {best_result['lagen']}l)")

        if st.checkbox("Toon visualisatie"):
            fig = go.Figure()
            for zi in range(best_result["lagen"]):
                for yi in range(best_result["kolommen"]):
                    for xi in range(best_result["rijen"]):
                        fig.add_trace(go.Scatter3d(
                            x=[xi*l, xi*l + l, xi*l + l, xi*l],
                            y=[yi*b, yi*b, yi*b + b, yi*b + b],
                            z=[zi*h]*4,
                            mode='lines',
                            line=dict(color='blue')
                        ))
            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                scene=dict(
                    xaxis_title="L",
                    yaxis_title="B",
                    zaxis_title="H",
                    aspectmode='data'
                )
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠ Geen passende omverpakking gevonden.")

with tab2:
    st.subheader("📋 Database van omverpakkingen")
    df = st.session_state.data_beheer
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="beheer_editor")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Wijzigingen opslaan"):
            st.session_state.data_beheer = edited_df
            st.success("Gegevens zijn opgeslagen.")
    with col2:
        if st.button("➕ Voeg lege rij toe"):
            lege_rij = {"Referentie": "", "Lengte": 0, "Breedte": 0, "Hoogte": 0, "Dikte": 3, "Stock": 0}
            st.session_state.data_beheer.loc[len(df)] = lege_rij
            st.experimental_rerun()
    with col3:
        if st.button("🗑️ Verwijder laatste rij") and not df.empty:
            st.session_state.data_beheer.drop(df.tail(1).index, inplace=True)
            st.experimental_rerun()

    st.download_button("⬇️ Download CSV", data=st.session_state.data_beheer.to_csv(index=False),
                       file_name="gruyaert_omverpakking_data.csv", mime="text/csv")

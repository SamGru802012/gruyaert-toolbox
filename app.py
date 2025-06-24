
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("📦 Gruyaert Toolbox – Verpakking Optimalisatie")

tab1, tab2 = st.tabs(["🔍 Optimalisatie", "🗂️ Data Beheer"])

def nummer_ids(df):
    df = df.reset_index(drop=True)
    df["DoosID"] = [f"OMV{i+1:03}" for i in range(len(df))]
    return df

# === TAB 2: DATA BEHEER ===
with tab2:
    st.header("🗂️ Omverpakking Beheer")

    
default_csv = "omverpakking_dataset_definitief.csv"
if "data_beheer" not in st.session_state:
    try:
        df_default = pd.read_csv(default_csv)
        st.session_state.data_beheer = nummer_ids(df_default)
    except:
        st.session_state.data_beheer = pd.DataFrame(columns=["Lengte", "Breedte", "Hoogte", "Dikte", "Stock", "Referentie"])

        st.session_state.data_beheer = pd.DataFrame(columns=["Lengte", "Breedte", "Hoogte", "Dikte", "Stock", "Referentie"])

    uploaded_file = st.file_uploader("Upload CSV", type="csv")
    if uploaded_file:
        df_uploaded = pd.read_csv(uploaded_file)
        st.session_state.data_beheer = nummer_ids(df_uploaded)

    df_edit = st.session_state.data_beheer.copy()
    df_edit["🗑️ Verwijder"] = False

    edited = st.data_editor(
        df_edit.drop(columns=["DoosID"], errors="ignore"),
        num_rows="dynamic",
        use_container_width=True,
        key="editor"
    )

    edited = edited[edited["🗑️ Verwijder"] == False].drop(columns=["🗑️ Verwijder"])
    updated = nummer_ids(edited)
    st.session_state.data_beheer = updated
    st.dataframe(updated)

    if st.button("💾 Download bewerkte CSV"):
        csv = updated.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, file_name="omverpakking_data.csv", mime="text/csv")

# === TAB 1: OPTIMALISATIE ===
with tab1:
    st.header("🔍 Optimalisatie Parameters")

    if st.session_state.data_beheer.empty:
        st.warning("⚠️ Geen data gevonden. Voeg dozen toe via 'Data Beheer'.")
        st.stop()

    df = st.session_state.data_beheer.copy()

    col1, col2, col3 = st.columns(3)
    with col1:
        l = st.number_input("Product lengte", 1, 1000, 100)
    with col2:
        b = st.number_input("Product breedte", 1, 1000, 80)
    with col3:
        h = st.number_input("Product hoogte", 1, 1000, 60)

    marge_l = st.number_input("Marge lengte", 0, 100, 0)
    marge_b = st.number_input("Marge breedte", 0, 100, 0)
    marge_h = st.number_input("Marge hoogte", 0, 100, 0)

    max_r = st.number_input("Max rijen", 0, 100, 10)
    max_k = st.number_input("Max kolommen", 0, 100, 10)
    max_l = st.number_input("Max lagen", 0, 100, 10)

    resultaten = []
    for _, row in df.iterrows():
        bin_l = row["Lengte"] - marge_l
        bin_b = row["Breedte"] - marge_b
        bin_h = row["Hoogte"] - marge_h

        beste = {"DoosID": row["DoosID"], "Aantal": 0}
        for r in range(1, int(bin_l // l) + 1):
            if max_r and r > max_r:
                continue
            for k in range(1, int(bin_b // b) + 1):
                if max_k and k > max_k:
                    continue
                for z in range(1, int(bin_h // h) + 1):
                    if max_l and z > max_l:
                        continue
                    aantal = r * k * z
                    efficiëntie = (aantal * l * b * h) / (row["Lengte"] * row["Breedte"] * row["Hoogte"])
                    if aantal > beste["Aantal"]:
                        beste.update({
                            "Aantal": aantal,
                            "Efficiëntie": round(efficiëntie * 100, 2),
                            "Rijen": r,
                            "Kolommen": k,
                            "Lagen": z
                        })
        resultaten.append(beste)

    df_result = pd.DataFrame(resultaten)
    st.subheader("📊 Resultaten")
    st.dataframe(df_result)

    if not df_result.empty:
        keuze = st.selectbox("Visualiseer omverpakking:", df_result["DoosID"])
        gekozen = df_result[df_result["DoosID"] == keuze].iloc[0]

        fig = go.Figure()
        kleuren = ["red", "green", "blue", "orange", "purple"]
        for x in range(gekozen["Rijen"]):
            for y in range(gekozen["Kolommen"]):
                for z in range(gekozen["Lagen"]):
                    fig.add_trace(go.Mesh3d(
                        x=[x*l, (x+1)*l, (x+1)*l, x*l]*2,
                        y=[y*b, y*b, (y+1)*b, (y+1)*b]*2,
                        z=[z*h]*4 + [(z+1)*h]*4,
                        color=kleuren[(x+y+z)%len(kleuren)],
                        opacity=0.7,
                        alphahull=0
                    ))
        fig.update_layout(scene=dict(xaxis_title="L", yaxis_title="B", zaxis_title="H"))
        st.plotly_chart(fig)

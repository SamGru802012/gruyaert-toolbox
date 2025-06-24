
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("📦 Gruyaert Toolbox — Verpakking Optimalisatie")

tab1, tab2 = st.tabs(["🔍 Optimalisatie", "🗂️ Beheer Omverpakking"])

def nummer_ids(df):
    df = df.reset_index(drop=True)
    df["DoosID"] = [f"OMV{i+1:03}" for i in range(len(df))]
    return df

# === TAB 2: Beheer ===
with tab2:
    st.header("🗂️ Omverpakking Data Beheer")

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"], key="beheer_csv")

    if "data_beheer" not in st.session_state:
        st.session_state.data_beheer = pd.DataFrame(columns=["Lengte", "Breedte", "Hoogte", "Dikte", "Stock", "Referentie"])

    if uploaded_file:
        df_beheer = pd.read_csv(uploaded_file)
        if "DoosID" not in df_beheer.columns:
            df_beheer = nummer_ids(df_beheer)
        st.session_state.data_beheer = df_beheer

    st.markdown("📝 **Bewerk hieronder je data.** Nieuw record toevoegen = lege rij invullen onderaan.")
    
edited_df = st.session_state.data_beheer.drop(columns=["DoosID"], errors="ignore").copy()
edited_df["🗑️ Verwijder"] = False

edited_df = st.data_editor(

        st.session_state.data_beheer.drop(columns=["DoosID"], errors="ignore"),
        num_rows="dynamic",
        use_container_width=True,
        key="beheer_editor"
    )

    # Voeg ID opnieuw toe
    
edited_df = edited_df[edited_df["🗑️ Verwijder"] == False].drop(columns=["🗑️ Verwijder"])
updated_df = nummer_ids(edited_df)

    st.session_state.data_beheer = updated_df

    st.dataframe(updated_df)

    if st.button("💾 Opslaan als CSV"):
        csv = updated_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download", csv, file_name="omverpakking_dataset.csv", mime="text/csv")

# === TAB 1: Optimalisatie ===
with tab1:
    st.header("🔍 Optimalisatie")

    if st.session_state.data_beheer.empty:
        st.warning("⚠️ Voeg eerst dozen toe in het tabblad 'Beheer Omverpakking'")
        st.stop()

    df = st.session_state.data_beheer.copy()
    l = st.number_input("Lengte product (mm)", min_value=1, value=100)
    b = st.number_input("Breedte product (mm)", min_value=1, value=80)
    h = st.number_input("Hoogte product (mm)", min_value=1, value=60)
    ref = st.text_input("📌 Productreferentie", value="Product X")

    marge_l = st.number_input("Marge lengte (mm)", 0, 100, 0)
    marge_b = st.number_input("Marge breedte (mm)", 0, 100, 0)
    marge_h = st.number_input("Marge hoogte (mm)", 0, 100, 0)

    max_r = st.number_input("Max rijen", 0, 100, 10)
    max_k = st.number_input("Max kolommen", 0, 100, 10)
    max_l = st.number_input("Max lagen", 0, 100, 10)

    resultaten = []

    for idx, row in df.iterrows():
        bin_l = row["Lengte"] - marge_l
        bin_b = row["Breedte"] - marge_b
        bin_h = row["Hoogte"] - marge_h

        opties = []
        for r in range(1, int(bin_l // l) + 1):
            if max_r and r > max_r: continue
            for k in range(1, int(bin_b // b) + 1):
                if max_k and k > max_k: continue
                for z in range(1, int(bin_h // h) + 1):
                    if max_l and z > max_l: continue
                    aantal = r * k * z
                    volume_producten = aantal * l * b * h
                    volume_doos = row["Lengte"] * row["Breedte"] * row["Hoogte"]
                    efficiëntie = volume_producten / volume_doos
                    opties.append((aantal, efficiëntie, r, k, z))

        if opties:
            best = max(opties, key=lambda x: (x[0], x[1]))
            resultaten.append({
                "DoosID": row["DoosID"],
                "Aantal": best[0],
                "Efficiëntie": round(best[1]*100, 2),
                "Rijen": best[2],
                "Kolommen": best[3],
                "Lagen": best[4]
            })

    if resultaten:
        df_res = pd.DataFrame(resultaten)
        st.dataframe(df_res)

        keuze = st.selectbox("📦 Visualiseer omdoos", df_res["DoosID"])
        selected = df_res[df_res["DoosID"] == keuze].iloc[0]

        fig = go.Figure()
        kleuren = ["red", "green", "blue", "orange"]
        for x in range(selected["Rijen"]):
            for y in range(selected["Kolommen"]):
                for z in range(selected["Lagen"]):
                    fig.add_trace(go.Mesh3d(
                        x=[x*l, (x+1)*l, (x+1)*l, x*l]*2,
                        y=[y*b, y*b, (y+1)*b, (y+1)*b]*2,
                        z=[z*h]*4 + [(z+1)*h]*4,
                        color=kleuren[(x+y+z) % len(kleuren)],
                        opacity=0.7,
                        alphahull=0
                    ))
        fig.update_layout(scene=dict(xaxis_title="L", yaxis_title="B", zaxis_title="H"))
        st.plotly_chart(fig)

    else:
        st.warning("❌ Geen geschikte combinaties gevonden.")

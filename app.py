
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="Gruyaert Toolbox")

st.title("📦 Gruyaert Toolbox – Omverpakking Optimalisatie")

# Ingebedde standaarddataset
default_data = pd.DataFrame([{'Lengte': 300, 'Breedte': 200, 'Hoogte': 150, 'Dikte': 3, 'Stock': 100, 'Referentie': ''}, {'Lengte': 250, 'Breedte': 180, 'Hoogte': 140, 'Dikte': 3, 'Stock': 80, 'Referentie': ''}, {'Lengte': 400, 'Breedte': 300, 'Hoogte': 200, 'Dikte': 4, 'Stock': 50, 'Referentie': ''}, {'Lengte': 320, 'Breedte': 210, 'Hoogte': 160, 'Dikte': 3, 'Stock': 60, 'Referentie': ''}, {'Lengte': 270, 'Breedte': 190, 'Hoogte': 170, 'Dikte': 2, 'Stock': 90, 'Referentie': ''}])
default_data = default_data.astype({
    "Lengte": int, "Breedte": int, "Hoogte": int, "Dikte": int, "Stock": int, "Referentie": str
})

# Session state initialiseren
if "data_beheer" not in st.session_state:
    st.session_state.data_beheer = default_data.copy()
if "next_id" not in st.session_state:
    st.session_state.next_id = len(default_data)

tab1, tab2 = st.tabs(["📊 Optimalisatie", "🗂️ Beheer omverpakking"])

with tab2:
    st.subheader("🗂️ Omverpakking database")
    df = st.session_state.data_beheer

    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="beheer_editor")

    if st.button("💾 Wijzigingen opslaan"):
        st.session_state.data_beheer = edited_df
        st.success("Gegevens bijgewerkt!")

    if st.button("➕ Voeg lege rij toe"):
        nieuwe_rij = {
            "Lengte": 0, "Breedte": 0, "Hoogte": 0, "Dikte": 3, "Stock": 0, "Referentie": ""
        }
        st.session_state.data_beheer.loc[len(st.session_state.data_beheer)] = nieuwe_rij
        st.experimental_rerun()

    if st.button("🗑️ Verwijder laatste rij") and not st.session_state.data_beheer.empty:
        st.session_state.data_beheer.drop(st.session_state.data_beheer.tail(1).index, inplace=True)
        st.experimental_rerun()

    st.download_button("⬇️ Exporteer als CSV", data=st.session_state.data_beheer.to_csv(index=False),
                       file_name="omverpakking_export.csv", mime="text/csv")

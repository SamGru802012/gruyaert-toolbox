
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="Gruyaert Toolbox")

st.title("📦 Gruyaert Toolbox – Omverpakking Optimalisatie")

# Ingebedde standaarddataset (Referentie als eerste kolom)
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

# Session state initialiseren
if "data_beheer" not in st.session_state:
    st.session_state.data_beheer = default_data.copy()

# Tabs
tab1, tab2 = st.tabs(["📊 Optimalisatie", "🗂️ Beheer omverpakking"])

with tab2:
    st.subheader("📋 Database van omverpakkingen")

    df = st.session_state.data_beheer

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        key="beheer_editor"
    )

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

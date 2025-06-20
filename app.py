
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Gruyaert Toolbox", layout="wide")
st.title("📦 Gruyaert Verpakking Optimalisatie")

uploaded_file = st.file_uploader("Upload een CSV met omverpakkingen", type=["csv"])

if uploaded_file:
    try:
        df_raw = pd.read_csv(uploaded_file)
        st.success("✅ Bestand succesvol geladen!")
    except Exception as e:
        st.error(f"Fout bij inlezen bestand: {e}")
        st.stop()
else:
    st.info("📄 Upload eerst een bestand om te starten.")
    st.stop()

# UI tabs
tab1, tab2, tab3 = st.tabs(["📐 Verpakking", "⚠️ Uitsluitingen", "📤 Export"])

with tab1:
    st.subheader("🔢 Productafmetingen (mm)")
    col1, col2, col3 = st.columns(3)
    with col1:
        pl = st.number_input("Lengte", min_value=1, value=200)
    with col2:
        pb = st.number_input("Breedte", min_value=1, value=150)
    with col3:
        ph = st.number_input("Hoogte", min_value=1, value=100)

    st.subheader("➕ Spatieverlies (trekt af van omverpakking!)")
    col4, col5, col6 = st.columns(3)
    with col4:
        sl = st.number_input("Spatie lengte", min_value=0, value=0)
    with col5:
        sb = st.number_input("Spatie breedte", min_value=0, value=20)
    with col6:
        sh = st.number_input("Spatie hoogte", min_value=0, value=0)

    st.subheader("📏 Palletinstellingen")
    col7, col8 = st.columns(2)
    with col7:
        pallet_height_max = st.number_input("Max. pallethoogte (incl. goederen)", value=1800)
    with col8:
        pallet_height_base = st.number_input("Hoogte lege pallet", value=150)

    resultaten = []
    uitsluitingen = []

    if st.button("🔍 Zoek optimale omverpakkingen"):

        required_columns = ["Lengte_mm", "Breedte_mm", "Hoogte_mm"]
        if not any("DoosID" in c or "OmverpakkingsID" in c for c in df_raw.columns):
            st.error("CSV mist verplichte kolom: 'OmverpakkingsID' of 'DoosID'")
            st.stop()
        if not all(col in df_raw.columns for col in required_columns):
            st.error("CSV mist vereiste afmetingskolommen: 'Lengte_mm', 'Breedte_mm', 'Hoogte_mm'")
            st.stop()

        df = df_raw.copy()
        orientations = [(pl, pb, ph), (pl, ph, pb), (pb, pl, ph), (pb, ph, pl), (ph, pl, pb), (ph, pb, pl)]

        for idx, row in df.iterrows():
            box_id = row.get("DoosID", row.get("OmverpakkingsID", f"DOOS-{idx+1}"))
            usable_l = row["Lengte_mm"] - sl
            usable_b = row["Breedte_mm"] - sb
            usable_h = row["Hoogte_mm"] - sh
            best = {}

            for o in orientations:
                l, b, h = o
                r = int(usable_l // l)
                k = int(usable_b // b)
                z = int((usable_h) // h)
                aantal = r * k * z
                hoogte_gebruikt = z * h
                totale_pallet_hoogte = hoogte_gebruikt + pallet_height_base

                if aantal == 0:
                    uitsluitingen.append({"OmverpakkingsID": box_id, "Reden": "Aantal = 0", "Afmetingen na verlies": f"{usable_l}×{usable_b}×{usable_h}"})
                    continue
                if totale_pallet_hoogte > pallet_height_max:
                    uitsluitingen.append({"OmverpakkingsID": box_id, "Reden": f"Hoogte {totale_pallet_hoogte} > {pallet_height_max}", "Afmetingen na verlies": f"{usable_l}×{usable_b}×{usable_h}"})
                    continue

                score = aantal * l * b * h
                if "score" not in best or score > best["score"]:
                    best = {
                        "OmverpakkingsID": box_id,
                        "Omverpakking_afmetingen": f"{int(row['Lengte_mm'])}×{int(row['Breedte_mm'])}×{int(row['Hoogte_mm'])}",
                        "Gebruikte_orientatie": f"{l}×{b}×{h}",
                        "Rijen": r,
                        "Kolommen": k,
                        "Lagen": z,
                        "Aantal": aantal,
                        "Totale hoogte (mm)": totale_pallet_hoogte,
                        "Score": score
                    }

            if "score" in best:
                resultaten.append(best)

        if resultaten:
            df_result = pd.DataFrame(resultaten).sort_values("Score", ascending=False)
            st.success(f"✅ {len(df_result)} resultaten gevonden.")
            st.dataframe(df_result)

            st.markdown("---")
            st.subheader("📊 Visualisatie")
            selected = st.selectbox("Kies een omverpakking", df_result["OmverpakkingsID"])
            selected_row = df_result[df_result["OmverpakkingsID"] == selected].iloc[0]
            r, k, z = selected_row["Rijen"], selected_row["Kolommen"], selected_row["Lagen"]
            l_str, b_str, h_str = selected_row["Gebruikte_orientatie"].split("×")
            l, b, h = float(l_str), float(b_str), float(h_str)
            fig = go.Figure()
            for zi in range(z):
                for yi in range(k):
                    for xi in range(r):
                        fig.add_trace(go.Mesh3d(
                            x=[xi*l, xi*l, (xi+1)*l, (xi+1)*l, xi*l, xi*l, (xi+1)*l, (xi+1)*l],
                            y=[yi*b, (yi+1)*b, (yi+1)*b, yi*b, yi*b, (yi+1)*b, (yi+1)*b, yi*b],
                            z=[zi*h]*4 + [(zi+1)*h]*4,
                            color='lightblue',
                            opacity=0.5,
                            showscale=False
                        ))
            fig.update_layout(scene=dict(xaxis_title='L', yaxis_title='B', zaxis_title='H'), margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig)

with tab2:
    st.subheader("🛑 Uitsluitingen (indien van toepassing)")
    if uitsluitingen:
        df_uitsluit = pd.DataFrame(uitsluitingen)
        st.dataframe(df_uitsluit)
        csv_uitsluit = df_uitsluit.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download uitsluitingen", data=csv_uitsluit, file_name="uitsluitingen.csv", mime="text/csv")
    else:
        st.info("⚠ Geen uitsluitingen geregistreerd.")

with tab3:
    if 'df_result' in locals():
        csv_succes = df_result.to_csv(index=False).encode("utf-8")
        st.success("✅ Klaar voor export")
        st.download_button("📤 Download resultaten", data=csv_succes, file_name="resultaten.csv", mime="text/csv")
    else:
        st.warning("⛔ Nog geen berekende resultaten om te exporteren.")

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Gruyaert Verpakkingstool", layout="centered")

st.title("📦 Gruyaert Verpakking Optimalisatie")

# Upload CSV
uploaded_file = st.file_uploader("Upload een CSV met omverpakkingen", type=["csv"])
if uploaded_file:
    try:
        df_raw = pd.read_csv(uploaded_file)
        st.success("✅ Bestand succesvol geladen!")
        st.write("Voorbeeld van data:", df_raw.head())
    except Exception as e:
        st.error(f"Fout bij inlezen bestand: {e}")
        st.stop()
else:
    st.info("📄 Upload eerst een bestand om te starten.")
    st.stop()

st.markdown("---")
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

st.markdown("---")
if st.button("🔍 Zoek optimale omverpakkingen"):

    required_columns = ["OmverpakkingsID", "Lengte_mm", "Breedte_mm", "Hoogte_mm"]
    if not all(col in df_raw.columns for col in required_columns):
        st.error("CSV mist verplichte kolommen: 'OmverpakkingsID', 'Lengte_mm', 'Breedte_mm', 'Hoogte_mm'")
        st.stop()

    df = df_raw.copy()
    resultaten = []

    orientations = [
        (pl, pb, ph),
        (pl, ph, pb),
        (pb, pl, ph),
        (pb, ph, pl),
        (ph, pl, pb),
        (ph, pb, pl)
    ]

    for _, row in df.iterrows():
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

            if aantal > 0 and totale_pallet_hoogte <= pallet_height_max:
                score = aantal * l * b * h
                if "score" not in best or score > best["score"]:
                    best = {
                        "OmverpakkingsID": row["OmverpakkingsID"],
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
        st.success(f"✅ {len(resultaten)} resultaten gevonden.")
        df_result = pd.DataFrame(resultaten).sort_values("Score", ascending=False)
        st.dataframe(df_result)
    else:
        st.warning("⚠ Geen resultaten voldoen aan de opgegeven filters en marges.")
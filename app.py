
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("📦 Gruyaert Verpakkingsoptimalisatie Tool")

st.sidebar.header("🔧 Invoerparameters")

# PRODUCTGEGEVENS
product_ref = st.sidebar.text_input("Referentie product", value="PRD-001")
prod_l = st.sidebar.number_input("Lengte (mm)", min_value=1, value=100)
prod_b = st.sidebar.number_input("Breedte (mm)", min_value=1, value=80)
prod_h = st.sidebar.number_input("Hoogte (mm)", min_value=1, value=60)

# SPATIES
st.sidebar.markdown("### Marges in omverpakking (ruimte die moet blijven)")
marge_l = st.sidebar.number_input("Marge links/rechts (mm)", min_value=0, value=0)
marge_b = st.sidebar.number_input("Marge voor/achter (mm)", min_value=0, value=0)
marge_h = st.sidebar.number_input("Marge boven/onder (mm)", min_value=0, value=0)

# LIMITS
st.sidebar.markdown("### Maximumverdeling per omverpakking")
max_rijen = st.sidebar.slider("Max. rijen (L)", 1, 10, 10)
max_kolommen = st.sidebar.slider("Max. kolommen (B)", 1, 10, 10)
max_lagen = st.sidebar.slider("Max. lagen (H)", 1, 10, 10)

# PALLET
st.sidebar.markdown("### Pallethoogte instellingen")
pallet_hoogte = st.sidebar.number_input("Max. totale pallethoogte (mm)", min_value=100, value=1200)
pallet_hoogte_zonder_lading = st.sidebar.number_input("Hoogte lege pallet (mm)", min_value=0, value=150)

# CSV upload
st.sidebar.markdown("### 📥 Upload omverpakking CSV")
uploaded_file = st.sidebar.file_uploader("Omverpakking CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Probeer kolommen te herkennen ongeacht de naam
    def find_col(name):
        for col in df.columns:
            if name.lower() in col.lower():
                return col
        return None

    col_l = find_col("lengte")
    col_b = find_col("breedte")
    col_h = find_col("hoogte")
    col_id = find_col("id") or find_col("ref")

    if None in [col_l, col_b, col_h, col_id]:
        st.error("❌ Kan de juiste kolommen niet herkennen. Zorg dat je CSV lengte, breedte, hoogte en ID bevat.")
    else:
        results = []

        for idx, row in df.iterrows():
            in_l = row[col_l] - marge_l
            in_b = row[col_b] - marge_b
            in_h = row[col_h] - marge_h

            if in_l <= 0 or in_b <= 0 or in_h <= 0:
                continue

            fits_l = int(in_l // prod_l)
            fits_b = int(in_b // prod_b)
            fits_h = int(in_h // prod_h)

            fits_l = min(fits_l, max_rijen)
            fits_b = min(fits_b, max_kolommen)
            fits_h = min(fits_h, max_lagen)

            if fits_l * fits_b * fits_h == 0:
                continue

            total = fits_l * fits_b * fits_h
            eff = round((total * prod_l * prod_b * prod_h) / (row[col_l]*row[col_b]*row[col_h]) * 100, 2)

            results.append({
                "ID": row[col_id],
                "LxBxH": f"{row[col_l]}x{row[col_b]}x{row[col_h]}",
                "Per laag": fits_l * fits_b,
                "Lagen": fits_h,
                "Totaal stuks": total,
                "Volume-efficiëntie (%)": eff
            })

        if results:
            res_df = pd.DataFrame(results).sort_values("Volume-efficiëntie (%)", ascending=False)
            st.subheader(f"📊 Resultaten voor product **{product_ref}**")
            st.dataframe(res_df)

            # Visualisatie
            selected = st.selectbox("📦 Visualiseer omverpakking", res_df["ID"])
            box = res_df[res_df["ID"] == selected].iloc[0]
            st.info(f"Toon {box['Totaal stuks']} stuks verdeeld over {box['Lagen']} lagen in omverpakking {selected}")
        else:
            st.warning("⚠ Geen geldige configuraties gevonden met deze marges en afmetingen.")
else:
    st.info("⏳ Upload een CSV-bestand om te starten.")

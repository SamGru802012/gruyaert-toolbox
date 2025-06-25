
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ⬛️ Configuratie van de Streamlit-app: breed layout
st.set_page_config(layout="wide")
# 🧰 Titel van de applicatie
st.title("📦 Gruyaert Verpakkingsoptimalisatie Tool")


# ➕ Sidebar-instellingen voor gebruikersinvoer
st.sidebar.header("🔧 Invoerparameters")

# 🔤 Referentiecode van het product
product_ref = st.sidebar.text_input("Referentie product", value="PRD-001")
# 📏 Invoer productlengte
prod_l = st.sidebar.number_input("Lengte (mm)", min_value=1, value=100)
# 📐 Invoer productbreedte
prod_b = st.sidebar.number_input("Breedte (mm)", min_value=1, value=80)
# 🧱 Invoer producthoogte
prod_h = st.sidebar.number_input("Hoogte (mm)", min_value=1, value=60)


# ➖ Marges in omverpakking: minimale vrije ruimte
st.sidebar.markdown("### Marges in omverpakking (ruimte die moet blijven)")
# ➕ marge per zijde van de verpakking
marge_l = st.sidebar.number_input("Marge links/rechts (mm)", min_value=0, value=0)
# ➕ marge per zijde van de verpakking
marge_b = st.sidebar.number_input("Marge voor/achter (mm)", min_value=0, value=0)
# ➕ marge per zijde van de verpakking
marge_h = st.sidebar.number_input("Marge boven/onder (mm)", min_value=0, value=0)

st.sidebar.markdown("### Pallethoogte instellingen")
# 🟫 Max. hoogte van pallet inclusief lading
pallet_hoogte = st.sidebar.number_input("Max. totale pallethoogte (mm)", min_value=100, value=1200)
# 🧱 Invoer producthoogte
pallet_hoogte_zonder_lading = st.sidebar.number_input("Hoogte lege pallet (mm)", min_value=0, value=150)

st.sidebar.markdown("### 📥 Upload omverpakking CSV")
# 📁 Upload CSV met omverpakkingen
uploaded_file = st.sidebar.file_uploader("Omverpakking CSV", type=["csv"])


# 🧾 Verwerk het geüploade CSV-bestand
if uploaded_file:
    try:
# 📚 Lees CSV-bestand in als pandas DataFrame
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Kan bestand niet inladen: {e}")
        st.stop()

# 🔍 Flexibele kolomherkenning op basis van naam
    def find_col(name):
        for col in df.columns:
            if name.lower() in col.lower():
                return col
        return None

    col_l = find_col("lengte") or find_col("length")
    col_b = find_col("breedte") or find_col("width")
    col_h = find_col("hoogte") or find_col("height")
    col_id = find_col("id") or find_col("ref") or df.columns[0]

# ⚠️ Controle of alle vereiste kolommen aanwezig zijn
    if None in [col_l, col_b, col_h, col_id]:
        st.error("❌ CSV moet kolommen bevatten voor lengte, breedte, hoogte, ID.")
    else:
        results = []


# 🔁 Itereer over alle rijen in CSV voor berekeningen
        for idx, row in df.iterrows():
# ➖ Trek marges af van binnenafmetingen van de omdoos
            in_l = row[col_l] - marge_l
            in_b = row[col_b] - marge_b
            in_h = row[col_h] - marge_h

# ⚠️ Sla afmetingen over als ze ongeldig zijn na marge
            if in_l <= 0 or in_b <= 0 or in_h <= 0:
                continue

# 📦 Bereken aantal rijen, kolommen, lagen dat past
            r = int(in_l // prod_l)
            k = int(in_b // prod_b)
            z = int(in_h // prod_h)

            if r * k * z == 0:
                continue

# 🧮 Bereken totaal aantal stuks in deze configuratie
            totaal = r * k * z
# 📊 Volume-efficiëntie van de vulling in %
            eff = round((totaal * prod_l * prod_b * prod_h) / (row[col_l]*row[col_b]*row[col_h]) * 100, 2)
# 🟫 Max. hoogte van pallet inclusief lading
            totale_hoogte = pallet_hoogte_zonder_lading + z * prod_h
# 🟫 Max. hoogte van pallet inclusief lading
            if totale_hoogte > pallet_hoogte:
                continue

# ✅ Voeg geldige verpakkingsoptie toe aan de resultaten
            results.append({
                "OmverpakkingID": row[col_id],
                "Binnenafm. (LxBxH)": f"{row[col_l]}x{row[col_b]}x{row[col_h]}",
                "Rijen": r,
                "Kolommen": k,
                "Lagen": z,
                "Totaal stuks": totaal,
                "Pallethoogte (mm)": totale_hoogte,
                "Volume-efficiëntie (%)": eff
            })

        if results:
            df_result = pd.DataFrame(results).sort_values("Volume-efficiëntie (%)", ascending=False)
            st.subheader(f"📊 Resultaten voor product **{product_ref}**")
            st.dataframe(df_result, use_container_width=True)

            csv = df_result.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download resultaten als CSV", csv, f"resultaten_{product_ref}.csv", mime="text/csv")

            selected = st.selectbox("📦 Kies omverpakking voor visualisatie", df_result["OmverpakkingID"])
            sel = df_result[df_result["OmverpakkingID"] == selected].iloc[0]

            r, k, z = int(sel["Rijen"]), int(sel["Kolommen"]), int(sel["Lagen"])
            kleuren = ["#1f77b4", "#2ca02c", "#d62728", "#9467bd", "#ff7f0e", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]

            fig = go.Figure()
            for zi in range(z):
                for yi in range(k):
                    for xi in range(r):
                        x0, x1 = xi * prod_l, (xi + 1) * prod_l
                        y0, y1 = yi * prod_b, (yi + 1) * prod_b
                        z0, z1 = zi * prod_h, (zi + 1) * prod_h
                        kleur = kleuren[(zi + yi + xi) % len(kleuren)]
                        fig.add_trace(go.Mesh3d(
                            x=[x0,x1,x1,x0,x0,x1,x1,x0],
                            y=[y0,y0,y1,y1,y0,y0,y1,y1],
                            z=[z0,z0,z0,z0,z1,z1,z1,z1],
                            i=[0, 0, 0, 1, 1, 2],
                            j=[1, 2, 3, 2, 3, 3],
                            k=[2, 3, 1, 5, 7, 6],
                            opacity=0.5,
                            color=kleur,
                            showscale=False
                        ))
            fig.update_layout(scene=dict(
                xaxis_title="Lengte",
                yaxis_title="Breedte",
                zaxis_title="Hoogte",
                aspectmode="data"
            ), margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠ Geen geldige configuraties gevonden.")
else:
    st.info("⬅️ Upload een CSV-bestand om te starten.")
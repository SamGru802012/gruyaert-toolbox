
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("📦 Gruyaert Verpakkingsoptimalisatie")

# Invoer: Product
st.sidebar.header("🔧 Invoer parameters")
product_ref = st.sidebar.text_input("Product referentie", "PRD-001")
prod_l = st.sidebar.number_input("Lengte product (mm)", min_value=1, value=100)
prod_b = st.sidebar.number_input("Breedte product (mm)", min_value=1, value=80)
prod_h = st.sidebar.number_input("Hoogte product (mm)", min_value=1, value=60)

# Invoer: Marges
st.sidebar.markdown("### Marges in omverpakking")
marge_l = st.sidebar.number_input("Marge lengte (mm)", min_value=0, value=0)
marge_b = st.sidebar.number_input("Marge breedte (mm)", min_value=0, value=0)
marge_h = st.sidebar.number_input("Marge hoogte (mm)", min_value=0, value=0)

# Invoer: beperkingen
st.sidebar.markdown("### Verpakkingslimieten")
lim_r = st.sidebar.slider("Max. rijen", 1, 20, 10)
lim_k = st.sidebar.slider("Max. kolommen", 1, 20, 10)
lim_z = st.sidebar.slider("Max. lagen", 1, 20, 10)

# Invoer: Pallet
st.sidebar.markdown("### Pallethoogte instellingen")
pallet_max_h = st.sidebar.number_input("Max. pallethoogte (mm)", min_value=100, value=1200)
pallet_hoogte = st.sidebar.number_input("Hoogte lege pallet (mm)", min_value=0, value=150)

# Upload CSV
st.sidebar.markdown("### 📥 Upload CSV")
uploaded_file = st.sidebar.file_uploader("CSV met omverpakkingen", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Fout bij lezen CSV: {e}")
        st.stop()

    # Zoek kolommen automatisch
    def zoek_kolom(df, naam):
        for col in df.columns:
            if naam.lower() in col.lower():
                return col
        return None

    col_l = zoek_kolom(df, "lengte")
    col_b = zoek_kolom(df, "breedte")
    col_h = zoek_kolom(df, "hoogte")
    col_id = zoek_kolom(df, "id") or zoek_kolom(df, "ref") or df.columns[0]

    if None in [col_l, col_b, col_h, col_id]:
        st.error("CSV moet kolommen hebben voor lengte, breedte, hoogte en ID.")
        st.stop()

    resultaten = []
    for _, row in df.iterrows():
        in_l = row[col_l] - marge_l
        in_b = row[col_b] - marge_b
        in_h = row[col_h] - marge_h

        max_r = int(in_l // prod_l)
        max_k = int(in_b // prod_b)
        max_z = int(in_h // prod_h)

        r = min(max_r, lim_r)
        k = min(max_k, lim_k)
        z = min(max_z, lim_z)

        if r * k * z == 0:
            continue

        total = r * k * z
        eff = round((total * prod_l * prod_b * prod_h) / (row[col_l]*row[col_b]*row[col_h]) * 100, 2)
        totaal_hoogte = pallet_hoogte + z * prod_h
        if totaal_hoogte > pallet_max_h:
            continue

        resultaten.append({
            "Omverpakking": row[col_id],
            "Binnenafm. (LxBxH)": f"{row[col_l]}x{row[col_b]}x{row[col_h]}",
            "Rijen": r,
            "Kolommen": k,
            "Lagen": z,
            "Totaal stuks": total,
            "Pallethoogte (mm)": totaal_hoogte,
            "Volume-efficiëntie (%)": eff
        })

    if resultaten:
        df_res = pd.DataFrame(resultaten).sort_values("Volume-efficiëntie (%)", ascending=False)
        st.success(f"✅ {len(df_res)} geldige oplossingen gevonden")
        st.dataframe(df_res)

        csv = df_res.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download resultaten", csv, f"resultaten_{product_ref}.csv")

        keuze = st.selectbox("📦 Kies een omverpakking voor visualisatie", df_res["Omverpakking"])
        vis_row = df_res[df_res["Omverpakking"] == keuze].iloc[0]
        r, k, z = int(vis_row["Rijen"]), int(vis_row["Kolommen"]), int(vis_row["Lagen"])

        kleuren = ["#1f77b4", "#2ca02c", "#d62728", "#ff7f0e", "#9467bd", "#8c564b", "#17becf"]

        fig = go.Figure()
        for zi in range(z):
            for yi in range(k):
                for xi in range(r):
                    kleur = kleuren[(zi + yi + xi) % len(kleuren)]
                    x0, x1 = xi * prod_l, (xi + 1) * prod_l
                    y0, y1 = yi * prod_b, (yi + 1) * prod_b
                    z0, z1 = zi * prod_h, (zi + 1) * prod_h
                    fig.add_trace(go.Mesh3d(
                        x=[x0,x1,x1,x0,x0,x1,x1,x0],
                        y=[y0,y0,y1,y1,y0,y0,y1,y1],
                        z=[z0,z0,z0,z0,z1,z1,z1,z1],
                        i=[0,1,2,3,4,5,6,7],
                        j=[1,2,3,0,5,6,7,4],
                        k=[2,3,0,1,6,7,4,5],
                        color=kleur,
                        opacity=0.5,
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
        st.warning("⚠ Geen geldige combinaties gevonden.")
else:
    st.info("⬅️ Upload een CSV-bestand om te starten.")

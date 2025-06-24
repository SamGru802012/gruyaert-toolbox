
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("📦 Gruyaert Verpakkingsoptimalisatie")

# Invoer parameters
st.sidebar.header("🔧 Invoer parameters")
ref = st.sidebar.text_input("Productreferentie", "PRD-001")
prod_l = st.sidebar.number_input("Productlengte (mm)", min_value=1, value=100)
prod_b = st.sidebar.number_input("Productbreedte (mm)", min_value=1, value=80)
prod_h = st.sidebar.number_input("Producthoogte (mm)", min_value=1, value=60)

st.sidebar.markdown("### Marges in omverpakking")
marge_l = st.sidebar.number_input("Marge lengte", 0, 100, 0)
marge_b = st.sidebar.number_input("Marge breedte", 0, 100, 0)
marge_h = st.sidebar.number_input("Marge hoogte", 0, 100, 0)

wanddikte = st.sidebar.number_input("Dikte omverpakking (mm)", 0, 10, 3)

st.sidebar.markdown("### Beperkingen")
max_r = st.sidebar.slider("Max rijen", 1, 20, 10)
max_k = st.sidebar.slider("Max kolommen", 1, 20, 10)
max_z = st.sidebar.slider("Max lagen", 1, 20, 10)

st.sidebar.markdown("### Pallethoogte")
pallet_hoogte = st.sidebar.number_input("Hoogte lege pallet", 0, 500, 150)
pallet_max = st.sidebar.number_input("Max. totale hoogte (mm)", 500, 3000, 1200)

uploaded = st.sidebar.file_uploader("📥 Upload CSV met omverpakkingen", type="csv")

def detect_col(df, keyword):
    for col in df.columns:
        if keyword in col.lower():
            return col
    return None

if uploaded:
    df = pd.read_csv(uploaded)
    col_l = detect_col(df, "lengte")
    col_b = detect_col(df, "breedte")
    col_h = detect_col(df, "hoogte")
    col_id = detect_col(df, "id") or detect_col(df, "ref") or df.columns[0]

    if None in [col_l, col_b, col_h, col_id]:
        st.error("CSV moet kolommen bevatten met lengte, breedte, hoogte en referentie.")
        st.stop()

    resultaten = []
    for _, row in df.iterrows():
        in_l = row[col_l] - marge_l
        in_b = row[col_b] - marge_b
        in_h = row[col_h] - marge_h

        r = min(max_r, in_l // prod_l)
        k = min(max_k, in_b // prod_b)
        z = min(max_z, in_h // prod_h)

        if r * k * z == 0:
            continue

        totaal_hoogte = pallet_hoogte + z * prod_h
        if totaal_hoogte > pallet_max:
            continue

        total = int(r * k * z)
        eff = round((total * prod_l * prod_b * prod_h) / (row[col_l]*row[col_b]*row[col_h]) * 100, 2)

        resultaten.append({
            "Omverpakking": row[col_id],
            "Binnenafm.": f"{row[col_l]}x{row[col_b]}x{row[col_h]}",
            "Rijen": int(r),
            "Kolommen": int(k),
            "Lagen": int(z),
            "Totaal stuks": total,
            "Pallethoogte": totaal_hoogte,
            "Efficiëntie (%)": eff
        })

    if not resultaten:
        st.warning("⚠ Geen geldige combinaties gevonden.")
        st.stop()

    df_res = pd.DataFrame(resultaten).sort_values("Efficiëntie (%)", ascending=False)
    st.success(f"{len(df_res)} geldige combinaties")
    st.dataframe(df_res)

    csv = df_res.to_csv(index=False).encode("utf-8")
    st.download_button("📤 Download resultaten", csv, f"verpakking_{ref}.csv")

    keuze = st.selectbox("📦 Kies voor 3D-visualisatie", df_res["Omverpakking"])
    vis = df_res[df_res["Omverpakking"] == keuze].iloc[0]
    r, k, z = vis["Rijen"], vis["Kolommen"], vis["Lagen"]

    fig = go.Figure()

    kleuren = ["#1f77b4", "#2ca02c", "#d62728", "#ff7f0e", "#9467bd"]
    for zi in range(z):
        for yi in range(k):
            for xi in range(r):
                kleur = kleuren[(xi + yi + zi) % len(kleuren)]
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
                    opacity=0.5,
                    color=kleur,
                    showscale=False
                ))

    box_l = r * prod_l + marge_l
    box_b = k * prod_b + marge_b
    box_h = z * prod_h + marge_h
    outer_l = box_l + 2 * wanddikte
    outer_b = box_b + 2 * wanddikte
    outer_h = box_h + 2 * wanddikte

    
# Teken randen van de omverpakking (buitenafmetingen)
edges = [
    [(0, 0, 0), (outer_l, 0, 0)],
    [(0, 0, 0), (0, outer_b, 0)],
    [(0, 0, 0), (0, 0, outer_h)],
    [(outer_l, outer_b, 0), (0, outer_b, 0)],
    [(outer_l, outer_b, 0), (outer_l, 0, 0)],
    [(outer_l, outer_b, 0), (outer_l, outer_b, outer_h)],
    [(0, outer_b, outer_h), (outer_l, outer_b, outer_h)],
    [(0, outer_b, outer_h), (0, 0, outer_h)],
    [(0, outer_b, outer_h), (0, outer_b, 0)],
    [(outer_l, 0, outer_h), (outer_l, outer_b, outer_h)],
    [(outer_l, 0, outer_h), (0, 0, outer_h)],
    [(outer_l, 0, outer_h), (outer_l, 0, 0)],
]
for e in edges:
    fig.add_trace(go.Scatter3d(
        x=[e[0][0], e[1][0]],
        y=[e[0][1], e[1][1]],
        z=[e[0][2], e[1][2]],
        mode='lines',
        line=dict(color='black', width=4),
        showlegend=False
    ))


    fig.update_layout(scene=dict(
        xaxis_title="L",
        yaxis_title="B",
        zaxis_title="H",
        aspectmode="data"
    ), margin=dict(l=0, r=0, t=0, b=0))

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("⬅️ Upload een CSV om te starten.")

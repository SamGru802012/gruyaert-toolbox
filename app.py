
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("📦 Gruyaert Verpakkingsoptimalisatie")

# Sidebar
st.sidebar.header("Productgegevens")
ref = st.sidebar.text_input("Referentie", "PRD-001")
prod_l = st.sidebar.number_input("Lengte (mm)", 1, 2000, 100)
prod_b = st.sidebar.number_input("Breedte (mm)", 1, 2000, 80)
prod_h = st.sidebar.number_input("Hoogte (mm)", 1, 2000, 60)

st.sidebar.header("Marges & Doosinstellingen")
marge_l = st.sidebar.number_input("Marge lengte", 0, 500, 0)
marge_b = st.sidebar.number_input("Marge breedte", 0, 500, 0)
marge_h = st.sidebar.number_input("Marge hoogte", 0, 500, 0)
wanddikte = st.sidebar.number_input("Dikte wand omverpakking (mm)", 0, 20, 3)

st.sidebar.header("Beperkingen")
max_r = st.sidebar.slider("Max rijen", 1, 20, 10)
max_k = st.sidebar.slider("Max kolommen", 1, 20, 10)
max_z = st.sidebar.slider("Max lagen", 1, 20, 10)
pallet_hoogte = st.sidebar.number_input("Hoogte lege pallet (mm)", 0, 500, 150)
pallet_max = st.sidebar.number_input("Max totale hoogte (mm)", 500, 3000, 1200)

mode = st.radio("📁 Data-invoer:", ["Interactieve invoer", "CSV upload"], horizontal=True)

if mode == "CSV upload":
    uploaded = st.file_uploader("Upload CSV", type="csv")
    if uploaded:
        df = pd.read_csv(uploaded)
    else:
        st.stop()
else:
    st.markdown("### 📦 Omverpakkingen")
    if "dozen" not in st.session_state:
        st.session_state["dozen"] = pd.DataFrame(columns=["ID", "Lengte", "Breedte", "Hoogte"])
    with st.expander("➕ Toevoegen"):
        with st.form("toevoegen_form"):
            oid = st.text_input("ID")
            ol = st.number_input("Lengte", 1, 2000)
            ob = st.number_input("Breedte", 1, 2000)
            oh = st.number_input("Hoogte", 1, 2000)
            add = st.form_submit_button("Toevoegen")
            if add:
                st.session_state["dozen"] = pd.concat([st.session_state["dozen"], pd.DataFrame([{
                    "ID": oid, "Lengte": ol, "Breedte": ob, "Hoogte": oh
                }])], ignore_index=True)
    df = st.session_state["dozen"]
    st.dataframe(df)

# Detect kolommen
def detect(df, name):
    for col in df.columns:
        if name in col.lower():
            return col
    return None

col_l = detect(df, "lengte")
col_b = detect(df, "breedte")
col_h = detect(df, "hoogte")
col_id = detect(df, "id") or df.columns[0]

if None in [col_l, col_b, col_h, col_id]:
    st.error("Kolommen niet gevonden.")
    st.stop()

resultaten = []
for _, row in df.iterrows():
    in_l = row[col_l] - marge_l
    in_b = row[col_b] - marge_b
    in_h = row[col_h] - marge_h

    max_rl = in_l // prod_l
    max_kl = in_b // prod_b
    max_zl = in_h // prod_h

    best = (0, 0, 0)
    best_count = 0

    for r in range(1, max_rl+1):
        if r > max_r: continue
        for k in range(1, max_kl+1):
            if k > max_k: continue
            for z in range(1, max_zl+1):
                if z > max_z: continue
                total = r * k * z
                if total > best_count:
                    if pallet_hoogte + z * prod_h <= pallet_max:
                        best = (r, k, z)
                        best_count = total

    r, k, z = best
    if best_count == 0:
        continue

    eff = round((best_count * prod_l * prod_b * prod_h) / (row[col_l]*row[col_b]*row[col_h]) * 100, 2)
    resultaten.append({
        "Omverpakking": row[col_id],
        "Rijen": r, "Kolommen": k, "Lagen": z,
        "Totaal stuks": best_count,
        "Pallethoogte": pallet_hoogte + z * prod_h,
        "Efficiëntie (%)": eff
    })

if not resultaten:
    st.warning("⚠ Geen geldige combinaties.")
    st.stop()

df_res = pd.DataFrame(resultaten).sort_values("Efficiëntie (%)", ascending=False)
st.success(f"{len(df_res)} geldige combinaties")
st.dataframe(df_res)

keuze = st.selectbox("Visualiseer omverpakking", df_res["Omverpakking"])
vis = df_res[df_res["Omverpakking"] == keuze].iloc[0]
r, k, z = vis["Rijen"], vis["Kolommen"], vis["Lagen"]

fig = go.Figure()
kleuren = ["#1f77b4", "#2ca02c", "#d62728", "#ff7f0e"]
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
                color=kleur
            ))

fig.update_layout(scene=dict(
    xaxis_title="Lengte",
    yaxis_title="Breedte",
    zaxis_title="Hoogte",
    aspectmode="data"
), margin=dict(l=0, r=0, t=0, b=0))

st.plotly_chart(fig, use_container_width=True)

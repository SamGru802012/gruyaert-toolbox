
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("📦 Gruyaert Verpakkingsoptimalisatie")

# Sidebar: Productinstellingen
st.sidebar.header("🔧 Product")
ref = st.sidebar.text_input("Referentie", "PRD-001")
prod_l = st.sidebar.number_input("Lengte (mm)", 1, 2000, 100)
prod_b = st.sidebar.number_input("Breedte (mm)", 1, 2000, 80)
prod_h = st.sidebar.number_input("Hoogte (mm)", 1, 2000, 60)

# Sidebar: Marges
st.sidebar.markdown("### 📏 Marges (afgetrokken van binnenruimte)")
marge_l = st.sidebar.number_input("Marge lengte", 0, 500, 0)
marge_b = st.sidebar.number_input("Marge breedte", 0, 500, 0)
marge_h = st.sidebar.number_input("Marge hoogte", 0, 500, 0)

wanddikte = st.sidebar.number_input("Dikte wand omverpakking (mm)", 0, 20, 3)

# Sidebar: Beperkingen
st.sidebar.markdown("### ⚙️ Beperkingen")
max_r = st.sidebar.slider("Max rijen", 1, 20, 10)
max_k = st.sidebar.slider("Max kolommen", 1, 20, 10)
max_z = st.sidebar.slider("Max lagen", 1, 20, 10)

st.sidebar.markdown("### 🏗️ Pallet")
pallet_hoogte = st.sidebar.number_input("Hoogte lege pallet (mm)", 0, 500, 150)
pallet_max = st.sidebar.number_input("Max totale hoogte (mm)", 500, 3000, 1200)

# Mode: database in app of CSV
mode = st.radio("📁 Omverpakkingdata via:", ["Interactieve tabel", "Upload CSV"], horizontal=True)

if mode == "Upload CSV":
    uploaded = st.file_uploader("Upload omverpakking-CSV", type="csv")
    if uploaded:
        df = pd.read_csv(uploaded)
    else:
        st.stop()
else:
    st.markdown("### 📦 Omverpakkingen (interactief)")
    if "omdozen" not in st.session_state:
        st.session_state.omdozen = pd.DataFrame(columns=["ID", "Lengte", "Breedte", "Hoogte"])

    # Voeg record toe
    with st.expander("➕ Voeg nieuwe omdoos toe"):
        with st.form("add_form"):
            oid = st.text_input("ID", key="oid")
            ol = st.number_input("Lengte", 1, 2000, key="ol")
            ob = st.number_input("Breedte", 1, 2000, key="ob")
            oh = st.number_input("Hoogte", 1, 2000, key="oh")
            submitted = st.form_submit_button("Toevoegen")
            if submitted and oid:
                new_row = {"ID": oid, "Lengte": ol, "Breedte": ob, "Hoogte": oh}
                st.session_state.omdozen = pd.concat([st.session_state.omdozen, pd.DataFrame([new_row])], ignore_index=True)

    # Toon + delete
    del_idx = st.number_input("Verwijder rij-index", 0, max(0, len(st.session_state.omdozen)-1), step=1)
    if st.button("Verwijder geselecteerde rij"):
        st.session_state.omdozen.drop(index=del_idx, inplace=True)
        st.session_state.omdozen.reset_index(drop=True, inplace=True)

    df = st.session_state.omdozen
    st.dataframe(df)

# Detecteer kolommen
def detect_col(df, keyword):
    for col in df.columns:
        if keyword in col.lower():
            return col
    return None

col_l = detect_col(df, "lengte")
col_b = detect_col(df, "breedte")
col_h = detect_col(df, "hoogte")
col_id = detect_col(df, "id") or detect_col(df, "ref") or df.columns[0]

if None in [col_l, col_b, col_h, col_id]:
    st.error("Kan vereiste kolommen niet detecteren.")
    st.stop()

# Berekening
resultaten = []
for _, row in df.iterrows():

    in_l = row[col_l] - marge_l
    in_b = row[col_b] - marge_b
    in_h = row[col_h] - marge_h

    r = in_l // prod_l if max_r > 0 else 0
    k = in_b // prod_b if max_k > 0 else 0
    z = in_h // prod_h if max_z > 0 else 0

if r > max_r:
    r = 0
if k > max_k:
    k = 0
if z > max_z:
    z = 0



max_possible_r = in_l // prod_l
max_possible_k = in_b // prod_b
max_possible_z = in_h // prod_h

r_values = range(1, max_possible_r+1) if max_r > 0 else [0]
k_values = range(1, max_possible_k+1) if max_k > 0 else [0]
z_values = range(1, max_possible_z+1) if max_z > 0 else [0]

best_config = None
best_count = 0

for r in r_values:
    if r > max_r: continue
    for k in k_values:
        if k > max_k: continue
        for z in z_values:
            if z > max_z: continue
            total = r * k * z
            if total > best_count:
                pallet_h = pallet_hoogte + z * prod_h
                if pallet_h <= pallet_max:
                    best_count = total
                    best_config = (r, k, z)
if not best_config:
    continue

r, k, z = best_config
totaal_hoogte = pallet_hoogte + z * prod_h
eff = round((best_count * prod_l * prod_b * prod_h) / (row[col_l]*row[col_b]*row[col_h]) * 100, 2)
    if r * k * z == 0:
        continue

    totaal_hoogte = pallet_hoogte + z * prod_h
    if totaal_hoogte > pallet_max:
        continue

    total = int(r * k * z)
    eff = round((total * prod_l * prod_b * prod_h) / (row[col_l]*row[col_b]*row[col_h]) * 100, 2)

    resultaten.append({
        "Omverpakking": row[col_id],
        "Rijen": int(r),
        "Kolommen": int(k),
        "Lagen": int(z),
        "Totaal stuks": total,
        "Pallethoogte": totaal_hoogte,
        "Efficiëntie (%)": eff
    })

if not resultaten:
    st.warning("⚠ Geen geldige combinaties.")
    st.stop()

df_res = pd.DataFrame(resultaten).sort_values("Efficiëntie (%)", ascending=False)
st.success(f"{len(df_res)} geldige combinaties")
st.dataframe(df_res)

# Visualisatie
keuze = st.selectbox("📦 Visualisatie van omverpakking", df_res["Omverpakking"])
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

# Teken omdoos als wireframe
box_l = r * prod_l + marge_l
box_b = k * prod_b + marge_b
box_h = z * prod_h + marge_h
outer_l = box_l + 2 * wanddikte
outer_b = box_b + 2 * wanddikte
outer_h = box_h + 2 * wanddikte

edges = [
    [(0,0,0),(outer_l,0,0)],[(0,0,0),(0,outer_b,0)],[(0,0,0),(0,0,outer_h)],
    [(outer_l,outer_b,0),(0,outer_b,0)],[(outer_l,outer_b,0),(outer_l,0,0)],
    [(outer_l,outer_b,0),(outer_l,outer_b,outer_h)],[(0,outer_b,outer_h),(outer_l,outer_b,outer_h)],
    [(0,outer_b,outer_h),(0,0,outer_h)],[(0,outer_b,outer_h),(0,outer_b,0)],
    [(outer_l,0,outer_h),(outer_l,outer_b,outer_h)],[(outer_l,0,outer_h),(0,0,outer_h)],
    [(outer_l,0,outer_h),(outer_l,0,0)]
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
    xaxis_title="Lengte",
    yaxis_title="Breedte",
    zaxis_title="Hoogte",
    aspectmode="data"
), margin=dict(l=0, r=0, t=0, b=0))

st.plotly_chart(fig, use_container_width=True)

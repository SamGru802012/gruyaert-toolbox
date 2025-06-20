
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Gruyaert Toolbox", layout="wide")
st.title("📦 Gruyaert Verpakking Optimalisatie")

uploaded_file = st.file_uploader("Upload een CSV met omverpakkingen", type=["csv"])
if not uploaded_file:
    st.stop()

try:
    df_raw = pd.read_csv(uploaded_file)
    st.success("✅ Bestand geladen")
except Exception as e:
    st.error(f"Fout bij laden CSV: {e}")
    st.stop()

# Tabs
tab1, tab2, tab3 = st.tabs(["📐 Verpakking", "⚠️ Uitsluitingen", "📤 Export"])

with tab1:
    st.subheader("🔢 Productafmetingen (mm)")
    pl = st.number_input("Lengte", min_value=1, value=200)
    pb = st.number_input("Breedte", min_value=1, value=150)
    ph = st.number_input("Hoogte", min_value=1, value=100)

    st.subheader("➕ Spatieverlies (aftrek van omdoos)")
    sl = st.number_input("Spatie lengte", min_value=0, value=0)
    sb = st.number_input("Spatie breedte", min_value=0, value=20)
    sh = st.number_input("Spatie hoogte", min_value=0, value=0)

    st.subheader("📏 Palletinstellingen")
    pallet_height_base = st.number_input("Hoogte lege pallet", value=150)
    pallet_height_max = st.number_input("Max. pallethoogte incl. goederen", value=1800)

    resultaten = []
    uitsluitingen = []

    if st.button("🔍 Zoek optimale omverpakkingen"):
        df = df_raw.copy()
        orientations = [(pl, pb, ph), (pl, ph, pb), (pb, pl, ph), (pb, ph, pl), (ph, pl, pb), (ph, pb, pl)]

        for idx, row in df.iterrows():
            box_id = row.get("DoosID", row.get("OmverpakkingsID", f"DOOS-{idx+1}"))
            usable_l = row["Lengte_mm"] - sl
            usable_b = row["Breedte_mm"] - sb
            usable_h = row["Hoogte_mm"] - sh

            best = {}
            for l, b, h in orientations:
                r = int(usable_l // l)
                k = int(usable_b // b)
                z = int(usable_h // h)
                aantal = r * k * z
                hoogte = z * h + pallet_height_base

                if aantal == 0:
                    uitsluitingen.append({"ID": box_id, "Reden": "Aantal = 0"})
                    continue
                if hoogte > pallet_height_max:
                    uitsluitingen.append({"ID": box_id, "Reden": f"Pallet te hoog ({hoogte})"})
                    continue

                score = aantal
                if "score" not in best or score > best["score"]:
                    best = {
                        "OmverpakkingsID": box_id,
                        "Config": f"{l}×{b}×{h}",
                        "Rijen": r,
                        "Kolommen": k,
                        "Lagen": z,
                        "Aantal": aantal,
                        "Hoogte (mm)": hoogte,
                        "Score": score
                    }

            if best:
                resultaten.append(best)

        if resultaten:
            df_result = pd.DataFrame(resultaten).sort_values("Score", ascending=False)
            st.success(f"{len(df_result)} resultaten gevonden.")
            st.dataframe(df_result)

            csv = df_result.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download resultaten als CSV", data=csv, file_name="verpakkingsresultaten.csv", mime="text/csv")

            st.subheader("📊 Visualisatie")
            selected = st.selectbox("Kies een omverpakking", df_result["OmverpakkingsID"])
            sel = df_result[df_result["OmverpakkingsID"] == selected].iloc[0]
            r, k, z = sel["Rijen"], sel["Kolommen"], sel["Lagen"]
            l, b, h = map(float, sel["Config"].split("×"))

            fig = go.Figure()
            for zi in range(z):
                for yi in range(k):
                    for xi in range(r):
                        fig.add_trace(go.Mesh3d(
                            x=[xi*l, xi*l, (xi+1)*l, (xi+1)*l, xi*l, xi*l, (xi+1)*l, (xi+1)*l],
                            y=[yi*b, (yi+1)*b, (yi+1)*b, yi*b, yi*b, (yi+1)*b, (yi+1)*b, yi*b],
                            z=[zi*h]*4 + [(zi+1)*h]*4,
                            color='lightblue', opacity=0.5, showscale=False
                        ))
            fig.update_layout(scene=dict(xaxis_title='L', yaxis_title='B', zaxis_title='H'), margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig)
        else:
            st.warning("⚠ Geen geldige configuraties gevonden.")

with tab2:
    st.subheader("🛑 Uitsluitingen")
    if uitsluitingen:
        df_uitsluit = pd.DataFrame(uitsluitingen)
        st.dataframe(df_uitsluit)
        st.download_button("📤 Download uitsluitingen", df_uitsluit.to_csv(index=False).encode("utf-8"), file_name="uitsluitingen.csv", mime="text/csv")
    else:
        st.info("Geen uitsluitingen vastgesteld.")

with tab3:
    st.markdown("👉 Resultaten en uitsluitingen worden pas zichtbaar na verwerking in tabblad 1.")

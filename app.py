
import streamlit as st
import pandas as pd
import numpy as np

st.title("📦 Verpakking Optimalisatie AI Agent")

if "reset" not in st.session_state:
    st.session_state.reset = False

def do_reset():
    st.session_state.reset = True

st.sidebar.header("Stap 1: Upload je stockbestand")
stock_file = st.sidebar.file_uploader("Upload een Excel- of CSV-bestand met omverpakkingstock", type=["csv", "xlsx"])

st.sidebar.header("Stap 2: Geef afmetingen van productdoos in (mm)")
prod_l = st.sidebar.number_input("Lengte", min_value=1, key="prod_l")
prod_b = st.sidebar.number_input("Breedte", min_value=1, key="prod_b")
prod_h = st.sidebar.number_input("Hoogte", min_value=1, key="prod_h")

st.sidebar.header("Stap 3: Interne verliesruimte per richting (mm)")
extra_l = st.sidebar.number_input("Verlies in lengte (doos L - X)", min_value=0, value=0, key="extra_l")
extra_b = st.sidebar.number_input("Verlies in breedte (doos B - X)", min_value=0, value=0, key="extra_b")
extra_h = st.sidebar.number_input("Verlies in hoogte (doos H - X)", min_value=0, value=0, key="extra_h")

st.sidebar.header("Stap 4: Palletinstellingen")
pallet_l = st.sidebar.number_input("Pallet lengte (mm)", value=1200, key="pallet_l")
pallet_b = st.sidebar.number_input("Pallet breedte (mm)", value=800, key="pallet_b")
pallet_h = st.sidebar.number_input("Max. pallet hoogte (mm)", value=1800, key="pallet_h")
pallet_tol = st.sidebar.number_input("Max. extra tolerantie (mm)", value=100, key="pallet_tol")

st.sidebar.header("Stap 5: Aantallenlimieten")
min_per_box = st.sidebar.number_input("Min. aantal per omverpakking", value=1, min_value=0, key="min_per_box")
max_per_box = st.sidebar.number_input("Max. aantal per omverpakking", value=9999, min_value=1, key="max_per_box")

st.sidebar.header("Stap 6: Filters")
min_stock = st.sidebar.number_input("Minimale beschikbare stock", value=1, min_value=0, key="min_stock")
max_leegte = st.sidebar.slider("Max. toegelaten lege ruimte (%)", 0, 100, 40, key="max_leegte")
top_x = st.sidebar.slider("Toon enkel top resultaten (aantal)", 1, 50, 10, key="top_x")

st.sidebar.markdown("---")
st.sidebar.button("🔄 Reset filters", on_click=do_reset)

if st.session_state.reset:
    st.warning("↩ Herstart de app handmatig om alle filters te resetten.")
    st.stop()

if stock_file and prod_l > 0 and prod_b > 0 and prod_h > 0:
    if stock_file.name.endswith(".csv"):
        df = pd.read_csv(stock_file)
    else:
        df = pd.read_excel(stock_file)

    required_cols = {"OmverpakkingsID", "Lengte_mm", "Breedte_mm", "Hoogte_mm", "Beschikbare_Stock"}
    if not required_cols.issubset(df.columns):
        st.error("Bestand mist vereiste kolommen: " + ", ".join(required_cols))
    else:
        orientations = [
            (prod_l, prod_b, prod_h),
            (prod_l, prod_h, prod_b),
            (prod_b, prod_l, prod_h),
            (prod_b, prod_h, prod_l),
            (prod_h, prod_l, prod_b),
            (prod_h, prod_b, prod_l)
        ]

        resultaten = []

        for idx, row in df.iterrows():
            if row["Beschikbare_Stock"] < min_stock:
                continue

            best = {"score": 0}
            usable_l = row["Lengte_mm"] - extra_l
            usable_b = row["Breedte_mm"] - extra_b
            usable_h = row["Hoogte_mm"] - extra_h

            if usable_l <= 0 or usable_b <= 0 or usable_h <= 0:
                continue

            for o in orientations:
                l, b, h = o
                per_laag = int(usable_l // l) * int(usable_b // b)
                lagen = int(usable_h // h)
                totaal = per_laag * lagen

                if totaal < min_per_box or totaal > max_per_box or totaal == 0:
                    continue

                vol_product = totaal * l * b * h
                vol_omv = row["Lengte_mm"] * row["Breedte_mm"] * row["Hoogte_mm"]
                leegte = 1 - (vol_product / vol_omv) if vol_omv > 0 else 1
                if leegte * 100 > max_leegte:
                    continue

                pallet_per_laag = int(pallet_l // row["Lengte_mm"]) * int(pallet_b // row["Breedte_mm"])
                pallet_lagen = int((pallet_h + pallet_tol) // row["Hoogte_mm"])
                totaal_pallet = pallet_per_laag * pallet_lagen * totaal

                score = totaal * (1 - leegte)
                if score > best["score"]:
                    best = {
                        "OmverpakkingsID": row["OmverpakkingsID"],
                        "Afmetingen": f"{row['Lengte_mm']}x{row['Breedte_mm']}x{row['Hoogte_mm']}",
                        "Gebruik": f"{usable_l}x{usable_b}x{usable_h}",
                        "Oriëntatie": f"{l}x{b}x{h}",
                        "Aantal per Omverpakking": totaal,
                        "Totale Producten per Pallet": totaal_pallet,
                        "Lege Ruimte (%)": f"{leegte*100:.1f}%",
                        "Beschikbare Stock": row["Beschikbare_Stock"],
                        "Score": round(score, 2)
                    }

            if best["score"] > 0:
                resultaten.append(best)

        if resultaten:
            df_result = pd.DataFrame(resultaten)
            df_result = df_result.sort_values(by="Score", ascending=False).reset_index(drop=True)
            df_top = df_result.head(top_x)
            st.success(f"✅ {len(df_top)} beste verpakkingsopties gevonden.")
            st.dataframe(df_top)

            csv = df_top.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download resultaten als CSV", csv, "verpakkingsopties.csv", "text/csv")
        else:
            st.warning("⚠ Geen resultaten voldoen aan de opgegeven filters en marges.")
else:
    st.info("📄 Upload eerst een bestand en geef de doosafmetingen in om te starten.")

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gruyaert Verpakkingstool", layout="centered")

st.title("📦 Gruyaert Verpakking Optimalisatie")

uploaded_file = st.file_uploader("Upload een CSV met omverpakkingen", type=["csv"])
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.success("✅ Bestand succesvol geladen!")
        st.dataframe(df)
    except Exception as e:
        st.error(f"Fout bij inlezen bestand: {e}")
else:
    st.info("📄 Upload een bestand om te starten.")

st.markdown("---")
st.caption("Toolbox ontwikkeld voor interne verpakkingstools bij Gruyaert.")
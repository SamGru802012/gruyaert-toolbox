
import streamlit as st
import pandas as pd
import numpy as np
from itertools import permutations
from io import BytesIO
import plotly.graph_objects as go

st.set_page_config(page_title="Pallet Optimalisatie Tool", layout="wide")
st.title("🧰 Pallet Optimalisatie Tool")

st.sidebar.header("📦 Productinformatie")
product_length = st.sidebar.number_input("Product lengte (mm)", min_value=1)
product_width = st.sidebar.number_input("Product breedte (mm)", min_value=1)
product_height = st.sidebar.number_input("Product hoogte (mm)", min_value=1)

st.sidebar.header("📏 Spaties in Doos")
space_l = st.sidebar.number_input("Extra spatie lengte (mm)", min_value=0, value=0)
space_w = st.sidebar.number_input("Extra spatie breedte (mm)", min_value=0, value=0)
space_h = st.sidebar.number_input("Extra spatie hoogte (mm)", min_value=0, value=0)

st.sidebar.header("🚛 Palletinstellingen")
pallet_l = st.sidebar.number_input("Pallet lengte (mm)", value=1200, min_value=100)
pallet_w = st.sidebar.number_input("Pallet breedte (mm)", value=800, min_value=100)
pallet_h = st.sidebar.number_input("Maximale stapelhoogte pallet (mm)", value=1800, min_value=100)

uploaded_file = st.file_uploader("Upload CSV met dozenvoorraad (kolommen: DoosID, Lengte_mm, Breedte_mm, Hoogte_mm)", type=["csv"])

def draw_3d_box(box_dim, product_dim, fits, box_id):
    fig = go.Figure()
    fig.add_trace(go.Mesh3d(
        x=[0, box_dim[0], box_dim[0], 0, 0, box_dim[0], box_dim[0], 0],
        y=[0, 0, box_dim[1], box_dim[1], 0, 0, box_dim[1], box_dim[1]],
        z=[0, 0, 0, 0, box_dim[2], box_dim[2], box_dim[2], box_dim[2]],
        opacity=0.2,
        color='lightblue',
        showscale=False
    ))
    for i in range(fits[0]):
        for j in range(fits[1]):
            for k in range(fits[2]):
                fig.add_trace(go.Mesh3d(
                    x=[0, product_dim[0], product_dim[0], 0, 0, product_dim[0], product_dim[0], 0] + i * [product_dim[0]],
                    y=[0, 0, product_dim[1], product_dim[1], 0, 0, product_dim[1], product_dim[1]] + j * [product_dim[1]],
                    z=[0, 0, 0, 0, product_dim[2], product_dim[2], product_dim[2], product_dim[2]] + k * [product_dim[2]],
                    color='darkorange',
                    opacity=1.0,
                    showscale=False
                ))
    fig.update_layout(
        scene=dict(
            xaxis_title='Lengte (mm)',
            yaxis_title='Breedte (mm)',
            zaxis_title='Hoogte (mm)'
        ),
        title=f"3D weergave: Product in Doos ({box_id})",
        margin=dict(l=0, r=0, b=0, t=40),
        scene_camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
    )
    
    # Voeg labels toe voor de eerste N dozen
    fig.add_trace(go.Scatter3d(
        x=[(i * box_dim[0]) + box_dim[0]/2 for i in range(min(5, pallet_dim[0] // box_dim[0]))],
        y=[box_dim[1]/2]*min(5, pallet_dim[0] // box_dim[0]),
        z=[box_dim[2]*layers + 20]*min(5, pallet_dim[0] // box_dim[0]),
        mode='text',
        text=[f'Doos {i+1}' for i in range(min(5, pallet_dim[0] // box_dim[0]))],
        textposition='top center'
    ))
    return fig
    


def draw_3d_pallet(box_dim, pallet_dim, boxes_per_layer, layers):
    fig = go.Figure()
    count = 0
    for layer in range(layers):
        for i in range(pallet_dim[0] // box_dim[0]):
            for j in range(pallet_dim[1] // box_dim[1]):
                x_shift = i * box_dim[0]
                y_shift = j * box_dim[1]
                z_shift = layer * box_dim[2]
                fig.add_trace(go.Mesh3d(
                    x=[coord + x_shift for coord in [0, box_dim[0], box_dim[0], 0, 0, box_dim[0], box_dim[0], 0]],
                    y=[coord + y_shift for coord in [0, 0, box_dim[1], box_dim[1], 0, 0, box_dim[1], box_dim[1]]],
                    z=[coord + z_shift for coord in [0, 0, 0, 0, box_dim[2], box_dim[2], box_dim[2], box_dim[2]]],
                    color='lightblue',
                    opacity=0.6,
                    showscale=False
                ))
                count += 1
                if count >= boxes_per_layer * layers:
                    break
    fig.update_layout(
        scene=dict(
            xaxis_title='Lengte (mm)',
            yaxis_title='Breedte (mm)',
            zaxis_title='Hoogte (mm)'
        ),
        title="3D weergave: Dozen op Pallet",
        margin=dict(l=0, r=0, b=0, t=40),
        scene_camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
    )
    
    # Voeg labels toe voor de eerste N dozen
    fig.add_trace(go.Scatter3d(
        x=[(i * box_dim[0]) + box_dim[0]/2 for i in range(min(5, pallet_dim[0] // box_dim[0]))],
        y=[box_dim[1]/2]*min(5, pallet_dim[0] // box_dim[0]),
        z=[box_dim[2]*layers + 20]*min(5, pallet_dim[0] // box_dim[0]),
        mode='text',
        text=[f'Doos {i+1}' for i in range(min(5, pallet_dim[0] // box_dim[0]))],
        textposition='top center'
    ))
    return fig
    
if uploaded_file:
    boxes_df = pd.read_csv(uploaded_file)
    results = []

    product_dims = [product_length, product_width, product_height]

    for idx, row in boxes_df.iterrows():
        box_id = row["DoosID"]
        box_dims = [
            row["Lengte_mm"] - space_l,
            row["Breedte_mm"] - space_w,
            row["Hoogte_mm"] - space_h
        ]

        max_units = 0
        best_rotation = ()
        best_fits = ()

        for rotation in permutations(product_dims):
            fits_l = box_dims[0] // rotation[0]
            fits_w = box_dims[1] // rotation[1]
            fits_h = box_dims[2] // rotation[2]
            total = fits_l * fits_w * fits_h

            if total > max_units:
                max_units = total
                best_rotation = rotation
                best_fits = (fits_l, fits_w, fits_h)

        box_per_layer = (pallet_l // row["Lengte_mm"]) * (pallet_w // row["Breedte_mm"])
        max_layers = pallet_h // row["Hoogte_mm"]
        total_boxes_per_pallet = box_per_layer * max_layers
        total_products_per_pallet = total_boxes_per_pallet * max_units

        results.append({
            "DoosID": box_id,
            "Producten per doos": max_units,
            "Rotatie (LxBxH)": f"{best_rotation[0]}×{best_rotation[1]}×{best_rotation[2]}",
            "Dozen per laag": box_per_layer,
            "Lagen": max_layers,
            "Dozen per pallet": total_boxes_per_pallet,
            "Totale producten per pallet": total_products_per_pallet,
            "BoxDims": box_dims,
            "ProdDims": best_rotation,
            "Fits": best_fits,
            "OrigBoxDims": [row["Lengte_mm"], row["Breedte_mm"], row["Hoogte_mm"]]
        })

    results_df = pd.DataFrame(results)
    sorted_df = results_df.sort_values(by="Totale producten per pallet", ascending=False)

    st.subheader("🔝 Beste opties")

    top_n = st.slider("🔢 Aantal topopties om te tonen", min_value=1, max_value=len(sorted_df), value=10)
    display_df = sorted_df.head(top_n)
    st.data_editor(display_df.drop(columns=["BoxDims", "ProdDims", "Fits", "OrigBoxDims"]), use_container_width=True, num_rows="dynamic")
    top_result = display_df.iloc[0]

    st.dataframe(sorted_df.drop(columns=["BoxDims", "ProdDims", "Fits", "OrigBoxDims"]), use_container_width=True)

    top_result = sorted_df.iloc[0]
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(draw_3d_box(top_result.BoxDims, top_result.ProdDims, top_result.Fits, top_result.DoosID))
    with col2:
        st.plotly_chart(draw_3d_pallet(top_result.OrigBoxDims, [pallet_l, pallet_w, pallet_h], top_result["Dozen per laag"], top_result["Lagen"]))

    def convert_df(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.drop(columns=["BoxDims", "ProdDims", "Fits", "OrigBoxDims"]).to_excel(writer, index=False)
        return output.getvalue()

    excel_data = convert_df(sorted_df)
    
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from tempfile import NamedTemporaryFile
import plotly.io as pio

# PDF-export knop
if st.button("📄 Exporteer topresultaat naar PDF"):
    fig = draw_3d_pallet(top_result.OrigBoxDims, [pallet_l, pallet_w, pallet_h], top_result["Dozen per laag"], top_result["Lagen"])
    with NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
        pio.write_image(fig, tmp_img.name, format="png", width=800, height=600)
        image_path = tmp_img.name

    pdf_file = BytesIO()
    c = canvas.Canvas(pdf_file, pagesize=A4)
    c.setFont("Helvetica", 12)
    c.drawString(50, 800, f"Pallet Optimalisatie Rapport")
    c.drawString(50, 780, f"Top Doos ID: {top_result.DoosID}")
    c.drawString(50, 760, f"Producten per Doos: {top_result['Producten per doos']}")
    c.drawString(50, 740, f"Totale producten per pallet: {top_result['Totale producten per pallet']}")
    c.drawImage(image_path, 50, 400, width=500, height=300)
    c.save()
    pdf_file.seek(0)

    st.download_button("📥 Download PDF", data=pdf_file, file_name="pallet_rapport.pdf", mime="application/pdf")
from reportlab.pdfgen import canvas
from tempfile import NamedTemporaryFile

# PDF-export knop
if st.button("📄 Exporteer topresultaat naar PDF"):
    pdf_file = BytesIO()
    c = canvas.Canvas(pdf_file, pagesize=A4)
    c.setFont("Helvetica", 12)
    c.drawString(50, 800, f"Pallet Optimalisatie Rapport")
    c.drawString(50, 780, f"Top Doos ID: {top_result.DoosID}")
    c.drawString(50, 760, f"Producten per Doos: {top_result['Producten per doos']}")
    c.drawString(50, 740, f"Rotatie: {top_result['Rotatie (LxBxH)']}")
    c.drawString(50, 720, f"Totale producten per pallet: {top_result['Totale producten per pallet']}")
    c.drawString(50, 700, f"Dozen per laag: {top_result['Dozen per laag']}")
    c.drawString(50, 680, f"Lagen: {top_result['Lagen']}")
    c.save()
    pdf_file.seek(0)

    st.download_button("📥 Download PDF", data=pdf_file, file_name="pallet_rapport.pdf", mime="application/pdf")
from reportlab.pdfgen import canvas
from tempfile import NamedTemporaryFile
import plotly.io as pio

# PDF-export knop
if st.button("📄 Exporteer topresultaat naar PDF"):
    fig = draw_3d_pallet(top_result.OrigBoxDims, [pallet_l, pallet_w, pallet_h], top_result["Dozen per laag"], top_result["Lagen"])
    with NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
        pio.write_image(fig, tmp_img.name, format="png", width=800, height=600)
        image_path = tmp_img.name

    pdf_file = BytesIO()
    c = canvas.Canvas(pdf_file, pagesize=A4)
    c.setFont("Helvetica", 12)
    c.drawString(50, 800, f"Pallet Optimalisatie Rapport")
    c.drawString(50, 780, f"Top Doos ID: {top_result.DoosID}")
    c.drawString(50, 760, f"Producten per Doos: {top_result['Producten per doos']}")
    c.drawString(50, 740, f"Totale producten per pallet: {top_result['Totale producten per pallet']}")
    c.drawImage(image_path, 50, 400, width=500, height=300)
    c.save()
    pdf_file.seek(0)

    st.download_button("📥 Download PDF", data=pdf_file, file_name="pallet_rapport.pdf", mime="application/pdf")

st.download_button(
        label="💾 Download resultaten als Excel",
        data=excel_data,
        file_name='pallet_optimalisatie_resultaten.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
else:
    st.info("📂 Upload een CSV-bestand om te beginnen.")

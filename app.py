import streamlit as st
from docxtpl import DocxTemplate, InlineImage
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
from docx.shared import Mm
from fpdf import FPDF # Librería para el PDF

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Honorarios LS", page_icon="📝", layout="centered")

# --- FUNCIÓN PARA GENERAR PDF ---
def generar_pdf_oficial(ctx, pil_img):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "INFORME MENSUAL DE ACTIVIDADES", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 7, f"Nombre: {ctx['nombre']}", ln=True)
    pdf.cell(0, 7, f"Unidad: {ctx['direccion']}", ln=True)
    pdf.cell(0, 7, f"Mes: {ctx['mes']} {ctx['anio']}", ln=True)
    pdf.ln(5)
    # Tabla de actividades en PDF
    pdf.set_font("Arial", "B", 10)
    pdf.cell(95, 8, " Actividad", border=1)
    pdf.cell(95, 8, " Producto/Resultado", border=1, ln=True)
    pdf.set_font("Arial", "", 9)
    for act in ctx['actividades']:
        pdf.multi_cell(190, 6, f"{act['Actividad']} | {act['Producto']}", border=1)
    # Firma en PDF
    if pil_img:
        pdf.ln(10)
        img_buf = io.BytesIO()
        pil_img.save(img_buf, format="PNG")
        pdf.image(img_buf, x=75, w=50)
    return pdf.output()

# --- DATOS (Paso 1, 2 y 3 se mantienen igual a tu versión) ---
# ... (Aquí va tu código de inputs de nombre, dirección, mes y actividades) ...

# --- FIRMA (Paso 4) ---
st.subheader("✍️ Paso 4: Firma Digital")
canvas_result = st_canvas(stroke_width=2, stroke_color="black", background_color="white", height=150, width=400, drawing_mode="freedraw", key="canvas")

# --- PROCESAMIENTO ---
if st.button("🚀 GENERAR INFORME OFICIAL", type="primary", use_container_width=True):
    if canvas_result.image_data is not None:
        try:
            # CORRECCIÓN DE ERROR BINARIO: Convertir canvas a imagen PIL primero
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            bbox = img.getbbox()
            if bbox: img = img.crop(bbox) # Recortar bordes sobrantes
            
            # Preparar buffer para Word
            img_word = io.BytesIO()
            img.save(img_word, format='PNG')
            img_word.seek(0)

            context = {
                'nombre': nombre.upper(), 'direccion': direccion, 'depto': depto,
                'jornada': jornada, 'mes': mes.upper(), 'anio': anio,
                'monto': f"${monto_contrato:,.0f}",
                'monto_boleta': f"${monto_boleta:,.0f}",
                'boleta': n_boleta, 'actividades': st.session_state.actividades
            }

            # Generar Word
            doc = DocxTemplate("plantilla_base.docx")
            context['firma'] = InlineImage(doc, img_word, height=Mm(20))
            doc.render(context)
            word_buf = io.BytesIO()
            doc.save(word_buf)
            
            st.success("✅ ¡Informe procesado con éxito!")
            c1, c2 = st.columns(2)
            c1.download_button("📥 DESCARGAR WORD", word_buf.getvalue(), f"Informe_{mes}.docx")
            
            # Generar y descargar PDF
            pdf_bytes = generar_pdf_oficial(context, img)
            c2.download_button("📥 DESCARGAR PDF", pdf_bytes, f"Informe_{mes}.pdf")
            
        except Exception as e:
            st.error(f"Error técnico: {e}")

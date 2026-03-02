import streamlit as st
from docxtpl import DocxTemplate, InlineImage
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
from docx.shared import Mm
from fpdf import FPDF # Generador de PDF

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Honorarios LS", page_icon="📝", layout="centered")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>", unsafe_allow_html=True)

st.title("Generador de Informes 📝")
st.markdown("### Ilustre Municipalidad de La Serena")

# --- 1. DATOS DEL PRESTADOR ---
with st.expander("👤 Paso 1: Datos del Prestador", expanded=True):
    nombre = st.text_input("Nombre Completo Prestador", value="RODRIGO ALDRÍN GODOY ALFARO")
    col_a, col_b = st.columns(2)
    direccion = col_a.text_input("Dirección Municipal", "Dirección de Alcaldía")
    depto = col_b.text_input("Departamento / Sección", "Depto. Comunicaciones Estratégicas")
    jornada = st.selectbox("Tipo de Jornada", ["Libre", "Completa", "Flexible", "Media Jornada"])

# --- 2. FINANZAS Y PERIODO ---
with st.expander("💰 Paso 2: Contrato y Boleta", expanded=True):
    c1, c2 = st.columns(2)
    mes = c1.selectbox("Mes del Informe", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=1)
    anio = c2.number_input("Año", value=2026)
    st.markdown("---")
    monto_contrato = st.number_input("Monto Bruto según Contrato ($)", value=2000000)
    n_boleta = st.text_input("Nº Boleta Honorarios")
    
    # Cálculo 2026 (15.25% retención)
    monto_boleta = monto_contrato
    liquido = int(monto_boleta * 0.8475)
    st.success(f"Líquido estimado: ${liquido:,.0f}")

# --- 3. ACTIVIDADES ---
st.subheader("📋 Paso 3: Actividades Realizadas")
if 'actividades' not in st.session_state:
    st.session_state.actividades = [{"Actividad": "", "Producto": ""}]

def add(): st.session_state.actividades.append({"Actividad": "", "Producto": ""})
def rem(): 
    if len(st.session_state.actividades) > 1: st.session_state.actividades.pop()

for i, item in enumerate(st.session_state.actividades):
    ca, cp = st.columns(2)
    st.session_state.actividades[i]["Actividad"] = ca.text_area(f"Actividad {i+1}", value=item["Actividad"], key=f"a{i}")
    st.session_state.actividades[i]["Producto"] = cp.text_area(f"Resultado {i+1}", value=item["Producto"], key=f"p{i}")

st.button("➕ Agregar Fila", on_click=add)

# --- 4. FIRMA ---
st.subheader("✍️ Paso 4: Firma Digital")
canvas_result = st_canvas(stroke_width=2, stroke_color="black", background_color="white", height=150, width=400, drawing_mode="freedraw", key="canvas")

# --- FUNCIÓN PDF ---
def generar_pdf_oficial(ctx, pil_img):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "INFORME MENSUAL DE ACTIVIDADES", ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 7, f"Nombre: {ctx['nombre']}", ln=True)
    pdf.cell(0, 7, f"Unidad: {ctx['direccion']}", ln=True)
    pdf.cell(0, 7, f"Mes: {ctx['mes']} {ctx['anio']}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(95, 8, " Actividad", border=1)
    pdf.cell(95, 8, " Producto/Resultado", border=1, ln=True)
    pdf.set_font("Arial", "", 9)
    for act in ctx['actividades']:
        pdf.multi_cell(95, 6, act['Actividad'], border=1)
        y = pdf.get_y()
        pdf.set_y(y - 6)
        pdf.set_x(105)
        pdf.multi_cell(95, 6, act['Producto'], border=1)
    if pil_img:
        pdf.ln(10)
        img_buf = io.BytesIO()
        pil_img.save(img_buf, format="PNG")
        pdf.image(img_buf, x=75, w=50)
    return pdf.output()

# --- 5. GENERACIÓN ---
if st.button("🚀 GENERAR INFORME OFICIAL", type="primary", use_container_width=True):
    if canvas_result.image_data is not None:
        try:
            # FIX BINARIO: Convertir a imagen PIL antes de procesar
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            bbox = img.getbbox()
            if bbox: img = img.crop(bbox)
            
            # Preparar para Word
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
            
            st.success("✅ ¡Informe procesado!")
            c_d1, c_d2 = st.columns(2)
            c_d1.download_button("📥 WORD", word_buf.getvalue(), f"Informe_{mes}.docx")
            
            # Generar PDF
            pdf_res = generar_pdf_oficial(context, img)
            c_d2.download_button("📥 PDF", pdf_res, f"Informe_{mes}.pdf")
            
        except Exception as e:
            st.error(f"Error: {e}")

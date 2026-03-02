import streamlit as st
from docxtpl import DocxTemplate, InlineImage
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
from docx.shared import Mm
from fpdf import FPDF # Asegúrate de que fpdf2 esté en tu requirements.txt

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Honorarios LS", page_icon="📝", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

st.title("Generador de Informes 📝")
st.markdown("### Ilustre Municipalidad de La Serena")
st.info("Complete los datos para generar su informe de honorarios 2026.")

# --- 2. PASO 1: DATOS DEL PRESTADOR ---
with st.expander("👤 Paso 1: Datos del Prestador", expanded=True):
    nombre = st.text_input("Nombre Completo Prestador", value="RODRIGO ALDRÍN GODOY ALFARO")
    col_a, col_b = st.columns(2)
    direccion = col_a.text_input("Dirección Municipal", "Dirección de Alcaldía")
    depto = col_b.text_input("Departamento / Sección", "Depto. Comunicaciones Estratégicas")
    jornada = st.selectbox("Tipo de Jornada", ["Libre", "Completa", "Flexible", "Media Jornada"])

# --- 3. PASO 2: CONTRATO Y BOLETA ---
with st.expander("💰 Paso 2: Contrato y Boleta", expanded=True):
    c1, c2 = st.columns(2)
    mes = c1.selectbox("Mes del Informe", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=2)
    anio = c2.number_input("Año", value=2026)
    st.markdown("---")
    c3, c4 = st.columns(2)
    monto_contrato = c3.number_input("Monto Bruto según Contrato ($)", value=2000000)
    n_boleta = c4.text_input("Nº Boleta SII")
    
    # Cálculo automático (Tasa 2026: 15.25%)
    descuentos = 0 
    monto_boleta = monto_contrato - descuentos
    liquido = int(monto_boleta * 0.8475)
    st.success(f"Líquido a recibir (aprox): ${liquido:,.0f}")

# --- 4. PASO 3: ACTIVIDADES (TABLA) ---
st.subheader("📋 Paso 3: Actividades Realizadas")
if 'actividades' not in st.session_state:
    st.session_state.actividades = [{"Actividad": "", "Producto": ""}]

def add_row(): st.session_state.actividades.append({"Actividad": "", "Producto": ""})
def del_row(): 
    if len(st.session_state.actividades) > 1: st.session_state.actividades.pop()

for i, item in enumerate(st.session_state.actividades):
    ca, cp = st.columns(2)
    st.session_state.actividades[i]["Actividad"] = ca.text_area(f"Actividad {i+1}", value=item["Actividad"], key=f"a{i}")
    st.session_state.actividades[i]["Producto"] = cp.text_area(f"Resultado {i+1}", value=item["Producto"], key=f"p{i}")

col_btns = st.columns([1, 4])
col_btns[0].button("➕ Añadir", on_click=add_row)
col_btns[1].button("🗑️ Quitar", on_click=del_row)

# --- 5. PASO 4: FIRMA ---
st.subheader("✍️ Paso 4: Firma Digital")
canvas_result = st_canvas(stroke_width=2, stroke_color="black", background_color="white", height=150, width=400, drawing_mode="freedraw", key="canvas")

# --- FUNCIÓN GENERADORA PDF ---
def crear_pdf(ctx, img_pil):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "INFORME MENSUAL DE ACTIVIDADES", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Nombre: {ctx['nombre']}", ln=True)
    pdf.cell(0, 8, f"Unidad: {ctx['direccion']}", ln=True)
    pdf.cell(0, 8, f"Mes: {ctx['mes']} {ctx['anio']}", ln=True)
    pdf.ln(5)
    if img_pil:
        buf = io.BytesIO()
        img_pil.save(buf, format="PNG")
        pdf.image(buf, x=75, w=50)
    return pdf.output()

# --- 6. BOTÓN GENERAR ---
st.divider()
if st.button("🚀 GENERAR INFORME OFICIAL", type="primary", use_container_width=True):
    if canvas_result.image_data is not None:
        try:
            # FIX: Convertir canvas a PIL para evitar error de bytearray
            raw_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            bbox = raw_img.getbbox()
            img = raw_img.crop(bbox) if bbox else raw_img
            
            # Buffer para Word
            img_word = io.BytesIO()
            img.save(img_word, format='PNG')
            img_word.seek(0)

            context = {
                'nombre': nombre.upper(), 'direccion': direccion, 'depto': depto,
                'jornada': jornada, 'mes': mes.upper(), 'anio': anio,
                'monto': f"${monto_contrato:,.0f}",
                'monto_boleta': f"${monto_boleta:,.0f}",
                'boleta': n_boleta, 'actividades': st.session_state.actividades,
                'descuentos': "$0"
            }

            # Render Word
            doc = DocxTemplate("plantilla_base.docx")
            context['firma'] = InlineImage(doc, img_word, height=Mm(20))
            doc.render(context)
            word_buf = io.BytesIO()
            doc.save(word_buf)
            
            st.success("✅ ¡Informe procesado con éxito!")
            c1, c2 = st.columns(2)
            c1.download_button("📥 BAJAR WORD", word_buf.getvalue(), f"Informe_{mes}.docx")
            
            # PDF
            pdf_bytes = crear_pdf(context, img)
            c2.download_button("📥 BAJAR PDF", pdf_bytes, f"Informe_{mes}.pdf")
            
        except Exception as e:
            st.error(f"Error: {e}")

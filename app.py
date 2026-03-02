import streamlit as st
from docxtpl import DocxTemplate, InlineImage
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
from docx.shared import Mm
from fpdf import FPDF # Asegúrate de agregar fpdf2 en requirements.txt

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

# --- 2. FINANZAS ---
with st.expander("💰 Paso 2: Contrato y Boleta", expanded=True):
    c1, c2 = st.columns(2)
    mes = c1.selectbox("Mes del Informe", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=1)
    anio = c2.number_input("Año", value=2026)
    st.markdown("---")
    c3, c4 = st.columns(2)
    monto_contrato = c3.number_input("Monto Bruto según Contrato ($)", value=2000000)
    n_boleta = c4.text_input("Nº Boleta Honorarios")
    
    # Cálculos automáticos (Tasa 2026: 15.25%)
    descuentos = 0 
    monto_boleta = monto_contrato - descuentos
    liquido = int(monto_boleta * 0.8475)
    st.success(f"Líquido estimado a recibir: ${liquido:,.0f}")

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

# --- FUNCIÓN GENERADORA PDF ---
def generar_pdf(ctx, pil_img):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "INFORME MENSUAL DE ACTIVIDADES", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Nombre: {ctx['nombre']}", ln=True)
    pdf.cell(0, 8, f"Dirección: {ctx['direccion']}", ln=True)
    pdf.cell(0, 8, f"Monto Bruto: {ctx['monto_contrato']}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(95, 8, "Actividad", border=1)
    pdf.cell(95, 8, "Producto", border=1, ln=True)
    pdf.set_font("Arial", "", 9)
    for act in ctx['actividades']:
        pdf.multi_cell(95, 6, act['Actividad'], border=1) # Simplificado para estabilidad
    if pil_img:
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        pdf.image(buf, x=75, w=50)
    return pdf.output()

# --- 5. PROCESAMIENTO ---
if st.button("🚀 GENERAR INFORME OFICIAL", type="primary", use_container_width=True):
    if canvas_result.image_data is not None:
        try:
            # Convertir canvas a Imagen PIL y limpiar
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            bbox = img.getbbox()
            if bbox: img = img.crop(bbox)
            
            # Preparar para Word
            img_buf = io.BytesIO()
            img.save(img_buf, format='PNG')
            img_buf.seek(0)

            # Diccionario de datos
            context = {
                'nombre': nombre.upper(), 'direccion': direccion, 'depto': depto,
                'jornada': jornada, 'mes': mes.upper(), 'anio': anio,
                'monto_contrato': f"${monto_contrato:,.0f}",
                'descuentos': f"${descuentos:,.0f}",
                'monto_boleta': f"${monto_boleta:,.0f}",
                'boleta': n_boleta, 'actividades': st.session_state.actividades
            }

            # Generar Word
            doc = DocxTemplate("plantilla_base.docx")
            context['firma'] = InlineImage(doc, img_buf, height=Mm(20))
            doc.render(context)
            word_buf = io.BytesIO()
            doc.save(word_buf)
            
            st.success("✅ ¡Informe procesado!")
            col1, col2 = st.columns(2)
            col1.download_button("📥 DESCARGAR WORD", word_buf.getvalue(), f"Informe_{mes}.docx")
            
            pdf_res = generar_pdf(context, img)
            col2.download_button("📥 DESCARGAR PDF", pdf_res, f"Informe_{mes}.pdf")
            
        except Exception as e:
            st.error(f"Error: {e}")

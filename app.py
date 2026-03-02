import streamlit as st
from docxtpl import DocxTemplate, InlineImage
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
from docx.shared import Mm
from fpdf import FPDF

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Honorarios La Serena", page_icon="📝", layout="centered")

# Estética Municipal
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

st.title("Generador de Informes 📝")
st.markdown("### Ilustre Municipalidad de La Serena")
st.caption("Herramienta oficial de autogestión para prestadores a honorarios.")

# --- LISTADO DE DIRECCIONES MUNICIPALES ---
unidades_municipales = [
    "Alcaldía",
    "Administración Municipal",
    "Secretaría Municipal",
    "DIDECO (Dirección de Desarrollo Comunitario)",
    "DOM (Dirección de Obras Municipales)",
    "SECPLAN (Secretaría Comunal de Planificación)",
    "Dirección de Tránsito y Transporte Público",
    "Dirección de Aseo y Ornato",
    "Dirección de Medio Ambiente, Seguridad y Gestión de Riesgo",
    "Dirección de Turismo y Patrimonio",
    "Dirección de Salud (Corporación)",
    "Dirección de Educación (Corporación)",
    "Dirección de Seguridad Ciudadana",
    "Dirección de Gestión de Personas",
    "Dirección de Finanzas",
    "Dirección de Control",
    "Asesoría Jurídica",
    "Departamento de Comunicaciones",
    "Departamento de Eventos",
    "Delegación Municipal Av. del Mar",
    "Delegación Municipal La Pampa",
    "Delegación Municipal La Antena",
    "Delegación Municipal Las Compañías",
    "Delegación Municipal Rural",
    "Radio Digital Municipal RDMLS"
]

# --- 2. PASO 1: DATOS DEL PRESTADOR ---
with st.expander("👤 Paso 1: Identificación", expanded=True):
    nombre = st.text_input("Nombre Completo del Prestador", placeholder="Ej: JUAN PÉREZ ROJAS")
    
    col_a, col_b = st.columns(2)
    direccion = col_a.selectbox("Dirección Municipal / Unidad", unidades_municipales)
    depto = col_b.text_input("Departamento o Sección Específica", placeholder="Ej: Oficina de Partes")
    
    jornada = st.selectbox("Tipo de Jornada", ["Libre", "Completa", "Flexible", "Media Jornada"])

# --- 3. PASO 2: FINANZAS Y PERIODO ---
with st.expander("💰 Paso 2: Periodo y Montos", expanded=True):
    c1, c2 = st.columns(2)
    mes = c1.selectbox("Mes del Informe", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=2)
    anio = c2.number_input("Año", value=2026)
    
    st.divider()
    
    c3, c4 = st.columns(2)
    monto_contrato = c3.number_input("Monto Bruto Contrato ($)", value=0, step=10000)
    n_boleta = c4.text_input("Nº Boleta SII", placeholder="000")
    
    # Cálculo 2026 (Tasa 15.25%)
    descuentos = 0 
    monto_boleta = monto_contrato - descuentos
    impuesto = int(monto_boleta * 0.1525)
    liquido = monto_boleta - impuesto
    
    if monto_contrato > 0:
        st.info(f"💰 **Resumen:** Bruto: ${monto_boleta:,.0f} | Retención (15.25%): ${impuesto:,.0f} | Líquido: ${liquido:,.0f}")

# --- 4. PASO 3: ACTIVIDADES ---
st.subheader("📋 Paso 3: Resumen de Actividades")
if 'actividades' not in st.session_state:
    st.session_state.actividades = [{"Actividad": "", "Producto": ""}]

def add_act(): st.session_state.actividades.append({"Actividad": "", "Producto": ""})
def del_act(): 
    if len(st.session_state.actividades) > 1: st.session_state.actividades.pop()

for i, item in enumerate(st.session_state.actividades):
    ca, cp = st.columns(2)
    st.session_state.actividades[i]["Actividad"] = ca.text_area(f"Actividad {i+1}", value=item["Actividad"], key=f"a{i}")
    st.session_state.actividades[i]["Producto"] = cp.text_area(f"Producto/Resultado {i+1}", value=item["Producto"], key=f"p{i}")

st.button("➕ Agregar Actividad", on_click=add_act)

# --- 5. PASO 4: FIRMA ---
st.subheader("✍️ Paso 4: Firma Digital")
canvas_result = st_canvas(stroke_width=2, stroke_color="black", background_color="white", height=150, width=400, drawing_mode="freedraw", key="canvas")

# --- FUNCIÓN PDF ---
def generar_pdf(ctx, img_pil):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "INFORME MENSUAL DE ACTIVIDADES", ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 7, f"Nombre: {ctx['nombre']}", ln=True)
    pdf.cell(0, 7, f"Unidad: {ctx['direccion']}", ln=True)
    pdf.cell(0, 7, f"Periodo: {ctx['mes']} {ctx['anio']}", ln=True)
    pdf.ln(5)
    if img_pil:
        buf = io.BytesIO()
        img_pil.save(buf, format="PNG")
        pdf.image(buf, x=75, w=50)
    return pdf.output()

# --- 6. GENERAR ---
st.divider()
if st.button("🚀 GENERAR INFORME OFICIAL", type="primary", use_container_width=True):
    if not nombre or canvas_result.image_data is None:
        st.error("⚠️ Debe ingresar su nombre y firmar el documento.")
    else:
        try:
            # Procesar Firma
            raw_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            bbox = raw_img.getbbox()
            img = raw_img.crop(bbox) if bbox else raw_img
            
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

            # Word
            doc = DocxTemplate("plantilla_base.docx")
            context['firma'] = InlineImage(doc, img_word, height=Mm(20))
            doc.render(context)
            word_buf = io.BytesIO()
            doc.save(word_buf)
            
            st.success("✅ Documentos generados.")
            c_w, c_p = st.columns(2)
            c_w.download_button("📥 WORD (.docx)", word_buf.getvalue(), f"Informe_{mes}.docx")
            
            pdf_bytes = generar_pdf(context, img)
            c_p.download_button("📥 PDF (.pdf)", pdf_bytes, f"Informe_{mes}.pdf")
            
        except Exception as e:
            st.error(f"Error: {e}")

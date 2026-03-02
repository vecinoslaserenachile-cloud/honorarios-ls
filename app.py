import streamlit as st
from docxtpl import DocxTemplate, InlineImage
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
from docx.shared import Mm
from fpdf import FPDF # Librería para el PDF de alta calidad

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
st.info("Complete los datos mensuales, firme digitalmente y descargue su informe estandarizado.")

# --- 2. DATOS DEL FUNCIONARIO ---
with st.expander("👤 Paso 1: Datos del Prestador", expanded=True):
    nombre = st.text_input("Nombre Completo Prestador", value="RODRIGO ALDRÍN GODOY ALFARO", key="nombre")
    col_a, col_b = st.columns(2)
    direccion = col_a.text_input("Dirección Municipal", "Dirección de Alcaldía")
    depto = col_b.text_input("Departamento / Sección", "Depto. Comunicaciones Estratégicas")
    jornada = st.selectbox("Tipo de Jornada", ["Libre", "Completa", "Flexible", "Media Jornada"])

# --- 3. DATOS FINANCIEROS Y PERIODO ---
with st.expander("💰 Paso 2: Contrato y Boleta", expanded=True):
    c1, c2 = st.columns(2)
    mes = c1.selectbox("Mes del Informe", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=1)
    anio = c2.number_input("Año", value=2026)
    st.markdown("---")
    c3, c4 = st.columns(2)
    monto_contrato = c3.number_input("Monto Bruto según Contrato ($)", value=2000000, step=50000)
    tiene_descuentos = st.checkbox("¿Hubo descuentos por atrasos o inasistencias?")
    descuentos = 0
    if tiene_descuentos:
        descuentos = st.number_input("Total a Descontar ($)", value=0)
    monto_boleta = monto_contrato - descuentos
    n_boleta = c4.text_input("Nº Boleta Honorarios")

    tasa_retencion = 0.1525 
    impuesto = int(monto_boleta * tasa_retencion)
    liquido = int(monto_boleta - impuesto)
    
    st.success(f"📊 **Resumen:** Bruto: ${monto_boleta:,.0f} | Retención: ${impuesto:,.0f} | **Líquido: ${liquido:,.0f}**")

# --- 4. ACTIVIDADES (TABLA DINÁMICA) ---
st.subheader("📋 Paso 3: Actividades Realizadas")
if 'actividades' not in st.session_state:
    st.session_state.actividades = [{"Actividad": "", "Producto": ""}]

def agregar_fila(): st.session_state.actividades.append({"Actividad": "", "Producto": ""})
def eliminar_fila():
    if len(st.session_state.actividades) > 1: st.session_state.actividades.pop()

for i, item in enumerate(st.session_state.actividades):
    col_act, col_prod = st.columns(2)
    st.session_state.actividades[i]["Actividad"] = col_act.text_area(f"Actividad {i+1}", value=item["Actividad"], height=70, key=f"a_{i}")
    st.session_state.actividades[i]["Producto"] = col_prod.text_area(f"Producto/Resultado {i+1}", value=item["Producto"], height=70, key=f"p_{i}")

c_mas, c_menos = st.columns([1, 4])
c_mas.button("➕ Agregar Fila", on_click=agregar_fila)
c_menos.button("🗑️ Quitar Última", on_click=eliminar_fila)

# --- 5. FIRMA DIGITAL ---
st.markdown("---")
st.subheader("✍️ Paso 4: Firma Digital")
tipo_firma = st.radio("Método de firma:", ["Dibujar en pantalla", "Subir imagen"], horizontal=True)
imagen_final = None

if tipo_firma == "Dibujar en pantalla":
    canvas_result = st_canvas(stroke_width=2, stroke_color="#000000", background_color="#ffffff", height=150, width=400, drawing_mode="freedraw", key="canvas_firma")
    if canvas_result.image_data is not None:
        imagen_final = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
else:
    uploaded_file = st.file_uploader("Suba su firma", type=["png", "jpg", "jpeg"])
    if uploaded_file: imagen_final = Image.open(uploaded_file)

# --- FUNCIÓN GENERADORA DE PDF ---
def generar_pdf(data, firma_img):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "INFORME MENSUAL DE ACTIVIDADES", ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, "ILUSTRE MUNICIPALIDAD DE LA SERENA", ln=True, align='C')
    pdf.ln(5)
    
    # Datos del Prestador
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, " DATOS DEL PRESTADOR", ln=True, fill=True, border=1)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 8, f" Nombre: {data['nombre']}", border=1)
    pdf.cell(95, 8, f" Mes: {data['mes']} {data['anio']}", border=1, ln=True)
    pdf.cell(95, 8, f" Dirección: {data['direccion']}", border=1)
    pdf.cell(95, 8, f" Jornada: {data['jornada']}", border=1, ln=True)
    pdf.ln(5)

    # Actividades
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, " RESUMEN DE ACTIVIDADES", ln=True, fill=True, border=1)
    pdf.cell(95, 8, " Actividad", border=1)
    pdf.cell(95, 8, " Producto/Resultado", border=1, ln=True)
    pdf.set_font("Arial", "", 9)
    for act in data['actividades']:
        # Altura dinámica
        inicio_y = pdf.get_y()
        pdf.multi_cell(95, 6, act['Actividad'], border=1)
        fin_y = pdf.get_y()
        pdf.set_y(inicio_y)
        pdf.set_x(105)
        pdf.multi_cell(95, 6, act['Producto'], border=1)
        pdf.set_y(max(fin_y, pdf.get_y()))

    # Firma
    pdf.ln(10)
    if firma_img:
        buf = io.BytesIO()
        firma_img.save(buf, format="PNG")
        pdf.image(buf, x=75, w=60)
    pdf.cell(0, 10, "__________________________", ln=True, align='C')
    pdf.cell(0, 5, "FIRMA DEL PRESTADOR", ln=True, align='C')
    return pdf.output()

# --- 6. GENERACIÓN DEL DOCUMENTO ---
st.markdown("---")
if st.button("🚀 GENERAR INFORME OFICIAL", type="primary", use_container_width=True):
    if not nombre or (tipo_firma == "Dibujar en pantalla" and len(canvas_result.json_data["objects"]) == 0):
        st.error("⚠️ Complete nombre y firma.")
    else:
        try:
            if imagen_final:
                bbox = imagen_final.getbbox()
                if bbox: imagen_final = imagen_final.crop(bbox)
                img_byte_arr = io.BytesIO()
                imagen_final.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
            
            doc = DocxTemplate("plantilla_base.docx")
            context = {
                'nombre': nombre.upper(), 'direccion': direccion, 'depto': depto, 'jornada': jornada,
                'mes': mes.upper(), 'anio': anio, 'monto_contrato': f"${monto_contrato:,.0f}",
                'descuentos': f"${descuentos:,.0f}", 'monto_boleta': f"${monto_boleta:,.0f}",
                'boleta': n_boleta, 'actividades': st.session_state.actividades,
                'firma': InlineImage(doc, img_byte_arr, height=Mm(20))
            }
            doc.render(context)
            bio_word = io.BytesIO()
            doc.save(bio_word)
            
            st.balloons()
            col_d1, col_d2 = st.columns(2)
            col_d1.download_button("📥 DESCARGAR WORD", data=bio_word.getvalue(), file_name=f"Informe_{mes}.docx")
            
            pdf_out = generar_pdf(context, imagen_final)
            col_d2.download_button("📥 DESCARGAR PDF", data=pdf_out, file_name=f"Informe_{mes}.pdf")

        except Exception as e:
            st.error(f"Error: {e}")

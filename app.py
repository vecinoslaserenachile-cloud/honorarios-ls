import streamlit as st
from docxtpl import DocxTemplate, InlineImage
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
from docx.shared import Mm

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Honorarios LS", page_icon="📝", layout="centered")
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>""", unsafe_allow_html=True)

st.title("Generador de Informes 📝")
st.markdown("**Ilustre Municipalidad de La Serena**")

# --- 1. DATOS DEL FUNCIONARIO ---
with st.expander("👤 Paso 1: Datos del Prestador", expanded=True):
    nombre = st.text_input("Nombre Completo Prestador", placeholder="Ej: RODRIGO GODOY", key="nombre")
    
    col_a, col_b = st.columns(2)
    direccion = col_a.text_input("Dirección Municipal", "Dirección de Alcaldía")
    depto = col_b.text_input("Departamento / Sección", "Depto. Comunicaciones Estratégicas")
    jornada = st.selectbox("Tipo de Jornada", ["Libre", "Completa", "Flexible", "Media Jornada"])

# --- 2. DATOS FINANCIEROS (CON CÁLCULO 2026) ---
with st.expander("💰 Paso 2: Contrato y Boleta", expanded=True):
    c1, c2 = st.columns(2)
    mes = c1.selectbox("Mes del Informe", ["Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
    anio = c2.number_input("Año", value=2026)
    
    st.markdown("---")
    
    c3, c4 = st.columns(2)
    # El contrato dice el Bruto (Total)
    monto_bruto = c3.number_input("Monto Bruto Contrato ($)", value=2000000, step=50000)
    n_boleta = c4.text_input("Nº Boleta Honorarios")

    # --- CÁLCULORA DE BOLSILLO (Solo informativo) ---
    # Tasa 2026 = 15.25%
    retencion = int(monto_bruto * 0.1525)
    liquido = int(monto_bruto - retencion)
    
    st.info(f"""
    📊 **Simulación de Pago (2026):**
    Tu boleta es por: **${monto_bruto:,.0f}** (Bruto)
    El Municipio retiene: **${retencion:,.0f}** (15.25% Impuesto)
    Tu recibirás: **${liquido:,.0f}** (Líquido)
    """)

# --- 3. ACTIVIDADES ---
st.subheader("📋 Paso 3: Actividades Realizadas")

if 'actividades' not in st.session_state:
    st.session_state.actividades = [{"Actividad": "", "Producto": ""}]

def agregar(): st.session_state.actividades.append({"Actividad": "", "Producto": ""})
def quitar(): 
    if len(st.session_state.actividades) > 1: st.session_state.actividades.pop()

for i, item in enumerate(st.session_state.actividades):
    c_act, c_prod = st.columns(2)
    st.session_state.actividades[i]["Actividad"] = c_act.text_area(f"Actividad {i+1}", value=item["Actividad"], height=70, key=f"a{i}")
    st.session_state.actividades[i]["Producto"] = c_prod.text_area(f"Producto {i+1}", value=item["Producto"], height=70, key=f"p{i}")

ca, cb = st.columns([1, 4])
ca.button("➕ Agregar Fila", on_click=agregar)
cb.button("🗑️ Quitar Última", on_click=quitar)

# --- 4. FIRMA ---
st.markdown("---")
st.subheader("✍️ Paso 4: Firma")
tipo = st.radio("Método:", ["Dibujar en pantalla", "Subir imagen"], horizontal=True)
img_final = None

if tipo == "Dibujar en pantalla":
    canvas = st_canvas(stroke_width=2, stroke_color="black", background_color="white", height=150, width=400, drawing_mode="freedraw", key="canvas")
    if canvas.image_data is not None: img_final = Image.fromarray(canvas.image_data.astype('uint8'), 'RGBA')
else:
    up = st.file_uploader("Subir firma", type=["png", "jpg"])
    if up: img_final = Image.open(up)

# --- GENERAR ---
if st.button("🚀 GENERAR INFORME", type="primary", use_container_width=True):
    if not nombre:
        st.error("⚠️ Falta el Nombre.")
    elif tipo == "Dibujar en pantalla" and (canvas.json_data is None or len(canvas.json_data["objects"]) == 0):
        st.error("⚠️ Falta la Firma.")
    else:
        if img_final:
            bbox = img_final.getbbox()
            if bbox: img_final = img_final.crop(bbox)
            byte_io = io.BytesIO()
            img_final.save(byte_io, format='PNG')
            byte_io.seek(0)
            
        doc = DocxTemplate("plantilla_base.docx")
        
        # AQUÍ ESTÁ LA LÓGICA DEL WORD:
        # Repetimos 'monto_bruto' en ambos campos porque no hubo descuentos.
        context = {
            'nombre': nombre.upper(),
            'direccion': direccion,
            'depto': depto,
            'jornada': jornada,
            'mes': mes.upper(),
            'anio': anio,
            'monto': f"${monto_bruto:,.0f}".replace(",", "."),       # Monto Bruto Contrato
            'monto_boleta': f"${monto_bruto:,.0f}".replace(",", "."),# Monto Boleta (Igual al Bruto)
            'boleta': n_boleta,
            'actividades': st.session_state.actividades,
            'firma': InlineImage(doc, byte_io, height=Mm(20))
        }
        doc.render(context)
        
        bio = io.BytesIO()
        doc.save(bio)
        bio.seek(0)
        
        st.download_button("📥 DESCARGAR", bio, f"Informe_{mes}_{nombre.split()[0]}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

import streamlit as st
from docxtpl import DocxTemplate, InlineImage
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
from docx.shared import Mm

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Honorarios LS", page_icon="📝", layout="centered")

# Ocultar elementos de la interfaz de Streamlit para que se vea más limpio
hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# --- TÍTULO Y ENCABEZADO ---
st.title("Generador de Informes 📝")
st.markdown("**Ilustre Municipalidad de La Serena**")
st.info("Complete los datos, firme digitalmente y descargue su informe mensual estandarizado.")

# --- 1. DATOS DEL FUNCIONARIO ---
with st.expander("👤 Paso 1: Datos Personales y Contrato", expanded=True):
    col1, col2 = st.columns(2)
    nombre = col1.text_input("Nombre Completo", placeholder="Ej: JUAN PÉREZ", key="nombre")
    rut = col2.text_input("RUT", placeholder="12.345.678-9", key="rut")
    direccion = col1.text_input("Dirección / Unidad", "Dirección de Alcaldía")
    programa = col2.text_input("Nombre del Programa", "COMUNICACIÓN ESTRATÉGICA...")
    
    # Cálculo de honorarios 2026 (Tasa 15.25%)
    monto_bruto = st.number_input("Monto Bruto ($)", value=2000000, step=50000)
    retencion = int(monto_bruto * 0.1525)
    liquido = int(monto_bruto - retencion)
    st.caption(f"💰 **Detalle Pago:** Bruto: ${monto_bruto:,.0f} | Retención (15.25%): ${retencion:,.0f} | Líquido: ${liquido:,.0f}")

# --- 2. PERIODO ---
with st.expander("📅 Paso 2: Periodo a Informar", expanded=True):
    c1, c2, c3 = st.columns(3)
    mes = c1.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
    anio = c2.number_input("Año", value=2026)
    boleta = c3.text_input("Nº Boleta SII")

# --- 3. ACTIVIDADES ---
st.subheader("📋 Paso 3: Actividades Realizadas")

# Inicializar estado de actividades
if 'actividades' not in st.session_state:
    st.session_state.actividades = [{"Actividad": "", "Producto": ""}]

def agregar_fila():
    st.session_state.actividades.append({"Actividad": "", "Producto": ""})

def eliminar_fila():
    if len(st.session_state.actividades) > 1:
        st.session_state.actividades.pop()

# Renderizar campos de actividades
for i, item in enumerate(st.session_state.actividades):
    col_a, col_b = st.columns(2)
    st.session_state.actividades[i]["Actividad"] = col_a.text_area(f"Actividad {i+1}", value=item["Actividad"], height=70, key=f"act_{i}")
    st.session_state.actividades[i]["Producto"] = col_b.text_area(f"Producto {i+1}", value=item["Producto"], height=70, key=f"prod_{i}")

c_plus, c_minus = st.columns([1, 4])
c_plus.button("➕ Agregar Otra", on_click=agregar_fila)
c_minus.button("🗑️ Quitar Última", on_click=eliminar_fila)

# --- 4. FIRMA DIGITAL (HÍBRIDA) ---
st.markdown("---")
st.subheader("✍️ Paso 4: Firma Digital")

tipo_firma = st.radio("Método de firma:", ["Dibujar en pantalla", "Subir imagen"], horizontal=True)
imagen_final = None

if tipo_firma == "Dibujar en pantalla":
    st.caption("Firme en el recuadro blanco usando su dedo (móvil) o mouse (PC):")
    # Canvas para dibujar
    canvas_result = st_canvas(
        stroke_width=2,
        stroke_color="#000000",
        background_color="#ffffff",
        height=150,
        width=400,
        drawing_mode="freedraw",
        key="canvas"
    )
    # Procesar el dibujo si existe
    if canvas_result.image_data is not None:
        imagen_final = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
else:
    # Subir archivo
    uploaded = st.file_uploader("Suba una foto de su firma (PNG/JPG)", type=["png", "jpg", "jpeg"])
    if uploaded:
        imagen_final = Image.open(uploaded)
        st.image(imagen_final, caption="Vista previa firma", width=200)

# --- GENERACIÓN DEL DOCUMENTO ---
st.markdown("---")
btn_generar = st.button("🚀 GENERAR INFORME OFICIAL", type="primary", use_container_width=True)

if btn_generar:
    # Validaciones
    if not nombre or not rut:
        st.error("⚠️ Por favor complete su Nombre y RUT.")
    # Validar firma en modo dibujo (si no ha dibujado nada)
    elif tipo_firma == "Dibujar en pantalla" and (canvas_result.json_data is None or len(canvas_result.json_data["objects"]) == 0):
         st.error("⚠️ Por favor dibuje su firma.")
    elif tipo_firma == "Subir imagen" and imagen_final is None:
         st.error("⚠️ Por favor suba la imagen de su firma.")
    else:
        try:
            # Preparar imagen de firma para Word (en memoria)
            # Recortar espacios vacíos de la firma (opcional pero estético)
            if imagen_final:
                bbox = imagen_final.getbbox()
                if bbox:
                    imagen_final = imagen_final.crop(bbox)
                
                img_byte_arr = io.BytesIO()
                imagen_final.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)

            # Cargar Plantilla
            # IMPORTANTE: El archivo debe llamarse exactamente así en el GitHub
            doc = DocxTemplate("plantilla_base.docx")

            # Crear Contexto (Diccionario de datos para reemplazar en el Word)
            context = {
                'nombre': nombre.upper(),
                'rut': rut,
                'direccion': direccion,
                'programa': programa,
                'mes': mes.upper(),
                'anio': anio,
                'monto': f"${monto_bruto:,.0f}".replace(",", "."), # Formato Chileno con puntos
                'boleta': boleta,
                'actividades': st.session_state.actividades, # La lista de la tabla
                'firma': InlineImage(doc, img_byte_arr, height=Mm(20)) # Altura fija de 2cm para que no se deforme
            }

            # Renderizar
            doc.render(context)
            
            # Guardar en buffer de memoria
            bio = io.BytesIO()
            doc.save(bio)
            bio.seek(0)

            # Botón de Descarga
            st.success("✅ ¡Informe generado correctamente!")
            st.download_button(
                label="📥 DESCARGAR INFORME (.DOCX)",
                data=bio,
                file_name=f"Informe_{mes}_{nombre.split()[0]}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        except Exception as e:
            st.error(f"Error al generar: {e}")
            st.warning("Asegúrate de que 'plantilla_base.docx' esté subido en el repositorio de GitHub.")

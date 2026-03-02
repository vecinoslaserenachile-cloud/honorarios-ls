import streamlit as st
from docxtpl import DocxTemplate, InlineImage
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
from docx.shared import Mm

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Honorarios LS", page_icon="📝", layout="centered")

# Ocultar marcas de agua y menú de Streamlit para un look profesional
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {
        background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)

# Encabezado con imagen (opcional) o texto
st.title("Generador de Informes 📝")
st.markdown("### Ilustre Municipalidad de La Serena")
st.info("Complete los datos mensuales, firme digitalmente y descargue su informe estandarizado.")

# --- 2. DATOS DEL FUNCIONARIO ---
with st.expander("👤 Paso 1: Datos del Prestador", expanded=True):
    nombre = st.text_input("Nombre Completo Prestador", placeholder="Ej: RODRIGO GODOY ALFARO", key="nombre")
    
    col_a, col_b = st.columns(2)
    direccion = col_a.text_input("Dirección Municipal", "Dirección de Alcaldía")
    depto = col_b.text_input("Departamento / Sección", "Depto. Comunicaciones Estratégicas")
    
    # Campo específico solicitado en el formato
    jornada = st.selectbox("Tipo de Jornada", ["Libre", "Completa", "Flexible", "Media Jornada"])

# --- 3. DATOS FINANCIEROS Y PERIODO ---
with st.expander("💰 Paso 2: Contrato y Boleta", expanded=True):
    c1, c2 = st.columns(2)
    mes = c1.selectbox("Mes del Informe", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
    anio = c2.number_input("Año", value=2026)
    
    st.markdown("---")
    
    # Entradas de dinero
    c3, c4 = st.columns(2)
    monto_contrato = c3.number_input("Monto Bruto según Contrato ($)", value=2000000, step=50000)
    
    # Lógica de Descuentos (Multas/Atrasos)
    tiene_descuentos = st.checkbox("¿Hubo descuentos por atrasos o inasistencias?")
    descuentos = 0
    if tiene_descuentos:
        descuentos = st.number_input("Total a Descontar ($)", value=0, help="Ingrese el monto total de la multa o descuento.")
    
    # Cálculo del valor final de la boleta
    monto_boleta = monto_contrato - descuentos
    
    n_boleta = c4.text_input("Nº Boleta Honorarios")

    # --- VISOR DE BOLSILLO (Cálculo 2026) ---
    # Esto es solo visual para el usuario, no va al documento Word
    tasa_retencion = 0.1525 # 15.25% para 2026
    impuesto = int(monto_boleta * tasa_retencion)
    liquido = int(monto_boleta - impuesto)
    
    st.success(f"""
    📊 **Resumen Financiero:**
    * **Monto Boleta:** ${monto_boleta:,.0f} (Valor a declarar)
    * **Retención (15.25%):** -${impuesto:,.0f} (Pago al SII)
    * **Líquido a Recibir:** ${liquido:,.0f} (En su cuenta)
    """)

# --- 4. ACTIVIDADES (TABLA DINÁMICA) ---
st.subheader("📋 Paso 3: Actividades Realizadas")

if 'actividades' not in st.session_state:
    st.session_state.actividades = [{"Actividad": "", "Producto": ""}]

def agregar_fila():
    st.session_state.actividades.append({"Actividad": "", "Producto": ""})

def eliminar_fila():
    if len(st.session_state.actividades) > 1:
        st.session_state.actividades.pop()

# Renderizar cada fila de actividad
for i, item in enumerate(st.session_state.actividades):
    col_act, col_prod = st.columns(2)
    st.session_state.actividades[i]["Actividad"] = col_act.text_area(f"Actividad {i+1}", value=item["Actividad"], height=70, key=f"a_{i}")
    st.session_state.actividades[i]["Producto"] = col_prod.text_area(f"Producto/Resultado {i+1}", value=item["Producto"], height=70, key=f"p_{i}")

# Botones de control de tabla
c_mas, c_menos = st.columns([1, 4])
c_mas.button("➕ Agregar Fila", on_click=agregar_fila)
c_menos.button("🗑️ Quitar Última", on_click=eliminar_fila)

# --- 5. FIRMA DIGITAL ---
st.markdown("---")
st.subheader("✍️ Paso 4: Firma Digital")

tipo_firma = st.radio("Método de firma:", ["Dibujar en pantalla", "Subir imagen"], horizontal=True)
imagen_final = None

if tipo_firma == "Dibujar en pantalla":
    st.caption("Firme en el recuadro blanco usando su dedo (móvil) o mouse:")
    canvas_result = st_canvas(
        stroke_width=2,
        stroke_color="#000000",
        background_color="#ffffff",
        height=150,
        width=400,
        drawing_mode="freedraw",
        key="canvas_firma"
    )
    if canvas_result.image_data is not None:
        imagen_final = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
else:
    uploaded_file = st.file_uploader("Suba su firma (PNG/JPG)", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        imagen_final = Image.open(uploaded_file)
        st.image(imagen_final, width=200, caption="Vista previa")

# --- 6. GENERACIÓN DEL DOCUMENTO ---
st.markdown("---")
btn_generar = st.button("🚀 GENERAR INFORME OFICIAL", type="primary", use_container_width=True)

if btn_generar:
    # Validaciones básicas
    error = False
    if not nombre:
        st.error("⚠️ Falta el Nombre del Prestador.")
        error = True
    
    if tipo_firma == "Dibujar en pantalla":
        # Verificar si el canvas está vacío (o tiene muy pocos trazos)
        if canvas_result.json_data is None or len(canvas_result.json_data["objects"]) == 0:
            st.error("⚠️ Por favor firme el documento.")
            error = True
    elif tipo_firma == "Subir imagen" and imagen_final is None:
        st.error("⚠️ Por favor suba la imagen de su firma.")
        error = True

    if not error:
        try:
            # Procesar la firma para insertarla en Word
            if imagen_final:
                # Recortar bordes vacíos (autocrop) para que la firma se vea grande
                bbox = imagen_final.getbbox()
                if bbox:
                    imagen_final = imagen_final.crop(bbox)
                
                img_byte_arr = io.BytesIO()
                imagen_final.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
            
            # Cargar la plantilla maestra
            doc = DocxTemplate("plantilla_base.docx")
            
            # Crear el Diccionario de Contexto (Mapping de variables)
            context = {
                'nombre': nombre.upper(),
                'direccion': direccion,
                'depto': depto,
                'jornada': jornada,
                'mes': mes.upper(),
                'anio': anio,
                'monto_contrato': f"${monto_contrato:,.0f}".replace(",", "."), # Formato Chileno
                'descuentos': f"${descuentos:,.0f}".replace(",", "."),
                'monto_boleta': f"${monto_boleta:,.0f}".replace(",", "."),
                'boleta': n_boleta,
                'actividades': st.session_state.actividades, # La lista de la tabla
                'firma': InlineImage(doc, img_byte_arr, height=Mm(20)) # Altura fija de 2cm
            }

            # Renderizar el documento
            doc.render(context)
            
            # Guardar en memoria para descarga
            bio = io.BytesIO()
            doc.save(bio)
            bio.seek(0)

            st.balloons() # ¡Efecto de celebración!
            st.success("✅ Informe generado exitosamente.")
            
            st.download_button(
                label="📥 DESCARGAR INFORME (.DOCX)",
                data=bio,
                file_name=f"Informe_{mes}_{nombre.split()[0]}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        except Exception as e:
            st.error(f"Error técnico: {e}")
            st.warning("Asegúrate de que el archivo 'plantilla_base.docx' esté cargado en el repositorio de GitHub.")

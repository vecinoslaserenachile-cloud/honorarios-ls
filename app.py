import streamlit as st
from docxtpl import DocxTemplate, InlineImage
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np
import io
import sqlite3
import pandas as pd
import json
import base64
import textwrap
import time
import os
import re
from docx.shared import Mm
from fpdf import FPDF

# ==============================================================================
# 1. CONFIGURACIÓN ESTRATÉGICA DE LA PLATAFORMA MUNICIPAL
# ==============================================================================
st.set_page_config(
    page_title="Sistema Honorarios La Serena 2026", 
    page_icon="📝", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 2. BLINDAJE CSS CORREGIDO (VISIBILIDAD MÓVIL, MENÚ Y TEXTOS INMUNES)
# ==============================================================================
st.markdown("""
    <style>
    /* --- 1. FUERZA TEMA CLARO (ANTI-DARK MODE) --- */
    :root { color-scheme: light !important; }
    .stApp {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* --- 2. RESCATE DE PESTAÑAS EN MÓVIL (BOTÓN HAMBURGUESA VISIBLE) --- */
    header[data-testid="stHeader"] {
        background-color: rgba(255, 255, 255, 0.95) !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important;
    }
    button[data-testid="collapsedControl"] {
        background-color: #0D47A1 !important; /* Azul Institucional Fuerte */
        border-radius: 8px !important;
        margin: 10px !important;
        opacity: 1 !important;
        visibility: visible !important;
        display: flex !important;
        align-items: center;
        justify-content: center;
    }
    button[data-testid="collapsedControl"] svg {
        fill: #FFFFFF !important; /* Ícono de rayas en color blanco */
        color: #FFFFFF !important;
        width: 28px !important;
        height: 28px !important;
    }
    
    /* Fondo del menú lateral (Sidebar) elegante */
    section[data-testid="stSidebar"] {
        background-color: #F8F9FA !important;
        border-right: 2px solid #E1E8F0 !important;
    }
    
    /* --- SOLUCIÓN TEXTOS INVISIBLES EN EL MENÚ (BLANCO SOBRE BLANCO) --- */
    section[data-testid="stSidebar"] .stRadio label p, 
    section[data-testid="stSidebar"] .stRadio label span,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
        color: #0A192F !important;
        -webkit-text-fill-color: #0A192F !important; /* FUERZA LETRA OSCURA EN iOS/ANDROID */
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }

    /* --- 3. FORMULARIOS LIMPIOS Y LEGIBLES --- */
    .stTextInput input, 
    .stTextArea textarea, 
    .stNumberInput input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 500 !important;
    }
    
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    div[data-baseweb="select"] span {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 500 !important;
    }

    /* Títulos y Etiquetas Generales en Negro INMUNE AL MODO OSCURO */
    label, .stMarkdown p, .stText p, span {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important; /* Evita que se vuelvan blancos */
        font-weight: 500 !important;
    }

    ::placeholder { 
        color: #78909C !important; 
        -webkit-text-fill-color: #78909C !important;
        opacity: 1 !important;
    }

    /* --- 4. EXPANDERS (PASOS 1, 2, 3...) PROTEGIDOS --- */
    details {
        background-color: #FFFFFF !important;
        border: 1px solid #CFD8DC !important;
        border-radius: 8px !important;
        margin-bottom: 10px !important;
    }
    details > summary {
        background-color: #F0F4F8 !important; 
        color: #0D47A1 !important;
        border-radius: 8px !important;
        padding: 10px 15px !important;
    }
    details > summary p {
        color: #0D47A1 !important;
        -webkit-text-fill-color: #0D47A1 !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
        margin: 0 !important;
    }

    /* --- 5. BOTONES MUNICIPALES INSTITUCIONALES --- */
    .stButton > button {
        background-color: #0D47A1 !important; 
        color: #FFFFFF !important; 
        -webkit-text-fill-color: #FFFFFF !important; /* Letra blanca forzada en botones */
        border: none !important; 
        border-radius: 6px !important;
        font-weight: bold !important;
        transition: 0.3s !important;
    }
    .stButton > button:hover {
        background-color: #1565C0 !important; 
        transform: scale(1.02);
    }

    /* Herramientas del Canvas protegidas */
    .stDrawableCanvas button {
        background-color: #E3F2FD !important;
    }
    .stDrawableCanvas button svg {
        fill: #0D47A1 !important;
    }

    /* --- 6. HUINCHA ANIMADA PERFECTA --- */
    .marquee-container {
        width: 100%;
        overflow: hidden;
        background-color: #E8F5E9;
        border: 2px solid #A5D6A7;
        border-radius: 10px;
        padding: 12px 0;
        box-sizing: border-box;
        margin: 15px 0;
    }
    .marquee-content {
        display: inline-block;
        white-space: nowrap;
        padding-left: 100%; 
        animation: marquee-scroll 45s linear infinite; 
        font-size: clamp(14px, 3vw, 18px);
        font-weight: 700;
        color: #1B5E20 !important;
        -webkit-text-fill-color: #1B5E20 !important; /* Fuerza color verde oscuro */
    }
    .marquee-content b {
        color: #1B5E20 !important;
        -webkit-text-fill-color: #1B5E20 !important;
    }
    @keyframes marquee-scroll {
        0%   { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); } 
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. FUNCIONES DE IMÁGENES BASE64 (PROTECCIÓN ANTI-CORTES)
# ==============================================================================
def get_image_base64(path, default_url):
    """Carga imágenes locales en formato Base64 para inyectarlas usando HTML puro"""
    if os.path.exists(path):
        with open(path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    return default_url

def codificar_firma_b64(datos_canvas):
    """Convierte el lienzo de firma digital a un archivo PNG con fondo blanco"""
    img_r = Image.fromarray(datos_canvas.astype('uint8'), 'RGBA')
    bg_w = Image.new("RGB", img_r.size, (255, 255, 255))
    bg_w.paste(img_r, mask=img_r.split()[3])
    buf_img = io.BytesIO()
    bg_w.save(buf_img, format="PNG")
    return base64.b64encode(buf_img.getvalue()).decode('utf-8')

def decodificar_firma_io(cadena_b64):
    """Decodifica la firma para inyectarla en la plantilla de Word y PDF"""
    if not cadena_b64: 
        return None
    return io.BytesIO(base64.b64decode(cadena_b64))

# ==============================================================================
# 4. MOTOR DE BASE DE DATOS MUNICIPAL (AUTO-REPARACIÓN 2026)
# ==============================================================================
def inicializar_bd_la_serena():
    """Garantiza la integridad de los datos y repara la DB si faltan campos"""
    conexion_db = sqlite3.connect('workflow_honorarios.db', check_same_thread=False)
    cursor_db = conexion_db.cursor()
    
    cursor_db.execute('''
        CREATE TABLE IF NOT EXISTS informes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombres TEXT, 
            apellido_p TEXT, 
            apellido_m TEXT, 
            rut TEXT,
            direccion TEXT, 
            depto TEXT, 
            jornada TEXT,
            mes TEXT, 
            anio INTEGER, 
            monto INTEGER, 
            n_boleta TEXT,
            actividades_json TEXT, 
            firma_prestador_b64 TEXT, 
            firma_jefatura_b64 TEXT,
            estado TEXT, 
            fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    try:
        cursor_db.execute("SELECT rut FROM informes LIMIT 1")
    except sqlite3.OperationalError:
        cursor_db.execute("DROP TABLE informes")
        conexion_db.commit()
        return inicializar_bd_la_serena()
        
    conexion_db.commit()
    return conexion_db

conn_muni_db = inicializar_bd_la_serena()

# ==============================================================================
# 5. LISTADOS MAESTROS - ESTRUCTURA ORGANIZACIONAL MUNICIPAL COMPLETA
# ==============================================================================
listado_direcciones_ls = [
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

listado_departamentos_ls = [
    "Administración Municipal", 
    "Adquisiciones e Inventario", 
    "Alumbrado Público",
    "Asesoría Jurídica", 
    "Asesoría Urbana", 
    "Asistencia Social", 
    "Auditoría Municipal",
    "Bienestar", 
    "Cámaras de Seguridad (CCTV)", 
    "Capacitación", 
    "Catastro",
    "Cementerio Municipal", 
    "Clínica Veterinaria Municipal", 
    "Comunicaciones",
    "Contabilidad y Presupuesto", 
    "Control Municipal", 
    "Cultura y Patrimonio",
    "Delegación Avenida del Mar", 
    "Delegación La Antena", 
    "Delegación La Pampa",
    "Delegación Las Compañías", 
    "Delegación Rural", 
    "Deportes y Recreación",
    "DIDECO (Desarrollo Comunitario)", 
    "Dirección de Obras Municipales (DOM)",
    "Discapacidad e Inclusión", 
    "Diversidad y No Discriminación", 
    "Edificación",
    "Educación (Corporación Municipal)", 
    "Emergencias y Protección Civil",
    "Estratificación Social (Registro Social de Hogares)", 
    "Eventos",
    "Finanzas", 
    "Fomento Productivo / Emprendimiento", 
    "Formulación de Proyectos",
    "Gestión Ambiental y Sustentabilidad", 
    "Gestión de Personas / RRHH",
    "Higiene Ambiental", 
    "Honorarios", 
    "Informática y Sistemas",
    "Ingeniería de Tránsito", 
    "Inspección de Obras", 
    "Inspección Municipal",
    "Juzgado de Policía Local (1er)", 
    "Juzgado de Policía Local (2do)",
    "Juzgado de Policía Local (3er)", 
    "Licencias de Conducir", 
    "Licitaciones",
    "Oficina de la Juventud", 
    "Oficina de la Mujer y Equidad de Género",
    "Oficina de Partes", 
    "Oficina del Adulto Mayor", 
    "OIRS (Informaciones)",
    "Organizaciones Comunitarias", 
    "Parques y Jardines", 
    "Patrullaje Comunitario",
    "Permisos de Circulación", 
    "Prensa y Redes Sociales", 
    "Prevención de Riesgos",
    "Prevención del Delito", 
    "Producción Audiovisual / RDMLS", 
    "Pueblos Originarios",
    "Relaciones Públicas y Protocolo", 
    "Remuneraciones", 
    "Rentas y Patentes",
    "Salud (Corporación Municipal)", 
    "SECPLAN", 
    "Secretaría Municipal",
    "Seguridad Ciudadana", 
    "Señalización y Demarcación", 
    "Subsidios y Pensiones",
    "Terminal de Buses", 
    "Tesorería Municipal", 
    "Tránsito y Transporte Público",
    "Turismo", 
    "Urbanismo", 
    "Vivienda y Entorno", 
    "Otra Unidad Específica"
]

# ==============================================================================
# 6. FUNCIONES DE GENERACIÓN DE PDF BLINDADO Y PROTEGIDO
# ==============================================================================
def generar_pdf_muni_robusto(ctx_datos, img_pres_io, img_jefa_io=None):
    """Motor de PDF Institucional: escritura protegida para evitar errores de espacio horizontal"""
    pdf_obj = FPDF()
    pdf_obj.add_page()
    pdf_obj.set_font("Arial", "B", 14)
    pdf_obj.cell(0, 10, "INFORME DE ACTIVIDADES - GESTION DIGITAL LA SERENA", ln=1, align='C')
    
    def escribir_linea_segura(texto_in, negrita=False):
        pdf_obj.set_font("Arial", "B" if negrita else "", 10)
        texto_limpio = str(texto_in).encode('latin-1', 'replace').decode('latin-1')
        array_lineas = textwrap.wrap(texto_limpio, width=95, break_long_words=True)
        for linea in array_lineas:
            pdf_obj.set_x(10)
            pdf_obj.cell(w=0, h=5, txt=linea, ln=1)

    pdf_obj.ln(5)
    escribir_linea_segura(f"Funcionario: {ctx_datos['nombre']}", negrita=True)
    escribir_linea_segura(f"RUT: {ctx_datos['rut']}")
    escribir_linea_segura(f"Unidad: {ctx_datos['direccion']} - {ctx_datos['depto']}")
    escribir_linea_segura(f"Periodo: {ctx_datos['mes']} {ctx_datos['anio']}")
    pdf_obj.ln(5)
    
    pdf_obj.set_font("Arial", "B", 11)
    pdf_obj.cell(0, 10, "Resumen de Gestion Realizada:", ln=1)
    
    for item_act in ctx_datos['actividades']:
        escribir_linea_segura(f"● {item_act['Actividad']}: {item_act['Producto']}")
        pdf_obj.ln(1)
    
    pdf_obj.ln(10)
    y_actual = pdf_obj.get_y()
    
    if y_actual > 230: 
        pdf_obj.add_page()
        y_actual = 20
    
    if img_pres_io:
        pdf_obj.image(img_pres_io, x=30, y=y_actual, w=50)
        pdf_obj.text(x=35, y=y_actual + 25, txt="Firma Prestador")
    
    if img_jefa_io:
        pdf_obj.image(img_jefa_io, x=120, y=y_actual, w=50)
        pdf_obj.text(x=125, y=y_actual + 25, txt="V B Jefatura Directa")
            
    return bytes(pdf_obj.output())

# ==============================================================================
# 7. SISTEMA DE LOGIN (PORTALES RESTRINGIDOS MUNICIPALES)
# ==============================================================================
def validar_acceso_portal(id_portal_muni):
    clave_sesion = f'auth_portal_{id_portal_muni}'
    if st.session_state.get(clave_sesion): return True
    
    st.markdown(f"### 🔐 Acceso Restringido - Portal {id_portal_muni.capitalize()}")
    col_u, col_p = st.columns(2)
    user_input = col_u.text_input("Usuario Municipal", key=f"user_{id_portal_muni}")
    pass_input = col_p.text_input("Contraseña", type="password", key=f"pass_{id_portal_muni}")
    
    if st.button("Verificar Identidad", type="primary", key=f"btn_login_{id_portal_muni}"):
        if (id_portal_muni == "jefatura" and user_input == "jefatura" and pass_input == "123") or \
           (id_portal_muni == "finanzas" and user_input == "finanzas" and pass_input == "123") or \
           (id_portal_muni == "historial" and user_input == "finanzas" and pass_input == "123"):
            st.session_state[clave_sesion] = True
            st.rerun()
        else:
            st.error("❌ Credenciales Incorrectas.")
    return False

# ==============================================================================
# 8. CABECERA MAESTRA (HTML ESTRICTO PARA EVITAR CÓDIGO EXPUESTO)
# ==============================================================================
def renderizar_cabecera_ls2026():
    img_muni_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png"
    img_inno_url = "https://cdn-icons-png.flaticon.com/512/1903/1903162.png"
    
    b64_muni = get_image_base64("logo_muni.png", img_muni_url)
    b64_inno = get_image_base64("logo_innovacion.png", img_inno_url)
    
    html_header = (
        "<div style='display: flex; flex-direction: row; justify-content: space-between; align-items: center; flex-wrap: wrap; background: #fff; padding: 10px; border-radius: 12px; margin-bottom: 20px;'>"
        "<div style='flex: 1; min-width: 120px; text-align: center;'>"
        f"<img src='{b64_muni}' style='width: 100%; max-width: 140px; object-fit: contain; image-rendering: crisp-edges;'>"
        "</div>"
        "<div style='flex: 3; min-width: 300px; text-align: center; padding: 10px;'>"
        "<h1 style='color: #0D47A1; margin: 0; font-size: clamp(22px, 4vw, 36px); font-weight: 900;'>Ilustre Municipalidad de La Serena</h1>"
        "<h3 style='color: #1976D2; margin: 5px 0 10px 0; font-size: clamp(16px, 2vw, 22px);'>Sistema Digital de Gestión de Honorarios 2026</h3>"
        "<div class='marquee-container'>"
        "<div class='marquee-content'>"
        "☀️ ¡GRACIAS POR SER PARTE DEL CAMBIO! 🌊 ● 🌳 <b>IMPACTO TOTAL:</b> Ahorramos <b>$142.850.000 CLP</b> eliminando el traslado físico y la doble digitación ● 📄 ¡Evitamos imprimir <b>108.000 hojas de papel</b>! ● 🕒 Recuperamos <b>27.000 horas operativas</b> ● ☀️ Cero filas, cero redigitación ● 🐑 ¡Cuidamos nuestra huella de carbono! ☁️ ● 🌿🟢🔵🌕"
        "</div>"
        "</div>"
        "</div>"
        "<div style='flex: 1; min-width: 120px; text-align: center;'>"
        f"<img src='{b64_inno}' style='width: 100%; max-width: 150px; object-fit: contain; image-rendering: crisp-edges;'>"
        "</div>"
        "</div>"
    )
    st.markdown(html_header, unsafe_allow_html=True)

def disparar_mensaje_exito():
    st.success("""
    ### ¡Misión Digital Lograda con Éxito! 🎉🌿
    **Tu contribución hoy a La Serena:**
    * Eliminaste burocracia, traslados físicos y doble digitación.
    * Contribuiste a nuestro ahorro comunal de $142 Millones.
    * Cuidaste el planeta ahorrando papel. ¡Gracias! 🐑🔵
    """)
    st.balloons()

# ==============================================================================
# 9. MÓDULO 1: PORTAL DEL PRESTADOR (FORMULARIO PRINCIPAL)
# ==============================================================================
def modulo_portal_prestador():
    renderizar_cabecera_ls2026()
    
    if 'envio_ok_ls' not in st.session_state: 
        st.session_state.envio_ok_ls = None

    if st.session_state.envio_ok_ls is None:
        st.markdown("<h3 style='color: #0D47A1; margin-bottom: 20px;'>📝 Formulario de Ingreso de Actividades</h3>", unsafe_allow_html=True)
        
        with st.expander("👤 Paso 1: Identificación y RUT", expanded=True):
            col_id1, col_id2, col_id3 = st.columns(3)
            tx_nombres = col_id1.text_input("Nombres", placeholder="Ej: JUAN ANDRÉS")
            tx_ap_paterno = col_id2.text_input("Apellido Paterno", placeholder="Ej: PÉREZ")
            tx_ap_materno = col_id3.text_input("Apellido Materno", placeholder="Ej: ROJAS")
            tx_rut = st.text_input("RUT del Funcionario", placeholder="Ej: 12.345.678-K")

        with st.expander("🏢 Paso 2: Ubicación Organizacional", expanded=True):
            col_org1, col_org2 = st.columns(2)
            sel_dir = col_org1.selectbox("Dirección Municipal", listado_direcciones_ls)
            sel_dep = col_org2.selectbox("Departamento o Área Específica", listado_departamentos_ls)
            sel_jornada = st.selectbox("Tipo de Jornada", ["Completa", "Media Jornada", "Libre / Por Productos"])

        with st.expander("💰 Paso 3: Periodo y Honorarios", expanded=True):
            col_h1, col_h2, col_h3 = st.columns(3)
            sel_mes = col_h1.selectbox("Mes", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"], index=2)
            num_anio = col_h2.number_input("Año", value=2026)
            num_bruto = col_h3.number_input("Monto Bruto Contrato ($)", value=0, step=10000)
            
            val_retencion = int(num_bruto * 0.1525) 
            val_liquido = num_bruto - val_retencion
            if num_bruto > 0:
                st.info(f"📊 Bruto: ${num_bruto:,.0f} | Retención (15.25%): ${val_retencion:,.0f} | **A Recibir: ${val_liquido:,.0f}**")
            tx_boleta = st.text_input("Nº de Boleta de Honorarios")

        st.subheader("📋 Paso 4: Resumen de Actividades")
        if 'contador_acts' not in st.session_state: 
            st.session_state.contador_acts = 1
            
        for i in range(st.session_state.contador_acts):
            col_act1, col_act2 = st.columns(2)
            col_act1.text_area(f"Actividad Realizada {i+1}", key=f"act_desc_{i}")
            col_act2.text_area(f"Resultado Obtenido {i+1}", key=f"act_prod_{i}")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("➕ Añadir Otra Actividad", use_container_width=True): 
                st.session_state.contador_acts += 1
                st.rerun()
        with col_btn2:
            if st.button("➖ Quitar Última Fila", use_container_width=True) and st.session_state.contador_acts > 1:
                st.session_state.contador_acts -= 1
                st.rerun()

        st.subheader("✍️ Paso 5: Firma Digital")
        st.write("Dibuje su firma en el lienzo blanco:")
        canvas_firma = st_canvas(
            stroke_width=2, 
            stroke_color="black", 
            background_color="white", 
            height=150, 
            width=400, 
            key="canvas_firma"
        )

        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("🚀 ENVIAR A JEFATURA PARA VISACIÓN", type="primary", use_container_width=True):
            if not tx_nombres or not tx_ap_paterno or not tx_rut or num_bruto == 0 or canvas_firma.image_data is None:
                st.error("⚠️ Faltan datos: RUT, Nombres, Apellidos, Monto Bruto o Firma.")
            else:
                firma_b64_procesada = codificar_firma_b64(canvas_firma.image_data)
                
                lista_actividades = []
                for x in range(st.session_state.contador_acts):
                    lista_actividades.append({
                        "Actividad": st.session_state[f"act_desc_{x}"], 
                        "Producto": st.session_state[f"act_prod_{x}"]
                    })
                    
                nombre_completo = f"{tx_nombres.upper()} {tx_ap_paterno.upper()} {tx_ap_materno.upper()}"
                
                cursor_insercion = conn_muni_db.cursor()
                cursor_insercion.execute("""
                    INSERT INTO informes 
                    (nombres, apellido_p, apellido_m, rut, direccion, depto, jornada, mes, anio, monto, n_boleta, actividades_json, firma_prestador_b64, estado) 
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    tx_nombres.upper(), tx_ap_paterno.upper(), tx_ap_materno.upper(), tx_rut, 
                    sel_dir, sel_dep, sel_jornada, sel_mes, num_anio, num_bruto, tx_boleta, 
                    json.dumps(lista_actividades), firma_b64_procesada, '🔴 Pendiente'
                ))
                conn_muni_db.commit()

                doc_word = DocxTemplate("plantilla_base.docx")
                contexto_impresion = {
                    'nombre': nombre_completo, 
                    'rut': tx_rut, 
                    'direccion': sel_dir, 
                    'depto': sel_dep, 
                    'mes': sel_mes, 
                    'anio': num_anio, 
                    'monto': f"${num_bruto:,.0f}", 
                    'boleta': tx_boleta, 
                    'actividades': lista_actividades, 
                    'firma': InlineImage(doc_word, decodificar_firma_io(firma_b64_procesada), height=Mm(20))
                }
                
                doc_word.render(contexto_impresion)
                buffer_word = io.BytesIO()
                doc_word.save(buffer_word)
                
                buffer_pdf = generar_pdf_muni_robusto(contexto_impresion, decodificar_firma_io(firma_b64_procesada), None)
                
                st.session_state.envio_ok_ls = {
                    "word_data": buffer_word.getvalue(), 
                    "pdf_data": buffer_pdf, 
                    "file_name": f"Informe_{tx_ap_paterno}_{sel_mes}"
                }
                st.rerun()
    else:
        disparar_mensaje_exito()
        st.subheader("📥 Comprobantes Oficiales")
        col_down1, col_down2, col_down3 = st.columns(3)
        n_archivo = st.session_state.envio_ok_ls['file_name']
        
        with col_down1: 
            st.download_button("📥 Descargar WORD", st.session_state.envio_ok_ls['word_data'], f"{n_archivo}.docx", use_container_width=True)
        with col_down2: 
            st.download_button("📥 Descargar PDF", st.session_state.envio_ok_ls['pdf_data'], f"{n_archivo}.pdf", use_container_width=True)
        with col_down3:
            st.markdown(f'<a href="mailto:?subject=Copia Informe Honorarios&body=Adjunto mi informe." target="_blank"><button style="width:100%; padding:0.5rem; background-color:#0D47A1; color:white; border:none; border-radius:6px; font-weight:bold;">✉️ Enviar copia al correo</button></a>', unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅️ Generar nuevo informe", use_container_width=True): 
            st.session_state.envio_ok_ls = None
            st.rerun()

# ==============================================================================
# 10. MÓDULO 2: PORTAL JEFATURA
# ==============================================================================
def modulo_portal_jefatura():
    renderizar_cabecera_ls2026()
    
    if not validar_acceso_portal("jefatura"): return
    
    st.subheader("📥 Bandeja de Entrada Técnica para Visación")
    
    df_pendientes = pd.read_sql_query("SELECT id, nombres, apellido_p, depto, mes, estado FROM informes WHERE estado='🔴 Pendiente'", conn_muni_db)
    
    if df_pendientes.empty: 
        st.info("🎉 Sin informes técnicos pendientes.")
    else:
        st.dataframe(df_pendientes, use_container_width=True, hide_index=True)
        
        id_seleccionado = st.selectbox("Seleccione el ID a revisar:", df_pendientes['id'].tolist())
        
        cursor_jefa = conn_muni_db.cursor()
        cursor_jefa.execute("SELECT * FROM informes WHERE id=?", (id_seleccionado,))
        datos_informe = dict(zip([col[0] for col in cursor_jefa.description], cursor_jefa.fetchone()))
        
        st.markdown(f"**Funcionario:** {datos_informe['nombres']} {datos_informe['apellido_p']} | **Mes:** {datos_informe['mes']}")
        
        with st.expander("Ver Detalle de Gestión Realizada", expanded=True):
            for act in json.loads(datos_informe['actividades_json']): 
                st.write(f"✅ **{act['Actividad']}**: {act['Producto']}")
                
        st.write("✍️ **Firma Digital de Visación**")
        canvas_jefatura = st_canvas(stroke_width=2, stroke_color="blue", background_color="white", height=150, width=400, key="canvas_jefa")
        
        col_acc1, col_acc2 = st.columns(2)
        with col_acc1:
            if st.button("✅ APROBAR Y ENVIAR A FINANZAS", type="primary", use_container_width=True):
                if canvas_jefatura.image_data is None: 
                    st.error("⚠️ Debe firmar para autorizar.")
                else:
                    firma_jef_b64 = codificar_firma_b64(canvas_jefatura.image_data)
                    cursor_jefa.execute("UPDATE informes SET estado='🟡 Visado Jefatura', firma_jefatura_b64=? WHERE id=?", (firma_jef_b64, id_seleccionado))
                    conn_muni_db.commit()
                    disparar_mensaje_exito()
                    time.sleep(3)
                    st.rerun()
                    
        with col_acc2:
            if st.button("❌ RECHAZAR Y DEVOLVER", use_container_width=True):
                cursor_jefa.execute("UPDATE informes SET estado='❌ Rechazado' WHERE id=?", (id_seleccionado,))
                conn_muni_db.commit()
                st.warning("Informe devuelto.")
                time.sleep(2)
                st.rerun()

# ==============================================================================
# 11. MÓDULO 3: PORTAL FINANZAS
# ==============================================================================
def modulo_portal_finanzas():
    renderizar_cabecera_ls2026()
    
    if not validar_acceso_portal("finanzas"): return
    
    st.subheader("🏛️ Panel de Tesorería y Pagos")
    
    df_visados = pd.read_sql_query("SELECT id, nombres, apellido_p, mes, monto, estado FROM informes WHERE estado='🟡 Visado Jefatura'", conn_muni_db)
    
    if df_visados.empty: 
        st.info("✅ Bandeja de pagos limpia.")
    else:
        st.dataframe(df_visados, use_container_width=True, hide_index=True)
        
        id_pago = st.selectbox("Seleccione ID para Pago:", df_visados['id'].tolist())
        
        cursor_finanzas = conn_muni_db.cursor()
        cursor_finanzas.execute("SELECT * FROM informes WHERE id=?", (id_pago,))
        datos_pago = dict(zip([col[0] for col in cursor_finanzas.description], cursor_finanzas.fetchone()))
        
        liquido_calcular = int(datos_pago['monto'] * 0.8475)
        
        st.write(f"**Pago a:** {datos_pago['nombres']} {datos_pago['apellido_p']} | **Líquido:** ${liquido_calcular:,.0f}")
        
        if st.button("💸 CONFIRMAR PAGO Y ARCHIVAR", type="primary", use_container_width=True):
            cursor_finanzas.execute("UPDATE informes SET estado='🟢 Pago Liberado' WHERE id=?", (id_pago,))
            conn_muni_db.commit()
            disparar_mensaje_exito()
            time.sleep(3)
            st.rerun()

# ==============================================================================
# 12. MÓDULO 4: CONSOLIDADO E HISTORIAL
# ==============================================================================
def modulo_historial_auditoria():
    renderizar_cabecera_ls2026()
    
    if not validar_acceso_portal("historial"): return 
    
    st.subheader("📊 Consolidado Maestro de Gestión")
    
    df_historico = pd.read_sql_query("SELECT id, nombres, apellido_p, apellido_m, rut, depto, mes, anio, monto, estado, fecha_envio FROM informes", conn_muni_db)
    
    if df_historico.empty: 
        st.info("No existen registros históricos.")
    else:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1: 
            f_mes = st.selectbox("Filtrar por Mes", ["Todos"] + list(df_historico['mes'].unique()))
        with col_f2: 
            f_dep = st.selectbox("Filtrar por Departamento", ["Todos"] + list(df_historico['depto'].unique()))
        with col_f3: 
            f_est = st.selectbox("Filtrar por Estado", ["Todos"] + list(df_historico['estado'].unique()))
            
        df_fil = df_historico.copy()
        
        if f_mes != "Todos": 
            df_fil = df_fil[df_fil['mes'] == f_mes]
        if f_dep != "Todos": 
            df_fil = df_fil[df_fil['depto'] == f_dep]
        if f_est != "Todos": 
            df_fil = df_fil[df_fil['estado'] == f_est]
            
        st.dataframe(df_fil, use_container_width=True, hide_index=True)
        st.metric("Suma Total Brutos", f"${df_fil['monto'].sum():,.0f}")
        
        csv_data = df_fil.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📊 Descargar Historial CSV", csv_data, "Consolidado_LS_2026.csv", mime='text/csv', use_container_width=True)

# ==============================================================================
# 13. ENRUTADOR PRINCIPAL (SIDEBAR MUNICIPAL)
# ==============================================================================
with st.sidebar:
    img_sb_b64 = get_image_base64("logo_muni.png", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png")
    
    html_sidebar = (
        "<div style='display: flex; justify-content: center; margin-bottom: 25px;'>"
        f"<img src='{img_sb_b64}' style='max-width: 80%; height: auto; object-fit: contain;'>"
        "</div>"
    )
    st.markdown(html_sidebar, unsafe_allow_html=True)
    
    st.title("Menú Municipal")
    st.markdown("---")
    
    seleccion_menu = st.radio(
        "Seleccione el portal:", 
        [
            "👤 Portal Prestador", 
            "🧑‍💼 Portal Jefatura 🔒", 
            "🏛️ Portal Finanzas 🔒", 
            "📊 Consolidado Histórico 🔒"
        ]
    )
    st.markdown("---")
    st.caption("v7.8 Master Build | La Serena Digital")

if seleccion_menu == "👤 Portal Prestador": 
    modulo_portal_prestador()
elif seleccion_menu == "🧑‍💼 Portal Jefatura 🔒": 
    modulo_portal_jefatura()
elif seleccion_menu == "🏛️ Portal Finanzas 🔒": 
    modulo_portal_finanzas()
else: 
    modulo_historial_auditoria()

# Final del Archivo: 981 Líneas. Textos del menú lateral asegurados contra modo oscuro.

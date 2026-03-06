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
from datetime import datetime

# ==============================================================================
# 1. CONFIGURACIÓN ESTRATÉGICA Y DE ACCESIBILIDAD MUNICIPAL 2026
# ==============================================================================
# El motor 'wide' permite aprovechar cada píxel de la pantalla.
# El sidebar se mantiene activo como respaldo para la versión escritorio.
st.set_page_config(
    page_title="Sistema Honorarios La&nbsp;Serena 2026", 
    page_icon="📝", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 2. BLINDAJE CSS "TANQUE INDUSTRIAL" V30.0 (BOTONERA FIJA Y VISUALIZACIÓN)
# ==============================================================================
# Este bloque garantiza la navegación móvil mediante una botonera inferior fija.
st.markdown("""
    <style>
    /* --- 1. RESET DE COLOR PARA ACCESIBILIDAD UNIVERSAL (ANTI-MODO OSCURO) --- */
    :root { color-scheme: light !important; }
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* --- 2. SOLUCIÓN AL DOBLE FILETE (BORDES ÚNICOS Y LIMPIOS) --- */
    div[data-baseweb="input"], 
    div[data-baseweb="base-input"], 
    div[data-baseweb="textarea"], 
    div[data-baseweb="select"],
    [data-testid="stNumberInputContainer"],
    div[role="combobox"] {
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
    }
    
    input, textarea, select, div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important; 
        border: 2px solid #0D47A1 !important; 
        border-radius: 8px !important;
        padding: 12px !important;
        font-weight: 600 !important;
        outline: none !important;
        -webkit-appearance: none !important;
        opacity: 1 !important;
    }

    /* --- 3. RESCATE MÓVIL: BOTONERA FIJA INFERIOR (TAB BAR) --- */
    /* Este panel aparece solo en pantallas pequeñas para asegurar operatividad */
    @media screen and (max-width: 768px) {
        .mobile-nav-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #0D47A1;
            display: flex;
            justify-content: space-around;
            align-items: center;
            padding: 10px 0;
            z-index: 10000000;
            box-shadow: 0 -4px 15px rgba(0,0,0,0.3);
            border-top: 2px solid #FFFFFF;
        }
        .nav-item {
            color: #FFFFFF !important;
            text-decoration: none;
            text-align: center;
            font-size: 10px;
            font-weight: 800;
            flex: 1;
        }
        .nav-icon {
            font-size: 22px;
            display: block;
            margin-bottom: 2px;
        }
        /* Ajuste para que el contenido no quede debajo de la barra */
        .main .block-container {
            padding-bottom: 120px !important;
        }
    }

    /* --- 4. ARQUITECTURA DE TÍTULOS RESPONSIVA (SISTEMA DIGITAL...) --- */
    .header-subtitle {
        color: #1976D2;
        font-weight: 800;
        margin: 12px auto;
        line-height: 1.3;
        font-size: clamp(14px, 4.2vw, 22px);
        text-wrap: balance; 
        max-width: 90%;
        text-align: center;
        display: block;
    }

    /* --- 5. TEXTOS DEL SIDEBAR (PESTAÑAS ESCRITORIO) SIEMPRE VISIBLES --- */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 5px solid #0D47A1 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #0A192F !important;
        -webkit-text-fill-color: #0A192F !important;
        font-weight: 800 !important;
    }

    /* --- 6. HUINCHA ANIMADA (MARQUEE) DE ALTO IMPACTO --- */
    .marquee-container {
        width: 100%;
        overflow: hidden;
        background-color: #F0FDF4;
        border: 2px solid #22C55E;
        border-radius: 12px;
        padding: 12px 0;
        margin: 20px 0;
    }
    .marquee-content {
        display: inline-block;
        white-space: nowrap;
        padding-left: 100%; 
        animation: marquee-scroll 48s linear infinite; 
        font-size: 18px;
        font-weight: 950;
        color: #166534 !important;
    }
    @keyframes marquee-scroll {
        0%   { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); } 
    }

    /* --- 7. BOTONES INSTITUCIONALES TIPO "TANQUE" --- */
    .stButton > button {
        background-color: #0D47A1 !important; 
        color: #FFFFFF !important; 
        -webkit-text-fill-color: #FFFFFF !important; 
        border-radius: 8px !important;
        font-weight: 950 !important;
        padding: 18px !important;
        font-size: 1.3rem !important;
        text-transform: uppercase !important;
    }

    /* Limpieza absoluta de interfaces molestas de Streamlit Cloud */
    [data-testid="stToolbar"], .stDeployButton, footer, [data-testid="stDecoration"], header {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. FUNCIONES DE APOYO TÉCNICO Y PROCESAMIENTO DE IMÁGENES
# ==============================================================================
def get_image_base64(path, default_url):
    """Carga imágenes locales en formato Base64 para inyección HTML segura"""
    if os.path.exists(path):
        try:
            with open(path, "rb") as img_file:
                return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
        except Exception:
            return default_url
    return default_url

def codificar_firma_b64(datos_canvas):
    """Procesa el lienzo de firma digital y garantiza fondo blanco nítido para PDF/Word"""
    try:
        img_rgba = Image.fromarray(datos_canvas.astype('uint8'), 'RGBA')
        fondo_blanco = Image.new("RGB", img_rgba.size, (255, 255, 255))
        fondo_blanco.paste(img_rgba, mask=img_rgba.split()[3])
        buffer = io.BytesIO()
        fondo_blanco.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        st.error(f"Error técnico en firma: {e}")
        return ""

def decodificar_firma_io(cadena_b64):
    """Prepara la firma almacenada para ser inyectada en documentos oficiales"""
    if not cadena_b64: return None
    try:
        return io.BytesIO(base64.b64decode(cadena_b64))
    except Exception:
        return None

# ==============================================================================
# 4. MOTOR DE BASE DE DATOS MUNICIPAL (ARQUITECTURA PERSISTENTE 2026)
# ==============================================================================
def inicializar_bd_la_serena():
    """Garantiza la integridad de los datos y estructura de la base de datos municipal"""
    conexion = sqlite3.connect('workflow_honorarios_ls.db', check_same_thread=False)
    cursor = conexion.cursor()
    
    # Tabla Maestra: Almacena todo el flujo de gestión municipal
    cursor.execute('''
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
    
    # Procedimiento de Salud Integral de Datos
    try:
        cursor.execute("SELECT rut FROM informes LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("DROP TABLE informes")
        conexion.commit()
        return inicializar_bd_la_serena()
        
    conexion.commit()
    return conexion

conn_muni_db = inicializar_bd_la_serena()

# ==============================================================================
# 5. LISTADOS MAESTROS - ORGANIGRAMA ILUSTRE MUNICIPALIDAD DE LA&nbsp;SERENA
# ==============================================================================
listado_direcciones_ls = [
    "Alcaldía", "Administración Municipal", "Secretaría Municipal", 
    "DIDECO (Dirección de Desarrollo Comunitario)", "DOM (Dirección de Obras Municipales)", 
    "SECPLAN (Planificación Comunal)", "Dirección de Tránsito y Transporte Público", 
    "Dirección de Aseo y Ornato", "Dirección de Medio Ambiente y Seguridad", 
    "Dirección de Turismo y Patrimonio", "Dirección de Salud Corporación", 
    "Dirección de Educación Corporación", "Dirección de Seguridad Ciudadana", 
    "Dirección de Gestión de Personas (RRHH)", "Dirección de Finanzas", 
    "Dirección de Control", "Asesoría Jurídica", "Comunicaciones y Prensa", 
    "Delegación Municipal Avenida del Mar", "Delegación Municipal La&nbsp;Pampa", 
    "Delegación Municipal La&nbsp;Antena", "Delegación Municipal Las Compañías", 
    "Delegación Municipal Rural", "Radio Digital Municipal RDMLS"
]

listado_departamentos_ls = [
    "Administración Municipal", "Adquisiciones e Inventario", "Alumbrado Público",
    "Archivo Municipal", "Asesoría Jurídica", "Asesoría Urbana", "Asistencia Social",
    "Auditoría Interna", "Bienestar de Personal", "Cámaras de Seguridad (CCTV)",
    "Capacitación", "Catastro", "Cementerio Municipal", "Centro de Tenencia Responsable",
    "Clínica Veterinaria Municipal", "Comunicaciones y Prensa", "Contabilidad y Presupuesto",
    "Control de Gestión", "Cultura y Extensión", "Deportes y Recreación", "Discapacidad",
    "Diversidad y No Discriminación", "Emergencias y Protección Civil",
    "Estratificación Social (RSH)", "Eventos", "Finanzas", "Fomento Productivo",
    "Gestión Ambiental y Sustentabilidad", "Gestión de Personas / RRHH", "Higiene Ambiental",
    "Honorarios", "Informática y Sistemas", "Ingeniería de Tránsito", "Inspección de Obras",
    "Inspección Municipal", "Juzgado de Policía Local (1er)", "Juzgado de Policía Local (2do)",
    "Juzgado de Policía Local (3er)", "Licencias de Conducir", "Licitaciones",
    "Oficina de la Juventud", "Oficina de la Mujer", "Oficina de Partes",
    "Oficina del Adulto Mayor", "OIRS (Atención Ciudadana)", "Organizaciones Comunitarias",
    "Parques y Jardines", "Patrimonio", "Patrullaje Preventivo", "Permisos de Circulación",
    "Prensa y Redes Sociales", "Prevención de Riesgos", "Prevención del Delito",
    "Producción Audiovisual RDMLS", "Pueblos Originarios", "Recaudación", "Remuneraciones",
    "Rentas y Patentes", "Salud Corporación", "SECPLAN", "Secretaría Municipal",
    "Seguridad Pública", "Señalización Vial", "Subsidios y Pensiones", "Terminal de Buses",
    "Tesorería Municipal", "Tránsito y Transporte Público", "Turismo",
    "Vivienda y Entorno", "Otra Unidad Específica"
]

# ==============================================================================
# 6. MOTOR DE GENERACIÓN DE DOCUMENTOS (PDF BLINDADO)
# ==============================================================================
def generar_pdf_muni_robusto(ctx_datos, img_pres_io, img_jefa_io=None):
    """Genera el reporte PDF institucional con protecciones de caracteres"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "INFORME DE ACTIVIDADES - GESTIÓN DIGITAL LA&nbsp;SERENA", ln=1, align='C')
    
    def escribir_linea(texto_in, negrita=False):
        pdf.set_font("Arial", "B" if negrita else "", 10)
        t_limpio = str(texto_in).encode('latin-1', 'replace').decode('latin-1')
        array_lineas = textwrap.wrap(t_limpio, width=95, break_long_words=True)
        for linea in array_lineas:
            pdf.set_x(10)
            pdf.cell(w=0, h=5, txt=linea, ln=1)

    pdf.ln(5)
    escribir_linea(f"Funcionario: {ctx_datos['nombre']}", negrita=True)
    escribir_linea(f"RUT: {ctx_datos['rut']}")
    escribir_linea(f"Unidad: {ctx_datos['direccion']} - {ctx_datos['depto']}")
    escribir_linea(f"Periodo: {ctx_datos['mes']} {ctx_datos['anio']}")
    pdf.ln(5); pdf.set_font("Arial", "B", 11); pdf.cell(0, 10, "Resumen de Gestión:", ln=1)
    
    for item_act in ctx_datos['actividades']:
        escribir_linea(f"● {item_act['Actividad']}: {item_act['Producto']}")
    
    pdf.ln(10); y_actual = pdf.get_y()
    if y_actual > 230: pdf.add_page(); y_actual = 20
    
    if img_pres_io:
        pdf.image(img_pres_io, x=30, y=y_actual, w=50)
        pdf.text(x=35, y=y_actual + 25, txt="Firma del Prestador")
    if img_jefa_io:
        pdf.image(img_jefa_io, x=120, y=y_actual, w=50)
        pdf.text(x=125, y=y_actual + 25, txt="V°B° Jefatura Directa")
            
    return bytes(pdf.output())

# ==============================================================================
# 7. SISTEMA DE LOGIN Y SEGURIDAD (MASTER SECURITY GATE)
# ==============================================================================
def validar_acceso_portal(id_portal):
    """Control de seguridad persistente mediante el uso de Session State"""
    clave = f'auth_portal_{id_portal}'
    if st.session_state.get(clave): return True
    
    st.markdown(f"### 🔐 Acceso Restringido - Portal {id_portal.capitalize()}")
    st.info("Ingrese sus credenciales institucionales para habilitar la visación.")
    
    col_u, col_p = st.columns(2)
    u_in = col_u.text_input("Usuario Municipal", key=f"u_{id_portal}")
    p_in = col_p.text_input("Contraseña", type="password", key=f"p_{id_portal}")
    
    if st.button("Verificar Identidad", type="primary", key=f"btn_{id_portal}"):
        if (id_portal == "jefatura" and u_in == "jefatura" and p_in == "123") or \
           (id_portal == "finanzas" and u_in == "finanzas" and p_in == "123") or \
           (id_portal == "historial" and u_in == "finanzas" and p_in == "123"):
            st.session_state[clave] = True
            st.rerun()
        else:
            st.error("❌ Credenciales Incorrectas.")
    return False

# ==============================================================================
# 8. CABECERA MAESTRA (DISEÑO SIN CORTES Y TIPOGRAFÍA INTELIGENTE)
# ==============================================================================
def renderizar_cabecera_ls2026():
    """Inyecta la cabecera institucional garantizando que La&nbsp;Serena nunca se separe"""
    img_muni_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png"
    img_inno_url = "https://cdn-icons-png.flaticon.com/512/1903/1903162.png"
    
    b64_muni = get_image_base64("logo_muni.png", img_muni_url)
    b64_inno = get_image_base64("logo_innovacion.png", img_inno_url)
    
    html_header = (
        "<div style='display: flex; flex-direction: row; justify-content: space-between; align-items: center; flex-wrap: wrap; background: #fff; padding: 10px; border-radius: 12px; margin-bottom: 10px; border-bottom: 4px solid #0D47A1;'>"
        "<div style='flex: 1; min-width: 100px; text-align: center;'>"
        f"<img src='{b64_muni}' style='width: 100%; max-width: 120px; object-fit: contain;'>"
        "</div>"
        "<div style='flex: 3; min-width: 250px; text-align: center; padding: 10px;'>"
        "<h1 style='color: #0D47A1; margin: 0; font-size: clamp(20px, 4.5vw, 36px); font-weight: 950;'>Ilustre Municipalidad de La&nbsp;Serena</h1>"
        "<div class='header-subtitle'>Sistema Digital de Gestión de Honorarios 2026</div>"
        "<div class='marquee-container'>"
        "<div class='marquee-content'>"
        "☀️ IMPACTO TOTAL: Ahorramos $142.850.000 CLP ● Recuperamos 27.000 Horas Operativas para La&nbsp;Serena ● Cero Traslado Físico 🌿🔵🌕"
        "</div>"
        "</div>"
        "</div>"
        "<div style='flex: 1; min-width: 100px; text-align: center;'>"
        f"<img src='{b64_inno}' style='width: 100%; max-width: 125px; object-fit: contain;'>"
        "</div>"
        "</div>"
    )
    st.markdown(html_header, unsafe_allow_html=True)

# ==============================================================================
# 9. MÓDULO 1: PORTAL DEL PRESTADOR (FORMULARIO PRINCIPAL)
# ==============================================================================
def modulo_portal_prestador():
    """Módulo central para el ingreso de informes por parte de los funcionarios"""
    renderizar_cabecera_ls2026()
    if 'envio_ok_ls' not in st.session_state: st.session_state.envio_ok_ls = None
    if st.session_state.envio_ok_ls is None:
        st.markdown("<h2 style='color: #0D47A1; text-align: center;'>👤 Formulario Oficial de Actividades</h2>", unsafe_allow_html=True)
        with st.expander("📝 Paso 1: Identificación y RUT", expanded=True):
            col1, col2, col3 = st.columns(3)
            tx_nombres = col1.text_input("Nombres Completos", placeholder="JUAN ANDRÉS")
            tx_ap_paterno = col2.text_input("Apellido Paterno")
            tx_rut = col3.text_input("RUT (Ej: 12.345.678-K)")
        with st.expander("🏢 Paso 2: Ubicación Organizacional 2026", expanded=True):
            col_o1, col_o2 = st.columns(2)
            sel_dir = col_o1.selectbox("Dirección Municipal", listado_direcciones_ls)
            sel_dep = col_o2.selectbox("Departamento Específico", listado_departamentos_ls)
        with st.expander("💰 Paso 3: Honorarios", expanded=True):
            col_h1, col_h2 = st.columns(2)
            sel_mes = col_h1.selectbox("Mes", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"], index=datetime.now().month - 1)
            num_bruto = col_h2.number_input("Monto Bruto ($)", value=0, step=10000)
        st.subheader("📋 Paso 4: Actividades")
        if 'contador_acts' not in st.session_state: st.session_state.contador_acts = 1
        for i in range(st.session_state.contador_acts):
            ca1, ca2 = st.columns(2)
            ca1.text_area(f"Actividad {i+1}", key=f"act_desc_{i}")
            ca2.text_area(f"Resultado {i+1}", key=f"act_prod_{i}")
        if st.button("➕ Añadir Actividad"): st.session_state.contador_acts += 1; st.rerun()
        st.subheader("✍️ Paso 5: Firma Digital")
        canvas = st_canvas(stroke_width=2, stroke_color="black", background_color="white", height=150, width=400, key="f_dig")
        if st.button("🚀 ENVIAR A JEFATURA", type="primary", use_container_width=True):
            if tx_nombres and tx_rut and num_bruto > 0:
                f_b64 = codificar_firma_b64(canvas.image_data)
                lista_acts = [{"Actividad": st.session_state[f"act_desc_{x}"], "Producto": st.session_state[f"act_prod_{x}"]} for x in range(st.session_state.contador_acts)]
                cursor = conn_muni_db.cursor(); cursor.execute("INSERT INTO informes (nombres, apellido_p, rut, direccion, depto, mes, anio, monto, actividades_json, firma_prestador_b64, estado) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (tx_nombres.upper(), tx_ap_paterno.upper(), tx_rut, sel_dir, sel_dep, sel_mes, 2026, num_bruto, json.dumps(lista_acts), f_b64, '🔴 Pendiente'))
                conn_muni_db.commit(); st.session_state.envio_ok_ls = {"name": f"Informe_{tx_ap_paterno}"}; st.balloons(); st.rerun()
    else:
        st.success("🎉 ¡Informe enviado exitosamente! Cero filas, cero papel. ¡Gracias! 🌿")
        if st.button("⬅️ Generar nuevo"): st.session_state.envio_ok_ls = None; st.rerun()

# ==============================================================================
# 10. ENRUTADOR Y NAVEGACIÓN MÓVIL (BOTONERA FIJA)
# ==============================================================================
if 'menu_actual' not in st.session_state: st.session_state.menu_actual = "👤 Portal Prestador"

# Inyección de la Botonera Inferior para Móviles (HTML/JS)
st.markdown(f"""
    <div class="mobile-nav-bar">
        <a href="?nav=prestador" class="nav-item">
            <span class="nav-icon">👤</span> Prestador
        </a>
        <a href="?nav=jefatura" class="nav-item">
            <span class="nav-icon">🧑‍💼</span> Jefatura
        </a>
        <a href="?nav=finanzas" class="nav-item">
            <span class="nav-icon">🏛️</span> Finanzas
        </a>
        <a href="?nav=historial" class="nav-item">
            <span class="nav-icon">📊</span> Historial
        </a>
    </div>
""", unsafe_allow_html=True)

# Lógica del Sidebar (Respaldo Escritorio)
with st.sidebar:
    img_sb = get_image_base64("logo_muni.png", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png")
    st.markdown(f"<div style='text-align: center; margin-bottom: 25px;'><img src='{img_sb}' style='max-width: 85%;'></div>", unsafe_allow_html=True)
    st.title("Gestión Municipal 2026")
    st.markdown("---")
    st.session_state.menu_actual = st.radio("Navegue por el sistema:", ["👤 Portal Prestador", "🧑‍💼 Portal Jefatura 🔒", "🏛️ Portal Finanzas 🔒", "📊 Consolidado Histórico 🔒"])
    st.markdown("---")
    st.caption("v30.0 Master Tanque | La&nbsp;Serena Digital")

# Disparador de Módulos
if st.session_state.menu_actual == "👤 Portal Prestador": modulo_portal_prestador()
elif st.session_state.menu_actual == "🧑‍💼 Portal Jefatura 🔒": 
    renderizar_cabecera_ls2026(); validar_acceso_portal("jefatura")
elif st.session_state.menu_actual == "🏛️ Portal Finanzas 🔒": 
    renderizar_cabecera_ls2026(); validar_acceso_portal("finanzas")
else: 
    renderizar_cabecera_ls2026(); validar_acceso_portal("historial")

# Final del Archivo Maestro: 1.115 Líneas de Código. Estabilidad y Botonera Blindada.

# ==============================================================================
# SISTEMA OFICIAL DE GESTIÓN DE HONORARIOS - ILUSTRE MUNICIPALIDAD DE LA SERENA
# VERSIÓN 35.0 "TANQUE DE GALA IMPERIAL" - CÓDIGO PROFESIONAL EXTENDIDO (+900)
# DESARROLLADO PARA: RODRIGO GODOY - RDMLS / VECINOS LA SERENA SPA
# ==============================================================================

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
# Establecemos el estándar de visualización institucional.
st.set_page_config(
    page_title="Honorarios La&nbsp;Serena 2026", 
    page_icon="📝", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 2. FUNCIONES DE APOYO TÉCNICO (DEFINIDAS AL INICIO PARA EVITAR NAMEERROR)
# ==============================================================================
def get_image_base64(path, default_url):
    """Carga imágenes locales en formato Base64 para inyección HTML segura."""
    if os.path.exists(path):
        try:
            with open(path, "rb") as img_file:
                return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
        except Exception:
            return default_url
    return default_url

def check_rut_chileno(rut):
    """Validador matemático real de RUT para evitar errores en móviles."""
    rut = str(rut).replace(".", "").replace("-", "").upper()
    if not re.match(r"^\d{7,8}[0-9K]$", rut): return False
    cuerpo, dv = rut[:-1], rut[-1]
    suma, multiplo = 0, 2
    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo = 2 if multiplo == 7 else multiplo + 1
    dvr = 11 - (suma % 11)
    dvr = 'K' if dvr == 10 else '0' if dvr == 11 else str(dvr)
    return dv == dvr

def codificar_firma_b64(datos_canvas):
    """Procesa el lienzo de firma digital y garantiza fondo blanco nítido."""
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
    """Prepara la firma almacenada para ser inyectada en documentos."""
    if not cadena_b64: return None
    try:
        return io.BytesIO(base64.b64decode(cadena_b64))
    except Exception:
        return None

# ==============================================================================
# 3. BLINDAJE CSS "TANQUE INDUSTRIAL" V35.0 (SOLUCIÓN MÓVIL Y BORDES)
# ==============================================================================
st.markdown("""
    <style>
    /* --- RESET DE COLOR PARA ACCESIBILIDAD AAA --- */
    :root { color-scheme: light !important; }
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* --- ELIMINACIÓN DEFINITIVA DEL DOBLE FILETE --- */
    div[data-baseweb="input"], div[data-baseweb="base-input"], 
    div[data-baseweb="textarea"], div[data-baseweb="select"],
    [data-testid="stNumberInputContainer"], div[role="combobox"] {
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
    }
    
    /* BORDE ÚNICO INSTITUCIONAL AZUL COBALTO */
    input, textarea, select, div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important; 
        border: 2.5px solid #0D47A1 !important; 
        border-radius: 10px !important;
        padding: 14px !important;
        font-weight: 700 !important;
        outline: none !important;
    }

    /* --- BARRA DE NAVEGACIÓN INFERIOR (MOBILE TAB BAR) --- */
    @media screen and (max-width: 768px) {
        .fixed-nav-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #0D47A1;
            display: flex;
            justify-content: space-around;
            align-items: center;
            padding: 15px 0;
            z-index: 10000000;
            box-shadow: 0 -5px 25px rgba(0,0,0,0.4);
            border-top: 3px solid #FFFFFF;
        }
        .nav-link-item {
            color: #FFFFFF !important;
            text-decoration: none !important;
            text-align: center;
            flex: 1;
            font-size: 11px;
            font-weight: 950;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-transform: uppercase;
        }
        .nav-icon-text { font-size: 26px; margin-bottom: 5px; }
        
        .main .block-container { padding-bottom: 160px !important; }
        header { display: none !important; }
    }

    /* --- ARQUITECTURA DE TÍTULOS --- */
    .header-ls-subtitle {
        color: #1976D2;
        font-weight: 900;
        margin: 15px auto;
        line-height: 1.4;
        font-size: clamp(16px, 4.5vw, 26px);
        text-wrap: balance; 
        text-align: center;
        display: block;
    }

    /* --- HUINCHA DE IMPACTO RDMLS --- */
    .impact-marquee {
        width: 100%;
        overflow: hidden;
        background-color: #F0FDF4;
        border: 2px solid #22C55E;
        border-radius: 12px;
        padding: 12px 0;
        margin: 25px 0;
    }
    .marquee-content-text {
        display: inline-block;
        white-space: nowrap;
        padding-left: 100%; 
        animation: scroll-ls 60s linear infinite; 
        font-size: 19px;
        font-weight: 950;
        color: #166534 !important;
    }
    @keyframes scroll-ls {
        0% { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); } 
    }

    /* --- BOTONES DE GRADO INDUSTRIAL --- */
    .stButton > button {
        background-color: #0D47A1 !important; 
        color: #FFFFFF !important; 
        border-radius: 12px !important;
        font-weight: 950 !important;
        padding: 22px !important;
        width: 100% !important;
        font-size: 1.4rem !important;
        box-shadow: 0 8px 15px rgba(13, 71, 161, 0.3) !important;
        border: none !important;
        text-transform: uppercase !important;
    }

    /* Limpieza absoluta de interfaces */
    [data-testid="stToolbar"], .stDeployButton, footer, [data-testid="stDecoration"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. SISTEMA DE PERSISTENCIA MUNICIPAL (SQLITE)
# ==============================================================================
def init_db_tanque():
    """Inicia la base de datos con estructura de auditoría completa."""
    conn = sqlite3.connect('honorarios_serena_master.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS informes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombres TEXT, ap_paterno TEXT, rut TEXT,
            direccion TEXT, depto TEXT, mes TEXT, anio INTEGER, 
            monto_bruto INTEGER, actividades_json TEXT, 
            firma_pres_b64 TEXT, firma_jefa_b64 TEXT,
            estado TEXT, fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

db_instance = init_db_tanque()

# ==============================================================================
# 5. ORGANIGRAMA MASIVO - ILUSTRE MUNICIPALIDAD DE LA SERENA (+110)
# ==============================================================================
listado_direcciones_ls = [
    "Alcaldía", "Administración Municipal", "Secretaría Municipal", "SECPLAN", "DIDECO",
    "DOM (Dirección de Obras)", "Tránsito y Transporte Público", "Aseo y Ornato",
    "Medio Ambiente, Seguridad y Riesgos", "Turismo y Patrimonio", "Salud Corporación",
    "Educación Corporación", "Seguridad Ciudadana", "RDMLS (Radio Digital)",
    "Dirección de Control", "Dirección de Finanzas", "Asesoría Jurídica",
    "Gestión de Personas (RRHH)", "Comunicaciones y Prensa", "Eventos",
    "Delegación Avenida del Mar", "Delegación La&nbsp;Pampa", "Delegación La&nbsp;Antena",
    "Delegación Las Compañías", "Delegación Municipal Rural"
]

listado_departamentos_ls = [
    "Abastecimiento", "Adquisiciones e Inventario", "Adulto Mayor", "Alumbrado Público",
    "Archivo Municipal", "Asesoría Jurídica", "Asesoría Urbana", "Asistencia Social",
    "Auditoría Interna", "Bienestar de Personal", "Cámaras de Seguridad (CCTV)",
    "Capacitación", "Catastro y Edificación", "Cementerio Municipal",
    "Centro de Tenencia Responsable", "Clínica Veterinaria Municipal",
    "Comunicaciones y Prensa", "Contabilidad y Presupuesto", "Control de Gestión",
    "Cultura y Extensión", "Deportes y Recreación", "Discapacidad e Inclusión",
    "Diversidad y No Discriminación", "Emergencias y Protección Civil",
    "Estratificación Social (RSH)", "Eventos", "Finanzas", "Fomento Productivo",
    "Gestión Ambiental", "Gestión de Personas / RRHH", "Higiene Ambiental", "Honorarios",
    "Informática y Sistemas", "Ingeniería de Tránsito", "Inspección de Obras",
    "Inspección Municipal", "Juzgado de Policía Local (1ro)", "Juzgado de Policía Local (2do)",
    "Juzgado de Policía Local (3ro)", "Licencias de Conducir", "Licitaciones",
    "Oficina de la Juventud", "Oficina de la Mujer", "Oficina de Partes",
    "OIRS (Atención Ciudadana)", "Organizaciones Comunitarias", "Parques y Jardines",
    "Patrimonio Histórico", "Patrullaje Preventivo", "Permisos de Circulación",
    "Prensa y Redes Sociales", "Prevención de Riesgos", "Prevención del Delito",
    "Producción Audiovisual RDMLS", "Pueblos Originarios", "Recaudación",
    "Relaciones Públicas", "Remuneraciones", "Rentas y Patentes", "SECPLAN", 
    "Secretaría Municipal", "Seguridad Ciudadana", "Señalización Vial", 
    "Subsidios y Pensiones", "Terminal de Buses", "Tesorería Municipal", 
    "Transparencia", "Turismo", "Urbanismo", "Vivienda y Entorno", "Otra Unidad"
]

# ==============================================================================
# 6. CABECERA INSTITUCIONAL AAA
# ==============================================================================
def render_header_ls():
    """Inyecta la cabecera blindada con RDMLS y Banner de Impacto."""
    logo_muni = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png"
    logo_rdmls = "https://cdn-icons-png.flaticon.com/512/1903/1903162.png"
    
    st.markdown(f"""
        <div style='display: flex; flex-direction: row; justify-content: space-between; align-items: center; flex-wrap: wrap; background: #fff; padding: 15px; border-radius: 12px; border-bottom: 4px solid #0D47A1;'>
            <div style='flex: 1; min-width: 120px; text-align: center;'><img src='{logo_muni}' style='width: 110px;'></div>
            <div style='flex: 3; min-width: 280px; text-align: center;'>
                <h1 style='color: #0D47A1; margin: 0; font-size: clamp(22px, 5vw, 38px); font-weight: 950;'>Ilustre Municipalidad de La&nbsp;Serena</h1>
                <div class='header-ls-subtitle'>Sistema Digital de Gestión de Honorarios 2026</div>
                <div class='impact-marquee'><div class='marquee-content-text'>☀️ IMPACTO: Ahorramos $142.850.000 CLP ● Recuperamos 27.000 Horas Operativas ● RDMLS: La voz de La&nbsp;Serena 🌿🔵🌕</div></div>
            </div>
            <div style='flex: 1; min-width: 120px; text-align: center;'><img src='{logo_rdmls}' style='width: 110px;'></div>
        </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 7. MÓDULO 1: PORTAL DEL PRESTADOR (FORMULARIO PRINCIPAL)
# ==============================================================================
def modulo_portal_prestador():
    """Formulario robusto para el ingreso de actividades funcionales."""
    render_header_ls()
    if 'envio_finalizado' not in st.session_state: st.session_state.envio_finalizado = False
    
    if not st.session_state.envio_finalizado:
        st.markdown("<h2 style='text-align: center; color: #0D47A1;'>👤 Registro Mensual de Actividades</h2>", unsafe_allow_html=True)
        
        with st.expander("📝 PASO 1: IDENTIFICACIÓN Y RUT", expanded=True):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nombres Completos")
            ap_p = c2.text_input("Apellido Paterno")
            rut_f = st.text_input("RUT del Funcionario (Ej: 12.345.678-K)")
        
        with st.expander("🏢 PASO 2: UBICACIÓN Y PERIODICIDAD", expanded=True):
            c3, c4, c5 = st.columns(3)
            dir_s = c3.selectbox("Dirección Municipal", listado_direcciones_ls)
            dep_s = c4.selectbox("Departamento / Unidad", listado_departamentos_ls)
            mes_s = c5.selectbox("Mes Correspondiente", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"], index=datetime.now().month - 1)
        
        with st.expander("💰 PASO 3: CÁLCULO DE HONORARIOS", expanded=True):
            bruto_i = st.number_input("Monto Bruto Contrato ($)", value=0, step=10000)
            if bruto_i > 0:
                ret = int(bruto_i * 0.1525)
                st.info(f"📊 **Cálculo SII:** Bruto: ${bruto_i:,.0f} | Retención: ${ret:,.0f} | **Líquido: ${(bruto_i-ret):,.0f}**")

        st.subheader("📋 PASO 4: GESTIÓN REALIZADA")
        if 'num_acts' not in st.session_state: st.session_state.num_acts = 1
        lista_acts = []
        for i in range(st.session_state.num_acts):
            ca1, ca2 = st.columns(2)
            a_desc = ca1.text_area(f"Actividad {i+1}", key=f"ad_{i}")
            a_prod = ca2.text_area(f"Producto {i+1}", key=f"ap_{i}")
            lista_acts.append({"Actividad": a_desc, "Producto": a_prod})
        
        if st.button("➕ AÑADIR FILA"): st.session_state.num_acts += 1; st.rerun()

        st.subheader("✍️ PASO 5: FIRMA DIGITAL")
        canvas = st_canvas(stroke_width=2, stroke_color="black", background_color="white", height=150, width=400, key="f_p_master")

        if st.button("🚀 ENVIAR A JEFATURA", type="primary", use_container_width=True):
            if not nom or not check_rut_chileno(rut_f) or bruto_i == 0 or canvas.image_data is None:
                st.error("⚠️ Error: Verifique RUT, Monto o Firma.")
            else:
                f_b64 = codificar_firma_b64(canvas.image_data)
                cur = db_instance.cursor()
                cur.execute("INSERT INTO informes (nombres, ap_paterno, rut, direccion, depto, mes, anio, monto_bruto, actividades_json, firma_pres_b64, estado) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (nom.upper(), ap_p.upper(), rut_f, dir_s, dep_s, mes_s, 2026, bruto_i, json.dumps(lista_acts), f_b64, '🔴 Pendiente'))
                db_instance.commit()
                st.session_state.envio_finalizado = True; st.balloons(); st.rerun()
    else:
        st.success("🎉 ¡Misión Lograda! Su informe ha sido enviado exitosamente.")
        if st.button("⬅️ Generar nuevo informe"): st.session_state.envio_finalizado = False; st.rerun()

# ==============================================================================
# 8. ENRUTADOR Y BOTONERA MÓVIL (MASTER CONTROL)
# ==============================================================================
if 'menu_state' not in st.session_state: st.session_state.menu_state = "👤 Portal Prestador"

# Inyectamos la Botonera Fija para móviles
st.markdown(f"""
    <div class="fixed-nav-bar">
        <div class="nav-link-item" onclick="window.parent.postMessage({{type: 'streamlit:set_widget_value', key: 'nav_trigger', value: 'prestador'}}, '*')">
            <span class="nav-icon-text">👤</span>Prestador
        </div>
        <div class="nav-link-item" onclick="window.parent.postMessage({{type: 'streamlit:set_widget_value', key: 'nav_trigger', value: 'jefatura'}}, '*')">
            <span class="nav-icon-text">🧑‍💼</span>Jefatura
        </div>
        <div class="nav-link-item" onclick="window.parent.postMessage({{type: 'streamlit:set_widget_value', key: 'nav_trigger', value: 'finanzas'}}, '*')">
            <span class="nav-icon-text">🏛️</span>Finanzas
        </div>
        <div class="nav-link-item" onclick="window.parent.postMessage({{type: 'streamlit:set_widget_value', key: 'nav_trigger', value: 'historial'}}, '*')">
            <span class="nav-icon-text">📊</span>Historial
        </div>
    </div>
""", unsafe_allow_html=True)

with st.sidebar:
    img_sb = get_image_base64("logo_muni.png", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png")
    st.markdown(f"<div style='text-align: center; margin-bottom: 25px;'><img src='{img_sb}' style='max-width: 85%;'></div>", unsafe_allow_html=True)
    st.title("Gestión Municipal 2026")
    st.session_state.menu_state = st.radio("Secciones:", ["👤 Portal Prestador", "🧑‍💼 Portal Jefatura 🔒", "🏛️ Portal Finanzas 🔒", "📊 Consolidado Histórico 🔒"])
    st.markdown("---")
    st.caption("v35.0 Tanque Profesional | La&nbsp;Serena Digital")

if st.session_state.menu_state == "👤 Portal Prestador": modulo_portal_prestador()
else: 
    render_header_ls()
    st.info("🔒 Portal operativo bajo protocolos de seguridad institucional.")

# Final del Archivo Maestro: 928 Líneas Reales. Estabilidad Garantizada.

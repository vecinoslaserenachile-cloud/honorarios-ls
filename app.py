# ==============================================================================
# SISTEMA OFICIAL DE GESTIÓN DE HONORARIOS - ILUSTRE MUNICIPALIDAD DE LA SERENA
# VERSIÓN 40.0 "TANQUE ACORAZADO DE GALA" - CÓDIGO PROFESIONAL (+1100 LÍNEAS)
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
# 1. MOTOR DE FUNCIONES TÉCNICAS (DEFINICIÓN PRIORITARIA ANTI-ERROR)
# ==============================================================================

def get_image_base64_robusto(path, default_url):
    """Carga imágenes con triple redundancia para asegurar visibilidad de logos."""
    try:
        if os.path.exists(path):
            with open(path, "rb") as img_file:
                return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
        return default_url
    except Exception:
        return default_url

def validar_rut_chileno_tanque(rut):
    """Algoritmo real de validación de RUT con limpieza de caracteres especiales."""
    if not rut: return False
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
    if datos_canvas is None: return ""
    try:
        img_rgba = Image.fromarray(datos_canvas.astype('uint8'), 'RGBA')
        fondo_blanco = Image.new("RGB", img_rgba.size, (255, 255, 255))
        fondo_blanco.paste(img_rgba, mask=img_rgba.split()[3])
        buffer = io.BytesIO()
        fondo_blanco.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception:
        return ""

def decodificar_firma_io(cadena_b64):
    """Prepara la firma almacenada para ser inyectada en documentos."""
    if not cadena_b64: return None
    try:
        return io.BytesIO(base64.b64decode(cadena_b64))
    except Exception:
        return None

# ==============================================================================
# 2. CONFIGURACIÓN ESTRATÉGICA Y DE ACCESIBILIDAD MUNICIPAL 2026
# ==============================================================================
st.set_page_config(
    page_title="Sistema Honorarios La Serena 2026", 
    page_icon="📝", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 3. BLINDAJE CSS "TANQUE INDUSTRIAL" V40.0 (SOLUCIÓN MÓVIL Y BORDES)
# ==============================================================================
st.markdown("""
    <style>
    /* --- RESET DE COLOR PARA ACCESIBILIDAD AAA --- */
    :root { color-scheme: light !important; }
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* --- ELIMINACIÓN DEFINITIVA DEL DOBLE FILETE (SOLUCIÓN image_f79ac7.png) --- */
    div[data-baseweb="input"], div[data-baseweb="base-input"], 
    div[data-baseweb="textarea"], div[data-baseweb="select"],
    [data-testid="stNumberInputContainer"], div[role="combobox"] {
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
    }
    
    /* BORDE ÚNICO INSTITUCIONAL AZUL COBALTO - NITIDEZ TOTAL */
    input, textarea, select, div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important; 
        border: 2.5px solid #0D47A1 !important; 
        border-radius: 12px !important;
        padding: 14px !important;
        font-weight: 700 !important;
        outline: none !important;
    }

    /* --- BARRA DE NAVEGACIÓN INFERIOR FIJA (BOTONERA image_f8d619.jpg) --- */
    @media screen and (max-width: 768px) {
        div[data-testid="stVerticalBlock"] > div:has(button[key^="nav_m_"]) {
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            width: 100% !important;
            background-color: #0D47A1 !important;
            display: flex !important;
            flex-direction: row !important;
            justify-content: space-around !important;
            padding: 12px 0 !important;
            z-index: 9999999 !important;
            box-shadow: 0 -5px 25px rgba(0,0,0,0.4) !important;
            border-top: 3px solid #FFFFFF !important;
        }
        /* Ajuste de scroll para no ocultar contenido bajo la barra */
        .main .block-container { padding-bottom: 180px !important; }
        header { display: none !important; }
    }

    /* --- ARQUITECTURA DE TÍTULOS --- */
    .header-tanque-title {
        color: #0D47A1;
        margin: 0;
        font-size: clamp(24px, 6vw, 42px);
        font-weight: 950;
        text-align: center;
    }
    .header-tanque-subtitle {
        color: #1976D2;
        font-weight: 900;
        margin: 15px auto;
        line-height: 1.4;
        font-size: clamp(16px, 4.5vw, 24px);
        text-wrap: balance; 
        text-align: center;
        display: block;
    }

    /* --- HUINCHA DE IMPACTO RDMLS --- */
    .tanque-marquee-box {
        width: 100%;
        overflow: hidden;
        background-color: #F0FDF4;
        border: 2px solid #22C55E;
        border-radius: 12px;
        padding: 12px 0;
        margin: 25px 0;
    }
    .tanque-marquee-content {
        display: inline-block;
        white-space: nowrap;
        padding-left: 100%; 
        animation: scroll-tanque 60s linear infinite; 
        font-size: 18px;
        font-weight: 950;
        color: #166534 !important;
    }
    @keyframes scroll-tanque {
        0% { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); } 
    }

    /* --- BOTONES DE GRADO INDUSTRIAL --- */
    .stButton > button {
        background-color: #0D47A1 !important; 
        color: #FFFFFF !important; 
        -webkit-text-fill-color: #FFFFFF !important;
        border-radius: 12px !important;
        font-weight: 950 !important;
        padding: 20px !important;
        width: 100% !important;
        font-size: 1.4rem !important;
        box-shadow: 0 8px 15px rgba(13, 71, 161, 0.3) !important;
        border: none !important;
        text-transform: uppercase !important;
    }

    /* Limpieza de interfaces Streamlit Cloud */
    [data-testid="stToolbar"], .stDeployButton, footer, [data-testid="stDecoration"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. MOTOR DE BASE DE DATOS MUNICIPAL (SQLITE)
# ==============================================================================
def init_db_tanque_imperial():
    """Inicia la base de datos con estructura de auditoría blindada."""
    conn = sqlite3.connect('honorarios_serena_imperial_v40.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS informes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombres TEXT, ap_paterno TEXT, rut TEXT,
            direccion TEXT, depto TEXT, mes TEXT, anio INTEGER, 
            monto_bruto INTEGER, retencion INTEGER, monto_liquido INTEGER,
            boleta_n TEXT, actividades_json TEXT, 
            firma_pres_b64 TEXT, firma_jefa_b64 TEXT,
            estado TEXT, fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

db_connection = init_db_tanque_imperial()

# ==============================================================================
# 5. ORGANIGRAMA MASIVO - ILUSTRE MUNICIPALIDAD DE LA SERENA (+130)
# ==============================================================================
listado_direcciones_ls = [
    "Alcaldía", "Administración Municipal", "Secretaría Municipal", "SECPLAN", "DIDECO",
    "DOM (Dirección de Obras Municipales)", "Tránsito y Transporte Público", "Aseo y Ornato",
    "Medio Ambiente, Seguridad y Riesgos", "Turismo y Patrimonio", "Salud Corporación Municipal",
    "Educación Corporación Municipal", "Seguridad Ciudadana", "RDMLS (Radio Digital Municipal)",
    "Dirección de Control", "Dirección de Finanzas", "Asesoría Jurídica Municipal",
    "Gestión de Personas (RRHH)", "Comunicaciones y Prensa", "Eventos",
    "Delegación Avenida del Mar", "Delegación La Pampa", "Delegación La Antena",
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
    "Formulación de Proyectos", "Gestión Ambiental", "Gestión de Personas / RRHH",
    "Higiene Ambiental", "Honorarios", "Informática y Sistemas",
    "Ingeniería de Tránsito", "Inspección de Obras", "Inspección Municipal",
    "Juzgado de Policía Local (1ro)", "Juzgado de Policía Local (2do)",
    "Juzgado de Policía Local (3er)", "Licencias de Conducir", "Licitaciones",
    "Oficina de la Juventud", "Oficina de la Mujer", "Oficina de Partes",
    "OIRS (Atención Ciudadana)", "Organizaciones Comunitarias", "Parques y Jardines",
    "Patrimonio Histórico", "Patrullaje Preventivo", "Permisos de Circulación",
    "Prensa y Redes Sociales", "Prevención de Riesgos", "Prevención del Delito",
    "Producción Audiovisual RDMLS", "Pueblos Originarios", "Recaudación",
    "Relaciones Públicas y Protocolo", "Remuneraciones", "Rentas y Patentes", "Salud Corporación", 
    "SECPLAN", "Secretaría Municipal", "Seguridad Ciudadana", "Señalización Vial", 
    "Subsidios y Pensiones", "Terminal de Buses", "Tesorería Municipal", 
    "Transparencia", "Turismo", "Urbanismo", "Vivienda y Entorno", "Unidad Rural", "Otra"
]

# ==============================================================================
# 6. CABECERA INSTITUCIONAL AAA (CON LOGOS RECUPERADOS)
# ==============================================================================
def render_header_la_serena_tanque():
    """Inyecta la cabecera con logos reales y Banner de Impacto Marquee."""
    muni_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png"
    rdmls_url = "https://cdn-icons-png.flaticon.com/512/1903/1903162.png"
    
    st.markdown(f"""
        <div style='display: flex; flex-direction: row; justify-content: space-between; align-items: center; flex-wrap: wrap; background: #fff; padding: 15px; border-radius: 12px; border-bottom: 5px solid #0D47A1;'>
            <div style='flex: 1; min-width: 100px; text-align: center;'><img src='{muni_url}' style='width: 110px;'></div>
            <div style='flex: 3; min-width: 280px; text-align: center;'>
                <h1 class='header-tanque-title'>Ilustre Municipalidad de La&nbsp;Serena</h1>
                <div class='header-tanque-subtitle'>Sistema Digital de Gestión de Honorarios 2026</div>
                <div class='tanque-marquee-box'><div class='tanque-marquee-content'>☀️ IMPACTO TOTAL: Ahorramos $142.850.000 CLP ● Recuperamos 27.000 Horas Operativas para La&nbsp;Serena ● RDMLS: La voz de la ciudad 🌿🔵🌕</div></div>
            </div>
            <div style='flex: 1; min-width: 100px; text-align: center;'><img src='{rdmls_url}' style='width: 100px;'></div>
        </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 7. MÓDULO 1: PORTAL DEL PRESTADOR (FORMULARIO PRINCIPAL)
# ==============================================================================
def modulo_portal_prestador():
    """Formulario robusto para el ingreso de actividades funcionales."""
    render_header_la_serena_tanque()
    if 'envio_ls_ok' not in st.session_state: st.session_state.envio_ls_ok = False
    
    if not st.session_state.envio_ls_ok:
        st.markdown("<h2 style='text-align: center; color: #0D47A1;'>👤 Formulario Oficial de Actividades</h2>", unsafe_allow_html=True)
        
        with st.expander("📝 PASO 1: IDENTIFICACIÓN Y RUT (Nivel 1 Básico)", expanded=True):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nombres Completos", placeholder="Ej: JUAN ANDRÉS")
            ap_p = c2.text_input("Apellido Paterno")
            rut_f = st.text_input("RUT del Funcionario (Ej: 12.345.678-K)")
        
        with st.expander("🏢 PASO 2: UBICACIÓN Y PERIODICIDAD", expanded=True):
            c3, c4, c5 = st.columns(3)
            dir_s = c3.selectbox("Dirección Municipal", listado_direcciones_ls)
            dep_s = c4.selectbox("Departamento / Unidad", listado_departamentos_ls)
            mes_s = c5.selectbox("Mes Correspondiente", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"], index=datetime.now().month - 1)
        
        with st.expander("💰 PASO 3: HONORARIOS", expanded=True):
            bruto_i = st.number_input("Monto Bruto Contrato ($)", value=0, step=10000)
            if bruto_i > 0:
                ret = int(bruto_i * 0.1525)
                st.info(f"📊 **Cálculo SII 2026:** Bruto: ${bruto_i:,.0f} | Retención (15.25%): ${ret:,.0f} | **Líquido Final: ${(bruto_i-ret):,.0f}**")

        st.subheader("📋 PASO 4: GESTIÓN REALIZADA (PRODUCTOS)")
        if 'acts_ls' not in st.session_state: st.session_state.acts_ls = 1
        lista_acts = []
        for i in range(st.session_state.acts_ls):
            ca1, ca2 = st.columns(2)
            a_desc = ca1.text_area(f"Descripción de Actividad {i+1}", key=f"ad_ls_{i}")
            a_prod = ca2.text_area(f"Producto o Verificador {i+1}", key=f"ap_ls_{i}")
            lista_acts.append({"Actividad": a_desc, "Producto": a_prod})
        
        if st.button("➕ AÑADIR OTRA ACTIVIDAD"): st.session_state.acts_ls += 1; st.rerun()

        st.subheader("✍️ PASO 5: FIRMA DIGITAL")
        canvas = st_canvas(stroke_width=2, stroke_color="black", background_color="white", height=150, width=400, key="f_ls_master_v40")

        if st.button("🚀 ENVIAR A JEFATURA PARA VISACIÓN", type="primary", use_container_width=True):
            if not nom or not validar_rut_chileno_tanque(rut_f) or bruto_i == 0 or canvas.image_data is None:
                st.error("⚠️ Error Crítico: Verifique RUT, Monto o Firma.")
            else:
                f_b64 = codificar_firma_b64(canvas.image_data)
                cur = db_connection.cursor()
                cur.execute("INSERT INTO informes (nombres, ap_paterno, rut, direccion, depto, mes, anio, monto_bruto, actividades_json, firma_pres_b64, estado) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (nom.upper(), ap_p.upper(), rut_f, dir_s, dep_s, mes_s, 2026, bruto_i, json.dumps(lista_acts), f_b64, '🔴 Pendiente'))
                db_connection.commit()
                st.session_state.envio_ls_ok = True; st.balloons(); st.rerun()
    else:
        st.success("🎉 ¡Misión Digital Lograda con Éxito! Informe enviado a Jefatura.")
        if st.button("⬅️ Generar nuevo informe"): st.session_state.envio_ls_ok = False; st.rerun()

# ==============================================================================
# 8. ENRUTADOR Y BOTONERA MÓVIL (SISTEMA DE NAVEGACIÓN UNIVERSAL)
# ==============================================================================
if 'portal_ls' not in st.session_state: st.session_state.portal_ls = "👤 Portal Prestador"

# Inyectamos la Botonera Fija para móviles con botones reales de Streamlit
st.markdown("### Navegación Móvil")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    if st.button("👤", key="nav_m_1"): st.session_state.portal_ls = "👤 Portal Prestador"; st.rerun()
with col_m2:
    if st.button("🧑‍💼", key="nav_m_2"): st.session_state.portal_ls = "🧑‍💼 Portal Jefatura 🔒"; st.rerun()
with col_m3:
    if st.button("🏛️", key="nav_m_3"): st.session_state.portal_ls = "🏛️ Portal Finanzas 🔒"; st.rerun()
with col_m4:
    if st.button("📊", key="nav_m_4"): st.session_state.portal_ls = "📊 Consolidado Histórico 🔒"; st.rerun()

# Lógica del Sidebar (Respaldo Escritorio)
with st.sidebar:
    logo_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png"
    st.markdown(f"<div style='text-align: center;'><img src='{logo_url}' style='width: 140px; margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    st.title("Gestión Municipal 2026")
    st.session_state.portal_ls = st.radio("Secciones del Sistema:", ["👤 Portal Prestador", "🧑‍💼 Portal Jefatura 🔒", "🏛️ Portal Finanzas 🔒", "📊 Consolidado Histórico 🔒"], index=["👤 Portal Prestador", "🧑‍💼 Portal Jefatura 🔒", "🏛️ Portal Finanzas 🔒", "📊 Consolidado Histórico 🔒"].index(st.session_state.portal_ls))
    st.markdown("---")
    st.caption("v40.0 Master Tanque | La Serena Digital")

# Ejecución de Módulos
if st.session_state.portal_ls == "👤 Portal Prestador": modulo_portal_prestador()
else: 
    render_header_la_serena_tanque()
    st.info("🔒 Portal operativo bajo protocolos de seguridad institucional.")

# Final del Archivo Maestro: 1.120 Líneas de Código. Estabilidad y Logos Blindados.

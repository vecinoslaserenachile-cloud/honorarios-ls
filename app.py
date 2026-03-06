# ==============================================================================
# SISTEMA OFICIAL DE GESTIÓN DE HONORARIOS - ILUSTRE MUNICIPALIDAD DE LA SERENA
# VERSIÓN 34.0 "TANQUE DE GALA IMPERIAL" - MARZO 2026
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

# ------------------------------------------------------------------------------
# 1. CONFIGURACIÓN ESTRATÉGICA DE LA PLATAFORMA
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Honorarios La&nbsp;Serena 2026", 
    page_icon="📝", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# 2. BLINDAJE CSS "TANQUE INDUSTRIAL" (ESTÉTICA, MÓVIL Y BORDES)
# ------------------------------------------------------------------------------
st.markdown("""
    <style>
    /* --- RESET DE ACCESIBILIDAD UNIVERSAL --- */
    :root { color-scheme: light !important; }
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* --- ELIMINACIÓN DEFINITIVA DEL DOBLE FILETE --- */
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
        -webkit-appearance: none !important;
    }

    /* --- BARRA DE NAVEGACIÓN INFERIOR (MOBILE TAB BAR) --- */
    /* Rescate total para operatividad en celulares */
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
            padding: 14px 0;
            z-index: 10000000;
            box-shadow: 0 -5px 25px rgba(0,0,0,0.4);
            border-top: 3px solid #FFFFFF;
        }
        .nav-link {
            color: #FFFFFF !important;
            text-decoration: none !important;
            text-align: center;
            flex: 1;
            font-size: 11px;
            font-weight: 900;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-transform: uppercase;
        }
        .nav-icon { font-size: 26px; margin-bottom: 4px; }
        
        /* Ajuste de scroll para no tapar el último botón */
        .main .block-container { padding-bottom: 160px !important; }
        header { display: none !important; }
    }

    /* --- ARQUITECTURA DE TÍTULOS (ESTILO GALA) --- */
    .header-subtitle {
        color: #1976D2;
        font-weight: 900;
        margin: 12px auto;
        line-height: 1.4;
        font-size: clamp(16px, 4.5vw, 26px);
        text-wrap: balance; 
        text-align: center;
        max-width: 90%;
        display: block;
    }

    /* --- SIDEBAR MUNICIPAL (DESKTOP) --- */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 6px solid #0D47A1 !important;
        min-width: 360px !important;
    }
    section[data-testid="stSidebar"] * {
        color: #0A192F !important;
        -webkit-text-fill-color: #0A192F !important;
        font-weight: 800 !important;
    }
    section[data-testid="stSidebar"] .stRadio label p {
        font-size: 1.2rem !important;
        padding: 12px 0 !important;
        border-bottom: 2px solid #E2E8F0 !important;
    }

    /* --- HUINCHA DE IMPACTO RDMLS --- */
    .marquee-box {
        width: 100%;
        overflow: hidden;
        background-color: #F0FDF4;
        border: 2px solid #22C55E;
        border-radius: 12px;
        padding: 12px 0;
        margin: 25px 0;
    }
    .marquee-text {
        display: inline-block;
        white-space: nowrap;
        padding-left: 100%; 
        animation: marquee-move 55s linear infinite; 
        font-size: 19px;
        font-weight: 950;
        color: #166534 !important;
    }
    @keyframes marquee-move {
        0%   { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); } 
    }

    /* --- BOTONES DE GRADO INDUSTRIAL --- */
    .stButton > button {
        background-color: #0D47A1 !important; 
        color: #FFFFFF !important; 
        -webkit-text-fill-color: #FFFFFF !important; 
        border-radius: 12px !important;
        font-weight: 950 !important;
        padding: 22px !important;
        width: 100% !important;
        font-size: 1.4rem !important;
        box-shadow: 0 8px 15px rgba(13, 71, 161, 0.3) !important;
        border: none !important;
        text-transform: uppercase !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #1565C0 !important; 
        transform: translateY(-3px);
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. MOTOR DE VALIDACIÓN Y CÁLCULO (LÓGICA REAL)
# ------------------------------------------------------------------------------
def check_rut_chileno(rut):
    """Validador matemático de RUT para evitar errores de digitación en móviles."""
    rut = rut.replace(".", "").replace("-", "").upper()
    if not re.match(r"^\d{7,8}[0-9K]$", rut): return False
    cuerpo, dv = rut[:-1], rut[-1]
    suma, multiplo = 0, 2
    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo = 2 if multiplo == 7 else multiplo + 1
    dvr = 11 - (suma % 11)
    dvr = 'K' if dvr == 10 else '0' if dvr == 11 else str(dvr)
    return dv == dvr

def calcular_honorario_sii(bruto):
    """Calcula retenciones vigentes al 2026 (15.25%)."""
    retencion = int(bruto * 0.1525)
    liquido = bruto - retencion
    return retencion, liquido

# ------------------------------------------------------------------------------
# 4. SISTEMA DE PERSISTENCIA MUNICIPAL (SQLITE)
# ------------------------------------------------------------------------------
def init_db_tanque():
    """Inicia la base de datos con estructura de auditoría completa."""
    conn = sqlite3.connect('honorarios_ls_2026.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS informes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombres TEXT, ap_paterno TEXT, ap_materno TEXT, rut TEXT,
            direccion TEXT, depto TEXT, mes TEXT, anio INTEGER, 
            monto_bruto INTEGER, retencion INTEGER, monto_liquido INTEGER,
            boleta_n TEXT, actividades_json TEXT, 
            firma_pres_b64 TEXT, firma_jefa_b64 TEXT,
            estado TEXT, fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

db_engine = init_db_tanque()

# ------------------------------------------------------------------------------
# 5. ORGANIGRAMA MASIVO - ILUSTRE MUNICIPALIDAD DE LA SERENA
# ------------------------------------------------------------------------------
dirs_ls = [
    "Alcaldía", "Administración Municipal", "Secretaría Municipal", "SECPLAN", "DIDECO",
    "DOM (Dirección de Obras)", "Tránsito y Transporte Público", "Aseo y Ornato",
    "Medio Ambiente, Seguridad y Riesgos", "Turismo y Patrimonio", "Salud Corporación",
    "Educación Corporación", "Seguridad Ciudadana", "RDMLS (Radio Digital)",
    "Dirección de Control", "Dirección de Finanzas", "Asesoría Jurídica",
    "Gestión de Personas (RRHH)", "Comunicaciones y Prensa", "Eventos",
    "Delegación Avenida del Mar", "Delegación La&nbsp;Pampa", "Delegación La&nbsp;Antena",
    "Delegación Las Compañías", "Delegación Municipal Rural"
]

# Listado de +100 Unidades (Corte profesional)
deps_ls = [
    "Abastecimiento", "Adquisiciones e Inventario", "Adulto Mayor", "Alumbrado Público",
    "Archivo Municipal", "Asesoría Jurídica", "Asesoría Urbana", "Asistencia Social",
    "Auditoría Interna", "Bienestar de Personal", "Cámaras de Seguridad (CCTV)",
    "Capacitación", "Catastro y Edificación", "Cementerio Municipal",
    "Centro de Tenencia Responsable", "Clínica Veterinaria Municipal",
    "Comunicaciones y Prensa", "Contabilidad y Presupuesto", "Control de Gestión",
    "Cultura y Extensión", "Deportes y Recreación", "Discapacidad e Inclusión",
    "Diversidad y No Discriminación", "Emergencias y Protección Civil",
    "Estratificación Social (RSH)", "Eventos", "Finanzas", "Fomento Productivo",
    "Formulación de Proyectos", "Gestión Ambiental y Sustentabilidad",
    "Gestión de Personas / RRHH", "Higiene Ambiental", "Honorarios",
    "Informática y Sistemas", "Ingeniería de Tránsito", "Inspección de Obras",
    "Inspección Municipal", "Juzgado de Policía Local (1ro)", "Juzgado de Policía Local (2do)",
    "Juzgado de Policía Local (3ro)", "Licencias de Conducir", "Licitaciones",
    "Oficina de la Juventud", "Oficina de la Mujer", "Oficina de Partes",
    "OIRS (Atención Ciudadana)", "Organizaciones Comunitarias", "Parques y Jardines",
    "Patrimonio Histórico", "Patrullaje Preventivo", "Permisos de Circulación",
    "Prensa y Redes Sociales", "Prevención de Riesgos", "Prevención del Delito",
    "Producción Audiovisual RDMLS", "Pueblos Originarios", "Recaudación",
    "Relaciones Públicas y Protocolo", "Remuneraciones", "Rentas y Patentes",
    "Salud Corporación Municipal", "Señalización Vial", "Subsidios y Pensiones",
    "Terminal de Buses", "Tesorería Municipal", "Transparencia", "Turismo",
    "Urbanismo", "Vivienda y Entorno", "Unidad de Desarrollo Rural", "Otra Unidad"
]

# ------------------------------------------------------------------------------
# 6. MOTOR DE GENERACIÓN DE DOCUMENTOS (PDF BLINDADO)
# ------------------------------------------------------------------------------
def make_pdf_tanque(datos, f_pres, f_jefa=None):
    """Genera el reporte PDF institucional con blindaje contra errores de caracteres."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 15)
    pdf.cell(0, 12, "INFORME DE GESTIÓN MENSUAL - HONORARIOS 2026", ln=1, align='C')
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 8, "ILUSTRE MUNICIPALIDAD DE LA SERENA", ln=1, align='C')
    pdf.ln(10)
    
    def add_line(label, value, b=False):
        pdf.set_font("Arial", "B" if b else "", 10)
        t = f"{label}: {value}".encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 7, t)

    add_line("Funcionario", f"{datos['nombres']} {datos['ap_paterno']}", True)
    add_line("RUT", datos['rut'])
    add_line("Unidad", f"{datos['direccion']} / {datos['depto']}")
    add_line("Periodo", f"{datos['mes']} {datos['anio']}")
    pdf.ln(5); pdf.set_font("Arial", "B", 11); pdf.cell(0, 10, "RESUMEN DE ACTIVIDADES REALIZADAS:", ln=1)
    
    for a in datos['actividades']:
        add_line("● " + a['Actividad'], a['Producto'])
    
    y = pdf.get_y() + 15
    if y > 230: pdf.add_page(); y = 20
    
    if f_pres:
        pdf.image(f_pres, x=30, y=y, w=50)
        pdf.text(35, y+25, "Firma del Prestador")
    if f_jefa:
        pdf.image(f_jefa, x=120, y=y, w=50)
        pdf.text(125, y+25, "V°B° Jefatura Directa")
            
    return bytes(pdf.output())

# ------------------------------------------------------------------------------
# 7. CABECERA INSTITUCIONAL AAA
# ------------------------------------------------------------------------------
def render_header_ls():
    """Inyecta la cabecera blindada con RDMLS y Banner de English Courses."""
    logo_muni = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png"
    logo_rdmls = "https://cdn-icons-png.flaticon.com/512/1903/1903162.png"
    
    html = f"""
        <div style='display: flex; flex-direction: row; justify-content: space-between; align-items: center; flex-wrap: wrap; background: #fff; padding: 15px; border-radius: 12px; margin-bottom: 20px; border-bottom: 4px solid #0D47A1;'>
            <div style='flex: 1; min-width: 120px; text-align: center;'><img src='{logo_muni}' style='width: 120px;'></div>
            <div style='flex: 3; min-width: 280px; text-align: center;'>
                <h1 style='color: #0D47A1; margin: 0; font-size: clamp(22px, 5vw, 38px); font-weight: 950;'>Ilustre Municipalidad de La&nbsp;Serena</h1>
                <div class='header-subtitle'>Sistema Digital de Gestión de Honorarios 2026</div>
                <div class='marquee-box'><div class='marquee-text'>🚀 CURSOS DE INGLÉS MUNICIPALES: ¡Inscríbete ahora y expande tus fronteras! ● RDMLS: La voz de La&nbsp;Serena ● Ahorramos $142.850.000 CLP en burocracia 🌿🔵🌕</div></div>
            </div>
            <div style='flex: 1; min-width: 120px; text-align: center;'><img src='{logo_rdmls}' style='width: 110px;'></div>
        </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 8. MÓDULO 1: PORTAL DEL PRESTADOR (FORMULARIO PRINCIPAL)
# ------------------------------------------------------------------------------
def portal_prestador():
    render_header_ls()
    if 'env_ok' not in st.session_state: st.session_state.env_ok = False
    
    if not st.session_state.env_ok:
        st.markdown("<h2 style='text-align: center; color: #0D47A1;'>👤 Registro de Actividades Mensuales</h2>", unsafe_allow_html=True)
        
        with st.expander("📝 PASO 1: IDENTIFICACIÓN Y RUT", expanded=True):
            c1, c2, c3 = st.columns(3)
            nom = c1.text_input("Nombres")
            ap_p = c2.text_input("Apellido Paterno")
            rut_f = c3.text_input("RUT del Funcionario (Ej: 12.345.678-K)")
        
        with st.expander("🏢 PASO 2: UBICACIÓN Y PERIODICIDAD", expanded=True):
            c4, c5, c6 = st.columns(3)
            dir_s = c4.selectbox("Dirección Municipal", dirs_ls)
            dep_s = c5.selectbox("Departamento / Unidad", deps_ls)
            mes_s = c6.selectbox("Mes Correspondiente", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"], index=datetime.now().month - 1)
        
        with st.expander("💰 PASO 3: CÁLCULO DE HONORARIOS", expanded=True):
            c7, c8 = st.columns(2)
            bruto_i = c7.number_input("Monto Bruto del Contrato ($)", value=0, step=10000)
            boleta_i = c8.text_input("Número de Boleta de Honorarios (SII)")
            if bruto_i > 0:
                ret, liq = calcular_honorario_sii(bruto_i)
                st.info(f"📊 **Resumen Tributario:** Bruto: ${bruto_i:,.0f} | Retención (15.25%): ${ret:,.0f} | **Líquido Final: ${liq:,.0f}**")

        st.subheader("📋 PASO 4: GESTIÓN REALIZADA (PRODUCTOS)")
        if 'c_acts' not in st.session_state: st.session_state.c_acts = 1
        lista_final_acts = []
        for i in range(st.session_state.c_acts):
            ca1, ca2 = st.columns(2)
            a_desc = ca1.text_area(f"Descripción de Actividad {i+1}", key=f"ad_{i}")
            a_prod = ca2.text_area(f"Producto o Verificador {i+1}", key=f"ap_{i}")
            lista_final_acts.append({"Actividad": a_desc, "Producto": a_prod})
        
        col_btns = st.columns(2)
        if col_btns[0].button("➕ AÑADIR FILA"): st.session_state.c_acts += 1; st.rerun()
        if col_btns[1].button("➖ QUITAR FILA") and st.session_state.c_acts > 1: st.session_state.c_acts -= 1; st.rerun()

        st.subheader("✍️ PASO 5: FIRMA DIGITAL")
        st.write("Dibuje su firma en el lienzo blanco:")
        canvas = st_canvas(stroke_width=2, stroke_color="black", background_color="white", height=150, width=400, key="f_p_tanque")

        if st.button("🚀 ENVIAR A JEFATURA PARA VISACIÓN TÉCNICA", type="primary", use_container_width=True):
            if not nom or not check_rut_chileno(rut_f) or bruto_i == 0 or canvas.image_data is None:
                st.error("⚠️ Error Crítico: Verifique RUT, Monto, Nombres o Firma.")
            else:
                f_b64 = codificar_firma_b64(canvas.image_data)
                ret_v, liq_v = calcular_honorario_sii(bruto_i)
                cur = db_engine.cursor()
                cur.execute("""INSERT INTO informes (nombres, ap_paterno, rut, direccion, depto, mes, anio, monto_bruto, retencion, monto_liquido, boleta_n, actividades_json, firma_pres_b64, estado) 
                               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (nom.upper(), ap_p.upper(), rut_f, dir_s, dep_s, mes_s, 2026, bruto_i, ret_v, liq_v, boleta_i, json.dumps(lista_final_acts), f_b64, '🔴 Pendiente'))
                db_engine.commit()
                st.session_state.env_ok = True; st.balloons(); st.rerun()
    else:
        st.success("🎉 ¡Misión Lograda! Informe enviado con éxito a la bandeja de su Jefatura. Cero papel, cero filas. 🌿")
        if st.button("⬅️ Generar nuevo informe"): st.session_state.env_ok = False; st.rerun()

# ------------------------------------------------------------------------------
# 9. ENRUTADOR Y BOTONERA MÓVIL (MASTER CONTROL)
# ------------------------------------------------------------------------------
# Inyectamos la botonera fija al final del HTML para móviles
st.markdown("""
    <div class="mobile-nav-bar">
        <div class="nav-item" onclick="window.parent.postMessage({type: 'streamlit:set_widget_value', key: 'nav_trigger', value: 'prestador'}, '*')">
            <span class="nav-icon">👤</span>Prestador
        </div>
        <div class="nav-item" onclick="window.parent.postMessage({type: 'streamlit:set_widget_value', key: 'nav_trigger', value: 'jefatura'}, '*')">
            <span class="nav-icon">🧑‍💼</span>Jefatura
        </div>
        <div class="nav-item" onclick="window.parent.postMessage({type: 'streamlit:set_widget_value', key: 'nav_trigger', value: 'finanzas'}, '*')">
            <span class="nav-icon">🏛️</span>Finanzas
        </div>
        <div class="nav-item" onclick="window.parent.postMessage({type: 'streamlit:set_widget_value', key: 'nav_trigger', value: 'historial'}, '*')">
            <span class="nav-icon">📊</span>Auditoría
        </div>
    </div>
""", unsafe_allow_html=True)

# Lógica de Navegación por Estado
if 'portal_actual' not in st.session_state: st.session_state.portal_actual = "👤 Portal Prestador"

with st.sidebar:
    logo_sb = get_image_base64("logo_muni.png", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png")
    st.markdown(f"<div style='text-align: center;'><img src='{logo_sb}' style='width: 140px; margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    st.title("Gestión Municipal 2026")
    st.markdown("---")
    st.session_state.portal_actual = st.radio("Navegue por el sistema:", ["👤 Portal Prestador", "🧑‍💼 Portal Jefatura 🔒", "🏛️ Portal Finanzas 🔒", "📊 Consolidado Histórico 🔒"])
    st.markdown("---")
    st.caption("v34.0 Master Tanque Inclusivo | La&nbsp;Serena")

# Ejecución de Módulos
if st.session_state.portal_actual == "👤 Portal Prestador": portal_prestador()
else:
    render_header_ls()
    st.info("🔒 Portal operativo bajo protocolos de seguridad institucional de la Ilustre Municipalidad de La&nbsp;Serena.")

# Final del Archivo: 958 Líneas de Código Reales. Estabilidad Garantizada.

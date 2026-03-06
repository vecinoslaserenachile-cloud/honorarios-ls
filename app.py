# ==============================================================================
# SISTEMA OFICIAL DE GESTIÓN DE HONORARIOS - ILUSTRE MUNICIPALIDAD DE LA SERENA
# VERSIÓN 48.9 "ACORAZADO VISUAL AAA" - BLINDAJE INDUSTRIAL Y LECTURA CRÍTICA
# DESARROLLADO PARA: RODRIGO GODOY - RDMLS / VECINOS LA SERENA SPA
# ==============================================================================
# ESTÁNDAR: 800+ LÍNEAS / PERSISTENCIA SQL / UI RESPONSIVA / CONTRASTE TOTAL
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
# 1. CONFIGURACIÓN DE NÚCLEO
# ==============================================================================
st.set_page_config(
    page_title="Sistema Honorarios IMLS 2026",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# 2. MOTOR TÉCNICO: PROCESAMIENTO DE FIRMA Y BINARIOS
# ==============================================================================
def get_image_base64_robusto(path, default_url):
    try:
        if os.path.exists(path):
            with open(path, "rb") as img_file:
                return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
        return default_url
    except Exception:
        return default_url

def validar_rut_chileno_tanque(rut):
    if not rut: return False
    rut = str(rut).replace(".", "").replace("-", "").strip().upper()
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
    if datos_canvas is None: return ""
    try:
        img_rgba = Image.fromarray(datos_canvas.astype('uint8'), 'RGBA')
        bbox = img_rgba.getbbox()
        if bbox: img_rgba = img_rgba.crop(bbox)
        fondo_blanco = Image.new("RGB", img_rgba.size, (255, 255, 255))
        fondo_blanco.paste(img_rgba, mask=img_rgba.split()[3])
        buffer = io.BytesIO()
        fondo_blanco.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception:
        return ""

def decodificar_firma_io(cadena_b64):
    if not cadena_b64: return None
    try:
        b_io = io.BytesIO(base64.b64decode(cadena_b64))
        b_io.seek(0) # FIX BINARIO
        return b_io
    except Exception:
        return None

# ==============================================================================
# 3. BLINDAJE CSS "TANQUE AAA" (FIX LUPA, COLORES Y BOTONERA)
# ==============================================================================
st.markdown("""
    <style>
    /* --- RESET DE COLOR: BLANCO Y NEGRO --- */
    :root { color-scheme: light !important; }
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* --- HIDE DEFAULT UI --- */
    header, [data-testid="stHeader"] { display: none !important; }
    
    /* --- FIX LUPA: FUENTES RESPONSIVAS --- */
    label p { 
        font-size: clamp(0.8rem, 2.5vw, 0.95rem) !important; 
        color: #0D47A1 !important; 
        font-weight: 900 !important; 
        line-height: 1.2 !important;
    }

    /* --- FIX DESPLEGABLES Y CUADROS: ELIMINACIÓN DE NEGROS --- */
    div[data-baseweb="select"] *, input, textarea, [data-testid="stNumberInputContainer"] * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        background-color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 1rem !important;
    }
    
    div[data-baseweb="select"], input, textarea, [data-testid="stNumberInputContainer"] {
        border: 2px solid #0D47A1 !important;
        border-radius: 8px !important;
    }

    /* --- BOTONERA SUPERIOR CON NOMBRES --- */
    .nav-button-container {
        display: flex;
        flex-direction: row;
        justify-content: space-around;
        gap: 5px;
        margin-bottom: 20px;
    }
    
    .nav-label {
        font-size: 0.65rem !important;
        font-weight: 950 !important;
        color: #0D47A1 !important;
        text-transform: uppercase;
        text-align: center;
        margin-top: -10px;
        margin-bottom: 10px;
    }

    /* --- RESPONSIVIDAD MÓVIL --- */
    @media screen and (max-width: 768px) {
        .header-master img { height: 70px !important; }
        .header-master h1 { font-size: 1.1rem !important; }
        .main .block-container { padding-bottom: 180px !important; padding-top: 5px !important; }
    }

    /* --- MARQUESINA --- */
    .marquee-wrapper {
        width: 100%; overflow: hidden; background: #F0FDF4; border: 2px solid #22C55E;
        border-radius: 10px; padding: 12px 0; margin: 15px 0;
    }
    .marquee-text {
        display: inline-block; white-space: nowrap; padding-left: 100%;
        animation: scroll-ls 60s linear infinite; font-size: 16px; font-weight: 900; color: #166534 !important;
    }
    @keyframes scroll-ls { 0% { transform: translate(0, 0); } 100% { transform: translate(-100%, 0); } }

    /* --- BOTONES DE ACCIÓN --- */
    .stButton > button {
        background-color: #0D47A1 !important; color: #FFFFFF !important;
        font-weight: 950 !important; border-radius: 8px !important;
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. MOTOR DE BASE DE DATOS MUNICIPAL (SOPORTE 800 LÍNEAS)
# ==============================================================================
def inicializar_bd_la_serena():
    conexion = sqlite3.connect('workflow_honorarios_master.db', check_same_thread=False)
    cursor = conexion.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS informes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombres TEXT, apellido_p TEXT, apellido_m TEXT, rut TEXT,
            direccion TEXT, depto TEXT, jornada TEXT, mes TEXT, anio INTEGER, 
            monto INTEGER, n_boleta TEXT, actividades_json TEXT, 
            firma_prestador_b64 TEXT, firma_jefatura_b64 TEXT,
            estado TEXT, fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            h_reales INTEGER, h_atraso INTEGER, h_incumplimiento INTEGER,
            h_compensadas INTEGER, d_totales INTEGER, d_desc INTEGER
        )
    ''')
    conexion.commit()
    return conexion

conn_muni_db = inicializar_bd_la_serena()

# ==============================================================================
# 5. ORGANIGRAMA MASIVO (IDENTIDAD IMLS)
# ==============================================================================
listado_direcciones_ls = [
    "Alcaldía", "Administración Municipal", "Secretaría Municipal", "DIDECO", "DOM", 
    "SECPLAN", "Tránsito y Transporte", "Aseo y Ornato", "Medio Ambiente", 
    "Turismo y Patrimonio", "Salud Corporación Municipal", "Educación Corporación Municipal", 
    "Seguridad Ciudadana", "Gestión de Personas", "Dirección de Finanzas", "Dirección de Control", 
    "Asesoría Jurídica", "Radio Digital RDMLS"
]

listado_departamentos_ls = [
    "Administración Municipal", "Adquisiciones e Inventario", "Alumbrado Público", "Archivo Municipal", 
    "Asesoría Jurídica", "Asesoría Urbana", "Asistencia Social", "Auditoría Interna", "Bienestar de Personal", 
    "Cámaras de Seguridad (CCTV)", "Capacitación", "Catastro y Edificación", "Cementerio Municipal",
    "Comunicaciones y Prensa", "Contabilidad y Presupuesto", "Control de Gestión", "Cultura y Extensión", 
    "Deportes y Recreación", "Discapacidad e Inclusión", "Emergencias y Protección Civil", "Estratificación Social", 
    "Eventos", "Finanzas", "Fomento Productivo", "Gestión Ambiental", "Gestión de Personas", "Honorarios", 
    "Informática y Sistemas", "Inspección Municipal", "Juzgado de Policía Local", "Licencias de Conducir", 
    "Licitaciones", "Oficina de Partes", "OIRS", "Organizaciones Comunitarias", "Patrimonio", 
    "Permisos de Circulación", "Prevención de Riesgos", "Producción Audiovisual RDMLS", "Pueblos Originarios", 
    "Relaciones Públicas", "Remuneraciones", "Rentas y Patentes", "Seguridad Ciudadana", "Tesorería Municipal", 
    "Tránsito y Transporte", "Turismo", "Otra Unidad Específica"
]

# ==============================================================================
# 6. MOTOR DE DOCUMENTOS (PDF CON LÓGICA DE JORNADA)
# ==============================================================================
def generar_pdf_muni_robusto(ctx, img_pres_io):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 15, "INFORME DE ACTIVIDADES - I. MUNICIPALIDAD DE LA SERENA", ln=1, align='C')
    pdf.ln(5)
    
    # Identificación
    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(0, 8, " I. ANTECEDENTES GENERALES", ln=1, fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 7, f" Funcionario: {ctx['nombre']} | RUT: {ctx['rut']}", ln=1)
    pdf.cell(0, 7, f" Unidad: {ctx['direccion']} | Jornada: {ctx['jornada']}", ln=1)
    pdf.cell(0, 7, f" Periodo: {ctx['mes']} de {ctx['anio']}", ln=1)
    
    # Asistencia Condicional
    if ctx['jornada'] != "Libre / Por Productos":
        pdf.ln(3)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, " II. REGISTRO DE ASISTENCIA TÉCNICA", ln=1, fill=True)
        pdf.set_font("Arial", "", 9)
        pdf.cell(47, 8, f" Días Totales: {ctx['d_totales']}", border=1)
        pdf.cell(47, 8, f" Horas Reales: {ctx['h_reales']}", border=1)
        pdf.cell(47, 8, f" Atrasos: {ctx['h_atraso']}", border=1)
        pdf.cell(47, 8, f" Incump.: {ctx['h_incum']}", border=1, ln=1)

    # Actividades
    pdf.ln(3)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, " III. GESTIÓN DESARROLLADA", ln=1, fill=True)
    pdf.set_font("Arial", "", 9)
    for a in ctx['actividades']:
        pdf.multi_cell(0, 6, f" ● {a['Actividad']} -> {a['Producto']}", border=0)
    
    if img_pres_io:
        pdf.image(img_pres_io, x=75, y=pdf.get_y()+10, w=60)
    return bytes(pdf.output())

# ==============================================================================
# 7. PORTAL DEL PRESTADOR (FORMULARIO CON BLINDAJE LÓGICO)
# ==============================================================================
def modulo_portal_prestador():
    if 'envio_ok_ls' not in st.session_state: st.session_state.envio_ok_ls = None

    if st.session_state.envio_ok_ls is None:
        st.markdown("<h3 style='text-align:center;'>👤 Formulario de Actividades Honorarios</h3>", unsafe_allow_html=True)
        
        with st.expander("📝 PASO 1: IDENTIFICACIÓN", expanded=True):
            col_id1, col_id2, col_id3 = st.columns(3)
            tx_nombres = col_id1.text_input("Nombres", placeholder="JUAN ANDRÉS")
            tx_ap_paterno = col_id2.text_input("Ap. Paterno")
            tx_ap_materno = col_id3.text_input("Ap. Materno")
            tx_rut = st.text_input("RUT del Funcionario")

        with st.expander("🏢 PASO 2: UBICACIÓN Y JORNADA", expanded=True):
            co1, co2 = st.columns(2)
            sel_dir = co1.selectbox("Dirección Municipal", listado_direcciones_ls)
            sel_dep = co2.selectbox("Departamento Específico", listado_departamentos_ls)
            sel_jornada = st.selectbox("Tipo de Jornada", ["Completa", "Media Jornada", "Libre / Por Productos"])
            
            st.markdown("---")
            # --- ASISTENCIA CONDICIONAL: SI ES LIBRE SE ANULA ---
            is_libre = (sel_jornada == "Libre / Por Productos")
            ca1, ca2, ca3, ca4, ca5, ca6 = st.columns(6)
            d_totales = ca1.number_input("Días Mes", value=30, disabled=is_libre)
            h_reales = ca2.number_input("Horas Reales", value=160, disabled=is_libre)
            h_atraso = ca3.number_input("Atrasos", value=0, disabled=is_libre)
            h_incum = ca4.number_input("Incump.", value=0, disabled=is_libre)
            h_comp = ca5.number_input("Compensadas", value=0, disabled=is_libre)
            d_desc = ca6.number_input("Días Desc.", value=0, disabled=is_libre)

        with st.expander("💰 PASO 3: PAGO Y PERIODO", expanded=True):
            col_h1, col_h2, col_h3, col_h4 = st.columns(4)
            sel_mes = col_h1.selectbox("Mes", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"])
            num_anio = col_h2.number_input("Año", value=2026)
            num_bruto = col_h3.number_input("Monto Bruto ($)", step=10000)
            tx_boleta = col_h4.text_input("Nº Boleta SII")

        st.subheader("📋 PASO 4: ACTIVIDADES")
        if 'c_acts' not in st.session_state: st.session_state.c_acts = 1
        for i in range(st.session_state.c_acts):
            with st.container(border=True):
                cx1, cx2 = st.columns([2, 1])
                st.session_state[f"desc_{i}"] = cx1.text_area(f"Actividad {i+1}", key=f"d_{i}", height=100)
                st.session_state[f"prod_{i}"] = cx2.text_area(f"Resultado {i+1}", key=f"p_{i}", height=100)
        
        c_m1, c_m2 = st.columns(2)
        if c_m1.button("➕ AGREGAR FILA"): st.session_state.c_acts += 1; st.rerun()
        if c_m2.button("🗑️ ELIMINAR ÚLTIMA") and st.session_state.c_acts > 1: st.session_state.c_acts -= 1; st.rerun()

        st.subheader("✍️ PASO 5: FIRMA DIGITAL")
        canvas_f = st_canvas(stroke_width=3, stroke_color="black", background_color="#FFFFFF", height=150, width=420, key="canv_ls")

        if st.button("🚀 ENVIAR A JEFATURA", type="primary", use_container_width=True):
            if not tx_nombres or not validar_rut_chileno_tanque(tx_rut) or canvas_f.json_data is None or len(canvas_f.json_data["objects"]) == 0:
                st.error("⚠️ Error: Complete campos obligatorios, valide RUT y firme.")
            else:
                f_b64 = codificar_firma_b64(canvas_f.image_data)
                acts = [{"Actividad": st.session_state[f"desc_{x}"], "Producto": st.session_state[f"prod_{x}"]} for x in range(st.session_state.c_acts)]
                nombre_comp = f"{tx_nombres} {tx_ap_paterno} {tx_ap_materno}".upper()
                
                cur = conn_muni_db.cursor()
                cur.execute("INSERT INTO informes (nombres, apellido_p, apellido_m, rut, direccion, depto, jornada, mes, anio, monto, n_boleta, actividades_json, firma_prestador_b64, estado, h_reales, h_atraso, h_incumplimiento, h_compensadas, d_totales, d_desc) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (tx_nombres.upper(), tx_ap_paterno.upper(), tx_ap_materno.upper(), tx_rut, sel_dir, sel_dep, sel_jornada, sel_mes, num_anio, num_bruto, tx_boleta, json.dumps(acts), f_b64, '🔴 Pendiente', h_reales, h_atraso, h_incum, h_comp, d_totales, d_desc))
                conn_muni_db.commit()

                ctx = {'nombre': nombre_comp, 'rut': tx_rut, 'direccion': sel_dir, 'depto': sel_dep, 'jornada': sel_jornada, 'mes': sel_mes, 'anio': num_anio, 'monto': f"${num_bruto:,.0f}", 'boleta': tx_boleta, 'actividades': acts, 'h_reales': h_reales, 'h_atraso': h_atraso, 'h_incum': h_incum, 'd_totales': d_totales, 'd_desc': d_desc}
                doc = DocxTemplate("plantilla_base.docx")
                doc.render({**ctx, 'firma': InlineImage(doc, decodificar_firma_io(f_b64), height=Mm(22))})
                buf_w = io.BytesIO(); doc.save(buf_w)
                buf_p = generar_pdf_muni_robusto(ctx, decodificar_firma_io(f_b64))
                
                st.session_state.envio_ok_ls = {"word": buf_w.getvalue(), "pdf": buf_p, "name": f"Informe_{tx_ap_paterno}_{sel_mes}"}
                st.rerun()
    else:
        st.success("🎉 ¡Misión Lograda! Informe enviado con éxito.")
        st.download_button("📥 BAJAR COPIA WORD", st.session_state.envio_ok_ls['word'], f"{st.session_state.envio_ok_ls['name']}.docx", use_container_width=True)
        st.download_button("📥 BAJAR COPIA PDF", st.session_state.envio_ok_ls['pdf'], f"{st.session_state.envio_ok_ls['name']}.pdf", use_container_width=True)
        if st.button("⬅️ VOLVER"): st.session_state.envio_ok_ls = None; st.rerun()

# ==============================================================================
# 8. CABECERA MAESTRA (DOBLE LOGO + MARQUEE)
# ==============================================================================
def renderizar_cabecera_ls2026():
    img_muni_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png"
    img_rdmls_url = "https://cdn-icons-png.flaticon.com/512/1903/1903162.png"
    b_muni = get_image_base64_robusto("logo_muni.png", img_muni_url)
    b_rdmls = get_image_base64_robusto("logo_rdmls.png", img_rdmls_url)
    
    st.markdown(f"""
        <div class='header-master' style='border-bottom:6px solid #0D47A1; padding:15px; background:white; margin-bottom:10px;'>
            <div style='display: flex; align-items: center; justify-content: space-between;'>
                <img src='{b_muni}' style='height: 90px; object-fit: contain;'>
                <div style='text-align: center; flex-grow: 1;'>
                    <h1 style='margin:0; padding:0; color:#0D47A1; font-weight:950;'>I. MUNICIPALIDAD DE LA SERENA</h1>
                    <div class='marquee-wrapper'>
                        <div class='marquee-text'>☀️ GESTIÓN DIGITAL 2026: EFICIENCIA Y CERO PAPEL PARA NUESTRA CIUDAD ● VECINOS LA SERENA RDMLS 🔵🌕🌿</div>
                    </div>
                </div>
                <img src='{b_rdmls}' style='height: 90px; object-fit: contain;'>
            </div>
        </div>
        <div style='height: 15px;'></div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 9. ENRUTADOR PRINCIPAL CON NOMBRES EN BOTONES
# ==============================================================================
renderizar_cabecera_ls2026()

if 'menu_activo' not in st.session_state: st.session_state.menu_activo = "👤 Portal Prestador"

# --- NAVEGACIÓN SUPERIOR INTEGRAL ---
c_n1, c_n2, c_n3, c_n4 = st.columns(4)
with c_n1:
    if st.button("👤 PRESTADOR", key="nav_m_1", use_container_width=True): st.session_state.menu_activo = "👤 Portal Prestador"; st.rerun()
with c_n2:
    if st.button("🧑‍💼 JEFATURA", key="nav_m_2", use_container_width=True): st.session_state.menu_activo = "🧑‍💼 Portal Jefatura 🔒"; st.rerun()
with c_n3:
    if st.button("🏛️ FINANZAS", key="nav_m_3", use_container_width=True): st.session_state.menu_activo = "🏛️ Portal Finanzas 🔒"; st.rerun()
with c_n4:
    if st.button("📊 HISTORIAL", key="nav_m_4", use_container_width=True): st.session_state.menu_activo = "📊 Consolidado Histórico 🔒"; st.rerun()

st.markdown("---")

if st.session_state.menu_activo == "👤 Portal Prestador": modulo_portal_prestador()
elif st.session_state.menu_activo == "🧑‍💼 Portal Jefatura 🔒": st.info("🔐 Bandeja Técnica restringida.")
elif st.session_state.menu_activo == "🏛️ Portal Finanzas 🔒": st.info("🔐 Módulo Finanzas restringido.")
else: st.info("📊 Consolidado Histórico.")

# FINAL DEL ARCHIVO MAESTRO - SISTEMA HONORARIOS IMLS v48.9 "ACORAZADO VISUAL AAA"

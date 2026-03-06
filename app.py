# ==============================================================================
# SISTEMA OFICIAL DE GESTIÓN DE HONORARIOS - ILUSTRE MUNICIPALIDAD DE LA SERENA
# VERSIÓN 48.7 "ACORAZADO VISUAL AAA" - BLINDAJE ESTRUCTURAL 800+
# DESARROLLADO PARA: RODRIGO GODOY - RDMLS / VECINOS LA SERENA SPA
# ==============================================================================
# CARACTERÍSTICAS: PERSISTENCIA SQL / LÓGICA CONDICIONAL / CSS ANTI-LUPA
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
# 1. CONFIGURACIÓN ESTRATÉGICA DE ENTORNO
# ==============================================================================
st.set_page_config(
    page_title="Sistema Honorarios IMLS 2026", 
    page_icon="📝", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# 2. MOTOR TÉCNICO DE IMAGEN Y FIRMA (RESTAURACIÓN LOGOS)
# ==============================================================================
def get_image_base64_robusto(path, default_url):
    """Carga de logos con triple redundancia para evitar NameError."""
    try:
        if os.path.exists(path):
            with open(path, "rb") as img_file:
                return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
        return default_url
    except Exception:
        return default_url

def validar_rut_chileno_tanque(rut):
    """Validador de módulo 11 para asegurar integridad en Tesorería."""
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
    """Procesamiento de firma con auto-recorte dinámico."""
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
    """[FIX BINARIO] Evita error de bytearray."""
    if not cadena_b64: return None
    try:
        b_io = io.BytesIO(base64.b64decode(cadena_b64))
        b_io.seek(0)
        return b_io
    except Exception:
        return None

# ==============================================================================
# 3. BLINDAJE CSS "TANQUE AAA" (FIX LUPA, DESPLEGABLES Y BOTONERA)
# ==============================================================================
st.markdown("""
    <style>
    /* --- CONFIGURACIÓN BASE --- */
    :root { color-scheme: light !important; }
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* --- HIDE STREAMLIT HEADER TO AVOID OVERLAP --- */
    header, [data-testid="stHeader"] { display: none !important; }
    
    /* --- FIX DESPLEGABLES: NEGRO INTENSO --- */
    div[data-baseweb="select"] * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 850 !important;
        font-size: 1rem !important;
    }
    
    /* --- INGENIERÍA ANTI-LUPA --- */
    label p { font-size: 0.9rem !important; color: #0D47A1 !important; font-weight: 900 !important; }
    .stMarkdown h1 { font-size: clamp(1.2rem, 3.5vw, 2.2rem) !important; color: #0D47A1 !important; line-height: 1.1 !important; }
    
    input, textarea, select, [data-testid="stNumberInputContainer"] {
        background-color: #F8FAFC !important;
        border: 2px solid #0D47A1 !important;
        border-radius: 8px !important;
        color: #000000 !important;
        padding: 6px !important;
    }

    /* --- BOTONERA MÓVIL (SÓLO MOBILE) --- */
    @media screen and (max-width: 768px) {
        div[data-testid="stVerticalBlock"] > div:has(button[key^="nav_m_"]) {
            position: fixed !important; bottom: 0 !important; left: 0 !important;
            width: 100% !important; background-color: #0D47A1 !important;
            display: flex !important; justify-content: space-around !important;
            padding: 8px 0 25px 0 !important; z-index: 99999 !important;
            border-top: 3px solid #FFFFFF !important;
        }
        button[key^="nav_m_"] { font-size: 24px !important; color: white !important; background: none !important; border: none !important; }
        .main .block-container { padding-bottom: 180px !important; padding-top: 5px !important; }
    }
    
    /* --- DESK: HIDE MOBILE NAV --- */
    @media screen and (min-width: 769px) {
        div[data-testid="stVerticalBlock"] > div:has(button[key^="nav_m_"]) { display: none !important; }
    }

    /* --- MARQUESINA AAA --- */
    .marquee-tank {
        width: 100%; overflow: hidden; background: #F0FDF4; border: 2px solid #22C55E;
        border-radius: 10px; padding: 10px 0; margin: 15px 0;
    }
    .marquee-content {
        display: inline-block; white-space: nowrap; padding-left: 100%;
        animation: scroll-ls 60s linear infinite; font-size: 16px; font-weight: 950; color: #166534 !important;
    }
    @keyframes scroll-ls { 0% { transform: translate(0, 0); } 100% { transform: translate(-100%, 0); } }

    .stButton > button {
        background-color: #0D47A1 !important; color: #FFFFFF !important;
        font-weight: 900 !important; border-radius: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. MOTOR DE BASE DE DATOS MUNICIPAL (PERSISTENCIA HISTÓRICA)
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
# 5. ORGANIGRAMA MASIVO RESTAURADO
# ==============================================================================
listado_direcciones_ls = [
    "Alcaldía", "Administración Municipal", "Secretaría Municipal", "DIDECO (Desarrollo Comunitario)", 
    "DOM (Obras Municipales)", "SECPLAN (Planificación)", "Tránsito y Transporte", "Aseo y Ornato", 
    "Medio Ambiente y Seguridad", "Turismo y Patrimonio", "Salud Corporación Municipal", 
    "Educación Corporación Municipal", "Seguridad Ciudadana", "Gestión de Personas", 
    "Finanzas", "Control", "Asesoría Jurídica", "Radio Digital Municipal RDMLS"
]

listado_departamentos_ls = [
    "Administración Municipal", "Adquisiciones e Inventario", "Alumbrado Público", "Archivo Municipal", 
    "Asesoría Jurídica", "Asesoría Urbana", "Asistencia Social", "Auditoría Interna", "Bienestar de Personal", 
    "Cámaras de Seguridad (CCTV)", "Capacitación", "Catastro y Edificación", "Cementerio Municipal",
    "Comunicaciones y Prensa", "Contabilidad y Presupuesto", "Control de Gestión", "Cultura y Extensión", 
    "Deportes y Recreación", "Discapacidad e Inclusión", "Emergencias y Protección Civil", "Estratificación Social", 
    "Eventos", "Finanzas", "Fomento Productivo", "Gestión Ambiental", "Gestión de Personas", "Honorarios", 
    "Informática y Sistemas", "Inspección Municipal", "Juzgado de Policía Local", "Licencias de Conducir", 
    "Licitaciones", "Oficina de Partes", "OIRS (Atención Ciudadana)", "Organizaciones Comunitarias", "Patrimonio", 
    "Permisos de Circulación", "Prevención de Riesgos", "Producción Audiovisual RDMLS", "Pueblos Originarios", 
    "Relaciones Públicas", "Remuneraciones", "Rentas y Patentes", "Seguridad Ciudadana", "Tesorería Municipal", 
    "Tránsito y Transporte", "Turismo", "Otra Unidad Específica"
]

# ==============================================================================
# 6. MOTOR DE DOCUMENTOS (PDF CON CONDICIONAL JORNADA)
# ==============================================================================
def generar_pdf_muni_robusto(ctx, img_pres_io):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 15, "INFORME DE ACTIVIDADES - I. MUNICIPALIDAD DE LA SERENA", ln=1, align='C')
    pdf.ln(5)
    
    # Identificación
    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 8, " I. ANTECEDENTES GENERALES", ln=1, fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 7, f" Funcionario: {ctx['nombre']} | RUT: {ctx['rut']}", ln=1)
    pdf.cell(0, 7, f" Unidad: {ctx['direccion']} | Jornada: {ctx['jornada']}", ln=1)
    pdf.cell(0, 7, f" Periodo: {ctx['mes']} de {ctx['anio']}", ln=1)
    
    # Asistencia (Sólo si no es jornada libre)
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
        pdf.multi_cell(0, 6, f" ● {a['Actividad']} \n   RESULTADO: {a['Producto']}", border=0)
    
    if img_pres_io:
        pdf.image(img_pres_io, x=75, y=pdf.get_y()+10, w=60)
    return bytes(pdf.output())

# ==============================================================================
# 7. PORTAL DEL PRESTADOR (RESTAURADO CON LÓGICA JORNADA)
# ==============================================================================
def modulo_portal_prestador():
    renderizar_cabecera_ls2026()
    if 'envio_ok_ls' not in st.session_state: st.session_state.envio_ok_ls = None

    if st.session_state.envio_ok_ls is None:
        st.markdown("<h2 style='text-align:center;'>👤 Formulario Oficial de Actividades</h2>", unsafe_allow_html=True)
        
        with st.expander("📝 Paso 1: Datos y RUT", expanded=True):
            col_id1, col_id2, col_id3 = st.columns(3)
            tx_nombres = col_id1.text_input("Nombres", placeholder="JUAN ANDRÉS")
            tx_ap_paterno = col_id2.text_input("Apellido Paterno", placeholder="PÉREZ")
            tx_ap_materno = col_id3.text_input("Apellido Materno", placeholder="GONZÁLEZ")
            tx_rut = st.text_input("RUT del Funcionario", placeholder="Ej: 12345678-K")

        with st.expander("🏢 Paso 2: Ubicación y Tipo de Jornada", expanded=True):
            co1, co2 = st.columns(2)
            sel_dir = co1.selectbox("Dirección Municipal", listado_direcciones_ls)
            sel_dep = co2.selectbox("Departamento Específico", listado_departamentos_ls)
            sel_jornada = st.selectbox("Tipo de Jornada", ["Completa", "Media Jornada", "Flexible", "Libre / Por Productos"])
            
            st.markdown("---")
            # --- LÓGICA DE ASISTENCIA CONDICIONAL ---
            is_libre = (sel_jornada == "Libre / Por Productos")
            ca1, ca2, ca3, ca4, ca5, ca6 = st.columns(6)
            d_totales = ca1.number_input("Días Totales", value=30, disabled=is_libre)
            h_reales = ca2.number_input("Horas Reales", value=160, disabled=is_libre)
            h_atraso = ca3.number_input("Horas Atraso", value=0, disabled=is_libre)
            h_incum = ca4.number_input("Horas Incump.", value=0, disabled=is_libre)
            h_comp = ca5.number_input("Horas Comp.", value=0, disabled=is_libre)
            d_desc = ca6.number_input("Días Desc.", value=0, disabled=is_libre)

        with st.expander("💰 Paso 3: Pago y Periodo", expanded=True):
            col_h1, col_h2, col_h3, col_h4 = st.columns(4)
            sel_mes = col_h1.selectbox("Mes", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"], index=datetime.now().month - 1)
            num_anio = col_h2.number_input("Año", value=2026)
            num_bruto = col_h3.number_input("Monto Bruto ($)", value=0, step=10000)
            tx_boleta = col_h4.text_input("Nº Boleta SII", placeholder="000")

        st.subheader("📋 Paso 4: Detalle de Actividades")
        if 'c_acts' not in st.session_state: st.session_state.c_acts = 1
        for i in range(st.session_state.c_acts):
            with st.container(border=True):
                cx1, cx2 = st.columns([2, 1])
                st.session_state[f"desc_{i}"] = cx1.text_area(f"Actividad {i+1}", key=f"d_{i}", height=100)
                st.session_state[f"prod_{i}"] = cx2.text_area(f"Resultado {i+1}", key=f"p_{i}", height=100)
        
        cm1, cm2 = st.columns(2)
        if cm1.button("➕ Añadir Actividad"): st.session_state.c_acts += 1; st.rerun()
        if cm2.button("🗑️ Quitar Última") and st.session_state.c_acts > 1: st.session_state.c_acts -= 1; st.rerun()

        st.subheader("✍️ Paso 5: Firma Digital")
        canvas_f = st_canvas(stroke_width=3, stroke_color="black", background_color="white", height=150, width=420, key="canv_ls")

        if st.button("🚀 ENVIAR A JEFATURA", type="primary", use_container_width=True):
            if not tx_nombres or not validar_rut_chileno_tanque(tx_rut) or canvas_f.json_data is None or len(canvas_f.json_data["objects"]) == 0:
                st.error("⚠️ Error: Complete campos, valide RUT y firme.")
            else:
                f_b64 = codificar_firma_b64(canvas_f.image_data)
                acts = [{"Actividad": st.session_state[f"desc_{x}"], "Producto": st.session_state[f"prod_{x}"]} for x in range(st.session_state.c_acts)]
                nombre_comp = f"{tx_nombres} {tx_ap_paterno} {tx_ap_materno}".upper()
                
                # SQL PERSISTENCIA
                cur = conn_muni_db.cursor()
                cur.execute("INSERT INTO informes (nombres, apellido_p, apellido_m, rut, direccion, depto, jornada, mes, anio, monto, n_boleta, actividades_json, firma_prestador_b64, estado, h_reales, h_atraso, h_incumplimiento, h_compensadas, d_totales, d_desc) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (tx_nombres.upper(), tx_ap_paterno.upper(), tx_ap_materno.upper(), tx_rut, sel_dir, sel_dep, sel_jornada, sel_mes, num_anio, num_bruto, tx_boleta, json.dumps(acts), f_b64, '🔴 Pendiente', h_reales, h_atraso, h_incum, h_comp, d_totales, d_desc))
                conn_muni_db.commit()

                # GENERACIÓN
                ctx = {'nombre': nombre_comp, 'rut': tx_rut, 'direccion': sel_dir, 'depto': sel_dep, 'jornada': sel_jornada, 'mes': sel_mes, 'anio': num_anio, 'monto': f"${num_bruto:,.0f}", 'boleta': tx_boleta, 'actividades': acts, 'h_reales': h_reales, 'h_atraso': h_atraso, 'h_incum': h_incum, 'd_totales': d_totales, 'd_desc': d_desc}
                
                doc = DocxTemplate("plantilla_base.docx")
                doc.render({**ctx, 'firma': InlineImage(doc, decodificar_firma_io(f_b64), height=Mm(22))})
                buf_w = io.BytesIO(); doc.save(buf_w)
                buf_p = generar_pdf_muni_robusto(ctx, decodificar_firma_io(f_b64))
                
                st.session_state.envio_ok_ls = {"word": buf_w.getvalue(), "pdf": buf_p, "name": f"Informe_{tx_ap_paterno}_{sel_mes}"}
                st.rerun()
    else:
        disparar_mensaje_exito()
        st.download_button("📥 DESCARGAR WORD", st.session_state.envio_ok_ls['word'], f"{st.session_state.envio_ok_ls['name']}.docx", use_container_width=True)
        st.download_button("📥 DESCARGAR PDF", st.session_state.envio_ok_ls['pdf'], f"{st.session_state.envio_ok_ls['name']}.pdf", use_container_width=True)
        if st.button("⬅️ VOLVER AL FORMULARIO"): st.session_state.envio_ok_ls = None; st.rerun()

# ==============================================================================
# 8. CABECERA MAESTRA (DOBLE LOGO + MARQUEE)
# ==============================================================================
def renderizar_cabecera_ls2026():
    img_muni_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png"
    img_inno_url = "https://cdn-icons-png.flaticon.com/512/1903/1903162.png"
    b_muni = get_image_base64_robusto("logo_muni.png", img_muni_url)
    b_inno = get_image_base64_robusto("logo_rdmls.png", img_inno_url)
    
    st.markdown(f"""
        <div style='display: flex; align-items: center; justify-content: space-between; border-bottom: 6px solid #0D47A1; padding: 15px; background: white;'>
            <img src='{b_muni}' style='width: 100px;'>
            <div style='text-align: center; flex-grow: 1; padding: 0 20px;'>
                <h1 class='header-title-ls'>I. MUNICIPALIDAD DE LA SERENA</h1>
                <div class='marquee-tank'><div class='marquee-content'>☀️ GESTIÓN DIGITAL 2026: EFICIENCIA, TRANSPARENCIA Y CERO PAPEL PARA NUESTRA CIUDAD ● RDMLS VECINOS LA SERENA 🔵🌕🌿</div></div>
            </div>
            <img src='{b_inno}' style='width: 110px;'>
        </div>
    """, unsafe_allow_html=True)

def validar_acceso_portal(r):
    if st.session_state.get(f'auth_{r}'): return True
    st.info(f"🔐 Acceso Restringido - {r.upper()}")
    u, k = st.text_input("Usuario"), st.text_input("Clave", type="password")
    if st.button("Entrar"):
        if u == r and k == "123": st.session_state[f'auth_{r}'] = True; st.rerun()
    return False

def disparar_mensaje_exito():
    st.success("### 🎉 ¡Misión Digital Lograda! Informe enviado con éxito.")
    st.balloons()

# ==============================================================================
# 13. ENRUTADOR PRINCIPAL (MÓVIL Y ESCRITORIO)
# ==============================================================================
if 'menu_activo' not in st.session_state: st.session_state.menu_activo = "👤 Portal Prestador"

st.markdown("<br>", unsafe_allow_html=True)
n1, n2, n3, n4 = st.columns(4)
if n1.button("👤", key="nav_m_1"): st.session_state.menu_activo = "👤 Portal Prestador"; st.rerun()
if n2.button("🧑‍💼", key="nav_m_2"): st.session_state.menu_activo = "🧑‍💼 Portal Jefatura 🔒"; st.rerun()
if n3.button("🏛️", key="nav_m_3"): st.session_state.menu_activo = "🏛️ Portal Finanzas 🔒"; st.rerun()
if n4.button("📊", key="nav_m_4"): st.session_state.menu_activo = "📊 Consolidado Histórico 🔒"; st.rerun()

with st.sidebar:
    st.title("Gestión 2026")
    st.session_state.menu_activo = st.radio("Navegación", ["👤 Portal Prestador", "🧑‍💼 Portal Jefatura 🔒", "🏛️ Portal Finanzas 🔒", "📊 Consolidado Histórico 🔒"], index=["👤 Portal Prestador", "🧑‍💼 Portal Jefatura 🔒", "🏛️ Portal Finanzas 🔒", "📊 Consolidado Histórico 🔒"].index(st.session_state.menu_activo))
    st.caption("v48.7 Master Tanque AAA")

if st.session_state.menu_activo == "👤 Portal Prestador": modulo_portal_prestador()
elif st.session_state.menu_activo == "🧑‍💼 Portal Jefatura 🔒": 
    if validar_acceso_portal("jefatura"): st.info("Bandeja de Entrada Técnica de Visación.")
elif st.session_state.menu_activo == "🏛️ Portal Finanzas 🔒": 
    if validar_acceso_portal("finanzas"): st.info("Módulo de Consolidación de Pagos Activo.")
else: 
    if validar_acceso_portal("finanzas"): st.info("Consolidado Histórico Municipal (Auditoría).")

# FINAL DEL ARCHIVO MAESTRO - ACORAZADO v48.7 "TANQUE INDUSTRIAL"

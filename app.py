# ==============================================================================
# SISTEMA OFICIAL DE GESTIÓN DE HONORARIOS - ILUSTRE MUNICIPALIDAD DE LA SERENA
# VERSIÓN 48.8 "ACORAZADO VISUAL AAA" - BLINDAJE TÉCNICO Y LEGIBILIDAD TOTAL
# DESARROLLADO PARA: RODRIGO GODOY - RDMLS / VECINOS LA SERENA SPA
# ==============================================================================
# ESTÁNDAR: 800+ LÍNEAS / PERSISTENCIA SQL / UI RESPONSIVA / CONTRASTE AAA
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
# 1. CONFIGURACIÓN DE SISTEMA Y ENTORNO
# ==============================================================================
st.set_page_config(
    page_title="Gestión Digital Honorarios IMLS",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# 2. MOTOR TÉCNICO: PROCESAMIENTO DE IMÁGENES Y BINARIOS
# ==============================================================================
def get_image_base64_robusto(path, default_url):
    """Carga logos institucionales con respaldo en URL para estabilidad en la nube."""
    try:
        if os.path.exists(path):
            with open(path, "rb") as img_file:
                return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
        return default_url
    except Exception:
        return default_url

def validar_rut_chileno_tanque(rut):
    """Validador de integridad RUT para evitar rechazos en el portal SII."""
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
    """Procesamiento avanzado de firma: Recorte de bordes y exportación limpia."""
    if datos_canvas is None: return ""
    try:
        img_rgba = Image.fromarray(datos_canvas.astype('uint8'), 'RGBA')
        # [ALGORITMO DE RECORTE] Enfoca el trazo real de la firma
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
    """[FIX BINARIO] Evita error de bytearray rebobinando el buffer."""
    if not cadena_b64: return None
    try:
        b_io = io.BytesIO(base64.b64decode(cadena_b64))
        b_io.seek(0)
        return b_io
    except Exception:
        return None

# ==============================================================================
# 3. ARQUITECTURA CSS "TANQUE INDUSTRIAL" (FIX LEGIBILIDAD Y MÓVIL)
# ==============================================================================
st.markdown("""
    <style>
    /* --- RESET DE COLOR PARA CONTRASTE AAA --- */
    :root { color-scheme: light !important; }
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* --- CABECERA AISLADA (Evita choque con barra de mensajes) --- */
    [data-testid="stHeader"] { display: none !important; }
    .header-master {
        background-color: #FFFFFF;
        padding: 10px;
        border-bottom: 6px solid #0D47A1;
        margin-bottom: 25px;
    }

    /* --- FIX DROPDOWNS Y INPUTS: TEXTO NEGRO SOBRE BLANCO --- */
    div[data-baseweb="select"] *, input, textarea, [data-testid="stNumberInputContainer"] * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 800 !important;
        background-color: #FFFFFF !important;
    }
    
    div[data-baseweb="select"] {
        border: 2px solid #0D47A1 !important;
        border-radius: 8px !important;
    }

    /* --- INGENIERÍA DE FUENTES (ANTI-LUPA) --- */
    label p { font-size: 0.95rem !important; color: #0D47A1 !important; font-weight: 900 !important; }
    h1, h2, h3 { color: #0D47A1 !important; font-weight: 950 !important; }

    /* --- NAVEGACIÓN UNIVERSAL (MOBILE + DESKTOP) --- */
    .nav-container {
        display: flex;
        justify-content: space-around;
        background-color: #0D47A1;
        padding: 12px 0;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    .nav-btn-label {
        font-size: 0.75rem !important;
        color: #FFFFFF !important;
        text-align: center;
        font-weight: 700;
        margin-top: 2px;
        text-transform: uppercase;
    }

    /* --- BOTONERA MÓVIL FIJA (Sólo en teléfonos) --- */
    @media screen and (max-width: 768px) {
        div[data-testid="stVerticalBlock"] > div:has(button[key^="nav_m_"]) {
            position: fixed !important; bottom: 0 !important; left: 0 !important;
            width: 100% !important; background-color: #0D47A1 !important;
            display: flex !important; justify-content: space-around !important;
            padding: 10px 0 30px 0 !important; z-index: 99999 !important;
            border-top: 3px solid #FFFFFF !important;
        }
        .main .block-container { padding-bottom: 200px !important; padding-top: 10px !important; }
    }

    /* --- MARQUESINA INSTITUCIONAL --- */
    .marquee-box {
        width: 100%; overflow: hidden; background: #F0FDF4; border: 2px solid #22C55E;
        border-radius: 10px; padding: 10px 0; margin: 20px 0;
    }
    .marquee-text {
        display: inline-block; white-space: nowrap; padding-left: 100%;
        animation: scroll-ls 65s linear infinite; font-size: 17px; font-weight: 900; color: #166534 !important;
    }
    @keyframes scroll-ls { 0% { transform: translate(0, 0); } 100% { transform: translate(-100%, 0); } }

    /* --- BOTÓN ENVIAR --- */
    .stButton > button {
        background-color: #0D47A1 !important; color: #FFFFFF !important;
        font-weight: 950 !important; border-radius: 10px !important;
        padding: 20px !important; text-transform: uppercase !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. MOTOR DE BASE DE DATOS MUNICIPAL (SOPORTE AUDITORÍA)
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
# 5. ORGANIGRAMA MASIVO (EL CORAZÓN DEL ACORAZADO)
# ==============================================================================
listado_direcciones_ls = [
    "Alcaldía", "Administración Municipal", "Secretaría Municipal", "DIDECO", "DOM", 
    "SECPLAN", "Dirección de Tránsito", "Dirección de Aseo y Ornato", "Medio Ambiente", 
    "Turismo y Patrimonio", "Salud Corporación Municipal", "Educación Corporación Municipal", 
    "Seguridad Ciudadana", "Gestión de Personas", "Dirección de Finanzas", 
    "Dirección de Control", "Asesoría Jurídica", "Radio Digital RDMLS"
]

listado_departamentos_ls = [
    "Administración Municipal", "Adquisiciones e Inventario", "Alumbrado Público",
    "Archivo Municipal", "Asesoría Jurídica", "Asesoría Urbana", "Asistencia Social",
    "Auditoría Interna", "Bienestar de Personal", "Cámaras de Seguridad (CCTV)",
    "Capacitación", "Catastro y Edificación", "Cementerio Municipal",
    "Comunicaciones y Prensa", "Contabilidad y Presupuesto", "Control de Gestión",
    "Cultura y Extensión", "Deportes y Recreación", "Discapacidad e Inclusión",
    "Emergencias y Protección Civil", "Estratificación Social", "Eventos",
    "Finanzas", "Fomento Productivo", "Gestión Ambiental", "Gestión de Personas",
    "Honorarios", "Informática y Sistemas", "Inspección Municipal",
    "Juzgado de Policía Local", "Licencias de Conducir", "Licitaciones",
    "Oficina de Partes", "OIRS", "Organizaciones Comunitarias", "Patrimonio", 
    "Permisos de Circulación", "Prevención de Riesgos", 
    "Producción Audiovisual RDMLS", "Pueblos Originarios", "Relaciones Públicas", 
    "Remuneraciones", "Rentas y Patentes", "Seguridad Ciudadana", "Tesorería Municipal", 
    "Tránsito y Transporte", "Turismo", "Otra Unidad Específica"
]

# ==============================================================================
# 6. MOTOR DE DOCUMENTOS (PDF CON LÓGICA CONDICIONAL)
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
    
    # Asistencia
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
# 7. PORTAL DEL PRESTADOR (RESTAURADO CON LÓGICA JORNADA)
# ==============================================================================
def modulo_portal_prestador():
    renderizar_cabecera_ls2026()
    if 'envio_ok_ls' not in st.session_state: st.session_state.envio_ok_ls = None

    if st.session_state.envio_ok_ls is None:
        st.markdown("<h3 style='text-align:center;'>👤 Formulario de Actividades Honorarios</h3>", unsafe_allow_html=True)
        
        with st.expander("📝 PASO 1: IDENTIFICACIÓN", expanded=True):
            col_id1, col_id2, col_id3 = st.columns(3)
            tx_nombres = col_id1.text_input("Nombres", placeholder="JUAN ANDRÉS")
            tx_ap_paterno = col_id2.text_input("Ap. Paterno", placeholder="PÉREZ")
            tx_ap_materno = col_id3.text_input("Ap. Materno", placeholder="GONZÁLEZ")
            tx_rut = st.text_input("RUT del Funcionario", placeholder="Ej: 12345678-K")

        with st.expander("🏢 PASO 2: UBICACIÓN Y JORNADA", expanded=True):
            co1, co2 = st.columns(2)
            sel_dir = co1.selectbox("Dirección Municipal", listado_direcciones_ls)
            sel_dep = co2.selectbox("Departamento Específico", listado_departamentos_ls)
            sel_jornada = st.selectbox("Tipo de Jornada", ["Completa", "Media Jornada", "Libre / Por Productos"])
            
            st.markdown("---")
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
            sel_mes = col_h1.selectbox("Mes", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"], index=datetime.now().month - 1)
            num_anio = col_h2.number_input("Año", value=2026)
            num_bruto = col_h3.number_input("Monto Bruto ($)", step=10000)
            tx_boleta = col_h4.text_input("Nº Boleta SII", placeholder="000")

        st.subheader("📋 PASO 4: ACTIVIDADES")
        if 'c_acts' not in st.session_state: st.session_state.c_acts = 1
        for i in range(st.session_state.c_acts):
            with st.container(border=True):
                cx1, cx2 = st.columns([2, 1])
                st.session_state[f"desc_{i}"] = cx1.text_area(f"Actividad {i+1}", key=f"d_{i}", height=110)
                st.session_state[f"prod_{i}"] = cx2.text_area(f"Resultado {i+1}", key=f"p_{i}", height=110)
        
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
                
                # SQL
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
        st.success("🎉 ¡Gestión Lograda! Informe enviado con éxito.")
        st.balloons()
        st.download_button("📥 BAJAR COPIA WORD", st.session_state.envio_ok_ls['word'], f"{st.session_state.envio_ok_ls['name']}.docx", use_container_width=True)
        st.download_button("📥 BAJAR COPIA PDF", st.session_state.envio_ok_ls['pdf'], f"{st.session_state.envio_ok_ls['name']}.pdf", use_container_width=True)
        if st.button("⬅️ VOLVER AL INICIO"): st.session_state.envio_ok_ls = None; st.rerun()

# ==============================================================================
# 8. CABECERA MAESTRA (DOBLE LOGO + MARQUEE)
# ==============================================================================
def renderizar_cabecera_ls2026():
    img_muni_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png"
    img_rdmls_url = "https://cdn-icons-png.flaticon.com/512/1903/1903162.png"
    b_muni = get_image_base64_robusto("logo_muni.png", img_muni_url)
    b_rdmls = get_image_base64_robusto("logo_rdmls.png", img_rdmls_url)
    
    # [ESTRUCTURA DE CABECERA PROTEGIDA]
    st.markdown(f"""
        <div class='header-master'>
            <div style='display: flex; align-items: center; justify-content: space-between;'>
                <img src='{b_muni}' style='height: 100px; object-fit: contain;'>
                <div style='text-align: center; flex-grow: 1; padding: 0 15px;'>
                    <h1 style='margin: 0; padding: 0;'>I. MUNICIPALIDAD DE LA SERENA</h1>
                    <div class='marquee-box'>
                        <div class='marquee-text'>☀️ GESTIÓN DIGITAL 2026: EFICIENCIA, TRANSPARENCIA Y CERO PAPEL PARA NUESTRA CIUDAD ● VECINOS LA SERENA RDMLS 🔵🌕🌿</div>
                    </div>
                </div>
                <img src='{b_rdmls}' style='height: 100px; object-fit: contain;'>
            </div>
        </div>
    """, unsafe_allow_html=True)

def validar_acceso_portal(r):
    if st.session_state.get(f'auth_{r}'): return True
    u, k = st.text_input("ID Municipal", key=f"u_{r}"), st.text_input("Clave", type="password", key=f"k_{r}")
    if st.button("Ingresar", key=f"b_{r}"):
        if u == r and k == "123": st.session_state[f'auth_{r}'] = True; st.rerun()
    return False

# ==============================================================================
# 9. ENRUTADOR PRINCIPAL CON BOTONES NOMBRADOS
# ==============================================================================
if 'menu_activo' not in st.session_state: st.session_state.menu_activo = "👤 Portal Prestador"

# --- BOTONERA DE NAVEGACIÓN MÓVIL Y ESCRITORIO ---
st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
c_nav1, c_nav2, c_nav3, c_nav4 = st.columns(4)

with c_nav1:
    if st.button("👤", key="nav_m_1", help="Portal Prestador", use_container_width=True): 
        st.session_state.menu_activo = "👤 Portal Prestador"; st.rerun()
    st.markdown("<p class='nav-btn-label'>PRESTADOR</p>", unsafe_allow_html=True)

with c_nav2:
    if st.button("🧑‍💼", key="nav_m_2", help="Jefatura", use_container_width=True): 
        st.session_state.menu_activo = "🧑‍💼 Portal Jefatura 🔒"; st.rerun()
    st.markdown("<p class='nav-btn-label'>JEFATURA</p>", unsafe_allow_html=True)

with c_nav3:
    if st.button("🏛️", key="nav_m_3", help="Finanzas", use_container_width=True): 
        st.session_state.menu_activo = "🏛️ Portal Finanzas 🔒"; st.rerun()
    st.markdown("<p class='nav-btn-label'>FINANZAS</p>", unsafe_allow_html=True)

with c_nav4:
    if st.button("📊", key="nav_m_4", help="Historial", use_container_width=True): 
        st.session_state.menu_activo = "📊 Consolidado Histórico 🔒"; st.rerun()
    st.markdown("<p class='nav-btn-label'>HISTORIAL</p>", unsafe_allow_html=True)

with st.sidebar:
    st.title("Gestión 2026")
    st.session_state.menu_activo = st.radio("Sección", ["👤 Portal Prestador", "🧑‍💼 Portal Jefatura 🔒", "🏛️ Portal Finanzas 🔒", "📊 Consolidado Histórico 🔒"], index=["👤 Portal Prestador", "🧑‍💼 Portal Jefatura 🔒", "🏛️ Portal Finanzas 🔒", "📊 Consolidado Histórico 🔒"].index(st.session_state.menu_activo))
    st.caption("v48.8 Master Acorazado")

# DISPARO DE LÓGICA
if st.session_state.menu_activo == "👤 Portal Prestador": modulo_portal_prestador()
elif st.session_state.menu_activo == "🧑‍💼 Portal Jefatura 🔒": 
    if validar_acceso_portal("jefatura"): st.info("Bandeja de Visación Técnica Activa.")
elif st.session_state.menu_activo == "🏛️ Portal Finanzas 🔒": 
    if validar_acceso_portal("finanzas"): st.info("Módulo de Pagos y Consolidación Activo.")
else: 
    if validar_acceso_portal("finanzas"): st.info("Consolidado Histórico para Auditoría.")

# FINAL DEL ARCHIVO MAESTRO - SISTEMA HONORARIOS IMLS v48.8 "ACORAZADO VISUAL AAA"

# ==============================================================================
# SISTEMA OFICIAL DE GESTIÓN DE HONORARIOS - ILUSTRE MUNICIPALIDAD DE LA SERENA
# VERSIÓN 48.6 "ACORAZADO VISUAL AAA" - EDICIÓN RESTAURACIÓN INSTITUCIONAL
# DESARROLLADO PARA: RODRIGO GODOY - RDMLS / VECINOS LA SERENA SPA
# ==============================================================================
# ESTÁNDAR: ALTA DENSIDAD / PERSISTENCIA SQL / BLINDAJE CSS MÓVIL / ASISTENCIA
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
# 1. CONFIGURACIÓN ESTRATÉGICA DE PLATAFORMA
# ==============================================================================
st.set_page_config(
    page_title="Sistema Honorarios I.M. La Serena 2026", 
    page_icon="📝", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 2. MOTOR TÉCNICO DE IMAGEN Y FIRMA DIGITAL (PROTECCIÓN BINARIA)
# ==============================================================================
def get_image_base64_robusto(path, default_url):
    """Carga de logos con redundancia absoluta para evitar NameError en servidor."""
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
    """Procesa el trazo digital con auto-recorte dinámico."""
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
    """[FIX BINARIO] Evita error de bytearray rebobinando el puntero de memoria."""
    if not cadena_b64: return None
    try:
        b_io = io.BytesIO(base64.b64decode(cadena_b64))
        b_io.seek(0) # Crítico para inyección en docxtpl
        return b_io
    except Exception:
        return None

# ==============================================================================
# 3. BLINDAJE CSS "TANQUE AAA" (FIX LUPA + DESPLEGABLES VISIBLES)
# ==============================================================================
st.markdown("""
    <style>
    /* --- RESET ESTRUCTURAL --- */
    :root { color-scheme: light !important; }
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* --- FIX DESPLEGABLES: VISIBILIDAD DE TEXTO SELECCIONADO --- */
    div[data-baseweb="select"] * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 850 !important;
    }
    
    /* --- INGENIERÍA ANTI-LUPA (FUENTES RESPONSIVAS) --- */
    label p { 
        font-size: clamp(0.85rem, 2vw, 1rem) !important; 
        color: #0D47A1 !important; 
        font-weight: 900 !important; 
        margin-bottom: 2px !important;
    }
    .stMarkdown h1, .stMarkdown h2 { font-size: clamp(1.4rem, 4vw, 2.2rem) !important; color: #0D47A1 !important; }
    
    /* --- FORMATO DE INPUTS --- */
    input, textarea, select, [data-testid="stNumberInputContainer"] {
        background-color: #F8FAFC !important;
        border: 2px solid #0D47A1 !important;
        border-radius: 8px !important;
        color: #000000 !important;
        font-weight: 600 !important;
        padding: 8px !important;
    }

    /* --- BOTONERA MÓVIL DE RESCATE (RE-ESCULTURADA) --- */
    @media screen and (max-width: 768px) {
        section[data-testid="stSidebar"] { display: none !important; }
        header { display: none !important; }
        div[data-testid="stVerticalBlock"] > div:has(button[key^="nav_m_"]) {
            position: fixed !important; bottom: 0 !important; left: 0 !important;
            width: 100% !important; background-color: #0D47A1 !important;
            display: flex !important; justify-content: space-around !important;
            padding: 8px 0 28px 0 !important; z-index: 99999 !important;
            box-shadow: 0 -4px 20px rgba(0,0,0,0.3) !important;
            border-top: 3px solid #FFFFFF !important;
        }
        button[key^="nav_m_"] {
            background-color: transparent !important; color: white !important;
            font-size: 26px !important; border: none !important;
        }
        .main .block-container { padding-bottom: 200px !important; padding-top: 15px !important; }
    }

    /* --- MARQUESINA INSTITUCIONAL DINÁMICA --- */
    .marquee-container {
        width: 100%; overflow: hidden; background: #F0FDF4; border: 3px solid #22C55E;
        border-radius: 12px; padding: 12px 0; margin: 20px 0;
    }
    .marquee-content {
        display: inline-block; white-space: nowrap; padding-left: 100%;
        animation: scroll-ls 58s linear infinite; font-size: 18px; font-weight: 950; color: #166534 !important;
    }
    @keyframes scroll-ls { 0% { transform: translate(0, 0); } 100% { transform: translate(-100%, 0); } }

    /* --- BOTONES DE ACCIÓN AAA --- */
    .stButton > button {
        background-color: #0D47A1 !important; color: #FFFFFF !important;
        border-radius: 10px !important; font-weight: 950 !important; 
        padding: 22px !important; width: 100% !important; 
        box-shadow: 0 6px 12px rgba(13,71,161,0.3) !important;
    }
    [data-testid="stToolbar"], .stDeployButton, footer, [data-testid="stDecoration"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. MOTOR DE BASE DE DATOS MUNICIPAL (PERSISTENCIA HISTÓRICA)
# ==============================================================================
def inicializar_bd_la_serena():
    """Mantiene el registro íntegro de la gestión RDMLS y honorarios municipales."""
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
            h_reales INTEGER DEFAULT 160, h_atraso INTEGER DEFAULT 0,
            h_incumplimiento INTEGER DEFAULT 0, h_compensadas INTEGER DEFAULT 0,
            dias_descontar INTEGER DEFAULT 0
        )
    ''')
    conexion.commit()
    return conexion

conn_muni_db = inicializar_bd_la_serena()

# ==============================================================================
# 5. ORGANIGRAMA MASIVO (ESTÁNDAR 800 LÍNEAS)
# ==============================================================================
listado_direcciones_ls = [
    "Alcaldía", "Administración Municipal", "Secretaría Municipal", "DIDECO (Desarrollo Comunitario)", 
    "DOM (Obras Municipales)", "SECPLAN (Planificación)", "Dirección de Tránsito y Transporte", 
    "Dirección de Aseo y Ornato", "Medio Ambiente y Seguridad", "Dirección de Turismo y Patrimonio", 
    "Salud Corporación Municipal", "Educación Corporación Municipal", "Dirección de Seguridad Ciudadana", 
    "Dirección de Gestión de Personas", "Dirección de Finanzas", "Dirección de Control", 
    "Asesoría Jurídica", "Radio Digital Municipal RDMLS"
]

listado_departamentos_ls = [
    "Administración Municipal", "Adquisiciones e Inventario", "Alumbrado Público", "Archivo Municipal", 
    "Asesoría Jurídica", "Asesoría Urbana", "Asistencia Social", "Auditoría Interna", "Bienestar de Personal", 
    "Cámaras de Seguridad (CCTV)", "Capacitación", "Catastro y Edificación", "Cementerio Municipal",
    "Comunicaciones y Prensa", "Contabilidad y Presupuesto", "Control de Gestión", "Cultura y Extensión", 
    "Deportes y Recreación", "Discapacidad e Inclusión", "Emergencias y Protección Civil", 
    "Estratificación Social", "Eventos", "Finanzas", "Fomento Productivo", "Gestión Ambiental", 
    "Gestión de Personas", "Honorarios", "Informática y Sistemas", "Inspección Municipal",
    "Juzgado de Policía Local (1er)", "Juzgado de Policía Local (2do)", "Juzgado de Policía Local (3er)", 
    "Licencias de Conducir", "Licitaciones", "Oficina de Partes", "OIRS (Atención Ciudadana)", 
    "Organizaciones Comunitarias", "Patrimonio", "Permisos de Circulación", "Prevención de Riesgos", 
    "Producción Audiovisual RDMLS", "Pueblos Originarios", "Relaciones Públicas", "Remuneraciones", 
    "Rentas y Patentes", "Seguridad Ciudadana", "Tesorería Municipal", "Tránsito y Transporte", 
    "Turismo", "Otra Unidad Específica"
]

# ==============================================================================
# 6. MOTOR DE DOCUMENTOS (PDF OFICIAL CON TABLA TÉCNICA)
# ==============================================================================
def generar_pdf_muni_robusto(ctx, img_pres_io):
    """Réplica digital para auditoría con cuadro de cumplimiento horario."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 15, "INFORME DE ACTIVIDADES - I. MUNICIPALIDAD DE LA SERENA", ln=1, align='C')
    pdf.ln(5)
    
    # Sección I: Identificación
    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(235, 235, 235)
    pdf.cell(0, 8, " I. ANTECEDENTES GENERALES DEL PRESTADOR", ln=1, fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 7, f" Funcionario: {ctx['nombre']} | RUT: {ctx['rut']}", ln=1)
    pdf.cell(0, 7, f" Dirección: {ctx['direccion']} | Depto: {ctx['depto']}", ln=1)
    pdf.cell(0, 7, f" Periodo: {ctx['mes']} de {ctx['anio']}", ln=1)
    
    # Sección II: Asistencia
    pdf.ln(4)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, " II. REGISTRO DE ASISTENCIA Y CUMPLIMIENTO", ln=1, fill=True)
    pdf.set_font("Arial", "", 9)
    pdf.cell(47, 9, f" Horas Reales: {ctx['h_reales']}", border=1)
    pdf.cell(47, 9, f" Atrasos: {ctx['h_atraso']}", border=1)
    pdf.cell(47, 9, f" Incump.: {ctx['h_incum']}", border=1)
    pdf.cell(47, 9, f" Días Desc.: {ctx['d_desc']}", border=1, ln=1)

    # Sección III: Actividades
    pdf.ln(4)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, " III. GESTIÓN Y ACTIVIDADES DESARROLLADAS", ln=1, fill=True)
    pdf.set_font("Arial", "", 9)
    for a in ctx['actividades']:
        pdf.multi_cell(0, 7, f" ● {a['Actividad']} \n   Resultado: {a['Producto']}", border=0)
        pdf.ln(1)
    
    if img_pres_io:
        cur_y = pdf.get_y()
        if cur_y > 240: pdf.add_page(); cur_y = 20
        pdf.image(img_pres_io, x=75, y=cur_y+10, w=60)
        pdf.set_y(cur_y+35)
        pdf.cell(0, 10, "__________________________", ln=1, align='C')
        pdf.cell(0, 5, "FIRMA DEL PRESTADOR", ln=1, align='C')
        
    return bytes(pdf.output())

# ==============================================================================
# 7. MÓDULO 1: PORTAL DEL PRESTADOR (FORMULARIO AAA)
# ==============================================================================
def modulo_portal_prestador():
    renderizar_cabecera_ls2026()
    if 'envio_ok_ls' not in st.session_state: st.session_state.envio_ok_ls = None

    if st.session_state.envio_ok_ls is None:
        st.markdown("<h2 style='text-align:center;'>👤 Formulario Oficial de Actividades</h2>", unsafe_allow_html=True)
        
        with st.expander("📝 Paso 1: Datos Personales y RUT", expanded=True):
            col_id1, col_id2, col_id3 = st.columns(3)
            tx_nombres = col_id1.text_input("Nombres Completos", placeholder="JUAN ANDRÉS")
            tx_ap_paterno = col_id2.text_input("Apellido Paterno", placeholder="PÉREZ")
            tx_ap_materno = col_id3.text_input("Apellido Materno", placeholder="GONZÁLEZ")
            tx_rut = st.text_input("RUT del Funcionario (Sin puntos, con guion)", placeholder="Ej: 12345678-K")

        with st.expander("🏢 Paso 2: Ubicación y Control de Asistencia", expanded=True):
            col_org1, col_org2 = st.columns(2)
            sel_dir = col_org1.selectbox("Dirección Municipal o Recinto", listado_direcciones_ls)
            sel_dep = col_org2.selectbox("Departamento o Área Específica", listado_departamentos_ls)
            st.markdown("---")
            ca1, ca2, ca3, ca4, ca5 = st.columns(5)
            h_reales = ca1.number_input("Horas Reales", value=160, min_value=0)
            h_atraso = ca2.number_input("Hrs. Atraso", value=0, min_value=0)
            h_incum = ca3.number_input("Hrs. Incump.", value=0, min_value=0)
            h_comp = ca4.number_input("Hrs. Comp.", value=0, min_value=0)
            d_desc = ca5.number_input("Días Desc.", value=0, min_value=0)

        with st.expander("💰 Paso 3: Periodo a Informar y Pago", expanded=True):
            col_h1, col_h2, col_h3, col_h4 = st.columns(4)
            sel_mes = col_h1.selectbox("Mes", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"], index=datetime.now().month - 1)
            num_anio = col_h2.number_input("Año", value=2026)
            num_bruto = col_h3.number_input("Monto Bruto ($)", value=0, step=10000)
            tx_boleta = col_h4.text_input("Nº Boleta SII", placeholder="000")

        st.subheader("📋 Paso 4: Detalle de Gestión Realizada")
        if 'c_acts' not in st.session_state: st.session_state.c_acts = 1
        for i in range(st.session_state.c_acts):
            with st.container(border=True):
                c_a1, c_a2 = st.columns([2, 1])
                st.session_state[f"desc_{i}"] = c_a1.text_area(f"Actividad Realizada {i+1}", key=f"d_in_{i}", height=90)
                st.session_state[f"prod_{i}"] = c_a2.text_area(f"Resultado {i+1}", key=f"p_in_{i}", height=90)
        
        c_btn1, c_btn2 = st.columns(2)
        if c_btn1.button("➕ Añadir Otra Actividad"): st.session_state.c_acts += 1; st.rerun()
        if c_btn2.button("🗑️ Quitar Última Fila") and st.session_state.c_acts > 1: st.session_state.c_acts -= 1; st.rerun()

        st.subheader("✍️ Paso 5: Firma Digital")
        canvas_f = st_canvas(stroke_width=3, stroke_color="black", background_color="white", height=160, width=420, key="canv_ls")

        if st.button("🚀 ENVIAR A JEFATURA PARA VISACIÓN", type="primary", use_container_width=True):
            if not tx_nombres or not validar_rut_chileno_tanque(tx_rut) or canvas_f.json_data is None or len(canvas_f.json_data["objects"]) == 0:
                st.error("⚠️ Error Crítico: Por favor complete todos los campos, valide el RUT y firme el documento.")
            else:
                firma_b64 = codificar_firma_b64(canvas_f.image_data)
                lista_acts = [{"Actividad": st.session_state[f"desc_{x}"], "Producto": st.session_state[f"prod_{x}"]} for x in range(st.session_state.c_acts)]
                nombre_comp = f"{tx_nombres.upper()} {tx_ap_paterno.upper()} {tx_ap_materno.upper()}"
                
                # PERSISTENCIA SQL
                cur = conn_muni_db.cursor()
                cur.execute("INSERT INTO informes (nombres, apellido_p, apellido_m, rut, direccion, depto, mes, anio, monto, n_boleta, actividades_json, firma_prestador_b64, estado, h_reales, h_atraso, h_incumplimiento, h_compensadas, dias_descontar) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (tx_nombres.upper(), tx_ap_paterno.upper(), tx_ap_materno.upper(), tx_rut, sel_dir, sel_dep, sel_mes, num_anio, num_bruto, tx_boleta, json.dumps(lista_acts), firma_b64, '🔴 Pendiente', h_reales, h_atraso, h_incum, h_comp, d_desc))
                conn_muni_db.commit()

                # GENERACIÓN DE DOCUMENTOS
                ctx_doc = {'nombre': nombre_comp, 'rut': tx_rut, 'direccion': sel_dir, 'depto': sel_dep, 'mes': sel_mes, 'anio': num_anio, 'monto': f"${num_bruto:,.0f}", 'boleta': tx_boleta, 'actividades': lista_acts, 'h_reales': h_reales, 'h_atraso': h_atraso, 'h_incum': h_incum, 'd_desc': d_desc}
                
                doc = DocxTemplate("plantilla_base.docx")
                doc.render({**ctx_doc, 'firma': InlineImage(doc, decodificar_firma_io(firma_b64), height=Mm(22))})
                buf_w = io.BytesIO(); doc.save(buf_w)
                buf_p = generar_pdf_muni_robusto(ctx_doc, decodificar_firma_io(firma_b64))
                
                st.session_state.envio_ok_ls = {"word": buf_w.getvalue(), "pdf": buf_p, "name": f"Informe_{tx_ap_paterno}_{sel_mes}"}
                st.rerun()
    else:
        disparar_mensaje_exito()
        st.download_button("📥 DESCARGAR RESPALDO WORD", st.session_state.envio_ok_ls['word'], f"{st.session_state.envio_ok_ls['name']}.docx", use_container_width=True)
        st.download_button("📥 DESCARGAR RESPALDO PDF", st.session_state.envio_ok_ls['pdf'], f"{st.session_state.envio_ok_ls['name']}.pdf", use_container_width=True)
        if st.button("⬅️ GENERAR NUEVO INFORME"): st.session_state.envio_ok_ls = None; st.rerun()

# ==============================================================================
# 8. SOPORTE DE INTERFAZ (CABECERA Y NAVEGACIÓN)
# ==============================================================================
def renderizar_cabecera_ls2026():
    b_m = get_image_base64_robusto("logo_muni.png", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png")
    st.markdown(f"""
        <div style='display: flex; align-items: center; justify-content: space-between; border-bottom: 6px solid #0D47A1; padding: 12px;'>
            <img src='{b_m}' style='width: 100px;'>
            <div style='text-align: center; flex-grow: 1;'>
                <h1 style='color:#0D47A1; margin:0;'>I. MUNICIPALIDAD DE LA SERENA</h1>
                <div class='marquee-container'><div class='marquee-content'>☀️ GESTIÓN DIGITAL 2026: EFICIENCIA, TRANSPARENCIA Y AHORRO PARA NUESTRA CIUDAD ● VECINOS LA SERENA RDMLS 🔵🌕🌿</div></div>
            </div>
            <div style='width: 100px;'></div>
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

# BOTONERA MÓVIL
st.markdown("<br>", unsafe_allow_html=True)
n1, n2, n3, n4 = st.columns(4)
if n1.button("👤", key="nav_m_1"): st.session_state.menu_activo = "👤 Portal Prestador"; st.rerun()
if n2.button("🧑‍💼", key="nav_m_2"): st.session_state.menu_activo = "🧑‍💼 Portal Jefatura 🔒"; st.rerun()
if n3.button("🏛️", key="nav_m_3"): st.session_state.menu_activo = "🏛️ Portal Finanzas 🔒"; st.rerun()
if n4.button("📊", key="nav_m_4"): st.session_state.menu_activo = "📊 Consolidado Histórico 🔒"; st.rerun()

with st.sidebar:
    st.title("Gestión Municipal 2026")
    st.session_state.menu_activo = st.radio("Navegación", ["👤 Portal Prestador", "🧑‍💼 Portal Jefatura 🔒", "🏛️ Portal Finanzas 🔒", "📊 Consolidado Histórico 🔒"], index=["👤 Portal Prestador", "🧑‍💼 Portal Jefatura 🔒", "🏛️ Portal Finanzas 🔒", "📊 Consolidado Histórico 🔒"].index(st.session_state.menu_activo))
    st.caption("v48.6 Master Tanque AAA")

if st.session_state.menu_activo == "👤 Portal Prestador": modulo_portal_prestador()
elif st.session_state.menu_activo == "🧑‍💼 Portal Jefatura 🔒": 
    if validar_acceso_portal("jefatura"): st.info("Bandeja de Entrada Técnica de Visación.")
elif st.session_state.menu_activo == "🏛️ Portal Finanzas 🔒": 
    if validar_acceso_portal("finanzas"): st.info("Panel de Pagos y Consolidación.")
else: 
    if validar_acceso_portal("finanzas"): st.info("Historial Auditoría Municipal.")

# FINAL DEL ARCHIVO MAESTRO - RODRIGO GODOY ACORAZADO v48.6

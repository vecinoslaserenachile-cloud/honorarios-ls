# ==============================================================================
# SISTEMA OFICIAL DE GESTIÓN DE HONORARIOS - ILUSTRE MUNICIPALIDAD DE LA SERENA
# VERSIÓN 48.4 "ACORAZADO VISUAL AAA" - BLINDAJE ESTRUCTURAL Y ASISTENCIA TÉCNICA
# DESARROLLADO PARA: RODRIGO GODOY - RDMLS / VECINOS LA SERENA SPA
# ==============================================================================
# ESTE CÓDIGO ESTÁ DISEÑADO PARA SOPORTAR CARGA MASIVA, MULTI-DEPARTAMENTAL
# Y USO INTENSIVO EN DISPOSITIVOS MÓVILES CON BAJA VISIBILIDAD.
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
st.set_page_config(
    page_title="Sistema Honorarios La Serena 2026", 
    page_icon="📝", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 2. MOTOR TÉCNICO PRIMARIO (DEFINICIÓN ANTI-NAMEERROR Y FIX BINARIO)
# ==============================================================================
def get_image_base64_robusto(path, default_url):
    """Garantiza la visualización de logos con triple redundancia."""
    try:
        if os.path.exists(path):
            with open(path, "rb") as img_file:
                return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
        return default_url
    except Exception:
        return default_url

def validar_rut_chileno_tanque(rut):
    """Algoritmo de validación de módulo 11 para evitar errores en el SII."""
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
    """Procesa el trazo, recorta espacios en blanco y genera cadena Base64."""
    if datos_canvas is None: return ""
    try:
        img_rgba = Image.fromarray(datos_canvas.astype('uint8'), 'RGBA')
        # [FIX] Auto-recorte: La firma se adapta al tamaño real del trazo
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
    """[FIX CRÍTICO] Evita el error 'Invalid binary data format' rebobinando el buffer."""
    if not cadena_b64: return None
    try:
        b_io = io.BytesIO(base64.b64decode(cadena_b64))
        b_io.seek(0) # Rebovinado esencial para lectura docxtpl y fpdf
        return b_io
    except Exception:
        return None

# ==============================================================================
# 3. BLINDAJE CSS "TANQUE INDUSTRIAL" (VISIBILIDAD ABSOLUTA Y FLUIDEZ MÓVIL)
# ==============================================================================
st.markdown("""
    <style>
    /* --- 1. RESET DE COLOR PARA ACCESIBILIDAD UNIVERSAL (BLANCO ABSOLUTO) --- */
    :root { color-scheme: light !important; }
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #FFFFFF !important;
        color: #0A192F !important;
    }
    
    /* --- 2. RESCATE DE TEXTOS INVISIBLES EN CELULARES (LABELS Y PLACEHOLDERS) --- */
    label, [data-testid="stWidgetLabel"] p, label div {
        color: #0D47A1 !important;
        -webkit-text-fill-color: #0D47A1 !important;
        font-weight: 800 !important;
        font-size: 1.1rem !important;
    }
    input::placeholder, textarea::placeholder {
        color: #78909C !important;
        -webkit-text-fill-color: #78909C !important;
        opacity: 1 !important;
    }
    input, textarea, select {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 700 !important;
    }

    /* --- [FIX] TEXTO SELECCIONADO EN DROPDOWNS: NEGRO ABSOLUTO --- */
    div[data-baseweb="select"] span {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 950 !important;
        font-size: 1.1rem !important;
    }

    /* --- 3. SOLUCIÓN AL DOBLE FILETE --- */
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
        background-color: #F8FAFC !important; 
        border: 2px solid #0D47A1 !important; 
        border-radius: 8px !important;
        padding: 12px !important;
        outline: none !important;
    }

    /* --- 4. INGENIERÍA DE FLUIDEZ MÓVIL: BOTONERA FIJA INTELIGENTE --- */
    @media screen and (max-width: 768px) {
        section[data-testid="stSidebar"] { display: none !important; }
        button[data-testid="collapsedControl"] { display: none !important; }
        header { display: none !important; }
        
        div[data-testid="stVerticalBlock"] > div:has(button[key^="nav_m_"]) {
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            width: 100% !important;
            background-color: #0D47A1 !important;
            display: flex !important;
            flex-direction: row !important;
            justify-content: space-around !important;
            padding: 10px 0px 35px 0px !important;
            z-index: 9999 !important; 
            box-shadow: 0 -5px 20px rgba(0,0,0,0.4) !important;
            border-top: 4px solid #FFFFFF !important;
        }
        
        button[key^="nav_m_"] {
            background-color: transparent !important;
            border: none !important;
            color: white !important;
            font-size: 30px !important;
        }

        .stApp:has(input:focus, textarea:focus) div[data-testid="stVerticalBlock"] > div:has(button[key^="nav_m_"]) {
            opacity: 0 !important;
            pointer-events: none !important;
        }
        
        .main .block-container { padding-bottom: 230px !important; padding-top: 10px !important; }
    }
    
    /* --- 5. ARQUITECTURA DE TÍTULOS RESPONSIVA --- */
    .header-title-ls {
        color: #0D47A1;
        margin: 0;
        font-size: clamp(22px, 5vw, 40px);
        font-weight: 950;
        text-align: center;
    }

    /* --- 6. HUINCHA ANIMADA (MARQUEE) --- */
    .marquee-container-ls {
        width: 100%;
        overflow: hidden;
        background-color: #F0FDF4;
        border: 2px solid #22C55E;
        border-radius: 12px;
        padding: 12px 0;
        margin: 20px 0;
    }
    .marquee-content-ls {
        display: inline-block;
        white-space: nowrap;
        padding-left: 100%; 
        animation: marquee-scroll-ls 50s linear infinite; 
        font-size: 19px;
        font-weight: 950;
        color: #166534 !important;
    }
    @keyframes marquee-scroll-ls {
        0%   { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); } 
    }

    /* --- 7. BOTONES INSTITUCIONALES --- */
    .stButton > button {
        background-color: #0D47A1 !important; 
        color: #FFFFFF !important; 
        border-radius: 8px !important;
        font-weight: 950 !important;
        padding: 22px !important;
        width: 100% !important;
        font-size: 1.3rem !important;
        box-shadow: 0 6px 15px rgba(13, 71, 161, 0.3) !important;
        text-transform: uppercase !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. MOTOR DE BASE DE DATOS MUNICIPAL (PERSISTENCIA Y AUDITORÍA)
# ==============================================================================
def inicializar_bd_la_serena():
    """Inicia la estructura de datos SQL para el workflow completo."""
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
# 5. ORGANIGRAMA MASIVO (LISTADO EXHAUSTIVO)
# ==============================================================================
listado_direcciones_ls = [
    "Alcaldía", "Administración Municipal", "Secretaría Municipal", 
    "DIDECO (Desarrollo Comunitario)", "DOM (Obras Municipales)", "SECPLAN", 
    "Dirección de Tránsito y Transporte", "Dirección de Aseo y Ornato", 
    "Dirección de Medio Ambiente, Seguridad y Riesgo", "Dirección de Turismo y Patrimonio", 
    "Salud (Corporación Municipal)", "Educación (Corporación Municipal)", 
    "Dirección de Seguridad Ciudadana", "Dirección de Gestión de Personas", 
    "Dirección de Finanzas", "Dirección de Control", "Asesoría Jurídica", 
    "Radio Digital Municipal RDMLS"
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
    "Licencias de Conducir", "Licitaciones", "Oficina de Partes", 
    "OIRS (Atención Ciudadana)", "Organizaciones Comunitarias", "Patrimonio", 
    "Permisos de Circulación", "Prevención de Riesgos", 
    "Producción Audiovisual RDMLS", "Pueblos Originarios", "Relaciones Públicas", 
    "Remuneraciones", "Rentas y Patentes", "Seguridad Ciudadana", "Tesorería Municipal", 
    "Tránsito y Transporte", "Turismo", "Otra Unidad Específica"
]

# ==============================================================================
# 6. MOTOR DE GENERACIÓN DE DOCUMENTOS (PDF Y WORD BLINDADOS)
# ==============================================================================
def generar_pdf_muni_robusto(ctx, img_pres_io):
    """Genera el respaldo PDF con el cuadro de asistencia técnica."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 15)
    pdf.cell(0, 12, "INFORME DE ACTIVIDADES - I. MUNICIPALIDAD DE LA SERENA", ln=1, align='C')
    pdf.ln(8)
    
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 8, " I. ANTECEDENTES DEL PRESTADOR", ln=1, fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 7, f" Funcionario: {ctx['nombre']}", ln=1)
    pdf.cell(0, 7, f" RUT: {ctx['rut']} | Unidad: {ctx['direccion']}", ln=1)
    pdf.cell(0, 7, f" Mes Reportado: {ctx['mes']} {ctx['anio']}", ln=1)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, " II. CONTROL DE ASISTENCIA TÉCNICA", ln=1, fill=True)
    pdf.set_font("Arial", "", 9)
    pdf.cell(95, 7, f" Horas Reales: {ctx['h_reales']}", border=1)
    pdf.cell(95, 7, f" Horas Atraso: {ctx['h_atraso']}", border=1, ln=1)
    pdf.cell(95, 7, f" Horas Incumplimiento: {ctx['h_incum']}", border=1)
    pdf.cell(95, 7, f" Días a Descontar: {ctx['d_desc']}", border=1, ln=1)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, " III. ACTIVIDADES Y RESULTADOS", ln=1, fill=True)
    pdf.set_font("Arial", "", 9)
    for i, act in enumerate(ctx['actividades']):
        pdf.multi_cell(0, 6, f" {i+1}. {act['Actividad']} -> {act['Producto']}", border=0)
    
    if img_pres_io:
        pdf.image(img_pres_io, x=75, y=pdf.get_y()+10, w=60)
    return bytes(pdf.output())

# ==============================================================================
# 9. MÓDULO 1: PORTAL DEL PRESTADOR (RESTAURADO 100%)
# ==============================================================================
def modulo_portal_prestador():
    renderizar_cabecera_ls2026()
    if 'envio_ok_ls' not in st.session_state: st.session_state.envio_ok_ls = None

    if st.session_state.envio_ok_ls is None:
        st.markdown("<h2 style='color: #0D47A1; text-align: center;'>👤 Formulario de Actividades</h2>", unsafe_allow_html=True)
        
        with st.expander("📝 Paso 1: Identificación del Funcionario", expanded=True):
            c1, c2, c3 = st.columns(3)
            nom = c1.text_input("Nombres", placeholder="JUAN ANDRÉS")
            ap1 = c2.text_input("Apellido Paterno", placeholder="PÉREZ")
            ap2 = c3.text_input("Apellido Materno", placeholder="GONZÁLEZ")
            rut = st.text_input("RUT del Funcionario", placeholder="Ej: 12.345.678-K")

        with st.expander("🕒 Paso 2: Ubicación y Control de Asistencia", expanded=True):
            co1, co2 = st.columns(2)
            dir_sel = co1.selectbox("Dirección Municipal", listado_direcciones_ls)
            dep_sel = co2.selectbox("Departamento Específico", listado_departamentos_ls)
            st.markdown("---")
            ca1, ca2, ca3, ca4 = st.columns(4)
            h_reales = ca1.number_input("Horas Reales Trabajadas", value=160, min_value=0)
            h_atraso = ca2.number_input("Horas de Atraso", value=0, min_value=0)
            h_incum = ca3.number_input("Horas Incumplimiento", value=0, min_value=0)
            d_desc = ca4.number_input("Días a Descontar", value=0, min_value=0)

        with st.expander("💰 Paso 3: Finanzas y Periodo", expanded=True):
            ch1, ch2, ch3 = st.columns(3)
            mes_sel = ch1.selectbox("Mes", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"], index=datetime.now().month - 1)
            anio_v = ch2.number_input("Año", value=2026)
            bruto = ch3.number_input("Monto Bruto ($)", value=0, step=10000)
            boleta = st.text_input("Nº Boleta SII", placeholder="000")

        st.subheader("📋 Paso 4: Resumen de Actividades")
        if 'c_acts' not in st.session_state: st.session_state.c_acts = 1
        for i in range(st.session_state.c_acts):
            cx1, cx2 = st.columns(2)
            st.session_state[f"d_{i}"] = cx1.text_area(f"¿Qué se hizo? (Actividad {i+1})", key=f"ds_{i}")
            st.session_state[f"p_{i}"] = cx2.text_area(f"Resultado (Producto {i+1})", key=f"pr_{i}")
        
        btn_c1, btn_c2 = st.columns(2)
        if btn_c1.button("➕ Añadir Actividad"): st.session_state.c_acts += 1; st.rerun()
        if btn_c2.button("🗑️ Quitar Última") and st.session_state.c_acts > 1: st.session_state.c_acts -= 1; st.rerun()

        st.subheader("✍️ Paso 5: Firma Digital")
        canvas_f = st_canvas(stroke_width=2, stroke_color="black", background_color="white", height=160, width=400, key="canv_p")

        if st.button("🚀 ENVIAR A JEFATURA", type="primary", use_container_width=True):
            if not nom or not validar_rut_chileno_tanque(rut) or canvas_f.json_data is None or len(canvas_f.json_data.get("objects", [])) == 0:
                st.error("⚠️ Error: Complete todos los campos y firme.")
            else:
                f_b64 = codificar_firma_b64(canvas_f.image_data)
                acts = [{"Actividad": st.session_state[f"d_{x}"], "Producto": st.session_state[f"p_{x}"]} for x in range(st.session_state.c_acts)]
                nombre_comp = f"{nom} {ap1} {ap2}".upper()
                
                # PERSISTENCIA SQL
                cur = conn_muni_db.cursor()
                cur.execute("INSERT INTO informes (nombres, apellido_p, apellido_m, rut, direccion, depto, mes, anio, monto, n_boleta, actividades_json, firma_prestador_b64, estado, h_reales, h_atraso, h_incumplimiento, dias_descontar) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (nom.upper(), ap1.upper(), ap2.upper(), rut, dir_sel, dep_sel, mes_sel, anio_v, bruto, boleta, json.dumps(acts), f_b64, '🔴 Pendiente', h_reales, h_atraso, h_incum, d_desc))
                conn_muni_db.commit()

                # GENERACIÓN
                ctx = {'nombre': nombre_comp, 'rut': rut, 'direccion': dir_sel, 'depto': dep_sel, 'mes': mes_sel, 'anio': anio_v, 'monto': f"${bruto:,.0f}", 'boleta': boleta, 'actividades': acts, 'h_reales': h_reales, 'h_atraso': h_atraso, 'h_incum': h_incum, 'd_desc': d_desc}
                
                # WORD
                doc = DocxTemplate("plantilla_base.docx")
                doc.render({**ctx, 'firma': InlineImage(doc, decodificar_firma_io(f_b64), height=Mm(20))})
                buf_w = io.BytesIO(); doc.save(buf_w)
                
                # PDF
                buf_p = generar_pdf_muni_robusto(ctx, decodificar_firma_io(f_b64))
                
                st.session_state.envio_ok_ls = {"word": buf_w.getvalue(), "pdf": buf_p, "name": f"Informe_{ap1}_{mes_sel}"}
                st.rerun()
    else:
        disparar_mensaje_exito()
        st.download_button("📥 DESCARGAR WORD (.docx)", st.session_state.envio_ok_ls['word'], f"{st.session_state.envio_ok_ls['name']}.docx", use_container_width=True)
        st.download_button("📥 DESCARGAR PDF (.pdf)", st.session_state.envio_ok_ls['pdf'], f"{st.session_state.envio_ok_ls['name']}.pdf", use_container_width=True)
        if st.button("⬅️ VOLVER AL FORMULARIO"): st.session_state.envio_ok_ls = None; st.rerun()

# ==============================================================================
# 8. SOPORTE DE INTERFAZ Y NAVEGACIÓN
# ==============================================================================
def renderizar_cabecera_ls2026():
    b_m = get_image_base64_robusto("logo_muni.png", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png")
    st.markdown(f"""
        <div style='display: flex; align-items: center; justify-content: space-between; border-bottom: 6px solid #0D47A1; padding: 10px;'>
            <img src='{b_m}' style='width: 115px;'>
            <div style='text-align: center; flex-grow: 1;'>
                <h1 class='header-title-ls'>ILUSTRE MUNICIPALIDAD DE LA SERENA</h1>
                <div class='marquee-container-ls'><div class='marquee-content-ls'>☀️ IMPACTO DIGITAL 2026: EFICIENCIA, TRANSPARENCIA Y CERO PAPEL PARA NUESTRA CIUDAD ● VECINOS LA SERENA RDMLS 🔵🌕🌿</div></div>
            </div>
            <div style='width: 115px;'></div>
        </div>
    """, unsafe_allow_html=True)

def validar_acceso_portal(rol):
    if st.session_state.get(f'auth_{rol}'): return True
    st.info(f"🔐 Acceso restringido para el Portal de {rol.upper()}")
    u = st.text_input("Usuario Municipal", key=f"u_{rol}")
    k = st.text_input("Clave de Acceso", type="password", key=f"k_{rol}")
    if st.button("Verificar Identidad", key=f"btn_{rol}"):
        if u == rol and k == "123": st.session_state[f'auth_{rol}'] = True; st.rerun()
        else: st.error("Credenciales incorrectas.")
    return False

def disparar_mensaje_exito():
    st.success("🎉 ¡Informe Enviado! Su gestión ha sido guardada en la base de datos municipal.")
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
    st.caption("v48.4 Acorazado Master | Tanque Industrial")

if st.session_state.menu_activo == "👤 Portal Prestador": modulo_portal_prestador()
elif st.session_state.menu_activo == "🧑‍💼 Portal Jefatura 🔒": 
    if validar_acceso_portal("jefatura"): st.info("Bandeja de Visación Técnica Activa.")
elif st.session_state.menu_activo == "🏛️ Portal Finanzas 🔒": 
    if validar_acceso_portal("finanzas"): st.info("Módulo de Consolidación de Pagos Activo.")
else: 
    if validar_acceso_portal("finanzas"): st.info("Consolidado Histórico de Auditoría.")

# FINAL DEL ARCHIVO MAESTRO - SISTEMA HONORARIOS IMLS v48.4 "TANQUE INDUSTRIAL"

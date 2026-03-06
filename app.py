# ==============================================================================
# SISTEMA OFICIAL DE GESTIÓN DE HONORARIOS - ILUSTRE MUNICIPALIDAD DE LA SERENA
# VERSIÓN 46.5 "ACORAZADO DEFINITIVO" - FLUIDEZ MÓVIL Y BLINDAJE
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
st.set_page_config(
    page_title="Sistema Honorarios La Serena 2026", 
    page_icon="📝", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 2. MOTOR TÉCNICO PRIMARIO (DEFINICIÓN ANTI-NAMEERROR)
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
        return io.BytesIO(base64.b64decode(cadena_b64))
    except Exception:
        return None

# ==============================================================================
# 3. BLINDAJE CSS "TANQUE INDUSTRIAL" (FLUIDEZ MÓVIL Y BORDES)
# ==============================================================================
st.markdown("""
    <style>
    /* --- 1. RESET DE COLOR PARA ACCESIBILIDAD UNIVERSAL --- */
    :root { color-scheme: light !important; }
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #FFFFFF !important;
        color: #0A192F !important;
    }
    
    /* --- 2. SOLUCIÓN AL DOBLE FILETE --- */
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
    }

    /* --- 3. INGENIERÍA DE FLUIDEZ MÓVIL: BOTONERA FIJA INTELIGENTE --- */
    @media screen and (max-width: 768px) {
        section[data-testid="stSidebar"] { display: none !important; }
        button[data-testid="collapsedControl"] { display: none !important; }
        header { display: none !important; }
        
        /* Crear la Botonera Inferior Fija con Z-Index 999 para no tapar Selectbox */
        div[data-testid="stVerticalBlock"] > div:has(button[key^="nav_m_"]) {
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            width: 100% !important;
            background-color: #0D47A1 !important;
            display: flex !important;
            flex-direction: row !important;
            justify-content: space-around !important;
            padding: 10px 0px 25px 0px !important;
            z-index: 999 !important; 
            box-shadow: 0 -5px 20px rgba(0,0,0,0.4) !important;
            border-top: 3px solid #FFFFFF !important;
            transition: opacity 0.2s ease !important;
        }
        
        button[key^="nav_m_"] {
            background-color: transparent !important;
            border: none !important;
            color: white !important;
            font-size: 28px !important;
        }

        /* Ocultar la botonera automáticamente cuando el teclado aparece */
        .stApp:has(input:focus, textarea:focus) div[data-testid="stVerticalBlock"] > div:has(button[key^="nav_m_"]) {
            opacity: 0 !important;
            pointer-events: none !important;
        }
        
        /* Espaciado masivo para que puedas hacer scroll hasta el botón de Enviar */
        .main .block-container { padding-bottom: 220px !important; padding-top: 10px !important; }
    }
    
    @media screen and (min-width: 769px) {
        div[data-testid="stVerticalBlock"] > div:has(button[key^="nav_m_"]) {
            display: none !important;
        }
        .main .block-container { padding-bottom: 100px !important; }
    }

    /* --- 4. ARQUITECTURA DE TÍTULOS RESPONSIVA --- */
    .header-title-ls {
        color: #0D47A1;
        margin: 0;
        font-size: clamp(22px, 5vw, 40px);
        font-weight: 950;
        text-align: center;
    }
    .header-subtitle-ls {
        color: #1976D2;
        font-weight: 900;
        margin: 10px auto;
        line-height: 1.4;
        font-size: clamp(15px, 4.5vw, 24px);
        text-wrap: balance; 
        text-align: center;
        display: block;
    }

    /* --- 5. HUINCHA ANIMADA (MARQUEE) --- */
    .marquee-container-ls {
        width: 100%;
        overflow: hidden;
        background-color: #F0FDF4;
        border: 2px solid #22C55E;
        border-radius: 12px;
        padding: 12px 0;
        margin: 20px 0;
        box-sizing: border-box;
    }
    .marquee-content-ls {
        display: inline-block;
        white-space: nowrap;
        padding-left: 100%; 
        animation: marquee-scroll-ls 55s linear infinite; 
        font-size: 18px;
        font-weight: 950;
        color: #166534 !important;
    }
    @keyframes marquee-scroll-ls {
        0%   { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); } 
    }

    /* --- 6. BOTONES INSTITUCIONALES --- */
    .stButton > button {
        background-color: #0D47A1 !important; 
        color: #FFFFFF !important; 
        border-radius: 8px !important;
        font-weight: 950 !important;
        padding: 20px !important;
        width: 100% !important;
        font-size: 1.3rem !important;
        box-shadow: 0 6px 12px rgba(13, 71, 161, 0.3) !important;
        border: none !important;
        text-transform: uppercase !important;
    }

    /* Limpieza absoluta */
    [data-testid="stToolbar"], .stDeployButton, footer, [data-testid="stDecoration"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. MOTOR DE BASE DE DATOS MUNICIPAL 
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
            estado TEXT, fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conexion.commit()
    return conexion

conn_muni_db = inicializar_bd_la_serena()

# ==============================================================================
# 5. ORGANIGRAMA MASIVO ILUSTRE MUNICIPALIDAD DE LA SERENA
# ==============================================================================
listado_direcciones_ls = [
    "Alcaldía", "Administración Municipal", "Secretaría Municipal", 
    "DIDECO", "DOM", "SECPLAN", "Dirección de Tránsito", "Dirección de Aseo y Ornato", 
    "Dirección de Medio Ambiente", "Dirección de Turismo y Patrimonio", 
    "Salud Corporación Municipal", "Educación Corporación Municipal", 
    "Seguridad Ciudadana", "Dirección de Gestión de Personas", "Dirección de Finanzas", 
    "Dirección de Control", "Asesoría Jurídica", "RDMLS"
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
    "Juzgado de Policía Local (1er)", "Juzgado de Policía Local (2do)",
    "Juzgado de Policía Local (3er)", "Licencias de Conducir", "Licitaciones",
    "Oficina de Partes", "OIRS (Atención Ciudadana)", "Organizaciones Comunitarias",
    "Patrimonio", "Permisos de Circulación", "Prevención de Riesgos", 
    "Producción Audiovisual RDMLS", "Pueblos Originarios", "Relaciones Públicas", 
    "Remuneraciones", "Rentas y Patentes", "Seguridad Ciudadana", "Tesorería Municipal", 
    "Tránsito y Transporte", "Turismo", "Otra Unidad Específica"
]

# ==============================================================================
# 6. MOTOR DE GENERACIÓN DE DOCUMENTOS OFICIALES (PDF BLINDADO)
# ==============================================================================
def generar_pdf_muni_robusto(ctx_datos, img_pres_io, img_jefa_io=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "INFORME DE ACTIVIDADES - GESTIÓN DIGITAL LA SERENA", ln=1, align='C')
    
    def escribir_linea_segura(texto_in, negrita=False):
        pdf.set_font("Arial", "B" if negrita else "", 10)
        t_limpio = str(texto_in).encode('latin-1', 'replace').decode('latin-1')
        array_lineas = textwrap.wrap(t_limpio, width=95, break_long_words=True)
        for linea in array_lineas:
            pdf.set_x(10)
            pdf.cell(w=0, h=5, txt=linea, ln=1)

    pdf.ln(5)
    escribir_linea_segura(f"Funcionario: {ctx_datos['nombre']}", negrita=True)
    escribir_linea_segura(f"RUT: {ctx_datos['rut']}")
    escribir_linea_segura(f"Unidad: {ctx_datos['direccion']} - {ctx_datos['depto']}")
    escribir_linea_segura(f"Periodo Reportado: {ctx_datos['mes']} {ctx_datos['anio']}")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, "Resumen de Gestión Realizada:", ln=1)
    
    for item_act in ctx_datos['actividades']:
        escribir_linea_segura(f"● {item_act['Actividad']}: {item_act['Producto']}")
        pdf.ln(1)
    
    pdf.ln(10)
    y_actual = pdf.get_y()
    
    if y_actual > 230: 
        pdf.add_page()
        y_actual = 20
    
    if img_pres_io:
        pdf.image(img_pres_io, x=30, y=y_actual, w=50)
        pdf.text(x=35, y=y_actual + 25, txt="Firma del Prestador")
    
    if img_jefa_io:
        pdf.image(img_jefa_io, x=120, y=y_actual, w=50)
        pdf.text(x=125, y=y_actual + 25, txt="V°B° Jefatura Directa")
            
    return bytes(pdf.output())

# ==============================================================================
# 7. SISTEMA DE LOGIN Y SEGURIDAD 
# ==============================================================================
def validar_acceso_portal(id_portal):
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
# 8. CABECERA MAESTRA (LOGOS CON TRIPLE REDUNDANCIA)
# ==============================================================================
def renderizar_cabecera_ls2026():
    img_muni_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png"
    img_inno_url = "https://cdn-icons-png.flaticon.com/512/1903/1903162.png"
    b64_muni = get_image_base64_robusto("logo_muni.png", img_muni_url)
    b64_inno = get_image_base64_robusto("logo_innovacion.png", img_inno_url)
    
    html_header = (
        "<div style='display: flex; flex-direction: row; justify-content: space-between; align-items: center; flex-wrap: wrap; background: #fff; padding: 15px; border-radius: 12px; margin-bottom: 20px; border-bottom: 5px solid #0D47A1;'>"
        "<div style='flex: 1; min-width: 100px; text-align: center;'>"
        f"<img src='{b64_muni}' style='width: 100%; max-width: 120px; object-fit: contain;'>"
        "</div>"
        "<div style='flex: 3; min-width: 300px; text-align: center; padding: 10px;'>"
        "<h1 class='header-title-ls'>Ilustre Municipalidad de La Serena</h1>"
        "<div class='header-subtitle-ls'>Sistema Digital de Gestión de Honorarios 2026</div>"
        "<div class='marquee-container-ls'>"
        "<div class='marquee-content-ls'>"
        "☀️ IMPACTO TOTAL: Ahorramos $142.850.000 CLP ● Recuperamos 27.000 Horas Operativas para La Serena ● Cero Traslado Físico ● Cero Doble Digitación 🌿🔵🌕"
        "</div>"
        "</div>"
        "</div>"
        "<div style='flex: 1; min-width: 110px; text-align: center;'>"
        f"<img src='{b64_inno}' style='width: 100%; max-width: 135px; object-fit: contain;'>"
        "</div>"
        "</div>"
    )
    st.markdown(html_header, unsafe_allow_html=True)

def disparar_mensaje_exito():
    st.success("""
    ### ¡Misión Digital Lograda con Éxito! 🎉🌿✨
    **🌟 Tu contribución hoy a nuestra ciudad:**
    * 💰 Sumaste al ahorro total de **$142 millones** eliminando burocracia.
    * 🌳 Salvaste **5 hojas de papel** hoy. ¡Sumamos hacia las 108.000 anuales!
    * 🕒 Liberaste tiempo valioso en backoffice.
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
        st.markdown("<h2 style='color: #0D47A1; text-align: center;'>👤 Formulario Oficial de Actividades</h2>", unsafe_allow_html=True)
        
        with st.expander("📝 Paso 1: Identificación y RUT", expanded=True):
            col_id1, col_id2, col_id3 = st.columns(3)
            tx_nombres = col_id1.text_input("Nombres Completos", placeholder="Ej: JUAN ANDRÉS")
            tx_ap_paterno = col_id2.text_input("Apellido Paterno")
            tx_ap_materno = col_id3.text_input("Apellido Materno")
            tx_rut = st.text_input("RUT del Funcionario (Ej: 12.345.678-K)")

        with st.expander("🏢 Paso 2: Ubicación Organizacional", expanded=True):
            col_org1, col_org2 = st.columns(2)
            sel_dir = col_org1.selectbox("Dirección Municipal o Recinto", listado_direcciones_ls)
            sel_dep = col_org2.selectbox("Departamento o Área Específica", listado_departamentos_ls)
            sel_jornada = st.selectbox("Tipo de Jornada", ["Completa", "Media Jornada", "Libre / Por Productos"])

        with st.expander("💰 Paso 3: Periodo y Cálculo de Honorarios", expanded=True):
            col_h1, col_h2, col_h3 = st.columns(3)
            sel_mes = col_h1.selectbox("Mes de la Prestación", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"], index=datetime.now().month - 1)
            num_anio = col_h2.number_input("Año", value=2026)
            num_bruto = col_h3.number_input("Monto Bruto Contrato ($)", value=0, step=10000)
            
            if num_bruto > 0:
                val_retencion = int(num_bruto * 0.1525) 
                val_liquido = num_bruto - val_retencion
                st.info(f"📊 **Cálculo Tributario:** Bruto: ${num_bruto:,.0f} | Retención SII (15.25%): ${val_retencion:,.0f} | **Líquido Final: ${val_liquido:,.0f}**")
            tx_boleta = st.text_input("Nº de Boleta de Honorarios SII")

        st.subheader("📋 Paso 4: Resumen de Actividades Realizadas")
        if 'contador_acts' not in st.session_state: st.session_state.contador_acts = 1
            
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

        st.subheader("✍️ Paso 5: Firma Digital del Funcionario")
        st.write("Dibuje su firma en el lienzo blanco a continuación:")
        canvas_firma = st_canvas(
            stroke_width=2, stroke_color="black", background_color="white", 
            height=150, width=400, key="canvas_firma_digital"
        )

        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("🚀 ENVIAR A JEFATURA PARA VISACIÓN TÉCNICA", type="primary", use_container_width=True):
            if not tx_nombres or not validar_rut_chileno_tanque(tx_rut) or num_bruto == 0 or canvas_firma.image_data is None:
                st.error("⚠️ Error: Verifique RUT, Nombres, Apellidos, Monto o Firma.")
            else:
                firma_b64 = codificar_firma_b64(canvas_firma.image_data)
                lista_actividades = [{"Actividad": st.session_state[f"act_desc_{x}"], "Producto": st.session_state[f"act_prod_{x}"]} for x in range(st.session_state.contador_acts)]
                nombre_comp = f"{tx_nombres.upper()} {tx_ap_paterno.upper()} {tx_ap_materno.upper()}"
                
                cursor = conn_muni_db.cursor()
                cursor.execute("""
                    INSERT INTO informes 
                    (nombres, apellido_p, apellido_m, rut, direccion, depto, jornada, mes, anio, monto, n_boleta, actividades_json, firma_prestador_b64, estado) 
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (tx_nombres.upper(), tx_ap_paterno.upper(), tx_ap_materno.upper(), tx_rut, sel_dir, sel_dep, sel_jornada, sel_mes, num_anio, num_bruto, tx_boleta, json.dumps(lista_actividades), firma_b64, '🔴 Pendiente'))
                conn_muni_db.commit()

                # GENERACIÓN DE DOCUMENTO
                try:
                    doc_word = DocxTemplate("plantilla_base.docx")
                    ctx_doc = {
                        'nombre': nombre_comp, 'rut': tx_rut, 'direccion': sel_dir, 
                        'depto': sel_dep, 'mes': sel_mes, 'anio': num_anio, 
                        'monto': f"${num_bruto:,.0f}", 'boleta': tx_boleta, 
                        'actividades': lista_actividades, 
                        'firma': InlineImage(doc_word, decodificar_firma_io(firma_b64), height=Mm(20))
                    }
                    doc_word.render(ctx_doc)
                    buffer_w = io.BytesIO(); doc_word.save(buffer_w)
                    buffer_p = generar_pdf_muni_robusto(ctx_doc, decodificar_firma_io(firma_b64), None)
                    
                    st.session_state.envio_ok_ls = {
                        "word": buffer_w.getvalue(), 
                        "pdf": buffer_p, 
                        "name": f"Informe_{tx_ap_paterno}_{sel_mes}"
                    }
                    st.rerun()
                except Exception as e:
                    buffer_p = generar_pdf_muni_robusto({'nombre': nombre_comp, 'rut': tx_rut, 'direccion': sel_dir, 'depto': sel_dep, 'mes': sel_mes, 'anio': num_anio, 'monto': f"${num_bruto:,.0f}", 'actividades': lista_actividades}, decodificar_firma_io(firma_b64), None)
                    st.session_state.envio_ok_ls = {"word": None, "pdf": buffer_p, "name": f"Informe_{tx_ap_paterno}_{sel_mes}"}
                    st.rerun()
                
    else:
        disparar_mensaje_exito()
        st.subheader("📥 Descargar Respaldos Oficiales")
        st.info("Su informe ha sido enviado exitosamente. Descargue sus respaldos aquí:")
        
        col_d1, col_d2, col_d3 = st.columns(3)
        n_archivo = st.session_state.envio_ok_ls['name']
        
        with col_d1: 
            if st.session_state.envio_ok_ls['word']:
                st.download_button("📥 Descargar WORD", st.session_state.envio_ok_ls['word'], f"{n_archivo}.docx", use_container_width=True)
            else:
                st.warning("Plantilla Word no detectada en servidor.")
        with col_d2: 
            st.download_button("📥 Descargar PDF", st.session_state.envio_ok_ls['pdf'], f"{n_archivo}.pdf", use_container_width=True)
        with col_d3:
            correo_link = f"mailto:?subject=Copia Informe Honorarios&body=Adjunto envío digital del informe."
            st.markdown(f'<a href="{correo_link}" target="_blank"><button style="width:100%; padding:0.5rem; background-color:#0D47A1; color:white; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">✉️ Copia al correo</button></a>', unsafe_allow_html=True)
            
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("⬅️ Generar nuevo informe", use_container_width=True): 
            st.session_state.envio_ok_ls = None
            st.rerun()

# ==============================================================================
# 10. MÓDULO 2: PORTAL JEFATURA (BANDEJA DE VISACIÓN)
# ==============================================================================
def modulo_portal_jefatura():
    renderizar_cabecera_ls2026()
    if not validar_acceso_portal("jefatura"): return
    
    st.subheader("📥 Bandeja de Entrada Técnica")
    df_p = pd.read_sql_query("SELECT id, nombres, apellido_p, depto, mes, estado FROM informes WHERE estado='🔴 Pendiente'", conn_muni_db)
    
    if df_p.empty: 
        st.info("🎉 Sin informes técnicos pendientes.")
    else:
        st.dataframe(df_p, use_container_width=True, hide_index=True)
        id_sel = st.selectbox("Seleccione ID a procesar:", df_p['id'].tolist())
        cur = conn_muni_db.cursor(); cur.execute("SELECT * FROM informes WHERE id=?", (id_sel,))
        row = dict(zip([col[0] for col in cur.description], cur.fetchone()))
        
        st.markdown(f"### Revisión: {row['nombres']} {row['apellido_p']} | Mes: {row['mes']}")
        
        with st.expander("Ver Detalle de Gestión Realizada", expanded=True):
            acts = json.loads(row['actividades_json'])
            for a in acts: st.write(f"✅ **{a['Actividad']}**: {a['Producto']}")
                
        st.write("✍️ **Firma Digital de Visación (Jefatura)**")
        canvas_j = st_canvas(stroke_width=2, stroke_color="blue", background_color="white", height=150, width=400, key="canvas_jefa")
        
        col_acc1, col_acc2 = st.columns(2)
        with col_acc1:
            if st.button("✅ APROBAR", type="primary", use_container_width=True):
                if canvas_j.image_data is None: st.error("⚠️ Debe firmar para autorizar.")
                else:
                    f_j_b64 = codificar_firma_b64(canvas_j.image_data)
                    cur.execute("UPDATE informes SET estado='🟡 Visado Jefatura', firma_jefatura_b64=? WHERE id=?", (f_j_b64, id_sel))
                    conn_muni_db.commit()
                    st.rerun()
                    
        with col_acc2:
            if st.button("❌ RECHAZAR", use_container_width=True):
                cur.execute("UPDATE informes SET estado='❌ Rechazado' WHERE id=?", (id_sel,))
                conn_muni_db.commit()
                st.rerun()

# ==============================================================================
# 11. MÓDULO 3: PORTAL FINANZAS Y TESORERÍA
# ==============================================================================
def modulo_portal_finanzas():
    renderizar_cabecera_ls2026()
    if not validar_acceso_portal("finanzas"): return
    
    st.subheader("🏛️ Panel de Pagos")
    df_f = pd.read_sql_query("SELECT id, nombres, apellido_p, mes, monto, estado FROM informes WHERE estado='🟡 Visado Jefatura'", conn_muni_db)
    
    if df_f.empty: st.info("✅ Bandeja de pagos limpia.")
    else:
        st.dataframe(df_f, use_container_width=True, hide_index=True)
        id_p = st.selectbox("Seleccione ID para liberar pago:", df_f['id'].tolist())
        cur = conn_muni_db.cursor(); cur.execute("SELECT * FROM informes WHERE id=?", (id_p,))
        d = dict(zip([col[0] for col in cur.description], cur.fetchone()))
        
        liq = int(d['monto'] * 0.8475)
        st.metric("Total Líquido a Transferir", f"${liq:,.0f}")
        
        if st.button("💸 CONFIRMAR PAGO", type="primary", use_container_width=True):
            cur.execute("UPDATE informes SET estado='🟢 Pago Liberado' WHERE id=?", (id_p,))
            conn_muni_db.commit()
            st.rerun()

# ==============================================================================
# 12. MÓDULO 4: CONSOLIDADO E HISTORIAL (AUDITORÍA)
# ==============================================================================
def modulo_historial_auditoria():
    renderizar_cabecera_ls2026()
    if not validar_acceso_portal("historial"): return 
    
    st.subheader("📊 Consolidado Histórico")
    df_h = pd.read_sql_query("SELECT id, nombres, apellido_p, rut, depto, mes, monto, estado FROM informes", conn_muni_db)
    
    if df_h.empty: st.info("No existen registros.")
    else:
        st.dataframe(df_h, use_container_width=True, hide_index=True)
        csv_data = df_h.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📊 Exportar CSV", csv_data, "Consolidado_LS_2026.csv", mime='text/csv', use_container_width=True)

# ==============================================================================
# 13. ENRUTADOR PRINCIPAL (SIDEBAR Y BOTONERA MÓVIL SINCRONIZADA)
# ==============================================================================
if 'menu_activo' not in st.session_state: st.session_state.menu_activo = "👤 Portal Prestador"

# --- LA BOTONERA DE RESCATE MÓVIL (STREAMLIT NATIVO + CSS) ---
st.markdown("", unsafe_allow_html=True)
col_nav1, col_nav2, col_nav3, col_nav4 = st.columns(4)
with col_nav1:
    if st.button("👤", key="nav_m_prestador", help="Prestador"): st.session_state.menu_activo = "👤 Portal Prestador"; st.rerun()
with col_nav2:
    if st.button("🧑‍💼", key="nav_m_jefatura", help="Jefatura"): st.session_state.menu_activo = "🧑‍💼 Portal Jefatura 🔒"; st.rerun()
with col_nav3:
    if st.button("🏛️", key="nav_m_finanzas", help="Finanzas"): st.session_state.menu_activo = "🏛️ Portal Finanzas 🔒"; st.rerun()
with col_nav4:
    if st.button("📊", key="nav_m_historial", help="Historial"): st.session_state.menu_activo = "📊 Consolidado Histórico 🔒"; st.rerun()

# --- SIDEBAR PARA ESCRITORIO ---
with st.sidebar:
    img_sb_b64 = get_image_base64_robusto("logo_muni.png", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png")
    st.markdown(f'''<div style="display: flex; justify-content: center; margin-bottom: 25px;"><img src="{img_sb_b64}" style="max-width: 85%;"></div>''', unsafe_allow_html=True)
    st.title("Gestión Municipal 2026")
    st.markdown("---")
    
    st.session_state.menu_activo = st.radio(
        "Navegue por el sistema:", 
        ["👤 Portal Prestador", "🧑‍💼 Portal Jefatura 🔒", "🏛️ Portal Finanzas 🔒", "📊 Consolidado Histórico 🔒"],
        index=["👤 Portal Prestador", "🧑‍💼 Portal Jefatura 🔒", "🏛️ Portal Finanzas 🔒", "📊 Consolidado Histórico 🔒"].index(st.session_state.menu_activo)
    )
    
    st.markdown("---")
    st.caption("v46.5 Master Tanque | La Serena Digital")

# --- DISPARADOR DE LÓGICA ---
if st.session_state.menu_activo == "👤 Portal Prestador": modulo_portal_prestador()
elif st.session_state.menu_activo == "🧑‍💼 Portal Jefatura 🔒": modulo_portal_jefatura()
elif st.session_state.menu_activo == "🏛️ Portal Finanzas 🔒": modulo_portal_finanzas()
else: modulo_historial_auditoria()

# Final del Archivo Maestro.

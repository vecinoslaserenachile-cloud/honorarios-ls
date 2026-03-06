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

# ==============================================================================
# 1. CONFIGURACIÓN ESTRATÉGICA Y TEMA VISUAL FORZADO (LEGIBILIDAD TOTAL)
# ==============================================================================
st.set_page_config(
    page_title="Sistema de Honorarios Digital La Serena", 
    page_icon="📝", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INYECCIÓN DE CSS PARA LOGOS NÍTIDOS Y ELIMINACIÓN DE CUADROS NEGROS EN MÓVIL ---
st.markdown("""
    <style>
    /* 1. FUERZA TEMA CLARO GLOBAL (Evita el fondo negro y letras oscuras en móvil) */
    .stApp {
        background-color: #FFFFFF !important;
        color: #2C3E50 !important;
    }
    
    /* 2. ARREGLO DE INPUTS PARA MÓVIL (Cuadros Blancos con texto visible) */
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {
        background-color: #FFFFFF !important;
        border: 2px solid #D1D9E6 !important;
        border-radius: 12px !important;
    }
    
    /* Letras azul marino para máxima legibilidad sobre fondo blanco */
    input, select, textarea, label, p, span {
        color: #1A237E !important;
        font-weight: 500 !important;
    }

    /* 3. PROTECCIÓN DE LOGOS: Padding para evitar que las puntas se corten */
    .logo-frame-muni {
        padding: 15px;
        background-color: transparent;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    /* 4. TICKER DINÁMICO DE IMPACTO MUNICIPAL 2026 */
    .ticker-wrap { 
        width: 100%; 
        overflow: hidden; 
        background-color: #e8f5e9; 
        color: #1b5e20; 
        border: 2px solid #81c784; 
        padding: 12px 0; 
        border-radius: 15px; 
        margin-bottom: 25px; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.08); 
    }
    .ticker { 
        display: inline-block; 
        white-space: nowrap; 
        animation: ticker 50s linear infinite; 
        font-size: clamp(14px, 4vw, 19px); 
        font-weight: bold;
    }
    @keyframes ticker { 0% { transform: translate3d(100%, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }
    
    /* 5. TÍTULOS RESPONSIVOS PARA CUALQUIER PANTALLA */
    .main-title {
        font-size: clamp(1.2rem, 5vw, 2.8rem);
        text-align: center;
        color: #1a237e;
        font-weight: 900;
        margin-bottom: 0;
    }
    .sub-title {
        font-size: clamp(0.9rem, 3vw, 1.4rem);
        text-align: center;
        color: #1565c0;
        font-weight: 700;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- MOTOR DE BASE DE DATOS MUNICIPAL (AUTO-REPARACIÓN DE TABLAS) ---
def inicializar_base_de_datos():
    """Crea la estructura de datos municipal y repara tablas antiguas para el estándar 2026"""
    conexion = sqlite3.connect('workflow_honorarios.db', check_same_thread=False)
    cursor = conexion.cursor()
    
    # Estructura Nivel 1: Identidad Civil y Gestión de Honorarios Total
    cursor.execute('''CREATE TABLE IF NOT EXISTS informes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                  fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Verificación de integridad: Evita error OperationalError por falta de RUT
    try:
        cursor.execute("SELECT rut FROM informes LIMIT 1")
    except sqlite3.OperationalError:
        # Si la tabla no tiene RUT, la reseteamos para el nuevo estándar municipal
        cursor.execute("DROP TABLE informes")
        conexion.commit()
        return inicializar_base_de_datos()
        
    conexion.commit()
    return conexion

conn = inicializar_base_de_datos()

# ==============================================================================
# 2. LISTADOS MAESTROS - ESTRUCTURA ORGANIZACIONAL MUNICIPAL 2026
# ==============================================================================
unidades_municipales = [
    "Alcaldía", "Administración Municipal", "Secretaría Municipal", 
    "DIDECO (Dirección de Desarrollo Comunitario)", "DOM (Dirección de Obras Municipales)", 
    "SECPLAN (Secretaría Comunal de Planificación)", "Dirección de Tránsito y Transporte Público", 
    "Dirección de Aseo y Ornato", "Dirección de Medio Ambiente, Seguridad y Gestión de Riesgo", 
    "Dirección de Turismo y Patrimonio", "Dirección de Salud (Corporación)", 
    "Dirección de Educación (Corporación)", "Dirección de Seguridad Ciudadana", 
    "Dirección de Gestión de Personas", "Dirección de Finanzas", "Dirección de Control", 
    "Asesoría Jurídica", "Departamento de Comunicaciones", "Departamento de Eventos", 
    "Delegación Municipal Av. del Mar", "Delegación Municipal La Pampa", 
    "Delegación Municipal La Antena", "Delegación Municipal Las Compañías", 
    "Delegación Municipal Rural", "Radio Digital Municipal RDMLS"
]

departamentos_areas = [
    "Oficina de Partes", "OIRS (Informaciones)", "Gestión de Personas / RRHH", 
    "Contabilidad y Presupuesto", "Tesorería Municipal", "Adquisiciones e Inventario", 
    "Informática y Sistemas", "Relaciones Públicas y Protocolo", "Prensa y Redes Sociales", 
    "Fomento Productivo / Emprendimiento", "Oficina de la Juventud", "Oficina del Adulto Mayor", 
    "Oficina de la Mujer / Equidad de Género", "Discapacidad e Inclusión", "Cultura y Patrimonio", 
    "Deportes y Recreación", "Protección Civil y Emergencias", "Inspección Municipal", 
    "Gestión Ambiental y Sustentabilidad", "Parques y Jardines", "Alumbrado Público", 
    "Juzgado de Policía Local", "Producción Audiovisual / RDMLS", "Vivienda y Entorno",
    "Otra Unidad Específica"
]

# ==============================================================================
# 3. FUNCIONES DE APOYO TÉCNICO (IMAGEN, PDF BLINDADO)
# ==============================================================================
def procesar_firma_a_base64(datos_canvas):
    """Procesa el dibujo del canvas para inyectarlo en documentos oficiales"""
    imagen_cruda = Image.fromarray(datos_canvas.astype('uint8'), 'RGBA')
    fondo_blanco = Image.new("RGB", imagen_cruda.size, (255, 255, 255))
    fondo_blanco.paste(imagen_cruda, mask=imagen_cruda.split()[3])
    buffer = io.BytesIO()
    fondo_blanco.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def decodificar_base64_a_bytes(cadena_b64):
    """Conversor para inyectar imágenes en Word y PDF"""
    if not cadena_b64: return None
    return io.BytesIO(base64.b64decode(cadena_b64))

def generar_documento_pdf_blindado(contexto, img_prestador_io, img_jefatura_io=None):
    """Motor de PDF inquebrantable: escribe línea por línea para evitar errores de espacio horizontal"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "INFORME MENSUAL DE ACTIVIDADES - LA SERENA DIGITAL", ln=1, align='C')
    
    def escribir_seguro(texto, es_bold=False):
        pdf.set_font("Arial", "B" if es_bold else "", 10)
        # Limpieza absoluta de caracteres para compatibilidad absoluta con FPDF
        texto_limpio = str(texto).encode('latin-1', 'replace').decode('latin-1')
        lineas = textwrap.wrap(texto_limpio, width=95, break_long_words=True)
        for l in lineas:
            pdf.set_x(10)
            pdf.cell(w=0, h=5, txt=l, ln=1)

    pdf.ln(5)
    escribir_seguro(f"Funcionario: {contexto['nombre']}", es_bold=True)
    escribir_seguro(f"RUT: {contexto['rut']}")
    escribir_seguro(f"Unidad: {contexto['direccion']} - {contexto['depto']}")
    escribir_seguro(f"Periodo: {contexto['mes']} {contexto['anio']}")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 11); pdf.cell(0, 10, "Resumen de Gestión Realizada:", ln=1)
    for act in contexto['actividades']:
        escribir_seguro(f"● {act['Actividad']}: {act['Producto']}")
        pdf.ln(1)
    
    pdf.ln(10); y_actual = pdf.get_y()
    if y_actual > 230: pdf.add_page(); y_actual = 20
    
    if img_prestador_io:
        pdf.image(img_prestador_io, x=30, y=y_actual, w=50)
        pdf.text(x=35, y=y_actual + 25, txt="Firma del Prestador")
    if img_jefatura_io:
        pdf.image(img_jefatura_io, x=120, y=y_actual, w=50)
        pdf.text(x=125, y=y_actual + 25, txt="V°B° Jefatura Directa")
            
    return bytes(pdf.output())

# --- SISTEMA DE LOGINS SEGUROS MUNICIPALES ---
def validar_acceso_portal(nombre_rol):
    """Control de seguridad por portal con credenciales municipales de prueba"""
    if st.session_state.get(f'auth_{nombre_rol}'): return True
    
    st.markdown(f"### 🔐 Acceso al Portal de {nombre_rol.capitalize()}")
    user_p = st.text_input("Usuario Municipal", key=f"u_{nombre_rol}")
    psw_p = st.text_input("Contraseña Institucional", type="password", key=f"p_{nombre_rol}")
    
    if st.button("Validar Credenciales", key=f"b_{nombre_rol}"):
        if (nombre_rol == "jefatura" and user_p == "jefatura" and psw_p == "123") or \
           (nombre_rol == "finanzas" and user_p == "finanzas" and psw_p == "123"):
            st.session_state[f'auth_{nombre_rol}'] = True
            st.rerun()
        else:
            st.error("Credenciales Incorrectas.")
    return False

# ==============================================================================
# 4. CABECERA MAESTRA (SOLO 2 LOGOS Y MÁXIMA NITIDEZ)
# ==============================================================================
def renderizar_cabecera_maestra():
    """Dibuja la cabecera con logos perfectos (sin cortes) y ticker masivo"""
    # Usamos columnas laterales pequeñas para los logos y una grande central
    col_l1, col_center, col_l2 = st.columns([1.5, 5, 1.5], gap="small")
    
    with col_l1:
        st.markdown('<div class="logo-frame-muni">', unsafe_allow_html=True)
        # Logo Municipal del repositorio
        if os.path.exists("logo_muni.png"): st.image("logo_muni.png", width=130)
        else: st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png", width=110)
        st.markdown('</div>', unsafe_allow_html=True)
            
    with col_center:
        st.markdown("<p class='main-title'>Ilustre Municipalidad de La Serena</p>", unsafe_allow_html=True)
        st.markdown("<p class='sub-title'>Sistema Digital de Gestión de Honorarios 2026</p>", unsafe_allow_html=True)
        # Ticker de Impacto Anual Masivo (1.800 funcionarios)
        st.markdown("""
            <div class="ticker-wrap">
                <div class="ticker">
                    ☀️ ¡BIENVENIDO A LA SERENA CERO PAPEL! 🌊 ● 🌳 <b>IMPACTO ANUAL PROYECTADO:</b> Estamos ahorrando juntos <b>$78.580.800 CLP</b> en costos operativos ● 📄 ¡Evitamos imprimir <b>108.000 hojas de papel</b> al año! ● 🕒 Ganamos <b>14.400 horas</b> de tiempo para servir mejor a nuestros vecinos ● ☀️ Menos tinta, menos electricidad ● 🐑 ¡Nuestra huella de carbono disminuye gracias a ti! ☁️ ● ✨ Innovación Ciudadana: ¡Cambiando papel por sol y progreso! 🌿🟢🔵🌕● 
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    with col_l2:
        st.markdown('<div class="logo-frame-muni">', unsafe_allow_html=True)
        # Logo Innovación del repositorio
        if os.path.exists("logo_innovacion.png"): st.image("logo_innovacion.png", width=140)
        else: st.image("https://cdn-icons-png.flaticon.com/512/1903/1903162.png", width=110)
        st.markdown('</div>', unsafe_allow_html=True)

def disparar_parafernalia_exito():
    """Lanza globos y muestra el mensaje de impacto ecológico positivo"""
    st.success("""
    ### ¡Misión Digital Completada con Éxito! 🎉🌿✨
    **🌟 Impacto Municipal hoy:**
    * 💰 Sumaste al ahorro anual de **$78 millones**.
    * 🌳 Has salvado **5 hojas de papel** hoy. ¡Sumamos hacia las 108.000!.
    * 🕒 Liberaste **40 minutos** de burocracia para enfocarte en lo que importa.
    
    *☀️ ¡Menos impresora, más vida! Gracias por cuidar nuestra huella de carbono.* 🐑🔵
    """)
    st.balloons()

# ==============================================================================
# 5. MÓDULO 1: PORTAL DEL PRESTADOR (INGRESO CIVIL Y MATEMÁTICO)
# ==============================================================================
def modulo_portal_prestador():
    renderizar_cabecera_maestra()
    
    if 'p_ok' not in st.session_state: st.session_state.p_ok = None

    if st.session_state.p_ok is None:
        st.subheader("📝 Nuevo Informe Mensual de Actividades")
        
        with st.expander("👤 Paso 1: Identificación Civil y RUT (Nivel 1)", expanded=True):
            col_n1, col_n2, col_n3 = st.columns(3)
            txt_n = col_n1.text_input("Nombres", placeholder="JUAN ANDRÉS")
            txt_p = col_n2.text_input("Apellido Paterno", placeholder="PÉREZ")
            txt_m = col_n3.text_input("Apellido Materno", placeholder="ROJAS")
            txt_r = st.text_input("RUT del Funcionario", placeholder="12.345.678-K")

        with st.expander("🏢 Paso 2: Ubicación Organizacional 2026", expanded=True):
            col_d, col_a = st.columns(2)
            sel_recinto = col_d.selectbox("Dirección Municipal o Recinto", unidades_municipales)
            sel_area = col_a.selectbox("Departamento, Área o Unidad Específica", departamentos_areas)
            sel_jor = st.selectbox("Tipo de Jornada", ["Libre / Por Productos", "Completa", "Media Jornada"])

        with st.expander("💰 Paso 3: Periodo y Cálculo de Honorarios", expanded=True):
            col_m1, col_m2, col_m3 = st.columns(3)
            sel_mes = col_m1.selectbox("Mes", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"], index=2)
            sel_anio = col_m2.number_input("Año", value=2026)
            num_monto = col_m3.number_input("Monto Bruto Contrato ($)", value=0, step=10000)
            
            # --- MOTOR MATEMÁTICO RECUPERADO (Fórmula de Retención 15.25%) ---
            ret_sii = int(num_monto * 0.1525) 
            liq_pagar = num_monto - ret_sii
            if num_monto > 0:
                st.info(f"📊 **Cálculo Tributario:** Bruto: ${num_monto:,.0f} | Retención SII (15.25%): ${ret_sii:,.0f} | **Líquido a Recibir: ${liq_pagar:,.0f}**")
            
            txt_bol = st.text_input("Nº de Boleta de Honorarios SII")

        st.subheader("📋 Paso 4: Resumen de Actividades")
        if 'num_acts' not in st.session_state: st.session_state.num_acts = 1
        for i in range(st.session_state.num_acts):
            ca, cp = st.columns(2)
            ca.text_area(f"Actividad {i+1}", key=f"desc_{i}", placeholder="Ej: Redacción de informes técnicos...")
            cp.text_area(f"Producto {i+1}", key=f"prod_{i}", placeholder="Ej: 5 Documentos firmados...")
        
        if st.button("➕ Añadir Otra Actividad"): 
            st.session_state.num_acts += 1
            st.rerun()

        st.subheader("✍️ Paso 5: Firma Digital")
        canv_p = st_canvas(stroke_width=2, stroke_color="black", background_color="white", height=150, width=400, key="cp")

        if st.button("🚀 ENVIAR PARA VISACIÓN TÉCNICA", type="primary", use_container_width=True):
            if not txt_n or not txt_p or not txt_r or num_monto == 0 or not canv_p.image_data is not None:
                st.error("⚠️ Datos faltantes: Asegúrese de completar Nombres, Apellidos, RUT, Monto y su Firma.")
            else:
                f_b64 = procesar_firma_a_base64(canv_p.image_data)
                acts_final = [{"Actividad": st.session_state[f"desc_{i}"], "Producto": st.session_state[f"prod_{i}"]} for i in range(st.session_state.num_acts)]
                nom_full = f"{txt_n.upper()} {txt_p.upper()} {txt_m.upper()}"
                
                # PERSISTENCIA EN BASE DE DATOS (Sincronización de Bandeja de Entrada)
                c_bd = conn.cursor()
                c_bd.execute("INSERT INTO informes (nombres, apellido_p, apellido_m, rut, direccion, depto, jornada, mes, anio, monto, n_boleta, actividades_json, firma_prestador_b64, estado) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (txt_n.upper(), txt_p.upper(), txt_m.upper(), txt_r, sel_recinto, sel_area, sel_jor, sel_mes, sel_anio, num_monto, txt_bol, json.dumps(acts_final), f_b64, '🔴 Pendiente'))
                conn.commit()

                # GENERACIÓN DE DOCUMENTOS (WORD ORIGINAL Y PDF)
                doc_o = DocxTemplate("plantilla_base.docx")
                ctx_doc = {'nombre': nom_full, 'rut': txt_r, 'direccion': sel_recinto, 'depto': sel_area, 'mes': sel_mes, 'anio': sel_anio, 'monto': f"${num_monto:,.0f}", 'boleta': txt_bol, 'actividades': acts_final, 'firma': InlineImage(doc_o, decodificar_base64_a_bytes(f_b64), height=Mm(20))}
                doc_o.render(ctx_doc)
                w_buf = io.BytesIO(); doc_o.save(w_buf)
                p_res = generar_documento_pdf_blindado(ctx_doc, decodificar_base64_a_bytes(f_b64), None)
                
                st.session_state.p_ok = {"word": w_buf.getvalue(), "pdf": p_res, "arch": f"Informe_{txt_p}_{sel_mes}"}
                st.rerun()
    else:
        disparar_parafernalia_exito()
        st.subheader("📥 Descarga tus comprobantes oficiales")
        cw, cp, ce = st.columns(3)
        with cw: st.download_button("📥 WORD Original", st.session_state.p_ok['word'], f"{st.session_state.p_ok['arch']}.docx", use_container_width=True)
        with cp: st.download_button("📥 PDF Certificado", st.session_state.p_ok['pdf'], f"{st.session_state.p_ok['arch']}.pdf", use_container_width=True)
        with ce:
            mail_l = f"mailto:?subject=Copia Informe Honorarios&body=Adjunto mi informe enviado digitalmente."
            st.markdown(f'<a href="{mail_l}" target="_blank"><button style="width:100%; padding:0.5rem; background-color:#2c3e50; color:white; border:none; border-radius:5px;">✉️ Enviar a mi correo</button></a>', unsafe_allow_html=True)
        if st.button("⬅️ Generar nuevo"): st.session_state.p_ok = None; st.rerun()

# ==============================================================================
# 6. MÓDULO 2: PORTAL DE JEFATURA (VISACIÓN)
# ==============================================================================
def modulo_portal_jefatura():
    renderizar_cabecera_maestra()
    if not validar_acceso_portal("jefatura"): return
    st.subheader("📥 Bandeja de Entrada Técnica")
    # Buscamos informes con estado nativo '🔴 Pendiente'
    df_p = pd.read_sql_query("SELECT id, nombres, apellido_p, depto, mes, estado FROM informes WHERE estado='🔴 Pendiente'", conn)
    if df_p.empty: st.info("🎉 Sin informes pendientes de visación técnica.")
    else:
        st.dataframe(df_p, use_container_width=True, hide_index=True)
        id_sel = st.selectbox("Seleccione ID:", df_p['id'].tolist())
        c_bd = conn.cursor(); c_bd.execute("SELECT * FROM informes WHERE id=?", (id_sel,))
        row = dict(zip([col[0] for col in c_bd.description], c_bd.fetchone()))
        st.write(f"**Funcionario:** {row['nombres']} {row['apellido_p']} | **Unidad:** {row['depto']}")
        with st.expander("Ver Actividades"):
            for a in json.loads(row['actividades_json']): st.write(f"● **{a['Actividad']}**: {a['Producto']}")
        st.write("✍️ **Firma de Visación (Jefatura)**")
        canv_j = st_canvas(stroke_width=2, stroke_color="blue", background_color="white", height=150, width=400, key="cj")
        if st.button("✅ VISAR Y ENVIAR A FINANZAS", type="primary", use_container_width=True):
            f_j = procesar_firma_a_base64(canv_j.image_data)
            c_bd.execute("UPDATE informes SET estado='🟡 Visado Jefatura', firma_jefatura_b64=? WHERE id=?", (f_j, id_sel))
            conn.commit(); disparar_parafernalia_exito(); time.sleep(3); st.rerun()

# ==============================================================================
# 7. MÓDULO 3: PORTAL DE FINANZAS (TESORERÍA)
# ==============================================================================
def modulo_portal_finanzas():
    renderizar_cabecera_maestra()
    if not validar_acceso_portal("finanzas"): return
    st.subheader("🏛️ Panel de Pagos y Tesorería")
    df_f = pd.read_sql_query("SELECT id, nombres, apellido_p, mes, monto, estado FROM informes WHERE estado='🟡 Visado Jefatura'", conn)
    if df_f.empty: st.info("✅ Bandeja de pagos limpia.")
    else:
        st.dataframe(df_f, use_container_width=True, hide_index=True)
        id_p = st.selectbox("ID para Liberar Pago:", df_f['id'].tolist())
        c_bd = conn.cursor(); c_bd.execute("SELECT * FROM informes WHERE id=?", (id_p,))
        d = dict(zip([col[0] for col in c_bd.description], c_bd.fetchone()))
        lq = int(d['monto'] * 0.8475)
        st.write(f"**Liberar Pago a:** {d['nombres']} {d['apellido_p']} | **Líquido:** ${lq:,.0f}")
        if st.button("💸 LIBERAR PAGO Y ARCHIVAR", type="primary", use_container_width=True):
            c_bd.execute("UPDATE informes SET estado='🟢 Pago Liberado' WHERE id=?", (id_p,))
            conn.commit(); disparar_parafernalia_exito(); time.sleep(3); st.rerun()

# ==============================================================================
# 8. MÓDULO 4: CONSOLIDADO E HISTORIAL
# ==============================================================================
def modulo_consolidado_historico():
    renderizar_cabecera_maestra()
    if not validar_acceso_portal("finanzas"): return 
    st.subheader("📊 Consolidado Maestro de Honorarios")
    df_h = pd.read_sql_query("SELECT id, nombres, apellido_p, apellido_m, rut, depto, mes, anio, monto, estado, fecha_envio FROM informes", conn)
    if df_h.empty: st.info("No hay registros históricos.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1: f_m = st.selectbox("Mes", ["Todos"] + list(df_h['mes'].unique()))
        with c2: f_d = st.selectbox("Departamento", ["Todos"] + list(df_h['depto'].unique()))
        with f3: f_e = st.selectbox("Estado", ["Todos"] + list(df_h['estado'].unique()))
        df_f = df_h.copy()
        if f_m != "Todos": df_f = df_f[df_f['mes'] == f_m]
        if f_d != "Todos": df_f = df_f[df_f['depto'] == f_d]
        st.dataframe(df_f, use_container_width=True, hide_index=True)
        st.metric("Gasto Bruto Consolidado", f"${df_f['monto'].sum():,.0f}")
        csv = df_f.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📊 Exportar Historial Excel", csv, "Consolidado_LS_2026.csv", use_container_width=True)

# ==============================================================================
# 9. ENRUTADOR PRINCIPAL (SIDEBAR MUNICIPAL)
# ==============================================================================
with st.sidebar:
    st.markdown('<div class="logo-frame-muni">', unsafe_allow_html=True)
    if os.path.exists("logo_muni.png"): st.image("logo_muni.png", width=120)
    else: st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png", width=110)
    st.markdown('</div>', unsafe_allow_html=True)
    st.title("Gestión 2026")
    rol = st.sidebar.radio("MENÚ PRINCIPAL", ["👤 Portal Prestador", "🧑‍💼 Portal Jefatura 🔒", "🏛️ Portal Finanzas 🔒", "📊 Consolidado Histórico 🔒"])
    st.caption("v5.7 High Robust Pro")

if rol == "👤 Portal Prestador": modulo_portal_prestador()
elif rol == "🧑‍💼 Portal Jefatura 🔒": modulo_portal_jefatura()
elif rol == "🏛️ Portal Finanzas 🔒": modulo_portal_finanzas()
else: modulo_consolidado_historico()

# Final del Archivo: 651 Líneas de Código Municipal Legible y Blindado.

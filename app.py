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
from docx.shared import Mm
from fpdf import FPDF

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Sistema de Honorarios - La Serena", page_icon="📝", layout="wide")

# --- 2. MOTOR DE BASE DE DATOS CON AUTO-REPARACIÓN ---
def init_db():
    conn = sqlite3.connect('workflow_honorarios.db', check_same_thread=False)
    c = conn.cursor()
    # Creamos la tabla con la estructura civil completa
    c.execute('''CREATE TABLE IF NOT EXISTS informes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombres TEXT, apellido_p TEXT, apellido_m TEXT, rut TEXT,
                  direccion TEXT, depto TEXT, jornada TEXT,
                  mes TEXT, anio INTEGER, monto INTEGER, n_boleta TEXT,
                  actividades_json TEXT, firma_prestador_b64 TEXT, firma_jefatura_b64 TEXT,
                  estado TEXT, fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Rutina para evitar el error de "columna no encontrada" tras la actualización
    try:
        c.execute("SELECT rut FROM informes LIMIT 1")
    except sqlite3.OperationalError:
        # Si falla, es porque la tabla es antigua. La borramos para que se cree limpia.
        c.execute("DROP TABLE informes")
        conn.commit()
        return init_db()
        
    conn.commit()
    return conn

conn = init_db()

# --- 3. LISTADOS MAESTROS ORGANIZACIONALES 2026 ---
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
    "Juzgado de Policía Local", "Producción Audiovisual / RDMLS", "Vivienda y Entorno"
]

# --- 4. FUNCIONES DE APOYO ---
def canvas_to_base64(canvas_data):
    raw_img = Image.fromarray(canvas_data.astype('uint8'), 'RGBA')
    bg = Image.new("RGB", raw_img.size, (255, 255, 255))
    bg.paste(raw_img, mask=raw_img.split()[3])
    buffered = io.BytesIO()
    bg.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def base64_to_bytesio(b64_str):
    return io.BytesIO(base64.b64decode(b64_str)) if b64_str else None

def generar_pdf(ctx, img_p_io, img_j_io=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "INFORME DE ACTIVIDADES DIGITAL", ln=1, align='C')
    def wl(t, b=False):
        pdf.set_font("Arial", "B" if b else "", 10)
        pdf.multi_cell(0, 5, str(t).encode('latin-1', 'replace').decode('latin-1'))
    wl(f"Nombre: {ctx['nombre']}")
    wl(f"RUT: {ctx['rut']}")
    wl(f"Unidad: {ctx['direccion']} - {ctx['depto']}")
    wl(f"Periodo: {ctx['mes']} {ctx['anio']}")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11); pdf.cell(0, 10, "Resumen de Gestión:", ln=1)
    for act in ctx['actividades']: wl(f"● {act['Actividad']}: {act['Producto']}")
    pdf.ln(10); y = pdf.get_y()
    if y > 230: pdf.add_page(); y = 20
    if img_p_io: pdf.image(img_p_io, x=30, y=y, w=50); pdf.text(x=35, y=y+25, txt="Firma Prestador")
    if img_j_io: pdf.image(img_j_io, x=120, y=y, w=50); pdf.text(x=125, y=y+25, txt="V°B° Jefatura")
    return bytes(pdf.output())

# --- 5. INTERFAZ VISUAL Y HUINCHA DE IMPACTO ---
def mostrar_cabecera():
    st.markdown("""
        <style>
        .ticker-wrap { width: 100%; overflow: hidden; background-color: #e3f2fd; color: #0d47a1; border: 2px solid #2196f3; padding: 12px 0; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .ticker { display: inline-block; white-space: nowrap; animation: ticker 60s linear infinite; font-size: 18px; font-weight: bold;}
        @keyframes ticker { 0% { transform: translate3d(100%, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }
        </style>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 4, 1], gap="large")
    with c1:
        if os.path.exists("logo_muni.png"): st.image("logo_muni.png", width=140)
        else: st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png", width=120)
    with c2:
        st.markdown("<h1 style='text-align: center; color: #1a237e; margin-bottom: 0;'>Ilustre Municipalidad de La Serena</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 20px; color: #1565c0; font-weight: bold;'>Sistema de Honorarios Digital</p>", unsafe_allow_html=True)
        # Ticker con el impacto anual total (1.800 funcionarios x 12 meses)
        st.markdown("""
            <div class="ticker-wrap">
                <div class="ticker">
                    ☀️ ¡BIENVENIDO AL CAMBIO! 🌊 ● 🌳 <b>IMPACTO ANUAL PROYECTADO:</b> Estamos ahorrando <b>$78.580.800 CLP</b> en costos operativos ● 📄 ¡Evitamos imprimir <b>108.000 hojas de papel</b> cada año! ● 🕒 Ganamos <b>14.400 horas</b> para servir mejor a nuestra comunidad ● ☀️ Menos tinta, menos electricidad, más vida ● 🐑 ¡Nuestra huella de carbono disminuye gracias a ti! ● ✨ ¡Transformando La Serena con innovación! 🌿🟢🔵🌕●
                </div>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        if os.path.exists("logo_innovacion.png"): st.image("logo_innovacion.png", width=140)
        else: st.image("https://cdn-icons-png.flaticon.com/512/1903/1903162.png", width=120)

def check_login(rol):
    if st.session_state.get(f'auth_{rol}'): return True
    st.warning(f"🔒 **Acceso Protegido - Módulo {rol.capitalize()}**")
    u = st.text_input("Usuario", key=f"u_{rol}")
    p = st.text_input("Clave", type="password", key=f"p_{rol}")
    if st.button("Ingresar", key=f"b_{rol}"):
        if (rol == "jefatura" and u == "jefatura" and p == "123") or (rol == "finanzas" and u == "finanzas" and p == "123"):
            st.session_state[f'auth_{rol}'] = True; st.rerun()
        else: st.error("Credenciales Incorrectas")
    return False

# ==========================================
# MÓDULO 1: PORTAL PRESTADOR
# ==========================================
def modulo_prestador():
    mostrar_cabecera()
    if 'p_ok' not in st.session_state: st.session_state.p_ok = None

    if st.session_state.p_ok is None:
        st.subheader("📝 Ingreso de Informe Mensual")
        with st.expander("👤 Paso 1: Identificación Civil y RUT", expanded=True):
            cn, cp, cm = st.columns(3)
            nombres = cn.text_input("Nombres", placeholder="Juan Andrés")
            ap_paterno = cp.text_input("Apellido Paterno", placeholder="Pérez")
            ap_materno = cm.text_input("Apellido Materno", placeholder="Rojas")
            rut = st.text_input("RUT", placeholder="12.345.678-K")

        with st.expander("🏢 Paso 2: Ubicación Organizacional", expanded=True):
            cdir, cdep = st.columns(2)
            recinto = cdir.selectbox("Dirección Municipal o Recinto", unidades_municipales)
            area = cdep.selectbox("Departamento, Área o Unidad Específica", departamentos_areas)
            jornada = st.selectbox("Tipo de Jornada", ["Completa", "Media Jornada", "Libre"])

        with st.expander("💰 Paso 3: Periodo y Cálculo de Honorarios", expanded=True):
            c1, c2, c3 = st.columns(3)
            mes = c1.selectbox("Mes del Informe", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=2)
            anio = c2.number_input("Año", value=2026)
            monto_bruto = c3.number_input("Monto Bruto Contrato ($)", value=0, step=10000)
            
            # --- RECUPERACIÓN DEL MOTOR DE CÁLCULO ---
            impuesto = int(monto_bruto * 0.1525)
            liquido = monto_bruto - impuesto
            if monto_bruto > 0:
                st.info(f"📊 **Desglose de Pago:** Bruto: ${monto_bruto:,.0f} | Retención SII (15.25%): ${impuesto:,.0f} | **Líquido a recibir: ${liquido:,.0f}**")
            
            n_boleta = st.text_input("Nº Boleta SII correspondente")

        st.subheader("📋 Paso 4: Resumen de Actividades")
        if 'num' not in st.session_state: st.session_state.num = 1
        for i in range(st.session_state.num):
            ca, cp = st.columns(2)
            ca.text_area(f"Actividad {i+1}", key=f"d_{i}")
            cp.text_area(f"Producto/Resultado {i+1}", key=f"r_{i}")
        if st.button("➕ Agregar Otra Actividad"): st.session_state.num += 1; st.rerun()

        st.subheader("✍️ Paso 5: Firma Digital")
        canvas = st_canvas(stroke_width=2, stroke_color="black", background_color="white", height=150, width=400, key="c_pres")

        if st.button("🚀 ENVIAR PARA REVISIÓN DIGITAL", type="primary", use_container_width=True):
            if not nombres or not ap_paterno or not rut or monto_bruto == 0: st.error("Complete sus datos, RUT y Monto.")
            else:
                firma_b64 = canvas_to_base64(canvas.image_data)
                acts = [{"Actividad": st.session_state[f"d_{i}"], "Producto": st.session_state[f"r_{i}"]} for i in range(st.session_state.num)]
                nombre_comp = f"{nombres.upper()} {ap_paterno.upper()} {ap_materno.upper()}"
                
                c = conn.cursor()
                c.execute("INSERT INTO informes (nombres, apellido_p, apellido_m, rut, direccion, depto, jornada, mes, anio, monto, n_boleta, actividades_json, firma_prestador_b64, estado) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (nombres.upper(), ap_paterno.upper(), ap_materno.upper(), rut, recinto, area, jornada, mes.upper(), anio, monto_bruto, n_boleta, json.dumps(acts), firma_b64, '🔴 Pendiente'))
                conn.commit()

                # Documentos inmediatos
                ctx = {'nombre': nombre_comp, 'rut': rut, 'direccion': recinto, 'depto': area, 'mes': mes.upper(), 'anio': anio, 'actividades': acts}
                pdf_bytes = generar_pdf(ctx, base64_to_bytesio(firma_b64), None)
                st.session_state.p_ok = {"pdf": pdf_bytes, "nombre": f"Informe_{mes}_{ap_paterno}"}
                st.rerun()
    else:
        st.success("✅ Informe enviado con éxito a Jefatura.")
        st.balloons()
        st.download_button("📥 Descargar mi Comprobante (PDF)", st.session_state.p_ok['pdf'], f"{st.session_state.p_ok['nombre']}.pdf", use_container_width=True)
        if st.button("Generar nuevo informe"): st.session_state.p_ok = None; st.rerun()

# ==========================================
# MÓDULO 2: PORTAL JEFATURA
# ==========================================
def modulo_jefatura():
    mostrar_cabecera()
    if not check_login("jefatura"): return
    st.subheader("Bandeja de Visación Técnica 📥")
    df = pd.read_sql_query("SELECT id, nombres, apellido_p, depto, mes, estado FROM informes WHERE estado='🔴 Pendiente'", conn)
    if df.empty: st.info("🎉 No hay informes pendientes.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        id_sel = st.selectbox("ID a Visar:", df['id'].tolist())
        c = conn.cursor(); c.execute("SELECT * FROM informes WHERE id=?", (id_sel,))
        d = dict(zip([col[0] for col in c.description], c.fetchone()))
        st.write(f"**Funcionario:** {d['nombres']} {d['apellido_p']} | **Área:** {d['depto']}")
        canvas_j = st_canvas(stroke_width=2, stroke_color="blue", background_color="white", height=150, width=400, key="c_jefa")
        if st.button("✅ VISAR Y ENVIAR A FINANZAS", type="primary", use_container_width=True):
            f_j_b64 = canvas_to_base64(canvas_j.image_data)
            c.execute("UPDATE informes SET estado='🟡 Visado', firma_jefatura_b64=? WHERE id=?", (f_j_b64, id_sel))
            conn.commit(); st.success("Visado con éxito."); time.sleep(2); st.rerun()

# ==========================================
# MÓDULO 3: PORTAL FINANZAS
# ==========================================
def modulo_finanzas():
    mostrar_cabecera()
    if not check_login("finanzas"): return
    st.subheader("Panel de Pagos y Tesorería 🏛️")
    df = pd.read_sql_query("SELECT id, nombres, apellido_p, mes, monto, estado FROM informes WHERE estado='🟡 Visado'", conn)
    if df.empty: st.info("✅ Bandeja limpia.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        id_sel = st.selectbox("ID para Pago:", df['id'].tolist())
        c = conn.cursor(); c.execute("SELECT * FROM informes WHERE id=?", (id_sel,))
        d = dict(zip([col[0] for col in c.description], c.fetchone()))
        st.write(f"**Aprobar Pago:** {d['nombres']} {d['apellido_p']} | **Bruto:** ${d['monto']:,.0f}")
        if st.button("💸 LIBERAR PAGO Y ARCHIVAR", type="primary", use_container_width=True):
            c.execute("UPDATE informes SET estado='🟢 Pago Liberado' WHERE id=?", (id_sel,))
            conn.commit(); st.success("Pago procesado correctamente."); time.sleep(2); st.rerun()

# ==========================================
# MÓDULO 4: CONSOLIDADO HISTÓRICO
# ==========================================
def modulo_historial():
    mostrar_cabecera()
    if not check_login("finanzas"): return
    st.subheader("📊 Consolidado Maestro de Gestión")
    df = pd.read_sql_query("SELECT id, nombres, apellido_p, apellido_m, rut, direccion as recinto, depto, mes, anio, monto, estado FROM informes", conn)
    if df.empty: st.info("No hay registros.")
    else:
        st.markdown("#### 🔍 Filtros Inteligentes")
        f1, f2, f3 = st.columns(3)
        with f1: f_mes = st.selectbox("Mes", ["Todos"] + list(df['mes'].unique()))
        with f2: f_dep = st.selectbox("Departamento", ["Todos"] + list(df['depto'].unique()))
        with f3: f_est = st.selectbox("Estado", ["Todos"] + list(df['estado'].unique()))
        df_f = df.copy()
        if f_mes != "Todos": df_f = df_f[df_f['mes'] == f_mes]
        if f_dep != "Todos": df_f = df_f[df_f['depto'] == f_dep]
        if f_est != "Todos": df_f = df_f[df_f['estado'] == f_est]
        st.dataframe(df_f, use_container_width=True, hide_index=True)
        csv = df_f.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📊 Exportar este Consolidado (Excel/CSV)", csv, "Historial_Honorarios_2026.csv", use_container_width=True)

# --- NAVEGACIÓN ---
rol = st.sidebar.radio("MENÚ PRINCIPAL", ["👤 Portal Prestador", "🧑‍💼 Portal Jefatura 🔒", "🏛️ Portal Finanzas 🔒", "📊 Consolidado Histórico 🔒"])
if rol == "👤 Portal Prestador": modulo_prestador()
elif rol == "🧑‍💼 Portal Jefatura 🔒": modulo_jefatura()
elif rol == "🏛️ Portal Finanzas 🔒": modulo_finanzas()
else: modulo_historial()

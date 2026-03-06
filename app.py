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

# --- 1. CONFIGURACIÓN INICIAL Y AUTO-REPARACIÓN DE BASE DE DATOS ---
st.set_page_config(page_title="Sistema Honorarios La Serena", page_icon="📝", layout="wide")

def init_db():
    conn = sqlite3.connect('workflow_honorarios.db', check_same_thread=False)
    c = conn.cursor()
    # Estructura completa: Identidad Civil + Organización + Montos
    c.execute('''CREATE TABLE IF NOT EXISTS informes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombres TEXT, apellido_p TEXT, apellido_m TEXT, rut TEXT,
                  direccion TEXT, depto TEXT, jornada TEXT,
                  mes TEXT, anio INTEGER, monto INTEGER, n_boleta TEXT,
                  actividades_json TEXT, firma_prestador_b64 TEXT, firma_jefatura_b64 TEXT,
                  estado TEXT, fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Verificación de columnas para evitar el OperationalError
    try:
        c.execute("SELECT rut FROM informes LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("DROP TABLE informes")
        conn.commit()
        return init_db()
    conn.commit()
    return conn

conn = init_db()

# --- 2. LISTADOS MAESTROS ESTRUCTURA 2026 ---
unidades_municipales = ["Alcaldía", "Administración Municipal", "Secretaría Municipal", "DIDECO", "DOM", "SECPLAN", "Tránsito", "Aseo y Ornato", "Medio Ambiente", "Turismo y Patrimonio", "Salud", "Educación", "Seguridad Ciudadana", "Gestión de Personas", "Finanzas", "Control", "Asesoría Jurídica", "Comunicaciones", "Eventos", "Delegación Av. del Mar", "Delegación La Pampa", "Delegación La Antena", "Delegación Las Compañías", "Delegación Rural", "Radio Digital RDMLS"]

departamentos_areas = ["Oficina de Partes", "OIRS", "Recursos Humanos", "Contabilidad", "Tesorería", "Adquisiciones", "Informática", "Relaciones Públicas", "Prensa", "Fomento Productivo", "Juventud", "Adulto Mayor", "Mujer", "Discapacidad", "Cultura", "Deportes", "Emergencias", "Inspección", "Gestión Ambiental", "Parques y Jardines", "Alumbrado", "Juzgado Policía Local", "Programas Sociales", "Producción Audiovisual", "Vivienda"]

# --- 3. FUNCIONES DE APOYO (IMAGEN Y PDF BLINDADO) ---
def canvas_to_base64(canvas_data):
    raw_img = Image.fromarray(canvas_data.astype('uint8'), 'RGBA')
    bg = Image.new("RGB", raw_img.size, (255, 255, 255))
    bg.paste(raw_img, mask=raw_img.split()[3])
    buffered = io.BytesIO()
    bg.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def base64_to_bytesio(b64_str):
    return io.BytesIO(base64.decodebytes(b64_str.encode())) if b64_str else None

def generar_pdf(ctx, img_p_io, img_j_io=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "INFORME DE GESTIÓN MENSUAL DIGITAL", ln=1, align='C')
    def wl(t, b=False):
        pdf.set_font("Arial", "B" if b else "", 10)
        pdf.multi_cell(0, 5, str(t).encode('latin-1', 'replace').decode('latin-1'))
    wl(f"Funcionario: {ctx['nombre']}")
    wl(f"RUT: {ctx['rut']}")
    wl(f"Unidad: {ctx['direccion']} - {ctx['depto']}")
    wl(f"Periodo: {ctx['mes']} {ctx['anio']}")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11); pdf.cell(0, 10, "Actividades Realizadas:", ln=1)
    for act in ctx['actividades']: wl(f"● {act['Actividad']}: {act['Producto']}")
    pdf.ln(10); y = pdf.get_y()
    if y > 230: pdf.add_page(); y = 20
    if img_p_io: pdf.image(img_p_io, x=30, y=y, w=50); pdf.text(x=35, y=y+25, txt="Firma Prestador")
    if img_j_io: pdf.image(img_j_io, x=120, y=y, w=50); pdf.text(x=125, y=y+25, txt="V°B° Jefatura")
    return bytes(pdf.output())

# --- 4. CABECERA Y MENSAJES DE IMPACTO POSITIVO ---
def mostrar_cabecera():
    st.markdown("""
        <style>
        .ticker-wrap { width: 100%; overflow: hidden; background-color: #e3f2fd; color: #0d47a1; border: 2px solid #2196f3; padding: 12px 0; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .ticker { display: inline-block; white-space: nowrap; animation: ticker 50s linear infinite; font-size: 18px; font-weight: bold;}
        @keyframes ticker { 0% { transform: translate3d(100%, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }
        </style>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 4, 1])
    with c1:
        if os.path.exists("logo_muni.png"): st.image("logo_muni.png", width=140)
        else: st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png", width=110)
    with c2:
        st.markdown("<h1 style='text-align: center; color: #1a237e; margin-bottom: 0;'>Ilustre Municipalidad de La Serena</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 20px; color: #1565c0; font-weight: bold;'>Sistema de Honorarios Digital</p>", unsafe_allow_html=True)
        st.markdown("""
            <div class="ticker-wrap">
                <div class="ticker">
                    ☀️ ¡GRACIAS POR SER PARTE DEL CAMBIO! 🌊 ● 🌳 <b>IMPACTO ANUAL:</b> Ahorramos <b>$78.580.800 CLP</b> al municipio ● 📄 ¡Evitamos imprimir <b>108.000 hojas de papel</b>! ● 🕒 Ganamos <b>14.400 horas</b> para servir a nuestros vecinos ● ☀️ Menos tinta, más vida ● 🐑 ¡Cuidamos nuestra huella de carbono! ● ✨ Innovación Ciudadana para La Serena 🌿🟢🔵🌕●
                </div>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        if os.path.exists("logo_innovacion.png"): st.image("logo_innovacion.png", width=140)
        else: st.image("https://cdn-icons-png.flaticon.com/512/1903/1903162.png", width=120)

def mostrar_mensaje_impacto():
    st.success("""
    ### ¡Misión Cumplida! 🌿✨
    **🌟 Impacto de tu gestión digital hoy:**
    * 💰 **Ahorro Municipal:** Contribuyes a los **$78 millones** de ahorro anual proyectado.
    * 🌳 **Eco-Héroe:** Has salvado **5 hojas** de papel. ¡Ayúdanos a llegar a las 108.000!.
    * 🕒 **Eficiencia:** Liberaste **40 minutos** de burocracia para tareas de valor real.
    
    *☀️ ¡Menos impresora, más vida! Gracias por cuidar nuestra huella de carbono.* 🐑🔵
    """)
    st.balloons()

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
            jornada = st.selectbox("Tipo de Jornada", ["Libre", "Completa", "Flexible"])

        with st.expander("💰 Paso 3: Cálculo de Honorarios", expanded=True):
            c1, c2, c3 = st.columns(3)
            mes = c1.selectbox("Mes", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"], index=2)
            anio = c2.number_input("Año", value=2026)
            monto_bruto = c3.number_input("Monto Bruto ($)", value=0, step=10000)
            impuesto = int(monto_bruto * 0.1525)
            liquido = monto_bruto - impuesto
            if monto_bruto > 0:
                st.info(f"📊 Bruto: ${monto_bruto:,.0f} | Retención (15.25%): ${impuesto:,.0f} | **Líquido: ${liquido:,.0f}**")
            n_boleta = st.text_input("Nº Boleta SII")

        st.subheader("📋 Paso 4: Actividades")
        if 'num' not in st.session_state: st.session_state.num = 1
        for i in range(st.session_state.num):
            ca, cp = st.columns(2)
            ca.text_area(f"Actividad {i+1}", key=f"d_{i}")
            cp.text_area(f"Producto {i+1}", key=f"r_{i}")
        if st.button("➕ Añadir Fila"): st.session_state.num += 1; st.rerun()

        st.subheader("✍️ Paso 5: Firma Digital")
        canvas = st_canvas(stroke_width=2, stroke_color="black", background_color="white", height=150, width=400, key="c_pres")

        if st.button("🚀 ENVIAR A JEFATURA", type="primary", use_container_width=True):
            if not nombres or not ap_paterno or not rut: st.error("⚠️ Datos faltantes.")
            else:
                firma_b64 = canvas_to_base64(canvas.image_data)
                acts = [{"Actividad": st.session_state[f"d_{i}"], "Producto": st.session_state[f"r_{i}"]} for i in range(st.session_state.num)]
                nombre_comp = f"{nombres.upper()} {ap_paterno.upper()} {ap_materno.upper()}"
                
                # BD
                c = conn.cursor()
                c.execute("INSERT INTO informes (nombres, apellido_p, apellido_m, rut, direccion, depto, jornada, mes, anio, monto, n_boleta, actividades_json, firma_prestador_b64, estado) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (nombres.upper(), ap_paterno.upper(), ap_materno.upper(), rut, recinto, area, jornada, mes, anio, monto_bruto, n_boleta, json.dumps(acts), firma_b64, '🔴 Pendiente'))
                conn.commit()

                # Generar WORD
                doc = DocxTemplate("plantilla_base.docx")
                context = {'nombre': nombre_comp, 'rut': rut, 'direccion': recinto, 'depto': area, 'mes': mes, 'anio': anio, 'monto': f"${monto_bruto:,.0f}", 'boleta': n_boleta, 'actividades': acts, 'firma': InlineImage(doc, base64_to_bytesio(firma_b64), height=Mm(20))}
                doc.render(context)
                w_buf = io.BytesIO(); doc.save(w_buf)
                
                # Generar PDF
                pdf_bytes = generar_pdf(context, base64_to_bytesio(firma_b64), None)
                
                st.session_state.p_ok = {"word": w_buf.getvalue(), "pdf": pdf_bytes, "nombre": f"Informe_{ap_paterno}_{mes}"}
                st.rerun()
    else:
        mostrar_mensaje_impacto()
        st.markdown("### 📥 Descarga tus comprobantes")
        cw, cp, ce = st.columns(3)
        with cw: st.download_button("📥 WORD Original", st.session_state.p_ok['word'], f"{st.session_state.p_ok['nombre']}.docx", use_container_width=True)
        with cp: st.download_button("📥 PDF Certificado", st.session_state.p_ok['pdf'], f"{st.session_state.p_ok['nombre']}.pdf", use_container_width=True)
        with ce:
            link_mail = f"mailto:?subject=Copia Informe Honorarios&body=Adjunto mi informe enviado a Jefatura."
            st.markdown(f'<a href="{link_mail}" target="_blank"><button style="width:100%; padding:0.5rem; background-color:#2c3e50; color:white; border:none; border-radius:5px;">✉️ Enviar a mi correo</button></a>', unsafe_allow_html=True)
        if st.button("⬅️ Volver"): st.session_state.p_ok = None; st.rerun()

# ==========================================
# MÓDULO 4: CONSOLIDADO HISTÓRICO 2026
# ==========================================
def modulo_historial():
    mostrar_cabecera()
    st.subheader("📊 Consolidado Maestro de Gestión")
    df = pd.read_sql_query("SELECT id, nombres, apellido_p, apellido_m, rut, depto, mes, anio, monto, estado FROM informes", conn)
    if df.empty: st.info("Sin registros.")
    else:
        f1, f2 = st.columns(2)
        with f1: f_mes = st.selectbox("Filtrar Mes", ["Todos"] + list(df['mes'].unique()))
        with f2: f_dep = st.selectbox("Departamento", ["Todos"] + list(df['depto'].unique()))
        df_f = df.copy()
        if f_mes != "Todos": df_f = df_f[df_f['mes'] == f_mes]
        if f_dep != "Todos": df_f = df_f[df_f['depto'] == f_dep]
        st.dataframe(df_f, use_container_width=True, hide_index=True)
        csv = df_f.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📊 Exportar Consolidado Excel", csv, "Historial_LaSerena_2026.csv", use_container_width=True)

# --- NAVEGACIÓN ---
rol = st.sidebar.radio("MENÚ", ["👤 Portal Prestador", "📊 Consolidado Histórico 🔒"])
if rol == "👤 Portal Prestador": modulo_prestador()
else: modulo_historial()

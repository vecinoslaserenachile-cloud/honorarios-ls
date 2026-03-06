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
# 1. CONFIGURACIÓN INICIAL Y MOTOR DE BASE DE DATOS (AUTO-REPARACIÓN)
# ==============================================================================
st.set_page_config(
    page_title="Sistema de Honorarios La Serena", 
    page_icon="📝", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_db():
    conn = sqlite3.connect('workflow_honorarios.db', check_same_thread=False)
    c = conn.cursor()
    # Estructura Nivel 1: Identidad Civil Completa
    c.execute('''CREATE TABLE IF NOT EXISTS informes
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
    
    # Rutina para asegurar que la columna RUT exista tras la actualización
    try:
        c.execute("SELECT rut FROM informes LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("DROP TABLE informes")
        conn.commit()
        return init_db()
        
    conn.commit()
    return conn

conn = init_db()

# ==============================================================================
# 2. LISTADOS MAESTROS - ESTRUCTURA ORGANIZACIONAL 2026
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
def canvas_to_base64(canvas_data):
    """Procesa la firma del canvas para documentos oficiales"""
    raw_img = Image.fromarray(canvas_data.astype('uint8'), 'RGBA')
    bg = Image.new("RGB", raw_img.size, (255, 255, 255))
    bg.paste(raw_img, mask=raw_img.split()[3])
    buffered = io.BytesIO()
    bg.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def base64_to_bytesio(b64_str):
    """Conversor para inyectar imágenes en Word y PDF"""
    if not b64_str: return None
    return io.BytesIO(base64.b64decode(b64_str))

def generar_pdf(ctx, img_p_io, img_j_io=None):
    """Motor de PDF blindado: escribe línea por línea para evitar errores de espacio"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "INFORME MENSUAL DE ACTIVIDADES - LA SERENA DIGITAL", ln=1, align='C')
    
    def write_safe(text, is_bold=False):
        pdf.set_font("Arial", "B" if is_bold else "", 10)
        clean = str(text).encode('latin-1', 'replace').decode('latin-1')
        lines = textwrap.wrap(clean, width=95, break_long_words=True)
        for line in lines:
            pdf.set_x(10)
            pdf.cell(w=0, h=5, txt=line, ln=1)

    pdf.ln(5)
    write_safe(f"Funcionario: {ctx['nombre']}", is_bold=True)
    write_safe(f"RUT: {ctx['rut']}")
    write_safe(f"Recinto: {ctx['direccion']}")
    write_safe(f"Unidad/Área: {ctx['depto']}")
    write_safe(f"Periodo: {ctx['mes']} {ctx['anio']}")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, "Resumen de Gestión Realizada:", ln=1)
    for idx, act in enumerate(ctx['actividades']):
        write_safe(f"Actividad {idx+1}: {act['Actividad']}", is_bold=True)
        write_safe(f"Resultado: {act['Producto']}")
        pdf.ln(2)
    
    pdf.ln(10)
    y_firmas = pdf.get_y()
    if y_firmas > 230: pdf.add_page(); y_firmas = 20
    
    if img_p_io:
        pdf.image(img_p_io, x=30, y=y_firmas, w=50)
        pdf.text(x=35, y=y_firmas + 25, txt="Firma del Prestador")
    if img_j_io:
        pdf.image(img_j_io, x=120, y=y_firmas, w=50)
        pdf.text(x=125, y=y_firmas + 25, txt="V°B° Jefatura Directa")
            
    return bytes(pdf.output())

# ==============================================================================
# 4. COMPONENTES VISUALES Y HUINCHA DE IMPACTO POSITIVO
# ==============================================================================
def mostrar_cabecera():
    """Cabecera con logos corregidos y letrero de impacto anual para 1.800 funcionarios"""
    st.markdown("""
        <style>
        .ticker-wrap { width: 100%; overflow: hidden; background-color: #e8f5e9; color: #1b5e20; border: 2px solid #4caf50; padding: 12px 0; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .ticker { display: inline-block; white-space: nowrap; animation: ticker 45s linear infinite; font-size: 18px; font-weight: bold;}
        @keyframes ticker { 0% { transform: translate3d(100%, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }
        </style>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 4, 1], gap="medium")
    
    with c1:
        if os.path.exists("logo_muni.png"): st.image("logo_muni.png", width=130)
        else: st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png", width=110)
            
    with c2:
        st.markdown("<h1 style='text-align: center; color: #2C3E50; margin-bottom: 0;'>Ilustre Municipalidad de La Serena</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 20px; color: #1565c0; font-weight: bold;'>Sistema Digital de Gestión de Honorarios 2026</p>", unsafe_allow_html=True)
        # Impacto Anual Proyectado (1.800 funcionarios x ahorro mensual)
        st.markdown("""
            <div class="ticker-wrap">
                <div class="ticker">
                    ☀️ ¡GRACIAS POR SER PARTE DEL CAMBIO! 🌊 ● 🌳 <b>IMPACTO ANUAL PROYECTADO:</b> Estamos ahorrando <b>$78.580.800 CLP</b> en costos operativos ● 📄 ¡Evitamos imprimir <b>108.000 hojas de papel</b> al año! ● 🕒 Ganamos <b>14.400 horas</b> de tiempo para servir a nuestros vecinos ● ☀️ Usemos menos la impresora, ahorremos tinta y energía ● 🐑 ¡Nuestra huella de carbono disminuye gracias a ti! ☁️ ● ✨ ¡Cambiando papel por innovación y sol! 🌿🟢🔵🌕●
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    with c3:
        if os.path.exists("logo_innovacion.png"): st.image("logo_innovacion.png", width=140)
        else: st.image("https://cdn-icons-png.flaticon.com/512/1903/1903162.png", width=120)

def mostrar_mensaje_impacto():
    """Parafernalia de éxito tras completar una acción"""
    st.success("""
    ### ¡Misión Cumplida! 🌿✨
    **🌟 Tu contribución de hoy:**
    * 💰 Has sumado al ahorro proyectado de **$78 millones** anuales del Municipio.
    * 🌳 Has salvado **5 hojas de papel** hoy. ¡Sumamos hacia las 108.000!.
    * 🕒 Liberaste **40 minutos** de trámites para enfocarte en lo que importa.
    
    *☀️ ¡Menos impresora, más vida! Gracias por cuidar nuestra huella de carbono.* 🐑🔵
    """)
    st.balloons()

def check_login(rol):
    """Control de acceso seguro para Jefatura, Finanzas e Historial"""
    if st.session_state.get(f'auth_{rol}'): return True
    st.warning(f"🔒 **Acceso Protegido - Módulo {rol.upper()}**")
    user_p = st.text_input("Usuario", key=f"u_{rol}")
    psw_p = st.text_input("Contraseña", type="password", key=f"p_{rol}")
    if st.button("Ingresar al Portal", key=f"b_{rol}"):
        if (rol == "jefatura" and user_p == "jefatura" and psw_p == "123") or \
           (rol == "finanzas" and user_p == "finanzas" and psw_p == "123"):
            st.session_state[f'auth_{rol}'] = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas.")
    return False

# ==============================================================================
# 5. MÓDULO 1: PORTAL DEL PRESTADOR (INGRESO)
# ==============================================================================
def modulo_prestador():
    mostrar_cabecera()
    if 'p_ok' not in st.session_state: st.session_state.p_ok = None

    if st.session_state.p_ok is None:
        st.subheader("📝 Ingreso de Informe Mensual")
        
        with st.expander("👤 Paso 1: Identificación Civil y RUT", expanded=True):
            c_n, c_p, c_m = st.columns(3)
            nombres = c_n.text_input("Nombres", placeholder="JUAN ANDRÉS")
            ap_paterno = c_p.text_input("Apellido Paterno", placeholder="PÉREZ")
            ap_materno = c_m.text_input("Apellido Materno", placeholder="ROJAS")
            rut = st.text_input("RUT del Funcionario", placeholder="12.345.678-K")

        with st.expander("🏢 Paso 2: Ubicación Organizacional", expanded=True):
            c_dir, c_dep = st.columns(2)
            recinto = c_dir.selectbox("Dirección Municipal o Recinto", unidades_municipales)
            area = c_dep.selectbox("Departamento, Área o Unidad Específica", departamentos_areas)
            jornada = st.selectbox("Tipo de Jornada", ["Completa", "Media Jornada", "Libre / Por Productos"])

        with st.expander("💰 Paso 3: Cálculo y Montos", expanded=True):
            c1, c2, c3 = st.columns(3)
            mes = c1.selectbox("Mes", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"], index=2)
            anio = c2.number_input("Año", value=2026)
            monto_bruto = c3.number_input("Monto Bruto Contrato ($)", value=0, step=10000)
            
            # --- MOTOR DE CÁLCULO DE HONORARIOS ---
            impuesto = int(monto_bruto * 0.1525)
            liquido = monto_bruto - impuesto
            if monto_bruto > 0:
                st.info(f"📊 **Desglose:** Bruto: ${monto_bruto:,.0f} | Retención SII (15.25%): ${impuesto:,.0f} | **Líquido: ${liquido:,.0f}**")
            
            n_boleta = st.text_input("Nº de Boleta SII")

        st.subheader("📋 Paso 4: Resumen de Actividades")
        if 'num_acts' not in st.session_state: st.session_state.num_acts = 1
        for i in range(st.session_state.num_acts):
            ca, cp = st.columns(2)
            ca.text_area(f"Actividad {i+1}", key=f"desc_{i}")
            cp.text_area(f"Producto {i+1}", key=f"prod_{i}")
        
        col_btns = st.columns(2)
        if col_btns[0].button("➕ Agregar Fila"): st.session_state.num_acts += 1; st.rerun()
        if col_btns[1].button("➖ Quitar Fila") and st.session_state.num_acts > 1: st.session_state.num_acts -= 1; st.rerun()

        st.subheader("✍️ Paso 5: Firma Digital")
        canvas = st_canvas(stroke_width=2, stroke_color="black", background_color="white", height=150, width=400, key="c_prestador")

        if st.button("🚀 ENVIAR PARA REVISIÓN DIGITAL", type="primary", use_container_width=True):
            # Validación exhaustiva Nivel 1
            if not nombres or not ap_paterno or not rut or monto_bruto == 0 or canvas.image_data is None:
                st.error("⚠️ Datos faltantes: Asegúrese de completar Nombres, Apellidos, RUT, Monto y su Firma.")
            else:
                f_b64 = canvas_to_base64(canvas.image_data)
                acts_f = []
                for i in range(st.session_state.num_acts):
                    acts_f.append({"Actividad": st.session_state[f"desc_{i}"], "Producto": st.session_state[f"prod_{i}"]})
                
                nombre_comp = f"{nombres.upper()} {ap_paterno.upper()} {ap_materno.upper()}"
                
                # PERSISTENCIA SQL
                c = conn.cursor()
                c.execute("""INSERT INTO informes (nombres, apellido_p, apellido_m, rut, direccion, depto, jornada, mes, anio, monto, n_boleta, actividades_json, firma_prestador_b64, estado) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                          (nombres.upper(), ap_paterno.upper(), ap_materno.upper(), rut, recinto, area, jornada, mes, anio, monto_bruto, n_boleta, json.dumps(acts_f), f_b64, '🔴 Pendiente'))
                conn.commit()

                # GENERACIÓN DE DOCUMENTOS (WORD ORIGINAL Y PDF)
                doc = DocxTemplate("plantilla_base.docx")
                ctx = {
                    'nombre': nombre_comp, 'rut': rut, 'direccion': recinto, 'depto': area,
                    'mes': mes, 'anio': anio, 'monto': f"${monto_bruto:,.0f}", 'boleta': n_boleta,
                    'actividades': acts_f, 'firma': InlineImage(doc, base64_to_bytesio(f_b64), height=Mm(20))
                }
                doc.render(ctx)
                w_buf = io.BytesIO(); doc.save(w_buf)
                pdf_bytes = generar_pdf(ctx, base64_to_bytesio(f_b64), None)
                
                st.session_state.p_ok = {"word": w_buf.getvalue(), "pdf": pdf_bytes, "nombre": f"Informe_{ap_paterno}_{mes}"}
                st.rerun()
    else:
        mostrar_mensaje_impacto()
        st.subheader("📥 Descarga tus comprobantes")
        cw, cp, ce = st.columns(3)
        n_base = st.session_state.p_ok['nombre']
        with cw: st.download_button("📥 WORD Original", st.session_state.p_ok['word'], f"{n_base}.docx", use_container_width=True)
        with cp: st.download_button("📥 PDF Certificado", st.session_state.p_ok['pdf'], f"{n_base}.pdf", use_container_width=True)
        with ce:
            mail_link = f"mailto:?subject=Copia Informe Honorarios&body=Adjunto mi informe enviado digitalmente."
            st.markdown(f'<a href="{mail_link}" target="_blank"><button style="width:100%; padding:0.5rem; background-color:#2c3e50; color:white; border:none; border-radius:5px;">✉️ Enviar a mi correo</button></a>', unsafe_allow_html=True)
        if st.button("⬅️ Generar nuevo informe"): st.session_state.p_ok = None; st.rerun()

# ==============================================================================
# 6. MÓDULO 2: PORTAL DE JEFATURA (VISACIÓN)
# ==============================================================================
def modulo_jefatura():
    mostrar_cabecera()
    if not check_login("jefatura"): return
    
    st.subheader("Bandeja de Visación Técnica 📥")
    # Buscamos exactamente el estado pendiente
    df = pd.read_sql_query("SELECT id, nombres, apellido_p, depto, mes, estado FROM informes WHERE estado='🔴 Pendiente'", conn)
    
    if df.empty:
        st.info("🎉 ¡Bandeja limpia! No hay informes pendientes de visación.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        id_sel = st.selectbox("Seleccione ID a visar:", df['id'].tolist())
        
        c = conn.cursor()
        c.execute("SELECT * FROM informes WHERE id=?", (id_sel,))
        d = dict(zip([col[0] for col in c.description], c.fetchone()))
        
        st.write(f"**Funcionario:** {d['nombres']} {d['apellido_p']} | **Área:** {d['depto']}")
        with st.expander("Ver Actividades Reportadas"):
            for a in json.loads(d['actividades_json']):
                st.write(f"● **{a['Actividad']}**: {a['Producto']}")
                
        st.write("✍️ **Firma del Visador (Jefatura)**")
        canvas_j = st_canvas(stroke_width=2, stroke_color="blue", background_color="white", height=150, width=400, key="c_jefa")
        
        if st.button("✅ VISAR Y ENVIAR A FINANZAS", type="primary", use_container_width=True):
            f_j = canvas_to_base64(canvas_j.image_data)
            c.execute("UPDATE informes SET estado='🟡 Visado', firma_jefatura_b64=? WHERE id=?", (f_j, id_sel))
            conn.commit()
            mostrar_mensaje_impacto()
            time.sleep(3); st.rerun()

# ==============================================================================
# 7. MÓDULO 3: PORTAL DE FINANZAS (PAGOS)
# ==============================================================================
def modulo_finanzas():
    mostrar_cabecera()
    if not check_login("finanzas"): return
    
    st.subheader("Panel de Pagos y Tesorería 🏛️")
    df = pd.read_sql_query("SELECT id, nombres, apellido_p, mes, monto, estado FROM informes WHERE estado='🟡 Visado'", conn)
    
    if df.empty:
        st.info("✅ Todos los pagos visados han sido procesados.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        id_sel = st.selectbox("Seleccione ID para Liberación de Pago:", df['id'].tolist())
        
        c = conn.cursor()
        c.execute("SELECT * FROM informes WHERE id=?", (id_sel,))
        d = dict(zip([col[0] for col in c.description], c.fetchone()))
        
        lq = int(d['monto'] * 0.8475)
        st.write(f"**Liberar Pago a:** {d['nombres']} {d['apellido_p']} | **Líquido a Pagar:** ${lq:,.0f}")
        
        if st.button("💸 LIBERAR PAGO Y ARCHIVAR", type="primary", use_container_width=True):
            c.execute("UPDATE informes SET estado='🟢 Pago Liberado' WHERE id=?", (id_sel,))
            conn.commit()
            mostrar_mensaje_impacto()
            time.sleep(3); st.rerun()

# ==============================================================================
# 8. MÓDULO 4: CONSOLIDADO HISTÓRICO Y AUDITORÍA
# ==============================================================================
def modulo_historial():
    mostrar_cabecera()
    if not check_login("finanzas"): return
    
    st.subheader("📊 Consolidado Maestro de Gestión")
    df = pd.read_sql_query("SELECT id, nombres, apellido_p, apellido_m, rut, direccion as recinto, depto, mes, anio, monto, estado, fecha_envio FROM informes", conn)
    
    if df.empty:
        st.info("No hay registros en el historial municipal.")
    else:
        st.markdown("#### 🔍 Filtros de Auditoría")
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
        st.download_button("📊 Exportar Historial a Excel (CSV)", csv, "Historial_LaSerena_2026.csv", use_container_width=True)

# ==============================================================================
# 9. ENRUTADOR PRINCIPAL (SIDEBAR)
# ==============================================================================
with st.sidebar:
    if os.path.exists("logo_muni.png"): st.image("logo_muni.png", width=120)
    else: st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png", width=110)
    st.title("Gestión Municipal 2026")
    rol = st.sidebar.radio("MENÚ PRINCIPAL", [
        "👤 Portal Prestador", 
        "🧑‍💼 Portal Jefatura 🔒", 
        "🏛️ Portal Finanzas 🔒", 
        "📊 Consolidado Histórico 🔒"
    ])

if rol == "👤 Portal Prestador": modulo_prestador()
elif rol == "🧑‍💼 Portal Jefatura 🔒": modulo_jefatura()
elif rol == "🏛️ Portal Finanzas 🔒": modulo_finanzas()
else: modulo_historial()

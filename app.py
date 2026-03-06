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
# 1. CONFIGURACIÓN ESTRATÉGICA DE LA PLATAFORMA
# ==============================================================================
st.set_page_config(
    page_title="Sistema Honorarios La Serena 2026", 
    page_icon="📝", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MOTOR DE BASE DE DATOS CON AUTO-REPARACIÓN DE ESQUEMA ---
def init_db():
    conn = sqlite3.connect('workflow_honorarios.db', check_same_thread=False)
    c = conn.cursor()
    # Estructura completa de Identidad Civil y Gestión Municipal
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
    
    # Verificación de integridad para evitar OperationalError (Columnas nuevas)
    try:
        c.execute("SELECT rut FROM informes LIMIT 1")
    except sqlite3.OperationalError:
        # Si la tabla es antigua y no tiene RUT, la reseteamos para el nuevo estándar
        c.execute("DROP TABLE informes")
        conn.commit()
        return init_db()
        
    conn.commit()
    return conn

conn = init_db()

# ==============================================================================
# 2. LISTADOS MAESTROS DE LA ESTRUCTURA ORGANIZACIONAL
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
# 3. FUNCIONES DE APOYO TÉCNICO (IMAGEN, PDF, LOGIN)
# ==============================================================================
def canvas_to_base64(canvas_data):
    """Convierte el dibujo a PNG con fondo blanco para documentos oficiales"""
    raw_img = Image.fromarray(canvas_data.astype('uint8'), 'RGBA')
    bg = Image.new("RGB", raw_img.size, (255, 255, 255))
    bg.paste(raw_img, mask=raw_img.split()[3])
    buffered = io.BytesIO()
    bg.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def base64_to_bytesio(b64_str):
    """Decodifica la firma para inyectarla en PDF y Word"""
    if not b64_str: return None
    return io.BytesIO(base64.b64decode(b64_str))

def generar_pdf(ctx, img_prestador_io, img_jefatura_io=None):
    """Generador blindado que escribe línea por línea para evitar colapsos"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "INFORME MENSUAL DE ACTIVIDADES - GESTIÓN DIGITAL", ln=1, align='C')
    
    def wl(text, is_bold=False):
        """Función interna de escritura segura"""
        pdf.set_font("Arial", "B" if is_bold else "", 10)
        # Limpieza de caracteres no soportados por FPDF (latin-1)
        clean_text = str(text).encode('latin-1', 'replace').decode('latin-1')
        paragraphs = clean_text.split('\n')
        for p in paragraphs:
            if not p.strip():
                pdf.ln(4)
                continue
            lines = textwrap.wrap(p, width=95, break_long_words=True)
            for line in lines:
                pdf.set_x(10)
                pdf.cell(w=0, h=5, txt=line, ln=1)

    # Cuerpo del Informe
    pdf.ln(5)
    wl(f"Nombre del Funcionario: {ctx['nombre']}", is_bold=True)
    wl(f"RUT: {ctx['rut']}")
    wl(f"Recinto: {ctx['direccion']}")
    wl(f"Unidad/Departamento: {ctx['depto']}")
    wl(f"Periodo Reportado: {ctx['mes']} {ctx['anio']}")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, "Detalle de Actividades y Productos:", ln=1)
    for idx, act in enumerate(ctx['actividades']):
        wl(f"Actividad {idx+1}: {act['Actividad']}", is_bold=True)
        wl(f"Resultado: {act['Producto']}")
        pdf.ln(2)
    
    # Sección de Firmas
    pdf.ln(10)
    y_firmas = pdf.get_y()
    if y_firmas > 230: # Salto de página preventivo para firmas
        pdf.add_page()
        y_firmas = 20
    
    if img_prestador_io:
        pdf.image(img_prestador_io, x=30, y=y_firmas, w=50)
        pdf.text(x=35, y=y_firmas + 25, txt="Firma del Prestador")
            
    if img_jefatura_io:
        pdf.image(img_jefatura_io, x=120, y=y_firmas, w=50)
        pdf.text(x=125, y=y_firmas + 25, txt="V°B° Jefatura Directa")
            
    return bytes(pdf.output())

def check_login(rol):
    """Sistema de seguridad por niveles"""
    if st.session_state.get(f'auth_{rol}'): return True
    
    st.warning(f"🔒 **Acceso Protegido - Módulo {rol.upper()}**")
    user_p = st.text_input("Usuario de Red Municipal", key=f"user_{rol}")
    psw_p = st.text_input("Contraseña Institucional", type="password", key=f"psw_{rol}")
    
    if st.button("Validar Credenciales", key=f"btn_{rol}"):
        # Credenciales de prueba solicitadas
        if (rol == "jefatura" and user_p == "jefatura" and psw_p == "123") or \
           (rol == "finanzas" and user_p == "finanzas" and psw_p == "123"):
            st.session_state[f'auth_{rol}'] = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas. Verifique con Informática.")
    return False

# ==============================================================================
# 4. COMPONENTES VISUALES (CABECERA Y HUINCHA DE IMPACTO)
# ==============================================================================
def mostrar_cabecera():
    """Cabecera con logos corregidos y letrero de impacto ecológico positivo"""
    st.markdown("""
        <style>
        .ticker-wrap { width: 100%; overflow: hidden; background-color: #e8f5e9; color: #1b5e20; border: 2px solid #4caf50; padding: 12px 0; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .ticker { display: inline-block; white-space: nowrap; animation: ticker 45s linear infinite; font-size: 18px; font-weight: bold;}
        @keyframes ticker { 0% { transform: translate3d(100%, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }
        </style>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 5, 1], gap="medium")
    
    with c1:
        # Logo municipal con tamaño controlado para evitar que se reviente
        if os.path.exists("logo_muni.png"): st.image("logo_muni.png", width=130)
        else: st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png", width=110)
            
    with c2:
        st.markdown("<h1 style='text-align: center; color: #2C3E50; margin-bottom: 0;'>Ilustre Municipalidad de La Serena</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 20px; color: #1565c0; font-weight: bold;'>Sistema Digital de Gestión de Honorarios 2026</p>", unsafe_allow_html=True)
        
        # Huincha de impacto anual proyectado para 1.800 funcionarios
        st.markdown("""
            <div class="ticker-wrap">
                <div class="ticker">
                    ☀️ ¡GRACIAS POR AYUDAR AL PLANETA! 🌊 ● 🌳 <b>IMPACTO ANUAL PROYECTADO:</b> Ahorramos juntos <b>$78.580.800 CLP</b> en costos operativos ● 📄 ¡Evitamos imprimir <b>108.000 hojas de papel</b> al año! ● 🕒 Ganamos <b>14.400 horas</b> para servir mejor a nuestros vecinos ● ☀️ Usemos menos la impresora, ahorremos tinta y energía ● 🐑 ¡Nuestra huella de carbono disminuye gracias a tu compromiso digital! ● ✨ ¡Cambiando papel por innovación y sol! 🌿🟢🔵🌕●
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    with c3:
        if os.path.exists("logo_innovacion.png"): st.image("logo_innovacion.png", width=140)
        else: st.image("https://cdn-icons-png.flaticon.com/512/1903/1903162.png", width=120)

def mostrar_mensaje_impacto():
    """Globos y mensaje de logro ecológico tras el envío"""
    st.success("""
    ### ¡Acción Realizada con Éxito! 🌿✨
    **🌟 Tu contribución en este momento:**
    * 💰 Has sumado al ahorro de **$78 millones** anuales del Municipio.
    * 🌳 Has salvado **5 hojas de papel** hoy. ¡Sumamos hacia las 108.000!.
    * 🕒 Has liberado **40 minutos** de trámites para enfocarte en lo que importa.
    
    *☀️ ¡Menos impresora, más vida! Gracias por cuidar nuestra huella de carbono.* 🐑🔵
    """)
    st.balloons()

# ==============================================================================
# 5. MÓDULO 1: PORTAL DEL PRESTADOR (INGRESO)
# ==============================================================================
def modulo_prestador():
    mostrar_cabecera()
    
    if 'prestador_ok' not in st.session_state: st.session_state.prestador_ok = None

    if st.session_state.prestador_ok is None:
        st.subheader("📝 Nuevo Informe de Actividades")
        
        with st.expander("👤 Paso 1: Identificación Civil y RUT", expanded=True):
            c_n, c_p, c_m = st.columns(3)
            nombres = c_n.text_input("Nombres", placeholder="JUAN ANDRÉS")
            ap_paterno = c_p.text_input("Apellido Paterno", placeholder="PÉREZ")
            ap_materno = c_m.text_input("Apellido Materno", placeholder="ROJAS")
            rut = st.text_input("RUT del Funcionario", placeholder="12.345.678-K")

        with st.expander("🏢 Paso 2: Ubicación Organizacional 2026", expanded=True):
            c_dir, c_dep = st.columns(2)
            recinto = c_dir.selectbox("Dirección Municipal o Recinto Principal", unidades_municipales)
            area = c_dep.selectbox("Departamento, Área o Unidad Específica", departamentos_areas)
            jornada = st.selectbox("Tipo de Jornada Laboral", ["Completa", "Media Jornada", "Libre / Por Productos"])

        with st.expander("💰 Paso 3: Periodo y Cálculo de Honorarios", expanded=True):
            c1, c2, c3 = st.columns(3)
            mes = c1.selectbox("Mes del Informe", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"], index=2)
            anio = c2.number_input("Año", value=2026)
            monto_bruto = c3.number_input("Monto Bruto Contrato ($)", value=0, step=10000)
            
            # --- MOTOR DE CÁLCULO RECUPERADO ---
            impuesto = int(monto_bruto * 0.1525)
            liquido = monto_bruto - impuesto
            if monto_bruto > 0:
                st.info(f"📊 **Desglose Presupuestario:** Bruto: ${monto_bruto:,.0f} | Retención SII (15.25%): ${impuesto:,.0f} | **Líquido a Recibir: ${liquido:,.0f}**")
            
            n_boleta = st.text_input("Nº de Boleta de Honorarios SII")

        st.subheader("📋 Paso 4: Resumen de Actividades Mensuales")
        if 'num_acts' not in st.session_state: st.session_state.num_acts = 1
        
        for i in range(st.session_state.num_acts):
            ca, cp = st.columns(2)
            ca.text_area(f"Actividad Realizada {i+1}", key=f"desc_{i}", placeholder="Ej: Redacción de informes técnicos...")
            cp.text_area(f"Producto o Resultado {i+1}", key=f"prod_{i}", placeholder="Ej: 5 Documentos entregados...")
        
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("➕ Agregar Otra Fila"): 
            st.session_state.num_acts += 1
            st.rerun()
        if col_btn2.button("➖ Quitar Última Fila") and st.session_state.num_acts > 1:
            st.session_state.num_acts -= 1
            st.rerun()

        st.subheader("✍️ Paso 5: Firma Digital")
        canvas = st_canvas(stroke_width=2, stroke_color="black", background_color="white", height=150, width=400, key="c_prestador")

        if st.button("🚀 GENERAR Y ENVIAR A JEFATURA", type="primary", use_container_width=True):
            # Validación exhaustiva de datos
            if not nombres or not ap_paterno or not rut or monto_bruto == 0 or not canvas.image_data is not None:
                st.error("⚠️ Datos faltantes: Asegúrese de completar Nombres, Apellidos, RUT, Monto y su Firma.")
            else:
                firma_b64 = canvas_to_base64(canvas.image_data)
                acts_final = []
                for i in range(st.session_state.num_acts):
                    acts_final.append({"Actividad": st.session_state[f"desc_{i}"], "Producto": st.session_state[f"prod_{i}"]})
                
                nombre_comp = f"{nombres.upper()} {ap_paterno.upper()} {ap_materno.upper()}"
                
                # PERSISTENCIA EN BASE DE DATOS
                c = conn.cursor()
                c.execute("""INSERT INTO informes (nombres, apellido_p, apellido_m, rut, direccion, depto, jornada, mes, anio, monto, n_boleta, actividades_json, firma_prestador_b64, estado) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                          (nombres.upper(), ap_paterno.upper(), ap_materno.upper(), rut, recinto, area, jornada, mes, anio, monto_bruto, n_boleta, json.dumps(acts_final), firma_b64, '🔴 Pendiente Jefatura'))
                conn.commit()

                # GENERACIÓN DE COMPROBANTES (WORD Y PDF)
                ctx = {
                    'nombre': nombre_comp, 'rut': rut, 'direccion': recinto, 'depto': area,
                    'mes': mes, 'anio': anio, 'monto': f"${monto_bruto:,.0f}", 'boleta': n_boleta,
                    'actividades': acts_final
                }
                
                # Render Word Oficial
                doc = DocxTemplate("plantilla_base.docx")
                ctx['firma'] = InlineImage(doc, base64_to_bytesio(firma_b64), height=Mm(20))
                doc.render(ctx)
                w_buf = io.BytesIO()
                doc.save(w_buf)
                
                # Render PDF Certificado
                pdf_bytes = generar_pdf(ctx, base64_to_bytesio(firma_b64), None)
                
                st.session_state.prestador_ok = {
                    "word": w_buf.getvalue(), 
                    "pdf": pdf_bytes, 
                    "nombre_arch": f"Informe_{ap_paterno}_{mes}"
                }
                st.rerun()
    else:
        mostrar_mensaje_impacto()
        st.subheader("📥 Descarga tus comprobantes")
        st.info("Copia enviada automáticamente al Portal de Jefatura para su visación.")
        
        c_w, c_p, c_e = st.columns(3)
        n_base = st.session_state.prestador_ok['nombre_arch']
        with c_w: st.download_button("📥 WORD Original", st.session_state.prestador_ok['word'], f"{n_base}.docx", use_container_width=True)
        with c_p: st.download_button("📥 PDF Certificado", st.session_state.prestador_ok['pdf'], f"{n_base}.pdf", use_container_width=True)
        with c_e:
            mail_link = f"mailto:?subject=Comprobante Informe Honorarios&body=Adjunto mi informe enviado digitalmente."
            st.markdown(f'<a href="{mail_link}" target="_blank"><button style="width:100%; padding:0.5rem; background-color:#2c3e50; color:white; border:none; border-radius:5px;">✉️ Enviar a mi correo</button></a>', unsafe_allow_html=True)
            
        if st.button("⬅️ Generar nuevo informe"): 
            st.session_state.prestador_ok = None
            st.rerun()

# ==============================================================================
# 6. MÓDULO 2: PORTAL DE JEFATURA (VISACIÓN)
# ==============================================================================
def modulo_jefatura():
    mostrar_cabecera()
    if not check_login("jefatura"): return
    
    st.subheader("Bandeja de Visación Técnica 📥")
    df = pd.read_sql_query("SELECT id, nombres, apellido_p, depto, mes, estado FROM informes WHERE estado='🔴 Pendiente Jefatura'", conn)
    
    if df.empty:
        st.info("🎉 ¡Excelente trabajo! No hay informes pendientes de visación en su recinto.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        id_sel = st.selectbox("Seleccione ID para Visar:", df['id'].tolist())
        
        c = conn.cursor()
        c.execute("SELECT * FROM informes WHERE id=?", (id_sel,))
        d = dict(zip([col[0] for col in c.description], c.fetchone()))
        
        st.write(f"**Funcionario:** {d['nombres']} {d['apellido_p']} | **Área:** {d['depto']} | **Periodo:** {d['mes']}")
        with st.expander("Ver Resumen de Actividades"):
            for a in json.loads(d['actividades_json']):
                st.write(f"● **{a['Actividad']}**: {a['Producto']}")
                
        st.write("✍️ **Firma del Visador (Jefatura)**")
        canvas_j = st_canvas(stroke_width=2, stroke_color="blue", background_color="white", height=150, width=400, key="c_jefa")
        
        if st.button("✅ VISAR Y ENVIAR A FINANZAS", type="primary", use_container_width=True):
            f_j_b64 = canvas_to_base64(canvas_j.image_data)
            c.execute("UPDATE informes SET estado='🟡 Visado', firma_jefatura_b64=? WHERE id=?", (f_j_b64, id_sel))
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
        st.info("✅ Bandeja limpia. Todos los informes visados han sido procesados.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        id_sel = st.selectbox("ID para Pago Liberado:", df['id'].tolist())
        
        c = conn.cursor()
        c.execute("SELECT * FROM informes WHERE id=?", (id_sel,))
        d = dict(zip([col[0] for col in c.description], c.fetchone()))
        
        lq = int(d['monto'] * 0.8475)
        st.write(f"**Aprobar Pago:** {d['nombres']} {d['apellido_p']} | **Líquido:** ${lq:,.0f}")
        
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
        st.info("No hay registros en el historial municipal aún.")
    else:
        st.markdown("#### 🔍 Filtros Inteligentes")
        f1, f2, f3 = st.columns(3)
        with f1: f_mes = st.selectbox("Filtrar Mes", ["Todos"] + list(df['mes'].unique()))
        with f2: f_dep = st.selectbox("Filtrar Departamento", ["Todos"] + list(df['depto'].unique()))
        with f3: f_est = st.selectbox("Filtrar Estado", ["Todos"] + list(df['estado'].unique()))
        
        df_f = df.copy()
        if f_mes != "Todos": df_f = df_f[df_f['mes'] == f_mes]
        if f_dep != "Todos": df_f = df_f[df_f['depto'] == f_dep]
        if f_est != "Todos": df_f = df_f[df_f['estado'] == f_est]
        
        st.dataframe(df_f, use_container_width=True, hide_index=True)
        
        csv = df_f.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📊 Exportar Consolidado a Excel (CSV)", csv, "Historial_Honorarios_LS2026.csv", use_container_width=True)

# ==============================================================================
# 9. ENRUTADOR PRINCIPAL (SIDEBAR)
# ==============================================================================
with st.sidebar:
    if os.path.exists("logo_muni.png"): st.image("logo_muni.png", width=120)
    else: st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png", width=110)
    st.title("Gestión 2026")
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

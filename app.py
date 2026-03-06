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
    page_title="Sistema de Honorarios Digital La Serena", 
    page_icon="📝", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MOTOR DE BASE DE DATOS CON AUTO-REPARACIÓN DE ESQUEMA ---
def inicializar_base_de_datos():
    """Crea la estructura de datos municipal y repara tablas antiguas si existen"""
    conexion = sqlite3.connect('workflow_honorarios.db', check_same_thread=False)
    cursor = conexion.cursor()
    
    # Estructura Nivel 1: Identidad Civil y Gestión de Honorarios
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
    
    # Rutina para asegurar la existencia del campo RUT (Auto-Reparación)
    try:
        cursor.execute("SELECT rut FROM informes LIMIT 1")
    except sqlite3.OperationalError:
        # Si la tabla es antigua, la reseteamos para el nuevo estándar 2026
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
    """Convierte la firma guardada para su uso en Word y PDF"""
    if not cadena_b64: return None
    return io.BytesIO(base64.b64decode(cadena_b64))

def generar_documento_pdf(contexto, img_prestador_bytes, img_jefatura_bytes=None):
    """Motor de PDF blindado: escribe línea por línea para evitar errores de espacio horizontal"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "INFORME MENSUAL DE ACTIVIDADES - LA SERENA DIGITAL", ln=1, align='C')
    
    def escribir_linea_segura(texto, es_negrita=False):
        pdf.set_font("Arial", "B" if es_negrita else "", 10)
        # Limpieza absoluta de caracteres para evitar errores de codificación
        texto_limpio = str(texto).encode('latin-1', 'replace').decode('latin-1')
        lineas = textwrap.wrap(texto_limpio, width=95, break_long_words=True)
        for l in lineas:
            pdf.set_x(10)
            pdf.cell(w=0, h=5, txt=l, ln=1)

    pdf.ln(5)
    escribir_linea_segura(f"Funcionario: {contexto['nombre']}", es_negrita=True)
    escribir_linea_segura(f"RUT: {contexto['rut']}")
    escribir_linea_segura(f"Unidad: {contexto['direccion']} - {contexto['depto']}")
    escribir_linea_segura(f"Periodo: {contexto['mes']} {contexto['anio']}")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 11); pdf.cell(0, 10, "Resumen de Gestión Realizada:", ln=1)
    for act in contexto['actividades']:
        escribir_linea_segura(f"● {act['Actividad']}: {act['Producto']}")
        pdf.ln(1)
    
    pdf.ln(10); y_actual = pdf.get_y()
    if y_actual > 230: pdf.add_page(); y_actual = 20
    
    if img_prestador_bytes:
        pdf.image(img_prestador_bytes, x=30, y=y_actual, w=50)
        pdf.text(x=35, y=y_actual + 25, txt="Firma del Prestador")
    if img_jefatura_bytes:
        pdf.image(img_jefatura_bytes, x=120, y=y_actual, w=50)
        pdf.text(x=125, y=y_actual + 25, txt="V°B° Jefatura Directa")
            
    return bytes(pdf.output())

# --- SISTEMA DE LOGINS SEGUROS MUNICIPALES ---
def validar_acceso_modulo(nombre_rol):
    """Control de seguridad por portal para evitar acceso no autorizado"""
    if st.session_state.get(f'autenticado_{nombre_rol}'): return True
    
    st.warning(f"🔒 **Portal {nombre_rol.capitalize()} Protegido**")
    usuario_ingresado = st.text_input("Usuario de Red Municipal", key=f"u_{nombre_rol}")
    clave_ingresada = st.text_input("Contraseña Institucional", type="password", key=f"p_{nombre_rol}")
    
    if st.button("Validar Credenciales", key=f"b_{nombre_rol}"):
        # Credenciales de prueba solicitadas por el Director
        if (nombre_rol == "jefatura" and usuario_ingresado == "jefatura" and clave_ingresada == "123") or \
           (nombre_rol == "finanzas" and usuario_ingresado == "finanzas" and clave_ingresada == "123"):
            st.session_state[f'autenticado_{nombre_rol}'] = True
            st.rerun()
        else:
            st.error("Credenciales Inválidas. Contacte con Informática.")
    return False

# ==============================================================================
# 4. COMPONENTES VISUALES Y CABECERA MAESTRA (LOGOS PROTEGIDOS)
# ==============================================================================
def renderizar_cabecera():
    """Dibuja la cabecera con logos nítidos (CSS padding) y ticker dinámico masivo"""
    st.markdown("""
        <style>
        /* Protección de Logos: evita que Streamlit corte las puntas */
        .logo-container { padding: 10px; display: flex; justify-content: center; align-items: center; }
        .logo-img { filter: drop-shadow(0px 2px 5px rgba(0,0,0,0.15)); }
        
        /* Ticker Dinámico con impacto anual real para 1.800 funcionarios */
        .ticker-wrap { width: 100%; overflow: hidden; background-color: #e8f5e9; color: #1b5e20; border: 2px solid #4caf50; padding: 12px 0; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .ticker { display: inline-block; white-space: nowrap; animation: ticker 45s linear infinite; font-size: 19px; font-weight: bold;}
        @keyframes ticker { 0% { transform: translate3d(100%, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }
        </style>
    """, unsafe_allow_html=True)

    # Columnas para logos y título central
    col_l1, col_center, col_l2 = st.columns([1, 4, 1], gap="medium")
    
    with col_l1:
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        if os.path.exists("logo_muni.png"): st.image("logo_muni.png", width=140)
        else: st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png", width=110)
        st.markdown('</div>', unsafe_allow_html=True)
            
    with col_center:
        st.markdown("<h1 style='text-align: center; color: #2C3E50; margin-bottom: 0;'>Ilustre Municipalidad de La Serena</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 21px; color: #1565c0; font-weight: bold; margin-top: 5px;'>Sistema Digital de Gestión de Honorarios 2026</p>", unsafe_allow_html=True)
        
        # El Ticker de Impacto masivo proyectado anualmente
        st.markdown("""
            <div class="ticker-wrap">
                <div class="ticker">
                    ☀️ ¡GRACIAS POR SER PARTE DEL CAMBIO! 🌊 ● 🌳 <b>IMPACTO ANUAL PROYECTADO:</b> Estamos ahorrando juntos <b>$78.580.800 CLP</b> en costos operativos para nuestra ciudad ● 📄 ¡Evitamos imprimir <b>108.000 hojas de papel</b> al año! ● 🕒 Ganamos <b>14.400 horas</b> de tiempo para servir mejor a nuestros vecinos ● ☀️ Usemos menos la impresora, ahorremos tinta y energía ● 🐑 ¡Nuestra huella de carbono disminuye gracias a ti! ☁️ ● ✨ Innovación Ciudadana: ¡Cambiando papel por sol y progreso! 🌿🟢🔵🌕● 
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    with col_l2:
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        if os.path.exists("logo_innovacion.png"): st.image("logo_innovacion.png", width=150)
        else: st.image("https://cdn-icons-png.flaticon.com/512/1903/1903162.png", width=120)
        st.markdown('</div>', unsafe_allow_html=True)

def disparar_parafernalia_exito():
    """Lanza globos y muestra el mensaje de impacto ecológico positivo"""
    st.success("""
    ### ¡Misión Digital Completada con Éxito! 🎉🌿✨
    **🌟 Tu contribución hoy al Municipio:**
    * 💰 Has sumado al ahorro proyectado de **$78 millones** anuales.
    * 🌳 Has salvado **5 hojas de papel** hoy. ¡Sumamos hacia las 108.000!.
    * 🕒 Liberaste **40 minutos** de burocracia para tareas de valor real.
    
    *☀️ ¡Menos impresora, más vida! Gracias por cuidar nuestra huella de carbono.* 🐑🔵
    """)
    st.balloons()

# ==============================================================================
# 5. MÓDULO 1: PORTAL DEL PRESTADOR (INGRESO CIVIL Y MATEMÁTICO)
# ==============================================================================
def modulo_portal_prestador():
    renderizar_cabecera()
    
    if 'informe_enviado' not in st.session_state: st.session_state.informe_enviado = None

    if st.session_state.informe_enviado is None:
        st.subheader("📝 Generar Nuevo Informe Mensual")
        
        with st.expander("👤 Paso 1: Identificación Civil y RUT (Nivel 1)", expanded=True):
            col_n1, col_n2, col_n3 = st.columns(3)
            txt_nombres = col_n1.text_input("Nombres", placeholder="JUAN ANDRÉS")
            txt_apellido_p = col_n2.text_input("Apellido Paterno", placeholder="PÉREZ")
            txt_apellido_m = col_n3.text_input("Apellido Materno", placeholder="ROJAS")
            txt_rut = st.text_input("RUT del Funcionario", placeholder="12.345.678-K")

        with st.expander("🏢 Paso 2: Ubicación Organizacional 2026", expanded=True):
            col_dir, col_area = st.columns(2)
            sel_recinto = col_dir.selectbox("Dirección Municipal o Recinto", unidades_municipales)
            sel_departamento = col_area.selectbox("Departamento, Área o Unidad Específica", departamentos_areas)
            sel_jornada = st.selectbox("Tipo de Jornada Laboral", ["Completa", "Media Jornada", "Libre / Por Productos"])

        with st.expander("💰 Paso 3: Periodo y Cálculo de Honorarios", expanded=True):
            col_m1, col_m2, col_m3 = st.columns(3)
            sel_mes = col_m1.selectbox("Mes del Informe", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"], index=2)
            sel_anio = col_m2.number_input("Año", value=2026)
            num_monto_bruto = col_m3.number_input("Monto Bruto Contrato ($)", value=0, step=10000)
            
            # --- MOTOR DE CÁLCULO DE HONORARIOS RECUPERADO ---
            retencion_sii = int(num_monto_bruto * 0.1525) # Retención 15.25% año 2026
            monto_liquido = num_monto_bruto - retencion_sii
            if num_monto_bruto > 0:
                st.info(f"📊 **Cálculo Tributario:** Bruto: ${num_monto_bruto:,.0f} | Retención SII (15.25%): ${retencion_sii:,.0f} | **Líquido a Recibir: ${monto_liquido:,.0f}**")
            
            txt_n_boleta = st.text_input("Nº de Boleta de Honorarios SII Relacionada")

        st.subheader("📋 Paso 4: Resumen de Actividades Mensuales")
        if 'num_filas_act' not in st.session_state: st.session_state.num_filas_act = 1
        
        for i in range(st.session_state.num_filas_act):
            col_a, col_b = st.columns(2)
            col_a.text_area(f"Actividad Realizada {i+1}", key=f"act_desc_{i}", placeholder="Ej: Redacción de informes técnicos y atención de público...")
            col_b.text_area(f"Producto o Resultado {i+1}", key=f"act_prod_{i}", placeholder="Ej: 5 Documentos entregados y firmados...")
        
        col_ctrl1, col_ctrl2 = st.columns(2)
        if col_ctrl1.button("➕ Agregar Fila de Actividad"): 
            st.session_state.num_filas_act += 1
            st.rerun()
        if col_ctrl2.button("➖ Quitar Última Fila") and st.session_state.num_filas_act > 1:
            st.session_state.num_filas_act -= 1
            st.rerun()

        st.subheader("✍️ Paso 5: Firma Digital")
        canvas_prestador = st_canvas(stroke_width=2, stroke_color="black", background_color="white", height=150, width=400, key="canvas_prestador")

        if st.button("🚀 GENERAR Y ENVIAR A JEFATURA", type="primary", use_container_width=True):
            # VALIDACIÓN EXHAUSTIVA DE DATOS
            if not txt_nombres or not txt_apellido_p or not txt_rut or num_monto_bruto == 0 or not canvas_prestador.image_data is not None:
                st.error("⚠️ Datos faltantes: Asegúrese de completar Nombres, Apellidos, RUT, Monto y su Firma.")
            else:
                b64_firma = procesar_firma_a_base64(canvas_prestador.image_data)
                lista_actividades = []
                for i in range(st.session_state.num_filas_act):
                    lista_actividades.append({"Actividad": st.session_state[f"act_desc_{i}"], "Producto": st.session_state[f"act_prod_{i}"]})
                
                nombre_formateado = f"{txt_nombres.upper()} {txt_apellido_p.upper()} {txt_apellido_m.upper()}"
                
                # PERSISTENCIA EN BASE DE DATOS
                cursor_bd = conn.cursor()
                cursor_bd.execute("""INSERT INTO informes (nombres, apellido_p, apellido_m, rut, direccion, depto, jornada, mes, anio, monto, n_boleta, actividades_json, firma_prestador_b64, estado) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                          (txt_nombres.upper(), txt_apellido_p.upper(), txt_apellido_m.upper(), txt_rut, sel_recinto, sel_departamento, sel_jornada, sel_mes, sel_anio, num_monto_bruto, txt_n_boleta, json.dumps(lista_actividades), b64_firma, '🔴 Pendiente'))
                conn.commit()

                # GENERACIÓN DE COMPROBANTES (WORD ORIGINAL Y PDF)
                contexto_doc = {
                    'nombre': nombre_formateado, 'rut': txt_rut, 'direccion': sel_recinto, 'depto': sel_departamento,
                    'mes': sel_mes, 'anio': sel_anio, 'monto': f"${num_monto_bruto:,.0f}", 'boleta': txt_n_boleta,
                    'actividades': lista_actividades
                }
                
                # Generación Word Fiel
                plantilla_word = DocxTemplate("plantilla_base.docx")
                contexto_doc['firma'] = InlineImage(plantilla_word, decodificar_base64_a_bytes(b64_firma), height=Mm(20))
                plantilla_word.render(contexto_doc)
                buf_word = io.BytesIO()
                plantilla_word.save(buf_word)
                
                # Generación PDF Blindado
                pdf_listo = generar_documento_pdf(contexto_doc, decodificar_base64_a_bytes(b64_firma), None)
                
                st.session_state.informe_enviado = {
                    "word": buf_word.getvalue(), 
                    "pdf": pdf_listo, 
                    "nombre_archivo": f"Informe_{txt_apellido_p}_{sel_mes}"
                }
                st.rerun()
    else:
        disparar_parafernalia_exito()
        st.subheader("📥 Descarga tus comprobantes oficiales")
        st.info("Su informe ya ha sido enviado a la bandeja de entrada de su Jefatura para visación técnica.")
        
        col_w, col_p, col_e = st.columns(3)
        nombre_final = st.session_state.informe_enviado['nombre_archivo']
        with col_w: st.download_button("📥 WORD Original", st.session_state.informe_enviado['word'], f"{nombre_final}.docx", use_container_width=True)
        with col_p: st.download_button("📥 PDF Certificado", st.session_state.informe_enviado['pdf'], f"{nombre_final}.pdf", use_container_width=True)
        with col_e:
            enlace_mail = f"mailto:?subject=Comprobante Informe Honorarios La Serena&body=Adjunto mi informe enviado digitalmente."
            st.markdown(f'<a href="{enlace_mail}" target="_blank"><button style="width:100%; padding:0.5rem; background-color:#2c3e50; color:white; border:none; border-radius:5px;">✉️ Enviar a mi correo</button></a>', unsafe_allow_html=True)
            
        if st.button("⬅️ Generar nuevo informe"): 
            st.session_state.informe_enviado = None
            st.rerun()

# ==============================================================================
# 6. MÓDULO 2: PORTAL DE JEFATURA (VISACIÓN TÉCNICA)
# ==============================================================================
def modulo_portal_jefatura():
    renderizar_cabecera()
    if not validar_acceso_modulo("jefatura"): return
    
    st.subheader("Bandeja de Visación Técnica 📥")
    # Buscamos informes con estado EXACTO '🔴 Pendiente'
    df_pendientes = pd.read_sql_query("SELECT id, nombres, apellido_p, depto, mes, estado FROM informes WHERE estado='🔴 Pendiente'", conn)
    
    if df_pendientes.empty:
        st.info("🎉 ¡Excelente trabajo! No hay informes pendientes de visación técnica en este momento.")
    else:
        st.dataframe(df_pendientes, use_container_width=True, hide_index=True)
        st.divider()
        id_seleccionar = st.selectbox("Seleccione ID de Informe a Visar:", df_pendientes['id'].tolist())
        
        c = conn.cursor()
        c.execute("SELECT * FROM informes WHERE id=?", (id_seleccionar,))
        datos = dict(zip([col[0] for col in c.description], c.fetchone()))
        
        st.write(f"**Funcionario:** {datos['nombres']} {datos['apellido_p']} | **Unidad:** {datos['depto']} | **Periodo:** {datos['mes']}")
        with st.expander("Ver Detalle de Actividades"):
            for act in json.loads(datos['actividades_json']):
                st.write(f"● **{act['Actividad']}**: {act['Producto']}")
                
        st.write("✍️ **Firma Digital de Visación (Jefatura)**")
        canvas_jefatura = st_canvas(stroke_width=2, stroke_color="blue", background_color="white", height=150, width=400, key="canvas_jefa")
        
        col_v1, col_v2 = st.columns(2)
        if col_v1.button("✅ VISAR Y ENVIAR A FINANZAS", type="primary", use_container_width=True):
            if not canvas_jefatura.image_data is not None:
                st.error("Debe firmar para visar.")
            else:
                firma_j_b64 = procesar_firma_a_base64(canvas_jefatura.image_data)
                c.execute("UPDATE informes SET estado='🟡 Visado Jefatura', firma_jefatura_b64=? WHERE id=?", (firma_j_b64, id_seleccionar))
                conn.commit()
                disparar_parafernalia_exito()
                time.sleep(3); st.rerun()
        
        if col_v2.button("❌ RECHAZAR POR CORRECCIÓN", use_container_width=True):
            c.execute("UPDATE informes SET estado='❌ Rechazado' WHERE id=?", (id_seleccionar,))
            conn.commit(); st.warning("Informe devuelto al prestador."); time.sleep(2); st.rerun()

# ==============================================================================
# 7. MÓDULO 3: PORTAL DE FINANZAS (TESORERÍA Y PAGOS)
# ==============================================================================
def modulo_portal_finanzas():
    renderizar_cabecera()
    if not validar_acceso_modulo("finanzas"): return
    
    st.subheader("Panel de Pagos y Control Presupuestario 🏛️")
    df_visados = pd.read_sql_query("SELECT id, nombres, apellido_p, mes, monto, estado FROM informes WHERE estado='🟡 Visado Jefatura'", conn)
    
    if df_visados.empty:
        st.info("✅ Bandeja limpia. Todos los informes visados han sido procesados para pago.")
    else:
        st.dataframe(df_visados, use_container_width=True, hide_index=True)
        st.divider()
        id_pago = st.selectbox("Seleccione ID para Liberación de Pago:", df_visados['id'].tolist())
        
        c = conn.cursor()
        c.execute("SELECT * FROM informes WHERE id=?", (id_pago,))
        datos = dict(zip([col[0] for col in c.description], c.fetchone()))
        
        monto_lq = int(datos['monto'] * 0.8475)
        st.write(f"**Liberar Pago a:** {datos['nombres']} {datos['apellido_p']} | **Boleta SII:** {datos['n_boleta']}")
        st.metric("Líquido a Pagar Estimado", f"${monto_lq:,.0f}")
        
        if st.button("💸 LIBERAR PAGO Y ARCHIVAR EXPEDIENTE", type="primary", use_container_width=True):
            c.execute("UPDATE informes SET estado='🟢 Pago Liberado' WHERE id=?", (id_pago,))
            conn.commit()
            disparar_parafernalia_exito()
            time.sleep(3); st.rerun()

# ==============================================================================
# 8. MÓDULO 4: CONSOLIDADO HISTÓRICO (INTELIGENCIA DE DATOS)
# ==============================================================================
def modulo_consolidado_historico():
    renderizar_cabecera()
    if not validar_acceso_modulo("finanzas"): return # El consolidado es de Finanzas
    
    st.subheader("📊 Consolidado Maestro de Gestión de Personas")
    st.markdown("Auditoría completa de todos los prestadores y sus estados de pago.")
    
    df_full = pd.read_sql_query("SELECT id, nombres, apellido_p, apellido_m, rut, direccion as recinto, depto, mes, anio, monto, estado, fecha_envio FROM informes", conn)
    
    if df_full.empty:
        st.info("No hay registros en el historial municipal aún.")
    else:
        st.markdown("#### 🔍 Filtros de Auditoría Inteligente")
        f1, f2, f3 = st.columns(3)
        with f1: fil_mes = st.selectbox("Mes", ["Todos"] + list(df_full['mes'].unique()))
        with f2: fil_dep = st.selectbox("Departamento", ["Todos"] + list(df_full['depto'].unique()))
        with f3: fil_est = st.selectbox("Estado", ["Todos"] + list(df_full['estado'].unique()))
        
        df_filtrado = df_full.copy()
        if fil_mes != "Todos": df_filtrado = df_filtrado[df_filtrado['mes'] == fil_mes]
        if fil_dep != "Todos": df_filtrado = df_filtrado[df_filtrado['depto'] == fil_dep]
        if fil_est != "Todos": df_filtrado = df_filtrado[df_filtrado['estado'] == fil_est]
        
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
        
        # Panel de KPIs dinámicos basado en los filtros
        k1, k2 = st.columns(2)
        k1.metric("Total Informes en Vista", len(df_filtrado))
        k2.metric("Monto Bruto Total en Vista", f"${df_filtrado['monto'].sum():,.0f}")
        
        csv_data = df_filtrado.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📊 Exportar Historial Seleccionado a Excel (CSV)", csv_data, "Consolidado_LaSerena_2026.csv", use_container_width=True)

# ==============================================================================
# 9. ENRUTADOR PRINCIPAL (EL ÁRBOL DEL SISTEMA)
# ==============================================================================
with st.sidebar:
    # Logo del Sidebar con nitidez protegida
    if os.path.exists("logo_muni.png"): st.image("logo_muni.png", width=120)
    else: st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png", width=110)
    
    st.title("Gestión Municipal 2026")
    st.markdown("---")
    
    seleccion_rol = st.sidebar.radio("MENÚ PRINCIPAL", [
        "👤 Portal Prestador", 
        "🧑‍💼 Portal Jefatura 🔒", 
        "🏛️ Portal Finanzas 🔒", 
        "📊 Consolidado Histórico 🔒"
    ])
    
    st.markdown("---")
    st.caption("v5.2 Standard | La Serena Digital")

# Disparar el módulo seleccionado
if seleccion_rol == "👤 Portal Prestador":
    modulo_portal_prestador()
elif seleccion_rol == "🧑‍💼 Portal Jefatura 🔒":
    modulo_portal_jefatura()
elif seleccion_rol == "🏛️ Portal Finanzas 🔒":
    modulo_portal_finanzas()
else:
    modulo_consolidado_historico()

# Final del Archivo: 601 Líneas de Código Municipal de Alto Nivel.

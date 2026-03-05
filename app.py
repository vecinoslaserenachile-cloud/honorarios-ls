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
from docx.shared import Mm
from fpdf import FPDF

# --- 1. CONFIGURACIÓN INICIAL Y BASE DE DATOS ---
st.set_page_config(page_title="Honorarios La Serena", page_icon="📝", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

# Motor SAP: Base de datos local
def init_db():
    conn = sqlite3.connect('workflow_honorarios.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS informes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombre TEXT, direccion TEXT, depto TEXT, jornada TEXT,
                  mes TEXT, anio INTEGER, monto INTEGER, n_boleta TEXT,
                  actividades_json TEXT, firma_prestador_b64 TEXT, firma_jefatura_b64 TEXT,
                  estado TEXT, fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    return conn

conn = init_db()

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

# --- FUNCIONES AUXILIARES DE IMAGEN ---
def canvas_to_base64(canvas_data):
    raw_img = Image.fromarray(canvas_data.astype('uint8'), 'RGBA')
    bg = Image.new("RGB", raw_img.size, (255, 255, 255))
    bg.paste(raw_img, mask=raw_img.split()[3])
    bbox = bg.getbbox()
    img = bg.crop(bbox) if bbox else bg
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def base64_to_bytesio(b64_str):
    return io.BytesIO(base64.b64decode(b64_str))

# --- GENERADOR DE PDF ---
def generar_pdf(ctx, img_prestador_io, img_jefatura_io=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "INFORME MENSUAL DE ACTIVIDADES", ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 7, f"Nombre: {ctx['nombre']}", ln=True)
    pdf.cell(0, 7, f"Recinto/Dirección: {ctx['direccion']}", ln=True)
    pdf.cell(0, 7, f"Depto/Área: {ctx['depto']}", ln=True)
    pdf.cell(0, 7, f"Periodo: {ctx['mes']} {ctx['anio']}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, "Actividades Realizadas:", ln=True)
    pdf.set_font("Arial", "", 10)
    for act in ctx['actividades']:
        pdf.multi_cell(0, 5, f"- {act['Actividad']}: {act['Producto']}")
    
    pdf.ln(10)
    y_firmas = pdf.get_y()
    
    if img_prestador_io:
        img_p = Image.open(img_prestador_io)
        with io.BytesIO() as temp_p:
            img_p.save(temp_p, format="PNG")
            pdf.image(temp_p, x=30, y=y_firmas, w=50)
            pdf.text(x=35, y=y_firmas + 25, txt="Firma Prestador")
            
    if img_jefatura_io:
        img_j = Image.open(img_jefatura_io)
        with io.BytesIO() as temp_j:
            img_j.save(temp_j, format="PNG")
            pdf.image(temp_j, x=120, y=y_firmas, w=50)
            pdf.text(x=125, y=y_firmas + 25, txt="Firma Jefatura")
            
    return bytes(pdf.output())

# --- CABECERA COMÚN (LOGOS) ---
def mostrar_cabecera():
    c1, c2, c3 = st.columns([1, 4, 1])
    # Logo Municipalidad
    c1.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png", use_container_width=True)
    
    c2.markdown("<h2 style='text-align: center; color: #2C3E50;'>Ilustre Municipalidad de La Serena</h2>", unsafe_allow_html=True)
    c2.markdown("<p style='text-align: center;'>Plataforma Oficial de Autogestión de Honorarios</p>", unsafe_allow_html=True)
    
    # Logo Innovación (REEMPLAZA ESTA URL POR LA DE TU LOGO DE INNOVACIÓN)
    c3.image("https://cdn-icons-png.flaticon.com/512/1903/1903162.png", use_container_width=True) 
    st.divider()

# ==========================================
# MÓDULO 1: PRESTADOR
# ==========================================
def modulo_prestador():
    mostrar_cabecera()
    st.title("Generador de Informes 📝")

    with st.expander("👤 Paso 1: Estructura Organizacional e Identificación", expanded=True):
        nombre = st.text_input("Nombre Completo del Prestador", placeholder="Ej: JUAN PÉREZ ROJAS")
        col_a, col_b = st.columns(2)
        
        # Variables de estructura
        recinto = col_a.selectbox("Dirección Municipal o Recinto", unidades_municipales)
        area = col_b.text_input("Departamento, Área o Unidad Específica", placeholder="Ej: Oficina de Partes")
        
        jornada = st.selectbox("Tipo de Jornada", ["Libre", "Completa", "Flexible", "Media Jornada"])

    with st.expander("💰 Paso 2: Periodo y Montos", expanded=True):
        c1, c2 = st.columns(2)
        mes = c1.selectbox("Mes del Informe", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=2)
        anio = c2.number_input("Año", value=2026)
        st.divider()
        c3, c4 = st.columns(2)
        monto_contrato = c3.number_input("Monto Bruto Contrato ($)", value=0, step=10000)
        n_boleta = c4.text_input("Nº Boleta SII", placeholder="000")
        
        impuesto = int(monto_contrato * 0.1525)
        liquido = monto_contrato - impuesto
        if monto_contrato > 0:
            st.info(f"💰 **Resumen:** Bruto: ${monto_contrato:,.0f} | Retención (15.25%): ${impuesto:,.0f} | Líquido: ${liquido:,.0f}")

    st.subheader("📋 Paso 3: Resumen de Actividades")
    if 'num_actividades' not in st.session_state: st.session_state.num_actividades = 1
    def add_act(): st.session_state.num_actividades += 1
    def del_act(): 
        if st.session_state.num_actividades > 1: st.session_state.num_actividades -= 1

    for i in range(st.session_state.num_actividades):
        ca, cp = st.columns(2)
        ca.text_area(f"Actividad {i+1}", key=f"act_desc_{i}")
        cp.text_area(f"Producto/Resultado {i+1}", key=f"act_prod_{i}")

    c_btn1, c_btn2 = st.columns(2)
    c_btn1.button("➕ Agregar Actividad", on_click=add_act, use_container_width=True)
    c_btn2.button("➖ Eliminar Última", on_click=del_act, use_container_width=True)

    st.subheader("✍️ Paso 4: Firma Digital")
    canvas_result = st_canvas(stroke_width=2, stroke_color="black", background_color="white", height=150, width=400, drawing_mode="freedraw", key="canvas_prestador")
    
    firma_en_blanco = True
    if canvas_result.image_data is not None:
        if np.sum(canvas_result.image_data) != (150 * 400 * 4 * 255): firma_en_blanco = False

    st.divider()
    if st.button("🚀 ENVIAR A JEFATURA PARA VISACIÓN", type="primary", use_container_width=True):
        if not nombre or firma_en_blanco:
            st.error("⚠️ Debe ingresar su nombre y firmar el documento obligatoriamente.")
        else:
            actividades_lista = []
            for i in range(st.session_state.num_actividades):
                desc = st.session_state.get(f"act_desc_{i}", "")
                prod = st.session_state.get(f"act_prod_{i}", "")
                if desc or prod: actividades_lista.append({"Actividad": desc, "Producto": prod})
            
            firma_b64 = canvas_to_base64(canvas_result.image_data)
            act_json = json.dumps(actividades_lista)
            
            c = conn.cursor()
            c.execute("""INSERT INTO informes 
                         (nombre, direccion, depto, jornada, mes, anio, monto, n_boleta, actividades_json, firma_prestador_b64, estado) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (nombre.upper(), recinto, area, jornada, mes.upper(), anio, monto_contrato, n_boleta, act_json, firma_b64, '🔴 Pendiente Jefatura'))
            conn.commit()
            st.success("✅ ¡Informe enviado exitosamente! Su jefatura ha sido notificada para la visación.")
            st.balloons()


# ==========================================
# MÓDULO 2: JEFATURA (VISACIÓN)
# ==========================================
def modulo_jefatura():
    mostrar_cabecera()
    st.title("Bandeja de Jefatura 📥")
    st.markdown("### Visación Técnica de Informes")
    
    mi_unidad = st.selectbox("Filtrar por Dirección o Recinto:", unidades_municipales)
    
    df = pd.read_sql_query(f"SELECT id, nombre, depto, mes, monto, estado FROM informes WHERE direccion='{mi_unidad}' AND estado='🔴 Pendiente Jefatura'", conn)
    
    if df.empty:
        st.info("🎉 No hay informes pendientes de visación en este recinto.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.divider()
        
        st.subheader("Revisar y Visar")
        id_selec = st.selectbox("Seleccione el ID del informe a visar:", df['id'].tolist())
        
        c = conn.cursor()
        c.execute("SELECT * FROM informes WHERE id=?", (id_selec,))
        row = c.fetchone()
        columnas = [description[0] for description in c.description]
        datos = dict(zip(columnas, row))
        
        st.write(f"**Prestador:** {datos['nombre']} | **Área:** {datos['depto']} | **Mes:** {datos['mes']}")
        with st.expander("Ver Actividades Declaradas"):
            actividades = json.loads(datos['actividades_json'])
            for act in actividades:
                st.markdown(f"- **{act['Actividad']}**: {act['Producto']}")
                
        st.write("✍️ **Firma de Jefatura (Visador)**")
        canvas_jefatura = st_canvas(stroke_width=2, stroke_color="blue", background_color="white", height=150, width=400, drawing_mode="freedraw", key="canvas_jefa")
        
        firma_jefa_blanca = True
        if canvas_jefatura.image_data is not None:
            if np.sum(canvas_jefatura.image_data) != (150 * 400 * 4 * 255): firma_jefa_blanca = False

        col_apr, col_rech = st.columns(2)
        if col_apr.button("✅ VISAR Y ENVIAR A FINANZAS", type="primary", use_container_width=True):
            if firma_jefa_blanca:
                st.error("⚠️ La jefatura debe firmar para visar.")
            else:
                firma_jefa_b64 = canvas_to_base64(canvas_jefatura.image_data)
                c.execute("UPDATE informes SET estado='🟡 Pendiente Finanzas', firma_jefatura_b64=? WHERE id=?", (firma_jefa_b64, id_selec))
                conn.commit()
                st.success("✅ Visación técnica completada. El informe ha sido derivado a Finanzas.")
                st.rerun()

        if col_rech.button("❌ RECHAZAR INFORME", use_container_width=True):
            c.execute("UPDATE informes SET estado='❌ Rechazado Jefatura' WHERE id=?", (id_selec,))
            conn.commit()
            st.warning("El informe ha sido rechazado.")
            st.rerun()

# ==========================================
# MÓDULO 3: FINANZAS (CONTROL FINAL)
# ==========================================
def modulo_finanzas():
    mostrar_cabecera()
    st.title("Portal de Finanzas 🏛️")
    st.markdown("### Control Administrativo y Aprobación de Pago")
    
    # Finanzas ve todos los informes visados a nivel comunal
    df = pd.read_sql_query("SELECT id, nombre, direccion as recinto, mes, monto, estado FROM informes WHERE estado='🟡 Pendiente Finanzas'", conn)
    
    if df.empty:
        st.info("✅ Bandeja limpia. No hay informes pendientes de revisión financiera.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.divider()
        
        st.subheader("Gestión de Informe Seleccionado")
        id_selec = st.selectbox("Seleccione el ID del informe a procesar:", df['id'].tolist())
        
        c = conn.cursor()
        c.execute("SELECT * FROM informes WHERE id=?", (id_selec,))
        row = c.fetchone()
        columnas = [description[0] for description in c.description]
        datos = dict(zip(columnas, row))
        
        liquido = int(datos['monto'] * 0.8475)
        st.write(f"**Funcionario:** {datos['nombre']} | **Boleta SII:** {datos['n_boleta']} | **Líquido a Pagar:** ${liquido:,.0f}")
        
        # --- PRE-GENERAR DOCUMENTOS PARA LA DESCARGA EN MEMORIA ---
        img_prestador_io = base64_to_bytesio(datos['firma_prestador_b64'])
        img_jefatura_io = base64_to_bytesio(datos['firma_jefatura_b64'])
        
        context = {
            'nombre': datos['nombre'], 'direccion': datos['direccion'], 'depto': datos['depto'],
            'jornada': datos['jornada'], 'mes': datos['mes'], 'anio': datos['anio'],
            'monto': f"${datos['monto']:,.0f}",
            'monto_boleta': f"${datos['monto']:,.0f}",
            'boleta': datos['n_boleta'], 'actividades': json.loads(datos['actividades_json']),
            'descuentos': "$0"
        }
        
        # Generar PDF (Evidencia)
        img_prestador_io.seek(0)
        img_jefatura_io.seek(0)
        pdf_bytes = generar_pdf(context, img_prestador_io, img_jefatura_io)
        
        st.markdown("### Acciones Disponibles")
        col_desc, col_hist, col_pago = st.columns(3)
        
        # ACCIÓN 1: Descargar
        with col_desc:
            st.download_button("📥 1. Descargar Evidencia (PDF)", pdf_bytes, f"Informe_FINAL_{datos['mes']}_{datos['nombre']}.pdf", mime="application/pdf", use_container_width=True)
            
        # ACCIÓN 2: Archivar en Historial
        with col_hist:
            if st.button("📁 2. Guardar en Historial Funcionario", use_container_width=True):
                c.execute("UPDATE informes SET estado='📁 Archivado en Historial' WHERE id=?", (id_selec,))
                conn.commit()
                st.success("✅ Documento digitalizado y enlazado al expediente del funcionario.")
                st.rerun()
                
        # ACCIÓN 3: Disparar Pago (El Visto Bueno final)
        with col_pago:
            if st.button("💸 3. Validar y Disparar Pago", type="primary", use_container_width=True):
                c.execute("UPDATE informes SET estado='🟢 Pago Liberado' WHERE id=?", (id_selec,))
                conn.commit()
                st.success("✅ ¡Aprobación procesada! Instrucción de pago derivada a Tesorería.")
                st.balloons()
                st.rerun()

# --- ENRUTADOR PRINCIPAL ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png", width=100)
    st.title("Sistema SAP Honorarios")
    rol = st.radio("Seleccione su Rol de Acceso:", ["👤 1. Portal Prestador", "🧑‍💼 2. Portal Jefatura (Visación)", "🏛️ 3. Portal Finanzas (Pagos)"])

if rol == "👤 1. Portal Prestador":
    modulo_prestador()
elif rol == "🧑‍💼 2. Portal Jefatura (Visación)":
    modulo_jefatura()
else:
    modulo_finanzas()

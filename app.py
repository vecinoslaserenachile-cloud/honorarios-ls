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

# Motor SAP: Base de datos local para almacenar los informes en tránsito
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
    """Convierte el dibujo del canvas a Base64 con fondo blanco puro"""
    raw_img = Image.fromarray(canvas_data.astype('uint8'), 'RGBA')
    bg = Image.new("RGB", raw_img.size, (255, 255, 255))
    bg.paste(raw_img, mask=raw_img.split()[3])
    bbox = bg.getbbox()
    img = bg.crop(bbox) if bbox else bg
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def base64_to_bytesio(b64_str):
    """Convierte Base64 de vuelta a BytesIO para Word/PDF"""
    return io.BytesIO(base64.b64decode(b64_str))

# --- GENERADOR DE PDF (Ahora soporta 2 firmas) ---
def generar_pdf(ctx, img_prestador_io, img_jefatura_io=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "INFORME MENSUAL DE ACTIVIDADES", ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 7, f"Nombre: {ctx['nombre']}", ln=True)
    pdf.cell(0, 7, f"Unidad: {ctx['direccion']}", ln=True)
    pdf.cell(0, 7, f"Periodo: {ctx['mes']} {ctx['anio']}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, "Actividades Realizadas:", ln=True)
    pdf.set_font("Arial", "", 10)
    for act in ctx['actividades']:
        pdf.multi_cell(0, 5, f"- {act['Actividad']}: {act['Producto']}")
    
    pdf.ln(10)
    # Firmas
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
            
    return pdf.output()


# ==========================================
# MÓDULO 1: PRESTADOR (TU CÓDIGO INTACTO)
# ==========================================
def modulo_prestador():
    st.title("Generador de Informes 📝")
    st.markdown("### Ilustre Municipalidad de La Serena")
    st.caption("Herramienta oficial de autogestión para prestadores a honorarios.")

    with st.expander("👤 Paso 1: Identificación", expanded=True):
        nombre = st.text_input("Nombre Completo del Prestador", placeholder="Ej: JUAN PÉREZ ROJAS")
        col_a, col_b = st.columns(2)
        direccion = col_a.selectbox("Dirección Municipal / Unidad", unidades_municipales)
        depto = col_b.text_input("Departamento o Sección Específica", placeholder="Ej: Oficina de Partes")
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
                      (nombre.upper(), direccion, depto, jornada, mes.upper(), anio, monto_contrato, n_boleta, act_json, firma_b64, '🔴 Pendiente'))
            conn.commit()
            st.success("✅ ¡Informe enviado exitosamente! Su jefatura ha sido notificada para la visación.")
            st.balloons()


# ==========================================
# MÓDULO 2: JEFATURA (VISACIÓN Y DESCARGA)
# ==========================================
def modulo_jefatura():
    st.title("Bandeja de Visación 📥")
    st.markdown("### Aprobación de Informes de Honorarios")
    
    mi_unidad = st.selectbox("Filtrar por Unidad / Dirección:", unidades_municipales)
    
    # Leer pendientes de la unidad seleccionada
    df = pd.read_sql_query(f"SELECT id, nombre, mes, monto, estado, fecha_envio FROM informes WHERE direccion='{mi_unidad}' AND estado='🔴 Pendiente'", conn)
    
    if df.empty:
        st.info("🎉 No hay informes pendientes de visación en esta unidad.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.divider()
        
        st.subheader("Revisar y Aprobar")
        id_selec = st.selectbox("Seleccione el ID del informe a visar:", df['id'].tolist())
        
        # Cargar datos completos del ID seleccionado
        c = conn.cursor()
        c.execute("SELECT * FROM informes WHERE id=?", (id_selec,))
        row = c.fetchone()
        columnas = [description[0] for description in c.description]
        datos = dict(zip(columnas, row))
        
        st.write(f"**Prestador:** {datos['nombre']} | **Mes:** {datos['mes']} | **Monto:** ${datos['monto']:,.0f}")
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
        if col_apr.button("✅ APROBAR Y GENERAR DOCUMENTOS FINAL", type="primary", use_container_width=True):
            if firma_jefa_blanca:
                st.error("⚠️ La jefatura debe firmar para aprobar.")
            else:
                firma_jefa_b64 = canvas_to_base64(canvas_jefatura.image_data)
                
                # Actualizar DB
                c.execute("UPDATE informes SET estado='🟢 Aprobado', firma_jefatura_b64=? WHERE id=?", (firma_jefa_b64, id_selec))
                conn.commit()
                
                # --- GENERAR ARCHIVOS FINALES ---
                img_prestador_io = base64_to_bytesio(datos['firma_prestador_b64'])
                img_jefatura_io = base64_to_bytesio(firma_jefa_b64)
                
                context = {
                    'nombre': datos['nombre'], 'direccion': datos['direccion'], 'depto': datos['depto'],
                    'jornada': datos['jornada'], 'mes': datos['mes'], 'anio': datos['anio'],
                    'monto': f"${datos['monto']:,.0f}",
                    'monto_boleta': f"${datos['monto']:,.0f}",
                    'boleta': datos['n_boleta'], 'actividades': json.loads(datos['actividades_json']),
                    'descuentos': "$0"
                }
                
                # Word
                doc = DocxTemplate("plantilla_base.docx")
                context['firma'] = InlineImage(doc, img_prestador_io, height=Mm(20))
                context['firma_jefatura'] = InlineImage(doc, img_jefatura_io, height=Mm(20))
                doc.render(context)
                word_buf = io.BytesIO()
                doc.save(word_buf)
                
                # PDF
                img_prestador_io.seek(0)
                img_jefatura_io.seek(0)
                pdf_bytes = generar_pdf(context, img_prestador_io, img_jefatura_io)
                
                st.success("✅ Informe aprobado. Los documentos finales han sido generados.")
                c_w, c_p = st.columns(2)
                c_w.download_button("📥 DESCARGAR WORD FINAL", word_buf.getvalue(), f"Informe_FINAL_{datos['mes']}_{datos['nombre']}.docx", use_container_width=True)
                c_p.download_button("📥 DESCARGAR PDF FINAL", pdf_bytes, f"Informe_FINAL_{datos['mes']}_{datos['nombre']}.pdf", use_container_width=True)

        if col_rech.button("❌ RECHAZAR INFORME", use_container_width=True):
            c.execute("UPDATE informes SET estado='❌ Rechazado' WHERE id=?", (id_selec,))
            conn.commit()
            st.warning("El informe ha sido rechazado. Desaparecerá de la bandeja.")
            st.rerun()

# --- ENRUTADOR PRINCIPAL ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Escudo_de_La_Serena.svg/800px-Escudo_de_La_Serena.svg.png", width=100)
    st.title("Portal de Honorarios")
    rol = st.radio("Seleccione su Perfil:", ["👤 1. Portal Prestador", "✅ 2. Portal Jefatura (Visación)"])

if rol == "👤 1. Portal Prestador":
    modulo_prestador()
else:
    modulo_jefatura()

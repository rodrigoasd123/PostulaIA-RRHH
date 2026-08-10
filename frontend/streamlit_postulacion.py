from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

import streamlit as st

# Cargar variables de entorno desde .env
load_dotenv()

# Agregar directorio raíz al sys.path para importar backend correctamente
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend import ApplicationAgent, QueryHistory, Evidence, PdfReadError, read_pdf
from backend.retrieval import normalize

st.set_page_config(
    page_title="PostulaIA - Asistente de Convocatorias Laborales",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS Avanzados - Modern Tech Clean Light Design System
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    :root {
        --primary: #2563eb;
        --primary-dark: #1d4ed8;
        --secondary: #0f172a;
        --bg-main: #f8fafc;
        --card-bg: #ffffff;
        --text-heading: #0f172a;
        --text-body: #334155;
        --text-muted: #64748b;
        --border-color: #e2e8f0;
        --accent-green: #059669;
        --accent-amber: #d97706;
        --accent-rose: #e11d48;
    }

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: var(--text-body);
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        letter-spacing: -0.025em;
        color: var(--text-heading) !important;
    }

    .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    }

    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: #0f172a;
        border-right: 1px solid #1e293b;
    }

    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }

    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
        color: #94a3b8 !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: #334155;
        margin: 1.2rem 0;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        background: #1e293b;
        border: 2px dashed #3b82f6;
        border-radius: 16px;
        padding: 1.2rem 1rem;
        transition: all 0.2s ease;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]:hover {
        background: #273549;
        border-color: #60a5fa;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
        background: #2563eb !important;
        color: #ffffff !important;
        border: 0;
        border-radius: 10px;
        font-weight: 700;
        padding: 0.5rem 1rem;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
    }

    /* Branding Header */
    .brand-container {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 6px 0 28px;
    }

    .brand-icon {
        width: 44px;
        height: 44px;
        border-radius: 14px;
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
        display: grid;
        place-items: center;
        font-size: 22px;
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.35);
        color: #ffffff !important;
    }

    .brand-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 22px;
        letter-spacing: -0.03em;
        color: #ffffff !important;
    }

    .brand-title span {
        color: #60a5fa !important;
    }

    .side-section-title {
        color: #94a3b8 !important;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 11px;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .prompt-chip {
        border: 1px solid #334155;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 10px 14px;
        margin: 8px 0;
        color: #e2e8f0 !important;
        font-size: 13px;
        line-height: 1.4;
        transition: all 0.2s ease;
    }

    .prompt-chip:hover {
        background: rgba(37, 99, 235, 0.15);
        border-color: #3b82f6;
    }

    /* Status Badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(5, 150, 105, 0.15);
        border: 1px solid rgba(5, 150, 105, 0.3);
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 700;
        color: #34d399 !important;
        margin-top: 6px;
    }

    /* Hero Banner */
    .hero-card {
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #1e3a8a 100%);
        border-radius: 24px;
        padding: 48px 52px;
        color: white !important;
        box-shadow: 0 20px 45px rgba(15, 23, 42, 0.12);
        margin-bottom: 24px;
    }

    .hero-card * {
        color: white !important;
    }

    .hero-tag {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        padding: 6px 16px;
        color: #93c5fd !important;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 18px;
    }

    .hero-card h1 {
        color: white !important;
        font-size: 44px !important;
        line-height: 1.1;
        margin: 0 0 16px !important;
        font-weight: 800 !important;
        max-width: 760px;
    }

    .hero-card p {
        color: #cbd5e1 !important;
        font-size: 17px;
        line-height: 1.6;
        max-width: 700px;
        margin: 0;
    }

    .hero-features {
        display: flex;
        gap: 24px;
        flex-wrap: wrap;
        margin-top: 28px;
        color: #e2e8f0 !important;
        font-size: 14px;
        font-weight: 600;
    }

    .hero-features span:before {
        content: '✦';
        color: #60a5fa;
        margin-right: 8px;
    }

    /* Cards & Grids */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
        margin: 20px 0 30px;
    }

    .feature-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .feature-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
    }

    .feature-icon-wrapper {
        width: 48px;
        height: 48px;
        border-radius: 14px;
        background: #eff6ff;
        display: grid;
        place-items: center;
        font-size: 22px;
        margin-bottom: 18px;
        color: #2563eb !important;
    }

    .feature-card h3 {
        font-size: 18px;
        margin: 0 0 8px;
        color: #0f172a !important;
    }

    .feature-card p {
        color: #64748b !important;
        font-size: 14px;
        line-height: 1.5;
        margin: 0;
    }

    .privacy-banner {
        display: flex;
        gap: 14px;
        align-items: center;
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 16px;
        padding: 16px 20px;
        color: #166534 !important;
        font-size: 14px;
        margin: 20px 0;
    }

    .privacy-banner strong {
        color: #14532d !important;
    }

    /* KPI Metrics High Contrast */
    [data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 20px !important;
        padding: 20px 22px !important;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04) !important;
        transition: transform 0.2s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
    }

    [data-testid="stMetricLabel"] p, [data-testid="stMetricLabel"] span {
        color: #64748b !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    [data-testid="stMetricValue"] div, [data-testid="stMetricValue"] span {
        color: #0f172a !important;
        font-size: 34px !important;
        font-weight: 800 !important;
        font-family: 'Outfit', sans-serif !important;
    }

    /* Styled Tabs */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 4px;
    }

    [data-testid="stTabs"] button p {
        font-weight: 700 !important;
        font-size: 15px !important;
        color: #64748b !important;
    }

    [data-testid="stTabs"] button[aria-selected="true"] p {
        color: #2563eb !important;
        font-weight: 800 !important;
    }

    /* Chat Messages */
    [data-testid="stChatMessage"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 16px 20px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03);
        margin-bottom: 12px;
    }

    @media(max-width: 800px) {
        .hero-card { padding: 36px 28px; }
        .hero-card h1 { font-size: 34px !important; }
        .feature-grid { grid-template-columns: 1fr; }
        .block-container { padding-top: 1rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_items(title: str, icon: str, items: list[Evidence], empty: str) -> None:
    st.markdown(f"### {icon} {title}")
    if not items:
        st.caption(empty)
        return
    seen_texts = set()
    for item in items:
        norm_key = normalize(item.text)
        if norm_key in seen_texts:
            continue
        seen_texts.add(norm_key)
        with st.container(border=True):
            st.markdown(item.text)
            st.caption(f"📍 Fuente: página {item.page}")


@st.cache_resource(show_spinner=False)
def history() -> QueryHistory:
    return QueryHistory()


# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown(
        '<div class="brand-container"><div class="brand-icon">✨</div><div class="brand-title">Postula<span>IA</span></div></div>',
        unsafe_allow_html=True
    )
    
    st.markdown('<div class="side-section-title">Documento a Analizar</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Carga una convocatoria en PDF", type=["pdf"], label_visibility="collapsed")
    
    use_ollama = st.toggle("Modo Offline (Ollama Local)", value=False)
    
    # Estado del agente inteligente
    if not use_ollama:
        st.markdown('<div class="status-badge">🟢 Agente Inteligente Listo</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge" style="color:#60a5fa!important;border-color:#3b82f6;">🦙 Modo Local Activo</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="side-section-title">Consultas Frecuentes</div>', unsafe_allow_html=True)
    for suggestion in (
        "¿Cuáles son los requisitos obligatorios?",
        "¿Cuál es la fecha límite de postulación?",
        "¿Qué condiciones contractuales contempla?",
        "¿Cuáles son los motivos de descalificación?",
    ):
        st.markdown(f'<div class="prompt-chip">💬 {suggestion}</div>', unsafe_allow_html=True)
    
    st.divider()
    st.caption("🔒 El documento se procesa en memoria local con máxima privacidad.")


# --- VISTA PRINCIPAL SIN ARCHIVO CARGADO ---
if not uploaded:
    st.markdown(
        """
        <section class="hero-card">
          <div class="hero-tag">✨ Asistente de Convocatorias Laborales</div>
          <h1>Analiza y entiende cualquier convocatoria antes de postular.</h1>
          <p>Extrae instantáneamente requisitos clave, plazos críticos, salarios y condiciones contractuales sin leer decenas de páginas de bases.</p>
          <div class="hero-features">
            <span>RAG Semántico Avanzado</span>
            <span>Extracción de Tablas pdfplumber</span>
            <span>Evidencia citada por página</span>
          </div>
        </section>

        <div style="margin: 32px 0 16px;">
          <h2>Todo lo importante en un solo lugar</h2>
          <p style="color: #64748b; margin-top: 4px;">Optimiza tu tiempo de postulación y reduce errores de expediente.</p>
        </div>

        <div class="feature-grid">
          <div class="feature-card">
            <div class="feature-icon-wrapper">🎯</div>
            <h3>Resumen Accionable</h3>
            <p>Identifica los aspectos clave del puesto, funciones principales y experiencia requerida.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon-wrapper">⚖️</div>
            <h3>Requisitos y Alertas</h3>
            <p>Clasifica plazos límite, sueldos, exclusiones y cláusulas que requieren tu atención.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon-wrapper">💬</div>
            <h3>Preguntas con Evidencia</h3>
            <p>Consulta cualquier duda en lenguaje natural y obtén respuestas respaldadas por el número de página exacto.</p>
          </div>
        </div>

        <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 18px; padding: 22px 28px; display: flex; align-items: center; justify-content: space-between; gap: 20px;">
          <div>
            <strong style="color: #1e40af; font-size: 16px; display: block; margin-bottom: 4px;">¿Listo para analizar una convocatoria?</strong>
            <span style="color: #3b82f6; font-size: 14px;">Utiliza la barra lateral para subir un documento PDF de postulación.</span>
          </div>
          <span style="background: #2563eb; color: white; padding: 8px 16px; border-radius: 10px; font-weight: 700; font-size: 13px;">PDF · Hasta 200 MB</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()


# --- PROCESAMIENTO DEL DOCUMENTO ---
data = uploaded.getvalue()
document_key = hashlib.sha256(data).hexdigest()

try:
    pages = read_pdf(data)
except PdfReadError as exc:
    st.error(str(exc))
    st.stop()

if st.session_state.get("document_key") != document_key:
    st.session_state.document_key = document_key
    st.session_state.messages = []

# Cargar API Key desde .env de forma transparente
gemini_key = os.getenv("GEMINI_API_KEY", "")
agent = ApplicationAgent(pages, use_ollama=use_ollama, gemini_api_key=gemini_key)
analysis = agent.analysis

# --- ENCABEZADO Y DASHBOARD DE MÉTRICAS ---
st.markdown('<div style="color:#2563eb; font-weight:700; font-size:13px; text-transform:uppercase; letter-spacing:0.1em;">✓ Documento Procesado Exitosamente</div>', unsafe_allow_html=True)
st.title(analysis.title)

st.markdown(
    '<div class="privacy-banner">🛡️ <div><strong>Análisis Privado y Verificado</strong><br>El documento ha sido analizado localmente. Las respuestas del agente citan siempre la evidencia del documento original.</div></div>',
    unsafe_allow_html=True
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Requisitos del Perfil", len(analysis.requirements))
m2.metric("Fechas y Plazos", len(analysis.dates))
m3.metric("Condiciones Laborales", len(analysis.conditions))
m4.metric("Alertas y Exclusiones", len(analysis.alerts) + len(analysis.exclusions))

# --- PESTAÑAS PRINCIPALES ---
overview_tab, chat_tab, evidence_tab = st.tabs(["📊 Resumen Ejecutivo", "💬 Pregúntale al Agente", "📄 Documento Fuente"])

with overview_tab:
    st.markdown("### 📋 Resumen del Documento")
    st.info(analysis.summary)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        render_items("Requisitos y Perfil", "✓", analysis.requirements, "No se detectaron requisitos explícitos.")
        render_items("Fechas Clave y Plazos", "◷", analysis.dates, "No se detectaron fechas o plazos de vigencia.")
    with c2:
        render_items("Condiciones Contractuales", "▣", analysis.conditions, "No se detectaron condiciones laborales específicas.")
        render_items("Alertas y Cláusulas Especiales", "⚠", analysis.alerts + analysis.exclusions, "No se detectaron alertas automáticas.")

with chat_tab:
    st.caption("Consulta cualquier duda en lenguaje natural. El agente responderá basándose únicamente en el contenido del PDF.")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    if question := st.chat_input("Ejemplo: ¿Cuál es la experiencia mínima solicitada?"):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Consultando evidencia en el documento..."):
                result = agent.ask(question)
            st.markdown(result.answer)
        st.session_state.messages.append({"role": "assistant", "content": result.answer})
        history().add(uploaded.name, question, result.answer)

with evidence_tab:
    st.markdown("### 📄 Texto y Tablas Extraídas por Página")
    st.caption("Inspecciona la extracción técnica realizada por pdfplumber página por página.")
    for page in pages:
        with st.expander(f"Página {page.page}"):
            st.text(page.text)

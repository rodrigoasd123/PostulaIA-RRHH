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

from backend import (
    ApplicationAgent,
    CandidateReview,
    Evidence,
    PdfReadError,
    build_review_context,
    extract_criteria,
    load_candidate_documents,
    read_pdf,
    screen_candidates,
)
from backend.retrieval import normalize

st.set_page_config(
    page_title="PostulaIA RR. HH. - Revisión de CV",
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


@st.cache_data(show_spinner=False)
def load_pdf(data: bytes, reading_mode: str):
    return read_pdf(data, mode=reading_mode)


configured_gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
MAX_PDF_BYTES = 20 * 1024 * 1024


def _unique_candidate_name(original: str, used: set[str]) -> str:
    if original not in used:
        return original
    path = Path(original)
    counter = 2
    while True:
        candidate = f"{path.stem} ({counter}){path.suffix}"
        if candidate not in used:
            return candidate
        counter += 1


def _render_review(review: CandidateReview) -> None:
    st.markdown(f"### {review.filename}")
    st.caption(
        f"Coincidencia documental: {review.score}/100. "
        "Este valor mide presencia de términos; no determina idoneidad ni una decisión laboral."
    )
    for match in review.matches:
        icon = "✅" if match.status == "Coincidencia alta" else "🟡" if match.status == "Coincidencia parcial" else "⚪"
        with st.expander(
            f"{icon} {match.criterion.identifier} · {match.status} · {int(match.coverage * 100)}%",
            expanded=match.status != "Coincidencia alta",
        ):
            st.markdown(f"**Requisito:** {match.criterion.text}")
            st.caption(f"Fuente del requisito: perfil del puesto, página {match.criterion.page}")
            terms = ", ".join(match.matched_terms) if match.matched_terms else "Ninguno"
            st.markdown(f"**Términos encontrados:** {terms}")
            if match.cv_evidence:
                st.markdown(f"**Evidencia del CV (página {match.cv_evidence.page}):**")
                st.write(match.cv_evidence.text)
            else:
                st.info("No se encontró un fragmento suficiente en el CV. Requiere revisión humana.")


# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown(
        '<div class="brand-container"><div class="brand-icon">👥</div><div class="brand-title">Postula<span>IA</span> RR.HH.</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="side-section-title">Documentos del proceso</div>', unsafe_allow_html=True)
    reading_method = st.radio(
        "Método de lectura",
        ("Normal", "OCR"),
        horizontal=True,
        help="Normal extrae texto digital. OCR reconoce el texto visible de PDFs escaneados.",
    )
    reading_mode = "ocr" if reading_method == "OCR" else "normal"
    st.caption("🔎 OCR local para escaneos; puede tardar más." if reading_mode == "ocr" else "⚡ Recomendado para PDFs con texto seleccionable.")

    job_profile = st.file_uploader(
        "1. Perfil del puesto o convocatoria",
        type=["pdf"],
        key="job_profile",
    )
    candidate_files = st.file_uploader(
        "2. CV de postulantes",
        type=["pdf"],
        accept_multiple_files=True,
        key="candidate_cvs",
        help="Puedes cargar hasta 20 CV por ejecución.",
    )

    st.markdown('<div class="side-section-title">Asistente opcional</div>', unsafe_allow_html=True)
    session_gemini_key = st.text_input(
        "API key gratuita de Gemini",
        type="password",
        placeholder="Opcional: clave de Google AI Studio",
        help="Se conserva solo durante esta sesión y no se escribe en archivos.",
    ).strip()
    gemini_key = session_gemini_key or configured_gemini_key
    use_ollama = st.toggle("Modo Offline (Ollama Local)", value=False)

    if use_ollama:
        st.markdown('<div class="status-badge" style="color:#60a5fa!important;border-color:#3b82f6;">🦙 Ollama activado</div>', unsafe_allow_html=True)
    elif gemini_key:
        st.markdown('<div class="status-badge">🟢 Gemini listo para consultas</div>', unsafe_allow_html=True)
        st.caption("El ranking no usa Gemini; siempre se calcula localmente.")
    else:
        st.markdown('<div class="status-badge">🟢 Comparador local listo</div>', unsafe_allow_html=True)
        st.caption("El ranking funciona sin API key.")

    st.divider()
    st.caption(
        "🔒 Los PDF, el OCR y el puntaje se procesan localmente y no se guardan. "
        "Si activas Gemini, solo se envían fragmentos recuperados al hacer una consulta."
    )


if not job_profile or not candidate_files:
    st.markdown(
        """
        <section class="hero-card">
          <div class="hero-tag">👥 Asistente de revisión para Recursos Humanos</div>
          <h1>Compara CV con requisitos verificables, sin delegar la decisión.</h1>
          <p>Carga el perfil del puesto y varios CV. PostulaIA identifica coincidencias documentales, muestra brechas y conserva la evidencia para que tu equipo realice la evaluación final.</p>
          <div class="hero-features">
            <span>Ranking determinista</span>
            <span>OCR local</span>
            <span>Evidencia por página</span>
            <span>Revisión humana obligatoria</span>
          </div>
        </section>

        <div class="feature-grid">
          <div class="feature-card">
            <div class="feature-icon-wrapper">1</div>
            <h3>Define el perfil</h3>
            <p>Sube una convocatoria o descripción de puesto con requisitos explícitos.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon-wrapper">2</div>
            <h3>Carga los CV</h3>
            <p>Procesa hasta veinte postulantes con lectura normal u OCR local.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon-wrapper">3</div>
            <h3>Revisa la evidencia</h3>
            <p>Prioriza la lectura y valida cada coincidencia antes de decidir.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if job_profile and not candidate_files:
        st.info("El perfil está listo. Agrega al menos un CV en la barra lateral.")
    elif candidate_files and not job_profile:
        st.info("Los CV están listos. Agrega el perfil del puesto en la barra lateral.")
    st.stop()

if len(candidate_files) > 20:
    st.error("Puedes analizar como máximo 20 CV por ejecución. Retira algunos archivos para continuar.")
    st.stop()

profile_data = job_profile.getvalue()
if len(profile_data) > MAX_PDF_BYTES:
    st.error("El perfil supera el límite de 20 MB. Reduce el archivo para continuar.")
    st.stop()
try:
    with st.spinner("Leyendo el perfil del puesto..."):
        profile_pages = load_pdf(profile_data, reading_mode)
except PdfReadError as exc:
    st.error(f"No se pudo leer el perfil del puesto: {exc}")
    st.stop()

extraction = extract_criteria(profile_pages)
if not extraction.criteria:
    st.warning(
        "No se detectaron requisitos explícitos utilizables en el perfil. "
        "Agrega requisitos de experiencia, formación, conocimientos o habilidades antes de comparar CV."
    )
    with st.expander("Revisar texto extraído del perfil"):
        for page in profile_pages:
            st.markdown(f"**Página {page.page}**")
            st.text(page.text)
    st.stop()

candidate_payloads: dict[str, bytes] = {}
used_names: set[str] = set()
bundle_hasher = hashlib.sha256(profile_data + reading_mode.encode("utf-8"))

with st.spinner(f"Procesando {len(candidate_files)} CV..."):
    for candidate_file in candidate_files:
        display_name = _unique_candidate_name(candidate_file.name, used_names)
        used_names.add(display_name)
        candidate_data = candidate_file.getvalue()
        bundle_hasher.update(display_name.encode("utf-8"))
        bundle_hasher.update(candidate_data)
        candidate_payloads[display_name] = candidate_data

    candidate_documents, candidate_errors = load_candidate_documents(
        candidate_payloads,
        reading_mode,
        max_bytes=MAX_PDF_BYTES,
        reader=lambda data, mode: load_pdf(data, mode),
    )

if not candidate_documents:
    st.error("Ningún CV pudo procesarse.")
    for filename, error in candidate_errors.items():
        st.error(f"{filename}: {error}")
    st.stop()

reviews = screen_candidates(candidate_documents, extraction)
review_by_name = {review.filename: review for review in reviews}
bundle_key = bundle_hasher.hexdigest()
if st.session_state.get("screening_bundle_key") != bundle_key:
    st.session_state.screening_bundle_key = bundle_key
    st.session_state.messages = []
    st.session_state.chat_context_key = None

profile_title = next(
    (line.strip() for line in profile_pages[0].text.splitlines() if line.strip()),
    "Proceso de selección",
)[:120]
processed_label = "OCR local" if reading_mode == "ocr" else "lectura normal"
st.markdown(
    f'<div style="color:#2563eb; font-weight:700; font-size:13px; text-transform:uppercase; letter-spacing:0.1em;">✓ {len(reviews)} CV procesados · {processed_label}</div>',
    unsafe_allow_html=True,
)
st.title(profile_title)
st.markdown(
    '<div class="privacy-banner">🛡️ <div><strong>Preselección asistida, decisión humana</strong><br>El puntaje solo mide coincidencia documental de términos. No valida experiencia, no infiere atributos personales y no aprueba ni rechaza candidatos.</div></div>',
    unsafe_allow_html=True,
)

if extraction.excluded_sensitive:
    st.warning(
        f"Se excluyeron {len(extraction.excluded_sensitive)} criterios sensibles del puntaje. "
        "Revísalos con el área legal o de cumplimiento."
    )
if candidate_errors:
    with st.expander(f"⚠️ {len(candidate_errors)} CV no pudieron procesarse"):
        for filename, error in candidate_errors.items():
            st.error(f"{filename}: {error}")

average_score = round(sum(review.score for review in reviews) / len(reviews))
m1, m2, m3, m4 = st.columns(4)
m1.metric("CV analizados", len(reviews))
m2.metric("Criterios usados", len(extraction.criteria))
m3.metric("Coincidencia promedio", f"{average_score}/100")
m4.metric("Revisión manual", "Obligatoria")

ranking_tab, detail_tab, chat_tab, source_tab = st.tabs(
    ["📊 Ranking orientativo", "🔎 Detalle por CV", "💬 Consulta al agente", "📄 Fuentes"]
)

with ranking_tab:
    st.markdown("### Priorización para revisión documental")
    st.caption("Ordenada por cobertura de términos; los empates se resuelven por nombre de archivo.")
    ranking_rows = []
    for position, review in enumerate(reviews, 1):
        high = sum(match.status == "Coincidencia alta" for match in review.matches)
        partial = sum(match.status == "Coincidencia parcial" for match in review.matches)
        missing = sum(match.status == "Sin evidencia suficiente" for match in review.matches)
        ranking_rows.append(
            {
                "Orden de revisión": position,
                "CV": review.filename,
                "Puntaje documental": review.score,
                "Altas": high,
                "Parciales": partial,
                "Sin evidencia": missing,
            }
        )
    st.dataframe(
        ranking_rows,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Puntaje documental": st.column_config.ProgressColumn(
                "Puntaje documental", min_value=0, max_value=100, format="%d"
            )
        },
    )
    with st.expander("¿Cómo se calcula?"):
        st.write(
            "Para cada requisito se calcula qué proporción de sus términos aparece en el CV. "
            "El puntaje es el promedio de esas coberturas, multiplicado por 100. "
            "No se usan Gemini, Ollama ni datos sensibles para ordenar."
        )

selected_name = st.selectbox(
    "Selecciona un CV para revisar",
    [review.filename for review in reviews],
    key="selected_candidate",
)
selected_review = review_by_name[selected_name]
selected_pages = candidate_documents[selected_name]

with detail_tab:
    _render_review(selected_review)
    if extraction.excluded_sensitive:
        with st.expander("Criterios sensibles excluidos"):
            for item in extraction.excluded_sensitive:
                st.warning(f"Perfil, página {item.page}: {item.text}")

with chat_tab:
    st.caption(
        f"Pregunta únicamente sobre **{selected_name}** frente al perfil. "
        "El agente recupera evidencia del perfil y de este CV; el ranking no cambia."
    )
    chat_context_key = f"{bundle_key}:{selected_name}"
    if st.session_state.get("chat_context_key") != chat_context_key:
        st.session_state.chat_context_key = chat_context_key
        st.session_state.messages = []

    question = st.chat_input("Ejemplo: ¿Qué experiencia del CV respalda el requisito de Python?")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        review_context = build_review_context(profile_pages, selected_pages)
        agent = ApplicationAgent(
            review_context,
            use_ollama=use_ollama,
            gemini_api_key=gemini_key,
            use_remote_embeddings=False,
        )
        with st.spinner("Consultando evidencia del perfil y del CV..."):
            result = agent.ask(question)
        st.session_state.messages.append({"role": "assistant", "content": result.answer})

    with st.container(height=520, autoscroll=True):
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

with source_tab:
    st.markdown("### Perfil del puesto")
    for page in profile_pages:
        with st.expander(f"Perfil · página {page.page}"):
            st.text(page.text)
    st.markdown(f"### CV seleccionado: {selected_name}")
    for page in selected_pages:
        with st.expander(f"CV · página {page.page}"):
            st.text(page.text)

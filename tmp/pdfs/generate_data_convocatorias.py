"""Genera 3 PDFs de convocatorias laborales peruanas de ejemplo en data/.

Reutiliza el patrón visual de generate_sample_convocatoria.py (mismo
esquema de estilos, encabezado/pie y estructura de secciones), pero
parametrizado para producir varios rubros: TI, administrativo y salud.
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

font_regular = "Helvetica"
font_bold = "Helvetica-Bold"
font_dir = Path("C:/Windows/Fonts")
if (font_dir / "arial.ttf").exists():
    pdfmetrics.registerFont(TTFont("Arial", str(font_dir / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("ArialBold", str(font_dir / "arialbd.ttf")))
    font_regular, font_bold = "Arial", "ArialBold"

NAVY = colors.HexColor("#13233F")
BLUE = colors.HexColor("#1769E0")
PALE = colors.HexColor("#EDF4FF")
INK = colors.HexColor("#172033")
MUTED = colors.HexColor("#5C667A")
RED = colors.HexColor("#B42318")
RED_PALE = colors.HexColor("#FFF0ED")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Kicker", fontName=font_bold, fontSize=9, leading=12, textColor=BLUE, spaceAfter=5))
styles.add(ParagraphStyle(name="Hero", fontName=font_bold, fontSize=24, leading=28, textColor=NAVY, spaceAfter=8))
styles.add(ParagraphStyle(name="Subtitle", fontName=font_regular, fontSize=11, leading=16, textColor=MUTED, spaceAfter=14))
styles.add(ParagraphStyle(name="Section", fontName=font_bold, fontSize=14, leading=18, textColor=NAVY, spaceBefore=8, spaceAfter=7))
styles.add(ParagraphStyle(name="BodyX", fontName=font_regular, fontSize=9.4, leading=14, textColor=INK, spaceAfter=6))
styles.add(ParagraphStyle(name="BulletX", fontName=font_regular, fontSize=9.2, leading=13.5, leftIndent=12, firstLineIndent=-8, textColor=INK, spaceAfter=4))
styles.add(ParagraphStyle(name="Small", fontName=font_regular, fontSize=8, leading=11, textColor=MUTED))
styles.add(ParagraphStyle(name="Alert", fontName=font_regular, fontSize=9, leading=13, textColor=RED))
styles.add(ParagraphStyle(name="Center", fontName=font_bold, fontSize=10, leading=13, textColor=colors.white, alignment=TA_CENTER))


def p(text, style="BodyX"):
    return Paragraph(text, styles[style])


def bullet(text):
    return p(f"• {text}", "BulletX")


def make_header_footer(entity_label):
    def header_footer(canvas, doc):
        canvas.saveState()
        width, height = A4
        canvas.setFillColor(NAVY)
        canvas.rect(0, height - 13 * mm, width, 13 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont(font_bold, 8)
        canvas.drawString(18 * mm, height - 8 * mm, entity_label)
        canvas.setFillColor(MUTED)
        canvas.setFont(font_regular, 7.5)
        canvas.drawString(18 * mm, 11 * mm, "Documento creado exclusivamente para demostración. No representa una oferta laboral real.")
        canvas.drawRightString(width - 18 * mm, 11 * mm, f"Página {doc.page}")
        canvas.restoreState()

    return header_footer


def build_convocatoria(cfg):
    output = DATA_DIR / cfg["filename"]
    doc = BaseDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=22 * mm,
        bottomMargin=19 * mm,
        title=cfg["doc_title"],
        author="PostulaIA Demo",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates(PageTemplate(id="default", frames=[frame], onPageEnd=make_header_footer(cfg["entity_label"])))

    story = [
        p(cfg["process_code"], "Kicker"),
        p(cfg["title"], "Hero"),
        p(cfg["subtitle"], "Subtitle"),
        Table(
            [[p("POSTULACIÓN", "Center"), p("CIERRE", "Center"), p("VACANTES", "Center")],
             [p(cfg["postulacion_rango"], "Small"), p(cfg["cierre"], "Small"), p(cfg["vacantes"], "Small")]],
            colWidths=[doc.width / 3] * 3,
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BLUE),
                ("BACKGROUND", (0, 1), (-1, 1), PALE),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BCD2F5")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BCD2F5")),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ])),
        Spacer(1, 8),
        p("1. Objetivo del puesto", "Section"),
        p(cfg["objetivo"]),
        p("2. Requisitos obligatorios", "Section"),
        *[bullet(item) for item in cfg["requisitos_obligatorios"]],
        p("3. Requisitos deseables", "Section"),
        *[bullet(item) for item in cfg["requisitos_deseables"]],
        p("4. Funciones principales", "Section"),
        *[bullet(item) for item in cfg["funciones"]],
        p("5. Condiciones laborales", "Section"),
        Table(
            [[p(k, "Small"), p(v, "Small")] for k, v in cfg["condiciones"]],
            colWidths=[43 * mm, doc.width - 43 * mm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), PALE),
                ("FONTNAME", (0, 0), (0, -1), font_bold),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCD5E3")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])),
        Spacer(1, 8),
        p("6. Documentos para postular", "Section"),
        *[bullet(item) for item in cfg["documentos"]],
        p("7. Cronograma del proceso", "Section"),
        Table(
            [[p("Etapa", "Center"), p("Fecha", "Center")]] +
            [[p(etapa, "Small"), p(fecha, "Small")] for etapa, fecha in cfg["cronograma"]],
            colWidths=[doc.width * 0.56, doc.width * 0.44],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCD5E3")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])),
        Spacer(1, 8),
        p("8. Exclusiones y condiciones que requieren atención", "Section"),
        Table(
            [[p("ALERTA DE LECTURA", "Center")]] + [[p(item, "Alert")] for item in cfg["exclusiones"]],
            colWidths=[doc.width],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), RED),
                ("BACKGROUND", (0, 1), (0, -1), RED_PALE),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#FDA29B")),
                ("INNERGRID", (0, 1), (-1, -1), 0.3, colors.HexColor("#FDA29B")),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ])),
        Spacer(1, 8),
        p("9. Canal de postulación", "Section"),
        p(cfg["canal"]),
        p("Importante: esta convocatoria, la organización y todos sus datos son ficticios. El archivo fue preparado para validar las funciones de PostulaIA.", "Small"),
    ]

    doc.build(story)
    print(output)


CONVOCATORIAS = [
    {
        "filename": "convocatoria_ti_desarrollador_backend.pdf",
        "doc_title": "Convocatoria ficticia - Desarrollador Backend Python",
        "entity_label": "NEXOTECH SOLUTIONS - CONVOCATORIA FICTICIA",
        "process_code": "PROCESO 2026-TI-031",
        "title": "Convocatoria: Desarrollador(a) Backend Python",
        "subtitle": "Área de Tecnología e Ingeniería de Software | Lima, Perú | Modalidad remota",
        "postulacion_rango": "Del 12 al 28 de agosto de 2026",
        "cierre": "28/08/2026 - 23:59",
        "vacantes": "3 posiciones",
        "objetivo": (
            "Diseñar, desarrollar y mantener servicios backend para las plataformas digitales de la "
            "empresa, garantizando calidad, seguridad y escalabilidad del código en entornos productivos."
        ),
        "requisitos_obligatorios": [
            "Bachiller o titulado en Ingeniería de Sistemas, Computación, Informática o carreras afines.",
            "Experiencia mínima de 2 años desarrollando APIs con Python (Django o FastAPI).",
            "Conocimiento sólido de bases de datos relacionales (PostgreSQL o MySQL) y modelado de datos.",
            "Manejo de control de versiones con Git y flujos de trabajo colaborativos (GitFlow, PRs, code review).",
            "Nivel de inglés técnico intermedio para lectura de documentación.",
        ],
        "requisitos_deseables": [
            "Experiencia con contenedores (Docker) y despliegue en la nube (AWS o GCP).",
            "Conocimiento de pruebas automatizadas (pytest) e integración continua.",
            "Familiaridad con arquitecturas de microservicios y mensajería asíncrona.",
        ],
        "funciones": [
            "Construir y mantener endpoints de API siguiendo estándares de seguridad.",
            "Optimizar consultas y estructuras de base de datos para mejorar el rendimiento.",
            "Participar en revisiones de código y en la documentación técnica del sistema.",
            "Colaborar con el equipo de producto para priorizar y estimar historias técnicas.",
        ],
        "condiciones": [
            ("Tipo de contrato", "Contrato a plazo fijo por 6 meses, renovable según desempeño y necesidad del área."),
            ("Remuneración", "S/ 4,500 brutos mensuales."),
            ("Horario", "Lunes a viernes, de 09:00 a 18:00, con una hora de refrigerio."),
            ("Modalidad", "100% remota, con reuniones de coordinación sincrónicas en horario de Lima."),
            ("Inicio estimado", "28 de septiembre de 2026."),
        ],
        "documentos": [
            "Currículum vitae de máximo tres páginas, sin documentos sustentatorios en esta etapa.",
            "Declaración jurada de veracidad firmada, según el formato incluido en el portal de postulación.",
            "Enlace a repositorio de código (GitHub o GitLab) con proyectos representativos.",
        ],
        "cronograma": [
            ("Recepción de postulaciones", "12/08/2026 al 28/08/2026 hasta las 23:59"),
            ("Publicación de aptos", "01/09/2026"),
            ("Evaluación técnica (prueba de código)", "04/09/2026 de 15:00 a 17:00"),
            ("Entrevistas técnicas", "09/09/2026 y 10/09/2026"),
            ("Resultado final", "14/09/2026"),
        ],
        "exclusiones": [
            "La postulación será descalificada si se presenta después de las 23:59 del 28/08/2026 o si falta la declaración jurada firmada. No se aceptarán subsanaciones posteriores al cierre.",
            "La prueba técnica de código es individual y con tiempo límite estricto; el uso de terceros para resolverla elimina automáticamente a la persona del proceso.",
            "El contrato inicial es temporal y su renovación no está garantizada. La remuneración indicada es bruta y está sujeta a los descuentos de ley.",
        ],
        "canal": (
            "Enviar la postulación mediante el portal interno de demostración antes del cierre indicado. "
            "No se recibirán documentos por correo electrónico ni mensajería instantánea."
        ),
    },
    {
        "filename": "convocatoria_administrativo_asistente.pdf",
        "doc_title": "Convocatoria ficticia - Asistente Administrativo",
        "entity_label": "CORPORACION ANDINA DE SERVICIOS - CONVOCATORIA FICTICIA",
        "process_code": "PROCESO 2026-AD-058",
        "title": "Convocatoria: Asistente Administrativo(a)",
        "subtitle": "Área de Administración y Logística | Arequipa, Perú | Modalidad presencial",
        "postulacion_rango": "Del 15 al 29 de agosto de 2026",
        "cierre": "29/08/2026 - 17:00",
        "vacantes": "1 posición",
        "objetivo": (
            "Brindar soporte administrativo y documentario al área de operaciones, asegurando el correcto "
            "archivo, control de correspondencia y atención de requerimientos internos."
        ),
        "requisitos_obligatorios": [
            "Bachiller o titulado técnico en Administración, Secretariado Ejecutivo o carreras afines.",
            "Experiencia mínima de 1 año en labores administrativas o de asistencia de oficina.",
            "Manejo intermedio de Microsoft Office (Word, Excel y Outlook).",
            "Buena redacción y capacidad de organización de documentos físicos y digitales.",
            "Disponibilidad para trabajar de forma presencial en las oficinas de Arequipa.",
        ],
        "requisitos_deseables": [
            "Experiencia previa con sistemas de gestión documentaria (ERP o similares).",
            "Conocimientos básicos de atención al cliente y protocolo de oficina.",
        ],
        "funciones": [
            "Recibir, clasificar y archivar documentación administrativa.",
            "Elaborar reportes, cartas y comunicados internos según indicaciones del jefe de área.",
            "Coordinar agendas, reuniones y reserva de salas.",
            "Atender llamadas y consultas internas, derivándolas al área correspondiente.",
        ],
        "condiciones": [
            ("Tipo de contrato", "Contrato a plazo fijo por 3 meses, renovable según desempeño y necesidad del área."),
            ("Remuneración", "S/ 1,700 brutos mensuales."),
            ("Horario", "Lunes a viernes, de 08:30 a 17:30, con una hora de refrigerio."),
            ("Modalidad", "Presencial, en oficinas administrativas de Arequipa."),
            ("Inicio estimado", "15 de septiembre de 2026."),
        ],
        "documentos": [
            "Currículum vitae de máximo dos páginas, sin documentos sustentatorios en esta etapa.",
            "Declaración jurada de veracidad firmada, según el formato incluido en el portal de postulación.",
            "Copia simple de certificado o constancia de estudios técnicos o universitarios.",
        ],
        "cronograma": [
            ("Recepción de postulaciones", "15/08/2026 al 29/08/2026 hasta las 17:00"),
            ("Publicación de aptos", "02/09/2026"),
            ("Evaluación de conocimientos administrativos", "05/09/2026 de 09:00 a 10:30"),
            ("Entrevista personal", "08/09/2026"),
            ("Resultado final", "11/09/2026"),
        ],
        "exclusiones": [
            "La postulación será descalificada si se presenta después de las 17:00 del 29/08/2026 o si falta la declaración jurada firmada. No se aceptarán subsanaciones posteriores al cierre.",
            "La inasistencia a la evaluación o a la entrevista en el horario asignado elimina automáticamente a la persona del proceso.",
            "El contrato inicial es temporal y su renovación no está garantizada. La remuneración indicada es bruta y está sujeta a los descuentos de ley.",
        ],
        "canal": (
            "Enviar la postulación mediante el portal interno de demostración antes del cierre indicado. "
            "No se recibirán documentos por correo electrónico ni mensajería instantánea."
        ),
    },
    {
        "filename": "convocatoria_salud_enfermeria.pdf",
        "doc_title": "Convocatoria ficticia - Enfermero(a) Asistencial",
        "entity_label": "RED DE SALUD BIENESTAR SUR - CONVOCATORIA FICTICIA",
        "process_code": "PROCESO 2026-SA-102",
        "title": "Convocatoria: Enfermero(a) Asistencial",
        "subtitle": "Área de Enfermería - Servicio de Hospitalización | Trujillo, Perú | Modalidad presencial",
        "postulacion_rango": "Del 11 al 26 de agosto de 2026",
        "cierre": "26/08/2026 - 18:00",
        "vacantes": "4 posiciones",
        "objetivo": (
            "Brindar atención de enfermería a pacientes hospitalizados, asegurando el cumplimiento de "
            "protocolos clínicos, bioseguridad y calidad en la atención según normativa vigente."
        ),
        "requisitos_obligatorios": [
            "Título profesional de Enfermería, colegiado(a) y habilitado(a) por el Colegio de Enfermeros del Perú.",
            "Experiencia mínima de 1 año en servicios de hospitalización o áreas críticas.",
            "Certificado vigente de Soporte Vital Básico (BLS) o equivalente.",
            "Disponibilidad para trabajar en turnos rotativos, incluidos noches, fines de semana y feriados.",
            "Conocimiento actualizado de protocolos de bioseguridad y manejo de historias clínicas.",
        ],
        "requisitos_deseables": [
            "Especialización o cursos en cuidados intensivos, emergencias o áreas afines.",
            "Experiencia en manejo de sistemas de historia clínica electrónica.",
        ],
        "funciones": [
            "Administrar tratamientos y medicamentos según indicación médica.",
            "Monitorear signos vitales y evolución clínica de los pacientes a su cargo.",
            "Registrar oportunamente la información en la historia clínica.",
            "Coordinar con el equipo médico ante cambios en el estado del paciente.",
        ],
        "condiciones": [
            ("Tipo de contrato", "Contrato a plazo fijo por 6 meses, renovable según desempeño y necesidad del área."),
            ("Remuneración", "S/ 3,200 brutos mensuales, más bonificación por turno nocturno."),
            ("Horario", "Turnos rotativos de 12 horas, según rol mensual publicado por el área."),
            ("Modalidad", "Presencial, en instalaciones hospitalarias de Trujillo."),
            ("Inicio estimado", "22 de septiembre de 2026."),
        ],
        "documentos": [
            "Currículum vitae de máximo tres páginas, sin documentos sustentatorios en esta etapa.",
            "Declaración jurada de veracidad firmada, según el formato incluido en el portal de postulación.",
            "Copia simple de título profesional y constancia de habilidad vigente del colegio profesional.",
            "Copia del certificado vigente de Soporte Vital Básico (BLS) o equivalente.",
        ],
        "cronograma": [
            ("Recepción de postulaciones", "11/08/2026 al 26/08/2026 hasta las 18:00"),
            ("Publicación de aptos", "29/08/2026"),
            ("Evaluación de conocimientos clínicos", "02/09/2026 de 09:00 a 10:30"),
            ("Entrevista y verificación documentaria", "05/09/2026 y 06/09/2026"),
            ("Resultado final", "10/09/2026"),
        ],
        "exclusiones": [
            "La postulación será descalificada si se presenta después de las 18:00 del 26/08/2026, si falta la declaración jurada firmada o si la colegiatura no se encuentra habilitada.",
            "No se aceptará el certificado de Soporte Vital Básico vencido; su vigencia se verificará antes de la entrevista.",
            "La inasistencia a la evaluación o a la verificación documentaria en el horario asignado elimina automáticamente a la persona del proceso.",
            "El contrato inicial es temporal y su renovación no está garantizada. La remuneración indicada es bruta y está sujeta a los descuentos de ley.",
        ],
        "canal": (
            "Enviar la postulación mediante el portal interno de demostración antes del cierre indicado. "
            "No se recibirán documentos por correo electrónico ni mensajería instantánea."
        ),
    },
]


if __name__ == "__main__":
    for cfg in CONVOCATORIAS:
        build_convocatoria(cfg)

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
OUTPUT = ROOT / "output" / "pdf" / "convocatoria_ejemplo_analista_datos.pdf"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

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
GREEN = colors.HexColor("#067647")

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


def header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 13 * mm, width, 13 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont(font_bold, 8)
    canvas.drawString(18 * mm, height - 8 * mm, "TALENTO FUTURO - CONVOCATORIA FICTICIA")
    canvas.setFillColor(MUTED)
    canvas.setFont(font_regular, 7.5)
    canvas.drawString(18 * mm, 11 * mm, "Documento creado exclusivamente para demostración. No representa una oferta laboral real.")
    canvas.drawRightString(width - 18 * mm, 11 * mm, f"Página {doc.page}")
    canvas.restoreState()


doc = BaseDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    leftMargin=18 * mm,
    rightMargin=18 * mm,
    topMargin=22 * mm,
    bottomMargin=19 * mm,
    title="Convocatoria ficticia - Analista Junior de Datos",
    author="PostulaIA Demo",
)
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
doc.addPageTemplates(PageTemplate(id="default", frames=[frame], onPageEnd=header_footer))

story = [
    p("PROCESO 2026-AD-014", "Kicker"),
    p("Convocatoria: Analista Junior de Datos", "Hero"),
    p("Área de Innovación y Analítica | Lima, Perú | Modalidad híbrida", "Subtitle"),
    Table(
        [[p("POSTULACIÓN", "Center"), p("CIERRE", "Center"), p("VACANTES", "Center")],
         [p("Del 10 al 30 de agosto de 2026", "Small"), p("30/08/2026 - 18:00", "Small"), p("2 posiciones", "Small")]],
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
    p("Apoyar al equipo de analítica en la preparación, validación y visualización de información para decisiones comerciales. La persona seleccionada trabajará con datos ficticios durante el periodo de inducción y con información corporativa bajo protocolos internos después de su incorporación."),
    p("2. Requisitos obligatorios", "Section"),
    bullet("Bachiller o titulado en Ingeniería de Sistemas, Estadística, Economía, Administración o carreras afines."),
    bullet("Experiencia mínima de un año realizando análisis de datos, prácticas preprofesionales incluidas."),
    bullet("Conocimiento intermedio de Python y SQL, demostrable mediante evaluación técnica."),
    bullet("Dominio de hojas de cálculo y capacidad para explicar resultados a públicos no técnicos."),
    bullet("Disponibilidad para asistir presencialmente dos días por semana en Lima."),
    p("3. Requisitos deseables", "Section"),
    bullet("Conocimiento de Power BI, Looker Studio o herramientas equivalentes."),
    bullet("Experiencia con control de versiones Git y documentación de procesos."),
    p("4. Funciones principales", "Section"),
    bullet("Limpiar, transformar y validar conjuntos de datos."),
    bullet("Construir reportes y tableros con indicadores de negocio."),
    bullet("Documentar fuentes, reglas de calidad y supuestos del análisis."),
    bullet("Presentar hallazgos y alertar oportunamente sobre inconsistencias."),
    p("5. Condiciones laborales", "Section"),
    Table(
        [[p("Tipo de contrato", "Small"), p("Contrato a plazo fijo por 3 meses, renovable según desempeño y necesidad del área.", "Small")],
         [p("Remuneración", "Small"), p("S/ 2,800 brutos mensuales.", "Small")],
         [p("Horario", "Small"), p("Lunes a viernes, de 09:00 a 18:00, con una hora de refrigerio.", "Small")],
         [p("Modalidad", "Small"), p("Híbrida: dos días presenciales y tres días remotos por semana.", "Small")],
         [p("Inicio estimado", "Small"), p("21 de septiembre de 2026.", "Small")]],
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
    bullet("Currículum vitae de máximo tres páginas, sin documentos sustentatorios en esta etapa."),
    bullet("Declaración jurada de veracidad firmada, según el formato incluido en el portal de postulación."),
    bullet("Portafolio o enlace a un proyecto de análisis de datos; puede utilizar información pública o ficticia."),
    p("7. Cronograma del proceso", "Section"),
    Table(
        [[p("Etapa", "Center"), p("Fecha", "Center")],
         [p("Recepción de postulaciones", "Small"), p("10/08/2026 al 30/08/2026 hasta las 18:00", "Small")],
         [p("Publicación de aptos", "Small"), p("03/09/2026", "Small")],
         [p("Evaluación técnica virtual", "Small"), p("07/09/2026 de 10:00 a 11:30", "Small")],
         [p("Entrevistas", "Small"), p("10/09/2026 y 11/09/2026", "Small")],
         [p("Resultado final", "Small"), p("15/09/2026", "Small")]],
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
        [[p("ALERTA DE LECTURA", "Center")],
         [p("La postulación será descalificada si se presenta después de las 18:00 del 30/08/2026 o si falta la declaración jurada firmada. No se aceptarán subsanaciones posteriores al cierre.", "Alert")],
         [p("La evaluación técnica requiere cámara encendida y documento de identidad visible. La inasistencia en el horario asignado elimina automáticamente a la persona del proceso.", "Alert")],
         [p("El contrato inicial es temporal y su renovación no está garantizada. La remuneración indicada es bruta y está sujeta a los descuentos de ley.", "Alert")]],
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
    p("Enviar la postulación mediante el portal interno de demostración antes del cierre indicado. No se recibirán documentos por correo electrónico ni mensajería instantánea."),
    p("Importante: esta convocatoria, la organización y todos sus datos son ficticios. El archivo fue preparado para validar las funciones de PostulaIA.", "Small"),
]

doc.build(story)
print(OUTPUT)

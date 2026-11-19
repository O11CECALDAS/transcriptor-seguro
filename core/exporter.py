import io
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def create_docx(record: dict) -> io.BytesIO:
    """Creates a beautifully styled Word (.docx) document from a transcription record."""
    doc = Document()

    # Title
    title = doc.add_heading(record.get("title", "Transcripción de Audio/Video"), level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Metadata
    p_meta = doc.add_paragraph()
    p_meta.add_run(f"📅 Fecha: {record.get('date', 'N/A')}\n").italic = True
    p_meta.add_run(f"📁 Archivo original: {record.get('filename', 'N/A')}\n").italic = True
    if record.get("duration_est"):
        p_meta.add_run(f"⏱️ Duración: {record.get('duration_est')}\n").italic = True

    doc.add_paragraph("―" * 40)

    # Resumen
    if record.get("resumen"):
        doc.add_heading("1. Resumen Ejecutivo", level=1)
        doc.add_paragraph(record["resumen"])

    # Puntos Clave
    if record.get("puntos_clave"):
        doc.add_heading("2. Temas y Puntos Clave", level=1)
        doc.add_paragraph(record["puntos_clave"])

    # Acuerdos
    if record.get("acuerdos"):
        doc.add_heading("3. Acuerdos y Compromisos", level=1)
        doc.add_paragraph(record["acuerdos"])

    # Transcripción Completa
    if record.get("transcripcion"):
        doc.add_heading("4. Transcripción Completa con Hablantes", level=1)
        for line in record["transcripcion"].split("\n"):
            line = line.strip()
            if not line:
                continue
            p = doc.add_paragraph()
            # If line starts with [HH:MM:SS] Hablante:
            if line.startswith("[") and "]" in line and ":" in line:
                closing_bracket = line.find("]")
                colon = line.find(":", closing_bracket)
                if colon != -1:
                    speaker_part = line[:colon + 1]
                    text_part = line[colon + 1:].strip()
                    run_speaker = p.add_run(speaker_part + " ")
                    run_speaker.bold = True
                    run_speaker.font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)
                    p.add_run(text_part)
                else:
                    p.add_run(line)
            else:
                p.add_run(line)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

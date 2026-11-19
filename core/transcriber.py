import os
import time
from typing import Callable, Optional, Dict, Any, List
from google import genai
from google.genai import types

FALLBACK_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash"
]

def load_api_key() -> str:
    """Loads Gemini API key from Streamlit secrets, environment or local .env file."""
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    return api_key

def transcribe_audio_with_gemini(
    audio_path: str,
    api_key: Optional[str] = None,
    speakers_hint: Optional[str] = None,
    model_name: str = "gemini-3.1-flash-lite",
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> Dict[str, Any]:
    """
    Uploads the audio to Google Gemini, performs speaker diarization,
    transcription, and structured summary with automatic fallback across models.
    """
    resolved_key = api_key or load_api_key()
    if not resolved_key:
        raise ValueError("No se encontró la clave GEMINI_API_KEY. Por favor configúrala.")

    client = genai.Client(api_key=resolved_key)

    if progress_callback:
        progress_callback("Subiendo archivo de audio a la nube de Gemini...", 0.2)

    # Upload audio file to Gemini Files API
    uploaded_file = client.files.upload(file=audio_path)

    # Wait for the file to be processed
    if progress_callback:
        progress_callback("Esperando procesamiento del audio...", 0.4)

    while str(getattr(uploaded_file.state, "name", uploaded_file.state)) == "PROCESSING":
        time.sleep(2)
        uploaded_file = client.files.get(name=uploaded_file.name)

    if str(getattr(uploaded_file.state, "name", uploaded_file.state)) == "FAILED":
        raise RuntimeError(f"Error procesando el archivo en Gemini: {uploaded_file.error}")

    # Construct system prompt
    speakers_context = ""
    if speakers_hint and speakers_hint.strip():
        speakers_context = f"\nContexto / Nombres de los participantes sugeridos: {speakers_hint.strip()}"

    prompt = f"""Eres un transcriptor profesional experto y analista de reuniones.
Analiza este archivo de audio completo y genera una transcripción fidedigna y detallada en español, identificando a cada uno de los hablantes.{speakers_context}

Estructura tu respuesta exactamente en estas cuatro secciones en formato Markdown:

# RESUMEN EJECUTIVO
(Un resumen claro y conciso de 3-4 párrafos que sintetice de qué trató la reunión o grabación).

# TEMAS Y PUNTOS CLAVE
- Tema 1: detalle breve
- Tema 2: detalle breve
...

# ACUERDOS Y COMPROMISOS
- [Responsable/Hablante si se sabe]: Acuerdo o tarea a realizar.

# TRANSCRIPCIÓN COMPLETA
(Transcripción cronológica íntegra, palabra por palabra sin omitir contenido importante. Cada intervención debe tener marca de tiempo y el hablante identificado, por ejemplo:
[00:00:15] Hablante 1: Hola, buenos días...
[00:00:22] Hablante 2: Buenos días, ¿cómo estás?...
Si el contexto o los nombres de las personas son evidentes en la conversación, utiliza sus nombres reales, ej: [00:01:05] Carlos: ...)

Sé riguroso, no inventes información y asegúrate de transcribir todo el contenido de principio a fin.
"""

    # Build sequence of models to attempt
    models_to_try = [model_name] + [m for m in FALLBACK_MODELS if m != model_name]
    last_error = None
    response = None

    for idx, candidate in enumerate(models_to_try):
        try:
            if progress_callback:
                progress_callback(f"Transcribiendo y separando hablantes con {candidate}...", 0.6)

            response = client.models.generate_content(
                model=candidate,
                contents=[uploaded_file, prompt]
            )
            if response and response.text:
                break
        except Exception as e:
            err_str = str(e)
            if "503" in err_str or "404" in err_str or "UNAVAILABLE" in err_str or "NOT_FOUND" in err_str:
                last_error = e
                continue
            else:
                raise e

    if not response or not response.text:
        if last_error:
            raise last_error
        raise RuntimeError("No se obtuvo respuesta del modelo.")

    if progress_callback:
        progress_callback("Finalizando y estructurando documento...", 0.9)

    parsed = parse_transcription_sections(response.text)
    return parsed

def parse_transcription_sections(raw_text: str) -> Dict[str, str]:
    """Splits the raw Gemini output into organized components."""
    sections = {
        "raw_full": raw_text,
        "resumen": "",
        "puntos_clave": "",
        "acuerdos": "",
        "transcripcion": ""
    }

    current_section = None
    lines = raw_text.split("\n")
    current_content = []

    def save_current():
        if current_section and current_section in sections:
            sections[current_section] = "\n".join(current_content).strip()

    for line in lines:
        upper = line.strip().upper()
        if "# RESUMEN EJECUTIVO" in upper:
            save_current()
            current_section = "resumen"
            current_content = []
        elif "# TEMAS Y PUNTOS CLAVE" in upper or "# PUNTOS CLAVE" in upper or "# TEMAS CLAVE" in upper:
            save_current()
            current_section = "puntos_clave"
            current_content = []
        elif "# ACUERDOS Y COMPROMISOS" in upper or "# ACUERDOS" in upper or "# COMPROMISOS" in upper:
            save_current()
            current_section = "acuerdos"
            current_content = []
        elif "# TRANSCRIPCIÓN COMPLETA" in upper or "# TRANSCRIPCIÓN" in upper:
            save_current()
            current_section = "transcripcion"
            current_content = []
        else:
            current_content.append(line)

    save_current()

    # Fallback if markdown headers differed
    if not sections["transcripcion"]:
        sections["transcripcion"] = raw_text

    return sections

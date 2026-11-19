import os
import sys
import shutil
import tempfile
from datetime import datetime
import streamlit as st

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.converter import extract_and_compress_audio, get_file_size_mb
from core.transcriber import transcribe_audio_with_gemini, load_api_key
from core.exporter import create_docx

# Page configuration
st.set_page_config(
    page_title="Convertidor Seguro de Transcripción",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #4B5563;
        margin-bottom: 1.2rem;
    }
    .privacy-badge {
        background-color: #ECFDF5;
        border: 1px solid #10B981;
        color: #065F46;
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }
    .stButton>button {
        border-radius: 8px;
    }
    .login-box {
        max-width: 420px;
        margin: 50px auto;
        padding: 30px;
        background: #F9FAFB;
        border-radius: 12px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# ----------------- PASSWORD AUTHENTICATION -----------------
def get_configured_password() -> str:
    """Reads configured password from Streamlit secrets, environment, or .env."""
    try:
        if "APP_PASSWORD" in st.secrets:
            return str(st.secrets["APP_PASSWORD"]).strip()
    except Exception:
        pass

    pwd = os.environ.get("APP_PASSWORD", "")
    if not pwd:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("APP_PASSWORD="):
                        pwd = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    return pwd or "nelson2026"

def check_authentication() -> bool:
    """Verifies if the user is authenticated with the session password."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    configured_password = get_configured_password()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 25px;">
            <span style="font-size: 3rem;">🔐</span>
            <h2 style="color: #1E3A8A; margin-top: 10px;">Acceso Seguro</h2>
            <p style="color: #6B7280; font-size: 0.95rem;">Ingresa la contraseña para acceder al convertidor de audio y video.</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            entered_password = st.text_input("Contraseña", type="password", placeholder="Escribe la clave de acceso")
            submit_button = st.form_submit_button("Ingresar a la Aplicación", use_container_width=True, type="primary")

            if submit_button:
                if entered_password == configured_password:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta. Inténtalo de nuevo.")

        st.caption("🔒 Acceso privado y exclusivo para el equipo autorizado.")
    return False

# Stop execution if not authenticated
if not check_authentication():
    st.stop()

# ----------------- MAIN APPLICATION (AUTHENTICATED) -----------------

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/shield.png", width=64)
    st.title("Convertidor Seguro")
    st.caption("🟢 Sesión autorizada")

    st.markdown("""
    **Garantía de Privacidad:**
    - 🛡️ **Cero almacenamiento:** No guardamos base de datos ni historial.
    - 🧹 **Autolimpieza:** Al terminar y descargar, los archivos temporales se destruyen.
    - 🔒 **Borrado en Google:** El archivo se elimina de la nube de Gemini de inmediato.
    """)

    st.divider()

    api_key_loaded = load_api_key()
    if api_key_loaded:
        st.success("✅ Conexión con IA activa")
    else:
        st.warning("⚠️ Clave GEMINI_API_KEY no detectada")

    model_choice = st.selectbox(
        "Motor de IA",
        options=["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.8-flash"],
        index=0,
        help="Gemini 3.1 Flash Lite procesa audios de hasta 9 horas con máxima estabilidad."
    )

    st.divider()
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# Header
st.markdown('<div class="main-header">🎙️ Convertidor de Grabaciones a Texto y Word</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Transcripción con separación de hablantes, resumen ejecutivo y actas de acuerdos</div>', unsafe_allow_html=True)

st.markdown("""
<div class="privacy-badge">
    <strong>🛡️ Modo Seguro y Efímero Activo:</strong> Esta herramienta funciona estrictamente como un convertidor. 
    Tus archivos de video y audio se procesan en memoria temporal y <strong>se eliminan de inmediato</strong> tras generar tu documento en Word.
</div>
""", unsafe_allow_html=True)

# Main Form
col_upload, col_meta = st.columns([2, 1])

with col_upload:
    st.markdown("### 1. Selecciona tu grabación")
    uploaded_file = st.file_uploader(
        "Arrastra aquí cualquier archivo de audio o video",
        type=["mp4", "mkv", "mov", "avi", "webm", "mp3", "wav", "m4a", "aac", "ogg", "opus", "3gp", "amr", "flac"],
        help="Soporta todos los formatos de Android (grabadora de voz, WhatsApp), iPhone, Windows y Mac."
    )

with col_meta:
    st.markdown("### 2. Datos opcionales")
    default_name = os.path.splitext(uploaded_file.name)[0] if uploaded_file else ""
    meeting_title = st.text_input("Título del informe o acta:", value=default_name, placeholder="Ej: Comité de Obra N° 2")
    speakers_hint = st.text_area(
        "Participantes conocidos:",
        placeholder="Ej: Nelson (Residente), Felipe (Interventor), Ing. Christian.",
        help="Si escribes los nombres de quienes hablan, la IA los identificará automáticamente por su nombre real."
    )

st.markdown("---")

if st.button("🚀 Procesar Grabación y Generar Word", type="primary", use_container_width=True, disabled=not uploaded_file):
    final_title = meeting_title.strip() if meeting_title.strip() else (uploaded_file.name if uploaded_file else "Transcripción")
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(msg: str, pct: float):
        status_text.info(f"⏳ {msg}")
        progress_bar.progress(pct)

    temp_dir = tempfile.mkdtemp()
    try:
        # Step 1: Save uploaded file temporarily
        temp_input_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        orig_size = get_file_size_mb(temp_input_path)
        update_progress(f"Archivo recibido ({orig_size} MB). Extrayendo pista de voz con FFmpeg...", 0.15)

        # Step 2: Extract audio
        opt_audio_path = os.path.join(temp_dir, "audio_voice_optimized.mp3")
        extract_and_compress_audio(temp_input_path, opt_audio_path)
        opt_size = get_file_size_mb(opt_audio_path)

        st.toast(f"Pista optimizada de {orig_size} MB a {opt_size} MB", icon="✨")

        # Step 3: Transcribe with Gemini
        transcription_result = transcribe_audio_with_gemini(
            audio_path=opt_audio_path,
            api_key=api_key_loaded,
            speakers_hint=speakers_hint,
            model_name=model_choice,
            progress_callback=update_progress
        )

        progress_bar.progress(1.0)
        status_text.success("🎉 ¡Conversión completada con éxito!")

        # Step 4: Build Word Document
        record_data = {
            "title": final_title,
            "filename": uploaded_file.name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration_est": f"Tamaño original: {orig_size} MB",
            "resumen": transcription_result.get("resumen", ""),
            "puntos_clave": transcription_result.get("puntos_clave", ""),
            "acuerdos": transcription_result.get("acuerdos", ""),
            "transcripcion": transcription_result.get("transcripcion", ""),
            "raw_full": transcription_result.get("raw_full", "")
        }
        docx_file = create_docx(record_data)

        # Step 5: Save in session state so user can download
        st.session_state["current_result"] = record_data
        st.session_state["current_docx"] = docx_file

    except Exception as e:
        status_text.error(f"❌ Error durante la conversión: {str(e)}")
        st.exception(e)
    finally:
        # Step 6: STRICT EPHEMERAL PURGE - Delete all local temp files immediately
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception:
            pass

# Display Download and Preview if available in session
if "current_result" in st.session_state and "current_docx" in st.session_state:
    res = st.session_state["current_result"]
    docx_buf = st.session_state["current_docx"]

    st.markdown("### 📥 Descarga tu Acta y Transcripción")

    col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 1])
    with col_btn1:
        st.download_button(
            label="📄 Descargar Acta en Word (.docx)",
            data=docx_buf,
            file_name=f"{res['title']}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True
        )
    with col_btn2:
        st.download_button(
            label="📋 Descargar Texto Completo (.txt)",
            data=res.get("raw_full", ""),
            file_name=f"{res['title']}.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col_btn3:
        if st.button("🗑️ Limpiar Pantalla", use_container_width=True):
            del st.session_state["current_result"]
            del st.session_state["current_docx"]
            st.rerun()

    # Previews
    tab_sum, tab_dialogue = st.tabs(["📌 Resumen Ejecutivo y Acuerdos", "🗣️ Diálogo Completo"])

    with tab_sum:
        if res.get("resumen"):
            st.subheader("1. Resumen Ejecutivo")
            st.markdown(res["resumen"])
        if res.get("puntos_clave"):
            st.subheader("2. Puntos Clave y Temas Tratados")
            st.markdown(res["puntos_clave"])
        if res.get("acuerdos"):
            st.subheader("3. Acuerdos y Compromisos")
            st.markdown(res["acuerdos"])

    with tab_dialogue:
        st.subheader("4. Transcripción con Identificación de Hablantes")
        st.markdown(res.get("transcripcion", ""))

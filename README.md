# 🎙️ Convertidor Seguro de Audio y Video con IA

Aplicación web privada para transcribir y estructurar grabaciones de audio y video con identificación de hablantes (diarización), resumen ejecutivo y generación automática de actas en Word (.docx).

Diseñada especialmente para sincronizar el trabajo entre **Android**, **Windows** y **Mac**.

---

## 🛡️ Principios de Seguridad y Privacidad
1. **Modo Convertidor Efímero:** No existe base de datos ni se almacenan historiales en el servidor.
2. **Autolimpieza Inmediata:** Los archivos temporales se destruyen del servidor tan pronto como se genera el documento.
3. **Borrado en Google:** El archivo se elimina de los servidores de Gemini inmediatamente después de procesarse.
4. **Protección por Contraseña:** Acceso restringido exclusivamente mediante clave privada.

---

## 🚀 Despliegue en la Nube (Gratis y Permanente en Streamlit Cloud)

### Paso 1: Subir este código a un repositorio privado en GitHub
Abre la terminal en esta carpeta y ejecuta:
```bash
git init
git add .
git commit -m "Convertidor seguro de transcripcion"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/transcriptor-seguro.git
git push -u origin main
```
*(Crea primero el repositorio vacío en github.com y asegúrate de marcarlo como **Private / Privado**).*

### Paso 2: Conectar con Streamlit Cloud
1. Entra a **[share.streamlit.io](https://share.streamlit.io)** e inicia sesión con tu cuenta de GitHub.
2. Presiona el botón **"New app"** (Nueva aplicación).
3. Selecciona tu repositorio `transcriptor-seguro`, rama `main` y archivo principal `app.py`.
4. En la sección **"Advanced settings"** -> pestaña **"Secrets"**, pega lo siguiente:
```toml
GEMINI_API_KEY = "TU_API_KEY_DE_GEMINI"
APP_PASSWORD = "nelson2026"
```
5. Presiona **"Deploy"** (Desplegar).

¡Listo! Te entregará una URL como: `https://transcriptor-nelson.streamlit.app`.

---

## 📱 ¿Cómo lo usa Nelson?

* **En Android (Teléfono):**
  1. Abre el enlace en Google Chrome.
  2. Ingresa la contraseña (`nelson2026`).
  3. En el menú de opciones de Chrome (tres puntos arriba a la derecha), toca **"Agregar a la pantalla principal"**.
  4. Le quedará un icono como una App nativa. Desde allí puede seleccionar cualquier nota de voz o audio y descargar el Word.

* **En Windows (PC):**
  1. Abre el enlace en Chrome o Edge.
  2. Ingresa la contraseña.
  3. Arrastra sus grabaciones y descarga el Word listo.

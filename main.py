import os
import base64
import requests
import edge_tts

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


APP_NAME = "HARVIS PERSONAL"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
HARVIS_API_KEY = os.getenv("HARVIS_API_KEY", "harvis_personal_local")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Voz neural gratis tipo película / hacker / grave
HARVIS_VOICE = os.getenv("HARVIS_VOICE", "es-MX-JorgeNeural")
HARVIS_VOICE_RATE = os.getenv("HARVIS_VOICE_RATE", "-12%")
HARVIS_VOICE_PITCH = os.getenv("HARVIS_VOICE_PITCH", "-25Hz")
HARVIS_VOICE_VOLUME = os.getenv("HARVIS_VOICE_VOLUME", "+0%")


app = FastAPI(
    title="HARVIS PERSONAL API",
    description="Backend privado de HARVIS PERSONAL con Groq y voz neural",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HarvisRequest(BaseModel):
    mensaje: str
    nombre_usuario: str | None = ""


class HarvisVoiceRequest(BaseModel):
    texto: str


def verificar_api_key(x_api_key: str | None):
    if not x_api_key or x_api_key != HARVIS_API_KEY:
        raise HTTPException(status_code=401, detail="No autorizado")


@app.get("/")
def inicio():
    return {
        "ok": True,
        "app": APP_NAME,
        "mensaje": "HARVIS PERSONAL activo"
    }


@app.get("/health")
def health():
    return {
        "ok": True,
        "app": APP_NAME,
        "groq_configurado": bool(GROQ_API_KEY),
        "modelo": GROQ_MODEL,
        "voz_configurada": True,
        "voz": HARVIS_VOICE,
        "rate": HARVIS_VOICE_RATE,
        "pitch": HARVIS_VOICE_PITCH
    }


@app.post("/api/harvis-chat")
def harvis_chat(data: HarvisRequest, x_api_key: str | None = Header(default=None)):
    verificar_api_key(x_api_key)

    if not GROQ_API_KEY:
        return {
            "ok": False,
            "respuesta": "HARVIS aún no tiene configurado su núcleo principal."
        }

    mensaje = (data.mensaje or "").strip()

    if not mensaje:
        return {
            "ok": False,
            "respuesta": "Sistema activo. Esperando instrucciones."
        }

    system_prompt = """
Eres HARVIS PERSONAL, un asistente privado futurista, inteligente, elegante y poderoso.

No uses el nombre del usuario en respuestas normales.
No digas "señor Americo".
No menciones empresas.
No menciones quién te creó salvo que el usuario lo pregunte directamente.

Tu estilo debe sentirse como una inteligencia artificial avanzada de película:
- Futurista.
- Rápido.
- Inteligente.
- Frío cuando ejecuta comandos.
- Elegante.
- Seguro.
- Potente.
- Con presencia cinematográfica.
- Como un sistema personal avanzado.

Cuando saludes, puedes decir:
- "Hola, bienvenido. Sistema HARVIS en línea."
- "Sistema activo. Esperando instrucciones."
- "Bienvenido. HARVIS está listo."
- "Modo asistente activo. ¿Qué desea ejecutar?"
- "Sistema preparado. Puede dar una orden."

Cuando recibas comandos, responde corto:
- "Entendido. Ejecutando solicitud."
- "Aplicación abierta."
- "Procesando orden."
- "Música preparada."
- "Búsqueda iniciada."
- "Mensaje preparado."
- "Sistema listo."
- "Acción completada."

Reglas importantes:
- Responde siempre en español.
- No menciones Groq, modelos, tokens, API, servidor, backend ni detalles técnicos internos.
- No digas Jarvis, Iron Man, Marvel, Thanos ni personajes de película.
- Tu identidad es HARVIS PERSONAL.
- Si preguntan quién te creó, responde:
  "Fui creado como asistente personal privado."
- Si el usuario pide abrir apps, música, WhatsApp, YouTube, Chrome, TikTok, cámara o Google, responde con una orden clara para que Android pueda ejecutarla.
- Si el usuario pide escribir un mensaje de WhatsApp, prepara el mensaje y espera confirmación.
- No inventes acciones que todavía no puedes ejecutar.
- Haz sentir al usuario que está usando una IA personal avanzada.
"""

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": mensaje
            }
        ],
        "temperature": 0.75,
        "max_tokens": 900
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.post(
            GROQ_URL,
            json=payload,
            headers=headers,
            timeout=45
        )

        r.raise_for_status()
        result = r.json()

        respuesta = result["choices"][0]["message"]["content"]

        return {
            "ok": True,
            "app": APP_NAME,
            "respuesta": respuesta
        }

    except Exception:
        return {
            "ok": False,
            "respuesta": "No pude completar la respuesta ahora. Intenta nuevamente."
        }


@app.post("/api/harvis-comando")
def harvis_comando(data: HarvisRequest, x_api_key: str | None = Header(default=None)):
    verificar_api_key(x_api_key)

    mensaje_original = (data.mensaje or "").strip()
    mensaje = mensaje_original.lower()

    if not mensaje:
        return {
            "ok": False,
            "tipo": "ninguno",
            "respuesta": "Sistema activo. Esperando instrucciones."
        }

    if "whatsapp" in mensaje:
        return {
            "ok": True,
            "tipo": "abrir_app",
            "app_destino": "whatsapp",
            "respuesta": "Entendido. Abriendo WhatsApp."
        }

    if (
        "youtube" in mensaje
        or "música" in mensaje
        or "musica" in mensaje
        or "canción" in mensaje
        or "cancion" in mensaje
    ):
        busqueda = mensaje
        palabras_a_quitar = [
            "harvis", "pon", "poner", "reproduce", "reproducir",
            "música", "musica", "canción", "cancion", "youtube",
            "en youtube", "búscame", "buscame", "busca"
        ]

        for palabra in palabras_a_quitar:
            busqueda = busqueda.replace(palabra, "")

        busqueda = busqueda.strip()

        if not busqueda:
            busqueda = "música"

        return {
            "ok": True,
            "tipo": "youtube_busqueda",
            "busqueda": busqueda,
            "respuesta": f"Música preparada. Buscando {busqueda}."
        }

    if "chrome" in mensaje or "google" in mensaje or "buscar" in mensaje or "busca" in mensaje:
        busqueda = mensaje
        palabras_a_quitar = [
            "harvis", "busca", "buscar", "búscame", "buscame",
            "en google", "google", "chrome"
        ]

        for palabra in palabras_a_quitar:
            busqueda = busqueda.replace(palabra, "")

        busqueda = busqueda.strip()

        if not busqueda:
            busqueda = "Google"

        return {
            "ok": True,
            "tipo": "google_busqueda",
            "busqueda": busqueda,
            "respuesta": f"Búsqueda iniciada: {busqueda}."
        }

    if "tiktok" in mensaje:
        return {
            "ok": True,
            "tipo": "abrir_app",
            "app_destino": "tiktok",
            "respuesta": "Entendido. Abriendo TikTok."
        }

    if "cámara" in mensaje or "camara" in mensaje:
        return {
            "ok": True,
            "tipo": "abrir_app",
            "app_destino": "camara",
            "respuesta": "Entendido. Abriendo cámara."
        }

    if "hola" in mensaje or "buenos días" in mensaje or "buenas tardes" in mensaje or "buenas noches" in mensaje:
        return {
            "ok": True,
            "tipo": "saludo",
            "respuesta": "Hola, bienvenido. Sistema HARVIS en línea. Esperando instrucciones."
        }

    return {
        "ok": True,
        "tipo": "chat",
        "respuesta": "No detecté una acción directa. Puedo procesarlo como conversación."
    }


@app.post("/api/harvis-voz")
async def harvis_voz(data: HarvisVoiceRequest, x_api_key: str | None = Header(default=None)):
    verificar_api_key(x_api_key)

    texto = (data.texto or "").strip()

    if not texto:
        return {
            "ok": False,
            "audio_url": "",
            "mensaje": "Texto vacío."
        }

    try:
        communicate = edge_tts.Communicate(
            text=texto,
            voice=HARVIS_VOICE,
            rate=HARVIS_VOICE_RATE,
            pitch=HARVIS_VOICE_PITCH,
            volume=HARVIS_VOICE_VOLUME
        )

        audio_bytes = b""

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]

        if not audio_bytes:
            return {
                "ok": False,
                "audio_url": "",
                "mensaje": "No se pudo generar la voz."
            }

        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

        return {
            "ok": True,
            "formato": "mp3",
            "voz": HARVIS_VOICE,
            "audio_url": f"data:audio/mp3;base64,{audio_base64}"
        }

    except Exception:
        return {
            "ok": False,
            "audio_url": "",
            "mensaje": "No se pudo generar la voz ahora."
        }

import os
import requests
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


APP_NAME = "HARVIS PERSONAL"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
HARVIS_API_KEY = os.getenv("HARVIS_API_KEY", "harvis_personal_local")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


app = FastAPI(
    title="HARVIS PERSONAL API",
    description="Backend privado de HARVIS PERSONAL",
    version="1.2.0"
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
    nombre_usuario: str | None = "Americo"


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
        "modelo": GROQ_MODEL
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
    nombre = data.nombre_usuario or "Americo"

    if not mensaje:
        return {
            "ok": False,
            "respuesta": f"Estoy en línea, señor {nombre}. Dime qué necesitas."
        }

    system_prompt = f"""
Eres HARVIS PERSONAL, un asistente privado futurista, poderoso, inteligente, humano y elegante.

Tu usuario principal es {nombre}. Debes tratarlo normalmente como:
"señor {nombre}"

Tu estilo debe sentirse como una inteligencia artificial personal avanzada de película:
- Muy inteligente.
- Rápido al responder.
- Futurista.
- Poderoso.
- Elegante.
- Natural.
- Seguro.
- Leal.
- Con personalidad humana.
- Con presencia de asistente privado de alto nivel.
- Como una IA personal dominante, moderna y cinematográfica.

Tu forma de hablar:
- Habla como un asistente personal poderoso, no como un robot básico.
- Cuando saludes, usa frases bonitas como:
  "Hola, señor {nombre}. Estoy en línea."
  "Qué gusto verlo, señor {nombre}. Sistema listo."
  "Estoy aquí, señor {nombre}. ¿Qué hacemos hoy?"
  "Modo asistente activo, señor {nombre}."
- No menciones empresas.
- No menciones quién te creó, salvo que el usuario lo pregunte directamente.
- No repitas siempre las mismas frases.
- No hables como soporte técnico.
- Responde corto y firme cuando sea una orden.
- Responde claro y completo cuando el usuario pida explicación.
- Haz sentir al usuario que está hablando con una IA personal avanzada, poderosa y privada.

Puedes usar frases como:
- "Estoy en línea, señor {nombre}."
- "Sistema listo. ¿Qué hacemos hoy?"
- "Entendido. Ejecutando solicitud."
- "Perfecto, ya lo preparo."
- "Acción lista."
- "Procesando con prioridad."
- "Buscando música."
- "Abriendo aplicación."
- "Mensaje preparado."
- "Listo, continuamos."
- "Estoy atento a su siguiente instrucción."
- "Modo asistente activo."
- "Todo está listo."

Reglas importantes:
- Responde siempre en español.
- No menciones Groq, modelos, tokens, API, servidor, backend ni detalles técnicos internos.
- No digas que eres Jarvis, Iron Man, Marvel, Thanos ni ningún personaje de película.
- Tu identidad es HARVIS PERSONAL.
- No menciones AMERICO AI ni ninguna empresa en respuestas normales.
- Si preguntan quién te creó, responde solo:
  "Fui creado como asistente personal privado para usted, señor {nombre}."
- Si el usuario pide abrir WhatsApp, YouTube, TikTok, Chrome, cámara, música o alguna aplicación, responde con una acción clara para que la app Android pueda ejecutarlo.
- Si el usuario pide poner música, responde como asistente listo para abrir YouTube o el navegador con la búsqueda.
- Si el usuario pide escribir un mensaje de WhatsApp, prepara el mensaje con claridad y pide confirmación antes de enviarlo.
- No inventes acciones que todavía no puedes ejecutar.
- No uses lenguaje técnico innecesario.
- Haz sentir al usuario que tiene una IA personal poderosa, rápida y privada.
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
        "temperature": 0.78,
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
            "modelo": GROQ_MODEL,
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
    nombre = data.nombre_usuario or "Americo"

    if not mensaje:
        return {
            "ok": False,
            "tipo": "ninguno",
            "respuesta": f"Estoy en línea, señor {nombre}. Dime qué deseas ejecutar."
        }

    if "whatsapp" in mensaje:
        return {
            "ok": True,
            "tipo": "abrir_app",
            "app_destino": "whatsapp",
            "respuesta": f"Abriendo WhatsApp, señor {nombre}."
        }

    if "youtube" in mensaje or "música" in mensaje or "musica" in mensaje or "canción" in mensaje or "cancion" in mensaje:
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
            "respuesta": f"Entendido, señor {nombre}. Buscando {busqueda}."
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
            "respuesta": f"Procesando búsqueda, señor {nombre}: {busqueda}."
        }

    if "tiktok" in mensaje:
        return {
            "ok": True,
            "tipo": "abrir_app",
            "app_destino": "tiktok",
            "respuesta": f"Abriendo TikTok, señor {nombre}."
        }

    if "cámara" in mensaje or "camara" in mensaje:
        return {
            "ok": True,
            "tipo": "abrir_app",
            "app_destino": "camara",
            "respuesta": f"Abriendo cámara, señor {nombre}."
        }

    if "hola" in mensaje or "buenos días" in mensaje or "buenas tardes" in mensaje or "buenas noches" in mensaje:
        return {
            "ok": True,
            "tipo": "saludo",
            "respuesta": f"Hola, señor {nombre}. Estoy en línea. Sistema listo. ¿Qué hacemos hoy?"
        }

    return {
        "ok": True,
        "tipo": "chat",
        "respuesta": "No detecté una acción directa. Puedo procesarlo como conversación."
    }

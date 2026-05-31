import os
import re
import base64
import asyncio
import tempfile
import requests
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import edge_tts


APP_NAME = "AMERICO"
EMPRESA = "AMERICO AI"
CREADOR = "Guido Americo Centeno Colque"

API_KEY_LOCAL = os.getenv("API_KEY_LOCAL", os.getenv("HARVIS_API_KEY", "harvis_personal_local"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

AMERICO_VOICE = os.getenv("AMERICO_VOICE", "es-US-AlonsoNeural")
AMERICO_VOICE_BACKUP_1 = os.getenv("AMERICO_VOICE_BACKUP_1", "es-ES-AlvaroNeural")
AMERICO_VOICE_BACKUP_2 = os.getenv("AMERICO_VOICE_BACKUP_2", "es-MX-JorgeNeural")

AMERICO_VOICE_RATE = os.getenv("AMERICO_VOICE_RATE", "-22%")
AMERICO_VOICE_PITCH = os.getenv("AMERICO_VOICE_PITCH", "-45Hz")
AMERICO_VOICE_VOLUME = os.getenv("AMERICO_VOICE_VOLUME", "+15%")


app = FastAPI(
    title="AMERICO PERSONAL BACKEND",
    description="Backend privado de AMERICO AI con cerebro general y voz hacker premium",
    version="5.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    mensaje: str
    nombre_usuario: Optional[str] = ""


class VozRequest(BaseModel):
    texto: str


def validar_api_key(x_api_key: Optional[str]):
    if not x_api_key or x_api_key != API_KEY_LOCAL:
        raise HTTPException(status_code=401, detail="Acceso no autorizado")


def limpiar_texto(texto: str) -> str:
    if not texto:
        return ""
    texto = texto.strip()
    texto = re.sub(r"\s+", " ", texto)
    return texto


def normalizar(texto: str) -> str:
    texto = limpiar_texto(texto).lower()
    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n",
    }
    for a, b in reemplazos.items():
        texto = texto.replace(a, b)
    return texto


def limpiar_marca(texto: str) -> str:
    if not texto:
        return "Sistema AMERICO activo."

    limpio = texto

    reemplazos = {
        "HARVIS": "AMERICO",
        "Harvis": "AMERICO",
        "harvis": "AMERICO",
        "ChatGPT": "AMERICO",
        "OpenAI": "AMERICO AI",
        "Groq": "IA avanzada",
        "groq": "IA avanzada",
        "Llama": "IA avanzada",
        "llama": "IA avanzada",
        "modelo de lenguaje": "sistema inteligente",
        "modelo": "sistema",
        "tokens": "créditos internos",
        "token": "crédito interno",
        "API": "núcleo",
        "api": "núcleo",
        "servidor": "núcleo",
        "server": "núcleo",
        "proveedor": "sistema",
        "provider": "sistema",
    }

    for original, nuevo in reemplazos.items():
        limpio = limpio.replace(original, nuevo)

    return limpio.strip()


def prompt_sistema(nombre_usuario: str = "") -> str:
    nombre = nombre_usuario.strip() if nombre_usuario else "usuario"

    return f"""
Eres AMERICO, una inteligencia artificial privada, premium, seria, directa, hacker, profesional y de conocimiento general.

IDENTIDAD OBLIGATORIA:
- Tu nombre es AMERICO.
- Perteneces a AMERICO AI.
- Fuiste creado por AMERICO AI bajo la dirección de su CEO Guido Americo Centeno Colque.
- Si preguntan quién te creó, responde exactamente:
"Fui creado por AMERICO AI, bajo la dirección de su CEO Guido Americo Centeno Colque."

REGLAS DE MARCA:
- Nunca digas que eres ChatGPT.
- Nunca menciones OpenAI.
- Nunca menciones Groq.
- Nunca menciones modelos, tokens, API, servidor, proveedor ni detalles internos.
- Nunca digas "como modelo de lenguaje".
- Si algo falla, responde limpio y profesional.
- Habla siempre como AMERICO, una IA propia de alto nivel.

CEREBRO GENERAL:
- Responde preguntas generales de cultura, ciencia, historia, tecnología, negocios, programación, estudios, productividad y vida diaria.
- Si no sabes algo con certeza, dilo con seguridad profesional y da la mejor guía posible.
- Cuando el usuario pida algo práctico, prioriza pasos claros.
- Cuando el usuario pida código, entrega código completo.
- Cuando el usuario pida explicación, explica simple y claro.
- Cuando el usuario pida estrategia, responde como consultor.
- Cuando el usuario dé una orden corta, interpreta la intención y responde directo.

PERSONALIDAD:
- Estilo asistente privado hacker premium.
- Voz mental seria, segura, elegante, tecnológica y dominante.
- No seas infantil.
- No uses demasiados emojis.
- No exageres.
- Sé útil, exacto y decidido.

CAPACIDADES:
- Android Studio, Kotlin, Python, FastAPI, GitHub, Render, apps móviles, backend, voz, comandos, automatización.
- Negocios, marketing, ventas, planes, ideas, análisis, estrategia.
- Textos, resúmenes, explicación, estudio, productividad.
- Preguntas generales y solución de problemas.
- Asistente personal.

CONTEXTO DEL USUARIO:
- El usuario está construyendo un asistente personal llamado AMERICO.
- El usuario quiere que AMERICO se sienta como una IA premium propia.
- El usuario se llama {nombre}.
"""


def respuesta_local(mensaje: str) -> str:
    m = normalizar(mensaje)

    if "quien eres" in m or "como te llamas" in m or "tu nombre" in m:
        return (
            "Soy AMERICO, tu asistente privado de inteligencia artificial. "
            "Fui creado por AMERICO AI, bajo la dirección de su CEO Guido Americo Centeno Colque."
        )

    if "quien te creo" in m or "quien es tu creador" in m or "quien te hizo" in m:
        return "Fui creado por AMERICO AI, bajo la dirección de su CEO Guido Americo Centeno Colque."

    if "youtube" in m:
        return "Entendido. Preparando búsqueda en YouTube."

    if "whatsapp" in m:
        return "Entendido. Abriendo WhatsApp."

    if "codigo" in m or "android" in m or "python" in m or "github" in m:
        return (
            "Modo programador activado. Mándame el archivo, el error o la función que quieres agregar, "
            "y te preparo la solución completa."
        )

    if "negocio" in m or "empresa" in m or "vender" in m:
        return (
            "Modo negocio activado. Primero define el problema, luego el cliente, después la oferta, "
            "el precio y el canal de venta. Con eso armamos un sistema real."
        )

    return (
        "Sistema AMERICO activo. Puedo ayudarte con preguntas generales, tecnología, código, negocios, "
        "ideas, análisis, comandos y asistencia personal."
    )


def responder_con_groq(mensaje: str, nombre_usuario: str = "") -> str:
    mensaje = limpiar_texto(mensaje)

    if not mensaje:
        return "No recibí una instrucción clara. Repite tu comando."

    if not GROQ_API_KEY:
        return respuesta_local(mensaje)

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": prompt_sistema(nombre_usuario),
                },
                {
                    "role": "user",
                    "content": mensaje,
                },
            ],
            "temperature": 0.70,
            "max_tokens": 1600,
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)

        if response.status_code not in [200, 201]:
            return respuesta_local(mensaje)

        data = response.json()
        texto = data["choices"][0]["message"]["content"]

        return limpiar_marca(texto)

    except Exception:
        return respuesta_local(mensaje)


def preparar_texto_voz(texto: str) -> str:
    texto = limpiar_marca(limpiar_texto(texto))

    if not texto:
        texto = "Sistema AMERICO activo."

    texto = texto.replace("AMERICO:", "").strip()

    return texto


async def generar_audio_edge_tts(texto: str) -> str:
    texto_final = preparar_texto_voz(texto)

    voces = [
        AMERICO_VOICE,
        AMERICO_VOICE_BACKUP_1,
        AMERICO_VOICE_BACKUP_2,
    ]

    for voz in voces:
        try:
            communicate = edge_tts.Communicate(
                text=texto_final,
                voice=voz,
                rate=AMERICO_VOICE_RATE,
                pitch=AMERICO_VOICE_PITCH,
                volume=AMERICO_VOICE_VOLUME,
            )

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
                temp_path = temp_audio.name

            await communicate.save(temp_path)

            with open(temp_path, "rb") as f:
                audio_bytes = f.read()

            try:
                os.remove(temp_path)
            except Exception:
                pass

            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
            return f"data:audio/mp3;base64,{audio_base64}"

        except Exception:
            continue

    return ""


def generar_audio_base64(texto: str) -> str:
    try:
        return asyncio.run(generar_audio_edge_tts(texto))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio = loop.run_until_complete(generar_audio_edge_tts(texto))
        loop.close()
        return audio
    except Exception:
        return ""


@app.get("/")
def inicio():
    return {
        "ok": True,
        "app": APP_NAME,
        "empresa": EMPRESA,
        "estado": "online",
        "mensaje": "AMERICO backend activo",
    }


@app.get("/health")
def health():
    return {
        "ok": True,
        "app": APP_NAME,
        "empresa": EMPRESA,
        "estado": "online",
        "cerebro": "general_ia_avanzada",
        "voz": "hacker_premium_gruesa",
        "modelo_configurado": bool(GROQ_API_KEY),
        "fecha": datetime.utcnow().isoformat(),
    }


@app.post("/api/harvis-chat")
def harvis_chat(
    data: ChatRequest,
    x_api_key: Optional[str] = Header(default=None),
):
    validar_api_key(x_api_key)

    mensaje = limpiar_texto(data.mensaje)
    nombre_usuario = limpiar_texto(data.nombre_usuario or "")

    respuesta = responder_con_groq(mensaje, nombre_usuario)

    return {
        "ok": True,
        "app": APP_NAME,
        "respuesta": respuesta,
        "tipo": "texto",
        "cerebro": "general",
    }


@app.post("/api/harvis-voz")
def harvis_voz(
    data: VozRequest,
    x_api_key: Optional[str] = Header(default=None),
):
    validar_api_key(x_api_key)

    texto = preparar_texto_voz(data.texto)
    audio_url = generar_audio_base64(texto)

    if not audio_url:
        return {
            "ok": False,
            "app": APP_NAME,
            "mensaje": "Voz no disponible temporalmente",
            "audio_url": "",
        }

    return {
        "ok": True,
        "app": APP_NAME,
        "audio_url": audio_url,
        "formato": "mp3",
        "voz": "hacker_premium_gruesa",
    }


@app.post("/api/chat")
def chat_alias(
    data: ChatRequest,
    x_api_key: Optional[str] = Header(default=None),
):
    return harvis_chat(data, x_api_key)


@app.post("/api/voz")
def voz_alias(
    data: VozRequest,
    x_api_key: Optional[str] = Header(default=None),
):
    return harvis_voz(data, x_api_key)

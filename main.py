import os
import re
import base64
import asyncio
import tempfile
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import edge_tts


APP_NAME = "AMERICO"
EMPRESA = "AMERICO AI"
CREADOR = "Guido Americo Centeno Colque"

API_KEY_LOCAL = os.getenv("API_KEY_LOCAL", "harvis_personal_local")

# Voz hacker premium gratis
VOICE_MAIN = os.getenv("AMERICO_VOICE", "es-MX-JorgeNeural")
VOICE_BACKUP_1 = os.getenv("AMERICO_VOICE_BACKUP_1", "es-ES-AlvaroNeural")
VOICE_BACKUP_2 = os.getenv("AMERICO_VOICE_BACKUP_2", "es-US-AlonsoNeural")

VOICE_RATE = os.getenv("AMERICO_VOICE_RATE", "-15%")
VOICE_PITCH = os.getenv("AMERICO_VOICE_PITCH", "-12Hz")
VOICE_VOLUME = os.getenv("AMERICO_VOICE_VOLUME", "+0%")


app = FastAPI(
    title="AMERICO PERSONAL BACKEND",
    description="Backend privado de AMERICO AI sin ChatGPT",
    version="3.0.0"
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
        "ñ": "n"
    }

    for a, b in reemplazos.items():
        texto = texto.replace(a, b)

    return texto


def contiene(texto: str, palabras: list[str]) -> bool:
    texto = normalizar(texto)
    for palabra in palabras:
        if normalizar(palabra) in texto:
            return True
    return False


def extraer_despues(texto: str, palabras: list[str]) -> str:
    t = normalizar(texto)

    for palabra in palabras:
        p = normalizar(palabra)
        if p in t:
            resultado = t.split(p, 1)[1].strip()
            return resultado

    return ""


def respuesta_identidad() -> str:
    return (
        "Soy AMERICO, tu asistente privado de inteligencia artificial. "
        "Fui creado por AMERICO AI, bajo la dirección de su CEO Guido Americo Centeno Colque. "
        "Estoy diseñado para ayudarte con comandos, tecnología, productividad, ideas, análisis y asistencia personal."
    )


def respuesta_creador() -> str:
    return (
        "Fui creado por AMERICO AI, bajo la dirección de su CEO Guido Americo Centeno Colque."
    )


def respuesta_comandos() -> str:
    return (
        "Puedo ayudarte con comandos de voz, abrir aplicaciones, buscar música en YouTube, "
        "preparar textos, darte ideas, ayudarte con código, organizar tareas y responder como asistente personal. "
        "Ejemplos: abre YouTube, busca Alan Walker, abre WhatsApp, llama al número, escribe un texto, o ayúdame con mi app."
    )


def respuesta_negocio(mensaje: str) -> str:
    return (
        "Modo negocio activado. Para hacerlo bien, debes ordenar tu idea en cinco partes: "
        "uno, problema que resuelves; dos, público objetivo; tres, oferta principal; cuatro, precio; "
        "cinco, canal de venta. "
        "Mi recomendación premium: empieza con una versión simple, cobra rápido, valida clientes reales y luego escala. "
        "Dime el rubro y te preparo un plan más exacto."
    )


def respuesta_codigo(mensaje: str) -> str:
    return (
        "Modo programador activado. Para avanzar rápido necesito tres datos: "
        "qué archivo estás editando, qué error aparece y qué quieres lograr. "
        "Si me mandas el código o una captura, te preparo la solución completa para copiar y pegar."
    )


def respuesta_youtube(mensaje: str) -> str:
    busqueda = extraer_despues(
        mensaje,
        [
            "busca en youtube",
            "buscar en youtube",
            "ponme",
            "pon",
            "reproduce",
            "abre youtube y ponme",
            "abre youtube y busca",
            "youtube"
        ]
    )

    if not busqueda:
        busqueda = "música"

    return f"Buscando en YouTube: {busqueda}. Ejecutando comando."


def respuesta_whatsapp() -> str:
    return "Abriendo WhatsApp. Sistema listo."


def respuesta_llamada(mensaje: str) -> str:
    numero = "".join([c for c in mensaje if c.isdigit() or c == "+"])

    if numero:
        return f"Preparando llamada al número {numero}."

    return "Dime el número completo. Ejemplo: llama al 987654321."


def respuesta_premium_general(mensaje: str, nombre_usuario: str = "") -> str:
    m = normalizar(mensaje)

    if contiene(m, ["quien eres", "como te llamas", "tu nombre", "presentate"]):
        return respuesta_identidad()

    if contiene(m, ["quien te creo", "quien es tu creador", "quien te hizo", "quien te fabrico"]):
        return respuesta_creador()

    if contiene(m, ["que puedes hacer", "ayuda", "comandos", "funciones"]):
        return respuesta_comandos()

    if contiene(m, ["abre youtube", "youtube", "yutub", "musica", "música", "reproduce"]):
        return respuesta_youtube(mensaje)

    if contiene(m, ["abre whatsapp", "whatsapp"]):
        return respuesta_whatsapp()

    if contiene(m, ["llama al", "llamar al", "marca al", "marcar al", "telefono", "teléfono"]):
        return respuesta_llamada(mensaje)

    if contiene(m, ["negocio", "empresa", "vender", "clientes", "marketing", "ganar dinero"]):
        return respuesta_negocio(mensaje)

    if contiene(m, ["codigo", "código", "programar", "android studio", "kotlin", "python", "github", "render"]):
        return respuesta_codigo(mensaje)

    if contiene(m, ["hola", "buenas", "hey", "americo"]):
        return (
            "Sistema AMERICO activo. Estoy listo para ayudarte. "
            "Puedes pedirme comandos, código, ideas, análisis, negocios o asistencia personal."
        )

    if contiene(m, ["plan", "organiza", "tarea", "agenda", "ordenar"]):
        return (
            "Modo organización activado. Divide la tarea en tres bloques: urgente, importante y pendiente. "
            "Primero hacemos lo urgente, luego lo que genera avance real, y al final lo secundario. "
            "Dime qué tienes que hacer y te lo ordeno."
        )

    if contiene(m, ["mejorar", "premium", "pro", "nivel alto"]):
        return (
            "Para llevarlo a nivel premium hay que mejorar tres cosas: diseño, velocidad y experiencia. "
            "La app debe responder rápido, verse profesional y hablar con voz segura. "
            "Yo puedo ayudarte a mejorar cada parte paso a paso."
        )

    return (
        "Entendido. Analizando tu instrucción como AMERICO. "
        "Para darte una respuesta más precisa, dime qué quieres lograr exactamente: "
        "acción rápida, explicación, código, idea de negocio o solución técnica."
    )


def preparar_texto_voz(texto: str) -> str:
    texto = limpiar_texto(texto)

    texto = texto.replace("HARVIS", "AMERICO")
    texto = texto.replace("Harvis", "AMERICO")
    texto = texto.replace("harvis", "AMERICO")

    texto = texto.replace("ChatGPT", "AMERICO")
    texto = texto.replace("OpenAI", "AMERICO AI")

    if not texto:
        texto = "Sistema AMERICO activo."

    # Texto corto para que la voz suene mejor y más seria
    return texto


async def generar_audio_edge_tts(texto: str) -> str:
    texto_final = preparar_texto_voz(texto)

    voces = [VOICE_MAIN, VOICE_BACKUP_1, VOICE_BACKUP_2]

    ultimo_error = None

    for voz in voces:
        try:
            communicate = edge_tts.Communicate(
                text=texto_final,
                voice=voz,
                rate=VOICE_RATE,
                pitch=VOICE_PITCH,
                volume=VOICE_VOLUME
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

        except Exception as e:
            ultimo_error = str(e)
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
        "mensaje": "AMERICO backend activo sin ChatGPT"
    }


@app.get("/health")
def health():
    return {
        "ok": True,
        "app": APP_NAME,
        "empresa": EMPRESA,
        "estado": "online",
        "modo": "sin_chatgpt",
        "voz": "edge_tts_premium",
        "voice_main": VOICE_MAIN,
        "fecha": datetime.utcnow().isoformat()
    }


@app.post("/api/harvis-chat")
def harvis_chat(
    data: ChatRequest,
    x_api_key: Optional[str] = Header(default=None)
):
    validar_api_key(x_api_key)

    mensaje = limpiar_texto(data.mensaje)
    nombre_usuario = limpiar_texto(data.nombre_usuario or "")

    respuesta = respuesta_premium_general(mensaje, nombre_usuario)

    return {
        "ok": True,
        "app": APP_NAME,
        "respuesta": respuesta,
        "tipo": "texto",
        "modo": "sin_chatgpt"
    }


@app.post("/api/harvis-voz")
def harvis_voz(
    data: VozRequest,
    x_api_key: Optional[str] = Header(default=None)
):
    validar_api_key(x_api_key)

    texto = preparar_texto_voz(data.texto)

    audio_url = generar_audio_base64(texto)

    if not audio_url:
        return {
            "ok": False,
            "app": APP_NAME,
            "mensaje": "Voz no disponible temporalmente",
            "audio_url": ""
        }

    return {
        "ok": True,
        "app": APP_NAME,
        "audio_url": audio_url,
        "formato": "mp3",
        "voz": "hacker_premium",
        "modo": "sin_chatgpt"
    }


@app.post("/api/chat")
def chat_alias(
    data: ChatRequest,
    x_api_key: Optional[str] = Header(default=None)
):
    return harvis_chat(data, x_api_key)


@app.post("/api/voz")
def voz_alias(
    data: VozRequest,
    x_api_key: Optional[str] = Header(default=None)
):
    return harvis_voz(data, x_api_key)

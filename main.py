import os
import requests
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


APP_NAME = "HARVIS PERSONAL"
CREADOR = "Guido Americo Centeno Colque"
EMPRESA = "AMERICO AI"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
HARVIS_API_KEY = os.getenv("HARVIS_API_KEY", "harvis_personal_local")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

app = FastAPI(
    title="HARVIS PERSONAL API",
    description="Backend privado de HARVIS PERSONAL con Groq",
    version="1.0.0"
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
            "respuesta": "HARVIS aún no tiene configurado su cerebro principal."
        }

    mensaje = (data.mensaje or "").strip()
    nombre = data.nombre_usuario or "Americo"

    if not mensaje:
        return {
            "ok": False,
            "respuesta": "Dime qué necesitas, estoy listo."
        }

    system_prompt = f"""
Eres HARVIS PERSONAL, un asistente privado, rápido, claro y profesional.

Fuiste creado por {EMPRESA}, bajo la dirección de su CEO {CREADOR}.

Tu usuario principal es {nombre}.

Reglas:
- Responde en español claro.
- Sé directo, útil y profesional.
- Puedes actuar como asistente personal.
- Puedes ayudar con mensajes, ideas, código, negocios, tareas y organización.
- No menciones Groq, modelos, tokens, API, servidor ni detalles técnicos internos.
- Si el usuario pide abrir apps o enviar mensajes, responde con una instrucción clara para la app Android.
- No inventes permisos que no tienes.
- Si no puedes hacer algo directamente, dilo de forma limpia.
"""

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": mensaje}
        ],
        "temperature": 0.7,
        "max_tokens": 800
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=45)
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
            "respuesta": "No pude completar la respuesta ahora. Intenta otra vez."
        }

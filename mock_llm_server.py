"""
Mock LLM Server for Ollama, Groq, and OpenAI-compatible providers.
Allows instantaneous, zero-cost, 100% deterministic testing of the Ollama SEO AI plugin.
"""

import json
import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="Ollama SEO AI - Mock LLM Server",
    description="Simulates Ollama / Groq / OpenAI LLM inference for local CI/CD testing",
    version="1.0.0"
)

# Standard mock responses for each capability
MOCK_SEO_RESPONSE = {
    "seo_title": "Auditoría SEO Profesional y Posicionamiento Web con IA",
    "meta_description": "Descubre cómo optimizar los metadatos de tu sitio WordPress con Inteligencia Artificial. Guía definitiva de posicionamiento orgánico.",
    "focus_keyword": "auditoría seo profesional",
    "secondary_keywords": [
        "posicionamiento web ia",
        "optimización de metadatos",
        "seo para wordpress",
        "marcado json-ld",
        "consultoría seo"
    ],
    "search_intent": "Comercial",
    "post_excerpt": "Aprende las mejores técnicas de SEO técnico y estructuración semántica con IA para mejorar la indexación en motores de búsqueda.",
    "slug": "auditoria-seo-profesional-ia",
    "breadcrumb_title": "Auditoría SEO",
    "robots_noindex": 0,
    "robots_nofollow": 0,
    "product_short_description": "• Análisis técnico completo\n• Sugerencias de palabras clave LSI\n• Optimización de velocidad y rich snippets"
}

MOCK_FAQS_RESPONSE = {
    "faqs": [
        {
            "question": "¿Qué es una auditoría SEO y por qué es necesaria?",
            "answer": "Una auditoría SEO evalúa la salud técnica, semántica y de enlaces de un sitio web para identificar oportunidades de posicionamiento en Google."
        },
        {
            "question": "¿Cómo ayuda la IA en el posicionamiento orgánico?",
            "answer": "Permite generar títulos atractivos, meta descripciones orientadas al CTR y marcado Schema.org sin esfuerzo manual."
        },
        {
            "question": "¿El plugin es compatible con WooCommerce?",
            "answer": "Sí, extrae automáticamente precios, SKU, marcas y genera viñetas de venta comerciales junto con marcado Product."
        }
    ]
}

MOCK_HOWTO_RESPONSE = {
    "name": "Cómo configurar el plugin Ollama SEO AI en WordPress",
    "description": "Guía paso a paso para conectar un modelo de IA local o en la nube y optimizar tus contenidos.",
    "total_time": "15 minutos",
    "steps": [
        {
            "name": "Paso 1: Instalar y Activar el Plugin",
            "text": "Sube el archivo ZIP a tu WordPress o copia la carpeta en wp-content/plugins y actívalo en el panel."
        },
        {
            "name": "Paso 2: Configurar el Proveedor de IA",
            "text": "Dirígete a Herramientas > SEO AI Engine y selecciona Ollama, Groq Cloud, Together AI u OpenAI con tus credenciales."
        },
        {
            "name": "Paso 3: Generar Metadatos y Schemas",
            "text": "Abre cualquier entrada o producto y haz clic en 'Generar Metadatos con IA' dentro del Meta Box."
        }
    ]
}

MOCK_REVIEW_RESPONSE = {
    "item_reviewed": "Suite Ollama & Multi-Provider SEO AI",
    "rating_value": 4.9,
    "best_rating": 5.0,
    "worst_rating": 1.0,
    "review_body": "Excelente plugin para automatizar el SEO en WordPress con soporte local y cero latencia."
}

MOCK_SITE_ADVICE_RESPONSE = {
    "site_title_recommendation": "Agencia Digital & Consultoría SEO",
    "site_title_variants": [
        {"title": "Quintanilla SEO Lab", "style": "Corporativo"},
        {"title": "Posicionamiento Web & IA", "style": "SEO / Especialidad"},
        {"title": "Quintanilla.dev", "style": "Moderno / Minimalista"}
    ],
    "tagline_recommendation": "Impulsamos tu visibilidad orgánica con Inteligencia Artificial y SEO de alto rendimiento.",
    "reasoning": "El título y lema actuales son genéricos. Las propuestas refuerzan la autoridad temática y atraen tráfico cualificado."
}


class OllamaGenerateRequest(BaseModel):
    model: str
    prompt: str
    stream: Optional[bool] = False
    format: Optional[str] = "json"
    options: Optional[Dict[str, Any]] = None


@app.get("/")
def root():
    return {"status": "ok", "service": "Ollama SEO AI Mock LLM Server"}


# ----------------------------------------------------------------------
# 1. Ollama Endpoints Simulation (/api/tags, /api/generate)
# ----------------------------------------------------------------------
@app.get("/api/tags")
def ollama_tags():
    """Simulates Ollama available models list."""
    return {
        "models": [
            {"name": "llama3.1:latest", "modified_at": "2026-08-20T10:00:00Z", "size": 4661224676},
            {"name": "mistral:latest", "modified_at": "2026-08-20T10:00:00Z", "size": 4109865159},
            {"name": "qwen2.5:7b", "modified_at": "2026-08-20T10:00:00Z", "size": 4434442560},
            {"name": "gemma2:9b", "modified_at": "2026-08-20T10:00:00Z", "size": 5400124000}
        ]
    }


@app.post("/api/generate")
async def ollama_generate(payload: OllamaGenerateRequest, request: Request):
    """Simulates Ollama generation with structured JSON schema response."""
    prompt = payload.prompt.lower()

    # Chaos testing hooks via query params
    if "simulate_error" in request.query_params:
        raise HTTPException(status_code=500, detail="Simulated Ollama internal error")

    if "simulate_invalid_json" in request.query_params:
        return {
            "model": payload.model,
            "created_at": "2026-08-27T19:00:00Z",
            "response": "Texto conversacional inválido sin JSON {roto",
            "done": True
        }

    # Route based on prompt keywords
    if "pregunta" in prompt or "faqs" in prompt:
        data_to_return = MOCK_FAQS_RESPONSE
    elif "howto" in prompt or "paso a paso" in prompt:
        data_to_return = MOCK_HOWTO_RESPONSE
    elif "reseña" in prompt or "review" in prompt or "estrellas" in prompt:
        data_to_return = MOCK_REVIEW_RESPONSE
    elif "ajustes del sitio" in prompt or "blogname" in prompt or "tagline" in prompt:
        data_to_return = MOCK_SITE_ADVICE_RESPONSE
    else:
        data_to_return = MOCK_SEO_RESPONSE

    # Return valid Ollama structure with serialized inner JSON
    return {
        "model": payload.model,
        "created_at": "2026-08-27T19:00:00Z",
        "response": json.dumps(data_to_return, ensure_ascii=False),
        "done": True,
        "total_duration": 420000000,
        "load_duration": 12000000,
        "prompt_eval_count": 120,
        "eval_count": 210,
        "eval_duration": 390000000
    }


# ----------------------------------------------------------------------
# 2. OpenAI / Groq / Together AI Simulation (/v1/chat/completions)
# ----------------------------------------------------------------------
@app.get("/v1/models")
@app.get("/openai/v1/models")
def openai_models():
    return {
        "data": [
            {"id": "llama-3.3-70b-versatile", "object": "model"},
            {"id": "gpt-4o-mini", "object": "model"},
            {"id": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", "object": "model"}
        ]
    }


@app.post("/v1/chat/completions")
@app.post("/openai/v1/chat/completions")
async def openai_chat_completions(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    prompt = " ".join([m.get("content", "") for m in messages]).lower()

    if "faqs" in prompt or "pregunta" in prompt:
        content = json.dumps(MOCK_FAQS_RESPONSE, ensure_ascii=False)
    elif "howto" in prompt:
        content = json.dumps(MOCK_HOWTO_RESPONSE, ensure_ascii=False)
    elif "review" in prompt:
        content = json.dumps(MOCK_REVIEW_RESPONSE, ensure_ascii=False)
    else:
        content = json.dumps(MOCK_SEO_RESPONSE, ensure_ascii=False)

    return {
        "id": "chatcmpl-mock-12345",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": body.get("model", "mock-model"),
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 200,
            "total_tokens": 350
        }
    }


def start_server(host: str = "127.0.0.1", port: int = 11435):
    """Entrypoint to launch mock server."""
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    start_server()

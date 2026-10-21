import json
from typing import Any

import httpx
from openai import AsyncOpenAI

from app.config import settings


class LLMError(RuntimeError):
    pass


_openai_client: AsyncOpenAI | None = None
_groq_client: AsyncOpenAI | None = None


def _get_openai() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        if not settings.openai_api_key:
            raise LLMError("OPENAI_API_KEY no configurada.")
        _openai_client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=60.0,
        )
    return _openai_client


def _get_groq() -> AsyncOpenAI:
    global _groq_client
    if _groq_client is None:
        if not settings.groq_api_key:
            raise LLMError("GROQ_API_KEY no configurada.")
        _groq_client = AsyncOpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            timeout=60.0,
        )
    return _groq_client


async def chat_completion(
    system_prompt: str,
    user_prompt: str,
    *,
    json_mode: bool = True,
) -> str:
    if settings.llm_provider == "openai":
        return await _call_openai(system_prompt, user_prompt, json_mode)
    if settings.llm_provider == "groq":
        return await _call_groq(system_prompt, user_prompt, json_mode)
    if settings.llm_provider == "ollama":
        return await _call_ollama(system_prompt, user_prompt, json_mode)
    raise LLMError(f"Proveedor LLM desconocido: {settings.llm_provider}")


async def _call_openai(system_prompt: str, user_prompt: str, json_mode: bool) -> str:
    client = _get_openai()
    kwargs: dict[str, Any] = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = await client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


async def _call_groq(system_prompt: str, user_prompt: str, json_mode: bool) -> str:
    client = _get_groq()

    # Groq con gpt-oss-* falla si se fuerza response_format=json_object
    # cuando el modelo no devuelve JSON puro. Le pedimos JSON en el prompt
    # y dejamos que safe_json_parse lo tolere.
    if json_mode:
        system_prompt = (
            system_prompt
            + "\n\nIMPORTANTE: responde EXCLUSIVAMENTE con un objeto JSON válido, "
            "sin texto antes ni después, sin bloques de código, sin explicaciones."
        )

    kwargs: dict[str, Any] = {
        "model": settings.groq_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
    }
    # NO enviamos response_format para evitar el 400 de validación estricta
    resp = await client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


async def _call_ollama(system_prompt: str, user_prompt: str, json_mode: bool) -> str:
    payload: dict[str, Any] = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {
            "temperature": settings.llm_temperature,
            "num_predict": settings.llm_max_tokens,
        },
    }
    if json_mode:
        payload["format"] = "json"

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(f"{settings.ollama_base_url}/api/chat", json=payload)
        r.raise_for_status()
        data = r.json()
        return data.get("message", {}).get("content", "")


def safe_json_parse(raw: str, fallback: dict) -> dict:
    if not raw:
        return fallback
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                pass
    return fallback
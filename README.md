# Chatbot de compañía para adultos mayores

Servidor de lógica conversacional e interpretación afectiva alineado al
Protocolo de comportamiento conversacional afectivo.

## Stack

- FastAPI + Uvicorn
- Groq (`openai/gpt-oss-120b`) como LLM
- Redis (opcional, para memoria y rate limiting)
- faster-whisper para STT
- Docker

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/chat` | Chat de texto |
| POST | `/api/chat/audio` | Chat con audio (STT) |
| POST | `/api/reset/{user_id}` | Resetear memoria del usuario |
| GET | `/docs` | Swagger interactivo |

## Variables de entorno

Ver `.env` para la lista completa. Las mínimas para correr:

- `LLM_PROVIDER=groq`
- `GROQ_API_KEY=gsk_...`
- `GROQ_MODEL=openai/gpt-oss-120b`

## Demo pública

https://compania-bot.onrender.com/docs

## Variables de entorno en Render

| Variable | Valor |
|---|---|
| `LLM_PROVIDER` | `groq` |
| `GROQ_API_KEY` | (Secret, no en el repo) |
| `GROQ_MODEL` | `openai/gpt-oss-120b` |
| `WHISPER_MODEL_SIZE` | `base` |
| `RATE_LIMIT_ENABLED` | `false` (o `true` con Upstash) |
| `TTS_SPEED` | `0.8` |
| `VAD_SILENCE_SEC` | `3.5` |
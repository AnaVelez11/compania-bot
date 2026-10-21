from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM: "openai" | "groq" | "ollama"
    llm_provider: str = "openai"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Groq
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # VUI
    tts_speed: float = 0.8
    vad_silence_sec: float = 3.5

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    memoria_ttl_seconds: int = 86400
    memoria_max_turnos: int = 10

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_chat_por_minuto: int = 20
    rate_limit_chat_por_hora: int = 200
    rate_limit_storage_uri: str = "redis://localhost:6379/1"

    # Evaluación
    evaluacion_embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    evaluacion_similitud_min: float = 0.70

    # STT
    whisper_model_size: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    # LLM
    llm_max_tokens: int = 300
    llm_temperature: float = 0.4

    @field_validator(
        "openai_api_key",
        "groq_api_key",
        "redis_url",
        "rate_limit_storage_uri",
        "ollama_base_url",
        mode="before",
    )
    @classmethod
    def _strip(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


settings = Settings()
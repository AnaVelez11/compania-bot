from typing import Literal
from pydantic import BaseModel, Field


AvatarLiteral = Literal["Eco", "Serena", "Leo"]

EmocionLiteral = Literal[
    "Tristeza", "Alegria", "Preocupacion", "Frustracion", "Cotidianidad",
]

IntencionLiteral = Literal[
    "contar_experiencia",
    "expresar_emocion",
    "rechazo_tema",
    "rechazo_propuesta", 
    "saludo",
    "otro",
]

NecesidadLiteral = Literal[
    "desahogo", "compania", "escucha", "exploracion", "orientacion",
    "reminiscencia", "distraccion", "dar_espacio",
    "conversacion_cotidiana", "celebracion",
]

EstrategiaLiteral = Literal[
    "Escuchar / validar", "Desahogo", "Compania", "Explorar", "Orientar",
    "Reminiscencia", "Tranquilizar", "Distraer", "Dar espacio",
    "Conversacion cotidiana", "Derivar",
]


class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    texto: str = Field(..., min_length=0, max_length=2000)
    avatar: AvatarLiteral = "Eco"


class VUIConfig(BaseModel):
    tts_speed: float
    vad_silence_sec: float


class Verificacion(BaseModel):
    ok: bool = True
    violaciones: list[str] = Field(default_factory=list)
    intentos_regeneracion: int = 0


class ChatMeta(BaseModel):
    evidencia: str = ""
    estado_hipotetico: str = ""
    confianza_emocional: float = 0.5
    necesidades_candidatas: list[str] = Field(default_factory=list)
    necesidad_hipotetica: str = ""
    estrategia: str = ""
    motivo_estrategia: str = ""
    tono: str = ""
    estructura: str = ""
    acciones_a_evitar: list[str] = Field(default_factory=list)
    rechazo_previo: bool = False
    riesgo: bool = False
    tipo_riesgo: str = ""
    texto_limpio: str = ""
    intencion: str = "otro"
    turno: int = 1
    verificacion: Verificacion = Field(default_factory=Verificacion)


class ChatResponse(BaseModel):
    respuesta_texto: str
    emocion_detectada: str
    quick_replies: list[str]
    vui_config: VUIConfig
    meta: ChatMeta
    verificacion_ok: bool = True
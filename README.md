# Víncula · Backend

API que conecta el [frontend de Víncula](https://github.com/AnaVelez11/compania-bot-front) con un modelo de lenguaje para dar respuesta a tres compañeros de IA: **Eco**, **Serena** y **Leo**. El proyecto está pensado principalmente para personas adultas mayores.

> ⚠️ Los compañeros son IA y no reemplazan la atención de un profesional de la salud ni de un servicio de emergencia.

## Qué hace

- Recibe el mensaje de la persona, el compañero elegido y un identificador de sesión temporal.
- Genera la respuesta con un modelo de lenguaje servido por Groq, con la personalidad de cada compañero.
- Devuelve el texto, respuestas rápidas sugeridas y parámetros de voz.
- Limita las peticiones por usuario con `slowapi`.
- Restringe los orígenes permitidos con CORS.
  
## Tecnologías

FastAPI · Python · Groq · slowapi · desplegado en Render

## Estructura

```
compania-bot/
├── app/
│   ├── __init__.py
│   ├── main.py              # App FastAPI, middlewares y endpoints
│   ├── config.py            # Configuración y variables de entorno
│   ├── models.py            # Modelos de datos (peticiones y respuestas)
│   ├── prompts.py           # Personalidad e instrucciones de Eco, Serena y Leo
│   ├── llm_client.py        # Cliente del modelo de lenguaje (Groq)
│   ├── rate_limit.py        # Límite de peticiones (slowapi)
│   ├── services/
│   │   ├── afectivo.py      # Detección del estado emocional
│   │   ├── avatar.py        # Lógica de cada compañero
│   │   ├── estrategias.py   # Estrategias de respuesta
│   │   ├── generador.py     # Generación de la respuesta
│   │   ├── memoria.py       # Contexto de la conversación
│   │   ├── middleware.py    # Middlewares propios
│   │   ├── necesidades.py   # Detección de necesidades de la persona
│   │   ├── riesgo.py        # Detección de situaciones de riesgo
│   │   ├── stt.py           # Voz a texto
│   │   └── verificador.py   # Verificación de las respuestas
│   └── utils/
│       └── logging.py       # Registro de eventos
├── eval/
│   ├── golden_set.json      # Casos de referencia para evaluar
│   └── runner.py            # Ejecuta la evaluación
├── tests/                   # Pruebas automáticas (afectivo, api, estrategias,
│                            #   generador, memoria, middleware, riesgo, verificador)
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitignore
├── requirements.txt
└── README.md
```

## Privacidad

No se solicitan datos personales. El identificador de sesión es temporal y los mensajes se envían al proveedor de IA únicamente para generar la respuesta.

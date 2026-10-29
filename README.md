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

## Privacidad

No se solicitan datos personales. El identificador de sesión es temporal y los mensajes se envían al proveedor de IA únicamente para generar la respuesta.

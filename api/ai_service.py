import os
import json
import requests
from django.conf import settings

OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
MODEL_NAME = 'google/gemini-2.0-flash-exp:free'

class OpenRouterAIService:
    # Clase para manejar la comunicación con la API de OpenRouter
    def __init__(self, system_prompt: str=None):
        # Inicializa el servicio
        self.system_prompt = system_prompt
        self.base_headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.YOUR_SITE_URL,
            "X-Title": settings.YOUR_SITE_NAME,
        }

    def _send_request(self, messages: list):
        # Ejecuta la petición HTTP POST
        data = {
            "model": MODEL_NAME,
            "messages": messages,
            "response_format": {
                "type": "json", # Asegura que la IA se esfuerce en devolver un objeto JSON
            }
        }

        try:
            response = requests.post(OPENROUTER_URL, headers=self.base_headers, json=data)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as err:
            return {
                "error": f"Error de conexión o HTTP con OpenRouter: {err}"
            }

    def start_conversacion(self, initial_user_message: str):
        # Con system_prompt inicia una conversación
        messages = []
        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt,
            })

        messages.append({
            "role": "user",
            "content": initial_user_message,
        })

        return self._send_request(messages)

    def continuar_conversacion(self, chat_history: list, new_user_message: str):
        # Continua con la conversación asumiendo que el chat_history ya incluye el system_prompt
        messages = chat_history + [{
            "role": "user",
            "content": new_user_message,
        }]

        return self._send_request(messages)

    def evaluar_test(self, chat_log: list, evaluacion_criteria: dict) -> dict:
        # Envia el historial completo de la conversación para una evaluación estructurada
        evaluation_prompt = f"""
        TAREA: Analiza el historial de conversación proporcionado a continuación. 
        Evalúa al usuario basándote en los siguientes criterios, usando una escala de 1 a 5 (siendo 5 el mejor).

        Criterios de Evaluación: {json.dumps(evaluacion_criteria)}

        FORMATO DE SALIDA: Debes responder ÚNICAMENTE con un objeto JSON válido, sin preámbulos.
        El objeto debe contener:
        1. 'scores': Un objeto con las puntuaciones para cada criterio (ej: {{"liderazgo": 4, "comunicacion": 3}}).
        2. 'summary': Un resumen textual y una interpretación profesional de los resultados.
        3. 'feedback': Una sugerencia concisa para el usuario.

        Aquí está el historial de la conversación:
        """

        mensajes_enviar = chat_log + [{
            "role": "user",
            "content": evaluation_prompt,
        }]

        response_data = self._send_request(mensajes_enviar)

        if 'error' in response_data:
            return response_data

        try:
            content = response_data['choices'][0]['message']['content'].strip()
            # Limpiar posibles bloques de código (```json ... ```)
            if content.startswith('```json') and content.endswith('```'):
                content = content[7:-3].strip()

            return json.loads(content)

        except (json.JSONDecodeError, KeyError) as err:
            return {
                "error": "Error de procesamiento de JSON de la IA"
            }
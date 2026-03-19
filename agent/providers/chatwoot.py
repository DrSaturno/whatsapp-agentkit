# agent/providers/chatwoot.py — Adaptador para Chatwoot Agent Bot
# Generado por AgentKit para Se Instala Shop

"""
Integración con Chatwoot via Agent Bot API.
- Recibe mensajes desde el webhook de Chatwoot
- Responde via la API de Chatwoot (no directamente a Meta)
- Cuando un humano toma control en Chatwoot, el bot se calla automáticamente
"""

import os
import logging
import httpx
from fastapi import Request
from agent.providers.base import ProveedorWhatsApp, MensajeEntrante

logger = logging.getLogger("agentkit")


class ProveedorChatwoot(ProveedorWhatsApp):
    """
    Proveedor que integra el agente con Chatwoot via Agent Bot.

    Flujo:
    1. Chatwoot envía webhook POST cuando llega un mensaje
    2. Parseamos el mensaje del formato de Chatwoot
    3. Respondemos via la API REST de Chatwoot
    4. Chatwoot muestra la respuesta en la bandeja y la envía al cliente
    """

    def __init__(self):
        self.chatwoot_url = os.getenv("CHATWOOT_URL", "").rstrip("/")
        self.api_token = os.getenv("CHATWOOT_API_TOKEN")
        self.account_id = os.getenv("CHATWOOT_ACCOUNT_ID", "2")

    async def parsear_webhook(self, request: Request) -> list[MensajeEntrante]:
        """
        Parsea el payload del webhook de Chatwoot Agent Bot.

        Chatwoot envía eventos de tipo 'message_created' cuando llega un mensaje
        de un cliente. Ignoramos los mensajes enviados por el agente (outgoing).
        """
        try:
            body = await request.json()
        except Exception:
            return []

        mensajes = []

        # Solo procesar eventos de mensaje nuevo entrante
        event_type = body.get("event")
        if event_type != "message_created":
            return []

        message_type = body.get("message_type")
        # 'incoming' = mensaje del cliente, 'outgoing' = mensaje del agente
        if message_type != "incoming":
            return []

        # Extraer datos del mensaje
        contenido = body.get("content", "")
        conversation = body.get("conversation", {})
        contact = body.get("contact", {})

        conversation_id = str(conversation.get("id", ""))
        telefono = contact.get("phone_number", "") or conversation_id
        mensaje_id = str(body.get("id", ""))

        if not contenido:
            return []

        # Usamos el conversation_id como "teléfono" para el historial
        # porque en Chatwoot el identificador único es la conversación
        mensajes.append(MensajeEntrante(
            telefono=conversation_id,
            texto=contenido,
            mensaje_id=mensaje_id,
            es_propio=False,
        ))

        return mensajes

    async def enviar_mensaje(self, telefono: str, mensaje: str) -> bool:
        """
        Envía una respuesta via la API de Chatwoot.
        El parámetro 'telefono' en este caso es el conversation_id de Chatwoot.
        """
        if not self.chatwoot_url or not self.api_token:
            logger.warning("CHATWOOT_URL o CHATWOOT_API_TOKEN no configurados")
            return False

        conversation_id = telefono
        url = f"{self.chatwoot_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/messages"

        headers = {
            "api_access_token": self.api_token,
            "Content-Type": "application/json",
        }

        payload = {
            "content": mensaje,
            "message_type": "outgoing",
            "private": False,  # False = mensaje visible al cliente
        }

        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload, headers=headers)
            if r.status_code not in (200, 201):
                logger.error(f"Error Chatwoot API: {r.status_code} — {r.text}")
            return r.status_code in (200, 201)

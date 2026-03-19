# agent/tools.py — Herramientas del agente
# Generado por AgentKit para Se Instala Shop

"""
Herramientas específicas del negocio de Se Instala Shop.
Cubre los 4 casos de uso: FAQ, ventas/leads, pedidos y soporte post-venta.
"""

import os
import yaml
import logging
from datetime import datetime

logger = logging.getLogger("agentkit")


def cargar_info_negocio() -> dict:
    """Carga la información del negocio desde business.yaml."""
    try:
        with open("config/business.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("config/business.yaml no encontrado")
        return {}


def obtener_horario() -> dict:
    """Retorna el horario de atención del negocio y si está abierto ahora."""
    info = cargar_info_negocio()
    ahora = datetime.now()
    dia_semana = ahora.weekday()  # 0=lunes, 6=domingo
    hora_actual = ahora.hour * 60 + ahora.minute  # minutos desde medianoche
    apertura = 10 * 60 + 30   # 10:30 en minutos
    cierre = 17 * 60           # 17:00 en minutos

    esta_abierto = (
        0 <= dia_semana <= 4 and  # lunes a viernes
        apertura <= hora_actual < cierre
    )

    return {
        "horario": info.get("negocio", {}).get("horario", "Lunes a Viernes de 10:30 a 17:00"),
        "esta_abierto": esta_abierto,
    }


def buscar_en_knowledge(consulta: str) -> str:
    """
    Busca información relevante en los archivos de /knowledge.
    Retorna el contenido más relevante encontrado.
    """
    resultados = []
    knowledge_dir = "knowledge"

    if not os.path.exists(knowledge_dir):
        return "No hay archivos de conocimiento disponibles."

    for archivo in os.listdir(knowledge_dir):
        ruta = os.path.join(knowledge_dir, archivo)
        if archivo.startswith(".") or not os.path.isfile(ruta):
            continue
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
                if consulta.lower() in contenido.lower():
                    resultados.append(f"[{archivo}]: {contenido[:500]}")
        except (UnicodeDecodeError, IOError):
            continue

    if resultados:
        return "\n---\n".join(resultados)
    return "No encontré información específica sobre eso en mis archivos."


# ── VENTAS / LEADS ────────────────────────────────────────────────────────────

# Registro en memoria simple (en producción esto iría a la base de datos)
_leads: dict[str, dict] = {}


def registrar_lead(telefono: str, nombre: str, interes: str) -> str:
    """Registra un cliente interesado para seguimiento del equipo de ventas."""
    _leads[telefono] = {
        "nombre": nombre,
        "interes": interes,
        "telefono": telefono,
        "fecha": datetime.now().isoformat(),
        "estado": "nuevo",
    }
    logger.info(f"Lead registrado: {nombre} ({telefono}) — interés: {interes}")
    return f"Lead registrado correctamente para {nombre}"


def obtener_lead(telefono: str) -> dict | None:
    """Recupera los datos de un lead por teléfono."""
    return _leads.get(telefono)


# ── PEDIDOS ───────────────────────────────────────────────────────────────────

# Registro de pedidos en memoria (en producción iría a la base de datos)
_pedidos: dict[str, list] = {}


def agregar_al_pedido(telefono: str, producto: str, cantidad: int = 1) -> str:
    """Agrega un producto al pedido actual del cliente."""
    if telefono not in _pedidos:
        _pedidos[telefono] = []
    _pedidos[telefono].append({
        "producto": producto,
        "cantidad": cantidad,
        "timestamp": datetime.now().isoformat(),
    })
    logger.info(f"Producto agregado al pedido de {telefono}: {cantidad}x {producto}")
    return f"Agregado: {cantidad}x {producto}"


def ver_pedido(telefono: str) -> list:
    """Retorna los ítems del pedido actual del cliente."""
    return _pedidos.get(telefono, [])


def confirmar_pedido(telefono: str, nombre_cliente: str, contacto: str) -> dict:
    """
    Confirma el pedido del cliente y lo registra para procesamiento.
    Retorna el resumen del pedido confirmado.
    """
    items = _pedidos.get(telefono, [])
    if not items:
        return {"error": "No hay productos en el pedido"}

    pedido = {
        "numero": f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "telefono": telefono,
        "nombre": nombre_cliente,
        "contacto": contacto,
        "items": items,
        "fecha": datetime.now().isoformat(),
        "estado": "confirmado",
    }

    # Limpiar el carrito después de confirmar
    _pedidos[telefono] = []

    logger.info(f"Pedido confirmado: {pedido['numero']} para {nombre_cliente}")
    return pedido


# ── SOPORTE POST-VENTA ────────────────────────────────────────────────────────

_tickets: dict[str, dict] = {}
_contador_tickets = 0


def crear_ticket_soporte(telefono: str, problema: str) -> str:
    """Crea un ticket de soporte para el cliente."""
    global _contador_tickets
    _contador_tickets += 1
    ticket_id = f"TKT-{_contador_tickets:04d}"

    _tickets[ticket_id] = {
        "id": ticket_id,
        "telefono": telefono,
        "problema": problema,
        "estado": "abierto",
        "fecha": datetime.now().isoformat(),
    }

    logger.info(f"Ticket creado: {ticket_id} — {problema[:50]}")
    return ticket_id


def consultar_ticket(ticket_id: str) -> dict | None:
    """Consulta el estado de un ticket de soporte."""
    return _tickets.get(ticket_id)


def escalar_a_humano(telefono: str, contexto: str) -> str:
    """
    Escala la conversación a un agente humano.
    En producción, esto podría enviar una notificación al equipo.
    """
    logger.warning(f"Escalado a humano solicitado para {telefono}: {contexto[:100]}")
    return f"Conversación de {telefono} escalada al equipo humano"

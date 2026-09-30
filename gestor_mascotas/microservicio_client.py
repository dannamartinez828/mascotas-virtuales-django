"""Funciones que hablan con el microservicio (Node + Neon) para el saldo de
monedas de cada mascota. Las usan tanto la app mascotas (minijuego) como la
app tienda (comprar cosas), por eso viven aca, a nivel de proyecto."""
import requests
from django.conf import settings


def obtener_monedas(mascota_id):
    """Devuelve (cantidad, error). Si hay error de conexion, cantidad es 0."""
    try:
        resp = requests.get(
            f"{settings.MICROSERVICIO_URL}/api/monedas/{mascota_id}", timeout=5
        )
        resp.raise_for_status()
        return resp.json().get('cantidad', 0), None
    except requests.RequestException as e:
        return 0, f"No se pudo consultar el saldo de monedas: {e}"


def ganar_monedas(mascota_id, cantidad):
    """Suma monedas (ej: al ganar el minijuego). Devuelve (nuevo_saldo, error)."""
    try:
        resp = requests.post(
            f"{settings.MICROSERVICIO_URL}/api/monedas/{mascota_id}/ganar",
            json={'cantidad': cantidad},
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json().get('cantidad', 0), None
    except requests.RequestException as e:
        return None, f"No se pudo guardar las monedas ganadas: {e}"


def gastar_monedas(mascota_id, cantidad):
    """Intenta gastar monedas (ej: comprar en la tienda).
    Devuelve (ok, saldo_resultante, error)."""
    try:
        resp = requests.post(
            f"{settings.MICROSERVICIO_URL}/api/monedas/{mascota_id}/gastar",
            json={'cantidad': cantidad},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get('ok', False), data.get('cantidad', 0), None
    except requests.RequestException as e:
        return False, 0, f"No se pudo procesar la compra: {e}"

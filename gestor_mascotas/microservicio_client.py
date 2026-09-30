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


# ---------------------------------------------------------------------------
# CRUD de curiosidades: estas funciones son las que hacen que la app Django
# modifique DIRECTAMENTE la base de datos Neon (INSERT/UPDATE/DELETE), a
# traves del microservicio. No hay nada guardado en SQLite para esto: la
# unica fuente de verdad es la tabla `curiosidades` en Neon.
# ---------------------------------------------------------------------------

def listar_curiosidades():
    """Devuelve (lista, error) con todas las curiosidades guardadas en Neon."""
    try:
        resp = requests.get(f"{settings.MICROSERVICIO_URL}/api/curiosidades", timeout=5)
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return [], f"No se pudo listar las curiosidades: {e}"


def obtener_curiosidad(curiosidad_id):
    """Devuelve (curiosidad, error) para precargar el formulario de edicion."""
    try:
        resp = requests.get(
            f"{settings.MICROSERVICIO_URL}/api/curiosidades/id/{curiosidad_id}", timeout=5
        )
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, f"No se pudo obtener la curiosidad: {e}"


def crear_curiosidad(especie, texto):
    """INSERT en Neon. Devuelve (curiosidad_creada, error)."""
    try:
        resp = requests.post(
            f"{settings.MICROSERVICIO_URL}/api/curiosidades",
            json={'especie': especie, 'texto': texto},
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, f"No se pudo crear la curiosidad: {e}"


def editar_curiosidad(curiosidad_id, especie, texto):
    """UPDATE en Neon. Devuelve (curiosidad_actualizada, error)."""
    try:
        resp = requests.put(
            f"{settings.MICROSERVICIO_URL}/api/curiosidades/{curiosidad_id}",
            json={'especie': especie, 'texto': texto},
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, f"No se pudo editar la curiosidad: {e}"


def eliminar_curiosidad(curiosidad_id):
    """DELETE en Neon. Devuelve (ok, error)."""
    try:
        resp = requests.delete(
            f"{settings.MICROSERVICIO_URL}/api/curiosidades/{curiosidad_id}", timeout=5
        )
        resp.raise_for_status()
        return True, None
    except requests.RequestException as e:
        return False, f"No se pudo eliminar la curiosidad: {e}"

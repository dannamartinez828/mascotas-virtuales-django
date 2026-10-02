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


# ---------- Curiosidades: lectura (Node) y escritura (Python, 1 servicio por operacion) ----------

# Los servicios de Render gratis se duermen y tardan ~50 s en despertar,
# por eso las escrituras usan un timeout largo.
TIMEOUT_ESCRITURA = 60


def _error_de(resp_o_excepcion):
    """Saca un mensaje legible de una respuesta HTTP o de una excepcion."""
    resp = getattr(resp_o_excepcion, 'response', None)
    if resp is not None:
        try:
            return resp.json().get('error') or f"HTTP {resp.status_code}"
        except ValueError:
            return f"HTTP {resp.status_code}"
    return str(resp_o_excepcion)


def listar_curiosidades():
    """Lee todas las curiosidades desde el microservicio Node. Devuelve (lista, error)."""
    try:
        resp = requests.get(f"{settings.MICROSERVICIO_URL}/api/curiosidades", timeout=10)
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return [], f"No se pudo consultar las curiosidades: {_error_de(e)}"


def insertar_curiosidad(especie, texto):
    """Microservicio Python de INSERCION. Devuelve (curiosidad, error)."""
    try:
        resp = requests.post(
            f"{settings.MS_INSERTAR_URL}/api/curiosidades",
            json={'especie': especie, 'texto': texto},
            timeout=TIMEOUT_ESCRITURA,
        )
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, f"No se pudo insertar: {_error_de(e)}"


def actualizar_curiosidad(curiosidad_id, especie, texto):
    """Microservicio Python de ACTUALIZACION. Devuelve (curiosidad, error)."""
    try:
        resp = requests.put(
            f"{settings.MS_ACTUALIZAR_URL}/api/curiosidades/{curiosidad_id}",
            json={'especie': especie, 'texto': texto},
            timeout=TIMEOUT_ESCRITURA,
        )
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, f"No se pudo actualizar: {_error_de(e)}"


def eliminar_curiosidad(curiosidad_id):
    """Microservicio Python de ELIMINACION. Devuelve (ok, error)."""
    try:
        resp = requests.delete(
            f"{settings.MS_ELIMINAR_URL}/api/curiosidades/{curiosidad_id}",
            timeout=TIMEOUT_ESCRITURA,
        )
        resp.raise_for_status()
        return True, None
    except requests.RequestException as e:
        return False, f"No se pudo eliminar: {_error_de(e)}"

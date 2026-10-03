"""Funciones que hablan con los microservicios (Neon): saldo de monedas y
curiosidades. Las usan la app mascotas (minijuego, curiosidades) y la app
tienda (comprar), por eso viven aca, a nivel de proyecto.

Las LECTURAS (curiosidades y monedas) pasan por `resiliencia.llamar_lectura`:
si el microservicio de Node.js falla, se usa el de respaldo escrito en Go."""
import requests
from django.conf import settings

from .resiliencia import llamar_lectura


def obtener_monedas(mascota_id):
    """Devuelve (cantidad, error). Si hay error de conexion, cantidad es 0."""
    try:
        resp = llamar_lectura('GET', f"/api/monedas/{mascota_id}")
        return resp.json().get('cantidad', 0), None
    except requests.RequestException as e:
        return 0, f"No se pudo consultar el saldo de monedas: {_error_de(e)}"


def ganar_monedas(mascota_id, cantidad):
    """Suma monedas (ej: al ganar el minijuego). Devuelve (nuevo_saldo, error)."""
    try:
        resp = llamar_lectura('POST', f"/api/monedas/{mascota_id}/ganar", json={'cantidad': cantidad})
        return resp.json().get('cantidad', 0), None
    except requests.RequestException as e:
        return None, f"No se pudo guardar las monedas ganadas: {_error_de(e)}"


def gastar_monedas(mascota_id, cantidad):
    """Intenta gastar monedas (ej: comprar en la tienda).
    Devuelve (ok, saldo_resultante, error)."""
    try:
        resp = llamar_lectura('POST', f"/api/monedas/{mascota_id}/gastar", json={'cantidad': cantidad})
        data = resp.json()
        return data.get('ok', False), data.get('cantidad', 0), None
    except requests.RequestException as e:
        return False, 0, f"No se pudo procesar la compra: {_error_de(e)}"


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
    if isinstance(resp_o_excepcion, requests.Timeout):
        return "el servicio tardo demasiado en responder"
    if isinstance(resp_o_excepcion, requests.ConnectionError):
        return "no hay conexion con el servicio"
    return str(resp_o_excepcion)


def listar_curiosidades():
    """Lee todas las curiosidades (Node.js, o Go si Node falla). Devuelve (lista, error)."""
    try:
        resp = llamar_lectura('GET', "/api/curiosidades")
        return resp.json(), None
    except requests.RequestException as e:
        return [], f"No se pudo consultar las curiosidades: {_error_de(e)}"


def curiosidades_por_especie(especie):
    """Curiosidades de una especie (Node.js, o Go si Node falla). Devuelve (lista, error)."""
    try:
        resp = llamar_lectura('GET', f"/api/curiosidades/{especie}")
        return resp.json(), None
    except requests.RequestException as e:
        return [], f"No se pudo consultar las curiosidades: {_error_de(e)}"


# Prefijo de las variables de settings de cada lenguaje:
# MS_* = Python, NODE_* = Node.js, JAVA_* = Java, GO_* = Go
PREFIJO_VIA = {'python': 'MS', 'node': 'NODE', 'java': 'JAVA', 'go': 'GO'}


def _url_escritura(operacion, via):
    """URL base del microservicio que ejecuta la operacion, segun el lenguaje elegido."""
    prefijo = PREFIJO_VIA.get(via, 'MS')
    return getattr(settings, f"{prefijo}_{operacion.upper()}_URL")


def insertar_curiosidad(especie, texto, via='python'):
    """Microservicio de INSERCION (via='python', 'node', 'java' o 'go'). Devuelve (curiosidad, error)."""
    try:
        resp = requests.post(
            f"{_url_escritura('insertar', via)}/api/curiosidades",
            json={'especie': especie, 'texto': texto},
            timeout=TIMEOUT_ESCRITURA,
        )
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, f"No se pudo insertar: {_error_de(e)}"


def actualizar_curiosidad(curiosidad_id, especie, texto, via='python'):
    """Microservicio de ACTUALIZACION (via='python', 'node', 'java' o 'go'). Devuelve (curiosidad, error)."""
    try:
        resp = requests.put(
            f"{_url_escritura('actualizar', via)}/api/curiosidades/{curiosidad_id}",
            json={'especie': especie, 'texto': texto},
            timeout=TIMEOUT_ESCRITURA,
        )
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, f"No se pudo actualizar: {_error_de(e)}"


def eliminar_curiosidad(curiosidad_id, via='python'):
    """Microservicio de ELIMINACION (via='python', 'node', 'java' o 'go'). Devuelve (ok, error)."""
    try:
        resp = requests.delete(
            f"{_url_escritura('eliminar', via)}/api/curiosidades/{curiosidad_id}",
            timeout=TIMEOUT_ESCRITURA,
        )
        resp.raise_for_status()
        return True, None
    except requests.RequestException as e:
        return False, f"No se pudo eliminar: {_error_de(e)}"

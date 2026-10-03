"""Resiliencia para el microservicio que CONSULTA los datos.

Servicio principal: Node.js (settings.MICROSERVICIO_URL)
Servicio de respaldo: Go (settings.MICROSERVICIO_RESPALDO_URL), misma API y
la misma base de datos de Neon.

Que hace:
  1. Llama primero al principal.
  2. Si falla (no conecta, tarda demasiado o responde 5xx) llama al de respaldo,
     asi la app sigue mostrando la informacion.
  3. Interruptor (circuit breaker): despues de 2 fallos seguidos el principal se
     "abre" por 30 segundos y las siguientes llamadas van directo al respaldo,
     sin esperar el timeout cada vez. Pasado ese tiempo se vuelve a intentar.
  4. Cuando se usa el respaldo, se "despierta" al principal en segundo plano
     (en Render gratis se duerme) para que vuelva a estar listo.

Los errores 4xx NO activan el respaldo: son respuestas validas del servicio.
Las escrituras (monedas) solo van al respaldo si el principal ni siquiera
llego a conectarse o respondio 5xx; un timeout no basta, porque el principal
podria haber procesado la peticion y se cobraria dos veces.
"""
import threading
import time

import requests
from django.conf import settings

UMBRAL_FALLOS = 2          # fallos seguidos para abrir el interruptor
SEGUNDOS_ABIERTO = 30      # cuanto tiempo se salta el principal
TIMEOUT_PRINCIPAL = 8      # lecturas: si tarda mas, se prueba el respaldo
TIMEOUT_RESPALDO = 45      # el respaldo tambien puede estar dormido (Render gratis)
TIMEOUT_ESCRITURA = 60     # monedas: esperar a que despierte el principal

NOMBRE_PRINCIPAL = 'Node.js'
NOMBRE_RESPALDO = 'Go'

_candado = threading.Lock()
_fallos = 0
_abierto_hasta = 0.0
_ultimo_despertar = 0.0

# que servicio uso la peticion en curso (para avisarle al usuario en pantalla)
_local = threading.local()


# ---------- Estado por peticion (middleware + context processor) ----------
class FuenteDatosMiddleware:
    """Reinicia, al empezar cada peticion, el registro de que servicio respondio."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.fuente = None
        _local.respaldo = False
        return self.get_response(request)


def fuente_datos(request):
    """Context processor: deja disponible en todas las plantillas que servicio
    entrego los datos de esta pagina (para mostrar el aviso del respaldo)."""
    usado_respaldo = getattr(_local, 'respaldo', False)
    fuente = getattr(_local, 'fuente', None)
    return {
        'respaldo_activo': usado_respaldo,
        'fuente_datos': NOMBRE_RESPALDO + ' (respaldo)' if usado_respaldo else (NOMBRE_PRINCIPAL if fuente else ''),
        'nombre_principal': NOMBRE_PRINCIPAL,
        'nombre_respaldo': NOMBRE_RESPALDO,
    }


# ---------- Interruptor ----------
def _principal_abierto():
    with _candado:
        return time.monotonic() < _abierto_hasta


def _registrar_fallo():
    global _fallos, _abierto_hasta
    with _candado:
        _fallos += 1
        if _fallos >= UMBRAL_FALLOS:
            _abierto_hasta = time.monotonic() + SEGUNDOS_ABIERTO


def _registrar_exito():
    global _fallos, _abierto_hasta
    with _candado:
        _fallos = 0
        _abierto_hasta = 0.0


def reiniciar_estado():
    """Para pruebas: deja el interruptor como nuevo."""
    _registrar_exito()


def estado_interruptor():
    with _candado:
        return {'fallos': _fallos, 'abierto': time.monotonic() < _abierto_hasta}


def _despertar_principal():
    """Pide la raiz del principal en segundo plano para sacarlo del sueno."""
    global _ultimo_despertar
    base = settings.MICROSERVICIO_URL
    with _candado:
        if time.monotonic() - _ultimo_despertar < 60:
            return
        _ultimo_despertar = time.monotonic()

    def _ping():
        try:
            requests.get(f"{base}/", timeout=TIMEOUT_ESCRITURA)
        except requests.RequestException:
            pass

    threading.Thread(target=_ping, daemon=True).start()


# ---------- Llamada con respaldo ----------
class _FalloDelServicio(Exception):
    """El servicio no pudo atender la peticion (candidato a usar el respaldo)."""

    def __init__(self, causa, definitivo_para_escritura):
        super().__init__(str(causa))
        self.causa = causa
        # True si el servicio claramente NO proceso la peticion (no conecto / 5xx)
        self.definitivo_para_escritura = definitivo_para_escritura


def _intentar(base, metodo, ruta, timeout, json):
    try:
        resp = requests.request(metodo, f"{base}{ruta}", json=json, timeout=timeout)
    except requests.ConnectionError as e:
        raise _FalloDelServicio(e, True)
    except requests.Timeout as e:
        raise _FalloDelServicio(e, False)
    except requests.RequestException as e:
        raise _FalloDelServicio(e, False)
    if resp.status_code >= 500:
        raise _FalloDelServicio(requests.HTTPError(f"HTTP {resp.status_code}", response=resp), True)
    return resp


def llamar_lectura(metodo, ruta, json=None, idempotente=None):
    """Llama a `ruta` en el servicio principal y, si falla, en el de respaldo.

    Devuelve la respuesta (requests.Response). Lanza requests.RequestException
    si no se pudo con ninguno de los dos, o si el servicio respondio 4xx
    (igual que `raise_for_status`).
    """
    if idempotente is None:
        idempotente = metodo.upper() == 'GET'
    principal = settings.MICROSERVICIO_URL.rstrip('/')
    respaldo = (getattr(settings, 'MICROSERVICIO_RESPALDO_URL', '') or '').rstrip('/')

    # orden de intentos: el principal primero, salvo que el interruptor este
    # abierto (entonces el respaldo primero y el principal como ultimo recurso)
    if not respaldo:
        orden = ['principal']
    elif _principal_abierto():
        orden = ['respaldo', 'principal']
    else:
        orden = ['principal', 'respaldo']

    ultimo_fallo = None
    for nombre in orden:
        base = principal if nombre == 'principal' else respaldo
        if nombre == 'principal':
            timeout = TIMEOUT_PRINCIPAL if idempotente else TIMEOUT_ESCRITURA
        else:
            timeout = TIMEOUT_RESPALDO if idempotente else TIMEOUT_ESCRITURA

        try:
            resp = _intentar(base, metodo, ruta, timeout, json)
        except _FalloDelServicio as f:
            if nombre == 'principal':
                _registrar_fallo()
            ultimo_fallo = f
            # una escritura solo se repite en otro servicio si el anterior
            # claramente no la proceso (no conecto o respondio 5xx)
            if not idempotente and not f.definitivo_para_escritura:
                raise f.causa
            continue

        if nombre == 'principal':
            _registrar_exito()
            _local.fuente = 'principal'
        else:
            _local.fuente = 'respaldo'
            _local.respaldo = True
            _despertar_principal()
        resp.raise_for_status()
        return resp

    raise ultimo_fallo.causa

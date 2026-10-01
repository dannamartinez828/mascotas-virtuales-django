import os
import requests
from django.conf import settings

ESPECIES_NOMBRES = {'perro':'Perro','gato':'Gato','dragon':'Dragón','robot':'Robot'}

def _url(name, default=''):
    return os.environ.get(name, default).rstrip('/')

def obtener_mascotas_resiliente():
    """Consulta Python primero y Node como respaldo. Devuelve (lista, fuente, error)."""
    primary = _url('CONSULTA_PYTHON_URL')
    fallback = _url('CONSULTA_NODE_URL')
    errores = []
    if primary:
        try:
            r=requests.get(f'{primary}/api/mascotas',timeout=4)
            r.raise_for_status()
            return r.json(), 'consulta-python', None
        except requests.RequestException as e:
            errores.append(f'Python: {e}')
    if fallback:
        try:
            r=requests.get(f'{fallback}/api/mascotas',timeout=4)
            r.raise_for_status()
            return r.json(), 'consulta-node (respaldo)', None
        except requests.RequestException as e:
            errores.append(f'Node: {e}')
    return [], None, ' | '.join(errores) if errores else 'No hay URLs de consulta configuradas.'

def crear_mascota_api(nombre, especie, hambre=50, felicidad=50):
    url=_url('CRUD_INSERTAR_URL')
    if not url: return None
    r=requests.post(f'{url}/api/mascotas',json={'nombre':nombre,'especie':especie,'hambre':hambre,'felicidad':felicidad},timeout=5)
    r.raise_for_status()
    return r.json()

def actualizar_mascota_api(mascota_id,nombre,especie,hambre=50,felicidad=50):
    url=_url('CRUD_ACTUALIZAR_URL')
    if not url: return None
    r=requests.put(f'{url}/api/mascotas/{mascota_id}',json={'nombre':nombre,'especie':especie,'hambre':hambre,'felicidad':felicidad},timeout=5)
    r.raise_for_status()
    return r.json()

def eliminar_mascota_api(mascota_id):
    url=_url('CRUD_ELIMINAR_URL')
    if not url: return None
    r=requests.delete(f'{url}/api/mascotas/{mascota_id}',timeout=5)
    r.raise_for_status()
    return r.json()

def obtener_monedas(mascota_id):
    try:
        resp=requests.get(f'{settings.MICROSERVICIO_URL}/api/monedas/{mascota_id}',timeout=5)
        resp.raise_for_status(); return resp.json().get('cantidad',0),None
    except requests.RequestException as e: return 0,f'No se pudo consultar el saldo de monedas: {e}'

def ganar_monedas(mascota_id,cantidad):
    try:
        resp=requests.post(f'{settings.MICROSERVICIO_URL}/api/monedas/{mascota_id}/ganar',json={'cantidad':cantidad},timeout=5)
        resp.raise_for_status(); return resp.json().get('cantidad',0),None
    except requests.RequestException as e: return None,f'No se pudo guardar las monedas ganadas: {e}'

def gastar_monedas(mascota_id,cantidad):
    try:
        resp=requests.post(f'{settings.MICROSERVICIO_URL}/api/monedas/{mascota_id}/gastar',json={'cantidad':cantidad},timeout=5)
        resp.raise_for_status(); data=resp.json()
        return data.get('ok',False),data.get('cantidad',0),None
    except requests.RequestException as e: return False,0,f'No se pudo procesar la compra: {e}'

from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
import random
import requests
from .models import Mascota, ESPECIES
from gestor_mascotas.microservicio_client import (
    obtener_monedas, ganar_monedas,
    listar_curiosidades, insertar_curiosidad, actualizar_curiosidad, eliminar_curiosidad,
)

OPCIONES_JUEGO = ('piedra', 'papel', 'tijera')
GANA_A = {'piedra': 'tijera', 'papel': 'piedra', 'tijera': 'papel'}


def listar_mascotas(request):
    mascotas = Mascota.objects.all()
    for mascota in mascotas:
        mascota.actualizar_por_tiempo()  # si paso tiempo, le baja la felicidad/sube el hambre
    return render(request, 'mascotas/listar.html', {'mascotas': mascotas})


def detalle_mascota(request, mascota_id):
    mascota = get_object_or_404(Mascota, id=mascota_id)
    mascota.actualizar_por_tiempo()
    monedas, error_monedas = obtener_monedas(mascota.id)
    context = {'mascota': mascota, 'monedas': monedas, 'error_monedas': error_monedas}
    return render(request, 'mascotas/detalle.html', context)


def crear_mascota(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        especie = request.POST.get('especie')
        if nombre:
            Mascota.objects.create(nombre=nombre, especie=especie)
            return redirect('listar_mascotas')
    return render(request, 'mascotas/crear.html', {'especies': ESPECIES})


def editar_mascota(request, mascota_id):
    # UPDATE del CRUD: permite cambiar el nombre y la especie de una mascota ya existente
    mascota = get_object_or_404(Mascota, id=mascota_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        especie = request.POST.get('especie')
        if nombre:
            mascota.nombre = nombre
            mascota.especie = especie
            mascota.save()
            return redirect('detalle_mascota', mascota_id=mascota.id)

    context = {'mascota': mascota, 'especies': ESPECIES}
    return render(request, 'mascotas/editar.html', context)


def eliminar_mascota(request, mascota_id):
    # DELETE del CRUD: borra la mascota (y en cascada su inventario, por el
    # related_name definido en tienda.models.Inventario). Solo por POST,
    # para que no se pueda borrar por accidente abriendo el link (GET).
    mascota = get_object_or_404(Mascota, id=mascota_id)
    if request.method == 'POST':
        mascota.delete()
        return redirect('listar_mascotas')
    return redirect('detalle_mascota', mascota_id=mascota.id)


def alimentar_mascota(request, mascota_id):
    # ruta dinamica: recibe el id de la mascota y le baja el hambre
    mascota = get_object_or_404(Mascota, id=mascota_id)
    mascota.actualizar_por_tiempo()
    mascota.hambre = max(mascota.hambre - 20, 0)
    mascota.registrar_interaccion()
    mascota.save()
    return redirect('detalle_mascota', mascota_id=mascota.id)


def jugar_mascota(request, mascota_id):
    # ruta dinamica: recibe el id de la mascota y le sube la felicidad
    mascota = get_object_or_404(Mascota, id=mascota_id)
    mascota.actualizar_por_tiempo()
    mascota.felicidad = min(mascota.felicidad + 15, 100)
    mascota.hambre = min(mascota.hambre + 5, 100)  # jugar tambien da un poco de hambre
    mascota.registrar_interaccion()
    mascota.save()
    return redirect('detalle_mascota', mascota_id=mascota.id)


def ver_curiosidades(request, mascota_id):
    # vista que consulta el modelo Mascota (shortcut get_object_or_404)
    # y ademas consume un microservicio propio (Node.js + Neon) desplegado en Render
    mascota = get_object_or_404(Mascota, id=mascota_id)

    curiosidades = []
    error = None
    try:
        url = f"{settings.MICROSERVICIO_URL}/api/curiosidades/{mascota.especie}"
        respuesta = requests.get(url, timeout=5)
        respuesta.raise_for_status()
        curiosidades = respuesta.json()
    except requests.RequestException as e:
        error = f"No se pudo contactar el microservicio: {e}"

    # patron visto en clase: la vista arma un context y se lo pasa al template
    context = {
        'mascota': mascota,
        'curiosidades': curiosidades,
        'error': error,
    }
    return render(request, 'mascotas/curiosidades.html', context)


def preguntar_ia(request, mascota_id):
    # consulta una IA externa gratuita (Groq) para responder preguntas
    # sobre el cuidado de la mascota. Ademas de la especie, le pasamos a
    # la IA datos reales sacados de la base de datos (hambre/felicidad/
    # monedas de la mascota, y los items que existen en la tienda con sus
    # precios y efectos) para que pueda dar respuestas concretas, por
    # ejemplo "que me conviene comprarle" usando los items que SI existen,
    # en vez de inventarse una respuesta generica.
    from tienda.models import Item, Inventario  # import local para evitar dependencia circular entre apps

    mascota = get_object_or_404(Mascota, id=mascota_id)
    mascota.actualizar_por_tiempo()
    monedas, _error_monedas = obtener_monedas(mascota.id)

    items = Item.objects.all()
    items_texto = '\n'.join(
        f"- {item.nombre} (cuesta {item.costo} monedas, da +{item.precio_felicidad} felicidad, "
        f"-{item.reduce_hambre} hambre)"
        for item in items
    ) or 'No hay items cargados en la tienda todavia.'

    inventario = Inventario.objects.filter(mascota=mascota, cantidad__gt=0).select_related('item')
    inventario_texto = '\n'.join(
        f"- {inv.cantidad}x {inv.item.nombre}" for inv in inventario
    ) or 'No tiene nada guardado en el inventario.'

    pregunta = ''
    respuesta = None
    error = None

    if request.method == 'POST':
        pregunta = request.POST.get('pregunta', '').strip()
        if not pregunta:
            error = 'Escribe una pregunta primero.'
        elif not settings.GROQ_API_KEY:
            error = 'Falta configurar GROQ_API_KEY para poder usar la IA.'
        else:
            try:
                headers = {
                    'Authorization': f'Bearer {settings.GROQ_API_KEY}',
                    'Content-Type': 'application/json',
                }
                datos_reales = (
                    f'Mascota: {mascota.nombre}, especie {mascota.get_especie_display()}.\n'
                    f'Hambre actual: {mascota.hambre}/100 (0=satisfecho, 100=muriendo de hambre).\n'
                    f'Felicidad actual: {mascota.felicidad}/100 (0=triste, 100=feliz).\n'
                    f'Monedas disponibles: {monedas}.\n\n'
                    f'Items en la tienda:\n{items_texto}\n\n'
                    f'Inventario de {mascota.nombre}:\n{inventario_texto}'
                )
                payload = {
                    'model': settings.GROQ_MODEL,
                    'temperature': 0.2,
                    'messages': [
                        {
                            'role': 'system',
                            'content': (
                                'Eres el asistente de cuidado dentro de una app de mascotas '
                                'virtuales. Respondes en español, en pocas frases. '
                                'CADA mensaje del usuario viene acompañado de los datos REALES '
                                'y ACTUALES de su mascota (hambre, felicidad, monedas, items de '
                                'la tienda). Es OBLIGATORIO que tu respuesta use esos datos '
                                'exactos (numeros, nombres de items) cuando sean relevantes a la '
                                'pregunta. Nunca digas que no tienes esa informacion: siempre la '
                                'tienes, esta en el mensaje del usuario. No inventes items ni '
                                'numeros que no esten en esos datos.'
                            ),
                        },
                        {
                            'role': 'user',
                            'content': (
                                f'Datos actuales de mi mascota y de la tienda:\n{datos_reales}\n\n'
                                f'Mi pregunta: {pregunta}'
                            ),
                        },
                    ],
                }
                resp = requests.post(settings.GROQ_API_URL, headers=headers, json=payload, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                respuesta = data['choices'][0]['message']['content']
            except requests.RequestException as e:
                error = f'No se pudo contactar la IA: {e}'

    context = {
        'mascota': mascota,
        'pregunta': pregunta,
        'respuesta': respuesta,
        'error': error,
    }
    return render(request, 'mascotas/preguntar_ia.html', context)


def jugar_minijuego(request, mascota_id):
    # minijuego simple (piedra, papel o tijera) para ganar monedas que
    # despues se gastan en la tienda. El saldo se guarda en Neon a traves
    # del microservicio (igual patron que ver_curiosidades: la vista
    # consume un servicio externo propio).
    mascota = get_object_or_404(Mascota, id=mascota_id)
    mascota.actualizar_por_tiempo()

    resultado = None
    eleccion_pc = None
    monedas_ganadas = 0
    error = None

    if request.method == 'POST':
        eleccion_usuario = request.POST.get('eleccion')
        if eleccion_usuario in OPCIONES_JUEGO:
            eleccion_pc = random.choice(OPCIONES_JUEGO)

            if eleccion_usuario == eleccion_pc:
                resultado = 'empate'
                monedas_ganadas = 2
            elif GANA_A[eleccion_usuario] == eleccion_pc:
                resultado = 'ganaste'
                monedas_ganadas = 10
            else:
                resultado = 'perdiste'
                monedas_ganadas = 0

            if monedas_ganadas > 0:
                _, error = ganar_monedas(mascota.id, monedas_ganadas)

    monedas, error_monedas = obtener_monedas(mascota.id)

    context = {
        'mascota': mascota,
        'resultado': resultado,
        'eleccion_pc': eleccion_pc,
        'monedas_ganadas': monedas_ganadas,
        'monedas': monedas,
        'error': error or error_monedas,
    }
    return render(request, 'mascotas/minijuego.html', context)


# ---------- Administrar curiosidades (CRUD sobre Neon via microservicios) ----------
# Leer: microservicio Node. Insertar / actualizar / eliminar: el usuario elige
# con que lenguaje se ejecuta cada operacion (boton "con Python", "con Node" o "con Java").

NOMBRE_VIA = {'python': 'Python', 'node': 'Node.js', 'java': 'Java'}


def _via(request):
    """Lenguaje elegido por el usuario en el boton que presiono."""
    via = request.POST.get('via')
    return via if via in NOMBRE_VIA else 'python'


def gestionar_curiosidades(request):
    curiosidades, error = listar_curiosidades()
    return render(request, 'mascotas/curiosidades_admin.html',
                  {'curiosidades': curiosidades, 'error': error})


def crear_curiosidad(request):
    error = None
    if request.method == 'POST':
        especie = request.POST.get('especie')
        texto = request.POST.get('texto', '').strip()
        via = _via(request)
        if texto:
            _, error = insertar_curiosidad(especie, texto, via)
            if not error:
                messages.success(request, f"Curiosidad insertada con el microservicio de {NOMBRE_VIA[via]}.")
                return redirect('gestionar_curiosidades')
    return render(request, 'mascotas/curiosidad_form.html', {'especies': ESPECIES, 'error': error})


def editar_curiosidad(request, curiosidad_id):
    error = None
    curiosidad = None

    if request.method == 'POST':
        especie = request.POST.get('especie')
        texto = request.POST.get('texto', '').strip()
        via = _via(request)
        curiosidad = {'id': curiosidad_id, 'especie': especie, 'texto': texto}
        if texto:
            _, error = actualizar_curiosidad(curiosidad_id, especie, texto, via)
            if not error:
                messages.success(request, f"Curiosidad actualizada con el microservicio de {NOMBRE_VIA[via]}.")
                return redirect('gestionar_curiosidades')
    else:
        lista, error = listar_curiosidades()
        curiosidad = next((c for c in lista if c['id'] == curiosidad_id), None)
        if curiosidad is None and not error:
            return redirect('gestionar_curiosidades')

    return render(request, 'mascotas/curiosidad_form.html',
                  {'curiosidad': curiosidad, 'especies': ESPECIES, 'error': error})


def eliminar_curiosidad_vista(request, curiosidad_id):
    # solo por POST, igual que eliminar_mascota
    if request.method == 'POST':
        via = _via(request)
        ok, error = eliminar_curiosidad(curiosidad_id, via)
        if ok:
            messages.success(request, f"Curiosidad eliminada con el microservicio de {NOMBRE_VIA[via]}.")
        else:
            messages.error(request, error)
    return redirect('gestionar_curiosidades')

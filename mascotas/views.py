from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
import requests
from .models import Mascota, ESPECIES


def listar_mascotas(request):
    mascotas = Mascota.objects.all()
    return render(request, 'mascotas/listar.html', {'mascotas': mascotas})


def detalle_mascota(request, mascota_id):
    mascota = get_object_or_404(Mascota, id=mascota_id)
    return render(request, 'mascotas/detalle.html', {'mascota': mascota})


def crear_mascota(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        especie = request.POST.get('especie')
        if nombre:
            Mascota.objects.create(nombre=nombre, especie=especie)
            return redirect('listar_mascotas')
    return render(request, 'mascotas/crear.html', {'especies': ESPECIES})


def alimentar_mascota(request, mascota_id):
    # ruta dinamica: recibe el id de la mascota y le baja el hambre
    mascota = get_object_or_404(Mascota, id=mascota_id)
    mascota.hambre = max(mascota.hambre - 20, 0)
    mascota.save()
    return redirect('detalle_mascota', mascota_id=mascota.id)


def jugar_mascota(request, mascota_id):
    # ruta dinamica: recibe el id de la mascota y le sube la felicidad
    mascota = get_object_or_404(Mascota, id=mascota_id)
    mascota.felicidad = min(mascota.felicidad + 15, 100)
    mascota.hambre = min(mascota.hambre + 5, 100)  # jugar tambien da un poco de hambre
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
    # vista que consulta el modelo (shortcut get_object_or_404) y ademas
    # consulta una IA externa gratuita (Groq) para responder preguntas
    # sobre el cuidado de la mascota
    mascota = get_object_or_404(Mascota, id=mascota_id)

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
                payload = {
                    'model': settings.GROQ_MODEL,
                    'messages': [
                        {
                            'role': 'system',
                            'content': (
                                'Eres un asistente que responde preguntas cortas sobre el '
                                'cuidado de mascotas (alimentacion, juego, bienestar). '
                                f'Estas ayudando con {mascota.nombre}, un/a {mascota.get_especie_display()}. '
                                'Responde en español, en pocas frases.'
                            ),
                        },
                        {'role': 'user', 'content': pregunta},
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

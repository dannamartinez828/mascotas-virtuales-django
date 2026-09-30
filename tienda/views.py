from django.shortcuts import render, redirect, get_object_or_404
from .models import Item, Inventario
from mascotas.models import Mascota  # modelo de otra app, consultado desde aqui
from gestor_mascotas.microservicio_client import obtener_monedas, gastar_monedas


def listar_items(request, mascota_id):
    mascota = get_object_or_404(Mascota, id=mascota_id)
    mascota.actualizar_por_tiempo()
    items = Item.objects.all()
    monedas, error = obtener_monedas(mascota.id)
    context = {'items': items, 'mascota': mascota, 'monedas': monedas, 'error': error}
    return render(request, 'tienda/listar.html', context)


def comprar_item(request, mascota_id, item_id):
    # ruta dinamica con dos parametros: id de mascota e id de item.
    # ya no aplica el efecto de una vez: cobra monedas (guardadas en Neon,
    # via el microservicio) y lo agrega al inventario para usarlo despues.
    mascota = get_object_or_404(Mascota, id=mascota_id)
    item = get_object_or_404(Item, id=item_id)

    ok, saldo, error = gastar_monedas(mascota.id, item.costo)

    if ok:
        inventario, _creado = Inventario.objects.get_or_create(mascota=mascota, item=item)
        inventario.cantidad += 1
        inventario.save()

    return redirect('listar_items', mascota_id=mascota.id)


def ver_inventario(request, mascota_id):
    mascota = get_object_or_404(Mascota, id=mascota_id)
    inventario = Inventario.objects.filter(mascota=mascota, cantidad__gt=0).select_related('item')
    return render(request, 'tienda/inventario.html', {'mascota': mascota, 'inventario': inventario})


def usar_item(request, mascota_id, item_id):
    # usa 1 unidad de un item guardado en el inventario: recien ahi aplica
    # el efecto (sube felicidad, baja hambre) sobre la mascota.
    mascota = get_object_or_404(Mascota, id=mascota_id)
    inventario = get_object_or_404(Inventario, mascota=mascota, item_id=item_id)

    if inventario.cantidad > 0:
        mascota.actualizar_por_tiempo()
        mascota.felicidad = min(mascota.felicidad + inventario.item.precio_felicidad, 100)
        mascota.hambre = max(mascota.hambre - inventario.item.reduce_hambre, 0)
        mascota.registrar_interaccion()
        mascota.save()

        inventario.cantidad -= 1
        inventario.save()

    return redirect('ver_inventario', mascota_id=mascota.id)

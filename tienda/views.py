from django.shortcuts import render, redirect, get_object_or_404
from .models import Item
from mascotas.models import Mascota  # modelo de otra app, consultado desde aqui


def listar_items(request, mascota_id):
    mascota = get_object_or_404(Mascota, id=mascota_id)
    items = Item.objects.all()
    return render(request, 'tienda/listar.html', {'items': items, 'mascota': mascota})


def comprar_item(request, mascota_id, item_id):
    # ruta dinamica con dos parametros: id de mascota e id de item
    mascota = get_object_or_404(Mascota, id=mascota_id)
    item = get_object_or_404(Item, id=item_id)

    mascota.felicidad = min(mascota.felicidad + item.precio_felicidad, 100)
    mascota.hambre = max(mascota.hambre - item.reduce_hambre, 0)
    mascota.save()

    return redirect('detalle_mascota', mascota_id=mascota.id)

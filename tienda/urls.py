from django.urls import path
from . import views

urlpatterns = [
    path('<int:mascota_id>/', views.listar_items, name='listar_items'),
    path('<int:mascota_id>/comprar/<int:item_id>/', views.comprar_item, name='comprar_item'),
    path('<int:mascota_id>/inventario/', views.ver_inventario, name='ver_inventario'),
    path('<int:mascota_id>/usar/<int:item_id>/', views.usar_item, name='usar_item'),
]

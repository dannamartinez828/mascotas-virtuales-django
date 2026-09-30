from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_mascotas, name='listar_mascotas'),
    path('crear/', views.crear_mascota, name='crear_mascota'),
    path('<int:mascota_id>/editar/', views.editar_mascota, name='editar_mascota'),
    path('<int:mascota_id>/eliminar/', views.eliminar_mascota, name='eliminar_mascota'),
    path('<int:mascota_id>/', views.detalle_mascota, name='detalle_mascota'),
    path('<int:mascota_id>/alimentar/', views.alimentar_mascota, name='alimentar_mascota'),
    path('<int:mascota_id>/jugar/', views.jugar_mascota, name='jugar_mascota'),
    path('<int:mascota_id>/curiosidades/', views.ver_curiosidades, name='ver_curiosidades'),
    path('<int:mascota_id>/preguntar-ia/', views.preguntar_ia, name='preguntar_ia'),
    path('<int:mascota_id>/minijuego/', views.jugar_minijuego, name='jugar_minijuego'),

    # CRUD de curiosidades sobre Neon (no depende de una mascota puntual)
    path('curiosidades/admin/', views.gestionar_curiosidades, name='gestionar_curiosidades'),
    path('curiosidades/admin/crear/', views.crear_curiosidad_view, name='crear_curiosidad'),
    path('curiosidades/admin/<int:curiosidad_id>/editar/', views.editar_curiosidad_view, name='editar_curiosidad'),
    path('curiosidades/admin/<int:curiosidad_id>/eliminar/', views.eliminar_curiosidad_view, name='eliminar_curiosidad'),
]

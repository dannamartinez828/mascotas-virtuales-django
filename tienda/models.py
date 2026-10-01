from django.db import models
from mascotas.models import Mascota  # modelo de otra app, se reutiliza aqui


class Item(models.Model):
    nombre = models.CharField(max_length=50)
    precio_felicidad = models.IntegerField(help_text="Cuanta felicidad da")
    reduce_hambre = models.IntegerField(help_text="Cuanto hambre quita")
    costo = models.IntegerField(default=10, help_text="Costo en monedas del minijuego")
    emoji = models.CharField(max_length=5, default='🎁')

    def __str__(self):
        return self.nombre


class Inventario(models.Model):
    """Lo que cada mascota tiene guardado (comprado pero no usado todavia)."""
    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE, related_name='inventario')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=0)

    class Meta:
        unique_together = ('mascota', 'item')

    def __str__(self):
        return f"{self.mascota.nombre}: {self.cantidad}x {self.item.nombre}"

from django.db import models


class Item(models.Model):
    nombre = models.CharField(max_length=50)
    precio_felicidad = models.IntegerField(help_text="Cuanta felicidad da")
    reduce_hambre = models.IntegerField(help_text="Cuanto hambre quita")
    emoji = models.CharField(max_length=5, default='🎁')

    def __str__(self):
        return self.nombre

from django.db import models

ESPECIES = (
    ('perro', 'Perro'),
    ('gato', 'Gato'),
    ('dragon', 'Dragón'),
    ('robot', 'Robot'),
)


class Mascota(models.Model):
    nombre = models.CharField(max_length=50)
    especie = models.CharField(max_length=20, choices=ESPECIES, default='perro')
    hambre = models.IntegerField(default=50)      # 0 = lleno, 100 = muriendo de hambre
    felicidad = models.IntegerField(default=50)   # 0 = triste, 100 = feliz
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def esta_bien(self):
        return self.hambre < 70 and self.felicidad > 30

    def __str__(self):
        return f"{self.nombre} ({self.especie})"

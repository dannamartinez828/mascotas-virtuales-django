from django.db import models
from django.utils import timezone

ESPECIES = (
    ('perro', 'Perro'),
    ('gato', 'Gato'),
    ('dragon', 'Dragón'),
    ('robot', 'Robot'),
)

# emoji de cada especie para la interfaz, y la lista (valor, nombre, emoji)
# que usan los formularios de crear/editar
ESPECIES_EMOJI = {'perro': '🐶', 'gato': '🐱', 'dragon': '🐲', 'robot': '🤖'}
ESPECIES_UI = [(valor, nombre, ESPECIES_EMOJI[valor]) for valor, nombre in ESPECIES]

# cada cuantos SEGUNDOS sin interactuar se le sube el hambre / baja la felicidad.
# pensado para que en una demo en vivo se note el cambio en unos 15-20 segundos,
# sin que sea tan rapido que se vea descontrolado.
SEGUNDOS_POR_CICLO = 10
HAMBRE_POR_CICLO = 7
FELICIDAD_POR_CICLO = 5


class Mascota(models.Model):
    nombre = models.CharField(max_length=50)
    especie = models.CharField(max_length=20, choices=ESPECIES, default='perro')
    hambre = models.IntegerField(default=50)      # 0 = lleno, 100 = muriendo de hambre
    felicidad = models.IntegerField(default=50)   # 0 = triste, 100 = feliz
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_interaccion = models.DateTimeField(default=timezone.now)

    @property
    def emoji(self):
        return ESPECIES_EMOJI.get(self.especie, '🐾')

    def esta_bien(self):
        return self.hambre < 70 and self.felicidad > 30

    def actualizar_por_tiempo(self):
        """Si paso tiempo desde la ultima vez que se toco esta mascota,
        le sube el hambre y le baja la felicidad (se van deteriorando solas,
        como en un tamagotchi). Se llama cada vez que se muestra la mascota."""
        ahora = timezone.now()
        segundos_pasados = (ahora - self.ultima_interaccion).total_seconds()
        ciclos = int(segundos_pasados // SEGUNDOS_POR_CICLO)

        if ciclos > 0:
            self.hambre = min(self.hambre + ciclos * HAMBRE_POR_CICLO, 100)
            self.felicidad = max(self.felicidad - ciclos * FELICIDAD_POR_CICLO, 0)
            self.ultima_interaccion = ahora
            self.save()

    def registrar_interaccion(self):
        """Reinicia el contador de tiempo cada vez que el usuario hace algo
        (alimentar, jugar, comprar) para que el deterioro cuente desde ahi."""
        self.ultima_interaccion = timezone.now()

    def __str__(self):
        return f"{self.nombre} ({self.especie})"

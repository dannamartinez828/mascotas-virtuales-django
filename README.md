# Mascotas Virtuales - Django

App de mascotas virtuales tipo tamagotchi. Problema que resuelve: una forma
simple y entretenida de tomar un descanso mientras se cuida a una mascota
digital (alimentarla, jugar con ella y comprarle cosas en la tienda).

## Apps del proyecto

- **mascotas**: crear mascotas, verlas, alimentarlas, jugar con ellas y ver curiosidades.
- **tienda**: comprar items que suben la felicidad y bajan el hambre de una mascota.

## Deterioro por tiempo

Las mascotas no se quedan estáticas: si no interactúas con una, cada 10
minutos sin tocarla le sube el hambre +5 y le baja la felicidad -3 (topes
0-100). Esto se calcula solo, sin cron ni tareas en segundo plano — el
modelo `Mascota` guarda `ultima_interaccion`, y cada vez que se carga una
vista donde aparece esa mascota (listar, detalle, tienda) se llama
`mascota.actualizar_por_tiempo()`, que revisa cuánto tiempo pasó y aplica
el deterioro correspondiente antes de mostrarla. Alimentar, jugar o
comprarle algo reinicia ese contador.

## Microservicio (Node.js + Neon)

La vista `ver_curiosidades` (app mascotas) consume un microservicio propio,
ubicado en `../microservicio/`, escrito en Node.js/Express, pensado para
desplegarse en Render y que consulta una base de datos PostgreSQL en Neon
(distinta al SQLite que usa Django). Instrucciones de despliegue completas
en `../microservicio/README.md`.

## Requisitos que cumple

- Shortcuts de Django: `render()` y `get_object_or_404()` en todas las vistas.
- Patron visto en clase: la vista consulta el modelo (Mascota / Item) y arma
  un `context` que se le pasa al template.
- Multiples vistas en una app (listar, detalle, crear, alimentar, jugar, curiosidades).
- Multiples apps en un proyecto (mascotas y tienda).
- Modelos consultados desde las vistas, incluso Mascota se consulta desde
  las vistas de la app tienda.
- Rutas dinamicas con parametros: `/mascotas/<id>/`, `/mascotas/<id>/alimentar/`,
  `/mascotas/<id>/curiosidades/`, `/tienda/<mascota_id>/comprar/<item_id>/`.
- Una vista (`ver_curiosidades`) consume un microservicio propio desplegado
  en la nube que a su vez consulta una base de datos en la nube (Neon).
- Una vista (`preguntar_ia`) consulta una IA externa gratuita (Groq) para
  responder preguntas sobre el cuidado de la mascota, usando datos REALES
  de la base de datos (hambre, felicidad, monedas e items de la tienda) en
  vez de respuestas genericas.
- El microservicio (`../microservicio/`) expone documentación interactiva
  Swagger en `/api-docs`.
- CRUD completo de Mascota: Crear (`crear_mascota`), Leer (`listar_mascotas`,
  `detalle_mascota`), Actualizar (`editar_mascota`) y Eliminar
  (`eliminar_mascota`), todo con formularios HTML. Este CRUD guarda en el
  SQLite local de Django.
- CRUD completo de Curiosidades (`gestionar_curiosidades`, `crear_curiosidad`,
  `editar_curiosidad`, `eliminar_curiosidad`), tambien con formularios HTML,
  pero este SI modifica la base de datos en la nube: cada Crear/Editar/
  Eliminar llama al microservicio, que ejecuta el INSERT/UPDATE/DELETE
  directamente sobre la tabla `curiosidades` en Neon. Se accede desde
  "Administrar curiosidades" en la pagina principal.

## IA externa (Groq, gratuita)

La vista `preguntar_ia` usa la API de Groq (https://console.groq.com),
compatible con el formato de chat completions de OpenAI y con capa
gratuita. Pasos:

1. Crear cuenta en https://console.groq.com y generar una API key.
2. Definir la variable de entorno `GROQ_API_KEY` antes de correr el
   servidor:
   ```bash
   export GROQ_API_KEY=tu_api_key   # Windows: set GROQ_API_KEY=tu_api_key
   ```
3. Si no se define, la vista muestra un mensaje de error controlado en
   vez de fallar.

## Como correr la app Django (Windows)

```bat
cd app
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

:: (opcional) apuntar al microservicio ya desplegado en Render
:: set MICROSERVICIO_URL=https://tu-servicio.onrender.com

:: (opcional) habilitar la IA de Groq
:: set GROQ_API_KEY=tu_api_key

python manage.py runserver
```

Abrir http://127.0.0.1:8000/ en el navegador.

Ya viene una mascota de ejemplo llamada "Firu" y 3 items en la tienda
(Croqueta, Pelota, Pastel). Se pueden crear mas mascotas desde el boton
"Adoptar una nueva mascota", y mas items desde /admin/ (usuario admin no
creado, correr `python manage.py createsuperuser` si se necesita).

Si `MICROSERVICIO_URL` no esta definida, la app intenta contactar
`http://localhost:3000` y, si no lo encuentra corriendo, la vista de
curiosidades simplemente muestra un mensaje de error controlado (no se cae
la app).


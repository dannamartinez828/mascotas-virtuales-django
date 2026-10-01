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
  (`eliminar_mascota`), todo con formularios HTML.

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

## Publicar la app Django en Render (para que el link sea verificable)

Se usa Render en vez de PythonAnywhere porque las cuentas gratis de
PythonAnywhere solo pueden llamar a un numero limitado de sitios externos
("whitelist"), lo que rompe las llamadas a Groq y al microservicio. Render
no tiene esa restriccion y ya se usa para el microservicio.

<<<<<<< HEAD
### 1. Reusar la misma base de datos de Neon del microservicio

No hace falta crear un proyecto de Neon nuevo: Django va a crear sus
propias tablas (`mascotas_mascota`, `tienda_item`, etc.) dentro de la
**misma base de datos** que ya usa el microservicio, y no chocan con
`curiosidades` ni `monedas` porque son nombres distintos.

Solo se reusa el mismo **Connection string** de Neon que ya usaste en el
`.env` del microservicio (dashboard de Neon → Connection Details). Se
usa tal cual en el paso 3.
=======
### 1. Crear una base de datos Postgres en Neon para Django

Igual que el microservicio, pero un proyecto de Neon **separado** (para no
mezclar las tablas de Django con las de `curiosidades`/`monedas`):

1. Crear un proyecto nuevo en https://neon.tech.
2. Copiar su **Connection string** (se usa en el paso 3).
>>>>>>> 67e04a29ca1c5064599473b122e60bcb1cfff31a

### 2. Subir la carpeta `app` a GitHub

Igual que se hizo con el microservicio:
```bash
cd app
git init
git add .
git commit -m "Primera version de la app Django"
git branch -M main
git remote add origin https://github.com/tu-usuario/mascotas-virtuales-django.git
git push -u origin main
```

### 3. Crear el Web Service en Render

1. En Render: **New +** → **Web Service** → elegir el repo
   `mascotas-virtuales-django`.
2. Configurar:

| Campo | Valor |
|---|---|
| Runtime | Python |
| Build Command | `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate` |
| Start Command | `gunicorn gestor_mascotas.wsgi` |
| Instance Type | Free |

3. En **Environment Variables** agregar:

| Key | Value |
|---|---|
| `SECRET_KEY` | cualquier texto largo y aleatorio (no uses el que trae el proyecto por defecto) |
| `DJANGO_DEBUG` | `False` |
<<<<<<< HEAD
| `DATABASE_URL` | el mismo connection string de Neon que usa el microservicio |
=======
| `DATABASE_URL` | el connection string de Neon del paso 1 |
>>>>>>> 67e04a29ca1c5064599473b122e60bcb1cfff31a
| `MICROSERVICIO_URL` | la URL del microservicio ya desplegado (ej. `https://microservicio-curiosidades.onrender.com`) |
| `GROQ_API_KEY` | tu key de Groq |

4. **Create Web Service**. Cuando termine, Render da una URL publica
   (ej. `https://mascotas-virtuales.onrender.com`) — esa es la que se
   comparte para que la verifiquen.

Como `python manage.py migrate` esta en el Build Command, las tablas se
crean solas en Neon la primera vez. Para tener datos de ejemplo (la
mascota "Firu" y los items de la tienda), entrar una vez a
`https://tu-app.onrender.com/admin/` (creando antes un superusuario con
`python manage.py createsuperuser` desde el Shell de Render, pestaña
"Shell" del servicio) o simplemente usar los formularios de la app para
crearlos a mano.


## 🚀 Guía de Instalación para Colaboradores

Asumo que ya has subido el código a un repositorio Git (como GitHub).

### 1\. 💾 Clonar el Repositorio

Tu colaborador debe clonar el código y moverse al directorio del proyecto:

```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_PROYECTO>
```

### 2\. 🐍 Configurar el Entorno Virtual

Deben crear y activar su propio entorno virtual para aislar las dependencias:

```bash
# Crear entorno virtual (solo la primera vez)
python -m venv venv

# Activar el entorno virtual (PowerShell en Windows)
.\venv\Scripts\activate
```

### 3\. 📦 Instalar Dependencias de Python

Tu colaborador necesita instalar todos los paquetes Python listados en tu archivo `requirements.txt` (debes generarlo antes):

```bash
# El colaborador instala:
pip install -r requirements.txt

# Si aún no tienes un requirements.txt, ejecútalo en tu máquina:
# pip freeze > requirements.txt
```

-----

## 🔑 Configuración de Claves y Base de Datos

Esta es la parte más crítica, ya que maneja la conexión a servicios externos y la base de datos.

### 4\. 📝 Crear el Archivo `.env`

-----

#### 📝 Paso 1: Crear el Archivo `.env`

Primero, crear un archivo de texto llamado **`.env`** en la raíz del proyecto (al lado de `manage.py` y `.gitignore`).

##### 1\. **`DB_ENGINE` (Motor de Base de Datos)**

Esta variable es estática y define el adaptador que Django usará.

```env
DB_ENGINE=django.db.backends.postgresql
```

-----

#### 🔑 Paso 2: Generar Claves Secretas y API

Estas variables son únicas para la seguridad del proyecto y la conexión con la IA.

##### 2\. **`SECRET_KEY` (Clave de Seguridad de Django)**

Esta clave es crítica para la seguridad criptográfica de Django y **debe ser única** para cada entorno (aunque para desarrollo se puede usar la misma, es buena práctica que cada uno la genere).

**Cómo Generarla (Recomendado):**

1.  Abre la terminal (con el `(venv)` activo).
2.  Abre el intérprete de Python:
    ```bash
    (venv) PS C:\Users\User\Desktop\Testeador> python
    ```
3.  Ejecuta estos comandos en la sesión de Python para obtener una clave aleatoria:
    ```python
    >>> from django.core.management.utils import get_random_secret_key
    >>> print(get_random_secret_key())
    ```
4.  Copia la clave larga generada e insértala en tu `.env`:

<!-- end list -->

```env
SECRET_KEY='LA_LARGA_CLAVE_GENERADA_AQUÍ'
```

##### 3\. **`OPENROUTER_API_KEY` (Clave de la IA)**

Esta clave permite la facturación y el acceso a los modelos de IA.

**Cómo Obtenerla:**

1.  Ir al sitio de **OpenRouter**.
2.  Iniciar sesión y dirigirse a la sección de configuración de API Keys.
3.  Generar una nueva clave.

<!-- end list -->

```env
OPENROUTER_API_KEY='COPIA_LA_CLAVE_DE_OPENROUTER_AQUÍ'
```

-----

#### 🐘 Paso 3: Configurar Credenciales de PostgreSQL

##### 4\. **`DB_NAME`, `DB_USER`, `DB_PASSWORD`**

**Cómo Configurar (Asumiendo que ya instalaron PostgreSQL):**

1.  En **pgAdmin**, deben verificar el **Nombre de la Base de Datos** que crearon para el proyecto (Ej: `testeador_db`).
2.  Deben verificar el **Nombre de Usuario** y la **Contraseña** que crearon para acceder a esa base de datos (Ej: `testeador_user`).
3.  El puerto es generalmente **5432**.

<!-- end list -->

```env
# Credenciales de PostgreSQL creadas localmente
DB_NAME=testeador_db
DB_USER=usuario
DB_PASSWORD='La_Contraseña_que_crearon_en_pgAdmin'
DB_HOST=localhost
DB_PORT=5432
```

-----

#### 📑 Contenido Final del Archivo `.env`

El archivo `.env` completo (con valores de ejemplo) debe verse así:

```env
# Seguridad y Claves
SECRET_KEY='x5!tq@#q34-2e&g-t*3e9v4t!m_q&9x$y5i0t&e9g2d7n0r-l'
OPENROUTER_API_KEY='sk-or-v1-a1b2c3d4-e5f6g7h8i9j0k1l2m3n4o5p6'
YOUR_SITE_URL="http://localhost:8000"
YOUR_SITE_NAME="Testeador-SaaS-Dev"
DEBUG=True

# Configuración de PostgreSQL local
DB_ENGINE=django.db.backends.postgresql
DB_NAME=testeador_db
DB_USER=usuario
DB_PASSWORD='La_Contraseña_que_crearon_en_pgAdmin'
DB_HOST=localhost
DB_PORT=5432
```

### 5\. 🐘 Instalar y Configurar PostgreSQL

Tus colaboradores deben seguir los mismos pasos que tú para instalar PostgreSQL y configurar un usuario y una base de datos localmente.

  * Deben crear una base de datos local (ej: `testeador_db`).
  * Deben crear un usuario local (ej: `usuario`).
  * Las credenciales de este usuario y la base de datos son las que se colocan en su archivo **`.env`**.

-----

## 🚀 Ejecución Final

Con el entorno virtual activado y el archivo `.env` configurado, ellos ya pueden inicializar el proyecto:

1.  **Aplicar Migraciones:** (Esto crea las tablas en su base de datos local de PostgreSQL)

    ```bash
    python manage.py migrate
    ```

2.  **Crear Superusuario:** (Para acceder al `/admin/` de su entorno local)

    ```bash
    python manage.py createsuperuser
    ```

3.  **Iniciar el Servidor:**

    ```bash
    python manage.py runserver
    ```

Una vez hecho todo esto iremos al navegador y accederemos a [http://127.0.0.1/admin/](http://127.0.0.1/admin/) donde nos pedirán las credenciales del super usuario y ya podremos empezar a utilizar la API.

----
-----
-------

## 🛠️ Prerrequisitos

1.  **Servidor Activo:** Tu servidor Django debe estar corriendo en la terminal (`python manage.py runserver`).
2.  **Usuario Listo:** Has creado el Superusuario en PostgreSQL y lo has asociado a una **Entidad** en `http://127.0.0.1:8000/admin/` (mediante un `EntityProfile`).

-----

## 🔑 Paso 1: Obtener las Cookies (Autenticación)

Para simular un usuario logueado en Postman, necesitamos las cookies de sesión y CSRF.

1.  **Abre el Admin:** Ve a `http://127.0.0.1:8000/admin/` en tu navegador e **inicia sesión** con tu superusuario.
2.  **Captura las Cookies:** Abre las herramientas de desarrollador del navegador (F12), ve a la pestaña **Aplicación** \> **Almacenamiento** \> **Cookies**.
3.  **Copia los Valores:** Copia los valores de **`sessionid`** y **`csrftoken`**.

-----

## 🚀 Fase 1: Iniciar el Test (`/api/test/<test_id>/initiate/`)

Esta petición crea el registro de ejecución y obtiene la primera respuesta de la IA.

1.  **Crea una nueva petición** en Postman.

2.  **Método y URL:**

      * Método: `POST`
      * URL: `http://127.0.0.1:8000/api/test/1/initiate/` (Asumiendo que creaste un **Test con ID 1**).

3.  **Headers (Autenticación):** Ve a la pestaña **Headers** y añade (o verifica) estas dos claves:

      * `Key`: `Cookie` | `Value`: `sessionid=<TU_SESSIONID>; csrftoken=<TU_CSRFTOKEN>`
      * `Key`: `X-CSRFToken` | `Value`: `<TU_CSRFTOKEN>`

4.  **Body (Contenido):** Ve a la pestaña **Body**, selecciona `raw`, y elige **JSON**. Simula el primer mensaje del candidato:

    ```json
    {
        "message": "Hola, estoy listo para iniciar la evaluación."
    }
    ```

5.  **Enviar:** Presiona **Send**.

      * **Resultado Esperado:** `Status: 200 OK`. Recibirás un JSON con el **`execution_id`** (ej: `2`) y la primera pregunta de la IA.
      * **¡ANOTA\!** Guarda el valor del **`execution_id`**.

-----

## 🔄 Fase 2: Continuar el Test (`/api/test/<execution_id>/continue/`)

Simula la respuesta del candidato para avanzar la conversación.

1.  **Crea una nueva petición** en Postman.

2.  **Método y URL:**

      * Método: `POST`
      * URL: `http://127.0.0.1:8000/api/test/<EXECUTION_ID>/continue/` (Reemplaza con el ID de la Fase 1, ej: `/api/test/2/continue/`).

3.  **Headers:** Reutiliza los mismos `Cookie` y `X-CSRFToken` de la Fase 1.

4.  **Body:** Selecciona `raw` y **JSON**. Responde a la pregunta de la IA:

    ```json
    {
        "message": "El principal desafío fue la desmotivación del equipo, lo abordé con reuniones uno a uno y objetivos claros."
    }
    ```

5.  **Enviar:** Presiona **Send**.

      * **Resultado Esperado:** `Status: 200 OK`. Recibirás la **siguiente pregunta** o comentario de la IA.
      * **Verificación:** Confirma en **pgAdmin** que el registro de la ejecución ID 2 en la tabla `core_testexecution` tiene el **`chat_log`** actualizado.

-----

## ✅ Fase 3: Finalizar y Evaluar (`/api/test/<execution_id>/finish/`)

Esto activa la lógica de evaluación final de la IA y marca el test como completado (crucial para la facturación).

1.  **Crea una nueva petición** en Postman.

2.  **Método y URL:**

      * Método: `POST`
      * URL: `http://127.0.0.1:8000/api/test/<EXECUTION_ID>/finish/` (Ej: `/api/test/2/finish/`).

3.  **Headers:** Reutiliza los mismos *headers* de autenticación.

4.  **Body:** Esta petición **no necesita** cuerpo (`Body`).

5.  **Enviar:** Presiona **Send**.

      * **Resultado Esperado:** `Status: 200 OK`. Recibirás un JSON con el campo **`results`**, que contiene el JSON estructurado de la evaluación final (puntuaciones y resumen).
      * **Verificación Final:** En **pgAdmin**, el registro ID 2 en la tabla `core_testexecution` debe tener el campo **`finish_time`** y **`evaluation_result`** rellenados con el JSON de la evaluación.

¡Con estos pasos, habrás comprobado el flujo completo de tu API de principio a fin\! ¿Hay alguna de estas fases en la que necesites ayuda específica o quieres pasar a configurar la autenticación por Tokens?
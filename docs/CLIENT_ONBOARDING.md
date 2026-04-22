# ReachRate — Guía de puesta en marcha

> Documento para el **operador** — la persona del cliente que usa ReachRate
> todos los días. Asume cero conocimiento de programación.

---

## 🎯 ¿Qué hace este sistema?

Es un asistente automatizado que:

1. **Busca negocios** de un rubro específico en la ciudad que elijas (ej: "estudios de abogados en Palermo").
2. **Analiza cada web** y detecta qué tipo de formulario de contacto tienen (form simple, chat tipo Intercom, agenda tipo Calendly).
3. **Espera respuestas** cuando les escribís vía formulario / SMS / WhatsApp / email.
4. **Arma una lista priorizada** cada lunes con los que **más tardan en responder** — son tus mejores prospectos.

**En criollo**: te genera automáticamente la lista de a quién llamar primero para venderles.

---

## 🚀 Instalación — elegí tu camino

### Opción A — La más simple: hosteado en la nube (Railway)

Recomendado para operadores no técnicos. Railway ofrece $5/mes de crédito
gratis que cubre este uso tranquilo.

1. Tocá este botón:

   [![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/new/deploy?template=https%3A%2F%2Fgithub.com%2Fjuan-alejo%2Freachrate)

2. Railway te pide loguearte con tu cuenta de Google o GitHub (sin tarjeta).
3. En ~2 minutos te genera una URL tipo `https://tu-nombre.up.railway.app`.
4. Abrís esa URL en el navegador → ¡ya está corriendo!
5. Vas al tab **Configuración** adentro del dashboard y pegás tus API keys
   cuando quieras usar datos reales.

### Opción B — Corriendo en tu propia computadora (Docker)

Si preferís tener todo local, con Docker es 2 comandos:

```bash
# Clonás el repo
git clone https://github.com/juan-alejo/reachrate.git
cd reachrate

# Arrancás el contenedor
docker compose up -d

# Abrís http://localhost:8501 en el navegador
```

Para detenerlo: `docker compose down`.

### Opción C — Corriendo directamente con Python (para devs)

```bash
git clone https://github.com/juan-alejo/reachrate.git
cd reachrate
python -m venv .venv
.venv/Scripts/activate      # Windows
# source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
playwright install chromium
streamlit run src/dashboard/app.py
```

---

## 👣 Tu primer uso — 3 pasos en 5 minutos

Una vez que abras el dashboard por primera vez:

### Paso 1 — Correr la demo

En la pantalla principal vas a ver un botón grande que dice
**"🚀 Correr búsqueda de demo (30 segundos)"**.

Tocalo. En ~30 segundos vas a ver:
- Se llenan los 4 contadores de arriba (Clientes potenciales, Contactos, etc).
- Aparecen datos en los tabs **Lista prioritaria**, **Estadísticas**, **Herramientas que usan**.

**Estos son datos de ejemplo** — simulados para que veas cómo funciona.

### Paso 2 — Mirar los resultados

Click a cada tab para familiarizarte:

- **🎯 Lista prioritaria** — los negocios ordenados de peor a mejor respondedor. Acá está el oro.
- **📊 Estadísticas** — ¿qué rubros en general responden lento? Eso te dice qué nichos atacar.
- **🕵 Herramientas que usan** — qué chat / agenda tiene instalado cada negocio. Útil para calibrar el pitch ("te integro con Calendly" vs "te reemplazo Intercom").
- **🗂 Datos detallados** — debug. Útil si algo se ve raro.

### Paso 3 — Configurar tus APIs reales

Cuando quieras salir del modo demo:

1. Click en el tab **⚙ Configuración**.
2. Apagá el **Modo demo** (toggle arriba a la derecha).
3. Se desbloquean las secciones de cada servicio. Abrís la que necesites.
4. Pegás tu API key.
5. Cambiás el modo a **"🌐 Real"**.
6. Opcional: tocás **🔌 Probar conexión** para verificar que funciona.

**Los cambios se guardan automáticamente** — no hay botón de guardar.

---

## 🌐 Qué APIs vas a necesitar (y cuánto cuestan)

| Servicio | Qué hace | Costo real | ¿Obligatorio? |
|---|---|---|---|
| **Google Places** | Encuentra negocios | Free ($200/mes de crédito gratis) | Sí, si querés búsquedas automáticas |
| **Anthropic (Claude)** | Clasifica los sitios con IA | $5 gratis + ~$1-2/semana | No (funciona sin IA con reglas regex) |
| **Twilio** | Recibe SMS y llamadas | $1/mes + ~$0.01 por SMS | Solo si tus clientes son EE.UU./Canadá/Europa |
| **WhatsApp (vía Twilio)** | Recibe WhatsApp | Free en sandbox; $5/mes en producción | **Imprescindible para LatAm** |
| **Gmail API** | Recibe respuestas por email | Gratis | Sí |
| **Airtable** | Base de datos compartida | Free tier alcanza | Opcional (tenés SQLite local) |

**Para empezar sin gastar nada:**
- Google Places: alcanza el free tier
- Anthropic: alcanzan los $5 de crédito inicial
- WhatsApp Sandbox: gratis para desarrollo
- Gmail: gratis
- Airtable: free plan alcanza

**Costo total mensual realista para un cliente pequeño**: ~$5-10 USD.

---

## 🔄 El ciclo semanal típico

Una vez configurado, tu flujo normal es:

**Lunes a la mañana** (o cualquier día):
1. Abrís el dashboard.
2. Mirás la **Lista prioritaria** — ahí están los prospectos de la semana.
3. Descargás el **CSV** filtrado con los que te interesan.
4. Los cargás en tu CRM / planilla y empezás a contactarlos.

**A lo largo de la semana**:
- Tu equipo llena formularios manualmente en las webs de los prospectos.
- Las respuestas (SMS, WhatsApp, email) van llegando a los buzones conectados.
- El sistema las asocia automáticamente a cada submission.

**Próximo lunes**:
- Dashboard regenera la lista con los datos nuevos.
- Los que no respondieron siguen arriba → clientes calientes para seguir insistiéndo.

---

## 🆘 Preguntas frecuentes

**¿Qué pasa si no tengo tarjeta de crédito para Google?**
Podés desactivar el servicio de Google Places en Configuración y cargar los
negocios manualmente (via CSV). El resto del sistema funciona igual.

**¿Tengo que tener un número de Twilio?**
Solo si querés recibir SMS o llamadas. Para clientes LatAm alcanza con
WhatsApp (que también se configura vía Twilio, pero el sandbox es gratis).

**¿Los datos son seguros?**
Las API keys se guardan en un archivo local `.env` que nunca se sube a
ningún servidor externo. La base de datos (prospectos, respuestas) también
vive en tu máquina o servidor propio.

**¿Cómo hago backup de mi configuración?**
Tab **⚙ Configuración → 🛠 Acciones rápidas → ⬇ Exportar configuración**.
Te descarga un JSON con todo. Para restaurarlo usás **⬆ Importar configuración**.

**¿Puedo agregar un tipo de negocio nuevo?**
Sí, desde **Configuración → 🎯 Tipos de negocio**. Editás la tabla,
escribís "dentistas / Dentista / dentista" (por ejemplo) y se guarda solo.

**¿Cómo cambio el idioma?**
Panel lateral izquierdo (ícono "›" arriba) → selector de idioma.

---

## 📞 Soporte

Si algo no funciona o querés customizar algo que no está en la
configuración, contactá al integrador que te vendió el sistema.

**Repo con el código fuente**:
https://github.com/juan-alejo/reachrate

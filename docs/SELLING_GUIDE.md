# Guía de venta — cómo posicionar y entregar esto a clientes

> Documento interno. NO publicar en la versión pública del repo si alguna
> sección la considerás "jugo secreto". Para tu referencia al escribir
> propuestas y armar pitches.

---

## 🎯 ¿Quién es el cliente ideal?

**Empresas B2B que venden productos de automatización de respuestas** a
negocios locales. Específicamente:

- **Plataformas de chatbots / live chat** (Intercom, Drift, Intaker,
  JuvoLeads y su competencia)
- **Herramientas de intake automatizado para profesionales** (Lawmatics,
  Clio, PracticePanther)
- **Booking widgets** (Calendly, Acuity y competencia de nicho)
- **CRMs con features de response automation** (HubSpot, Zoho, etc.)
- **Agencias de lead gen** que venden listas calificadas a otras empresas
- **Consultoras de AI-for-SMBs** que implementan automatizaciones a PyMEs

**No es para:** usuarios finales directos (abogados, peluquerías, dentistas).
Esos son los **prospects** del cliente, no el cliente.

## 💬 El pitch en 30 segundos

> "Construí una herramienta que automatiza el trabajo más tedioso de
> ventas B2B: encontrar prospectos que respondan lento. Busca negocios
> en Google Places, analiza sus webs, les llena formularios de prueba,
> mide tiempos de respuesta, y te entrega todos los lunes una lista
> ordenada de peores respondedores — tus mejores clientes.
>
> Todo desde un dashboard que cualquiera en tu equipo puede usar sin
> ayuda técnica. Lo puedo configurar para tu vertical y geografía en
> 1-2 días."

## 🎁 Qué le entregás al cliente

Por el precio de setup (~$500-800 USD fijo), el cliente recibe:

1. **Instancia corriendo** — en Railway / Render / su propia infra
2. **URL de acceso** — su equipo entra y usa
3. **Onboarding call de 30-60 min** — walkthrough del dashboard
4. **API keys configuradas** — con sus cuentas, no las tuyas
5. **Documento** [`CLIENT_ONBOARDING.md`](./CLIENT_ONBOARDING.md) traducido
   y personalizado con el nombre de su empresa
6. **2 semanas de soporte** por bugs post-entrega
7. **Configuración de 3-5 verticals específicos** de su industria

Por el precio mensual ($100-200/mes):

1. **Monitoreo del cron semanal** — que funcione todos los lunes
2. **Ajustes menores** — agregar un vertical, cambiar una query
3. **Bug fixes** cuando las APIs cambien (Twilio, Google, Claude actualizan
   contratos a veces)
4. **Soporte por email/WhatsApp** con SLA de 24h

## 💰 Estructura de precios sugerida

### Tier 1 — Setup básico ($500 USD one-time)

- Deploy en Railway con la cuenta del cliente
- Configuración de 3 verticals
- Modo Gmail + WhatsApp (sin Twilio SMS)
- 30 min de onboarding call
- 1 semana de soporte

### Tier 2 — Setup completo ($800 USD one-time)

- Todo lo del Tier 1
- +Airtable integration configurada
- +5-7 verticals
- +Todos los canales (SMS, voice, WhatsApp, email)
- +60 min de onboarding + training con su equipo
- 2 semanas de soporte

### Tier 3 — White-glove ($1200 USD one-time + $200/mes)

- Todo lo del Tier 2
- +Customización visual del dashboard (logo, colores del cliente)
- +Integración con su CRM existente (HubSpot / Salesforce via Zapier)
- +Retainer mensual de mantenimiento
- SLA 24h por email

## 📝 Template de propuesta para Upwork

```
Hi [Client Name],

I saw your posting for [lead generation / sales automation / similar].

I built a system that automates exactly this: it discovers prospect
businesses via Google Places, measures how slowly they respond to
inbound inquiries across SMS / WhatsApp / email, and produces a weekly
priority list sorted by worst responders — which is the cohort most
likely to convert for a response-automation product.

It's already working. Full source + demo screenshots:
https://github.com/juan-alejo/lead-response-intelligence

What I'd build for you:
- Deploy a custom instance on your infrastructure
- Configure the verticals and geography you target
- Wire up your Google Places / Twilio / Gmail / Airtable credentials
- Train your team (1 call, ~60 min)

Timeline: 3-5 business days from kickoff.
Fixed price: $[XXX].

One question before I bid: [pick ONE from the brief they wrote,
showing you read carefully].

Best,
Juan Alejo
```

**Regla de oro**: los clientes que publican specs detallados (como el
"Python Developer to Build Web Form Audit" que inspiró este proyecto)
explícitamente rechazan propuestas genéricas. Siempre incluí una
pregunta específica sobre su brief.

## 🔍 Demo tips

Cuando le mostrás el dashboard a un prospect:

1. **Siempre** arrancás en **modo demo** (amarillo). No les muestres las
   keys reales — ni las tuyas ni las de tu otro cliente.
2. Tocá **Correr búsqueda de demo** en vivo. Los 30 segundos de spinner
   se sienten "real".
3. Navegá las 4 tabs en orden: Lista → Estadísticas → Herramientas → Datos.
4. Abrí **⚙ Configuración**, mostrales el expander de WhatsApp con el
   callout en español. Si es latino, ojo brillante.
5. Decí: "Esto mismo, pero con tus datos reales, corre para vos todos los
   lunes a las 6 AM".

## 🛡 Riesgo: reventa y protección IP

El repo es público (buena señal para portfolio). Si te preocupa que un
cliente lo "revenda":

**Lo que NO protege**:
- El código está online. Cualquiera lo clona.

**Lo que SÍ protege**:
- **Contrato**: cláusula de "uso interno solo, no reventa" en el setup contract.
- **Tu tiempo de configuración** es lo que se paga, no el código.
- Clientes tipo "pagé $500 por el setup y ahora se lo revendo a otro" es
  raro porque **el setup es lo caro** — ellos no tienen el know-how.

**Para protecciones adicionales** (futuro, cuando vendas a 5+ clientes):
- SaaS hosteado propio (los clientes nunca ven el código fuente)
- License server con validación (ver comentarios en el proyecto)

Por ahora, **no te protejas demasiado**. Foco en vender.

## 📅 Plan de los próximos 30 días

Semana 1:
- Subir perfil Upwork con link al repo en portfolio
- Aplicar a 3 trabajos/día que matcheen (`lead gen`, `sales automation`, `python scraping`)
- Precio inicial en propuestas: $500 (por debajo del listed para ganar reviews)

Semana 2:
- Seguir aplicando
- Responder mensajes entrantes en <3h (Upwork premia respuesta rápida)
- Si te interview → demoás el dashboard en modo demo

Semana 3-4:
- Cerrar primer contrato
- Entregar
- Pedir review 5★
- Subir precio a $650

Una vez con 2-3 reviews buenas:
- Subir precio a $800-1000
- Empezar a vender retainer mensual
- Pensar en SaaS hosteado

---

## 📊 Métricas a trackear

Para saber si la estrategia está funcionando:

- **Connects gastados vs. interviews conseguidas** — ratio < 3:1 es bueno
- **Interviews vs. trabajos cerrados** — ratio < 5:1 es bueno
- **Tiempo dedicado por trabajo vs. precio cobrado** — objetivo $50/hr+
  efectivo (no el listed rate)
- **Repeat clients / referencias** — LTV real del cliente

## 💡 Ideas de evolución del producto

- **Phase 2**: automated form submission con Playwright (+$500-800 extra)
- **Lead enrichment**: conectar con Apollo / LinkedIn Sales Nav para
  enriquecer datos del decision-maker
- **CRM integrations**: HubSpot, Pipedrive, Salesforce webhooks
- **Multi-language prospects**: soporte para detección de formularios en
  idiomas no-inglés (alemán, francés)
- **AI-generated outreach drafts**: Claude genera el primer contacto
  personalizado para cada prospect

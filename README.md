# 中国今日 · China Hoy 🇨🇳

**Newsletter diaria en español sobre China**

Cada día, 10 noticias seleccionadas sobre China —tecnología, cultura, sociedad, empresas, ciencia y geopolítica— con comentarios contextuales en español. Sin sensacionalismo, sin propaganda. Solo observación informada y curiosa de un país complejo.

---

## ¿Qué hace este proyecto?

```
┌─────────────────────────────────────────────────────┐
│              Cada día a las 8:00 UTC                 │
├─────────────────────────────────────────────────────┤
│  GitHub Action ejecuta newsletter.py                 │
│       │                                              │
│       ▼                                              │
│  Claude (IA) busca noticias en la web                │
│  (Sixth Tone, SCMP, Caixin, TechNode…)               │
│       │                                              │
│       ▼                                              │
│  Selecciona 10 noticias, filtra duplicados           │
│  y escribe comentarios en español                    │
│       │                                              │
│       ▼                                              │
│  Genera HTML + Markdown + JSON de fuentes            │
│       │                                              │
│       ▼                                              │
│  Commit y push → GitHub Pages publica la web         │
└─────────────────────────────────────────────────────┘
```

---

## Cómo obtener la clave de API de Google Gemini (gratis)

El script usa **Gemini 2.0 Flash**, que tiene una capa gratuita más que suficiente para una edición diaria (límite: 1.500 peticiones/día y 1 millón de tokens/minuto en el plan gratuito).

1. Ve a **[aistudio.google.com](https://aistudio.google.com)**
2. Inicia sesión con tu cuenta de Google
3. Haz clic en **"Get API key"** → **"Create API key"**
4. Selecciona un proyecto de Google Cloud (o crea uno nuevo, es gratuito)
5. Copia la clave generada — empieza siempre por `AIza...`

> No necesitas tarjeta de crédito ni activar ninguna facturación para usar la capa gratuita.

---

## Requisitos previos

- **Python 3.11+**
- **Cuenta en GitHub** (gratuita)
- **Clave de API de Google Gemini** → gratuita, ver instrucciones más abajo
- **GitHub CLI (`gh`)** → [cli.github.com](https://cli.github.com) *(solo para configuración inicial)*

---

## Instalación en 3 pasos

### Paso 1 — Clonar o descargar el repositorio

```bash
git clone https://github.com/TU_USUARIO/china-hoy.git
cd china-hoy
```

O descarga el ZIP desde GitHub y descomprímelo.

### Paso 2 — Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 3 — Ejecutar el configurador y seguir las instrucciones

```bash
chmod +x configurar_proyecto.sh
./configurar_proyecto.sh
```

El script te guiará para:
- Crear el repositorio `china-hoy` en tu cuenta de GitHub
- Activar GitHub Pages automáticamente
- Añadir tu clave de API de Anthropic como secreto

---

## Cómo ver la newsletter publicada

Una vez configurado, la newsletter queda publicada en:

```
https://TU_USUARIO.github.io/china-hoy
```

Cada edición diaria tiene su propia URL:

```
https://TU_USUARIO.github.io/china-hoy/ediciones/YYYY-MM-DD.html
```

---

## Cómo ejecutar el script manualmente

Si quieres generar una edición ahora mismo (sin esperar al workflow automático):

```bash
export GEMINI_API_KEY="AIza...tu-clave"
python newsletter.py
```

El script generará los archivos en `docs/` y actualizará `fuentes_consultadas.json`.

Para publicarlo, haz commit y push:

```bash
git add docs/ fuentes_consultadas.json
git commit -m "📰 Edición manual $(date +%Y-%m-%d)"
git push
```

---

## Estructura de carpetas

```
china-hoy/
├── newsletter.py              # Script principal (genera la newsletter)
├── requirements.txt           # Dependencias Python (solo `google-generativeai`)
├── configurar_proyecto.sh     # Configuración inicial (ejecutar una vez)
├── fuentes_consultadas.json   # Registro de URLs y titulares publicados
├── .gitignore
├── README.md
├── .github/
│   └── workflows/
│       └── newsletter_diaria.yml   # GitHub Action (cron diario)
└── docs/                      # Servido por GitHub Pages
    ├── index.html             # Índice de todas las ediciones
    └── ediciones/
        ├── 2025-01-15.html    # Edición del día (HTML)
        ├── 2025-01-15.md      # Edición del día (Markdown)
        └── ...
```

---

## Fuentes utilizadas

El script prioriza estas fuentes, en este orden:

| Fuente | Web |
|---|---|
| Sixth Tone | sixthtone.com |
| Caixin Global | caixinglobal.com |
| South China Morning Post | scmp.com |
| TechNode | technode.com |
| 36Kr Global | 36kr.com/en |
| Pandaily | pandaily.com |
| China Daily | chinadaily.com.cn |
| CGTN | cgtn.com |
| Xinhua | xinhuanet.com |
| Nikkei Asia | asia.nikkei.com |

---

## Preguntas frecuentes

**¿Cuánto cuesta?**
**Nada.** El script usa Gemini 2.0 Flash, que tiene una capa gratuita de 1.500 peticiones/día y 1 millón de tokens por minuto. Una edición diaria consume una sola petición, muy por debajo de ese límite. No necesitas tarjeta de crédito.

**¿Puedo cambiar las fuentes o el tono editorial?**
Sí. Edita el `prompt_sistema` dentro de la función `buscar_noticias()` en `newsletter.py`.

**¿Puedo cambiar la hora de publicación?**
Sí. Edita la línea `cron: "0 8 * * *"` en `.github/workflows/newsletter_diaria.yml`. El formato es minuto/hora/día/mes/día-semana en UTC.

**¿Qué pasa si no hay noticias nuevas?**
El script detecta si todas las noticias ya fueron publicadas en los últimos 7 días y termina sin crear archivos ni hacer commit.

---

## Licencia

MIT — Úsalo, modifícalo y compártelo libremente.

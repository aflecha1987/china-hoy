#!/usr/bin/env python3
"""
China Hoy 🇨🇳 — Newsletter diaria sobre China
Genera automáticamente 10 noticias con comentarios en español.
Usa Claude Haiku (Anthropic) para minimizar costes.
"""

import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
import anthropic

# ── Configuración ────────────────────────────────────────────────────────────
_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODELO = "claude-haiku-4-5"

CARPETA_DOCS       = Path("docs")
CARPETA_EDICIONES  = CARPETA_DOCS / "ediciones"
ARCHIVO_FUENTES    = Path("fuentes_consultadas.json")

FECHA_HOY = datetime.now().strftime("%Y-%m-%d")
FECHA_LEGIBLE = datetime.now().strftime("%-d de %B de %Y").replace(
    "January","enero").replace("February","febrero").replace("March","marzo"
    ).replace("April","abril").replace("May","mayo").replace("June","junio"
    ).replace("July","julio").replace("August","agosto").replace("September","septiembre"
    ).replace("October","octubre").replace("November","noviembre").replace("December","diciembre")



# ═════════════════════════════════════════════════════════════════════════════
# 1. BÚSQUEDA Y SELECCIÓN DE NOTICIAS
# ═════════════════════════════════════════════════════════════════════════════

def buscar_noticias() -> list[dict]:
    """
    Lanza la búsqueda web con IA y devuelve una lista de 10 noticias.
    Cada noticia es un dict con: titulo, url, fuente, categoria, comentario.
    """
    print("🔍 Buscando noticias relevantes sobre China para hoy…")

    prompt_sistema = """Eres el editor de "China Hoy", una newsletter diaria en español sobre China.
Tu misión: encontrar y comentar las 10 noticias más relevantes del día, equilibradas entre estas categorías:
tecnología, cultura, sociedad, empresas, ciencia y geopolítica.

Fuentes PRIORITARIAS (úsalas en este orden):
1. Sixth Tone (sixthtone.com)
2. Caixin Global (caixinglobal.com)
3. South China Morning Post (scmp.com)
4. TechNode (technode.com)
5. 36Kr Global (36kr.com/en)
6. Pandaily (pandaily.com)
7. China Daily (chinadaily.com.cn)
8. CGTN (cgtn.com)
9. Xinhua News Agency (xinhuanet.com)
10. Nikkei Asia (asia.nikkei.com)
11. Global Times (globaltimes.cn)
12. Reuters China (reuters.com)
13. People's Daily Online (english.peopledaily.com.cn)
14. China Today (chinatoday.com.cn)
15. CCTV News (english.cctv.com)
16. ChinaNews (chinanews.com.cn)
17. Yicai Global (yicaiglobal.com)

TONO EDITORIAL:
- Positivo pero honesto: destacar progreso, innovación, cambio social y matices
- Evitar sensacionalismo, alarmismo y narrativas simplistas
- Escribir como observador informado y curioso que respeta la complejidad china
- En temas sensibles: presentar múltiples perspectivas sin dramatizar
- TODO el contenido en español

Usarás la herramienta 'guardar_noticias' para entregar las 10 noticias seleccionadas.
El comentario de cada noticia debe ser UN solo párrafo de 4-5 frases en español."""

    prompt_usuario = f"""Hoy es {FECHA_HOY}. Selecciona 10 noticias recientes e importantes sobre China de las últimas semanas, usando tu conocimiento actualizado.

Cubre al menos 4 categorías diferentes. Evita noticias repetidas o muy similares entre sí.

Criterios de selección:
- Noticias con impacto real o que ilustren tendencias importantes
- Información sustancial (no solo titulares)
- Sin sensacionalismo ni narrativas alarmistas
- Preferir noticias con datos concretos, citas o contexto histórico

Para las URLs, usa la URL real del artículo si la conoces, o la URL de la portada del medio (ej: https://www.sixthtone.com) si no estás seguro.

Para cada noticia escribe UN párrafo de 4-5 frases EN ESPAÑOL que explique qué ocurrió, por qué importa y qué tendencia ilustra."""

    herramienta = {
        "name": "guardar_noticias",
        "description": "Guarda las 10 noticias seleccionadas con sus comentarios.",
        "input_schema": {
            "type": "object",
            "properties": {
                "noticias": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "titulo":    {"type": "string"},
                            "url":       {"type": "string"},
                            "fuente":    {"type": "string"},
                            "categoria": {"type": "string", "enum": ["tecnología","cultura","sociedad","empresas","ciencia","geopolítica"]},
                            "comentario":{"type": "string"},
                        },
                        "required": ["titulo","url","fuente","categoria","comentario"]
                    },
                    "minItems": 5,
                    "maxItems": 10,
                }
            },
            "required": ["noticias"]
        }
    }

    print("   Consultando a Claude Haiku…")
    respuesta = _client.messages.create(
        model=MODELO,
        max_tokens=4096,
        system=prompt_sistema,
        tools=[herramienta],
        tool_choice={"type": "tool", "name": "guardar_noticias"},
        messages=[{"role": "user", "content": prompt_usuario}],
    )

    # Extraer noticias del tool_use (JSON garantizado válido)
    for bloque in respuesta.content:
        if bloque.type == "tool_use" and bloque.name == "guardar_noticias":
            noticias = bloque.input.get("noticias", [])
            print(f"   ✅ {len(noticias)} noticias encontradas")
            return noticias

    print("   ⚠️  No se recibió respuesta estructurada")
    return []


def _extraer_json_noticias(texto: str) -> list[dict]:
    """Extrae y valida la lista de noticias del texto JSON devuelto."""
    # Intentar extraer JSON aunque haya texto extra alrededor
    patron = re.search(r'\{[\s\S]*"noticias"[\s\S]*\}', texto)
    if not patron:
        print("   ⚠️  No se encontró JSON válido en la respuesta")
        return []

    try:
        datos = json.loads(patron.group())
        noticias = datos.get("noticias", [])
        # Validar campos mínimos
        noticias_validas = []
        campos_requeridos = {"titulo", "url", "fuente", "categoria", "comentario"}
        for noticia in noticias:
            if campos_requeridos.issubset(noticia.keys()):
                noticias_validas.append(noticia)
        return noticias_validas[:10]
    except json.JSONDecodeError as e:
        print(f"   ⚠️  Error al parsear JSON: {e}")
        return []


# ═════════════════════════════════════════════════════════════════════════════
# 2. DEDUPLICACIÓN
# ═════════════════════════════════════════════════════════════════════════════

def filtrar_duplicados(noticias_candidatas: list[dict]) -> list[dict]:
    """
    Elimina noticias cuya URL o titular haya aparecido en los últimos 7 días.
    """
    if not ARCHIVO_FUENTES.exists():
        return noticias_candidatas

    registro = json.loads(ARCHIVO_FUENTES.read_text(encoding="utf-8"))
    fecha_limite = datetime.now() - timedelta(days=7)

    urls_recientes: set[str] = set()
    titulares_recientes: set[str] = set()

    for fecha_str, datos in registro.items():
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        except ValueError:
            continue
        if fecha >= fecha_limite:
            urls_recientes.update(datos.get("fuentes", []))
            titulares_recientes.update(
                t.lower() for t in datos.get("titulares", [])
            )

    filtradas = []
    for n in noticias_candidatas:
        titulo_limpio = n.get("titulo", "").strip().lower()
        if titulo_limpio in titulares_recientes:
            print(f"   ⏭  Duplicado (titular): {n.get('titulo','')[:60]}")
            continue
        filtradas.append(n)

    eliminadas = len(noticias_candidatas) - len(filtradas)
    if eliminadas:
        print(f"   🔁 {eliminadas} noticia(s) descartadas por duplicado")
    return filtradas


# ═════════════════════════════════════════════════════════════════════════════
# 3. GENERACIÓN HTML DE LA EDICIÓN
# ═════════════════════════════════════════════════════════════════════════════

def generar_html_edicion(noticias: list[dict]) -> str:
    """Construye el HTML completo de la edición del día."""
    ICONOS_CATEGORIA = {
        "tecnología": "💻",
        "cultura":    "🎭",
        "sociedad":   "👥",
        "empresas":   "💼",
        "ciencia":    "🔬",
        "geopolítica":"🌏",
    }

    tarjetas_html = ""
    for i, n in enumerate(noticias, 1):
        icono = ICONOS_CATEGORIA.get(n.get("categoria", ""), "📰")
        categoria = n.get("categoria", "general").capitalize()
        titulo = _escapar_html(n.get("titulo", "Sin título"))
        fuente = _escapar_html(n.get("fuente", "Fuente desconocida"))
        url = n.get("url", "#")
        # Convertir párrafos del comentario en bloques <p>
        parrafos = [
            f"<p>{_escapar_html(p.strip())}</p>"
            for p in n.get("comentario", "").split("\n")
            if p.strip()
        ]
        comentario_html = "\n".join(parrafos)

        tarjetas_html += f"""
        <article class="tarjeta" id="noticia-{i}">
          <div class="tarjeta-cabecera">
            <span class="categoria-etiqueta">{icono} {categoria}</span>
            <span class="numero-noticia">#{i}</span>
          </div>
          <h2 class="tarjeta-titulo">{titulo}</h2>
          <div class="tarjeta-comentario">
            {comentario_html}
          </div>
          <div class="tarjeta-pie">
            <span class="fuente-nombre">📰 {fuente}</span>
            <a href="{url}" class="enlace-fuente" target="_blank" rel="noopener">
              Leer artículo original →
            </a>
          </div>
        </article>"""

    # Lista de fuentes en el pie de página
    fuentes_lista = "".join(
        f'<li><a href="{n.get("url","#")}" target="_blank" rel="noopener">'
        f'{_escapar_html(n.get("fuente",""))} — {_escapar_html(n.get("titulo",""))}</a></li>'
        for n in noticias
    )

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>China Hoy — {FECHA_LEGIBLE}</title>
  <style>
    /* ── Reset y base ── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Georgia', 'Times New Roman', serif;
      background: #fafaf8;
      color: #1a1a1a;
      line-height: 1.7;
      font-size: 17px;
    }}
    a {{ color: #c0392b; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}

    /* ── Cabecera ── */
    .cabecera {{
      background: linear-gradient(135deg, #c0392b 0%, #922b21 100%);
      color: white;
      padding: 2.5rem 1.5rem;
      text-align: center;
    }}
    .cabecera-nav {{
      font-size: 0.85rem;
      margin-bottom: 1rem;
      opacity: 0.85;
    }}
    .cabecera-nav a {{ color: rgba(255,255,255,0.9); }}
    .logo {{ font-size: 2.8rem; font-weight: bold; letter-spacing: -0.5px; }}
    .logo-sub {{ font-size: 1rem; opacity: 0.8; margin-top: 0.3rem; letter-spacing: 2px; text-transform: uppercase; }}
    .fecha-edicion {{
      margin-top: 1rem;
      font-size: 1.05rem;
      opacity: 0.9;
      font-style: italic;
    }}

    /* ── Resumen ejecutivo ── */
    .resumen {{
      max-width: 780px;
      margin: 2.5rem auto 0;
      padding: 0 1.5rem;
    }}
    .resumen-caja {{
      background: #fff8e7;
      border-left: 4px solid #f39c12;
      border-radius: 6px;
      padding: 1.5rem 1.8rem;
    }}
    .resumen-caja h2 {{
      font-size: 1rem;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #7d6608;
      margin-bottom: 0.8rem;
    }}
    .resumen-caja ul {{
      padding-left: 1.2rem;
      color: #4a4a4a;
      font-size: 0.95rem;
    }}
    .resumen-caja li {{ margin-bottom: 0.4rem; }}

    /* ── Noticias ── */
    .contenido {{ max-width: 780px; margin: 0 auto; padding: 2rem 1.5rem 3rem; }}

    .tarjeta {{
      background: white;
      border-radius: 10px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.08);
      padding: 2rem;
      margin-bottom: 2rem;
      border: 1px solid #ece9e0;
      transition: box-shadow 0.2s;
    }}
    .tarjeta:hover {{ box-shadow: 0 4px 20px rgba(0,0,0,0.12); }}

    .tarjeta-cabecera {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.8rem;
    }}
    .categoria-etiqueta {{
      background: #f0ebe0;
      color: #5d4e37;
      font-size: 0.78rem;
      font-weight: bold;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      padding: 0.25rem 0.7rem;
      border-radius: 20px;
      font-family: sans-serif;
    }}
    .numero-noticia {{
      color: #c0392b;
      font-weight: bold;
      font-size: 0.9rem;
      font-family: sans-serif;
    }}
    .tarjeta-titulo {{
      font-size: 1.35rem;
      line-height: 1.35;
      color: #1a1a1a;
      margin-bottom: 1.2rem;
      font-weight: bold;
    }}
    .tarjeta-comentario p {{
      color: #333;
      margin-bottom: 1rem;
      font-size: 1rem;
    }}
    .tarjeta-comentario p:last-child {{ margin-bottom: 0; }}
    .tarjeta-pie {{
      margin-top: 1.4rem;
      padding-top: 1rem;
      border-top: 1px solid #ece9e0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.5rem;
    }}
    .fuente-nombre {{
      color: #7a7a7a;
      font-size: 0.88rem;
      font-family: sans-serif;
    }}
    .enlace-fuente {{
      background: #c0392b;
      color: white;
      padding: 0.4rem 1rem;
      border-radius: 4px;
      font-size: 0.85rem;
      font-family: sans-serif;
      transition: background 0.2s;
    }}
    .enlace-fuente:hover {{ background: #922b21; text-decoration: none; }}

    /* ── Pie de página ── */
    .pie {{
      background: #1a1a1a;
      color: #aaa;
      padding: 2.5rem 1.5rem;
      margin-top: 2rem;
    }}
    .pie-contenido {{ max-width: 780px; margin: 0 auto; }}
    .pie h3 {{ color: #ddd; font-size: 0.95rem; margin-bottom: 1rem; font-family: sans-serif; }}
    .pie ul {{ list-style: none; font-size: 0.82rem; column-count: 2; column-gap: 2rem; }}
    .pie ul li {{ margin-bottom: 0.5rem; }}
    .pie ul a {{ color: #888; }}
    .pie ul a:hover {{ color: #ccc; }}
    .pie-creditos {{
      margin-top: 1.5rem;
      padding-top: 1.2rem;
      border-top: 1px solid #333;
      font-size: 0.8rem;
      text-align: center;
      color: #666;
    }}

    /* ── Responsive ── */
    @media (max-width: 600px) {{
      .logo {{ font-size: 2rem; }}
      .tarjeta {{ padding: 1.3rem; }}
      .tarjeta-titulo {{ font-size: 1.15rem; }}
      .pie ul {{ column-count: 1; }}
      .tarjeta-pie {{ flex-direction: column; align-items: flex-start; }}
    }}
  </style>
</head>
<body>

<header class="cabecera">
  <nav class="cabecera-nav"><a href="../../index.html">← Volver al índice</a></nav>
  <div class="logo">中国今日 · China Hoy 🇨🇳</div>
  <div class="logo-sub">Newsletter diaria en español</div>
  <div class="fecha-edicion">Edición del {FECHA_LEGIBLE}</div>
</header>

<section class="resumen">
  <div class="resumen-caja">
    <h2>📋 Resumen ejecutivo — {len(noticias)} noticias de hoy</h2>
    <ul>
      {"".join(f'<li><strong>#{i}.</strong> {_escapar_html(n.get("titulo",""))}</li>' for i,n in enumerate(noticias,1))}
    </ul>
  </div>
</section>

<main class="contenido">
  {tarjetas_html}
</main>

<footer class="pie">
  <div class="pie-contenido">
    <h3>Fuentes consultadas en esta edición</h3>
    <ul>
      {fuentes_lista}
    </ul>
    <div class="pie-creditos">
      China Hoy · Edición {FECHA_HOY} · Generado automáticamente con IA ·
      Las opiniones expresadas son editoriales y no representan posiciones oficiales.
    </div>
  </div>
</footer>

</body>
</html>"""
    return html


def _escapar_html(texto: str) -> str:
    """Escapa caracteres especiales HTML."""
    return (texto
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


# ═════════════════════════════════════════════════════════════════════════════
# 4. GENERACIÓN MARKDOWN
# ═════════════════════════════════════════════════════════════════════════════

def generar_markdown(noticias: list[dict]) -> str:
    """Construye el archivo .md de la edición."""
    ICONOS = {
        "tecnología":"💻","cultura":"🎭","sociedad":"👥",
        "empresas":"💼","ciencia":"🔬","geopolítica":"🌏",
    }
    secciones = []
    for i, n in enumerate(noticias, 1):
        icono = ICONOS.get(n.get("categoria",""), "📰")
        categoria = n.get("categoria","general").capitalize()
        titulo = n.get("titulo","Sin título")
        fuente = n.get("fuente","Fuente desconocida")
        url = n.get("url","#")
        comentario = n.get("comentario","")
        secciones.append(
            f"## {i}. {titulo}\n\n"
            f"**{icono} {categoria}** · 📰 [{fuente}]({url})\n\n"
            f"{comentario}\n\n"
            f"[🔗 Leer artículo completo]({url})\n"
        )

    fuentes_md = "\n".join(
        f"- [{n.get('fuente','')}]({n.get('url','#')}) — {n.get('titulo','')}"
        for n in noticias
    )

    resumen_md = "\n".join(f"{i}. {n.get('titulo','')}" for i, n in enumerate(noticias, 1))
    cuerpo_md = "---\n\n".join(secciones)

    return f"""# 中国今日 · China Hoy 🇨🇳

**Edición del {FECHA_LEGIBLE}**

[← Volver al índice](../../index.html)

---

## Resumen ejecutivo

{resumen_md}

---

{cuerpo_md}

---

## Fuentes consultadas

{fuentes_md}

---

*China Hoy · {FECHA_HOY} · Generado con IA · Contenido editorial independiente*
"""


# ═════════════════════════════════════════════════════════════════════════════
# 5. REGENERAR ÍNDICE
# ═════════════════════════════════════════════════════════════════════════════

def regenerar_indice():
    """
    Recorre /docs/ediciones/ y reconstruye el index.html con todas las ediciones,
    de la más reciente a la más antigua.
    """
    CARPETA_EDICIONES.mkdir(parents=True, exist_ok=True)

    # Recopilar ediciones existentes (archivos .html)
    ediciones = sorted(
        [f.stem for f in CARPETA_EDICIONES.glob("*.html") if re.match(r"\d{4}-\d{2}-\d{2}", f.stem)],
        reverse=True
    )

    items_html = ""
    for fecha_str in ediciones:
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
            fecha_fmt = fecha.strftime("%-d de %B de %Y").replace(
                "January","enero").replace("February","febrero").replace("March","marzo"
                ).replace("April","abril").replace("May","mayo").replace("June","junio"
                ).replace("July","julio").replace("August","agosto").replace("September","septiembre"
                ).replace("October","octubre").replace("November","noviembre").replace("December","diciembre")
        except ValueError:
            fecha_fmt = fecha_str
        items_html += f"""
        <li class="edicion-item">
          <a href="ediciones/{fecha_str}.html" class="edicion-enlace">
            <span class="edicion-fecha">{fecha_fmt}</span>
            <span class="edicion-flecha">→</span>
          </a>
        </li>"""

    total = len(ediciones)
    html_indice = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>China Hoy 🇨🇳 — Newsletter diaria sobre China en español</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Georgia', 'Times New Roman', serif;
      background: #fafaf8;
      color: #1a1a1a;
      line-height: 1.7;
    }}
    .cabecera {{
      background: linear-gradient(135deg, #c0392b 0%, #922b21 100%);
      color: white;
      padding: 3.5rem 1.5rem;
      text-align: center;
    }}
    .logo {{ font-size: 3rem; font-weight: bold; letter-spacing: -0.5px; }}
    .logo-sub {{ font-size: 1rem; opacity: 0.8; margin-top: 0.4rem; letter-spacing: 2px; text-transform: uppercase; }}
    .descripcion {{
      max-width: 550px;
      margin: 1.2rem auto 0;
      font-size: 1.05rem;
      opacity: 0.9;
      line-height: 1.6;
    }}
    .contador {{
      margin-top: 1rem;
      font-size: 0.9rem;
      opacity: 0.75;
      font-family: sans-serif;
    }}
    .contenido {{ max-width: 680px; margin: 3rem auto; padding: 0 1.5rem 4rem; }}
    .seccion-titulo {{
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 2px;
      color: #888;
      margin-bottom: 1.2rem;
      font-family: sans-serif;
    }}
    .lista-ediciones {{ list-style: none; }}
    .edicion-item {{ border-bottom: 1px solid #ece9e0; }}
    .edicion-item:first-child {{ border-top: 1px solid #ece9e0; }}
    .edicion-enlace {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 0.2rem;
      color: #1a1a1a;
      transition: color 0.15s;
    }}
    .edicion-enlace:hover {{ color: #c0392b; text-decoration: none; }}
    .edicion-fecha {{ font-size: 1.05rem; }}
    .edicion-flecha {{ color: #c0392b; font-size: 1.2rem; }}
    .vacio {{
      text-align: center;
      color: #aaa;
      padding: 3rem 0;
      font-style: italic;
    }}
    .pie {{
      text-align: center;
      padding: 2rem;
      color: #aaa;
      font-size: 0.82rem;
      border-top: 1px solid #ece9e0;
      font-family: sans-serif;
    }}
    @media (max-width: 500px) {{ .logo {{ font-size: 2.2rem; }} }}
  </style>
</head>
<body>

<header class="cabecera">
  <div class="logo">中国今日 · China Hoy 🇨🇳</div>
  <div class="logo-sub">Newsletter diaria en español</div>
  <p class="descripcion">
    Cada día, 10 noticias seleccionadas sobre China: tecnología, cultura,
    sociedad, empresas, ciencia y geopolítica. Sin sensacionalismo, con contexto.
  </p>
  <div class="contador">{total} edición{'es' if total != 1 else ''} publicada{'s' if total != 1 else ''}</div>
</header>

<main class="contenido">
  <p class="seccion-titulo">📅 Todas las ediciones — más reciente primero</p>
  {"<ul class='lista-ediciones'>" + items_html + "</ul>" if ediciones else "<p class='vacio'>Todavía no hay ediciones publicadas.<br>Ejecuta el script para generar la primera.</p>"}
</main>

<footer class="pie">
  China Hoy · Actualizado el {FECHA_HOY} · Generado con IA ·
  <a href="https://github.com" style="color:#aaa">Ver en GitHub</a>
</footer>

</body>
</html>"""

    (CARPETA_DOCS / "index.html").write_text(html_indice, encoding="utf-8")
    print(f"   📄 Índice actualizado con {total} edición(es)")


# ═════════════════════════════════════════════════════════════════════════════
# 6. ACTUALIZAR REGISTRO DE FUENTES
# ═════════════════════════════════════════════════════════════════════════════

def actualizar_registro_fuentes(noticias: list[dict]):
    """Actualiza fuentes_consultadas.json con las noticias de hoy."""
    if ARCHIVO_FUENTES.exists():
        registro = json.loads(ARCHIVO_FUENTES.read_text(encoding="utf-8"))
    else:
        registro = {}

    registro[FECHA_HOY] = {
        "fuentes": [n.get("url", "") for n in noticias],
        "titulares": [n.get("titulo", "") for n in noticias],
    }

    ARCHIVO_FUENTES.write_text(
        json.dumps(registro, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"   💾 Registro de fuentes actualizado ({len(noticias)} entradas para {FECHA_HOY})")


# ═════════════════════════════════════════════════════════════════════════════
# 7. MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 60)
    print("  中国今日 · CHINA HOY  —  Newsletter diaria sobre China")
    print(f"  Fecha: {FECHA_HOY}")
    print("═" * 60 + "\n")

    # Verificar clave API
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ ERROR: No se encontró la variable de entorno ANTHROPIC_API_KEY")
        print("   Consíguela en: https://console.anthropic.com/settings/keys")
        print("   Configúrala con: export ANTHROPIC_API_KEY='sk-ant-...'")
        return

    # Crear carpetas necesarias
    CARPETA_EDICIONES.mkdir(parents=True, exist_ok=True)
    print(f"📁 Carpetas preparadas: {CARPETA_DOCS}/ y {CARPETA_EDICIONES}/\n")

    # ── Paso 1: Buscar noticias ────────────────────────────────────────────
    try:
        noticias_crudas = buscar_noticias()
    except Exception as e:
        print(f"❌ Error al buscar noticias: {e}")
        return

    if not noticias_crudas:
        print("⚠️  No se encontraron noticias. Terminando sin generar archivos.")
        return

    # ── Paso 2: Filtrar duplicados ─────────────────────────────────────────
    print("\n🔁 Verificando duplicados de los últimos 7 días…")
    noticias = filtrar_duplicados(noticias_crudas)

    if not noticias:
        print("⚠️  Todas las noticias ya fueron publicadas recientemente. No hay contenido nuevo.")
        return

    print(f"   ✅ {len(noticias)} noticias únicas listas para publicar\n")

    # ── Paso 3: Generar archivos ───────────────────────────────────────────
    print("📝 Generando archivos de la edición…")

    # HTML de la edición
    try:
        html_edicion = generar_html_edicion(noticias)
        ruta_html = CARPETA_EDICIONES / f"{FECHA_HOY}.html"
        ruta_html.write_text(html_edicion, encoding="utf-8")
        print(f"   ✅ HTML generado: {ruta_html}")
    except Exception as e:
        print(f"   ❌ Error al generar HTML: {e}")

    # Markdown de la edición
    try:
        md_edicion = generar_markdown(noticias)
        ruta_md = CARPETA_EDICIONES / f"{FECHA_HOY}.md"
        ruta_md.write_text(md_edicion, encoding="utf-8")
        print(f"   ✅ Markdown generado: {ruta_md}")
    except Exception as e:
        print(f"   ❌ Error al generar Markdown: {e}")

    # Índice principal
    try:
        print("\n🗂️  Regenerando índice…")
        regenerar_indice()
    except Exception as e:
        print(f"   ❌ Error al regenerar índice: {e}")

    # Registro de fuentes
    try:
        print("\n📊 Actualizando registro de fuentes…")
        actualizar_registro_fuentes(noticias)
    except Exception as e:
        print(f"   ❌ Error al actualizar registro: {e}")

    # ── Resumen final ──────────────────────────────────────────────────────
    fuentes_usadas = list({n.get("fuente", "") for n in noticias})
    categorias_usadas = list({n.get("categoria", "") for n in noticias})

    print("\n" + "═" * 60)
    print("  ✅ RESUMEN DE LA EDICIÓN GENERADA")
    print("═" * 60)
    print(f"  📅 Fecha:             {FECHA_HOY}")
    print(f"  📰 Noticias:          {len(noticias)}")
    print(f"  🗂️  Categorías:        {', '.join(sorted(categorias_usadas))}")
    print(f"  🌐 Fuentes usadas:    {len(fuentes_usadas)}")
    for f in sorted(fuentes_usadas):
        print(f"     • {f}")
    print(f"\n  📄 Archivos generados:")
    print(f"     • docs/ediciones/{FECHA_HOY}.html")
    print(f"     • docs/ediciones/{FECHA_HOY}.md")
    print(f"     • docs/index.html")
    print(f"     • fuentes_consultadas.json")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()

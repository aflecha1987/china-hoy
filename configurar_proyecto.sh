#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# configurar_proyecto.sh — Script de configuración inicial de China Hoy 🇨🇳
#
# Ejecutar UNA SOLA VEZ para:
#   1. Verificar dependencias (gh CLI, git)
#   2. Crear el repositorio en GitHub
#   3. Hacer el primer commit y push
#   4. Activar GitHub Pages apuntando a /docs
#   5. Guiar al usuario para añadir el secreto GEMINI_API_KEY
# ──────────────────────────────────────────────────────────────────────────────

set -e  # Salir si cualquier comando falla

# ── Colores para mensajes ──────────────────────────────────────────────────────
ROJO='\033[0;31m'
VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
AZUL='\033[0;34m'
NEGRITA='\033[1m'
RESET='\033[0m'

titulo()  { echo -e "\n${AZUL}${NEGRITA}▶ $1${RESET}"; }
ok()      { echo -e "  ${VERDE}✅ $1${RESET}"; }
info()    { echo -e "  ${AMARILLO}ℹ️  $1${RESET}"; }
error()   { echo -e "  ${ROJO}❌ $1${RESET}"; }

echo ""
echo -e "${NEGRITA}════════════════════════════════════════════════════════${RESET}"
echo -e "${NEGRITA}   中国今日 · CHINA HOY — Configuración inicial         ${RESET}"
echo -e "${NEGRITA}════════════════════════════════════════════════════════${RESET}"
echo ""

# ═════════════════════════════════════════════════════════════════════════════
# PASO 1: Verificar que gh CLI está instalado
# ═════════════════════════════════════════════════════════════════════════════
titulo "PASO 1: Verificando GitHub CLI (gh)"

if ! command -v gh &> /dev/null; then
    error "GitHub CLI (gh) no está instalado."
    echo ""
    echo "  Por favor instálalo siguiendo las instrucciones en:"
    echo "  https://cli.github.com/manual/installation"
    echo ""
    echo "  En macOS (Homebrew):  brew install gh"
    echo "  En Ubuntu/Debian:     sudo apt install gh"
    echo "  En Windows:           winget install GitHub.cli"
    echo ""
    exit 1
fi

ok "GitHub CLI (gh) encontrado: $(gh --version | head -1)"

# ── Verificar autenticación en gh ─────────────────────────────────────────────
titulo "PASO 2: Verificando autenticación en GitHub"

if ! gh auth status &> /dev/null; then
    info "No estás autenticado en GitHub. Iniciando sesión…"
    gh auth login
else
    ok "Ya estás autenticado en GitHub"
    gh auth status 2>&1 | grep "Logged in" | sed 's/^/  /'
fi

# ═════════════════════════════════════════════════════════════════════════════
# PASO 3: Pedir nombre de usuario de GitHub
# ═════════════════════════════════════════════════════════════════════════════
titulo "PASO 3: Identificando tu usuario de GitHub"

USUARIO_GITHUB=$(gh api user --jq '.login' 2>/dev/null || echo "")

if [ -z "$USUARIO_GITHUB" ]; then
    read -p "  Introduce tu nombre de usuario de GitHub: " USUARIO_GITHUB
fi

ok "Usuario de GitHub: $USUARIO_GITHUB"

NOMBRE_REPO="china-hoy"
URL_REPO="https://github.com/$USUARIO_GITHUB/$NOMBRE_REPO"
URL_PAGES="https://$USUARIO_GITHUB.github.io/$NOMBRE_REPO"

# ═════════════════════════════════════════════════════════════════════════════
# PASO 4: Crear el repositorio en GitHub
# ═════════════════════════════════════════════════════════════════════════════
titulo "PASO 4: Creando repositorio '$NOMBRE_REPO' en GitHub"

if gh repo view "$USUARIO_GITHUB/$NOMBRE_REPO" &> /dev/null; then
    info "El repositorio '$NOMBRE_REPO' ya existe en tu cuenta."
    ok "Usando repositorio existente: $URL_REPO"
else
    gh repo create "$NOMBRE_REPO" \
        --public \
        --description "Newsletter diaria sobre China — 中国今日" \
        --homepage "$URL_PAGES"
    ok "Repositorio creado: $URL_REPO"
fi

# ═════════════════════════════════════════════════════════════════════════════
# PASO 5: Inicializar git y hacer primer commit
# ═════════════════════════════════════════════════════════════════════════════
titulo "PASO 5: Inicializando git y haciendo el primer commit"

# Inicializar git si no está ya inicializado
if [ ! -d ".git" ]; then
    git init
    ok "Repositorio git inicializado"
else
    info "El repositorio git ya está inicializado"
fi

# Crear carpetas mínimas necesarias para que GitHub Pages funcione
mkdir -p docs/ediciones

# Crear un index.html provisional si no existe
if [ ! -f "docs/index.html" ]; then
    cat > docs/index.html << 'EOF'
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>China Hoy 🇨🇳</title>
</head>
<body>
  <h1>中国今日 · China Hoy 🇨🇳</h1>
  <p>La newsletter se generará automáticamente. Vuelve mañana para ver la primera edición.</p>
</body>
</html>
EOF
    ok "Creada página de inicio provisional en docs/index.html"
fi

# Configurar el remoto
if git remote get-url origin &> /dev/null; then
    info "El remoto 'origin' ya existe, actualizando URL…"
    git remote set-url origin "https://github.com/$USUARIO_GITHUB/$NOMBRE_REPO.git"
else
    git remote add origin "https://github.com/$USUARIO_GITHUB/$NOMBRE_REPO.git"
fi

# Configurar rama main
git checkout -b main 2>/dev/null || git checkout main

# Primer commit
git add .
git commit -m "🚀 Configuración inicial de China Hoy" || info "No hay cambios nuevos para hacer commit"

ok "Commit inicial listo"

# ═════════════════════════════════════════════════════════════════════════════
# PASO 6: Push al repositorio
# ═════════════════════════════════════════════════════════════════════════════
titulo "PASO 6: Subiendo archivos a GitHub"

git push -u origin main
ok "Archivos subidos a $URL_REPO"

# ═════════════════════════════════════════════════════════════════════════════
# PASO 7: Activar GitHub Pages apuntando a /docs en la rama main
# ═════════════════════════════════════════════════════════════════════════════
titulo "PASO 7: Activando GitHub Pages"

# Usar la API de GitHub para configurar Pages
gh api \
    --method POST \
    -H "Accept: application/vnd.github+json" \
    "/repos/$USUARIO_GITHUB/$NOMBRE_REPO/pages" \
    -f source='{"branch":"main","path":"/docs"}' \
    2>/dev/null || \
gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "/repos/$USUARIO_GITHUB/$NOMBRE_REPO/pages" \
    -f source='{"branch":"main","path":"/docs"}' \
    2>/dev/null || \
info "GitHub Pages ya estaba activado o requiere activación manual."

ok "GitHub Pages configurado → carpeta /docs en la rama main"
info "Puede tardar 1-2 minutos en estar disponible en: $URL_PAGES"

# ═════════════════════════════════════════════════════════════════════════════
# PASO 8: Instrucciones para añadir el secreto GEMINI_API_KEY
# ═════════════════════════════════════════════════════════════════════════════
titulo "PASO 8: Configurar el secreto GEMINI_API_KEY"

echo ""
echo -e "  ${NEGRITA}Para que el workflow automático funcione, necesitas añadir${RESET}"
echo -e "  ${NEGRITA}tu clave de API de Anthropic como secreto de GitHub.${RESET}"
echo ""
echo -e "  ${AMARILLO}Sigue estos pasos:${RESET}"
echo ""
echo -e "  1️⃣  Ve a esta URL:"
echo -e "      ${AZUL}${NEGRITA}https://github.com/$USUARIO_GITHUB/$NOMBRE_REPO/settings/secrets/actions${RESET}"
echo ""
echo -e "  2️⃣  Haz clic en ${NEGRITA}'New repository secret'${RESET}"
echo ""
echo -e "  3️⃣  En el campo ${NEGRITA}Name${RESET}, escribe exactamente:"
echo -e "      ${VERDE}GEMINI_API_KEY${RESET}"
echo ""
echo -e "  4️⃣  En el campo ${NEGRITA}Secret${RESET}, pega tu clave de API de Anthropic"
echo -e "      (la encuentras en: https://aistudio.google.com — empieza por 'AIza...')"
echo ""
echo -e "  5️⃣  Haz clic en ${NEGRITA}'Add secret'${RESET}"
echo ""

read -p "  Pulsa ENTER cuando hayas añadido el secreto para continuar…"

# ═════════════════════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ═════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${NEGRITA}════════════════════════════════════════════════════════${RESET}"
echo -e "${VERDE}${NEGRITA}   ✅ ¡Configuración completada con éxito!${RESET}"
echo -e "${NEGRITA}════════════════════════════════════════════════════════${RESET}"
echo ""
echo -e "  📦 Repositorio:     ${AZUL}$URL_REPO${RESET}"
echo -e "  🌐 Newsletter web:  ${AZUL}$URL_PAGES${RESET}"
echo -e "  ⏰ Publicación:     Automática cada día a las 8:00 UTC"
echo ""
echo -e "  ${AMARILLO}Para generar la primera edición ahora mismo, ejecuta:${RESET}"
echo -e "  ${NEGRITA}  export GEMINI_API_KEY='tu-clave-aquí'${RESET}"
echo -e "  ${NEGRITA}  python newsletter.py${RESET}"
echo ""
echo -e "  ${AMARILLO}O espera a mañana a las 8:00 UTC para la primera edición automática.${RESET}"
echo ""

# MCPs — Configuración local

> **Audiencia**: cualquier usuario tras `skynex install --package skills --target opencode`
> **Estado**: 10 MCPs definidos en `opencode/opencode.json`. Algunos requieren API keys que el usuario debe inyectar vía variables de entorno.

---

## Resumen — qué MCP necesita configuración

| MCP | Necesita env var | Acción |
|---|---|---|
| `atlassian` | ❌ no | OAuth flow al primer uso |
| `brevo` | ✅ `BREVO_API_KEY` | crear API key en panel Brevo |
| `chrome-devtools` | ❌ no | requiere Chromium ejecutándose con `--remote-debugging-port=9222` |
| `cloudflare-api` | ❌ no | OAuth flow al primer uso |
| `context7` | ⚠️ opcional `CONTEXT7_API_KEY` | API key opcional para mayor cuota |
| `exa` | ❌ no | gratis hasta cuota límite |
| `figma` | ✅ `FIGMA_API_KEY` | crear PAT en Figma settings |
| `jina-mcp-server` | ❌ no | gratis hasta cuota límite |
| `neurox` | ❌ no | requiere binario `neurox` instalado (ver Neurox repo) |
| `slack` | ✅ `SLACK_BOT_TOKEN` + `SLACK_TEAM_ID` | crear bot en Slack app + invitarlo al workspace |

---

## Cómo setear las variables de entorno

El JSON del MCP usa sintaxis `${VAR_NAME}` que OpenCode resuelve desde el environment del proceso.

### Opción A — `.envrc` con direnv (recomendado)

```bash
# ~/.config/opencode/.envrc o en tu home
export BREVO_API_KEY="xkeysib-..."
export FIGMA_API_KEY="figd_..."
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_TEAM_ID="T..."
export CONTEXT7_API_KEY="..."   # opcional
```

Después `direnv allow`.

### Opción B — Shell rc (bash/zsh)

Añadí al final de `~/.bashrc` o `~/.zshrc`:

```bash
export BREVO_API_KEY="xkeysib-..."
export FIGMA_API_KEY="figd_..."
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_TEAM_ID="T..."
```

Reload: `source ~/.bashrc` (o nueva terminal).

### Opción C — Por sesión (testing)

```bash
BREVO_API_KEY=xkeysib-... FIGMA_API_KEY=figd-... opencode
```

---

## Cómo obtener cada token

### Brevo

1. Panel Brevo → SMTP & API → API Keys → Generate new API key
2. Copiar el key (formato `xkeysib-...`)
3. **El header lleva `Bearer ${BREVO_API_KEY}`** — solo necesitás el key, OpenCode arma el Bearer
4. Si tu key es del tipo "Brevo encoded" (Base64 con JWT-like format `eyJ...`), pegalo tal cual

### Figma

1. Figma → Account Settings → Personal Access Tokens → Create new token
2. Scopes mínimos: `File content: Read`, `Library content: Read`
3. Token formato `figd_...`

### Slack

1. https://api.slack.com/apps → Create new app → From scratch
2. OAuth & Permissions → Bot Token Scopes mínimos: `channels:read`, `channels:history`, `chat:write`, `users:read`
3. Install app to workspace
4. Copiar Bot User OAuth Token (formato `xoxb-...`)
5. Workspace settings → Team ID (formato `T...`)

### Context7 (opcional)

1. https://context7.com → Sign up → Settings → API Keys
2. Sin key, igual funciona pero con cuota más baja

### Cloudflare API

OAuth flow automático en el primer uso. No requiere env var.

### Atlassian

OAuth flow automático en el primer uso. No requiere env var.

---

## Verificación post-setup

```bash
# 1. Variables presentes
env | grep -E "BREVO_API_KEY|FIGMA_API_KEY|SLACK_BOT_TOKEN|SLACK_TEAM_ID"

# 2. JSON válido
python3 -c "import json; json.load(open('$HOME/.config/opencode/opencode.json'))"

# 3. Arrancar OpenCode y verificar que los MCPs conectan
opencode  # luego en TUI: revisar status de MCPs
```

Si un MCP aparece como `Disconnected` o `Error`, suele ser por:
- Env var no exportada en la shell que lanzó OpenCode
- Token expirado / revocado
- Para `neurox`: binario no instalado
- Para `chrome-devtools`: Chromium no corriendo con remote debugging
- Para `slack`: bot no invitado a ningún canal

---

## Seguridad

⚠️ **Nunca commitees archivos con tokens reales.**

El repo `skynex/opencode/opencode.json` usa placeholders `${VAR_NAME}` precisamente para que sea seguro versionarlo. Si modificás tu copia local con tokens reales (`~/.config/opencode/opencode.json`), ese archivo NO debe volver al repo.

Si por error commiteás un token:
1. Rotalo INMEDIATAMENTE en el panel del proveedor (no sirve borrar el commit — quedó en historial)
2. `git push --force` no resuelve nada — los crawlers ya lo agarraron
3. Generar nuevo token, actualizar env vars, seguir

---

## Referencias

- `opencode/opencode.json` — definición de MCPs en repo (con `${VAR}` placeholders)
- `~/.config/opencode/opencode.json` — copia local en runtime (puede tener tokens reales)
- `docs/installation.md` — instalación general de skynex

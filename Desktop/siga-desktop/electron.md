# Wrapper Electron — Monitor de Filas

Este documento descreve **como montar o repositório do wrapper Electron** que empacota a
tela de monitor (totem/recepção) da nossa aplicação de gestão de filas.

## Objetivo

O wrapper é uma **casca fina**: ele só abre a URL web do monitor numa janela em modo
kiosk e **destrava as políticas de autoplay do navegador** (áudio de chamada de senha +
vídeo do YouTube). Toda a lógica de negócio continua no web app — o wrapper **não tem e
nunca terá** código de feature.

**Regra de ouro:** features novas saem sempre pelo web app. O monitor pega no próximo
refresh. O wrapper só é rebuildado/redistribuído quando mudarmos configuração do próprio
shell (o que é raro).

```
┌─────────────────────────────┐
│  Wrapper Electron (este repo)│
│  - janela fullscreen / kiosk │
│  - autoplayPolicy off        │  ──loadURL──►  https://app.seudominio.com/monitor
│  - autostart no boot         │                (web app de produção, sem mudança)
│  - tela de reconexão         │
│  - auto-update do shell      │
└─────────────────────────────┘
```

## Por que o wrapper resolve

A política de autoplay do Chrome é uma permissão que o navegador **revoga periodicamente**
(volta a pedir o gesto do usuário depois de atualizações). Dentro do Electron, a flag
`autoplay-policy=no-user-gesture-required` é **definitiva** — o navegador não "repergunta".
Resolve o problema de uma vez, sem depender do cliente clicar em nada.

## Alvo

- **SO:** Windows (instalador NSIS `.exe`).
- **Auto-update:** self-hosted (electron-updater apontando para nosso bucket/CDN).
- **Cliente:** leigo → tem que ligar o PC e o monitor subir sozinho, sem interação.

---

## Estrutura do repositório

```
monitor-wrapper/
├── package.json
├── electron-builder.yml
└── src/
    ├── main.js        # processo principal: janela, autoplay, kiosk, update
    └── error.html     # tela de "reconectando" (cliente leigo)
```

---

## Arquivos

### `package.json`

```json
{
  "name": "monitor-wrapper",
  "version": "1.0.0",
  "main": "src/main.js",
  "scripts": {
    "start": "electron .",
    "dist": "electron-builder --win --publish always"
  },
  "devDependencies": {
    "electron": "^31.0.0",
    "electron-builder": "^24.13.3"
  },
  "dependencies": {
    "electron-updater": "^6.2.1",
    "electron-log": "^5.1.5",
    "auto-launch": "^5.0.6"
  }
}
```

### `src/main.js`

```js
const { app, BrowserWindow, powerSaveBlocker } = require('electron')
const { autoUpdater } = require('electron-updater')
const AutoLaunch = require('auto-launch')
const log = require('electron-log')
const path = require('path')

// 1) O CORAÇÃO DA SOLUÇÃO — destrava autoplay de áudio e vídeo, de forma definitiva.
//    (não é uma permissão revogável; o Chrome não vai "reperguntar" depois de atualizar)
app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required')

// URL do monitor. Em produção, definir por configuração (ver "Identificação do monitor").
const MONITOR_URL = process.env.MONITOR_URL || 'https://app.seudominio.com/monitor'

let win

function createWindow () {
  win = new BrowserWindow({
    fullscreen: true,
    kiosk: true,                 // trava em tela cheia, esconde barra/atalhos
    backgroundColor: '#000000',
    webPreferences: {
      autoplayPolicy: 'no-user-gesture-required', // redundância segura
      backgroundThrottling: false  // não pausa áudio/timer quando "sem foco"
    }
  })

  // 2) Não deixa a tela apagar (monitor de recepção fica ligado o dia todo)
  powerSaveBlocker.start('prevent-display-sleep')

  loadMonitor()

  // 3) Tela de erro própria + retry automático (essencial pro cliente leigo)
  win.webContents.on('did-fail-load', (_e, code, desc) => {
    log.warn('Falha ao carregar:', code, desc)
    win.loadFile(path.join(__dirname, 'error.html'))
    setTimeout(loadMonitor, 5000) // tenta reconectar sozinho
  })
}

function loadMonitor () {
  win.loadURL(MONITOR_URL).catch(err => log.error('loadURL', err))
}

// 4) Sobe junto com o Windows
new AutoLaunch({ name: 'Monitor de Filas' }).enable().catch(() => {})

app.whenReady().then(() => {
  createWindow()

  // 5) Auto-update do PRÓPRIO wrapper (raro, mas sem reinstalação manual)
  autoUpdater.logger = log
  autoUpdater.checkForUpdatesAndNotify()
  autoUpdater.on('update-downloaded', () => autoUpdater.quitAndInstall())
  setInterval(() => autoUpdater.checkForUpdates(), 6 * 60 * 60 * 1000) // a cada 6h
})

app.on('window-all-closed', () => app.quit())
```

### `src/error.html`

```html
<!doctype html><meta charset="utf-8">
<style>
  html,body{height:100%;margin:0;display:grid;place-items:center;
    background:#0b0b0b;color:#eee;font:600 28px system-ui}
  .dot{animation:b 1s infinite}@keyframes b{50%{opacity:.2}}
</style>
<div>Reconectando<span class="dot">…</span></div>
```

### `electron-builder.yml` (auto-update self-hosted)

```yaml
appId: com.seudominio.monitor
productName: Monitor de Filas
win:
  target: nsis
nsis:
  oneClick: true
  perMachine: true
publish:
  provider: generic
  url: https://downloads.seudominio.com/monitor/   # nosso bucket/CDN
```

---

## Identificação do monitor (qual fila exibir)

Cada instalação precisa saber qual monitor/fila exibir. Três caminhos, do mais simples ao
mais robusto — **escolher um**:

1. **Por instalador/atalho** — passa `MONITOR_URL` por variável de ambiente ou um build por
   cliente. Simples, mas multiplica builds.
2. **Tela de setup no 1º boot** — o wrapper salva a URL/código em
   `app.getPath('userData')`. O técnico cola o link uma vez na instalação. 1 build pra todos.
3. **Login no próprio web app** — o wrapper sempre abre `https://app/monitor`, e a tela web
   pede login/seleção de fila e guarda em cookie/localStorage. Zero config no shell.

> **Recomendado:** se a rota `/monitor` já tem login ou seleção de fila, use a **opção 3** —
> o wrapper fica exatamente do tamanho acima, sem nenhuma config local.

---

## Passos de instalação (para o ambiente de desenvolvimento)

```bash
# 1. Criar o repo com a estrutura acima e os arquivos
npm install

# 2. Rodar localmente apontando para uma URL de teste
MONITOR_URL=https://app.seudominio.com/monitor npm start

# 3. Gerar o instalador Windows e publicar no bucket de updates
npm run dist
```

O `npm run dist` gera o `.exe` (NSIS) **e** o `latest.yml`, publicando ambos na `url` do
`electron-builder.yml`. Os monitores já instalados leem o `latest.yml` e se atualizam
sozinhos.

---

## Checklist de produção

- [ ] Trocar `MONITOR_URL` / `appId` / `url` de download pelos valores reais.
- [ ] Definir a estratégia de identificação do monitor (seção acima).
- [ ] Assinar o instalador (code signing) para o Windows não bloquear / dar SmartScreen.
- [ ] Validar que o áudio de chamada de senha e o vídeo do YouTube tocam sem clique.
- [ ] Validar autostart após reiniciar o Windows.
- [ ] Validar a tela de reconexão (desligar a internet e ver se volta sozinho).
- [ ] Validar um ciclo de auto-update (subir versão `1.0.1` e confirmar atualização).

---

## O que este wrapper NÃO faz (de propósito)

- Não tem lógica de filas, senhas, players ou layout — isso é tudo do web app.
- Não duplica nenhuma feature → mantemos **um único repositório de produto** (o web app).
- Só muda quando precisamos mexer em config do shell (autoplay, kiosk, update, autostart).
```
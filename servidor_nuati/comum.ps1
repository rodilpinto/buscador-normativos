# servidor_nuati: funcoes usadas pelos outros scripts (carregado com ". comum.ps1").
# ORIGEM: github.com/rodilpinto/nuati-framework, pasta servidor_nuati/. Nao edite uma copia.
# Nasceu de checklist-conformidade/servidor/ (@ e06b826); mudancas no CHANGELOG.md.
# So ASCII neste arquivo: o PowerShell 5.1 le .ps1 sem BOM como ANSI.

$VersaoServidorNuati = "1.0.0"

# A pasta servidor_nuati/ fica na raiz do repo do app; o .venv, os logs e o .conf tambem.
$Raiz        = Split-Path -Parent $PSScriptRoot
$Venv        = Join-Path $Raiz ".venv"
$Python      = Join-Path $Venv "Scripts\python.exe"
$Iniciar     = Join-Path $PSScriptRoot "iniciar.cmd"
$ArquivoConf = Join-Path $Raiz "servidor_nuati.conf"

function Falha($msg) {
    Write-Host "[ERRO] $msg" -ForegroundColor Red
    exit 1
}

function Ok($msg) { Write-Host "[OK] $msg" -ForegroundColor Green }

function Exigir-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $admin = ([Security.Principal.WindowsPrincipal]$id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $admin) {
        Falha "Rode como Administrador (botao direito no PowerShell > Executar como administrador)."
    }
}

# ---------------------------------------------------------------------------
# servidor_nuati.conf (raiz do repo do app): CHAVE=valor, # comenta a linha.
# ---------------------------------------------------------------------------

$PadroesConf = [ordered]@{
    NOME_TAREFA  = ""                               # obrigatorio
    PORTA        = ""                               # obrigatorio
    PASTA_APP    = "."                              # relativa a raiz do repo
    ARQUIVO_APP  = "app.py"                         # relativo a PASTA_APP
    REQUIREMENTS = "requirements.txt"               # relativo a PASTA_APP
    CONFIG       = ".env,.streamlit/secrets.toml"   # basta existir um, relativo a PASTA_APP
    RAMO         = "main"                           # branch que o servidor roda
    LOG_MAX_MB   = "20"                             # acima disso, logs\app.log vira app.log.1 ao subir
}

function Ler-Conf([string]$Arquivo = $ArquivoConf) {
    if (-not (Test-Path -LiteralPath $Arquivo -PathType Leaf)) {
        Falha "Falta $Arquivo. Copie servidor_nuati\servidor_nuati.conf.example para a raiz do repo com o nome servidor_nuati.conf e preencha."
    }
    $conf = @{}
    foreach ($k in $PadroesConf.Keys) { $conf[$k] = $PadroesConf[$k] }
    $n = 0
    foreach ($linha in Get-Content -LiteralPath $Arquivo) {
        $n++
        $l = $linha.Trim()
        if ($l -eq "" -or $l.StartsWith("#")) { continue }
        if ($l -notmatch '^([A-Za-z_]+)\s*=\s*(.*)$') {
            Falha "servidor_nuati.conf, linha ${n}: esperado CHAVE=valor, veio '$l'."
        }
        $chave = $Matches[1].ToUpper()
        $valor = $Matches[2].Trim().Trim('"')
        if (-not $PadroesConf.Contains($chave)) {
            Falha "servidor_nuati.conf, linha ${n}: chave desconhecida '$chave'. Validas: $($PadroesConf.Keys -join ', ')."
        }
        $conf[$chave] = $valor
    }

    if ($conf.NOME_TAREFA -notmatch '^[A-Za-z0-9_-]+$') {
        Falha "servidor_nuati.conf: NOME_TAREFA e obrigatorio (so letras, numeros, _ e -)."
    }
    $p = 0
    if (-not [int]::TryParse("$($conf.PORTA)", [ref]$p) -or $p -lt 1024 -or $p -gt 65535) {
        Falha "servidor_nuati.conf: PORTA e obrigatoria, um numero entre 1024 e 65535."
    }
    $conf.PORTA = $p
    $mb = 0
    if (-not [int]::TryParse("$($conf.LOG_MAX_MB)", [ref]$mb) -or $mb -lt 1 -or $mb -gt 1024) {
        Falha "servidor_nuati.conf: LOG_MAX_MB deve ser um inteiro entre 1 e 1024."
    }
    $conf.LOG_MAX_BYTES = [int64]$mb * 1MB
    if ($conf.RAMO -notmatch '^[A-Za-z0-9._/-]+$') { Falha "servidor_nuati.conf: RAMO invalido." }

    $conf.PASTA_APP_ABS = [IO.Path]::GetFullPath((Join-Path $Raiz $conf.PASTA_APP))
    if (-not (Test-Path -LiteralPath $conf.PASTA_APP_ABS -PathType Container)) {
        Falha "servidor_nuati.conf: PASTA_APP nao existe: $($conf.PASTA_APP_ABS)"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $conf.PASTA_APP_ABS $conf.ARQUIVO_APP) -PathType Leaf)) {
        Falha "servidor_nuati.conf: ARQUIVO_APP '$($conf.ARQUIVO_APP)' nao existe em $($conf.PASTA_APP_ABS)"
    }
    $conf.REQUIREMENTS_ABS = Join-Path $conf.PASTA_APP_ABS $conf.REQUIREMENTS
    if (-not (Test-Path -LiteralPath $conf.REQUIREMENTS_ABS -PathType Leaf)) {
        Falha "servidor_nuati.conf: REQUIREMENTS nao existe: $($conf.REQUIREMENTS_ABS)"
    }
    return $conf
}

# Primeiro arquivo de configuracao do app que existe (lista CONFIG), ou $null.
# Ele fica DENTRO de PASTA_APP: a tarefa roda como SYSTEM, entao o ~/.streamlit/ e o do sistema, nao o seu.
function Achar-Configuracao($conf) {
    foreach ($c in ($conf.CONFIG -split ',')) {
        $c = $c.Trim()
        if ($c -and (Test-Path -LiteralPath (Join-Path $conf.PASTA_APP_ABS $c) -PathType Leaf)) { return $c }
    }
    return $null
}

# O servidor roda a branch RAMO (D-C22: o servidor espelha a main).
function Exigir-Ramo($conf) {
    git -C $Raiz rev-parse --git-dir 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { Falha "$Raiz nao e um clone git (o servidor atualiza com git pull)." }
    $atual = git -C $Raiz symbolic-ref --short -q HEAD 2>$null
    if ($LASTEXITCODE -ne 0) { $atual = "(nenhuma: HEAD solta)" }
    if ($atual -ne $conf.RAMO) {
        Falha "O clone esta na branch '$atual'; o servidor roda '$($conf.RAMO)' (RAMO do servidor_nuati.conf). Rode: git -C `"$Raiz`" switch $($conf.RAMO)"
    }
}

# ---------------------------------------------------------------------------
# Python, dependencias, processo e saude
# ---------------------------------------------------------------------------

# Python 3.10+. O "python" da Microsoft Store e so um atalho e nao serve.
function Achar-Python {
    foreach ($cand in @(@("py", "-3"), @("python"))) {
        if (-not (Get-Command $cand[0] -ErrorAction SilentlyContinue)) { continue }
        $extra = @($cand | Select-Object -Skip 1)
        $v = & $cand[0] @extra -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
        if ($LASTEXITCODE -eq 0 -and "$v" -match '^3\.(\d+)$' -and [int]$Matches[1] -ge 10) {
            return ,$cand
        }
    }
    return $null
}

function Instalar-Dependencias($conf) {
    Write-Host "Instalando dependencias ($($conf.REQUIREMENTS_ABS))..."
    & $Python -m pip install --disable-pip-version-check -q -r $conf.REQUIREMENTS_ABS
    if ($LASTEXITCODE -ne 0) {
        Falha ("pip falhou (mensagem acima). Causas comuns: proxy (defina HTTPS_PROXY e rode de novo) " +
               "ou caminho longo demais, WinError 206 (clone numa pasta curta, como C:\apps\<app>).")
    }
    Ok "dependencias instaladas"
}

# Processos escutando na porta: @{ Id; Linha } (Linha = linha de comando).
function Ouvintes-Da-Porta([int]$Porta) {
    $ids = Get-NetTCPConnection -LocalPort $Porta -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($id in $ids) {
        $p = Get-CimInstance Win32_Process -Filter "ProcessId = $id" -ErrorAction SilentlyContinue
        [pscustomobject]@{ Id = $id; Linha = $(if ($p) { $p.CommandLine } else { "" }) }
    }
}

# Para a tarefa e encerra o Streamlit que sobrar NA PORTA. Recusa matar qualquer outro programa.
# O Streamlit e reconhecido pela linha de comando: no Windows, o python.exe de um .venv e um lancador
# e quem escuta pode ser o Python base, como processo filho (LICOES do checklist, 01/10).
function Parar-App([string]$NomeTarefa, [int]$Porta) {
    if (Get-ScheduledTask -TaskName $NomeTarefa -ErrorAction SilentlyContinue) {
        Stop-ScheduledTask -TaskName $NomeTarefa -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
    foreach ($o in Ouvintes-Da-Porta $Porta) {
        if ($o.Linha -match "streamlit" -and $o.Linha -match "--server\.port $Porta(\s|$)") {
            Stop-Process -Id $o.Id -Force -ErrorAction SilentlyContinue
        } else {
            Falha "A porta $Porta esta ocupada por outro programa (PID $($o.Id): $($o.Linha)). Escolha outra PORTA no servidor_nuati.conf."
        }
    }
    Start-Sleep -Seconds 2
}

# Espera o Streamlit responder em /_stcore/health. Devolve $true se respondeu.
function Esperar-App([int]$Porta, [int]$Segundos = 90) {
    $fim = (Get-Date).AddSeconds($Segundos)
    while ((Get-Date) -lt $fim) {
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:$Porta/_stcore/health" -UseBasicParsing -TimeoutSec 5
            # Sem Content-Type, o PowerShell 5.1 devolve o corpo como bytes (o Streamlit manda text/html).
            $corpo = $r.Content
            if ($corpo -is [byte[]]) { $corpo = [Text.Encoding]::UTF8.GetString($corpo) }
            if ($corpo -match "ok") { return $true }
        } catch { }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Regra-Firewall($conf) { return "$($conf.NOME_TAREFA) (TCP $($conf.PORTA))" }

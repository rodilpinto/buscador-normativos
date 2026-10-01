# servidor_nuati: atualiza o app no servidor: git pull, dependencias e reinicio da tarefa.
# Rode como Administrador, na raiz do clone, depois de cada promocao (o servidor NAO atualiza sozinho):
#   powershell -ExecutionPolicy Bypass -File servidor_nuati\atualizar.ps1
# Tambem serve quando so a configuracao do app mudou: o app so le .env/secrets.toml ao subir.
# ORIGEM: github.com/rodilpinto/nuati-framework, pasta servidor_nuati/. Nao edite uma copia.

. (Join-Path $PSScriptRoot "comum.ps1")

Exigir-Admin
$conf = Ler-Conf
if (-not (Get-ScheduledTask -TaskName $conf.NOME_TAREFA -ErrorAction SilentlyContinue)) {
    Falha "A tarefa '$($conf.NOME_TAREFA)' nao existe. Rode antes servidor_nuati\instalar_tarefa.ps1."
}
Exigir-Ramo $conf

Set-Location $Raiz

# 1. Codigo novo. Alteracao local em arquivo versionado bloquearia o pull: avisa em vez de descartar.
$sujos = git status --porcelain --untracked-files=no
if ($sujos) {
    Falha "Ha alteracoes locais em arquivos versionados (git status). Resolva antes de atualizar:`n$sujos"
}
$antes = git rev-parse --short HEAD
git pull --ff-only
if ($LASTEXITCODE -ne 0) { Falha "git pull falhou (veja a mensagem acima). Nada foi reiniciado." }
$depois = git rev-parse --short HEAD

if ($antes -eq $depois) {
    Ok "ja estava na versao mais nova ($depois); reiniciando mesmo assim"
} else {
    Ok "codigo atualizado: $antes -> $depois"
    git log --oneline "$antes..$depois"
}

# 2. O .conf pode ter mudado com o pull: le de novo.
$conf = Ler-Conf
if (-not (Achar-Configuracao $conf)) {
    Falha "Falta a configuracao do app em $($conf.PASTA_APP_ABS) (um destes: $($conf.CONFIG)). Nada foi reiniciado."
}

# 3. Dependencias (rapido quando nada mudou)
Instalar-Dependencias $conf

# 4. Reinicio
Parar-App $conf.NOME_TAREFA $conf.PORTA
Start-ScheduledTask -TaskName $conf.NOME_TAREFA
Write-Host "Aguardando o app responder na porta $($conf.PORTA)..."
if (Esperar-App $conf.PORTA) {
    Ok "app no ar: http://$($env:COMPUTERNAME):$($conf.PORTA)/ (versao $depois)"
} else {
    Falha "o app nao respondeu em 90 s. Veja $Raiz\logs\app.log."
}

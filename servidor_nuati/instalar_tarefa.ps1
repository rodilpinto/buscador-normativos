# servidor_nuati: instala o app como tarefa agendada do Windows (sobe junto com o servidor, como SYSTEM).
# Rode UMA VEZ, como Administrador, na raiz do clone:
#   powershell -ExecutionPolicy Bypass -File servidor_nuati\instalar_tarefa.ps1
# Le tudo do servidor_nuati.conf (raiz do repo). Pode rodar de novo: refaz a tarefa sem duplicar.
# ORIGEM: github.com/rodilpinto/nuati-framework, pasta servidor_nuati/. Nao edite uma copia.

. (Join-Path $PSScriptRoot "comum.ps1")

Exigir-Admin
$conf = Ler-Conf
Exigir-Ramo $conf
Write-Host "servidor_nuati ${VersaoServidorNuati}: tarefa $($conf.NOME_TAREFA), porta $($conf.PORTA), app $($conf.PASTA_APP_ABS)\$($conf.ARQUIVO_APP)"

# 1. Ambiente virtual na raiz do repo
if (Test-Path $Python) {
    Ok "ambiente virtual ja existe (.venv)"
} else {
    $py = Achar-Python
    if (-not $py) {
        Falha "Python 3.10 ou mais novo nao encontrado. Instale de python.org (marque 'Add python.exe to PATH') e rode de novo."
    }
    Write-Host "Criando .venv com: $($py -join ' ')"
    $extra = @($py | Select-Object -Skip 1)
    & $py[0] @extra -m venv $Venv
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $Python)) { Falha "nao consegui criar o .venv" }
    Ok "ambiente virtual criado (.venv)"
}

# 2. Dependencias
Instalar-Dependencias $conf

# 3. Configuracao do app (nao vai para o git). Fica dentro de PASTA_APP.
$achou = Achar-Configuracao $conf
if (-not $achou) {
    Falha ("Falta a configuracao do app em $($conf.PASTA_APP_ABS): um destes: $($conf.CONFIG). " +
           "Copie o .example da propria branch $($conf.RAMO), preencha (valores internos no _sessao\INTERNO.md do app) e rode de novo.")
}
Ok "configuracao encontrada: $achou"

# 4. Tarefa agendada: sobe com o Windows, sem usuario logado, reinicia se cair
Parar-App $conf.NOME_TAREFA $conf.PORTA
Unregister-ScheduledTask -TaskName $conf.NOME_TAREFA -Confirm:$false -ErrorAction SilentlyContinue

$Action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"`"$Iniciar`" $($conf.PORTA) `"$($conf.PASTA_APP_ABS)`" `"$($conf.ARQUIVO_APP)`" $($conf.LOG_MAX_BYTES)`"" `
    -WorkingDirectory $conf.PASTA_APP_ABS

$Trigger = New-ScheduledTaskTrigger -AtStartup

$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

$Principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName $conf.NOME_TAREFA `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Streamlit (servidor_nuati $VersaoServidorNuati) na porta $($conf.PORTA). App: $($conf.PASTA_APP_ABS)\$($conf.ARQUIVO_APP)" `
    -ErrorAction Stop | Out-Null
Ok "tarefa '$($conf.NOME_TAREFA)' registrada"

# 5. Firewall do Windows (a liberacao da rede e outra camada). Regra de porta antiga desta tarefa sai.
$Regra = Regra-Firewall $conf
Get-NetFirewallRule -DisplayName "$($conf.NOME_TAREFA) (TCP *)" -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName -ne $Regra } |
    ForEach-Object { Remove-NetFirewallRule -Name $_.Name; Ok "regra antiga removida: $($_.DisplayName)" }
if (-not (Get-NetFirewallRule -DisplayName $Regra -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName $Regra -Direction Inbound -Protocol TCP -LocalPort $conf.PORTA -Action Allow | Out-Null
    Ok "regra de firewall criada: $Regra"
} else {
    Ok "regra de firewall ja existe: $Regra"
}

# 6. Sobe agora e confere
Start-ScheduledTask -TaskName $conf.NOME_TAREFA
Write-Host "Aguardando o app responder na porta $($conf.PORTA)..."
if (Esperar-App $conf.PORTA) {
    Ok "app no ar: http://$($env:COMPUTERNAME):$($conf.PORTA)/"
} else {
    Falha "o app nao respondeu em 90 s. Veja $Raiz\logs\app.log."
}

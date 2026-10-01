# servidor_nuati: tira o app do servidor (para, apaga a tarefa e as regras de firewall dela).
# Rode como Administrador, na raiz do clone:
#   powershell -ExecutionPolicy Bypass -File servidor_nuati\desinstalar_tarefa.ps1
# NAO apaga o clone, o .venv, os logs nem a configuracao do app.
# ORIGEM: github.com/rodilpinto/nuati-framework, pasta servidor_nuati/. Nao edite uma copia.

. (Join-Path $PSScriptRoot "comum.ps1")

Exigir-Admin
$conf = Ler-Conf

Parar-App $conf.NOME_TAREFA $conf.PORTA
if (Get-ScheduledTask -TaskName $conf.NOME_TAREFA -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $conf.NOME_TAREFA -Confirm:$false
    Ok "tarefa '$($conf.NOME_TAREFA)' apagada"
} else {
    Ok "tarefa '$($conf.NOME_TAREFA)' nao existia"
}
Get-NetFirewallRule -DisplayName "$($conf.NOME_TAREFA) (TCP *)" -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-NetFirewallRule -Name $_.Name; Ok "regra de firewall removida: $($_.DisplayName)" }
Ok "pronto. O clone, o .venv e os logs ficaram em $Raiz."

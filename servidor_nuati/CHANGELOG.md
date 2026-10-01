# Changelog do servidor_nuati

Versão atual: `$VersaoServidorNuati` em `comum.ps1`.

## 1.0.0 (01/10/2026): entra no nuati-framework, generalizado

Nasceu de `checklist-conformidade/servidor/` (servidor interno, `homologacao` @ `e06b826`; scripts de `13bc7dc` e
`9be45e2`), que o Rodrigo instalou e conferiu no servidor do Nuati em 01/10 (porta 8400 recusada por estar ocupada; app
no ar na 8401; health e página de outra máquina da rede; geração com o Gemini). Esse app, por sua vez, seguiu o modelo
do `instalar_servico.ps1` do pesquisa_diario. Pedido e guia: `_sessao/relatorio-servidor-nuati-para-framework.md` do
checklist.

A lógica é a mesma (tarefa SYSTEM ao iniciar, até 3 reinícios, `IgnoreNew`; firewall; health; `Parar-App` que só mata
o Streamlit da porta; `atualizar.ps1` com `pull --ff-only`). 📝 Mudanças propostas pelo Claude para servir a qualquer
app (seção 4 do relatório do checklist):

- tudo que era do checklist (nome da tarefa, porta, `app.py` e `requirements.txt` na raiz) foi para o
  `servidor_nuati.conf` do app; os scripts não aceitam mais `-Porta`/`-NomeTarefa` na linha de comando, para instalar
  e atualizar nunca divergirem;
- `PASTA_APP`: o `iniciar.cmd` entra na pasta do app (o buscador fica em `levantamento-normativos/`);
- configuração `.env` **ou** `.streamlit/secrets.toml`, dentro de `PASTA_APP` (a tarefa roda como SYSTEM);
- log rodado ao subir, acima de `LOG_MAX_MB`;
- `RAMO` (padrão `main`): instalar e atualizar recusam um clone em outra branch;
- `desinstalar_tarefa.ps1` (antes, comandos à mão no README);
- `--server.port <PORTA>` reconhecido com fronteira (8409 não casa com 84091);
- trocar a porta remove a regra de firewall antiga da mesma tarefa; o nome da regra passa a ser
  `<NOME_TAREFA> (TCP <PORTA>)` (no checklist era `checklist-conformidade (TCP 8401)`: na troca, apague a antiga à mão).

Testes novos (`test_servidor_nuati.py`, Windows, sem Administrador): ASCII e parser do PowerShell nos `.ps1`; leitura e
validação do `.conf` (padrões, subpasta, 11 erros); configuração dentro da pasta do app; branch errada recusada;
`Parar-App` recusa outro programa e encerra o Streamlit da porta; `Esperar-App`; `iniciar.cmd` entra na pasta e roda o
log. Registrar tarefa e firewall exige Administrador: conferência manual no passe.

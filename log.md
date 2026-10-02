# Log — Buscador de Base Normativa

<!-- entradas mais recentes no topo · formato: ## [data] operação | título -->

## [2026-10-01] servidor | buscador no servidor do Nuati (`servidor_nuati` 1.0.0, porta 8404, `v1.1.1`)

Passe do servidor (framework @ `36e888a`). D-C31: espelho no Gitea (F-A11 = a), `servidor_nuati` na `main` antes da v0.2.0
(F-A12), porta 8404. Linha de base TUDO VERDE (416), golden OK. `57f6b08`: `servidor_nuati/` (9/9 hashes), `.conf`, `logs/` no
`.gitignore`, `.gitattributes` (`.ps1`/`.cmd` CRLF); 32 testes do recurso. Remoto `camara` criado; `main` = `v1.1.1` = `57f6b08`
no GitHub e no Gitea. No servidor (Rodrigo): `instalar_tarefa.ps1` ok; health `ok` e página 200 vistos deste PC; app subiu
**sem LLM** por BOM no `secrets.toml` (LESSONS) e sem `LLM_MODEL`, corrigido; `atualizar.ps1` ok (2x). Busca vista deste PC:
cadeia começando no `local`; 29 palavras-chave em 44 s e relevância 22/22 `(modelo)` pelo `local (google/gemma-4)`
(`LLM_DISABLE_THINKING=1`); busca inteira 140 s; LexML/TCU indisponíveis ou parciais; tempo economizado 9h22min. Categorização:
não legível pela tela (tabela em canvas); conferir no `logspp.log` do servidor. Registro no framework: `937b9a0`.

## [2026-10-01] promoção | `homologacao` → `main` como `v1.1.0`

Ok do Rodrigo ("subir o homologação para main uma vez q ele está estável"), com a F-A3 do framework aprovada junto (D-C30). Ele
colou na produção os Secrets da homologação e deu Reboot; depois fast-forward `main` `e2cd56a` → `829e71e`, tag anotada `v1.1.0`,
push. Conferido no ar: `buscador-normativos.streamlit.app` com título e rodapé da Câmara, cadeia na barra lateral, geração de
palavras-chave com "Última resposta: gemini (gemini-3.5-flash-lite)". O contador do Passo 5 é o mesmo código conferido na
homologação. App `-teste`: Rodrigo pode apagar (B-11).

## [2026-10-01] migração | passe por app do nuati-framework: `main`/`homologacao`, framework na homologação

Sessão no PC do trabalho, prompt do passe (framework @ `56d7eb0`, branch `homologacao` do framework; sem tag `v0.1.0`).
- Passo 0: `master` local estava 11 commits atrás; `git fetch` + fast-forward até `e22822e`. Cópia do `llm_cadeia` = 7/7 hashes
  do framework @ `b301593`. Mapeamento confirmado pelo Rodrigo (D-C27); branding incluído (D-C28).
- Passo 1: tags `pre-framework-2026-10-01-deploy` (`e2cd56a`) e `pre-framework-2026-10-01-master` (`e22822e`).
- Passo 2: linha de base vermelha **por ambiente** (LESSONS de 01/10); golden OK.
- Passo 3 (`homologacao`): `9fd1939` llm_cadeia 1.1.0 (9/9 hashes) · `1a9ddb7` branding 1.0.0 (29/29) · `0a74ddb` runner com
  `LLM_SOMENTE=nenhum` · `e6861b3` tempo_economizado 1.0.0 (6/6) no Passo 5 (D-C29). Runner TUDO VERDE (416 testes, 6 min),
  golden OK. `python -m llm_cadeia`: local, gemini, gemini-2, groq-2, cerebras-2, openrouter-2 responderam. App local: palavras-chave
  e notas pelo `local (google/gemma-4)`; categorização vazia (LESSONS).
- Passo 4: `main` = `e2cd56a` (= `deploy` = v1.0.1), sem framework.
- Passos 6-7: Rodrigo recriou `buscador-normativos` (`main`) e criou `buscador-normativos-homologacao` (`homologacao`).
  Conferido no ar: produção igual a antes (título "NUATI", só Gemini, 30 palavras-chave); homologação com branding, cadeia na
  barra lateral, "Última resposta: gemini (gemini-3.5-flash-lite)", 30 palavras-chave. A cadeia de lá não tem `local` (B-12).
- Passo 8 (ok do Rodrigo): `main` padrão no GitHub; apagadas `master`, `deploy`, `frente2/trilha-a`, `frente2/trilha-b`
  (remoto) e `master`, `llm-cadeia-1.0.1` (local). App `-teste`: B-11.
- Pedidos ao framework (`_TODO.md`, seção "Pedidos ao nuati-framework").

## [2026-09-29] decisão | D-C26 = `a`: apps seguem públicos; faturamento desligado nos dois projetos Google

Rodrigo conferiu no console: faturamento desligado nos projetos das duas chaves Gemini. Pior caso de uso por terceiros = cota
esgotada (o app degrada para "sem IA"). Ligar faturamento reabre a D-C26.

## [2026-09-29] correção | os apps do Streamlit são PÚBLICOS (não privados); nova D-C26

O Rodrigo conferiu o painel: seis apps, **todos públicos**, e salvou os Secrets de cada um fora do repo. "Privado" vinha de
22/09 e nunca tinha sido conferido no painel — corrigido no state file (§2 e §8) e na D-C14. A lista do painel também confirma
que a produção do scopediagram serve `main` e revela um sexto app, `dou-clipping-app` (`master`). Nova 🔴 **D-C26**: app
público gasta as chaves de LLM do app; faturamento dos projetos Google **não conferido**. Orientação dada: não apagar apps
agora — a recriação acontece no passe por app, depois das branches novas.

## [2026-09-29] decisão | D-C25 = `a`: `Nuati-SECIN/framework` vira espelho interno do `nuati-framework`

Rodrigo escolheu `a`. Registro na D-C25 (`_DECISOES-PENDENTES.md`). O prompt da sessão do framework (entregue na conversa)
leva `a` no campo da D-C25; ela roda no PC do trabalho, numa pasta nova e vazia (não na pasta do repo interno).

## [2026-09-29] relatos | pausa das sessões para o framework: scopediagram, checklist, levantamento

Os três relatos voltaram. Conferido aqui por `git ls-remote`: scopediagram `feat/llm-cadeia` = `9d52dc5`, `main` = `0b5aee1`
(repo **público**, 30 commits varridos, sem chave); checklist no GitHub `feat/llm-cadeia` = `da8ccd4` (1.0.0) e `master` =
`090aa67` — o `92ac158` do relato está **só** no servidor interno. O levantamento está em `Nuati-SECIN/framework` (git.camara,
`master` @ `4c751ba`), repo criado em 28/09 → nova 🔴 **D-C25** (o que fazer com ele). A sessão do checklist listou 5 pedidos
para o `llm_cadeia` (timeout do Gemma, desligar raciocínio, dados internos na pasta, forçar um só provedor, Gemini sem
timeout) — entram no prompt do framework, não aqui (D-C24). Padrão observado nos dois apps: a entrada de log cita o hash
**anterior** ao commit que a grava; vale o hash da branch.

## [2026-09-29] decisão | depois da reunião: dois ambientes (`main`/`homologacao`) e framework central `nuati-framework`

Reunião passou; o Rodrigo liberou o push (os 2 commits do checkpoint subiram: `a76b6c0`). Decisões D-C22 (dois ambientes;
servidor do Nuati espelha `main`), D-C23 (framework em repo próprio e privado, origem única do compartilhado; passe por
app faz adoção + migração de branches juntas) e D-C24 (`llm_cadeia/` congelado aqui a partir de agora). O framework
parte da `llm_cadeia` 1.0.1 **deste repo no commit que grava esta entrada** (ver `git log -1 -- log.md`); a cópia do
checklist (1.0.0) não serve de fonte. Marcação de supersessão dentro do README do `llm_cadeia` (sem mudança de código, versão
segue 1.0.1). Prompts das 4 sessões entregues ao Rodrigo na conversa.

## [2026-09-29] checkpoint | cadeia de LLM (23–28/09) e congelamento da versão ao vivo para a reunião

Sessão longa, de 23/09 a 29/09, sobre o LLM. Cadeia de commits: `git log --oneline --reverse 0dd60b4..HEAD`. Resumo: cadeia de
provedores com rodízio de modelos e chave do usuário (`de9f616`) → módulo copiável `llm_cadeia/` 1.0.0 (spec `fb6f2a9`,
código `affc13f`) → verificação ao vivo nos 5 provedores → 1.0.1 vinda do scopediagram (`98d955e`). Decisões D-C18 a D-C21.
Ledgers: frente 5 🟡 com veredito por insumo (o (f) reproduzido hoje); B-08, B-09, B-10 novos; D-C17 com prazo vencido
declarado; D-C14 com a contradição "1 app privada por conta" × dois apps. Lição nova no `LESSONS.md` (modelo que pensa →
resposta vazia). `~/.claude/ENVIRONMENT.md` ganhou o arquivo de chaves e o que o PC do trabalho alcança. ⚠ Checkpoint
**commitado e NÃO empurrado**: hoje é o dia da reunião e push em `master` redeploya o app de teste (reserva). Snapshot de
memória **não** escrito (política de autorização) — perguntado ao Rodrigo.

## [2026-09-28] merge | `llm_cadeia` 1.0.1 no `master` (vinda da adoção no scopediagram)

Branch `llm-cadeia-1.0.1` (`98d955e`) revisada linha a linha e integrada por fast-forward; baseline do runner 19 → 23
(`3f4e61c`); runner TUDO VERDE aqui (as 8 falhas de `test_fontes_indisponiveis.py` relatadas na máquina da Câmara não
se reproduzem aqui = rede de lá). `master` empurrado com ok do Rodrigo (só o app de teste redeploya; `deploy` conferida
em `e2cd56a`); branch remota apagada. Checklist v2 = repo público `rodilpinto/checklist-conformidade`: `master` = app ao
vivo, `feat/llm-cadeia` = app de teste; varredura de chaves nos dois ramos e no histórico: nenhuma.

## [2026-09-28] feat | `llm_cadeia` 1.0.1: achados da adoção no `scopediagram` (máquina na rede da Câmara)

Primeira adoção do módulo fora do buscador (`scopediagram`). Verificado ao vivo lá: Gemma do Nuati (`google/gemma-4`)
com `sistema=` + `json=True` → `json.loads` OK (antes "não verificado"); a rede da Câmara deixa passar gemini, groq,
cerebras e openrouter. Correções: "Última resposta" na mesma execução (gancho `ao_responder`; verificado no app do
scopediagram sem `st.rerun()`); OpenAI de raciocínio repete com `max_completion_tokens` (⚠ só dublê); docstrings
desatualizadas. Módulo: 23 passed (19 + 4). Suíte `tests/` + `test_llm_phase3.py`: 8 failed / 58 passed, **as mesmas 8
falhas no `3edba4d` sem as mudanças** (`tests/test_fontes_indisponiveis.py`, DDG/Google; não é regressão do módulo).
Commit local no `master`; ⚠ push aguardando o Rodrigo (nota de 28/09 abaixo: não empurrar `master` até a reunião).

## [2026-09-28] deploy | app de teste `buscador-normativos-teste` (branch `master`); `deploy` intocada antes da reunião

`master` empurrado (`affc13f`); `origin/deploy` conferido igual antes/depois (`e2cd56a`). Rodrigo criou o app de teste
(Python 3.14, Secrets = `~/.llm-chaves.toml`) e confirmou: IA gerou palavras-chave, status lista gemini, gemini-2, groq-2,
cerebras-2, openrouter-2; a chave do usuário funcionou. Diagnóstico local ao vivo: os 5 provedores pontuam e categorizam
(categorias idênticas); `gemini-3.5-flash-lite` estava em 503 nas duas chaves — o app ao vivo (v1.0.1) não tem fallback.
Busca no app de teste: LexML `bloqueio_waf`/503 (B-05, conhecido desde 22/09, não é regressão). ⚠ `GROQ_API_KEY_2`
apareceu no contexto da conversa (seleção no editor) → trocar depois da reunião. Não empurrar `master` até a reunião.
Depois, a pedido do Rodrigo ("commit and push"): teste ao vivo de `sistema=` + `json=True` nos 5 provedores → JSON válido
em todos; `master` empurrado (redeploy do app de teste só com docs).

## [2026-09-28] feat | `llm_cadeia/` — módulo de LLM copiável para todas as soluções

Decisão do Rodrigo: distribuir por **copiar e colar** (não serviço nem pip); origem neste repo; destino final servidor
do Nuati + cópia no Streamlit Cloud (portfólio). Spec `docs/superpowers/specs/2026-09-28-llm-cadeia-portatil-design.md`,
plano `docs/superpowers/plans/2026-09-28-llm-cadeia-portatil.md`. `llm/cadeia.py` → `llm_cadeia/nucleo.py` (git mv);
novos: `Resposta` (texto/origem/tentativas), `sistema=`, `json=`, `_2` para todo serviço, `painel_llm()` (saiu do
`app.py`), `python -m llm_cadeia`, README com instrução para as outras sessões. Achado no diagnóstico real:
gemini-2.5-flash e gemma-4 devolvem **vazio** com orçamento de tokens pequeno (pensam antes) → piso de 4096 no Gemini.
Outros apps com LLM achados: `projeto-nuati-diagrama-de-escopo` (JSON + schema), `projetos-nuati-checklist`.

## [2026-09-25] feat | cadeia de LLM: rodízio de modelos, serviços gratuitos, chave do usuário; vira módulo genérico

Pedido do Rodrigo (esgotar Gemini; padrão para outros apps). A cadeia saiu de `gemini_client.py` para `llm/cadeia.py`
(sem import do projeto); `gemini_client` ficou com prompts/parsing e wrappers (`_generate`, `is_available`). Novidades:
(1) cada provedor tem lista de modelos — 429/503 param só o modelo (429 diário até a meia-noite do Pacífico), chave
inválida/rede param o provedor; (2) presets Groq, Cerebras, OpenRouter (`*_API_KEY`, `*_MODELS`); `LLM_ORDEM`;
(3) campo "Usar minha própria chave de IA" na barra lateral, por sessão (ContextVar), na frente da cadeia. Verificado:
cota do Gemini = por projeto e por modelo (docs + quotaId); 7 modelos Gemini responderam a chamada real; rodízio real
(404 → próximo modelo) conferido; `test_cadeia_llm.py` 7 → 14; runner TUDO VERDE; AppTest da barra lateral sem exceção.
⚠ Groq/Cerebras/OpenRouter sem teste com chave real. LESSONS 25/09. `deploy` segue em `v1.0.1`.

## [2026-09-23] feat | cadeia de LLM A > B > C (urgente, antes da frente 5)

Pedido do Rodrigo: não depender de uma só cota Gemini. `llm/gemini_client.py` troca o cliente único por uma cadeia:
A = servidor OpenAI-compatível (`LLM_BASE_URL`/`LLM_MODEL`/`LLM_API_KEY`), B = `GEMINI_API_KEY` (nuati.secin),
C = `GEMINI_API_KEY_2` (chave pessoal). Falha → espera (cota 15 min, erro 5 min) e passa ao próximo; resposta vazia NÃO
troca de modelo. Prompts e parsing intocados. Barra lateral mostra a ordem e quem está em espera (nunca a chave).
Versão mínima do protocolo de backend da frente 5 (plano de 16/09, T5/T6), mesma ordem. Teste: `tests/test_cadeia_llm.py`
(7, sem rede) no runner; runner TUDO VERDE; chamada real ao Gemini pela cadeia conferida. ⚠ O LM `10.10.111.125` é intranet:
inalcançável do Streamlit Cloud. `deploy` segue em `v1.0.1` até o ok do Rodrigo.

## [2026-09-23] checkpoint | frente 2 encerrada (fase 5): worktrees limpos, evidência preservada

T10 em `master` (`9b4d9dd`). Limpeza: 6 worktrees removidos depois de copiar a evidência de cada um para
`tests/evidencia/<worktree>/` (ignorada, local; contagem conferida arquivo a arquivo); branches locais `t9`, `fix-*`, `t10`
apagadas; `frente2/trilha-a`/`-b` ficam (remoto atrás) → B-07. Execução por agentes encerrada: `execucao/` vira registro.
Próxima: frente 5 (LM local). 🔴 D-C17 aberta. Snapshot de memória não escrito (política de autorização).

## [2026-09-23] review | T10: state file enxugado (§3/§7/§8 históricos arquivados aqui); SSOT dos números do fechamento

Review da T10 (testador APROVADO; reviewer: aprovável com consertos). O `SESSION-ONBOARD` caiu para perto de 1 página:
§3 itens 1–4 e 8–9, a tabela de ponteiros do §7 (→ `CLAUDE.md`), o histórico das linhas "Chave do LLM" e "Hospedagem"
do §8 e os avisos antigos (assimetria de branch, `R1-*`, 6.533/6.561, receita da D-C9 → D-C9) estão abaixo, verbatim.
Também: "336" deixou de ser restatado (`implementacao/10-fechar-frente.md` é a casa); LESSONS ganhou as linhas de
Cobertura e a causa-raiz que faltavam; D-C17 com a faixa `:256-286`.

<details><summary>Arquivado do <code>SESSION-ONBOARD-buscador.md</code> na review da T10 (linhas removidas ou reescritas, verbatim, na ordem do arquivo; a receita da D-C9 também foi para a D-C9 em <code>_DECISOES-PENDENTES.md</code>)</summary>

 (`7322cc0`) + FIX-SAÍDA (`51883f6`) → T10. Critérios §7 conferidos: runner **336 TUDO VERDE**, golden OK,
 `dedup_esperado.json` = `d054d5b`, **V11 7/7**. Registro completo: `spec/frente2-honestidade-fontes/execucao/` (TODOS =
 **Ferramentas:** `python tools/run_all_tests.py` (≈9 min — as suítes LIVE batem em fontes quebradas) e
 1. **O projeto NÃO é greenfield.** O app `levantamento-normativos` existe desde março/2026 em
    `~/Documents/projeto-nuati-normativos-levantamento/`: **205 testes verdes** medidos em 16/09 (13+53+98+41),
    busca por API (LexML SRU/CQL, TCU Dados Abertos, Google CSE/DuckDuckGo). A spec de 08/09 dizia
    o contrário — a varredura dela não cobriu essa pasta. Detalhe em `LESSONS.md`.
 2. **A decisão B2 foi REVERTIDA:** a base é o **Streamlit já escrito**, não um FastAPI novo.
 3. **(Plano de 16/09 apenas — v2.0)** Precedência das emendas: C > B > A > corpo; cada seção do corpo
    derrubada carrega um marcador `⛔` apontando a emenda. **O plano da frente 2 não tem isso: está dobrado.**
 4. **(Plano de 16/09 apenas)** A ordem das tasks não é a numeração (emenda A1). No plano da frente 2,
    **ordem = numeração**.
 8. **As duas fontes catalogadas estão quebradas hoje (medido 22/09):** LexML `/busca/SRU` atrás de desafio
    de JavaScript do Senado (200 `text/html`; fallbacks 404; sem conserto legítimo → B-05); TCU
    `atonormativo` em 500 e, pior, a API de acórdãos **não devolve `ementa`/`numero`/`ano`** — o código lia
    só isso, então todo acórdão colapsa num id e nunca casa. Só a web aberta (DuckDuckGo; `GOOGLE_CSE_ID`
    vazio) traz resultado. A frente 2 conserta o que dá; detalhe em `LESSONS.md` (22/09).
 9. **Fixture real do TCU** em `levantamento-normativos/tests/fixtures/tcu_acordaos_real.json`; o HTML real do
    desafio do Senado em `lexml_desafio_senado.html`. Fixtures de API são captura, não redação.
 | Doc | Papel |
 |---|---|
 | `docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md` | **spec da frente 2** (em execução) |
 | `docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md` | **plano v4 da frente 2** — tudo dobrado no corpo; ordem = numeração; **fonte de verdade** |
 | `spec/frente2-honestidade-fontes/` | **split do plano v4** (22/09, D-C16): `00-overview.md` (5 fases, dependências) + `tasks/01..10` (verbatim + critérios de aceite) + `reference/` — é o que o subagente lê |
 | `docs/superpowers/specs/2026-09-16-consolidacao-buscador-design.md` | spec da consolidação (arquitetura; vale) |
 | `docs/superpowers/plans/2026-09-16-consolidacao-fase1.md` | plano da Fase 1 — T3/T1/T2/T9 **feitas**; T5/T6 viraram a frente 5; T4/T7/T8 = **v2.0** (emendas no topo, D-C9) |
 | `_TODO.md` · `_DECISOES-PENDENTES.md` · `log.md` | status · decisões · timeline |
 | `LESSONS.md` · `BLOCKED-ON-RODRIGO.md` | lições transversais · o que espera o humano |
 | `decisions/DECISIONS-LOG.md` + o board `.html` | as rodadas de decisão, com os comentários |
 | ⛔ `docs/.../2026-09-08-*` e `spec/buscador/tasks/` | **SUPERADOS**, histórico apenas |
 | **Chave do LLM no app da nuvem** | Chave Gemini do projeto Google **`nuati.secin`**, gravada pelo Rodrigo em 22/09 nos *Secrets* do app `buscador-normativos` (share.streamlit.io) — **o valor nunca passa pelo chat nem pelo repo**. O v1.0 só lê o segredo **`GEMINI_API_KEY`** (`llm/gemini_client.py:58`, SDK `google-genai`, modelo **`gemini-3.5-flash-lite`** desde 22/09 — o `2.5-flash-lite` dá 404 para chave nova). ⚠ O segredo só é lido **no import do módulo**: depois de mudar Secrets, **Reboot app**. O app antigo `levantamento-normativos.streamlit.app` foi **apagado** pelo Rodrigo em 22/09. ⛔ **Não criar `levantamento-normativos/.streamlit/secrets.toml` nesta máquina até a frente 5:** `st.secrets` vence a variável vazia do runner e a suíte passaria a chamar o Gemini de verdade. Para LLM local, variável só no terminal do `streamlit run`. |
 | Hospedagem / deploy | ⚠ **CORRIGIDO 22/09 (noite):** existe **deploy no Streamlit Community Cloud** — `https://levantamento-normativos.streamlit.app/`, apontado pelo Rodrigo. Prova: GET → `303` para `share.streamlit.io/-/auth/app` (app **privado**, exige login). A verificação anterior ("nenhum") só olhou arquivos do repo, e deploy no Community Cloud **não deixa rastro no repo**. Esse app vinha do **repo A** (confirmado pelo Rodrigo). ✅ **22/09 (noite): redeploy a partir deste repo B** → **`https://buscador-normativos.streamlit.app/`**, privado (GET → `303` para login), branch **`master`** (única branch de B; `main file` = `levantamento-normativos/app.py`). Streamlit recebeu acesso a repo privado; B **segue privado** (decisão do Rodrigo, depois de ver o que ficaria exposto: IP interno, nomes, ledgers — nenhum segredo no histórico). ⚠ **Branch do deploy: `deploy`**, não `master` (22/09) — congelada em `v1.0.1`; **só avança num marco, com ok do Rodrigo**
 (`git push origin master:deploy`). ✅ Rodrigo trocou o app para `deploy` em 22/09 e confirmou a IA gerando palavras-chave (precisou regravar o segredo + reboot). ❓ O app antigo (`levantamento-normativos.streamlit.app`) ainda responde `303` em 22/09 — apagar ou não é do Rodrigo (B-06 item 4). Único outro endereço de infra: o LM local `10.10.111.125:1234` (D-C5). Nenhuma org da Câmara visível no `gh` deste token (só `neuko-repo`). |
 
 ⚠ **Assimetria de branch:** A usa `main`, B usa `master`. No merge (T3) isso aparece como
 `git fetch levantamento` + `levantamento/main`, enquanto o push daqui é `origin master`.
 
 ⚠ **Namespace `R1-*` tem dois significados:** no plano de 08/09 são as emendas de 2026-09-11; na
 revisão de 16/09 os achados brutos foram numerados à parte. Diga sempre de qual documento.
 
 ⚠ **A mensagem da tag de rollback é imutável e cita `6.533 linhas`** — medição antiga, que omitia
 `llm/__init__.py`. O valor correto é **6.561** (`git ls-files 'levantamento-normativos/*.py' | xargs wc -l` — ⚠ só o app; `'*.py'` cru soma `tools/`, medido em 22/09: 6.849).
 
 **Fechar a D-C9** quando respondida (só importa na v2.0): mover para 🟢 em `_DECISOES-PENDENTES.md` com a
 data, abrir seção em `decisions/DECISIONS-LOG.md`, fechar `B-02` no `BLOCKED-ON-RODRIGO.md`.

</details>

## [2026-09-23] fechamento | frente 2 (honestidade das fontes) fechada — T10; próxima: frente 5

Depois da fase 4, a revisão final do estado combinado (`d4cab80`, 5 lentes: spec, segurança, testes com mutação,
manutenção, UX do app real) achou o que nenhuma revisão por task viu: **fórmula na aba Normativos** (crítico de segurança),
o aviso "nenhuma fonte catalogada entregou" com o TCU entregando (bloqueador), o TCU parcial chamado de indisponível, a
legenda do 0% falsa por acento e a janela do TCU escondida. Triagem (`execucao/revisoes/final-triagem.md`) → duas trilhas
de conserto com ciclo completo: **FIX-FONTES** (em master `7322cc0`: SSRF com revalidação por salto, LexML/TCU/Google nos
cantos, janela do TCU no detalhe, heurística sem acento, CQL dublado) e **FIX-SAÍDA** (em master `51883f6`: toda célula de
texto como string literal, "Parcial" na tela e na planilha, Passo 3 não verde com tudo indisponível, caractere de controle
não derruba a exportação). **T10:** critérios da spec §7 conferidos no worktree `bn-t10`: runner **336 TUDO VERDE** sem
`[AVISO] cresceu`, golden OK, `dedup_esperado.json` idêntico ao de `d054d5b`, **V11 7/7** (app sem chaves de LLM),
auditoria de docs sobre `1c063ea..HEAD` (a faixa `dc99d73..HEAD` do plano sai vazia por construção, porque a base não tem
nenhum `.py`; lição nova). Comandos e saídas: `spec/frente2-honestidade-fontes/implementacao/10-fechar-frente.md`.
Duráveis atualizados (`_TODO.md`, B-04, D-C17, `LESSONS.md` com 7 entradas, `SESSION-ONBOARD`). 🔴 **D-C17 fica aberta
e declarada**: o conserto vira task própria. Não foram feitos: o `deploy` (⛔ intocado), o push, o `/checkpoint` da fase 5
e a limpeza dos worktrees (os três ficam com o orquestrador).

<details><summary>Arquivado do <code>SESSION-ONBOARD-buscador.md</code> na T10 (texto substituído em §2/§6, verbatim; só os títulos de seção viraram <code>####</code>)</summary>

#### (§) 2. Estado na última pausa (2026-09-23, checkpoint da fase 4 da frente 2)

▶ **Frente 2 (honestidade das fontes) EM EXECUÇÃO desde 22/09 (noite), por agentes.** Plano v4 dividido em
`spec/frente2-honestidade-fontes/` (D-C16). **Status por task: `spec/frente2-honestidade-fontes/execucao/TODOS.md`
(SSOT)**; regras do orquestrador e trilhas: `execucao/CONTEXTO.md`; briefs dos agentes: `execucao/BRIEFS.md`.
✅ **T1–T9 em `master` (fases 1–4 fechadas)** — trilha B desde `9e259ca`, trilha A desde `08d9d8c`, T9 desde `d4cab80`
(V11 7/7; runner + golden OK). ▶ **Revisão final** de 5 perspectivas rodando sobre `d4cab80` — ver "Trabalho em voo" em §6.
Faltam: revisão final → coder aplica os achados → (D-C17, se o Rodrigo decidir consertar nesta frente) → T10.
Os worktrees `../bn-trilha-a`, `../bn-trilha-b` e `../bn-t9` ficam até a T10 (guardam os screenshots de evidência, não versionados);
as branches deles já estão em `master`.

**Cadeia da sessão de 22–23/09:** rode `git log --oneline --reverse 1c063ea..HEAD` (é longa e cresce a cada task;
não é mais restatada aqui). Marcos: `da543be` T1 · `a6de0af` checkpoint fase 1 · `9e259ca` merge da trilha B.
Sessões anteriores: `git log`. ⚠ **O SHA mais novo listado aqui está SEMPRE um passo atrás do commit que gravou
este arquivo** — a cadeia real termina em `git log --oneline -3`. ⚠ Commits das trilhas vivem nas branches
`frente2/trilha-*` até o merge.

#### (§) 6. Próximo movimento

▶ **Frente 2 EM EXECUÇÃO.** Ler `spec/frente2-honestidade-fontes/execucao/CONTEXTO.md` e `TODOS.md` (SSOT)
**antes de tudo**. Regra do Rodrigo (22/09): **o orquestrador não escreve código** — despacha, por task, coder
(implementa) → coder (testa + e2e Playwright) → code-reviewer → o mesmo coder aplica o review e documenta em
`spec/frente2-honestidade-fontes/implementacao/NN-*.md`; `/checkpoint` a cada fase; no fim, reviewers de várias
perspectivas, depois a T10. Briefs prontos em `execucao/BRIEFS.md`.

**Trabalho em voo no checkpoint da fase 4 (23/09):** 5 reviewers finais, só leitura, sobre `master` `d4cab80`:
conformidade com a spec; segurança; qualidade dos testes e gates (com mutação); manutenibilidade + preservação de docs;
UX do app real (Playwright, porta 8531). **Onde cai:** o orquestrador grava cada veredito em
`execucao/revisoes/final-<perspectiva>.md`. **Se a sessão morreu antes:** despachar de novo os que não têm arquivo (os
perspectivas, slugs e o que cada um faz estão na linha "reviewers do estado final" de `execucao/TODOS.md`; custo: ~5 agentes). **Onde o resultado cai:** commits na branch do worktree da vez (`git worktree list`; `git -C <worktree> log
--oneline master..`). **Se a sessão morreu com ele no meio:** `git -C <worktree> status`
— árvore suja = task pela metade: despachar um coder novo com o brief 1 de `BRIEFS.md` mandando **conferir o
estado contra os steps da task e continuar** (não recomeçar); árvore limpa com commit = seguir para o brief 2
(teste). Worktrees criados com `git worktree add -b frente2/trilha-X ../bn-trilha-X master`.
**Casos do trabalho em voo:** árvore limpa sem commit = task nem começou → brief 1; commit + árvore suja = fix/doc
pela metade → brief 4 com `execucao/revisoes/T{N}.md`; na dúvida, `git -C <wt> log -1 --stat` e o `TODOS.md` dizem o passo.
**Próximo passo agêntico:** triar os 5 vereditos finais (bloqueador/importante → coder aplica num worktree novo, com
teste + re-teste; menor → `_TODO.md` P3) → **T10** (critérios §7, duráveis, LESSONS, limpeza dos worktrees) →
`/checkpoint` fase 5.

Decisões abertas que **não** travam: D-C9 (só volta na v2.0), D-C14 (deploy), 🔴 **D-C17** (dedup fuzzy funde acórdãos
distintos — não trava a execução, mas é perda silenciosa até o Rodrigo decidir). (D-C10.1 fechada em 22/09:
tags só nos marcos.) ⛔ **Não avançar a branch `deploy`** durante a frente 2 — só no marco, com ok. Ações do
Rodrigo pendentes: B-01 a B-06 (`BLOCKED-ON-RODRIGO.md`) — nenhuma trava a frente 2.

</details>

## [2026-09-23] checkpoint | frente 2, fase 4 fechada: T9 em master; revisão final despachada

T9 (tela) fechou o ciclo e entrou em `master` em `d4cab80`: relatório por motivo, aviso por fonte (TCU "respondeu
parcialmente" ≠ indisponível), pontuação sempre (heurística sem LLM, com a origem no card/preview/planilha), a aba de
diagnóstico com os status reais e hora BRT; gate visual **V11 7/7**. Além do plano: o **escape HTML duplo** (item carregado
da T2/T3) e, no review, o **texto da fonte formatado como Markdown/LaTeX no card** (`R$ … R$` sumia) — os dois consertados
com helpers e testes que falham no padrão velho; a sugestão do testador para o F1 escaparia em dobro e foi trocada pela do
reviewer. Revisão final: 5 reviewers de perspectivas diferentes sobre `d4cab80`. 🔴 D-C17 segue aberta.

## [2026-09-23] checkpoint | frente 2, fase 2 fechada: trilha A (T2–T5) em master

Trilha A entrou em `master` em `08d9d8c` (conflito só no `BASELINE` de `tools/run_all_tests.py`, previsto pelo dogfood com
`git merge-tree`; dois lados mantidos; runner 291 + golden OK no merge). Achados da trilha que viraram código além do
plano: **T4** — o testador **reprovou**: acórdãos da 1ª e 2ª Câmara colidiam no `id` e no dedup (212 colisões, ~1.175
fusões em 3.200 reais) → `numero` na forma de citação do TCU com o colegiado literal; efeito colateral: o dedup fuzzy passou
a fundir acórdãos distintos (26/900) → 🔴 **D-C17** para o Rodrigo (a spec proíbe mudar o dedup nesta frente); **T5** — o
teste de "a chave do CSE não vaza no log" não podia falhar (provado com mutante) → reescrito. Suíte nova +8 sobre o plano.
T9 em worktree próprio (`../bn-t9`). Detalhe: `execucao/INSIGHTS.md` e `execucao/revisoes/`.

## [2026-09-23] checkpoint | frente 2, fase 3 fechada: trilha B (T6, T7, T8) em master

Trilha B fechou o ciclo nas três tasks e entrou em `master` por fast-forward em `9e259ca` (merge de `origin/master` na
branch sem conflito; runner 246 + golden OK no merge). Achados que viraram código além do plano: **T6** — `NaN`/`Infinity`/
`true` do modelo saíam rotulados "modelo" (NaN → nota máxima) → `fallback_erro` (+1 teste); **T8** — recongelamento do
golden provado por reconstrução: sem a coluna nova, a aba reproduz o sha pré-T8. Trilha A: T2 e T3 fechadas (review da
T2 pegou corpo ilegível sem URL; o da T3, 200 com corpo de erro lido como "sem resultado", `null` na pág. 2 descartando a
pág. 1 e contagem inflada — +4 testes além do plano na suíte nova); T4 em teste. Detalhe: `execucao/INSIGHTS.md` e
`execucao/revisoes/`. Snapshot de memória não escrito (política de autorização).

## [2026-09-23] checkpoint | frente 2, fase 1 fechada; trilhas A e B em voo

Rodrigo pediu (22/09, noite) a execução do plano inteiro **por agentes**: o orquestrador não escreve código;
por task, coder implementa → coder testa (+ e2e Playwright) → code-reviewer → o coder aplica e documenta;
`/checkpoint` a cada fase; trilhas paralelas onde não há dependência. Arquivos da execução em
`spec/frente2-honestidade-fontes/execucao/` (CONTEXTO, TODOS = SSOT de status, INSIGHTS, BRIEFS).
**T1 fechada no ciclo inteiro:** impl `da543be` (contagens exatamente as do plano), testador APROVADO (sondas extras +
e2e até o Passo 5 + Excel baixado), reviewer "nada a corrigir" (4 menores viraram 📝 hardening em INSIGHTS), doc
`ed50b6b` em `implementacao/01-*.md`. Trilhas: A (T2→T5) em `../bn-trilha-a`, B (T6→T8) em `../bn-trilha-b`, branches
`frente2/trilha-*`. O e2e da T1 fotografou a UI v1.0 dizendo "0 erros" com o LexML bloqueado — a mentira da frente.
Snapshot de memória **não** escrito: a regra `memory-write-policy` exige autorização do Rodrigo.

## [2026-09-22] split | plano v4 da frente 2 cortado em 10 arquivos de task, 5 fases

Pedido do Rodrigo (D-C16). O plano tem **2.882 linhas**; o subagente de cada task passa a ler o arquivo da task
(42–791 linhas) + `reference/global-constraints.md` (74). Destino: `spec/frente2-honestidade-fontes/`
(`00-overview.md`, `tasks/01..10`, `reference/{global-constraints,triagem-adversarial,self-review-v4}.md`).
Fases: 1 fundação (T1) · 2 fontes honestas (T2–T5) · 3 procedência da nota (T6–T7) · 4 saída honesta (T8–T9) ·
5 fechamento (T10).

**Corte verbatim por script** (`tools/split_frente2.py`): toda linha não vazia e diferente de `---` do plano cai em
exatamente um arquivo, sem sobreposição; cercas de código pares. Cada task ganha um header com **"Depende de"**
(por símbolo consumido, não por ordem) e **critérios de aceite derivados do próprio plano** — nenhum critério novo.
O plano segue fonte de verdade.

**Dependências achadas lendo as tasks:** a T9 consome T2, T3, T4, T5, T6 e T8; a T5 não consome código da T3/T4, mas
soma na mesma suíte e no mesmo `BASELINE`; a T8 depende da T7 só na contagem. 📝 Depois da T1, as trilhas T2→T5 e
T6→T8 só colidem em `tools/run_all_tests.py` — ficou como proposta no overview, não decidida; o plano manda sequencial.

**Deploy:** Rodrigo confirmou nesta data que o app da nuvem roda a partir da branch `deploy`. Corrigida a D-C14, que
ainda dizia "push em `master` = deploy". Push por task em `master` segue valendo e não publica nada.

Nenhuma linha de produção mudou.
## [2026-09-22] deploy descoberto | o app já estava no Streamlit Community Cloud

Rodrigo apontou `https://levantamento-normativos.streamlit.app/`. GET → `303` para login (app privado). Docs
que diziam "nenhum deploy" corrigidos (state §8, D-C14); origem do app a confirmar no painel (B-06 item 4);
lição em `LESSONS.md`. Nada muda na ordem: a frente 2 continua sendo a próxima.
Depois: o app vinha do repo A (arquivado); o Streamlit não enxergava B por ser privado. Cogitado tornar B público —
varredura do histórico: **nenhum segredo** (só placeholders), mas IP interno, nomes e ledgers ficariam expostos →
Rodrigo decidiu **manter privado** e dar ao Streamlit acesso a repo privado. Redeploy:
`https://buscador-normativos.streamlit.app/` (B, `master`). ⚠ push em `master` agora é deploy. App antigo apagado. Chave Gemini do projeto `nuati.secin` nos Secrets do app novo
(valor fora do chat e do repo); regra: nada de `secrets.toml` local até a frente 5. Insumos da frente 5 no `_TODO.md`.
IA da nuvem não funcionava: (1) chave lida só no import → reboot; (2) `gemini-2.5-flash-lite` dá 404 para chave nova →
`MODEL_NAME = "gemini-3.5-flash-lite"` (provado com chamada real). Runner 205/205 com as chaves fora do ambiente; golden OK.
Rodrigo confirmou palavras-chave geradas na nuvem → tags anotadas `v1.0` (`eb91277`) e **`v1.0.1`** (`e2cd56a`), empurradas;
D-C10.1 fechada como "tags nos marcos".
Branch **`deploy`** criada em `v1.0.1` e empurrada; a nuvem passa a segui-la (troca no painel: Rodrigo). Frente 2 fica para
sessão nova (D-C15). App trocado para `deploy` pelo Rodrigo; segredo regravado + reboot → IA gerando. Confirmado.

---

## [2026-09-22] frente 2 planejada | 3 rodadas adversariais; repo A aposentado; deploy em análise

**Segunda metade da sessão de 22/09** (a primeira está na entrada abaixo).

**Repo A aposentado (T9 antecipada).** Tag `levantamento-v1-streamlit` empurrada para o remoto de B; README
de arquivamento em A (`af88593`); `rodilpinto/levantamento-normativos` **privado e arquivado**
(`gh repo view` → `PRIVATE | arquivado=true`). Descoberta no caminho: o repo A estava **público** e o state
file dizia "privado" — corrigido (`407b5a1`). Fluxo do espelho `git.camara.gov.br` (pelo PC do trabalho)
registrado no state file §8. Deploy: **não existe nenhum**; opções e recomendação em **D-C14 🟡**; perguntas
que só o Rodrigo responde em **B-06**.

**Frente 2 — spec + plano.** Brainstorm com 3 perguntas ao Rodrigo (tela E planilha; heurística roda sem
LLM; LexML sem conserto legítimo → detectar/avisar + fonte substituta + B-05). Spec `b489d00`. Plano v1
`b1a6d3c` → **rodada 1** (55 achados; TCU: esquema real da API não tem `ementa`/`numero`/`ano` — bug de
produção da v1.0; Google entra no vocabulário) → v2 `1e24933` → **rodada 2** (68 achados; bloqueador
principal = cruzamento H4×B2, `redigir(300)` cortava a cadeia agregada) → v3 `46cdb0e` → **rodada 3**
(59 achados; bloqueador = cruzamento R2-H5×H2 no TCU + `Optional` sem import derrubando o app) → **v4**
`02dc620`/`a457e84`. Vereditos da rodada 3: T1, T2, T3, T6, T7, T8, T9 aplicam e fecham como previsto
(um revisor rodou o app patchado e o V11 ao vivo); sobras localizadas, todas dobradas na v4. Lições em
`LESSONS.md` (cruzamento de correções; fixture escrita à mão).

**Decisões:** D-C10..D-C15 (`_DECISOES-PENDENTES.md`). **Ambiente:** Playwright sem navegadores baixados
(`channel="chrome"`), `/tmp` do Git Bash ≠ `/tmp` do Python — em `~/.claude/ENVIRONMENT.md`.

**Próximo:** sessão nova, contexto zerado, executar o plano v4 da frente 2 a partir da **T1**.

---

## [2026-09-22] frente 1 | primeiro código entra; a rede de proteção existe

**A sessão começou vendo a v1.0 rodar** (`python -m streamlit run app.py`, dirigida pelo
navegador até o Passo 4) — e a demonstração achou o que ninguém tinha medido: **as duas fontes
catalogadas devolvem zero**, e a UI diz "0 erros". LexML está atrás de um desafio de JavaScript
do Senado (só `/busca/SRU`; a home abre; User-Agent não resolve; os 2 URLs de fallback são 404);
o endpoint de atos normativos do TCU responde 500 (acórdãos respondem 200). Só a web aberta —
que na prática é **DuckDuckGo**, porque `GOOGLE_CSE_ID` está vazio — traz resultado, o que o
Rodrigo confirmou no teste dele. Detalhe medido em `LESSONS.md`.

**Decisões do Rodrigo** (`_DECISOES-PENDENTES.md`, D-C10 a D-C13): v1.0 = app atual, v2.0 =
consolidação; **todos os consertos da v1 entram**, com a mesma metodologia SDD; a v1.x vira
**5 frentes** (1 rede de proteção · 2 honestidade das fontes · 5 LM local = T5+T6 puxadas ·
3 cobertura Planalto/LEGIN · 4 explicabilidade F8/F9), ordem **1 → 2 → 5 → 3 → 4**; rede de
proteção **antes** de qualquer conserto; LexML sem conserto legítimo → detectar/avisar + fonte
substituta + pedido de acesso oficial (B-05). Pedidos novos: aba de instruções na planilha (F8),
aba de explicações no app (F9). D-C9 ganhou a opção `c`. Push a cada task.

**Frente 1 executada inteira — T3, T1, T2:**
- **T3** (`4f36080`): merge `--allow-unrelated-histories`; conflito só no `.gitignore`; história
  de A preservada (`--follow` alcança os 2 commits, autoria de março, 2 pais); **6.561 linhas**.
  ⚠ O heredoc do plano **não era a união** — faltava `/*.xlsx`; o primeiro gate de auditoria deu
  falso verde por ler estágios de conflito já apagados pelo `git add`. Ambos em `LESSONS.md`.
- **T1** (`d054d5b`): golden-master com corpus de 14 itens que dispara as **3** estratégias de
  dedup (14 → 11); sha de células estável em 3 execuções; comparador reprova nos 2 ramos.
- **T2** (commit seguinte): runner único; **205 verdes, exit 0**; prova bidirecional verde →
  vermelho → verde; BASELINE como piso com 3 ramos. `test_searchers.py` leva ~390s por causa das
  fontes quebradas.

**Pesquisa para a frente 5:** o conector de LM local do `wiki-chat` (`wikichat/llm/openai_compat.py`)
é OpenAI-compatible via SDK `openai`, mas **nunca foi exercitado contra servidor real** e o endereço
da Câmara não está versionado lá — está aqui, na D-C5 (`10.10.111.125:1234`). Lições a herdar:
`/v1` obrigatório, `max_retries=0`, timeout do httpx conta inatividade (não tempo total),
`stream.close()` no `finally`, porta fechada no Windows vira timeout.

**Próximo:** spec da frente 2 (honestidade das fontes) via brainstorming → plano → execução.

---

## [2026-09-16] consolidação | dois projetos viram um; o artefato "inexistente" existia

**O achado que reorienta o projeto.** A entrada de 08/09 afirma que "o artefato original não
existe" e que o buscador "nunca foi código". **Está errado.** O app `levantamento-normativos`
existe desde março de 2026 em `~/Documents/projeto-nuati-normativos-levantamento/`: 6.561 linhas
(4.087 produção + 2.474 teste; medido com `git ls-files '*.py' | xargs wc -l`), busca por API (LexML SRU/CQL, TCU Dados Abertos, Google
CSE/DuckDuckGo), revisões de segurança e qualidade aplicadas. A varredura de 08/09 cobriu
`solucoes/`, as skills e `projeto-AI-com-IA/` — **não** cobriu a pasta onde o app mora.

**Prova medida em 16/09, antes de qualquer mudança:** 205 testes verdes — `test_searchers` 13/13,
`test_llm_phase3` 53/53, `test_comprehensive` 98/98 (com `LIVE: LexML search`, `LIVE: TCU search`
e `LIVE: End-to-end search + export` passando) e `test_phase4` 41 passed. Enquanto isso, a emenda
R1-10 do plano antigo verificou que **duas das três rotas de scraping planejadas retornam 404**.

**Consequências.** O projeto deixa de ser greenfield. A decisão **B2 é revertida**: a base passa a
ser o Streamlit já escrito, não um FastAPI novo — ela fora tomada sem saber que A existia. O
escopo cai de 16 tasks sobre pasta vazia para **7 features sobre código que roda**, e 8 das 19
emendas antigas ficam sem efeito por construção.

**Decisões.** Board de 10 grupos respondido em duas rodadas (`decisions/DECISIONS-LOG.md`).
Entra o agrupamento semântico dos resultados (F7), com o requisito vinculante de que o
agrupamento é **aditivo** — nunca remove, oculta ou filtra item da visão do usuário. Ficam de
fora chat sobre o acervo, busca semântica no acervo baixado, selo já-tenho por embedding, handoff
de checklist (roadmap) e adaptadores Planalto/LEGIN (adiados). **D-B1 e D-B2 fecham**, abertas
desde 09/09.

**Revisão adversarial, 3 rodadas, 38 emendas vinculantes** (A1-A21, B1-B12, C1-C5). A rodada 2
achou 3 bloqueadores que as correções da rodada 1 haviam **introduzido**; a rodada 3, dirigida,
fechou com zero bloqueadores. Detalhe e cobertura em `LESSONS.md`.

**Entregas:** spec de consolidação, plano da Fase 1 (9 tasks, 43 steps), `LESSONS.md`,
`BLOCKED-ON-RODRIGO.md`, `decisions/`. **Nenhuma linha de código de produção.**

---

## [2026-09-09 e 2026-09-10] registros migrados do `_TODO.md` (preservados no checkpoint de 16/09)

Os dois registros `[x]` que viviam só na seção P3 do `_TODO.md`, movidos para cá antes da
reescrita daquele arquivo — o `log.md` é append-only e é a casa certa deles.

- **2026-09-09 · Remoto criado:** `github.com/rodilpinto/buscador-normativos`, **privado**
  (confirmado via `gh repo view --json visibility`). ⚠ Exigiu instalar o GitHub CLI
  (`winget install --id GitHub.cli`), que não existia nesta máquina — criar repositório é chamada
  de **API**, não operação git, então o token do Credential Manager que faz o `push` funcionar não
  bastava. **Esta lição foi promovida a `~/.claude/ENVIRONMENT.md`** por ser de máquina, não de repo.
- **2026-09-10 · Split feito:** as 16 tasks do plano antigo extraídas verbatim para
  `spec/buscador/tasks/`, em 5 ondas e 7 trilhas, com checagem mecânica de colisão de arquivos.
  ⚠ Esse plano e esse split foram **superados** pela consolidação de 16/09.

---

## [2026-09-10] split | 16 tasks extraídas em arquivos, agrupadas em 5 ondas e 7 trilhas

Fase `split` do `/go`. O plano tem **2641 linhas**: um agente de build que o lesse inteiro a
cada task gastaria em leitura o contexto de que precisa para implementar. As 16 tasks foram
cortadas **verbatim** (não reescritas) para `spec/buscador/tasks/NN-nome.md`, de 122 a 255
linhas cada, e o material transversal (Global Constraints + File Structure + Tech Stack) foi
para `spec/buscador/reference/global-constraints.md`, citado pelos headers.

**O plano segue fonte de verdade do conteúdo.** Divergência entre plano e cópia: o plano ganha.
Status por task continua só no `_TODO.md`; ordenamento em `spec/buscador/00-overview.md`.

**Ondas e trilhas.** 5 ondas. A onda 2 tem 4 trilhas paralelas (A dados, B fontes, C llm,
D triagem-core) com **interseção de arquivos vazia**, verificada listando os arquivos tocados
por trilha e comparando, não por julgamento. A T3 foi puxada para o gate junto com a T1 porque
`Resultado` e `normalizar_titulo` são consumidos por 3 das 4 trilhas.

**Duas colisões reais encontradas, ambas serializadas:**
- `buscador/web/app.py`: T14 cria, T15 modifica. Mesma trilha, nesta ordem, nunca em paralelo.
- `README.md`: T1 e T16 listam as duas como "Create". Ondas distintas, mas a T16 sobrescreve.
  **Ambiguidade do plano, não resolvida** (registrada no overview e no `_TODO.md` P3).

**Verificação da extração** (feita por quem não extraiu): cobertura contígua das linhas
53-2641 do plano sem buraco nem sobreposição, cercas de código pares em todos os 16 arquivos,
nenhum truncamento, nenhum acento corrompido.

**Lição de ambiente:** `python` nu não resolve nesta máquina (o alias do Microsoft Store
intercepta e imprime instrução de instalação). Usar o caminho completo do plano,
`C:\Users\P_8106\AppData\Local\Programs\Python\Python313\python.exe`, ou Bash puro.

> ⛔ **RETRATADO em 2026-09-16.** Medido nesta máquina: `python --version` → `Python 3.13.7`;
> `which python` → `/c/Python313/python`. O alias da Store **não** intercepta. E o caminho
> prescrito acima é de **outro perfil de usuário**: `ls C:/Users/P_8106` → *No such file or
> directory*. Seguir esta lição mandaria o executor a um caminho inexistente. Use `python` nu.

Nenhuma linha de código de produção foi escrita nesta fase.

## [2026-09-08] scaffold | Brainstorm, spec e plano de 16 tasks — projeto nasce

Sessão de origem: área `ai-com-ia` do `projetos-nuati`, durante a ingestão dos Relatórios de
Situação. O Rodrigo pediu "a aplicação completa" do buscador de base normativa citado de
memória em 23/08.

**Varredura que precedeu o desenho (e mudou o projeto).** Procurei o artefato original em
`solucoes/` (6 repos), nas skills e comandos do `projetos-nuati`, e na pasta do
`projeto-AI-com-IA`. **Não existe.**
>
> ⛔ **RETRATADO em 2026-09-16: o artefato EXISTE.** A varredura não cobriu
> `~/Documents/projeto-nuati-normativos-levantamento/`, onde vive o app `levantamento-normativos`
> desde março de 2026 — 6.561 linhas, busca por API (LexML SRU/CQL, TCU Dados Abertos, Google
> CSE/DuckDuckGo), 205 testes verdes medidos em 16/09. O parágrafo abaixo sobre o formatador
> `gerar_planilha_normativos.py` continua correto; errada é a conclusão de que ele era tudo o que
> havia. Ver a entrada de 2026-09-16 no topo e `LESSONS.md`.
> O candidato `/analise-normativa` foi lido por inteiro
(154 linhas) e **descartado**: é gerador/auditor de checklists (modos `extrair`, `verificar`,
`instanciar`), a montante do `checklist-conformidade`, sem nenhuma função de busca. O que
existe em `referencias/_apendices-e-scripts/` é só um **formatador**:
`gerar_planilha_normativos.py` tem uma lista de ~30 normativos escrita à mão dentro do fonte
e **nenhuma chamada de rede** (sem `requests`, `urllib`, `selenium`, `playwright`). Ou seja,
dos passos do processo — tema → palavras-chave → busca → planilha → download → pastas — só o
"planilha" era código. O resto era conversa com LLM.

**Um alerta meu que se mostrou errado, registrado por honestidade.** Levantei que o projeto
duplicaria o `wiki-chat` (que tem chunker, retriever e citações planejados). O Rodrigo
corrigiu: o wiki-chat **consome** acervo, este **constrói**. Alerta retirado.

**A dor que define o produto:** a primeira busca do levantamento LGPD trouxe **100+
normativos**, "inviável de usar por um humano". O problema não é buscar, é **triar** — daí o
princípio de reduzir o *número* de decisões, não embelezar cada uma (spec §2, mecanismos
M1-M4).

**Decisões B1-B5** tomadas no brainstorm (detalhe na spec §4 e no
`_DECISOES-PENDENTES.md`), com duas tensões explicitamente aceitas pelo Rodrigo e suas
mitigações obrigatórias: B4 (duplicação entre temas → dedup sha256) e B5 (inflação de
decisões → ações de grupo).

**Entregas:** spec de design + plano de implementação de 16 tasks com TDD passo a passo.
**Nenhuma linha de código.**

---

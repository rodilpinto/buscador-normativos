---
title: Buscador de Base Normativa — TODOs
last_audit: 2026-10-01
related: [_DECISOES-PENDENTES.md, log.md, LESSONS.md, BLOCKED-ON-RODRIGO.md, SESSION-ONBOARD-buscador.md, decisions/DECISIONS-LOG.md]
---

# TODOs — o que está pendente

> **Frente 2 fechada em 23/09** (T10). **Frente 5 (LM local) 🟡 em andamento** desde 28/09 — o núcleo (cadeia de LLM,
> `llm_cadeia/`) foi entregue; o que falta está na linha da frente 5, abaixo. Ordem D-C11 1 → 2 → **5** → 3 → 4. Histórico da frente 2: conteúdo das tasks em
> `docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md` (tudo dobrado no corpo; ordem = numeração).
> O plano de 16/09 só volta na v2.0 (T4/T7/T8) e aí valem
> as três seções de emendas dele (precedência **C > B > A > corpo**, marcadores `⛔` no corpo).
> **Status**: aqui, e só aqui. O status por task da frente 2 (já fechada) ficou em
> `spec/frente2-honestidade-fontes/execucao/TODOS.md` (SSOT da execução, 22–23/09).

## ⛔ Superado — o plano de 16 tasks NÃO vale mais

O plano de 08/09 (`docs/superpowers/plans/2026-09-08-buscador-normativos.md`) e o split em
`spec/buscador/tasks/` foram **superados** pela consolidação de 16/09. Ficam no repo como
histórico e porque várias das emendas antigas continuam citadas. **Não execute aquelas tasks.**
Motivo em `log.md` (entrada de 16/09) e na spec de consolidação §1.1.

---

## Fase 1 — consolidação (plano de 16/09)

⚠ **A ordem NÃO é a numeração.** A emenda A1 reordenou: **T3 → T1 → T2 → T4 → T5 → T6 → T7 → T8 → T9.**

- [x] **T3 · Merge do histórico de A** — ✅ **feita em 2026-09-22** (`4f36080`). Conflito só no
      `.gitignore`, como previsto. Step 6 não executado (A1). ✅ Verificado: `git log --follow`
      no `app.py` alcança os 2 commits de A, autoria de março preservada, merge com 2 pais,
      15 arquivos `.py` / **6.561 linhas**.
      ⚠ **Correção ao plano:** o heredoc do Step 3 não era a união — faltava `/*.xlsx`. Ver a
      nota na Task 3 do plano e a entrada de 22/09 no `LESSONS.md`.
- [x] **T1 · Golden-master** — ✅ **feita em 2026-09-22.** `tools/golden_master.py` +
      `tests/golden/{entrada_fixa,dedup_esperado}.json`, `planilha_sha256.txt`, `ambiente.txt`.
      Emendas aplicadas: A2 (`generate_excel`), A3 (hash de células), A14 (entrada limpa nas
      duas chamadas), A21 (nome do arquivo · 1º item divergente na mensagem · prova dos 2 ramos),
      A12/B12 (14 itens), B11 (ambiente gravado, mecanizado em `ambiente.txt`).
      ✅ **Provas:** as 3 estratégias disparam uma cada (`id_match` · `tipo_numero` · `fuzzy 0.99`),
      14 → **11** únicos (colapso < 14, check da A12); sha estável em **3** execuções; comparador
      reprova nos **dois** ramos e volta a passar ao desfazer.
- [x] **T2 · Runner único** — ✅ **feita em 2026-09-22.** `tools/run_all_tests.py`. Emendas:
      A5 (exit code das suítes-script não é descartado), B2 (nasce só com `test_phase4.py`),
      A9/B3/C1 (BASELINE como piso com 3 ramos: sem entrada = erro · encolheu = erro · cresceu =
      aviso), C3 (no laço de impressão, onde `nome` existe), A19/B4 (prova bidirecional).
      ✅ **Linha de base após o merge: 205 (13 + 53 + 98 + 41), TUDO VERDE, exit 0.**
      ✅ **Prova bidirecional:** verde → `assert False` injetado → `41 | 1`, HOUVE FALHA, exit 1 →
      desfeito via `git checkout` → verde, exit 0.
      ➕ Coluna de **tempo por suíte** (não estava no plano): `test_searchers.py` leva **~390s**
      porque bate no LexML bloqueado e no TCU em 500 com retries — insumo da frente 2.
- [ ] **T4 · Ambiente reproduzível** — `pyproject.toml` + venv. ⚠ `pandas` é dependência de
      produção não declarada (A13); SDK de LLM vira extra opcional.
- [ ] **T5 · Protocolo de backend de LLM** — ➡ **migrou para a frente 5 da v1.x** (D-C11). ⚠ `timeout=(3.05, 60)`, tupla (A7); o teste precisa
      afirmar o `timeout` (B9).
- [ ] **T6 · Ligar o cliente ao backend** — ➡ **migrou para a frente 5 da v1.x** (D-C11). A task mais emendada. ⚠ **ACRESCENTAR** linha, não
      trocar a 14 do `test_llm_phase3.py` (B1); blocos nomeados (A4/B6); `app.py` e
      `llm/__init__.py` entram nos Files (A15/B7); Step 4b registra a suíte no runner (B2).
- [ ] **T7 · Corrigir os documentos com premissa falsa** — ⚠ o MEMORY.md é auto-memória e exige
      **autorização do Rodrigo** (B8).
- [ ] **T8 · Renomear para `buscador/` + auditoria de docstrings** — ⚠ gate sem `head` (A8); o
      Step 3 espera **215**, não "os mesmos números da T2" (C2).
- [x] **T9 · Aposentar o repo A** — ✅ **feita em 2026-09-22, antecipada** (a T3 + golden-master
      + 205 verdes já provavam a consolidação; Rodrigo confirmou na hora). Tag empurrada para o
      remoto de B; README de arquivamento em A (`af88593`); A **privado e arquivado**
      (`gh repo view` → `PRIVATE | arquivado=true`). Apagar de vez: só depois da tag v1.x.
      - [x] 2026-09-16 · tag no remoto de A · [x] 2026-09-22 · tag no remoto de B
      - [x] README de arquivamento · [x] `gh repo archive`

## v1.x — programa de 5 frentes (D-C11; ordem 1 → 2 → 5 → 3 → 4)

- [x] **Frente 1 · rede de proteção** — ✅ T3 `4f36080` · T1 `d054d5b` · T2 `e18dd4b` (22/09). Baseline atual:
      `BASELINE` em `tools/run_all_tests.py` (**única casa do número**; não restatar aqui).
- [x] **Frente 2 · honestidade das fontes** — ✅ **fechada em 23/09 (T10)**: as fontes declaram por que não responderam
      (`motivo`/`detalhe`/`parcial`), o TCU lê o esquema real do acórdão, a nota diz de onde veio, planilha (coluna + aba
      de diagnóstico) e tela dizem indisponível ≠ parcial ≠ sem resultado; 9 tasks + revisão final de 5 perspectivas + 2
      trilhas de conserto (FIX-FONTES, FIX-SAÍDA); gates do fechamento (runner, golden, V11) em `implementacao/10-fechar-frente.md`. ⚠ Fechou com a 🔴 **D-C17**
      aberta (dedup fuzzy funde acórdãos distintos). Registro completo: **`spec/frente2-honestidade-fontes/execucao/`**
      (TODOS, INSIGHTS, `revisoes/`) e `spec/frente2-honestidade-fontes/implementacao/10-fechar-frente.md`.
      Histórico da execução (fases e status por task: `spec/frente2-honestidade-fontes/execucao/TODOS.md`):
      Spec: `docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md`.
      Plano **v4** (3 rodadas adversariais, tudo dobrado no corpo — não há seção de emendas a consultar):
      `docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md`, 10 tasks, TDD, BASELINE previsto
      por task na tabela do próprio plano. ⚠ Ordem = numeração no plano; na execução, trilhas A (T2–T5) e B (T6–T8) em
      paralelo depois da T1, por decisão do Rodrigo de 22/09 (D-C16). Runner + golden como gate.
      ✅ **Split em arquivos por task (22/09, D-C16):** `spec/frente2-honestidade-fontes/` — `00-overview.md`
      (5 fases, grafo de dependências, protocolo por task), `tasks/01..10` (verbatim + "Depende de" + critérios de
      aceite derivados do plano), `reference/`. O plano segue fonte de verdade.
      Executada de 22/09 (noite) a 23/09. Status por task da frente 2: **`spec/frente2-honestidade-fontes/execucao/TODOS.md`**
      (SSOT da execução — aqui não se marca mais nada da frente 2). Contexto/regras: `execucao/CONTEXTO.md`.
- [ ] **Frente 5 · LM local** — 🟡 **em andamento.** ✅ **Núcleo entregue 23–28/09** (fora da ordem de tasks, a pedido
      urgente do Rodrigo): `levantamento-normativos/llm_cadeia/` (spec `docs/superpowers/specs/2026-09-28-llm-cadeia-portatil-design.md`,
      plano `docs/superpowers/plans/2026-09-28-llm-cadeia-portatil.md`; versão e changelog no README da pasta). Cobre o que
      T5/T6 pediam: backend injetável por ambiente, local OpenAI-compatível com `timeout=(5, 120)` em tupla, backend nulo =
      cadeia vazia, teste do módulo no runner. **Veredito de cada insumo abaixo (29/09):** (a) ✅ feito (segredos por
      ambiente); (b) ✅ dispensado — Gemini fala pelo SDK nativo e o local pelo endpoint OpenAI; (c) ✅ **01/10**: o runner passa `LLM_SOMENTE=nenhum` (llm_cadeia 1.1.0) e as suítes rodam sem LLM mesmo com
      o `secrets.toml` global; o `_segredo` continua lendo `st.secrets` antes do ambiente (decisão F-P5 do framework); (d) 🟡 a 1.1.0 trouxe
      `recarregar()`, mas a cadeia continua montada no import e o app não o chama; (e) 🟡 meio caminho — `gerar` devolve `Resposta.tentativas`, mas `gemini_client._generate` só
      repassa `.texto` e a tela ainda diz "Nenhuma palavra-chave gerada"; (f) 🔴 aberto — **reproduzido em 29/09** (`TypeError` com `ementa=None`), agora em `gemini_client.py:317` e `:415`; (g) 🔴 aberto.
      **Falta também:** rodar o app no servidor do Nuati (B-06); ⚠ a D-C17 venceu o prazo (ver o ledger).
      Insumo antigo: pesquisa do conector do wiki-chat no `log.md` (22/09).
      ➕ **Insumos de 22/09 (noite):** (a) configuração **por ambiente** — nuvem Streamlit = Gemini (não alcança a
      rede interna); servidor Nuati = LM local primário + Gemini de reserva (coerente com D-C5). (b) 📝 o Gemini tem
      endpoint **OpenAI-compatível** (`https://generativelanguage.googleapis.com/v1beta/openai/`, informado pelo
      Rodrigo junto com a chave `nuati.secin`) — um backend OpenAI-compatível só, trocando `base_url`+chave, poderia
      servir os dois; não decidido. (c) consertar `st.secrets` vencendo a variável vazia do runner. (d) a chave é lida **uma vez, no import** de
      `gemini_client.py` — segredo gravado depois exige reboot; ler na hora do uso. (g) achado na T5 (23/09): com o logger `urllib3` em DEBUG, a linha da requisição do CSE sai com `key=AIza…` (o app fixa
      WARNING em `app.py:38` (29/09: `:50`); vaza só se alguém ligar DEBUG) — filtro de log com `redigir`. (f) ⚠ achado na execução da frente 2 (review da T6, 23/09): com LLM ligado, `ementa`/`nome` `None` levanta
      `TypeError` em `score_relevance_com_origem` e `categorize_results` (linhas de 23/09 `:384`/`:476`; em 29/09 `:317`/`:415`) — `(r.get('ementa') or '')`.
      (e) `_generate` engole o erro da API
      (vira "Nenhuma palavra-chave gerada"): o motivo real precisa chegar à tela — mesma família da frente 2.
- [ ] **Frente 3 · cobertura** — Planalto e/ou LEGIN; spec não escrita. Reabre D-B2 (D-C13).
- [ ] **Frente 4 · explicabilidade** — F8 + F9; spec não escrita; depende do vocabulário da frente 2.
      ➕ **Insumos da revisão final da frente 2 (23/09, `spec/frente2-honestidade-fontes/execucao/revisoes/final-ux.md`):**
      relatório enxuto (uma linha por fonte + "Detalhe técnico" recolhido; hoje 16 blocos de debug); rótulo humano para cada
      motivo com o código entre colchetes; lembrete de cobertura no Passo 5; acentos nos rótulos (Orgao, Relevancia…) e
      cores (laranja = parcial, "sem resultado" neutro); emissor/tipo inventados — `"gov.br": "Governo Federal"`
      (`google_searcher.py:101`) casa df.gov.br/go.gov.br, e `nome` montado por nós (TCU atos, LexML sem título, Google com
      a URL) parece título da fonte.
- [x] **Fase framework → passe por app (D-C22/D-C23)**: ✅ **feito em 01/10** (sessão no PC do trabalho; detalhe no `log.md`).
      Branches: `main` = `e2cd56a` (v1.0.1, **sem** framework; produção) e `homologacao` (framework do `nuati-framework` @
      `56d7eb0`: `llm_cadeia` 1.1.0, `branding` 1.0.0, `tempo_economizado` 1.0.0). Apps recriados pelo Rodrigo e conferidos
      no ar: `buscador-normativos` (`main`) e `buscador-normativos-homologacao` (`homologacao`). `main` é a padrão no GitHub;
      `master`, `deploy`, `frente2/*` e `llm-cadeia-1.0.1` apagadas (tags `pre-framework-2026-10-01-*` guardam as pontas).
      `llm_cadeia/` deixou de ser origem: é **cópia** (D-C24 encerrada). Pendências que ficaram: ver abaixo.
- [ ] **Depois do passe por app (01/10):**
      - [ ] (Rodrigo) apagar o app `buscador-normativos-teste` no share.streamlit.io (a branch `master` que ele seguia já não existe). Rodrigo perguntou em 01/10 e recebeu o ok para apagar.
      - [ ] (Rodrigo, opcional) completar os Secrets da homologação com o bloco padrão (`LLM_BASE_URL`, `LLM_MODEL`, chaves sem
            sufixo de Groq/Cerebras/OpenRouter); hoje a cadeia de lá começa no `gemini`. Reboot depois.
      - [x] promover `homologacao` → `main`: ✅ **feito em 01/10**, `v1.1.0` (`829e71e`), D-C30.
      - [ ] 📝 Categorização vazia com o Gemma local (raciocínio ligado): visto em 01/10 no app local; provar
            `LLM_DISABLE_THINKING=1` nos Secrets do servidor do Nuati quando ele existir (pedido 2 ao framework).
      - [ ] 📝 O `gemini_client.py` importa `_segredo` (interno) do `llm_cadeia`: trocar quando o framework expuser uma
            função pública (pedido 1 ao framework).
- [ ] **Pedidos ao nuati-framework (passe de 01/10)**: entregues no relatório do passe; nada disto se conserta na cópia daqui.
      1. **`_segredo` é interno e o app depende dele.** `levantamento-normativos/llm/gemini_client.py:45` faz
         `from llm_cadeia.nucleo import _segredo` (lê `GEMINI_API_KEY` para o `api_key` de compatibilidade). Existe na 1.1.0 e os
         testes passam, mas é API privada: uma renomeação no framework quebra o import do app. 📝 Sugestão: o framework expor
         uma função pública de leitura de segredo (ex.: `llm_cadeia.segredo(nome)`), ou o app ler os seus.
      2. **Resposta vazia do `local` (Gemma) na categorização.** App local da `homologacao`, 01/10: log
         `Gemini returned empty response for categorize batch 0` (cerca de 5 min) e `batch 1` (cerca de 2 min); as notas de relevância do
         mesmo `local` vieram. Resposta vazia não passa para o próximo provedor (desenho da 1.0.x). 📝 Sugestões: recomendar
         `LLM_DISABLE_THINKING=1` no bloco do servidor do Nuati, e/ou um ajuste para tratar "vazio" como falha e seguir a cadeia.
      3. **"Sem LLM" por `LLM_SOMENTE=nenhum` funciona, mas não está documentado.** O runner daqui passou a depender disso
         (`0a74ddb`): 65/65 em 3 s, contra 60/3 com o `secrets.toml` global. 📝 Documentar no README como o jeito oficial de
         desligar o LLM em teste (ou criar um nome próprio, ex. `LLM_DESLIGADO=1`).
      4. **Branding em app público.** O README do branding diz que app aberto ao público mostra só a marca, sem assinatura de
         unidade; os apps do Streamlit são públicos (D-C26) e o `rodape()` padrão mostra a assinatura (checklist e buscador).
         📝 Esclarecer a regra para esses apps (ou `rodape(unidades=())`).
      5. 📝 **Receita do passe (§3/PASSE-POR-APP, passo 2):** instalar o `requirements.txt` do app antes da linha de base. Aqui o
         Python do PC do trabalho não tinha `ddgs`, e a linha de base pareceu regressão (LESSONS de 01/10).
- [ ] **Depois da reunião de 29/09** (o Rodrigo decide; nada disso é do agente sozinho): `BLOCKED-ON-RODRIGO.md` B-08
      (trocar a chave Groq), B-09 (versão nova para os apps ao vivo + visibilidade dos apps de teste), B-05 (pedido ao LexML).
- [ ] **Tag `v1.x`** ao fim das 5 frentes (D-C10) → checkpoint → v2.0 (T4, T7, T8 do plano de 16/09).
      ✅ Tags `v1.0` (`eb91277`) e **`v1.0.1`** (`e2cd56a`, ponto de retorno funcional) criadas e empurradas em 22/09 (D-C10.1).

## Fase 2 — as features (plano ainda não escrito)

- [ ] **F1** procedência (`catalogada` / `web-aberta`) — ➕ revisão final da frente 2: a aba Normativos não tem a coluna;
      título das abas usa só a 1ª keyword no modo manual.
- [ ] **F2** vinculação (`obrigatorio` / `aplicavel` / `contexto`)
- [ ] **F3** pré-marcação com motivo + as **duas** travas anti-ancoragem
- [ ] **F4** selo "já tenho" por sha256
- [ ] **F5** download + organização por tema + relatório de duplicata
- [ ] **F6** SQLite + colunas de registro na planilha
- [ ] **F7** agrupamento semântico dos resultados — ⚠ **aditivo**, nunca subtrativo (D-C1)
- [ ] **F8** **aba de instruções e explicações na planilha de saída** — pedido do Rodrigo em
      2026-09-22, ao ver a v1.0 rodando. Hoje a planilha tem **uma aba só** (`Normativos`,
      `excel_export.py:304`; 29/09: `:475`). A aba nova explica as colunas, a procedência de cada resultado e
      **como a nota de relevância foi calculada**, inclusive qual parte é determinística.
- [ ] **F9** **aba de explicações e configurações no app** — mesmo pedido, mesma data. Hoje a
      régua de relevância existe **só dentro do prompt** em `llm/gemini_client.py` e não aparece
      em lugar nenhum da interface. Quem lê "30%" não tem como saber o que isso significa.
      ⚠ **Achado da leitura de código (2026-09-22), insumo desta feature:** a coluna `Relevancia`
      hoje **colapsa três procedências diferentes** no mesmo número, sem marcar qual é qual:
      (a) nota dada pelo Gemini; (b) `0.5` de fallback quando o lote do LLM falha ou volta
      malformado; (c) o default do searcher (`0.3` Google, `0.5` LexML/TCU) quando o LLM não roda.
      **`0.5` pode ser as três coisas.** Contra o princípio de rastreabilidade do projeto —
      precisa de campo de procedência da nota, não só da fonte.
      ✅ **Virou código na frente 2 (23/09):** `relevancia_origem` (`modelo` / `fallback_erro` / `padrao_fonte` /
      `heuristica`, vocabulário `ORIGENS_RELEVANCIA` em `models.py`) — T6 `score_relevance_com_origem`, T7 `_merge`,
      T8 coluna "Origem da nota" na planilha, T9 origem no card e no preview. A F9 continua valendo para a **explicação**
      da régua na interface (o campo existe; o texto que diz o que "30%" significa, não).
      ⚠ **Segundo achado:** a heurística determinística `_keyword_relevance` é **inalcançável
      pelo app**. `score_relevance` só é chamada dentro de `if llm_available()` (`app.py:571`),
      então sem chave a nota **nunca é calculada** — fica no default do searcher. A heurística só
      roda se alguém chamar a função direto.
      ✅ **Virou código na frente 2 (23/09):** T9 — a pontuação roda **sempre** (sem LLM, a heurística, rotulada
      `heuristica`); FIX-FONTES F-UX2 (`66b7145`) — a heurística compara sem acento, com a mesma normalização do filtro de busca.

### 📥 Observações do Rodrigo sobre a planilha de saída (em coleta)

> Aberto em 2026-09-22: *"Eu tenho algumas observações para fazer na Excel de saída, mas já tá bem
> interessante por agora."* As demais observações ainda **não** foram ditas — este é o lugar delas.

- [x] aba de instruções e explicações → virou **F8**

## P3 — depois da Fase 1

- [x] ~~Consertar LexML e TCU~~ → **absorvido pela frente 2** (spec + plano v4 de 22/09). Medição em `LESSONS.md` (22/09).
- [ ] **Medir a lacuna de cobertura** das fontes catalogadas → **`BLOCKED-ON-RODRIGO.md` B-04**.
      É bloqueio no humano (exige tema real e julgamento de quem conhece o acervo), não task.
      ⚠ Obrigatório antes de fechar o MVP. O pacote completo está lá; aqui só o ponteiro.
- [ ] Rodar contra um tema real e medir o critério de sucesso nº 2 da spec: 100+ resultados
      triáveis em menos de 15 decisões.
- [ ] Reavaliar se Planalto e LEGIN fazem falta (D-B2 adiou; a lacuna não foi medida).
- [ ] **Deploy** — pós-v2.0. Ver D-C14 (🟡) e B-06. `Dockerfile` nasce na T4 (ambiente reproduzível).
- [ ] Escrever o plano da Fase 2.
- [ ] **Sobras da frente 2 registradas nas rodadas adversariais (não entram nela):** sanitizar `ementa`/`nome` contra
      fórmula na aba `Normativos`; dublar `test_lexml_cql_injection_sanitization` (faz rede real); na tela, agrupar
      o detalhe do TCU por fonte (é idêntico por keyword); runner "sem LLM" de verdade — `st.secrets` vence a
      variável vazia (frente 5); reduzir os ~390s dos testes LIVE (📝 `BUSCADOR_SKIP_LIVE=1`, não decidido; medido 23/09: ~200s no `test_searchers`).
      **Reconciliado na T10 (23/09)** — são os 4 itens de P3 do plano da frente 2 (Task 10) mais o dos testes LIVE:
      - [x] fórmula na aba `Normativos` — ✅ **feito na própria frente 2** (a revisão final de segurança o classificou
            como crítico): FIX-SAÍDA **S-SEC** `624bed5`, toda célula de texto das duas abas gravada como string literal
            (sem `<f>` no XML, sem apóstrofo); caractere de controle `f749360`.
      - [x] dublar `test_lexml_cql_injection_sanitization` — ✅ **feito**: FIX-FONTES **F-T1** `9fb4aeb` (sem rede, provado
            por mutante). É o mesmo item da linha "(T2, Step 11b)" das sobras da execução, abaixo.
      - [ ] tela: agrupar o detalhe do TCU por fonte (é idêntico por keyword) — **aberto**; conversa com o "relatório
            enxuto" da frente 4.
      - [x] runner sem LLM de verdade (`st.secrets` vence a variável vazia): ✅ **01/10**, `LLM_SOMENTE=nenhum` no runner (`0a74ddb`);
            antes: **aberto, frente 5** (é o insumo (c) de lá;
            não duplicar). ⚠ Agravante medido na execução: as chaves de LLM estão **definidas no ambiente da máquina**
            (`~/.claude/ENVIRONMENT.md`, 23/09) — o runner as zera, o app lançado à mão não.
      - [ ] reduzir os ~390s dos testes LIVE — **aberto**. Medido na T3: o custo é **paginação** do TCU (~114s por busca),
            não retry; ver a linha "(T3) `max_results<=0`" abaixo.
- [ ] **Sobras achadas na EXECUÇÃO da frente 2** (testadores/reviewers; detalhe em
      `spec/frente2-honestidade-fontes/execucao/revisoes/T*.md` e `INSIGHTS.md`):
      - ✅ (T2, Step 11b do plano) `test_lexml_cql_injection_sanitization` em `test_comprehensive.py` faz **rede real** — dublar.
        → **feito** em FIX-FONTES F-T1 (`9fb4aeb`), 23/09.
      - ✅ (T2 M2) LexML: WAF/HTML num URL já cacheado (`_sru_url`) não entra em `_urls_mortos` nem tenta fallback.
        → **feito** em FIX-FONTES F-M2 (`9fb4aeb`), 23/09 (a revisão final de spec subiu para importante).
      - (T2 obs. 2) keyword que sanitiza para vazio nunca é enviada mas sai `empty` — tratar em `search()`.
      - (T2 obs. 3 + T5) keywords além de `MAX_RETRIES` ou cortadas no retry ficam sem nota no detalhe — LexML e Google.
      - (T5) ddgs devolveu lista vazia depois de HTTP 202 do DDG (COBIT, ISO 27001 → "sem resultado"): possível mascaramento no ddgs — investigar.
      - (T3) TCU: `ChunkedEncodingError`/`ContentDecodingError` viram `erro_interno` sem retry (é erro da fonte).
      - (T3) TCU: status `nao_consultada`/`erro_interno` por keyword sem `parcial` nem o resumo dos endpoints.
      - (T3) TCU: `max_results<=0` ainda baixa todas as páginas (≈128s por busca; metade do tempo do `test_searchers`).
      - (T3 d) `redigir`: o regex `[^&\s]+` come `;`/`,` depois do segredo → `[^&\s;,)'"]+` + teste.
      - (T9 r1) URL solta (`http://…`) no texto da fonte vira link clicável no card (autolink do GFM, não se desliga por
        escape); o texto visível fica literal. 📝 sugestão do coder: quebrar o nó de texto com `<span></span>` depois de `http`/`www`.
      - (T9 r2) "Ementa completa" com `_md_texto` troca quebras de linha por espaço (muda o layout, não o texto).
      - (revisão final) TCU com os dois endpoints caídos: o aviso por fonte mostra só o motivo dos acórdãos (spec N6).
      - (revisão final) snippets do Google com palavras coladas ("doturismoem") — contra "texto literal"; investigar ddgs.
      - (revisão final) Relevancia int/float variando entre exportações; Numero/Data vazios em vez de "—".
      - (revisão final) deriva do retry LexML × Google (guarda B2 só no LexML; helper `aplicar_retry` em `base.py`);
        `e_indisponivel(s)` em `models.py`; e os menores de `revisoes/final-manutencao.md`.
        ✅ Parte feita: `models.e_indisponivel(s)` nasceu na FIX-SAÍDA (`624bed5`/`f749360`, usada pela tela e pela
        planilha). A deriva do retry e os menores seguem abertos.
      - (revisão final, testes alto) golden que passe pelos searchers: payload real congelado de TCU/LexML → parse real →
        hash de `KeywordStatus`/`NormativoResult` (hoje o golden são 14 `NormativoResult` à mão).
      - (FIX-SAÍDA) `topic` com caractere de controle ainda derruba o título das duas abas (improvável: vem do usuário).
      - (FIX-FONTES) mover `BaseSearcher._normalize_text` para um módulo de texto leve (`llm` importa de `searchers` hoje).
      - (T1) 📝 hardening de `redigir`: marcador de corte conta `len - 2*metade`; guarda para `limite < len(marca)`;
        validar `motivo` em `__setattr__`; redigir `key%3D…`/`"key": "…"` (frente 5).
      - (T10) `levantamento-normativos/tests/fixtures/lexml_sru_valido.xml` não tem a nota "📝 escrita à mão, sem captura"
        no cabeçalho, que a regra de 22/09 do `LESSONS.md` exige; e falta a **captura real** do SRU do LexML, a fazer
        quando a fonte responder (lição (3) do plano, `LESSONS.md` 23/09).
- [ ] Registrar este repo no `MEMORY.md` do `projetos-nuati` como solução nova.
      ⛔ **Bloqueado em autorização** — é auto-memória; a regra `memory-write-policy` exige que o
      Rodrigo autorize antes.

## Fora de escopo (registrado para não voltar à pauta)

Decidido no board de 16/09 (`decisions/DECISIONS-LOG.md`):

- **Chat sobre o acervo** — é o `wiki-chat`, projeto distinto.
- **Busca semântica sobre o acervo baixado** — mesmo terreno do `wiki-chat`.
- **Selo já-tenho por embedding** — ⚠ lacuna conhecida e **não mitigada**: material sem numeração
  (manuais, frameworks, guias ANPD) continua escapando do selo.
- **Extração de dispositivos e geração de checklist** — o handoff vai para roadmap, fora do MVP.
- **Reescrita em FastAPI** — a decisão B2 foi revertida.

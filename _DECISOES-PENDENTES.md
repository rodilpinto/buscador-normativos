---
title: "Decisões abertas — Buscador de Base Normativa"
maintained_by: sessões do Claude Code; só o Rodrigo resolve
last_updated: 2026-09-23
related: [_TODO.md, SESSION-ONBOARD-buscador.md, log.md, decisions/DECISIONS-LOG.md]
---

# Decisões — o que espera o humano

> Sugestões aqui são propostas, não fatos validados — marcadas com 📝.
> Histórico de rodadas respondidas: `decisions/DECISIONS-LOG.md`.

> **Legenda de estados usada neste arquivo:** 🔴 ABERTA · 🟡 EM ANÁLISE · 🟢 DECIDIDA · ⛔ bloqueada
> em autorização. Ao procurar o que está aberto, procure **🔴 e 🟡 e ⛔**, não só 🔴.

## 🔴 D-C9 — Como consumir o plano da Fase 1: dobrar as emendas, construir como está, ou dividir em tasks?

- **Onde aparece:** fim da sessão de 16/09, depois das 3 rodadas adversariais. **Não respondida.**
- **Atualizada em 2026-09-22:** acrescentada a opção **`c`** (split por task), pedida pelo Rodrigo
  na sessão de 22/09. As opções `a` e `b` seguem como estavam.
- **Trava:** ⚠ **nada — e menos ainda depois de 22/09.** A T3 (e a T1 e a T2) já foram executadas lendo as
  emendas junto (opção `b`, na prática). O plano da **frente 2** nasceu com as emendas **dobradas no corpo**
  (opção `a`/`c` por construção). A D-C9 só volta a importar na **v2.0**, quando T4/T7/T8 do plano de 16/09
  forem executadas. Pode ficar aberta até lá sem custo.

O plano da Fase 1 tem emendas vinculantes em três camadas (A1-A21, B1-B12, C1-C5), com
precedência **C > B > A > corpo**. Cada seção do corpo derrubada já carrega um marcador `⛔`
apontando qual emenda a derruba (feito no checkpoint de 16/09).

| Opção | Ganha | Perde / risco |
|---|---|---|
| **a** Dobrar as emendas no corpo primeiro | plano linear, lido de cima a baixo sem saltar | ~1 passada de edição sobre 1.7k linhas; risco de errar ao transcrever |
| **b** Construir com as emendas como estão | começa agora; a precedência está explícita e marcada | o executor precisa ler 3 seções + o corpo por task; é onde alguém escorrega |
| **c** Dobrar as emendas **e** dividir o plano em um arquivo por task | as duas vantagens da `a`, mais: o executor carrega ~150 linhas por task em vez de 1.741; é o que a fase *split* do `/go` fez com o plano de 08/09 | a passada de edição da `a` **mais** a extração; cria uma segunda cópia do conteúdo, que pode divergir do plano |

### Sobre a opção `c` — o que ela repete e o que ela herda

✅ **Já foi feito uma vez neste projeto**, com o plano de 08/09: 16 tasks cortadas **verbatim**
para `spec/buscador/tasks/NN-nome.md` (122-255 linhas cada) + o transversal em
`spec/buscador/reference/global-constraints.md`. Registrado no `log.md` de 2026-09-10. Aquele
split está ⛔ superado junto com o plano que o originou — mas o **procedimento** vale, inclusive
a verificação que ele usou: cobertura contígua das linhas, cercas de código pares, sem
truncamento, conferida por quem não extraiu.

⚠ **Regra herdada daquela rodada, obrigatória se a `c` for escolhida:** o **plano segue fonte de
verdade**. Divergência entre plano e cópia por task → o plano ganha. Status continua só no
`_TODO.md`. É a mitigação do único risco novo que a `c` traz (duas cópias do mesmo conteúdo).

⚠ **A `c` só faz sentido dobrando as emendas antes** (o trabalho da `a`). Dividir o plano sem
dobrar espalharia por 9 arquivos a necessidade de consultar 3 seções de emendas que ficariam
fora deles — piorando exatamente o problema que a `b` já tem.

📝 **Recomendação:** `c`, com a mesma força fraca de antes. Ganha da `a` porque o custo extra é
pequeno depois que as emendas já foram dobradas, e o benefício (contexto por task) é o mesmo que
justificou o split de 10/09. Ganha da `b` porque os marcadores `⛔` mitigam, mas não eliminam, o
risco de alguém executar um trecho do corpo que uma emenda derrubou.

**Decisão tomada:** _(pendente)_

---

## 🟡 D-C14 — Onde o app roda: desenvolvimento, demonstração e produção

- **Onde aparece:** 22/09, pergunta do Rodrigo: *"é possível fazermos o desenvolvimento no streamlit
  privado mesmo e quando estiver numa solução mais pronta a gente migra para o servidor nuati? ou
  então continuamos no servidor local dessa máquina até mover para o servidor nuati"*.
- **Trava:** nada da v1.x. Só o `Dockerfile` (T4, v2.0) e a frente de deploy pós-v2.0.

⚠ **CORRIGIDO em 22/09 (noite):** a frase original dizia "não existe deploy nenhum" — **errado**. Existe o app
`https://levantamento-normativos.streamlit.app/` no Community Cloud, **privado** (GET → `303` para o login do
`share.streamlit.io`). A verificação só olhou o repo; deploy no Community Cloud não deixa arquivo no repo.
Vinha do repo A. ✅ **Redeploy feito em 22/09 (noite)** a partir do repo B, branch `master`:
`https://buscador-normativos.streamlit.app/`, privado; B continua privado. ~~⚠ Push em `master` = deploy.~~
⚠ **CORRIGIDO em 22/09:** o app segue a branch **`deploy`** (congelada em `v1.0.1`), não `master` — Rodrigo
confirmou nesta data que a versão publicada roda a partir da branch. Push em `master` **não** é deploy.
✅ Continua valendo: sem Dockerfile/Procfile. Doc oficial do Streamlit Community Cloud: repo **privado é aceito** e o app
herda a visibilidade do repo (privado → só convidados, login Google/e-mail); **limite de 1 app
privada por conta**. A nuvem da Streamlit **não alcança o LM local** (`10.10.111.125`) — lá só
Gemini, e cada tema digitado sai da rede.

| Fase | Opção | Observação |
|---|---|---|
| **Desenvolvimento** | 📝 local nesta máquina (como hoje) | zero infra; Gemini pessoal ou `NullLLM`; LM local inalcançável daqui de qualquer jeito |
| **Demonstração** | 📝 Streamlit Community Cloud **privado**, opcional | serve para mostrar a colegas sem instalar nada; 1 app privada; Gemini obrigatório; **não** para tema real de auditoria |
| **Produção** | 📝 servidor do Nuati, empacotado em Docker | mesmo host do LM Studio (`base_url` localhost), intranet, sem URL pública — o desenho do wiki-chat (D13 lá) |

📝 **Recomendação:** as duas coisas que o Rodrigo perguntou são compatíveis, e a resposta é "as duas":
**desenvolver local** (é o que já funciona) **e**, quando quiser mostrar, **uma app privada no
Community Cloud** como vitrine — sabendo que ela roda com Gemini e fora da rede; **produção só no
servidor do Nuati**. O que NÃO fazer: tratar a app da nuvem como produção.

**Decisão tomada:** _(pendente — 🟡 em análise; ver B-06 para o que só o Rodrigo responde)_

---

## 🟢 D-C10.1 — Tag a cada task fechada, ou só nos marcos v1.0 / v1.x / v2.0?

> ✅ **Decidida em 22/09 (noite), na prática:** Rodrigo, ao ver a IA funcionando na nuvem: *"podemos guardar essa
> versão como um ponto de retorno e seguir para as próximas versões"* → **tags nos marcos funcionais**, não por task.
> Criadas e empurradas: `v1.0` (`eb91277`) e `v1.0.1` (`e2cd56a`). 📝 Leitura minha da frase; corrigir se não for isso.

- **Onde aparece:** 22/09, pergunta minha ao registrar a D-C10; respondida na prática no mesmo dia (ver o topo).
- **Trava:** nada. 📝 Recomendação: só nos marcos — o push por task (D-C7) + golden + runner já dão o
  rastro; tag por task é ruído. Se `a` (marcos): criar `v1.0` já (aponta `eb91277`).

**Decisão tomada:** tags só nos marcos funcionais (22/09) — ver o topo desta entrada.

---

## ⛔ Bloqueadas em autorização (não são escolhas, são permissões)

- **Registrar este repo no `MEMORY.md` do `projetos-nuati`** — é auto-memória, e a regra global
  `memory-write-policy` exige autorização explícita do Rodrigo. Item no `_TODO.md` §P3.

---

## 🟢 Decididas em 2026-09-22

- **D-C16 · O plano da frente 2 é dividido em arquivos por task, agrupados em fases.** Rodrigo, 22/09: *"Please
  split this plan into separate files in a tasks subfolder. This implementation plan should be split up into phases
  and actionable tasks. Each is a individual feature with detailed actionable tasks, tests and acceptance criteria
  [...] Carefully consider the dependencies between features."* Feito em `spec/frente2-honestidade-fontes/`: 5 fases,
  10 tasks, corte **verbatim** (script `tools/split_frente2.py`, cobertura verificada) + header com "Depende de" e
  critérios de aceite **derivados do plano**. Regra herdada do split de 10/09 (D-C9, opção `c`): **o plano segue fonte
  de verdade**; divergência → o plano ganha. ~~Status só no `_TODO.md`. Ordem sequencial; trilhas = 📝 não decidida.~~
  ⚠ Superado no mesmo dia pelo ➕ abaixo: status em `execucao/TODOS.md`; execução por trilhas.
  ⚠ Não fecha a D-C9: aquela é sobre o plano de 16/09 (v2.0).
  ➕ **Execução por trilhas decidida pelo Rodrigo (22/09, noite):** *"create different tracks [...] find any phases
  or tasks that do not have a dependency on each other"* — a proposta 📝 do overview (trilhas A = T2→T5 e B = T6→T8
  depois da T1) passa a ser o modo de execução. Regras: `spec/frente2-honestidade-fontes/execucao/CONTEXTO.md`.

- **D-C15 · Como a frente 2 é revisada e executada.** Rodrigo, 22/09: *"2 rodadas de adversarial review e
  depois vamos parar e começar a implementação em uma nova sessão com contexto zerado."* Feito: o plano
  passou por **3** rodadas (a 1ª antes do pedido, mais as 2 pedidas), cada uma aplicando o plano num
  worktree e rodando os testes do próprio plano; em **duas rodadas seguidas o pior achado foi um
  cruzamento de duas correções da rodada anterior** (registrado em `LESSONS.md`). Execução: **sessão nova**,
  um subagente por task, runner + golden como gate, push por task.

- **D-C11 · A v1.x vira um programa de 5 frentes, cada uma com seu ciclo SDD.** Decidido por
  Rodrigo em 2026-09-22: *"Vamos fazer todos os consertos dessa versão 1. use a mesma metodologia
  sdd. escreva os arquivos com os fixes, desenhe, implemente e teste, revise o app e parta para a
  próxima."*

  **Ordem decidida: 1 → 2 → 5 → 3 → 4.**

  | # | Frente | Conteúdo | Spec nova? |
  |---|---|---|---|
  | **1** | Rede de proteção | T3 merge · T1 golden-master · T2 runner | ❌ **não** — o plano de 16/09 já cobre |
  | **2** | Honestidade das fontes | fonte indisponível ≠ sem resultado · TCU 500 · procedência da nota · heurística inalcançável | ✅ sim |
  | **5** | LM local | **T5+T6 puxadas para cá** — protocolo de backend + ligar o cliente | ✅ sim (emenda o plano) |
  | **3** | Cobertura | adaptador Planalto e/ou LEGIN | ✅ sim |
  | **4** | Explicabilidade | F8 aba da planilha · F9 aba do app | ✅ sim |

  ⚠ **As frentes 2 e 5 tocam os mesmos arquivos** (`gemini_client.py`, `app.py`) — serializadas
  de propósito, nunca em paralelo. Foi o que decidiu pôr a 5 logo depois da 2.
  ⚠ **A frente 4 vem por último porque depende do vocabulário de procedência criado na 2** —
  aba de explicação escrita antes descreveria comportamento que ainda vai mudar.

  **Consequência para os marcos da D-C10:** a v1.x passa a conter o grosso do conteúdo técnico
  (T3, T1, T2, T5, T6 + os consertos + Planalto/LEGIN + as abas). A **v2.0 fica com T4**
  (ambiente), **T7** (documentos), **T8** (renomear para `buscador/`) e **T9** (aposentar o repo A).

- **D-C12 · Rede de proteção antes dos consertos.** Decidido em 2026-09-22. T3, T1 e T2 rodam
  **antes** de qualquer mudança de comportamento, porque as três não alteram uma linha de
  produção (git puro + ferramentas novas). Só depois delas "não regrediu" passa a ser afirmação
  verificável por máquina, em vez de quatro suítes rodadas à mão em três formatos de resumo.

- **D-C13 · Cobertura do LexML: detectar/avisar E acrescentar fonte catalogada substituta.**
  Decidido em 2026-09-22, depois de medido que o LexML não tem conserto técnico legítimo.
  ✅ **Medições que sustentam:** só `/busca/SRU` está desafiado (a home do `lexml.gov.br` abre
  normal); User-Agent descritivo **não** resolve; o desafio é de **JavaScript**; `/oai` é 404.
  ⛔ **Resolver o desafio programaticamente está fora de escopo** — seria contornar proteção
  anti-robô. Entra no lugar: detecção honesta + Planalto/LEGIN (frente 3) + pedido de acesso
  oficial ao Senado (ação humana, ver `BLOCKED-ON-RODRIGO.md`).
  ⚠ Isto **reabre a decisão D-B2**, que tinha adiado Planalto e LEGIN por julgar LexML+TCU
  suficientes. A premissa caiu: o LexML não entrega nada hoje.

- **D-C10 · Versionamento por marcos, com fallback declarado.** Decisão do Rodrigo nesta sessão,
  depois de ver o app v1.0 rodando: *"ele será nossa v1.0 e esse merge de specs será a v2.0. é bom
  termos marcos e fallbacks para o caso de regressão."*

  | Marco | O que é | Fallback |
  |---|---|---|
  | **v1.0** | o app Streamlit de A, como está hoje: 6.561 linhas, 205 testes verdes, wizard de 5 passos, busca por API | tag anotada `levantamento-v1-streamlit` no repo A, ✅ já no remoto |
  | **v2.0** | o resultado da Fase 1: merge + golden-master + runner único + backend de LLM injetável + pacote `buscador/` | volta para **v1.0** |

  ⚠ **Estado em 22/09 (fim do dia):**
  - tag `v1.0` neste repo — **pode ser criada agora** (a T3 trouxe `eb91277` para a história de B); não
    criada: espera a D-C10.1.
  - tag `v2.0` — ao fechar os critérios de pronto da v2.0 (T4/T7/T8 do plano de 16/09; o número de
    testes esperado será o `BASELINE` de `tools/run_all_tests.py` naquele momento — o "215" do plano de
    16/09 não vale mais, T5/T6 migraram para a frente 5).
  - **A prova de regressão existe** desde a frente 1: golden-master (T1) + runner (T2). "Temos fallback"
    agora significa `git checkout levantamento-v1-streamlit` + os dois gates.

## 🟢 Decididas em 2026-09-16 (board da consolidação)

- **D-C1 · Indexação semântica:** **só `1a`** — agrupar os resultados da busca por assunto.
  Ficam de fora `1b` (selo já-tenho por embedding; a dedup bibliográfica de A atende por ora)
  e `1c` (busca no acervo baixado; é o `wiki-chat`).
  ### ⚠ Requisito vinculante — o agrupamento é aditivo
  > "não remover do usuário a capacidade de ver tudo. os agrupamentos devem facilitar e não
  > remover opções." — Rodrigo, 2026-09-16

  O agrupamento **oferece** um atalho para decidir em bloco; **nunca** remove, oculta ou filtra
  itens da visão do usuário. Reforça a decisão B5 ("mostrar todos, nada é ocultado") e derruba o
  principal risco da feature: se nada some, cluster mal formado custa uma conferência a mais,
  não um normativo perdido. **Precisa de teste próprio** — não "simplificar".
- **D-C1.2 · Modelo de embeddings:** **`2b`** — `sentence-transformers` local no próprio app.
  Roda offline, inclusive nesta máquina, sem depender de terceiros para destravar.
  ➡ **Follow-up registrado:** tentar depois mover o modelo de embeddings para o servidor local.
  Pedido a repassar ao Alexandro — ver `BLOCKED-ON-RODRIGO.md`.

- **D-C2 · Chat sobre o acervo:** **não entra**. É o `wiki-chat`, projeto distinto.
- **D-C3 · Extração de dispositivos e geração de checklist:** **não entra no MVP**. O handoff
  para `/analise-normativa` e `checklist-conformidade` vai para **roadmap de feature futura**.
- **D-B2 · Adaptadores Planalto e LEGIN:** **ficam para depois**. Não entram agora; a lacuna de
  cobertura que deixam **precisa ser medida** contra um tema real (ver requisito abaixo).
- **D-B1 · Provedor de web aberta:** **reusar o que A já tem** — DuckDuckGo sem chave e Google
  CSE quando houver chave, ambos já revisados em segurança. Fecha decisão aberta desde 09/09.
- **D-C5 · Configuração do LLM:** **local primário** (`gemma-4` em `10.10.111.125:1234`),
  Gemini como alternativa configurável, `NullLLM` como padrão inerte.
- **D-C6 · Destino do repo A:** **arquivar no GitHub** depois que o golden-master provar a
  consolidação. Reversível; a tag `levantamento-v1-streamlit` garante restauração.
- **D-C7 · Push:** **a cada chunk fechado**, para o outro PC enxergar o andamento.
- **D-C8 · Lição do endpoint inalcançável:** registrar em **`~/.claude/ENVIRONMENT.md`**.

### ⚠ Requisito derivado do comentário do Rodrigo (grupo 5)

> "essa é uma ferramenta de pesquisar, então devemos conseguir pegar o máximo de coisas possível
> senão a ferramenta não será segura."

**Cobertura é requisito, não preferência.** Adiar Planalto/LEGIN (D-B2) só é aceitável porque a
web aberta (D-B1) é a **via subsidiária**. Decorre disto, e é obrigatório antes de fechar o MVP:
**medir a lacuna de cobertura** das fontes catalogadas contra um tema real, e registrar o
resultado. Cobertura insuficiente conta como falha, não como limitação conhecida.

---

## 🟢 Decididas no brainstorm de 2026-09-08

Detalhe na spec de 08/09 §4. ⚠ **A decisão B2 foi revertida em 2026-09-16** — ver spec de
consolidação §2: a base é o Streamlit já escrito, não um FastAPI novo. As demais seguem válidas.

- **B1 · Fontes:** híbrido — catalogadas primeiro, web aberta como rede de segurança, com
  procedência marcada por resultado.
- ~~**B2 · Arquitetura:** app web local (FastAPI + SQLite)~~ → **revertida em 16/09**.
- **B3 · LLM:** híbrido — o sistema roda **inteiro sem LLM**; quando configurado, enriquece.
- **B4 · Organização:** por tema/ação de controle. Mitigação obrigatória: dedup sha256 com
  detecção e relatório — nunca duplicação silenciosa.
- **B5 · Já-tenho:** mostrar todos os resultados com selo, nada é ocultado. Mitigação
  obrigatória: ação de grupo "desmarcar todos os já-tenho".

## ⚠ Decisão do repo-pai que este projeto reverte

**D-AI-01** (`projetos-nuati/projeto-AI-com-IA/decisions/`) dizia "nesta rodada não se constrói
nada". Construir o buscador **reverte isso** — decisão do Rodrigo em 08/09, já registrada no
`DECISIONS-LOG.md` daquela área.

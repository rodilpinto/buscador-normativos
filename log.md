# Log — Buscador de Base Normativa

<!-- entradas mais recentes no topo · formato: ## [data] operação | título -->

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

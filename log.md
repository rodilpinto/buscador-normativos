# Log — Buscador de Base Normativa

<!-- entradas mais recentes no topo · formato: ## [data] operação | título -->
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

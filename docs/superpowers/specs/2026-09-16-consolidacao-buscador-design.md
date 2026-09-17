# Consolidação do Buscador de Base Normativa — Design

**Data:** 2026-09-16 · **Origem:** sessão de consolidação pedida pelo Rodrigo ("merge sem
regressões, manter o melhor de cada") · **Repo alvo:** `~/Documents/solucoes/buscador-normativos/`

> **Precedência:** este documento **prevalece** sobre a spec de 2026-09-08
> (`2026-09-08-buscador-normativos-design.md`) onde houver contradição. A spec anterior
> continua válida no que não for contrariado aqui — em especial §2 (princípio), §6
> (rastreabilidade) e §7 (riscos).
>
> **Separação fato / sugestão:** ✅ = verificado nesta sessão por leitura de código, execução
> de comando ou medição. 📝 = proposta de desenho, não validada.

---

## 1. O achado que motiva esta spec

Existiam **dois projetos concorrentes**, não duas cópias do mesmo:

| | **A** — `levantamento-normativos` | **B** — `buscador-normativos` |
|---|---|---|
| Local | `~/Documents/projeto-nuati-normativos-levantamento/` | este repo |
| Criado | mar/2026 | 08/09/2026 |
| Estado | ✅ código completo e revisado | ✅ spec + plano, **zero linha de código** |
| Volume | ✅ 6.561 linhas (4.087 produção + 2.474 teste) | ✅ 16 tasks, plano de 2.641 linhas + 19 emendas |
| Stack | Streamlit + Gemini + openpyxl | FastAPI + SQLite (planejado) |
| Remoto | `rodilpinto/levantamento-normativos` | `rodilpinto/buscador-normativos` |

### 1.1 A premissa falsa de B — corrigida aqui

O `log.md` de 08/09 e a §1 da spec daquela data afirmam que **"o artefato original não
existe"**, que o buscador "nunca foi código" e que só existiria um formatador
`gerar_planilha_normativos.py` "sem nenhuma chamada de rede".

✅ **Isso está errado, e a prova é direta.** A varredura de 08/09 cobriu `solucoes/`, as
skills, e `projeto-AI-com-IA/` — **nunca** `~/Documents/projeto-nuati-normativos-levantamento/`.
Lá existe, e com chamadas de rede reais:

- `searchers/lexml_searcher.py` (501 linhas) — API **SRU/CQL** do LexML, com 3 URLs de fallback
- `searchers/tcu_searcher.py` (335 linhas) — TCU Dados Abertos
- `searchers/google_searcher.py` (499 linhas) — Google CSE + DuckDuckGo como fallback
- `llm/gemini_client.py` (504) · `deduplicator.py` (299) · `excel_export.py` (357) · `models.py` (117)
- `app.py` (1.286) — wizard de 5 passos
- Revisões de segurança (SSRF, injeção CQL, `javascript:` URI) e de qualidade aplicadas

**Ação obrigatória desta consolidação:** corrigir `log.md`, a spec de 08/09 §1 e o
`SESSION-ONBOARD-buscador.md` §3 item 2, citando esta prova. Afirmação sabidamente falsa
deixada de pé faz o próximo agente repetir o erro (regra global `verify-stale-docs`).

✅ **Segundo fato desatualizado:** a spec de 08/09 diz que o repo vive em
`~/Documents/solucoes/buscador-normativos/`. Essa pasta **não existia** nesta máquina; foi
criada nesta sessão, e o repo foi clonado nela.

---

## 2. Decisão central: A é a base, B é a lista de features

> **Inverte a decisão B2** da spec de 08/09, que descartou Streamlit em favor de FastAPI+SQLite.

**Razão da inversão.** B2 foi decidida sem saber que A existia. Naquele contexto, "Streamlit"
significava *escrever um Streamlit do zero*, e FastAPI era escolha legítima. Hoje significa
*usar 1.286 linhas já escritas, testadas e revisadas*. A premissa mudou; a decisão muda com ela.

**Instrução do Rodrigo (2026-09-16):** "evitar overcomplicate as coisas e aproveitar o que já
funciona ao máximo."

### 2.1 O que já existe em A e B planejava construir

✅ Verificado por leitura de `app.py`: `_apply_filters`, `_apply_sort`, `_init_checkboxes`,
`_select_all`, `_deselect_all`, `_count_selected`, `_render_search_diagnostics`, e os botões
**"Selecionar todos" / "Desmarcar todos"** (linhas 1007 e 1012). Isso é o mecanismo **M2**
(decisão por grupo) da spec de 08/09, parcialmente pronto — e já corrigido para checkbox
obsoleto e O(n²) nas revisões E7/E8 de A.

### 2.2 O que fica intacto (zero trabalho de port)

Searchers LexML/TCU/Google · `deduplicator.py` · `excel_export.py` · `models.py` ·
wizard de 5 passos · suíte de testes (2.474 linhas).

✅ **O acoplamento de A ao Streamlit é cosmético.** `import streamlit` aparece fora do
`app.py` em apenas 2 arquivos (`llm/gemini_client.py:57`, `searchers/google_searcher.py:32`),
sempre dentro de `try/except` e apenas para ler chave de API, com fallback para variável de
ambiente. Em `excel_export.py` as menções a `st.` são **só docstring**. `models.py`,
`deduplicator.py`, `searchers/base.py`, `lexml_searcher.py` e `tcu_searcher.py` não tocam
Streamlit. Consequência: manter Streamlit não nos prende a ele — migrar depois continua barato.

---

## 3. Escopo: as features que entram de B (F1-F7)

Tudo o mais do plano de 16 tasks **sai de escopo**. Entram, sobre código que já roda:

| # | Feature | Mecanismo da spec de 08/09 | Emendas que continuam valendo |
|---|---|---|---|
| F1 | `procedencia` (`catalogada` / `web-aberta`) | rastreabilidade §6 | — |
| F2 | `vinculacao` (`obrigatorio` / `aplicavel` / `contexto`) | M3 | — |
| F3 | Pré-marcação com motivo + **duas travas anti-ancoragem** | M4 | R1-05, R1-06 |
| F4 | Selo **"já tenho"**, casando por **sha256** (não por título) | M1 | R1-08, R1-09 |
| F5 | Download + organização por tema + relatório de duplicata | B4 | R1-07, R1-12, R1-17 |
| F6 | SQLite (retomabilidade) + colunas de registro na planilha | §6, critério 4 | R1-11, R1-15 |
| F7 | **Agrupamento semântico dos resultados** para triagem em bloco | **M2** — é o que faz o critério nº 2 fechar | — |

### 3.1 F7 — agrupamento semântico (decisão D-C1, 2026-09-16)

**Por que entrou.** Na spec de 08/09 "indexação semântica" foi cortada como YAGNI, junto com o
chat sobre o acervo. ✅ Verificado que o corte foi **por associação de nome, não por análise**:
são três coisas distintas, e só uma delas pertence ao `wiki-chat`.

✅ **O problema que F7 resolve é aritmético.** `score_relevance` (com LLM) e `_keyword_relevance`
(sem LLM) **ordenam** resultados; nenhum **agrupa**. Ordenar 100 itens muda a ordem das 100
decisões, não o número. Agrupar por metadado (`tipo`, `orgao_emissor`) produz grupos
internamente heterogêneos, em que o humano desce ao item e volta às 100 decisões. Sem
agrupamento por assunto, **o critério de sucesso nº 2 não tem mecanismo**.

> ### ⚠ Requisito vinculante — o agrupamento é ADITIVO
> "não remover do usuário a capacidade de ver tudo. os agrupamentos devem facilitar e não
> remover opções." — Rodrigo, 2026-09-16
>
> O agrupamento **oferece** um atalho para decidir em bloco. **Nunca** remove, oculta, filtra
> nem colapsa item fora da visão do usuário. Reforça a decisão B5 ("mostrar todos, nada é
> ocultado"). **Tem teste próprio** — não "simplificar".
>
> 📝 Efeito colateral notado: isto **derruba o risco principal** que a própria feature carregava
> (cluster ruim → decisão em bloco errada). Se nada some, cluster mal formado custa uma
> conferência a mais, não um normativo perdido.

**Fora de escopo, confirmado (board de 16/09):**

- **Chat sobre o acervo** (D-C2) — é o `wiki-chat`, projeto distinto, já 15/15 implementado.
- **Busca semântica sobre o acervo baixado** (opção `1c` da D-C1) — mesmo terreno do `wiki-chat`.
- **Selo já-tenho por embedding** (opção `1b` da D-C1) — não entra agora. ⚠ **Lacuna conhecida e
  não mitigada:** material **sem numeração** (manuais, frameworks, guias ANPD) continua
  escapando do selo, porque a dedup bibliográfica de A depende de `tipo|numero|data`.
- **Extração de dispositivos e geração de checklist** (D-C3) — o handoff para
  `/analise-normativa` e `checklist-conformidade` vai para **roadmap de feature futura**, fora
  do MVP.
- **Adaptadores Planalto e LEGIN** (D-B2) — adiados; ver §3.2.
- **Reescrita em FastAPI** e as tasks T14/T15.

### 3.2 Cobertura é requisito, não preferência (D-B2 + D-B1)

> "essa é uma ferramenta de pesquisar, então devemos conseguir pegar o máximo de coisas possível
> senão a ferramenta não será segura. então temos de ter formas de pegar os resultados e formas
> subsidiárias de pegar o q a ferramenta original não pegar" — Rodrigo, 2026-09-16

Adiar Planalto e LEGIN **só é aceitável porque a web aberta é a via subsidiária** (D-B1: reusar
o DuckDuckGo + Google CSE que A já tem). Decorre daí um item **obrigatório antes de fechar o
MVP**: medir a lacuna de cobertura das fontes catalogadas contra um tema real e registrar o
resultado. Cobertura insuficiente conta como **falha**, não como limitação conhecida.

---

## 4. Modelo de dados: união, com `NormativoResult` de A como base

Os dois modelos são **complementares, não concorrentes** (✅ verificado lendo `models.py` de A
e a Task 3 de B):

- **B tem e A não:** `procedencia`, `vinculacao`, `ementa_llm`, `ja_tenho`, `ja_tenho_onde`,
  `pre_marca`, `pre_motivo`, `sha256`, `coletado_em`.
- **A tem e B não:** `numero`, `orgao_emissor`, `data` completa (B só guardava `ano`),
  `situacao` (vigente/revogado), `relevancia`, `found_by` (qual palavra-chave trouxe o item).

**Decisão:** partir de `NormativoResult` de A e **acrescentar** os campos de B. Assim os
searchers, o deduplicador, o export e os 2.474 linhas de teste de A continuam válidos —
o inverso quebraria tudo. Como nenhuma linha de B foi escrita, conformar B ao modelo de A
custa zero.

📝 **Ganho colateral não planejado:** os campos bibliográficos de A (`tipo`, `orgao_emissor`)
**melhoram o M2 de B** — agrupar para decisão em bloco funciona muito melhor por tipo e órgão
emissor do que pelos campos que B tinha.

### 4.1 Dedup: a estratégia de A prevalece

✅ A dedupa por **identidade bibliográfica** (`sha256(tipo|numero|data)`, com `link` no lugar
de `numero` quando este é vazio) mais 3 estratégias em `deduplicator.py`. B planejava
`chave_dedup` por URL+título normalizados.

A de A é mais forte para normativos: pega a mesma Lei vinda de LexML **e** do Planalto com
URLs diferentes — caso que a chave de B deixaria passar. **Usamos a de A.** A `normalizar_url`
e a `chave_dedup` de B saem de escopo.

⚠ **Trava obrigatória herdada (R1-04):** todo colapso de dedup **vira registro visível** — o
que foi fundido com o quê. Dedup silencioso é proibido nas duas direções. Isso vale para o
deduplicador de A, que hoje não emite esse relatório.

---

## 5. Camada de LLM: endpoint local como caminho de produção

✅ `_generate(prompt, temperature, max_tokens)` (`llm/gemini_client.py:106`) é o **único ponto**
por onde as três funções públicas (`expand_topic_to_keywords`, `score_relevance`,
`categorize_results`) falam com o modelo. Trocar o transporte reescreve ~2 funções
(`_get_client` e `_generate`) e **preserva ~400 linhas** de prompt, parsing e fallback já
cobertas por 53/53 testes.

**Alvo:** adaptador **OpenAI-compatível**, atendendo a decisão B3 da spec de 08/09.

- **Produção:** `http://10.10.111.125:1234/v1`, modelo `google/gemma-4` (informado pelo
  Alexandro/Secin-Nuati em 14/09/2026). Endpoint e modelo vêm de **configuração**, nunca
  fixos no código.
- ⚠ ✅ **Verificado: esse endpoint não responde desta máquina** (timeout de 10s; IP `10.10.*`
  é interno da Câmara). A solução **será migrada para uma máquina na rede**, onde o LLM local
  passa a ser utilizável. Nesta máquina, desenvolvimento e teste rodam sem ele.
- **Degradação:** Gemini como alternativa configurável, e `NullLLM` como padrão inerte.

**Requisito duro (B3), agora testável:** nenhum caminho de código pode **exigir** LLM. Como o
endpoint de produção é inalcançável no ambiente de desenvolvimento, esse requisito deixa de
ser teórico — é a condição para a suíte rodar aqui.

📝 **Ganho:** somem a chave de API e os limites de tier gratuito que o próprio código de A
documenta (`gemini-2.5-flash-lite`: 15 RPM, 1.000/dia) — limite que morde exatamente no caso
de uso que originou o projeto, o acervo de 100+ normativos.

### 5.1 Embeddings são caminho SEPARADO do LLM (decisão D-C1.2)

⚠ **Distinção que precisa ficar explícita no código:** embedding **não é** o LLM. É modelo
menor e separado, que só produz vetores — não gera texto e não é o `gemma-4`, que é modelo de
geração. Confundir os dois quebra o requisito B3.

**Escolha:** `sentence-transformers` rodando **dentro do app**, não no servidor. Roda offline,
**inclusive nesta máquina**, o que destrava desenvolvimento e teste sem depender de terceiros.
Custo aceito: PyTorch e ~500MB de modelo, num projeto que hoje instala 7 pacotes leves.

📝 **Migração prevista:** quando houver modelo de embeddings no LM Studio do servidor local, a
troca é de **configuração** — a interface é a mesma, muda só quem gera o vetor. O pedido a ser
repassado ao Alexandro está em `BLOCKED-ON-RODRIGO.md` (B-01). **Não bloqueia nada**: foi por
isso que a opção local-no-app foi escolhida.

**Consequência de desenho:** F7 precisa de uma interface de vetorização de um método só
(`vetorizar(textos) -> matriz`), com pelo menos duas implementações desde o início —
`sentence-transformers` e um fallback sem modelo — para que a troca seja verdadeiramente de
configuração e não um refactor.

---

## 6. Emendas adversariais: o que continua valendo

✅ O plano de B recebeu 19 emendas vinculantes (5 bloqueadores) em 2026-09-11, acrescentadas
ao arquivo em 16/09. Reusar A **torna 8 delas sem efeito por construção**:

| Emenda | Situação | Motivo |
|---|---|---|
| R1-01 grafo de ondas errado | ❌ some | não usamos as ondas de B |
| R1-03 `normalizar_url` falha o próprio teste | ❌ some | o deduplicador de A substitui |
| R1-04 `chave_dedup` perde normativo em silêncio | ⚠ **parcial** | a chave some; **o requisito de relatório de dedup permanece** (§4.1) |
| R1-10 duas das três rotas catalogadas dão 404 hoje | ❌ some | não raspamos Planalto/LEGIN |
| R1-13 sem rate limit, User-Agent nem backoff | ❌ some | `searchers/base.py` de A já tem, com jitter |
| R1-14 toda rota FastAPI vaza conexão sqlite | ❌ some | não há FastAPI |
| R1-18 / R1-19 fixture sintética não é gate; seletor errado retorna vazio | ❌ somem | valem só para scraping |

**Continuam vinculantes:** R1-02 (instalar dependências / venv), R1-05 e R1-06 (travas
anti-ancoragem, inclusive quando furadas por ação de grupo), R1-07 (relatório de duplicata
não pode ser calculado e jogado fora), R1-08 e R1-09 (já-tenho por sha256, cobrindo o acervo
preexistente), R1-11 (coluna "Dimensão TCU"), R1-12 e R1-17 (caminho longo e pasta por tema no
Windows), R1-15 (re-execução não rebaixa decisão), R1-16 (o critério de sucesso nº 2 precisa de
teste).

📝 **Nota sobre R1-10:** ela é evidência verificada de que os adaptadores por scraping de B já
nasciam quebrados. É o argumento mais forte a favor de reusar a busca por API de A.

---

## 7. Travas anti-regressão

1. ✅ **Feito:** tag anotada `levantamento-v1-streamlit` criada em A (2026-09-16), nomeando o
   estado pré-consolidação.
2. **Golden-master antes de mexer no modelo de dados.** §4 acrescenta campos a
   `NormativoResult`, o que pode alterar a planilha. Congelar saídas de referência de
   `excel_export.py` e `deduplicator.py` (entrada fixa → arquivo de saída) e provar
   equivalência **mecanicamente**, não por leitura de código.
3. **Auditoria de preservação de documentação.** As docstrings de A são densas e carregam
   contrato (ex.: `models.py` documenta os valores esperados de `tipo` e explica por que o
   hash inclui `link` quando `numero` é vazio). Elas **movem junto com o código**. Perda seca
   de explicação conta como regressão, mesmo com saída byte-idêntica.
4. **Correção dos docs falsos de B** (§1.1), com a prova citada.
5. **`app.py` não é modificado sem herdeiro.** A UX de triagem que ele já tem (§2.1) é
   ponto de partida das features F3 e F4, não código a descartar.
6. **A não é apagado.** Depois da consolidação provada, vira somente-leitura: `README`
   apontando para este repo e arquivamento no GitHub. A tag garante restauração.

---

## 8. Critérios de sucesso

Herdados da spec de 08/09, com o nº 2 como critério central:

1. Uma busca de tema real devolve resultados **com procedência**, sem intervenção manual.
2. Uma lista de **100+ resultados é triável em menos de 15 decisões humanas** (M1–M4).
   ⚠ R1-16: isto **precisa de teste**, que hoje não existe em nenhuma task.
3. O download organiza por tema e **detecta** arquivo já baixado em outro tema.
4. A planilha final reproduz as colunas atuais do projeto **mais** as de rastreabilidade,
   incluindo "Dimensão TCU" (R1-11).
5. **Novo:** a suíte de A continua verde após a consolidação — provado por golden-master, não
   por inspeção.
6. **Novo:** o sistema roda de ponta a ponta **sem nenhum LLM configurado**.
7. **Novo (F7):** o agrupamento **nunca reduz** o conjunto visível. Teste que prova que a soma
   dos itens dos grupos é igual ao total de resultados, e que existe caminho para ver a lista
   inteira sem agrupamento. Requisito vinculante de §3.1.
8. **Novo (§3.2):** a lacuna de cobertura das fontes catalogadas foi **medida** contra um tema
   real e registrada, antes de o MVP ser considerado fechado.

---

## 9. Riscos

| Risco | Mitigação |
|---|---|
| Acrescentar campos ao modelo quebra a planilha ou o dedup de A | golden-master congelado **antes** (§7.2) |
| O LLM local não pode ser testado nesta máquina | `NullLLM` é o padrão; endpoint por configuração; teste de contrato com duplo, não com rede |
| Streamlit re-executa o script a cada interação, e a triagem precisa ser retomável | estado vive no **SQLite** (F6), não em `session_state`; o rerun lê do banco |
| Ancoragem pela pré-marcação (M4) | motivo sempre visível; contador de divergência; R1-05 e R1-06 continuam vinculantes |
| Duplicação de arquivo entre temas (B4) | dedup sha256 **com relatório** (R1-07) |
| Caminho > 260 chars no Windows | pasta de tema curta + helper de caminho longo (R1-12, R1-17) |
| 📝 Perder o histórico de A ao consolidar | tag (§7.1) + preservação de docstrings (§7.3) |

---

## 10. Como o código de A entra neste repo

**Requisito:** o histórico de A é **preservado dentro do repo consolidado**, não só na tag.
Cópia simples de arquivos perderia autoria e a cadeia de commits — regressão de rastreabilidade,
que neste projeto é requisito de essência (spec de 08/09 §6).

**Mecanismo:** A entra como **remoto adicional**, com `git merge --allow-unrelated-histories`.
Assim os 2 commits de A e sua autoria passam a viver aqui.

✅ **Colisões verificadas** (`git ls-files` nos dois repos):

| Caminho | A | B | Resolução |
|---|---|---|---|
| `.gitignore` | sim | sim | **único conflito real**; resolver à mão, unindo as duas listas |
| `spec/` | `spec/context.md`, `spec/implementation-plan/00..06`, `spec/insights.md`, `spec/todos.md` | `spec/buscador/**` | sem colisão de arquivo; mover os de A para `docs/historico/levantamento-v1/` para não competirem com o `spec/` vivo |
| `levantamento-normativos/` | código | — | sem colisão; é onde o código de A já mora |
| `docs/`, `CLAUDE.md`, `log.md`, `_TODO.md`, `_DECISOES-PENDENTES.md` | — | sim | sem colisão |

📝 **Sobre o nome da pasta de código:** manter `levantamento-normativos/` no merge (evita
renomear no mesmo commit em que se funde histórico, o que atrapalha o `git log --follow`), e
renomear para o nome definitivo **em commit separado**, depois.

⚠ **Os 21 PNGs de teste e o `.playwright-mcp/`** na raiz de A estão **não versionados** (saída
de `git status`). Não entram no merge, e não devem: são artefatos de sessão de teste.

---

## 11. O que muda nos documentos existentes

| Arquivo | Ação |
|---|---|
| `log.md` | entrada nova registrando o achado de §1.1 e esta consolidação |
| `docs/superpowers/specs/2026-09-08-...-design.md` | corrigir §1 (premissa falsa) e a B2 (stack), apontando para cá |
| `SESSION-ONBOARD-buscador.md` | reescrever §2 (fase), §3 (achados críticos) e §6 (próximo movimento) |
| `_TODO.md` | substituir as 16 tasks pelas features F1-F7 de §3 |
| `_DECISOES-PENDENTES.md` | fechar D-B1 e D-B2 à luz desta spec; abrir a de configuração do LLM |
| `CLAUDE.md` | registrar que a base é Streamlit e que o LLM é OpenAI-compatível |
| `projetos-nuati/MEMORY.md` | ponteiro para esta solução (item já aberto no `_TODO.md` de B) |

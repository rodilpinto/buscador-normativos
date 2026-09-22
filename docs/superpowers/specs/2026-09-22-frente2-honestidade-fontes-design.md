# Frente 2 da v1.x — Honestidade das fontes — Design

**Data:** 2026-09-22 · **Origem:** decisões D-C11/D-C12/D-C13 de 22/09 (`_DECISOES-PENDENTES.md`)
· **Aprovado por:** Rodrigo, em 22/09, por escolha entre alternativas (seções 1-8 apresentadas na
sessão) · **Repo:** `~/Documents/solucoes/buscador-normativos/`, código em `levantamento-normativos/`

> **Precedência:** esta spec **não** contraria a spec de consolidação de 16/09; ela detalha um
> subconjunto da v1.x que aquela não previa (os consertos da v1 foram decididos depois). Onde
> houver conflito com o plano da Fase 1 de 16/09, **o plano de 16/09 só volta a valer na v2.0**
> (T4, T7, T8, T9); as tasks T5/T6 foram puxadas para a frente 5 da v1.x (D-C11).
>
> **Separação fato / sugestão:** ✅ = medido nesta sessão por execução, `curl` ou leitura de
> código com `arquivo:linha`. 📝 = decisão de desenho, aprovada pelo Rodrigo mas ainda não
> implementada.

---

## 1. O problema, medido

✅ Em 2026-09-22 o app v1.0 foi dirigido pelo navegador até o Passo 4 com as fontes LexML e TCU.
Resultado: *"Nenhum normativo encontrado"*, relatório **"0 OK, 0 erros, 4 sem resultados"**.
As duas fontes estavam **quebradas**, por motivos diferentes, e a UI não distinguiu isso de
"o tema não tem normativo":

| Fonte | O que acontece | Onde o código erra |
|---|---|---|
| **LexML** | `GET /busca/SRU` devolve **HTTP 200 `text/html`** com `<title>Verificação de segurança — Senado Federal</title>` — desafio de **JavaScript**, não XML SRU. Só `/busca/` está desafiado (a home abre). User-Agent descritivo não muda nada. Os 2 URLs de fallback (`/sru/SRU`, `/srw/SRU`) são **404**. | `_parse_sru_response` captura `ET.ParseError` e devolve `([], 0)` (`lexml_searcher.py:395-397`); `search()` vê lista vazia sem erro e grava `status="empty"` (`:133-137`). |
| **TCU** | `atonormativo/recupera-atos-normativos` devolve **HTTP 500** nas 3 tentativas com backoff. `acordao/recupera-acordaos` responde 200 JSON em 0,66s. | `_request_with_retry` devolve `None` após os retries (`tcu_searcher.py:248-251`); `_fetch_all_pages` trata `None` como **fim das páginas** (`break`, `:198`); `_fetch_all_pages_safe` devolve `(itens, "")` — erro vazio. Só marca `error` se **os dois** endpoints falharem (`:88-96`), e mesmo assim só se a exceção subir, o que não acontece. O 503 da janela de manutenção (`:227-234`) segue o mesmo caminho. |
| **Rede daqui** | ✅ `curl` em google.com e no host do LexML: 200 em ~0,35s. Não é proxy nem rede. | — |

✅ **Consequência medida no runner:** `test_searchers.py` leva **~390s** (T2, 22/09) porque cada
palavra-chave tenta os 3 URLs do LexML de novo — `_sru_url` só é cacheado em **sucesso**
(`lexml_searcher.py:327-343`) — e o TCU faz 3 retries com backoff por endpoint.

✅ **E a nota de relevância tem o mesmo defeito de honestidade**, por outro caminho:

- `score_relevance` só é chamada dentro de `if llm_available()` (`app.py:571`). Sem chave, a nota
  **nunca é calculada**: fica na constante do searcher (`0.3` Google/DDG em
  `google_searcher.py:331,393`; `0.5` LexML `:489` e TCU `:283,317`).
- A heurística determinística `_keyword_relevance` (`gemini_client.py:233`) só roda quando
  `is_available()` é falso **dentro** de `score_relevance` — que nesse caso não é chamada. **Código
  inalcançável pelo app.**
- Com LLM, lote que volta vazio ou malformado recebe `0.5` para todos os 20 itens
  (`gemini_client.py:403-416`). `0.5` pode ser nota do modelo, fallback de erro, ou default do
  LexML/TCU. **Três procedências, um número, nenhuma marca.**

**Por que isto é a frente mais urgente.** Requisito vinculante do Rodrigo (16/09): *"essa é uma
ferramenta de pesquisar, então devemos conseguir pegar o máximo de coisas possível senão a
ferramenta não será segura."* Uma fonte bloqueada que aparece como "sem resultado" faz o auditor
concluir que o normativo não existe. É o pior resultado possível para uma ferramenta de critério.

---

## 2. Decisões que esta spec implementa

| Decisão | Escolha do Rodrigo (22/09) | Alternativas descartadas |
|---|---|---|
| Onde o fato "fonte indisponível" / "nota veio de fallback" fica gravado | **Na tela E na planilha exportada** | só na tela (a lacuna persistiria no artefato de auditoria); tela + planilha + log por busca (escopo maior, decisões novas de retenção) |
| O que fazer com a nota quando não há LLM | **Rodar a heurística e rotular a origem** | manter a constante e só rotular (nota continua sem significado offline); não exibir nota (tira a ordenação de quem está offline) |
| Contornar o desafio do WAF do LexML | ⛔ **Nunca.** | — |

---

## 3. Desenho

### 3.1 Vocabulário de status (`models.py`)

📝 `KeywordStatus` **mantém** `status: "ok" | "empty" | "error"` — a UI (`app.py:914-916`) e os
searchers já dependem dos três valores, e nenhum teste precisa mudar por causa do vocabulário.
Muda o **significado** de `error`: passa a ser **"a fonte não pôde ser consultada"** (bloqueio,
5xx, timeout, resposta ilegível), e o rótulo na tela vira **"indisponível"**.

Campos novos, todos com default para não quebrar construtores existentes:

```python
motivo: str = ""        # "" | bloqueio_waf | http_5xx | manutencao_503 | timeout | conexao | resposta_ilegivel
detalhe: str = ""       # URL, HTTP status, content-type, primeiros 120 chars do corpo — o que
                        # um humano precisa para reproduzir com curl
parcial: bool = False   # status == "ok", mas a paginação parou por erro: "achei 40, a fonte
                        # caiu na página 3" é diferente de "achei 40"
```

`motivo` é string com valores fechados (não `Enum`) para caber na planilha e no JSON sem
conversão; o conjunto vive numa constante `MOTIVOS` em `models.py`, e um teste afirma que todo
`motivo` gravado está nela.

### 3.2 LexML (`searchers/lexml_searcher.py`)

📝 `_try_fetch` deixa de confiar em HTTP 200. Depois de `raise_for_status()`:

1. Se o `Content-Type` não contém `xml` **ou** o corpo, sem espaços iniciais, não começa com
   `<?xml` nem `<srw:` nem `<searchRetrieveResponse` → não é SRU.
2. Se o corpo contém `Verificação de segurança` ou `challenge` → levanta
   `FonteIndisponivel(motivo="bloqueio_waf", detalhe=...)`. Senão → `resposta_ilegivel`.
3. `_parse_sru_response` deixa de engolir `ET.ParseError`: levanta `FonteIndisponivel("resposta_ilegivel")`.
   Devolver `([], 0)` era a linha que transformava bloqueio em "sem resultado".

`FonteIndisponivel(Exception)` nasce em `searchers/base.py` com os campos `motivo` e `detalhe`;
`_search_keyword_safe` (`:236-241`) passa a preencher `KeywordStatus.motivo/detalhe` a partir
dela, em vez de `str(e)` genérico. `ConnectionError` e `Timeout` do `requests` mapeiam para
`conexao` e `timeout`.

📝 **Cache de falha por busca.** `_fetch_sru` hoje só cacheia o URL que **funcionou**. Passa a
lembrar, por instância (= por busca), os URLs que falharam com 404 ou bloqueio, e não os tenta de
novo para a palavra-chave seguinte. Os dois fallbacks continuam no código (podem voltar a existir);
só deixam de custar 2 requisições × N palavras-chave por busca. É a única mudança desta frente que
altera **quantas** requisições saem, e é para menos.

⚠ O que **não** muda: a cadeia de URLs, o CQL, a paginação, o mapeamento de campos, o
`REQUEST_TIMEOUT`. O `timeout` em tupla `(3.05, read)` é assunto da frente 5 (emenda A7 do plano).

### 3.3 TCU (`searchers/tcu_searcher.py`)

📝 `_fetch_all_pages` passa a devolver `(itens, erro, parcial)`:

- `_request_with_retry` devolve `None` **na primeira página** → `erro = FonteIndisponivel(...)`,
  `itens = []`. Motivo: `http_5xx` para 5xx após retries; `manutencao_503` para 503, com o
  `detalhe` carregando o texto que o código já sabe ("indisponível diariamente das 20h às 21h");
  `timeout` / `conexao` para os respectivos.
- `None` numa página **seguinte** → `parcial = True`, `erro` preenchido, `itens` = o que veio.
  Hoje isso é `break` silencioso ("return what we have", `:198`).

`search()` passa a marcar `error` para a palavra-chave se **qualquer** endpoint falhou na primeira
página, com `detalhe` dizendo qual (`Acórdãos: ok (312 itens) · Atos: http_5xx em <url>`). Se um
endpoint respondeu e o outro caiu, os resultados do que respondeu **continuam entrando** — o
status é `error` com `result_count > 0`, e a UI mostra os dois fatos. `parcial` sobe para o
`KeywordStatus`.

### 3.4 Procedência da nota de relevância

📝 `NormativoResult` (`models.py`) ganha:

```python
relevancia_origem: str = "padrao_fonte"   # modelo | heuristica | fallback_erro | padrao_fonte
```

Valores fechados em `ORIGENS_RELEVANCIA` em `models.py`. Os searchers não mudam: continuam
atribuindo a constante, e o default `padrao_fonte` diz a verdade sobre ela.

📝 `llm/gemini_client.py` ganha `score_relevance_com_origem(topic, results, keywords) ->
list[tuple[float, str]]`. A `score_relevance` existente (53 testes em `test_llm_phase3.py`)
**não muda de assinatura**: passa a ser um wrapper que descarta a origem. Regras da origem:

| Caminho em `score_relevance` hoje | Origem |
|---|---|
| `is_available()` falso, com keywords → `_keyword_relevance` | `heuristica` |
| `is_available()` falso, sem keywords → `[0.5] * n` | `fallback_erro` (não há o que calcular; rotular honestamente) |
| lote com resposta vazia → `0.5` | `fallback_erro` |
| lote com tamanho errado ou JSON ilegível → `0.5` | `fallback_erro` |
| valor não numérico dentro de um lote válido → `0.5` | `fallback_erro` (só aquele item) |
| valor numérico (clampado) | `modelo` |

📝 `app.py` (`:570-588`): a pontuação sai de dentro do `if llm_available()`. Passa a rodar
**sempre** que há resultados: `score_relevance_com_origem` decide sozinha entre modelo e
heurística. A **categorização** continua condicionada ao LLM (não há heurística para ela; sem
modelo fica `Nao categorizado`, que já é honesto). Texto de progresso: "Avaliando relevância com
IA..." quando há modelo; "Avaliando relevância por palavras-chave..." quando não há.

📝 `deduplicator._merge` (`:147`) guarda `max(existing.relevancia, incoming.relevancia)`. Passa a
levar `relevancia_origem` do registro **cuja nota venceu**. Empate: mantém o existente (ordem de
chegada, que já é a regra do módulo). A docstring do `_merge` (que lista campo a campo o que é
fundido) ganha a linha correspondente — documentação move com o código.

### 3.5 Planilha (`excel_export.py`)

📝 **Coluna nova** em `COLUMNS`, logo após `Relevancia`:
`("Origem da nota", 16, "relevancia_origem")`. Valores em português na célula: `modelo` →
"Modelo (IA)", `heuristica` → "Heurística (palavras-chave)", `fallback_erro` → "Fallback (erro do
modelo)", `padrao_fonte` → "Padrão da fonte". ✅ `test_phase4.py:424` e `:438` fixam **10**
colunas/cabeçalhos — passam a fixar **11**, no mesmo commit; `:443` lista os cabeçalhos, ganha o
novo.

📝 **Aba nova "Diagnostico da busca"**, criada **depois** da `Normativos` (que continua
`wb.active` — `test_phase4.py:377` afirma isso). Colunas: `Fonte · Palavra-chave · Status ·
Motivo · Detalhe · Resultados · Parcial · Retentado`. Uma linha por `KeywordStatus`. Linha de
título com o tema e a data/hora da busca. Status na célula em português: `ok` → "OK", `empty` →
"Sem resultado", `error` → "Indisponível".

📝 `generate_excel(results, topic)` ganha parâmetro **opcional** `diagnostico: list[KeywordStatus]
| None = None`. `None` ou lista vazia → a aba é criada com título e cabeçalho e uma linha
"Nenhum diagnóstico registrado nesta exportação" — a aba **sempre existe**, para que quem abre a
planilha saiba que o campo é previsto. `app.py` passa `st.session_state["keyword_statuses"]`.

⚠ **Golden-master.** `tests/golden/planilha_sha256.txt` **vai divergir** — coluna nova e aba nova
(o hash lê `wb.active`, que é `Normativos`, então só a coluna pesa; a aba de diagnóstico não entra
no hash porque o corpus fixo não tem `KeywordStatus`). Procedimento: o commit que muda
`COLUMNS` **recongela no mesmo commit** (`python tools/golden_master.py congelar`) e a mensagem do
commit diz por quê, citando esta seção. O `dedup_esperado.json` **não** pode mudar — `_merge`
levar a origem junto não altera `id`, `nome` nem `link`; se mudar, é regressão.

### 3.6 Tela (`app.py`)

📝 `_render_search_diagnostics` (`:840-905`):

- Rótulo: `Relatório da busca — {n_ok} OK · {n_err} indisponíveis · {n_empty} sem resultado
  ({total} buscas)`. Métricas idem. Expander abre sozinho se houver `error` **ou** `parcial`.
- Seção de `error` passa a se chamar **"Fontes indisponíveis"**, e cada linha mostra `motivo` e
  `detalhe` (escapados). A legenda troca "erros de rede ou API" por: *"A fonte não pôde ser
  consultada. Isso NÃO significa que não existem normativos — significa que esta busca não os
  viu. Motivo e detalhe acima; a aba 'Diagnostico da busca' da planilha registra o mesmo."*
- `parcial` aparece como badge `(parcial)` ao lado do `result_count`, com uma linha de legenda.
- Bloco novo, **acima** do relatório, só quando **toda** fonte catalogada selecionada deu `error`:
  `st.warning`: *"Nenhuma fonte catalogada respondeu nesta busca. Os resultados abaixo vêm só da
  web aberta."* — é o caso de 22/09, e é a frase que o usuário precisava ter lido.

📝 Card do resultado (`:1049-1065`): `Relevancia: 30% · heurística` (ou `modelo` / `fallback` /
`padrão da fonte`). Preview do Passo 5 (`:1221-1232`): coluna `Origem` depois de `Relevancia`.

📝 `app.py:291-296` (instrução de configurar `secrets.toml`) **não** muda aqui — é a emenda A15,
frente 5.

### 3.7 O que NÃO muda

- Nenhum searcher muda **o que** busca (CQL, endpoints, filtros, mapeamento de campos).
- `deduplicate` não muda estratégia, ordem nem critério; `dedup_esperado.json` é o gate.
- `score_relevance` não muda assinatura nem os 53 testes que a cobrem.
- Nada de rede em teste novo: respostas enlatadas (fixtures).
- `.streamlit/`, `requirements.txt`, `pyproject` (não existe ainda; T4 é v2.0).

---

## 4. Verificação

**TDD por mudança**, na ordem da §3 (cada item: teste que falha → ver falhar → implementar →
ver passar → commit + push):

| # | Teste (sem rede) | Prova |
|---|---|---|
| V1 | `models`: `KeywordStatus(motivo="x")` fora de `MOTIVOS` é rejeitado; defaults preservam construtores antigos | `test_phase4.py` (pytest) |
| V2 | LexML: fixture com o **HTML real** do desafio do Senado (capturado em 22/09, salvo em `tests/fixtures/lexml_desafio_senado.html`) → `status="error"`, `motivo="bloqueio_waf"`, `detalhe` cita o título | novo `tests/test_fontes_indisponiveis.py` (pytest), `requests.get` dublado |
| V3 | LexML: corpo `<html>` genérico → `resposta_ilegivel`; XML SRU válido (fixture) → `ok` com contagem; XML truncado → `resposta_ilegivel` | idem |
| V4 | LexML: 404 no primário e nos 2 fallbacks → **cada URL é tentado uma vez por busca**, não uma vez por palavra-chave (contar chamadas do dublê) | idem |
| V5 | TCU: 500 × 3 no endpoint de atos, 200 no de acórdãos → `status="error"`, `motivo="http_5xx"`, `result_count` dos acórdãos, `detalhe` nomeia o endpoint | idem |
| V6 | TCU: 503 → `manutencao_503`; `None` na 2ª página → `ok` com `parcial=True` | idem |
| V7 | `score_relevance_com_origem`: sem LLM → `heuristica` e nota = fração de keywords; lote vazio → `fallback_erro`; `score_relevance` continua devolvendo `list[float]` idêntico | `test_llm_phase3.py` (script; **BASELINE 53 → 5x**, atualizado no mesmo commit) |
| V8 | `_merge` leva a origem da nota vencedora; `dedup_esperado.json` **não** muda (`golden_master.py comparar`, ramo do dedup) | `test_phase4.py` + golden-master |
| V9 | `generate_excel`: 11 colunas; célula de origem em português; aba `Diagnostico da busca` existe, com N+2 linhas para N statuses e 3 linhas para `None`; `wb.active.title == "Normativos"` | `test_phase4.py` (asserts de 10 → 11 atualizados) |
| V10 | Golden-master recongelado **no commit de V9**, com a mensagem citando §3.5 | `git log` + `ambiente.txt` |
| V11 | App dirigido pelo navegador (Playwright, `channel="chrome"`): busca com LexML + TCU + DDG → relatório mostra **indisponíveis ≥ 1**, o aviso "Nenhuma fonte catalogada respondeu", e o card mostra `· heurística` ou `· modelo` | roteiro em `tools/` ou no plano; é o gate humano-visível |

**Gate de fechamento da frente:** `python tools/run_all_tests.py` → TUDO VERDE, exit 0, com o
BASELINE novo; `python tools/golden_master.py comparar` → OK (após o recongelamento de V10);
V11 executado e o screenshot lido. Tag **não** é criada aqui — a `v1.x` marca o fim das 5 frentes
(D-C10).

**Auditoria de documentação** (regra global `docs-move-with-code`): o diff de cada commit contra
o anterior é lido inteiro por `git diff -U0 | grep '^-' | grep -v '^---'`, sem `head`, e toda
docstring/comentário removido é reposto ou movido. Alvo conhecido: a docstring de `_merge`
(lista de campos fundidos) e a de `_fetch_all_pages` ("Empty list on total failure" fica falsa).

---

## 5. Arquivos tocados

| Arquivo | Mudança |
|---|---|
| `levantamento-normativos/models.py` | `KeywordStatus.motivo/detalhe/parcial`; `NormativoResult.relevancia_origem`; constantes `MOTIVOS`, `ORIGENS_RELEVANCIA` |
| `levantamento-normativos/searchers/base.py` | `class FonteIndisponivel(Exception)` |
| `levantamento-normativos/searchers/lexml_searcher.py` | sniff de conteúdo em `_try_fetch`; `ParseError` levanta; cache de falha em `_fetch_sru`; mapeamento para `motivo` em `_search_keyword_safe` |
| `levantamento-normativos/searchers/tcu_searcher.py` | `_fetch_all_pages` → `(itens, erro, parcial)`; classificação por endpoint em `search()` |
| `levantamento-normativos/llm/gemini_client.py` | `score_relevance_com_origem`; `score_relevance` vira wrapper |
| `levantamento-normativos/deduplicator.py` | `_merge` leva a origem; docstring |
| `levantamento-normativos/excel_export.py` | coluna "Origem da nota"; aba "Diagnostico da busca"; parâmetro `diagnostico=` |
| `levantamento-normativos/app.py` | pontuação sempre; relatório com "indisponíveis" e `parcial`; aviso de "nenhuma catalogada respondeu"; card e preview com origem; passa `diagnostico=` |
| `levantamento-normativos/test_phase4.py` · `test_llm_phase3.py` | asserts de 10 → 11 colunas; testes de origem |
| `levantamento-normativos/tests/test_fontes_indisponiveis.py` · `tests/fixtures/*` | **novos** |
| `tools/run_all_tests.py` | `BASELINE` atualizado por commit que acrescenta teste; nova suíte em `SUITES_PYTEST` |
| `tests/golden/planilha_sha256.txt` · `ambiente.txt` | recongelados no commit de V9/V10 |
| `_TODO.md` · `log.md` · `LESSONS.md` · `SESSION-ONBOARD-buscador.md` | fechamento |

⚠ **Colisão com a frente 5** (`gemini_client.py`, `app.py`): esta frente fecha e pusha antes
de a frente 5 começar (D-C11). A frente 5 lê o `git log` desta.

---

## 6. Fora de escopo — registrado para não voltar

- ⛔ **Resolver o desafio de JavaScript do LexML** — contornar proteção anti-robô. O caminho é o
  B-05 (`BLOCKED-ON-RODRIGO.md`).
- Fontes novas (Planalto/LEGIN) — frente 3.
- Abas de explicação na planilha e no app (F8/F9) — frente 4; esta frente cria o **vocabulário**
  que aquela vai explicar.
- Transporte do LLM, `timeout=(3.05, 60)`, `BUSCADOR_LLM_*`, mensagem do `secrets.toml` (A7,
  A15, A20 do plano) — frente 5.
- Reduzir os ~390s dos testes LIVE — 📝 sugestão: variável `BUSCADOR_SKIP_LIVE=1` respeitada por
  `test_searchers.py`/`test_comprehensive.py`. **Não decidido; não entra aqui.**
- Log por busca em arquivo (a terceira opção da decisão de rastreabilidade) — não escolhida.

---

## 7. Critérios de pronto

1. V1–V11 verdes, cada um com o commit que o introduziu no `git log`.
2. `run_all_tests.py` TUDO VERDE com BASELINE atualizado; nenhum `[AVISO] cresceu` pendente.
3. `golden_master.py comparar` OK; `dedup_esperado.json` byte-idêntico ao de 22/09 (`d054d5b`).
4. Dirigindo o app com LexML + TCU quebrados como estão hoje: **é impossível** ver "0 erros".
5. Auditoria de documentação feita e citada no commit final da frente.
6. `_TODO.md`, `log.md`, `SESSION-ONBOARD` atualizados; push feito (D-C7).

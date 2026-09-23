# T9 · Tela: pontuar sempre, relatório por motivo, avisos por fonte, origem no card/preview, fonte que levanta não some — registro de implementação

> Task: `../tasks/09-tela-honesta.md` (plano v4, linhas 2641-2874 depois da anotação da T4 no plano; o plano é a fonte de verdade).
> Worktree `bn-t9`, branch `frente2/t9` (criada de master `3e1f279`), 23/09/2026.
> Commits: **`49d19e1`** `feat(frente2): a tela classifica por motivo, avisa por fonte e mostra a origem da nota` ·
> **`0370a21`** `fix(frente2): review da T9 — texto da fonte literal no card (_md_html); aviso da web aberta honesto`.
> Teste independente: **APROVADO**. Revisão de código: **APROVADO**, com 1 importante (F1) e 1 menor (F2), os dois aplicados no `0370a21`.
> Vereditos completos: `../execucao/revisoes/T9.md`.

## 1. O que foi feito

| Arquivo | Símbolos |
|---|---|
| `levantamento-normativos/app.py` | **Step 1:** `from datetime import datetime`, `from zoneinfo import ZoneInfo`, `from models import KeywordStatus, NormativoResult, ORIGENS_RELEVANCIA, statuses_para_falha_total` (sem `rotulo_status`, R3), e `ORIGEM_CURTA` no topo, com um comentário que aponta para o teste de sincronia. **Step 2:** bloco H2 no `except` do laço de fontes. **Step 3:** a pontuação roda sempre, via `score_relevance_com_origem`; uma origem desconhecida é logada e vira `padrao_fonte`; a categorização continua condicionada ao LLM. **Step 4:** `_render_search_diagnostics(kw_statuses)`, que classifica por motivo. **Step 5:** `catalogadas`/`indisponiveis`/`por_fonte`/`mortas`/`parciais_fonte` calculados uma vez; a closure `_avisos_por_fonte()` é chamada depois do `st.header` dos dois ramos; `st.error` novo. **Step 6:** origem no card; coluna `Origem` no preview; `generate_excel(..., diagnostico=, quando=<BRT>)`. **Escape (item carregado da T2/T3 + review F1):** helpers `_md_texto`, `_md_codigo`, `_md_html` e os conjuntos `_MD_PONTUACAO`/`_MD_PONTUACAO_HTML`, logo antes de `_render_search_diagnostics`. **Review:** F2 (frase da web aberta), `found_by` vazio → "N/I", destino do link com `quote`, e `redigir(str(e))` no log do `except` |
| `levantamento-normativos/test_phase4.py` | `TestRotulosSincronizados::test_origem_curta_do_app_cobre_o_vocabulario` (plano). **Além do plano:** `TestEscapeDaTela` com 3 testes (`_md_texto`, `_md_codigo`, `_md_html`); `TestAvisoPorFonte` com 1 teste AppTest; helper `_apptest_passo4`; amostras `_AMOSTRAS_TELA` |
| `tools/dirigir_app.py` | **novo**, verbatim do plano (gate V11) |
| `.gitignore` | `tests/evidencia/` |
| `tools/run_all_tests.py` | só `BASELINE["test_phase4.py"]`: 71 → 74 (`49d19e1`) → **76** (`0370a21`) |

`dedup_esperado.json` e o golden **não mudaram**.

## 2. Desvios do plano e por quê

1. **Escape da tela (item carregado T2/T3), em `49d19e1`.** O código do plano punha `html_module.escape` dentro de `st.markdown` e de code spans.
   - **Causa:** sem `unsafe_allow_html`, o Streamlit **não** interpreta HTML (mostra a tag como texto), mas interpreta Markdown. Dentro de code span a entidade sai literal: `&#x27;` e `&lt;!DOCTYPE` na tela, como visto no e2e da T2 e da T3. Em texto normal, a entidade era decodificada, mas `*`, `_`, `[`, `:red[` e `$` do texto externo continuavam formatando.
   - **Regra adotada** (comentário no código): `html.escape` **só onde o HTML é interpretado**; no Markdown, escape de Markdown; o detalhe longo vai em `st.code`.
   - `_md_texto(t)`: barra invertida antes de toda pontuação ASCII do conjunto `_MD_PONTUACAO`. Qualquer pontuação ASCII aceita barra no CommonMark, e o Streamlit documenta `\$`. Quebra de linha vira espaço.
   - `_md_codigo(t)`: code span sem `html.escape`. A cerca tem uma crase a mais que a maior sequência de crases do texto, com espaço nas pontas quando precisa.
   - `st.code(..., wrap_lines=True)` em todo detalhe: o detalhe longo quebra linha e não estoura a largura.
   - Aplicado no relatório inteiro e em "Encontrado por".
2. **`_md_html` (review F1), em `0370a21`, e por que é diferente de `_md_texto`.**
   - **O problema:** o card usa `unsafe_allow_html=True`, e ali o HTML **e** o Markdown são interpretados. Só com `html.escape`, a ementa `R$ 1.000,00 a R$ 5.000,00` virava LaTeX inline (os `$` sumiam), `*caput*` virava itálico e `[a](http://b.c)` virava link. Isso é texto normativo alterado na tela, contra a regra de nunca parafrasear.
   - **Por que não `_md_texto` depois de `html.escape`:** escaparia em dobro. `&amp;` viraria `\&amp;`, e a tela mostraria `&amp;`.
   - **O que `_md_html(t)` faz:** `html.escape(t, quote=False)` e depois o escape de Markdown com `_MD_PONTUACAO_HTML = _MD_PONTUACAO - {"&", ";"}`, porque esses dois formam as entidades que o navegador tem de ler.
   - **Truncamento:** no card, o texto é truncado **cru** antes do escape (`(item.ementa or "")[:200]`). Antes, `html.escape(...)[:200]` podia partir uma entidade ao meio.
   - **Onde se aplica:** nome, tipo, órgão, data, fonte e rótulo da origem.
   - **No expander** (sem HTML: "Ementa completa", Categoria, Situacao, Numero): `_md_texto`.
3. **Rótulo da origem no card com escape.** O plano não escapava. O `.get` devolve o valor cru quando a chave falta, e ali o HTML é interpretado. Hoje o rótulo passa por `_md_html`.
4. **Docstring de `_render_search_diagnostics`.** O plano dizia "Rotulos vem de models.rotulo_status", o que é falso: a tela não importa `rotulo_status` (R3). O texto novo diz que os rótulos seguem esse vocabulário, mas a tela agrupa por motivo, e só a planilha rotula por status.
5. **Step 5 como closure.** A parte de exibição (`st.warning` e legenda M14) é a closure `_avisos_por_fonte()`, chamada depois de cada `st.header`, em vez do mesmo bloco colado duas vezes. O cálculo é feito uma vez, como o plano pede.
6. **F2 (review, menor).** "O que aparece abaixo vem só da web aberta." sai só quando há resultado. Sem resultado e com o Google consultado: " A web aberta também não entregou resultado." Sem Google: " Nenhuma outra fonte foi consultada."
7. **Menores aceitos pelo orquestrador** (`0370a21`):
   - `found_by` vazio → "N/I", em vez de um code span vazio.
   - Link do expander: o texto passa por `_md_texto`; o destino passa por `quote(link, safe=":/?#@!$&'*+,;=%~-._")`, então `( ) [ ] < >` e espaço viram `%XX`. Antes, um `)` na URL fechava o link.
   - `logger.error` do `except` do laço de fontes: `redigir(str(e))`.
8. **Comentários preservados/estendidos:**
   - `# Summary metrics` (o código do plano o perdia) e `# Convert NormativoResult objects…` ficaram.
   - `# Escape ementa to prevent XSS…` e `# Detail expander — escape all external data…` foram estendidos com o porquê do helper.
   - Os comentários `# LLM enrichment…`, `# Score relevance` e `# Categorize` foram substituídos pelos comentários do plano ("Relevancia SEMPRE roda…" e "Categorizacao continua condicionada ao LLM…").
9. **Contagens.**
   - `test_phase4` = **76**: 72 do plano, +2 do escape em `49d19e1` (`_md_texto`, `_md_codigo`), +2 da review em `0370a21` (`_md_html`, AppTest da web aberta).
   - Total do runner: 13+64+98+76+45 = **296**. O plano diz 283 e não conta: o record extra da T6 (+1), os testes de review da T2–T5 na suíte nova (45 em vez de 37) e estes 4.
   - `ORIGEM_CURTA` ficou em `app.py`, porque importar `app` fora do Streamlit funciona (o `test_comprehensive` já faz isso).

## 3. Gates e saídas

### Implementador, `49d19e1`

- **Step 1, ver falhar:** `ImportError: cannot import name 'ORIGEM_CURTA' from 'app'` → depois: `1 passed`.
- **Escape, ver falhar:** com `_md_texto`/`_md_codigo` trocados pelo padrão antigo (plugin descartável no scratchpad), os 2 testes falham assim:
  - `assert 'd&#x27;água' == "d'água"` (o bug da tela);
  - `'negrito italico link :red[cor]' == '**negrito** …'` (formatação injetada).
- **Runner** (`timeout 900 python -u tools/run_all_tests.py`, foreground): 13 / 64 / 98 / 74 / 45 → **TUDO VERDE** (294).
- **Golden:** `golden-master OK`.
- **Auditoria:** `git diff -U0 HEAD~1 -- '*.py' | grep '^-' | grep -v '^---'` → 86 linhas, lidas inteiras; os comentários e a docstring removidos têm destino (§2.8). `git grep` dos símbolos: `_render_search_diagnostics` tem só as 2 chamadas em `render_step4`, as duas com `(kw_statuses)`; `generate_excel` tem a chamada nova no `app.py`; `score_relevance` sobra só no wrapper, no `__init__` e nos testes.

### Implementador, `0370a21`

- **Ver falhar:**
  - `ImportError: cannot import name '_md_html' from 'app'`;
  - `AssertionError: assert 'vem só da web aberta' not in 'Nenhuma fon…'`.
- **Depois:** `test_phase4.py` → `76 passed`.
- **Runner:** 13 / 64 / 98 / **76** / 45 → **TUDO VERDE** (296). **Golden:** `golden-master OK`.
- **Auditoria:** as linhas removidas são as trocadas por `_md_html`/`_md_texto`, o `BASELINE` e o import; os 2 comentários removidos voltam estendidos.

### Gate visual V11 (`tools/dirigir_app.py`, app sem chave de LLM, porta 8501)

Rodado 3 vezes (implementador em `49d19e1`, testador, implementador em `0370a21`), sempre **7/7 OK**:

```
  OK  relatório mostra ≥1 indisponível
  OK  bloqueio_waf visível na tela
  OK  aviso por fonte presente
  OK  TCU declarado parcial (acórdãos 200, atos 500 — cenário de 22/09)
  OK  origem no card
  OK  nenhum card sumiu (cards == N do cabeçalho)
  OK  '0 erros' não aparece
GATE V11 OK
```

O cenário de 22/09 continua valendo em 23/09: LexML com `bloqueio_waf`, e TCU com acórdãos 200 e atos 500.

**O que o PNG mostra** (`tests/evidencia/v11_passo4.png`, não versionado):
- O header "Passo 4 - Revisar Resultados (17 normativos)"; foram 18 na primeira rodada, porque o Google varia.
- Abaixo do header, o aviso amarelo "Cobertura incompleta nas fontes catalogadas: lexml indisponível (bloqueio_waf); tcu respondeu parcialmente (0 resultado(s); http_5xx)…".
- A legenda M14.
- O relatório aberto: "2 OK · 4 indisponíveis · 0 sem resultado · 0 não consultadas (6 buscas)", com 5 métricas.
- Dois lexml `bloqueio_waf` e dois tcu "(parcial)" `http_5xx`.
- O detalhe em bloco de código **quebrando linha**, com `'<!DOCTYPE html>\n<meta name="viewport"…` **literal**, sem `&#x27;`, `&quot;` ou `&lt;`.

⚠ **Caveat D-C17 (testador):** o check "cards == N do cabeçalho" conta depois do dedup, então não enxerga fusão fuzzy. Prova que a tela não perde card; não prova que o dedup não fundiu demais.

**Olhado fora do V11** (scripts descartáveis, no scratchpad):
- Um card: "Relevancia: 50% *(heurística)*".
- O preview do Passo 5, com a coluna "Origem" = "heurística".
- O xlsx baixado pela UI: abas `Normativos` + `Diagnostico da busca`, K2 "Origem da nota", título "Diagnóstico da busca: LGPD — 23/09/2026 16:29" (BRT).

**E2E hostil do card (`0370a21`).** Um wrapper descartável pré-carrega no `session_state` um resultado com:
- nome `Portaria *caput* __x__ [a](http://b.c) :red[x]`;
- ementa `Fixa multa de R$ 1.000,00 a R$ 5.000,00; *caput* do art. 5º; a &amp; b; <b>negrito?</b> d'a`;
- órgão `Órgão & Cia <b>x</b>`;
- situação `Vigente $x$`;
- link `https://exemplo.gov.br/a_(b)`;
- `found_by` vazio.

Com isso, roda o `app.py` real no Chrome. O screenshot mostra tudo **literal**: nenhum KaTeX no DOM, nenhum `<b>` injetado, os `$` presentes, `&amp;` exibido como `&amp;`, o link com o texto `a_(b)` inteiro e "Encontrado por: N/I".

### Testador (resumo; íntegra em `../execucao/revisoes/T9.md`)

- Runner 294 verde, golden OK, V11 7/7.
- 7 cenários de honestidade sem rede (AppTest), todos ✔:
  - só web aberta;
  - TCU parcial ≠ indisponível (R3-H4);
  - `nao_consultada` sem expander vermelho (R2-B6);
  - fonte que levanta (H2);
  - `st.error` novo;
  - sem LLM → heurística + M14;
  - origem inventada → log + `padrao_fonte`.
- Página hostil real: relatório e "Encontrado por" literais.

## 4. Achados de teste e revisão, e para onde foram

| # | Achado | Origem | Destino |
|---|---|---|---|
| F1 | Card e "Ver detalhes" passavam o texto da fonte pelo Markdown: `R$…R$` virava LaTeX, `*caput*` itálico, link clicável | testador (médio, pré-existente); reviewer (importante) | **Corrigido em `0370a21`** (`_md_html` no card, `_md_texto` no expander; §2.2) |
| F2 | "vem só da web aberta" com 0 resultados | testador / reviewer (menor, código do plano) | **Corrigido em `0370a21`** (§2.6) + teste AppTest |
| m1 | `found_by` vazio → code span vazio | reviewer (menor) | **Corrigido** ("N/I") |
| m2 | Link `[u](u)` quebra com `)`/`]` | reviewer (menor) | **Corrigido** (`quote` no destino) |
| m3 | `app.py` loga a exceção sem `redigir` | reviewer (menor) | **Corrigido** (`redigir(str(e))`) |
| D-C17 | "cards == N" conta depois do dedup | testador | Registrado (§3), sem ação na T9 |
| r1 | Um `http://…` solto no texto da fonte continua virando link clicável (visto no DOM do e2e hostil: `[a](<a href="http://b.c">http://b.c</a>)`). O **texto visível segue literal**. O autolink-literal do GFM age sobre o nó de texto já parseado, e nenhum escape de barra impede. Achado "URL solta vira link — baixo" do testador | testador (baixo) / implementador (confirmado) | **Aberto**, para o orquestrador decidir (P3 ou frente 5). 📝 Sugestão minha (não validada): no card (HTML interpretado), partir o nó de texto com um `<span></span>` vazio depois de `http`/`www`; no Markdown sem HTML, não há saída limpa |
| r2 | `_md_texto` na "Ementa completa" troca quebra de linha por espaço. O Markdown já juntava quebra simples; só a quebra dupla (parágrafo) deixa de separar | implementador | Registrado aqui; o texto não muda, só o layout |

## 5. Regras respeitadas

- Texto normativo nunca parafraseado: o texto da fonte aparece literal no card, no expander e no relatório, provado por teste (markdown-it) e por e2e.
- Nenhum LLM de verdade (app e runner com `GEMINI_API_KEY`/`GOOGLE_API_KEY` vazias); nenhum teste novo faz rede (o AppTest roda sem busca).
- Sem `secrets.toml`; `deploy` e `execucao/*` intocados; sem push.
- CRLF preservado em todo arquivo editado; UTF-8 explícito.

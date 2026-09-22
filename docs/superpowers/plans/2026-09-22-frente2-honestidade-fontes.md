# Frente 2 — Honestidade das fontes — Implementation Plan (v4, pós 3 rodadas adversariais)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer o app dizer a verdade quando uma fonte não pôde ser consultada e de onde veio cada nota de relevância — na tela e na planilha — sem mudar como ele deduplica.

**Architecture:** Uma exceção tipada (`FonteIndisponivel`, com `motivo` e `detalhe`) nasce nos searchers e sobe até `KeywordStatus`, que ganha os mesmos campos mais `parcial`. A nota de relevância ganha um campo irmão `relevancia_origem`. A planilha ganha uma coluna e uma aba; a tela, rótulos honestos. Cada mudança é provada por teste sem rede (fixtures reais capturadas em 22/09, dublês de `requests.get`) e pelo golden-master, que passa a cobrir as duas abas.

**Tech Stack:** Python 3.13.7 · Streamlit 1.55 · requests 2.32 · openpyxl 3.1.5 · pytest 9 · ddgs 9.12 · Playwright (Python, `channel="chrome"`) só para o gate visual.

**Spec:** `docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md` (§3.x). **Esta v2 emenda a spec em 4 pontos**, listados na triagem abaixo e marcados `⚠ emenda à spec` no corpo.

---

## Rodada 1 adversarial — triagem (2026-09-22)

5 lentes independentes (regressão · dados/API · risco · arquitetura · testes), **55 achados brutos, todos os 5 vereditos "não executável como está"**, a maioria provada aplicando a v1 do plano num clone e rodando os testes do próprio plano. **Esta v2 dobra as emendas aceitas no corpo** (não há seção separada de emendas a consultar). O registro abaixo é a trilha de auditoria: o que entrou, o que foi adaptado e o que foi rejeitado, com a razão.

### Bloqueadores convergentes (≥2 lentes, provados por execução) — todos ACEITOS

| # | Achado | Lentes | O que muda no plano |
|---|---|---|---|
| B1 | `_try_fetch` mantinha os `except ... return None`: timeout/conexão/5xx do LexML viravam `endpoint_inexistente`; o teste do próprio plano falhava | 1, 3, 4, 5 | T2: `_try_fetch` reescrito inteiro; só 404 devolve `None`; o resto **levanta** com o motivo certo. `_fetch_sru` só mata URL em 404 / bloqueio / ilegível — timeout e 5xx sobem sem matar o URL |
| B2 | Cache de falha + laço de retry **sobrescreviam `bloqueio_waf` por `endpoint_inexistente`** no cenário real de 22/09 (primário WAF, fallbacks 404) — o fato central da frente nunca chegava à tela | 2, 3, 4 | T2: cache guarda a **causa** por URL; esgotada a cadeia, relevanta a causa mais específica com detalhe agregado; retry **pula** cadeia morta (sem sleep) e nunca rebaixa motivo. Teste V2 vira o cenário misto |
| B3 | `test_comprehensive.py` perde 2 testes (LexML parse malformado; TCU mock de `_fetch_all_pages`) já na T2; o plano dizia "98 intactos" | 1, 3, 5 | T2 e T3 ganham step de **adaptação nomeada** das duas asserções, no mesmo commit; `test_comprehensive` entra nas listas de "rodar" |
| B4 | Step 5g deixava `error_msg` na linha 196 → `NameError` no retry; 6 de 7 testes crashavam | 2 | T2: o laço de retry é colado **inteiro**, literal |
| B5 | Fixture do TCU usava `numeroAcordao`/`anoAcordao`, chaves que `_map_acordao` não lê → 20 itens colapsam em 1. **E a lente 2 mediu por `curl` que o esquema REAL da API é esse** — não há `ementa`/`numero`/`ano`: **todo acórdão real colapsa e nunca casa palavra-chave** | 1, 2, 3, 4, 5 | ✅ confirmado por mim em 22/09 (`tests/fixtures/tcu_acordaos_real.json`). **T4 nova: mapear o esquema real** (`⚠ emenda à spec §3.7`). O teste de paginação usa a fixture real |
| B6 | openpyxl devolve `None` para célula `""` no round-trip; teste da aba falhava | 1, 2, 4, 5 | T8: célula vazia grava `"—"` de propósito (leitor sabe que o campo foi considerado); teste espera `"—"` |

### Altos — ACEITOS

| # | Achado | Lente | O que muda |
|---|---|---|---|
| H1 | Ramo `if self._sru_url` de `_fetch_sru` devolvia `None` num 404 tardio → `TypeError` → `erro_interno` com traceback no detalhe | 5 | T2: `None` no URL cacheado invalida o cache e cai na cadeia; teste `200 → 404` |
| H2 | `app.py` engole exceção do `search()` e a fonte **some** do relatório e da aba — a mentira que a frente quer matar | 3 | T1: `statuses_para_falha_total()` em `models.py` (testável sem Streamlit); T9 usa no `except`; T3 envolve o mapeamento de item |
| H3 | Aviso "nenhuma catalogada respondeu" disparava com acórdãos do TCU na tela (T3 marca `error` com `result_count>0`); o gate V11 **premiava** o bug | 3, 5 | T9: critério = soma de `result_count` das catalogadas; frase distinta para "respondeu parcialmente"; V11 checa a frase certa ao cenário |
| H4 | `error_message` do Google CSE carrega a URL com `key=`/`cx=` → chave na tela e, com a aba nova, na planilha | 3 | T1: `redigir()` em `models.py`, aplicada no `__post_init__` de `KeywordStatus` (segredos, chars de controle, prefixo `=` de fórmula, 300 chars) |
| H5 | `parcial` só existia no TCU; LexML com falha na página ≥2 seguia `ok` sem declarar | 3 | T2: `_search_keyword` registra o erro de paginação; `search()` grava `parcial=True` + detalhe; teste de 2 páginas |
| H6 | 4xx do TCU retentado 3× e rotulado `http_5xx`; 200 HTML → `JSONDecodeError` → `http_5xx`; 503 com causa afirmada como fato | 2, 3, 4 | T3: classificação por status (404 → `endpoint_inexistente`, 429 → `rate_limit`, outro 4xx → `http_4xx`, sem retry); JSON ilegível → sniff HTML → `bloqueio_waf`/`resposta_ilegivel`; 503 com hora e hipótese marcada (`⚠ emenda à spec §3.1`: `rate_limit`, `http_4xx`) |

### Médios/baixos — ACEITOS ou ADAPTADOS

| # | Achado | Verdict | O que muda |
|---|---|---|---|
| M1 | Retry-depois-sucesso sem teste; TCU timeout/conexão sem teste | aceito | T2/T3: testes acrescentados |
| M2 | `MOTIVOS` validado só no `KeywordStatus`: typo num searcher derruba a fonte inteira; `e.detalhe = ...` não atualiza `str(e)` | adaptado | T1: `FonteIndisponivel.__init__` mapeia motivo desconhecido → `erro_interno` (com o original no detalhe) em vez de levantar; `__str__` dinâmico; `KeywordStatus` continua validando (cinto) |
| M3 | `__init__` do LexML **já existe** em `:76-77`; a v1 tinha dois textos concorrentes | aceito | T2: "acrescentar 2 linhas mantendo o comentário" |
| M4 | Palavras-chave nunca consultadas (cap de `max_results`, `MAX_GOOGLE_KEYWORDS=5`) não geram status → lidas como "não existe" | adaptado | `⚠ emenda à spec §3.1`: motivo `nao_consultada` com `status="error"`; T2/T3/T5 gravam para cada keyword pulada |
| M5 | `google_searcher.py` fora do vocabulário: `DDGSException('No results')` vira `error`; nada tem `motivo` | adaptado | `⚠ emenda à spec §5`: **T5 nova, mínima** — mapear ddgs/CSE para `empty`/`timeout`/`rate_limit`/`http_4xx`/`erro_interno`; 4 testes com dublê |
| M6 | Aba de diagnóstico sem data/hora; detalhe sem query string | aceito | T8: `generate_excel(..., quando: str \| None)`; T2/T3: detalhe usa `response.url` (já redigido) |
| M7 | Golden-master lia só a aba ativa: a aba nova ficava sem proteção | aceito | T8: `_sha_planilha` hasheia **todas** as abas; `diagnostico_fixo.json` (3 statuses) ao lado de `entrada_fixa.json`; recongelar no mesmo commit |
| M8 | `_merge` com origem nunca é exercitado pelo app (dedup roda antes da pontuação); origem atribuída depois não passa pelo `__post_init__` | adaptado | T7 fica como **invariante declarado** na docstring; T9 valida a origem no ponto de atribuição. Inverter a ordem dedup/pontuação **rejeitado**: muda o dedup, exige task própria com golden |
| M9 | Docstring de módulo de `gemini_client.py:11` fica falsa; o gate de auditoria só vê linhas removidas | aceito | T6 edita a linha; gate de cada task ganha `git grep` dos símbolos renomeados |
| M10 | Sniff SRU estrito demais (BOM U+FEFF; prefixo `zs:`) — declararia "indisponível" um LexML que voltasse noutro formato | aceito | T2: sniff permissivo — só HTML explícito é bloqueio/ilegível; o resto o `ET` decide. `LESSONS`: falta captura real de SRU |
| M11 | `_urls_mortos` por instância nunca limpo; comentário prometia "nesta busca" | aceito | T2: `clear()` no início de `search()`; teste de reuso |
| M12 | T6 (agora T8) Step 2 previa "7 failed"; só 1 falha (os outros iteram `range(1, 11)` e passam por omissão) | aceito | corrigido |
| M13 | PNG do V11 em `tests/golden/`; docstring de `golden_master.py` cita assinatura velha; dicts de rótulo sem teste de sincronia; `RespostaFake.headers` dict simples; `detalhe` renderizado via Markdown | aceito | `tests/evidencia/` + `.gitignore`; T8 atualiza a docstring; asserts `set(ORIGEM_LABEL) == ORIGENS_RELEVANCIA` etc.; `CaseInsensitiveDict` no dublê; `st.code` para o detalhe |
| M14 | Sem LLM, ementa vazia → 0% onde antes 50%; ordem dos cards muda | aceito | T9: linha explicando "0% = nenhuma palavra-chave na ementa"; V11 confere que nenhum card sumiu |
| M15 | `diagnostico=[]` não testado separado de `None` | aceito | T8 |

### Rejeitados — com a razão

| Achado | Por quê |
|---|---|
| Pontuar antes de deduplicar para `_merge` valer de verdade (lente 5, opção b) | Muda o dedup e o golden; é task própria, fora desta frente. A origem está protegida pela atribuição pós-dedup (M8). |
| Retentar 503 uma vez (lente 3) | 503 é manutenção declarada; retentar só atrasa. Fica sem retry, com hora no detalhe. |
| Novo motivo `acesso_negado` para 401/403 (lente 3) | Coberto por `http_4xx` + detalhe com o status; vocabulário menor envelhece melhor. |
| Sanitizar `ementa`/`nome` na aba `Normativos` contra fórmula (lente 3) | Pré-existente, fora do escopo desta frente; registrado em `_TODO.md` P3. |

✅ **Verificado pela lente 4 e registrado para o executor não gastar tempo:** `python -m pytest tests/...` de dentro de `levantamento-normativos/` importa `searchers` sem `conftest`/`__init__` (cwd entra no `sys.path` via `-m`); `monkeypatch.setattr("searchers.lexml_searcher.requests.get")` patcha o módulo `requests` compartilhado (vale para TCU e Google); `"time.sleep"` global cobre o `import time` local de `_try_fetch`; `app.py:23` importa `gemini_client` como módulo; `searchers.base` não importa `models` (sem ciclo — `FonteIndisponivel` fica sem validar contra `MOTIVOS` por import; ver T1); searchers são instanciados por busca (`app.py:490-494`).

---

## Rodada 2 adversarial — triagem (2026-09-22)

5 revisores frescos, **68 achados brutos**, todos os 5 vereditos "não executável numa sessão nova". Método
das lentes: T1–T5 (e T8) aplicadas literalmente em worktree descartável e os testes do próprio plano
executados. **O que a rodada 2 confirmou SÓLIDO por execução:** B1, B4, B5 (mapeamento real; ids
distintos; testes antigos passam pelo fallback), B6, H1, H2, H6, M1, M2, M3, M7 (golden nas 2 abas
estável 2×; dedup intacto), M10, M11, M15; T1 fecha em 56. **Esta v3 dobra as correções abaixo no corpo.**

### Bloqueadores convergentes (≥3 lentes, provados por execução) — ACEITOS

| # | Achado | O que muda |
|---|---|---|
| R2-B1 | **Cruzamento H4×B2:** `redigir(limite=300)` corta o `detalhe` (URL real do LexML tem ~230 chars; detalhe bruto 579) — o título do desafio e a cadeia agregada **nunca chegam** à tela/planilha; e o resumo da cadeia emite nomes de motivo, nunca `404` | T1: `redigir` **não corta** (limite 2000, só como teto de célula); detalhe ordenado **fato primeiro, URL por último**; T2: resumo da cadeia com o status HTTP; dublê com URL longa real (`url + '?' + urlencode(params)`); asserts sobre `KeywordStatus.detalhe` |
| R2-B2 | `test_comprehensive.py:382` (`test_lexml_cql_injection_sanitization`) desempacota 2 valores de `_search_keyword_safe` — B3 tinha 3 call sites, não 2 | T2 Step 11 ganha a 3ª adaptação; regra: `git grep` de todo símbolo cuja assinatura muda, **antes** de fechar a task |
| R2-B3 | `test_lexml_timeout...` afirma o estado pré-retry: o retry re-consulta 'a', recebe SRU e zera o motivo (comportamento **correto**) | teste reescrito: Timeout nas chamadas 1 **e** 3 → `retried=True, motivo="timeout"`; caso "recuperado" fica em teste próprio |
| R2-B4 | LexML parcial prefixa só `startRecord=N:` (TCU prefixa o motivo) → a página bloqueada vira "OK · — · startRecord=21: GET …" | `f"startRecord={n}: {e.motivo}: {e.detalhe}"`; `motivo` continua `""` em ok/empty (vocabulário intocado); o detalhe carrega o motivo |
| R2-B5 | `"não informado" in "data/hora não informada"` → False | título e assert unificados em **"não informada"** |
| R2-B6 | `nao_consultada` com `status="error"` vira "N indisponíveis", abre o expander em vermelho e grava "Indisponível" na planilha **no caminho feliz** (10 keywords + `max_results` atingido) | `rotulo_status(s)` em `models.py` é o rótulo da **planilha** ("Não consultada"); a **tela** agrupa por motivo com títulos de seção próprios (R3: não importa `rotulo_status`); só abre por indisponível ou parcial; `diagnostico_fixo.json` ganha um `nao_consultada`; V11 ganha o cenário de sucesso |

### Altos — ACEITOS

| # | Achado | O que muda |
|---|---|---|
| R2-H1 | `redigir` só no `__post_init__`; os retries **mutam** `error_message`/`detalhe` depois (Google `:368`, LexML retry) → chave do CSE vaza pela porta dos fundos | `KeywordStatus.__setattr__` redige `detalhe`/`error_message` em **toda** atribuição; teste de mutação pós-construção |
| R2-H2 | Retry pulado (cadeia morta) marcava `retried=True` sem requisição → "Retentado: Sim" falso na planilha; keywords 2-4 herdavam a URL com a **query da keyword 1** | ramo de cadeia morta **não** marca `retried` (LexML **e** Google — R3); detalhe ganha `retry pulado: …`; causa cacheada diz `causa cacheada da palavra-chave "X" (esta palavra-chave não foi enviada)` e a URL cacheada perde a query |
| R2-H3 | Google: **dois** call sites de `_search_urls` (`:261` e `:363`) + `:368`; `nao_consultada` só funciona **depois** do laço de retry; CSE 200 não-JSON → `AttributeError` dentro do handler | T5 com blocos literais para os 2 laços, posição pinada, `JSONDecodeError` tratado; 5º teste (retry que dá certo) |
| R2-H4 | T3 3d colava `_texto_do_acordao` **dentro** de `search()` (o rabo original — callback final e `return` — caía dentro do método novo → `search()` devolve `None`); T2 Step 8 tinha `# inalterado` como placeholder | `_texto_do_acordao` vira step próprio; Step 8 colado inteiro |
| R2-H5 | ✅ medido ao vivo: `sumario` é **nulo em 20/20** acórdãos recentes (sessão 16/09) e em ~40% da janela de 500 — "acórdãos voltaram a casar" é fato parcial | detalhe do TCU conta `N sem texto`; T10 registra como fato medido, não como vitória |

### Médios/baixos — ACEITOS ou ADAPTADOS

| # | Verdict | O que muda |
|---|---|---|
| contagens (T3 tem **9** testes; totais recomputados) | aceito | tabela e steps corrigidos |
| T4: teste H2 vivia em dois lugares (T3 com `dataSessao=int`, nota da T4) | aceito | escrito **uma vez**, já com `sumario=123`/`TypeError`, `xfail` na T3 |
| T6/T8/T9 delegavam código à v1 (`git show b1a6d3c`) | adaptado | os blocos críticos são colados aqui; o que ficou delegado tem **faixa de linhas** pinada |
| `parcial` semântica: pode acompanhar `empty` (e `error` no TCU com um endpoint vivo) | aceito | spec §3.1 emendada; TCU: `parcial = … or (erro_primario and itens)`; H3 distingue fonte **morta** de **parcial** por fonte |
| `datetime.now()` naive; janela 20h-21h comparada em UTC num servidor | aceito | `datetime.now(ZoneInfo("America/Sao_Paulo"))` |
| `_RE_SEGREDO` não pega `access_token`/`secret`/`Bearer` | aceito | regex ampliado; `redigir` aplicada também no `__init__` de `FonteIndisponivel` (o log sai redigido) |
| `redigir` prefixava `'` em `+ - @` (openpyxl só trata `=` como fórmula) | aceito | só `=` |
| runner não garante "sem LLM": `test_comprehensive` achou `GEMINI_API_KEY` no ambiente (429 do Gemini no log) | aceito | `run_all_tests.py` passa `env` com `GEMINI_API_KEY=""` |
| `statuses_para_falha_total` descartava statuses já coletados; slug default `"google"` para fonte desconhecida | aceito | `SOURCE_ID` em `BaseSearcher`; o `except` coleta `searcher.keyword_statuses` antes |
| retry que dá certo apaga o motivo anterior | adaptado | detalhe = `recuperado no retry após {motivo}` (rastreável sem campo novo) |
| faixas de linha do LexML/app desatualizadas; Step 10 ia até `:212` (o retry acaba em `:215`); logs removidos sem aviso | aceito | corrigidas; perdas deliberadas listadas |
| V11 `'0 erros' not in texto` é gate vazio (a string deixa de existir por construção) | aceito | asserts: `≥1 indisponíveis` **e** `bloqueio_waf` no texto; cards == N do cabeçalho vira assert |
| golden: fixture sem `nao_consultada`/`retried`/`detalhe=''` | aceito | `diagnostico_fixo.json` com 5 linhas |

### Rejeitados
| Achado | Por quê |
|---|---|
| `motivo` preenchido em linha `ok`/`empty` parcial (R2-B4, opção 2) | mudaria o significado de `motivo` ("" = não é error) que a spec §3.1 fixa; o detalhe já carrega o motivo |
| campo `retentativas: int` / enum de retry | escopo; o booleano honesto + detalhe basta |
| mover `redigir` para módulo próprio | `models.py` não importa `searchers`; `base.py` importar `models` só para `redigir` não cria ciclo |

---

## Rodada 3 adversarial — triagem (2026-09-22)

5 revisores frescos, **59 achados**, T1–T9 aplicadas literalmente em worktree; um deles rodou o app patchado e o
gate V11 ao vivo. **Confirmado SÓLIDO por execução:** T1 (58), T2 (15 + `test_comprehensive` 98/98 + `test_searchers`
13/13 ao vivo), T3 (23 + 1 xfail), T6 (63), T7 (61), T8 (71; golden diverge só na planilha, recongela, estável 2×,
dedup intacto), T9 (AppTest em 4 cenários; V11 verde ao vivo); R2-B1..B4, R2-H1, R2-H2 (LexML) sólidas; `__setattr__`
não quebra `replace`/`copy`/`pickle`/`==`; `from models import redigir` sem ciclo. **Esta v4 dobra o resto no corpo.**

### Bloqueadores convergentes (5 lentes) — ACEITOS

| # | Achado | O que muda |
|---|---|---|
| R3-B1 | **Cruzamento R2-H5 × H2:** `sem_texto` roda **fora** do `try` por keyword e chama `_texto_do_acordao`, que depois da T4 não é total → o próprio teste H2 (`sumario=123`) derruba `search()` do TCU inteiro. E o contador media a coisa errada: `titulo` está sempre preenchido, então "N sem texto" era **sempre 0** — no cenário exato (sumário nulo em 20/20) que a R2-H5 mandou expor | T3: contador defensivo `_sem_sumario(item)` (try/except) que olha o **campo** `sumario`/`ementa`, rotulado "N sem sumário (nesses só o título casa)"; `_texto_do_acordao` continua não-total de propósito (é o que o teste H2 exercita **dentro** do try); teste novo com `sumario=None` |
| R3-B2 | T5 anota `Optional[...]` sem `from typing import Optional`; `google_searcher.py` não tem `from __future__ import annotations` → `NameError` na importação → **o app inteiro não sobe** | T5: import acrescentado à lista |
| R3-B3 | Contagens erradas por 1 a partir da T4 (o teste do 500 contado duas vezes) | recomputadas de novo, agora com os testes novos desta rodada |

### Altos — ACEITOS

| # | Achado | O que muda |
|---|---|---|
| R3-H1 | R2-H2 só foi aplicada ao LexML: o ramo de retry **pulado** do Google (`:354-361`) segue marcando `retried=True` sem requisição | T5: ramo colado e corrigido; teste |
| R3-H2 | M4 incompleta no Google: `break` por `max_results` dentro das 5 ativas não gera status | T5: `nao_consultada` antes do `break`; teste |
| R3-H3 | Cruzamento B3 × H5: XML **ilegível** na página ≥2 do LexML levanta fora do `try` → keyword vira `error` e a página 1 é **descartada** (regressão vs HEAD) | T2 Step 8: `_parse_sru_response` dentro do `try`; teste |
| R3-H4 | H3 ainda mente no cenário real: TCU com acórdãos 200 (0 match) + atos 500 cai em `mortas` — "tcu indisponível" enquanto metade foi pesquisada | T9: fonte é `morta` só se nenhum status dela é `parcial`; frase "respondeu parcialmente (0 resultado(s); …)"; V11 afirma |
| R3-H5 | TCU com os dois endpoints ok e todos sem sumário → `empty` sem detalhe: "consultei e não há" quando 500 chegaram sem texto | T3: `detalhe` **sempre** gravado; T9: seção "sem resultado" mostra o detalhe quando houver |
| R3-H6 | T5 3e ainda tinha um placeholder (`...` no ramo de sucesso) — `...` é Python válido e vira no-op | T5: laço de retry do Google colado **inteiro** |

### Médios/baixos — ACEITOS ou ADAPTADOS

| Achado | Verdict | O que muda |
|---|---|---|
| gate de `git grep` com `\b` não casa `score_relevance_com_origem`; faltam `_search_urls`, `_render_search_diagnostics`, `generate_excel`, `tools/` | aceito | Global Constraints |
| `redigir` corta o **sufixo** sem marca — os appends `| retry pulado…` somem num detalhe de 1990 chars | aceito | corte no meio com marcador `[…cortado…]`; teste |
| T4 muda precedência de data (`dataSessao` antes de `dataAta`) e troca `""` por `None` (muda o `id`) sem declarar | adaptado | declarado; mantém `""` (ids preservados); assert de `data`/`id` no teste antigo |
| `indisponiveis` e `parciais` não são disjuntos (TCU error+parcial renderiza 2×) | aceito | `parciais` exclui `error`; badge `(parcial)` na seção de indisponíveis |
| `rotulo_status` importado e não usado no app; R2-B6 prometia "planilha e tela" | adaptado | R2-B6 corrigida: a planilha usa `rotulo_status`; a tela agrupa por motivo; import removido |
| T3 âncora `:73` (é `:72`); `_request_with_retry` vai até `:253` | aceito | corrigido; regra: âncora pelo **texto**, número é dica |
| timeout/conexão do TCU e do LexML gravam URL sem query | aceito | `f"{url}?{urlencode(params)}"` |
| `quando` do app naive; hora do 503 em BRT não bate | aceito | `datetime.now(ZoneInfo("America/Sao_Paulo"))` no app |
| `ZoneInfo` no Windows depende de `tzdata` (vem por acidente via pandas) | aceito | `tzdata` no `requirements.txt` (T3) |
| T8 Step 2 esperava "1 + 10 failed"; é `ImportError` na coleta | aceito | corrigido |
| `statuses_para_falha_total` com lista vazia grava `(todas)` mesmo com tudo coberto | aceito | T9: só chama se sobrou keyword |
| `assert` como validação de origem some com `-O`; `ORIGEM_CURTA[...]` é lookup duro | aceito | validação real + `.get` |
| avisos antes do `st.header`; frase "(LexML, TCU)" e "web aberta" hardcoded | aceito | bloco depois do header; nomes vindos de `por_fonte`; "web aberta" só se houver status `google` |
| `ConnectTimeout` herda de `ConnectionError` e `Timeout`; a ordem dos `except` rotula `conexao` | aceito | `Timeout` antes |
| ramo não-cacheado de `_causa_da_cadeia_morta` deixa a URL no meio | aceito | `partition(" | GET ")`, URL por último |
| hash do golden passa a depender de `redigir`/`rotulo_status`/`ORIGEM_LABEL`/`VAZIO`/título | aceito | dito na docstring e no commit da T8 |
| `retried` tem 3 semânticas por fonte | aceito | docstring de `KeywordStatus.retried` fixa: "reenviada à fonte depois do passe principal; tentativas HTTP internas ficam no detalhe" |
| `secrets.toml` vence a variável vazia do runner | aceito (nota) | comentário no runner + `LESSONS`; código na frente 5 |
| `keyword`/`source` crus na aba nova (fórmula) | aceito | `redigir(s.keyword)` ao escrever |
| CSE não coberto por teste (R2-H3 provada só por leitura) | aceito | T5: teste com `_BACKEND="cse"` e 200 não-JSON |
| texto da triagem R2-H2 ≠ código | aceito | alinhado ao código |
| detalhe do TCU idêntico por keyword impresso N vezes | adiado | `_TODO.md` P3 (agrupar por fonte na tela) |

---

## Global Constraints

- **Texto normativo NUNCA é parafraseado.** `nome`/`ementa` só recebem campos literais da API (T4 troca *qual* campo, não o texto).
- **O sistema roda inteiro sem LLM.** Todo teste novo roda com `GEMINI_API_KEY` vazia; nenhum teste novo faz rede.
- **Rastreabilidade:** `motivo` e `detalhe` bastam para reproduzir com `curl` (URL efetiva com query, status, content-type, hora quando relevante) — **com segredos redigidos**.
- **Separar fato de sugestão:** `📝` no que for proposta não validada.
- **UTF-8 explícito em todo `open()` / `read_text` / `write_text`.** `PYTHONIOENCODING=utf-8` em comando que imprime acento.
- **Rodar Python via Bash, não PowerShell.** Acima de 260 caracteres o Python falha em silêncio no Windows.
- **Documentação move junto com o código.** Gate ao fim de **cada** task, os dois comandos, lidos inteiros: `git diff -U0 HEAD~1 -- '*.py' | grep '^-' | grep -v '^---'` e `git grep -n -E 'score_relevance|_fetch_all_pages|_search_keyword_safe|_request_with_retry|_parse_sru_response|_search_urls|_render_search_diagnostics|generate_excel|_texto_do_acordao|_map_acordao|rotulo_status' -- '*.py'` (**sem ``** — ele não casa `score_relevance_com_origem`; inclui `tools/` porque `golden_master.py` documenta `generate_excel`; todo call site e docstring de símbolo cuja assinatura mudou, **antes** de escrever o step de adaptação; R2-B2, R3).
- **Golden-master:** `python tools/golden_master.py comparar` → OK ao fim de **toda** task, exceto a T8, que recongela **no mesmo commit** e diz por quê. `dedup_esperado.json` **nunca** muda nesta frente.
- **Runner:** `python tools/run_all_tests.py` TUDO VERDE ao fim de toda task (≈9 min hoje; deve cair com o cache de falha da T2 — anotar). Task que acrescenta teste atualiza `BASELINE` **no mesmo commit**. ⚠ **Os números "Expected" abaixo são previsões**: se o observado divergir, **parar e reconciliar** (um teste a mais/menos é sinal de step aplicado errado), nunca "ajustar o BASELINE ao que deu".
- **Sem LLM de verdade:** `tools/run_all_tests.py` roda as suítes com `env={**os.environ, "GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}` (T1 Step 6); a suíte nova tem `monkeypatch.delenv` autouse. ⚠ `st.secrets` **vence** a variável: se existir `levantamento-normativos/.streamlit/secrets.toml` (hoje só há o `.example`), o runner acha que roda sem LLM e não roda — dito no comentário do runner e no `LESSONS`; o conserto de código é da frente 5.
- **Push a cada task fechada** (D-C7).
- **Vocabulário fechado** em `models.py`: `MOTIVOS` e `ORIGENS_RELEVANCIA`. Nenhum outro arquivo inventa valor.
- **Diretório:** raiz do repo para `tools/`; `levantamento-normativos/` para `pytest` e os scripts de teste. Cada step diz qual.
- **Âncoras:** onde um step diz "de `:N` até `:M`", o **texto** citado é a âncora e o número é dica (linhas mudam); substituir sempre do começo da linha que contém o texto-âncora inicial até o fim da linha do texto-âncora final, **inclusive**.

---

## Estrutura de arquivos

| Arquivo | Responsabilidade nesta frente |
|---|---|
| `levantamento-normativos/models.py` | `MOTIVOS`, `ORIGENS_RELEVANCIA`, `redigir()`, `statuses_para_falha_total()`; campos novos em `KeywordStatus` e `NormativoResult` |
| `levantamento-normativos/searchers/base.py` | `FonteIndisponivel` |
| `levantamento-normativos/searchers/lexml_searcher.py` | sniff permissivo; `_try_fetch` levanta; cache de causa por URL; parcial; `nao_consultada`; retry que não rebaixa motivo |
| `levantamento-normativos/searchers/tcu_searcher.py` | `_request_with_retry` classifica por status e levanta; `_fetch_all_pages` → `(itens, erro, parcial)`; classificação por endpoint; **mapeamento do esquema real do acórdão** |
| `levantamento-normativos/searchers/google_searcher.py` | mapeamento mínimo ddgs/CSE → motivo; `nao_consultada` para keywords além de 5 |
| `levantamento-normativos/llm/gemini_client.py` · `llm/__init__.py` | `score_relevance_com_origem`; wrapper; docstrings |
| `levantamento-normativos/deduplicator.py` | `_merge` leva `relevancia_origem` (invariante) |
| `levantamento-normativos/excel_export.py` | coluna "Origem da nota"; aba "Diagnostico da busca"; `diagnostico=`, `quando=` |
| `levantamento-normativos/app.py` | pontuação sempre; relatório; avisos; card; preview; `statuses_para_falha_total`; `diagnostico=`/`quando=` |
| `levantamento-normativos/tests/test_fontes_indisponiveis.py` | **novo** — pytest, sem rede |
| `levantamento-normativos/tests/fixtures/lexml_desafio_senado.html` | ✅ capturado 22/09 (9.049 bytes, HTML real do desafio) |
| `levantamento-normativos/tests/fixtures/tcu_acordaos_real.json` | ✅ capturado 22/09 (2 acórdãos reais; chaves `numeroAcordao`, `anoAcordao`, `sumario`, `titulo`, `dataSessao`, `urlAcordao`…) |
| `levantamento-normativos/tests/fixtures/lexml_sru_valido.xml` | **novo** — SRU mínimo, 📝 escrito à mão (não há captura real: a fonte está bloqueada) |
| `levantamento-normativos/test_phase4.py` · `test_llm_phase3.py` · `test_comprehensive.py` | asserts adaptados; testes novos |
| `tools/run_all_tests.py` | suíte nova em `SUITES_PYTEST`; `BASELINE` por task |
| `tools/golden_master.py` | hash de **todas** as abas; `diagnostico_fixo.json` |
| `tests/golden/diagnostico_fixo.json` · `planilha_sha256.txt` · `ambiente.txt` | novo · recongelados na T8 |
| `tools/dirigir_app.py` · `tests/evidencia/` | gate visual V11 (PNG **não** versionado) |

**BASELINE previsto por task** (o runner avisa `cresceu`; o commit da task o atualiza):

| Após | `test_searchers` | `test_llm_phase3` | `test_comprehensive` | `test_phase4` | `tests/test_fontes_indisponiveis.py` | total |
|---|---|---|---|---|---|---|
| T1 | 13 | 53 | 98 | **58** | — | 222 |
| T2 | 13 | 53 | 98 | 58 | **16** | 238 |
| T3 | 13 | 53 | 98 | 58 | **25** (26 coletados, 1 xfail) | 247 |
| T4 | 13 | 53 | 98 | 58 | **29** | 251 |
| T5 | 13 | 53 | 98 | 58 | **37** | 259 |
| T6 | 13 | **63** | 98 | 58 | 37 | 269 |
| T7 | 13 | 63 | 98 | **61** | 37 | 272 |
| T8 | 13 | 63 | 98 | **71** | 37 | 282 |
| T9 | 13 | 63 | 98 | 71 | 37 | 282 |

⚠ Contagens **recomputadas na v4** (a v3 contou um teste duas vezes na T4). **O observado manda**; se divergir, `grep -c '^def test_'` no bloco da task **antes** de suspeitar do código — e a regra "parar e reconciliar" vale para a diferença entre o bloco e o observado, não entre a tabela e o observado.

---

### Task 1: Vocabulário, `redigir()`, `statuses_para_falha_total()`, `FonteIndisponivel`

**Files:**
- Modify: `levantamento-normativos/models.py` (topo; `NormativoResult:59-63` e `__post_init__:65-76`; `KeywordStatus:95-100`)
- Modify: `levantamento-normativos/searchers/base.py` (fim do arquivo)
- Test: `levantamento-normativos/test_phase4.py` (classes novas no fim)
- Modify: `tools/run_all_tests.py` (`BASELINE["test_phase4.py"]`)
- Modify: spec §3.1 (emenda dos motivos novos)

**Interfaces — Produces:**
- `MOTIVOS: frozenset[str]` = `{"", "bloqueio_waf", "http_5xx", "http_4xx", "rate_limit", "manutencao_503", "timeout", "conexao", "resposta_ilegivel", "endpoint_inexistente", "nao_consultada", "erro_interno"}`
- `ORIGENS_RELEVANCIA: frozenset[str]` = `{"modelo", "heuristica", "fallback_erro", "padrao_fonte"}`
- `redigir(texto: str, limite: int = 2000) -> str` — redige `key=`/`cx=`/`api_key=`/`apikey=`/`token=`/`access_token=`/`secret=`/`client_secret=`/`password=` (valor → `***`) e `Bearer <x>`, remove chars de controle (exceto `\n`, `\t`), prefixa `'` **só** se começar com `=` (R2), corta em `limite` (2000 = teto de célula; **não** é para caber na tela — R2-B1).
- `rotulo_status(s: KeywordStatus) -> str` — `"OK" | "Sem resultado" | "Indisponível" | "Não consultada"` (o último quando `motivo == "nao_consultada"`); usado pela planilha e pela tela (R2-B6).
- `KeywordStatus(..., motivo: str = "", detalhe: str = "", parcial: bool = False)`; `__post_init__`: `ValueError` se `motivo ∉ MOTIVOS`; **`__setattr__` aplica `redigir` a `detalhe` e `error_message` em toda atribuição** — construtor e mutações posteriores (R2-H1).
- `NormativoResult(..., relevancia_origem: str = "padrao_fonte")`; `__post_init__`: `ValueError` se fora de `ORIGENS_RELEVANCIA`.
- `statuses_para_falha_total(source: str, keywords: list[str], exc: BaseException) -> list[KeywordStatus]` — um `error`/`erro_interno` por keyword.
- `searchers.base.FonteIndisponivel(motivo, detalhe="")` — motivo desconhecido vira `erro_interno`; `detalhe` passa por `redigir` já aqui (o log sai redigido); `str(e)` lê `self.motivo`/`self.detalhe` dinamicamente.
- `searchers.base.BaseSearcher.SOURCE_ID: str` — `"lexml" | "tcu" | "google"`, definido em cada subclasse (T2/T3/T5); é o `source` de todo `KeywordStatus` e o que `app.py` usa no `except`.

- [ ] **Step 1: Testes que falham** — ao fim de `levantamento-normativos/test_phase4.py`:

```python
# ===========================================================================
#  FRENTE 2 — VOCABULARIO DE HONESTIDADE (spec 2026-09-22 §3.1, plano v2 T1)
# ===========================================================================

from models import (KeywordStatus, MOTIVOS, ORIGENS_RELEVANCIA, redigir,
                    statuses_para_falha_total)


class TestVocabularioHonestidade:
    def test_motivos_fechados(self):
        assert MOTIVOS == frozenset({
            "", "bloqueio_waf", "http_5xx", "http_4xx", "rate_limit", "manutencao_503",
            "timeout", "conexao", "resposta_ilegivel", "endpoint_inexistente",
            "nao_consultada", "erro_interno",
        })

    def test_origens_fechadas(self):
        assert ORIGENS_RELEVANCIA == frozenset({"modelo", "heuristica", "fallback_erro", "padrao_fonte"})

    def test_keyword_status_construtor_antigo_continua_valido(self):
        s = KeywordStatus(keyword="lgpd", source="lexml", result_count=0, status="empty")
        assert (s.motivo, s.detalhe, s.parcial) == ("", "", False)

    def test_keyword_status_aceita_motivo_valido(self):
        s = KeywordStatus(keyword="lgpd", source="lexml", status="error",
                          motivo="bloqueio_waf", detalhe="HTTP 200 text/html")
        assert s.motivo == "bloqueio_waf"

    def test_keyword_status_rejeita_motivo_inventado(self):
        with pytest.raises(ValueError, match="motivo"):
            KeywordStatus(keyword="lgpd", source="lexml", status="error", motivo="waf")

    def test_keyword_status_redige_detalhe_e_error_message(self):
        s = KeywordStatus(keyword="k", source="google", status="error", motivo="http_4xx",
                          detalhe="GET https://g/api?key=AIzaSECRET&cx=abc&q=x -> 403",
                          error_message="500 for url: https://g/x?key=AIzaSECRET")
        assert "AIzaSECRET" not in s.detalhe and "key=***" in s.detalhe
        assert "AIzaSECRET" not in s.error_message

    def test_keyword_status_redige_tambem_na_mutacao_pos_construcao(self):
        """R2-H1: os retries mutam error_message/detalhe depois do construtor."""
        s = KeywordStatus(keyword="k", source="google", status="error", motivo="http_5xx")
        s.error_message = "Retry failed: 500 for url: https://g/x?key=AIzaSECRET"
        s.detalhe = "GET https://g/x?cx=SEGREDO -> 500"
        assert "AIzaSECRET" not in s.error_message and "SEGREDO" not in s.detalhe

    def test_normativo_origem_default_e_padrao_fonte(self):
        assert _make_result().relevancia_origem == "padrao_fonte"

    def test_normativo_rejeita_origem_inventada(self):
        with pytest.raises(ValueError, match="relevancia_origem"):
            NormativoResult(nome="x", tipo="Lei", numero="1", data=None, orgao_emissor="",
                            ementa="", link="", source="lexml", found_by="k",
                            relevancia_origem="ia")


class TestRedigir:
    def test_redige_segredos_em_query_e_bearer(self):
        assert redigir("u?key=ABC&cx=DEF&api_key=GHI&token=JKL&access_token=MNO&client_secret=PQR&q=x") == \
            "u?key=***&cx=***&api_key=***&token=***&access_token=***&client_secret=***&q=x"
        assert redigir("Authorization: Bearer eyJabc.def") == "Authorization: Bearer ***"

    def test_remove_controle_e_corta_no_meio_com_marcador(self):
        assert redigir("a\x00b\x07c\n") == "abc\n"
        assert len(redigir("x" * 1500)) == 1500
        cortado = redigir("A" * 1990 + " | GET https://fonte/x | retry pulado")
        assert len(cortado) <= 2000 and "[…cortado" in cortado          # R3: sufixo (URL, 'retry pulado') sobrevive
        assert cortado.startswith("AAAA") and cortado.endswith("| retry pulado")

    def test_neutraliza_so_formula(self):
        assert redigir('=HYPERLINK("http://evil","clique")').startswith("'=")
        assert redigir("-1") == "-1" and redigir("+1") == "+1" and redigir("@x") == "@x"   # openpyxl so trata '=' como formula

    def test_texto_normal_intacto(self):
        assert redigir("GET https://x/y?q=lgpd -> 200 text/html") == "GET https://x/y?q=lgpd -> 200 text/html"


class TestRotuloStatus:
    def test_rotulos(self):
        from models import rotulo_status
        mk = lambda **k: KeywordStatus(keyword="k", source="lexml", **k)
        assert rotulo_status(mk(status="ok")) == "OK"
        assert rotulo_status(mk(status="empty")) == "Sem resultado"
        assert rotulo_status(mk(status="error", motivo="bloqueio_waf")) == "Indisponível"
        assert rotulo_status(mk(status="error", motivo="nao_consultada")) == "Não consultada"   # R2-B6


class TestStatusesParaFalhaTotal:
    def test_um_status_por_keyword(self):
        sts = statuses_para_falha_total("tcu", ["a", "b"], AttributeError("'int' object has no attribute 'strip'"))
        assert [s.keyword for s in sts] == ["a", "b"]
        assert all((s.source, s.status, s.motivo) == ("tcu", "error", "erro_interno") for s in sts)
        assert "AttributeError" in sts[0].detalhe and "strip" in sts[0].detalhe

    def test_lista_vazia_de_keywords_da_um_status_generico(self):
        sts = statuses_para_falha_total("lexml", [], RuntimeError("x"))
        assert len(sts) == 1 and sts[0].keyword == "(todas)"
```

- [ ] **Step 2: Rodar e ver falhar** — em `levantamento-normativos/`: `python -m pytest test_phase4.py -q` → `ImportError: cannot import name 'MOTIVOS'` na coleta.

- [ ] **Step 3: `models.py`** — logo após `from dataclasses import dataclass, field`, acrescentar `import re` e:

```python
# ---------------------------------------------------------------------------
# Vocabulario fechado de honestidade (spec 2026-09-22 §3.1; plano v2 T1)
# ---------------------------------------------------------------------------

# Por que uma fonte NAO pode ser consultada. String (nao Enum) para caber na
# planilha e no JSON sem conversao. "" = nao se aplica (status ok/empty).
MOTIVOS: frozenset[str] = frozenset({
    "",
    "bloqueio_waf",          # HTTP 200 com pagina de desafio (Senado/LexML, medido em 22/09)
    "http_5xx",              # 5xx depois dos retries
    "http_4xx",              # 4xx que nao e 404 nem 429 (401, 403...) — sem retry
    "rate_limit",            # 429 / RatelimitException — esperar, nao "fonte caiu"
    "manutencao_503",        # 503 (o TCU tem janela diaria 20h-21h BRT; hipotese, ver detalhe)
    "timeout",               # requests.Timeout
    "conexao",               # requests.ConnectionError
    "resposta_ilegivel",     # HTTP 200, mas o corpo nao e o formato esperado
    "endpoint_inexistente",  # 404 em todos os URLs da cadeia
    "nao_consultada",        # a busca parou antes desta palavra-chave (limite de resultados/keywords)
    "erro_interno",          # excecao nao prevista — bug nosso, nao da fonte
})

# De onde veio a nota de relevancia. Tres procedencias colapsavam no mesmo
# numero (0.5 podia ser modelo, fallback de erro ou default da fonte).
ORIGENS_RELEVANCIA: frozenset[str] = frozenset({
    "modelo",         # nota dada pelo LLM
    "heuristica",     # fracao das palavras-chave presentes na ementa (deterministica)
    "fallback_erro",  # o LLM falhou nesse lote; 0.5 rotulado como tal
    "padrao_fonte",   # constante que o searcher atribui; nenhuma avaliacao rodou
})

_RE_SEGREDO = re.compile(r"(?i)(?<![A-Za-z0-9])(key|cx|api[_-]?key|token|access_token|secret|client_secret|password|sig(?:nature)?)=([^&\s]+)")
_RE_BEARER = re.compile(r"(?i)\bBearer\s+\S+")
_RE_CONTROLE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def redigir(texto: str, limite: int = 2000) -> str:
    """Torna um texto vindo de fora seguro para tela, log e planilha.

    Redige segredos em query string e Bearer (a mensagem do requests inclui a
    URL inteira: `?key=AIza...` ia para a aba de diagnostico), remove chars de
    controle (openpyxl levanta IllegalCharacterError), neutraliza formula
    (so '=': e o unico prefixo que o openpyxl trata como formula) e corta em
    `limite`. O limite e o TETO DE CELULA (2000), nao um tamanho de tela:
    com 300, a URL real do LexML (~230 chars) engolia o titulo do desafio e a
    cadeia de URLs — o fato central da frente nunca chegava a planilha
    (rodada 2, R2-B1). Quem precisa de texto curto corta na renderizacao.
    """
    texto = _RE_SEGREDO.sub(lambda m: f"{m.group(1)}=***", texto or "")
    texto = _RE_BEARER.sub("Bearer ***", texto)
    texto = _RE_CONTROLE.sub("", texto)
    if texto[:1] == "=":
        texto = "'" + texto
    if len(texto) > limite:
        # corta no MEIO, com marca: o comeco (fato) e o fim (URL, 'retry pulado')
        # sao o que importa; cortar o sufixo em silencio apagava exatamente os
        # appends que a T2/T5 fazem no detalhe (rodada 3)
        marca = f" […cortado {len(texto) - limite} chars…] "
        metade = (limite - len(marca)) // 2
        texto = texto[:metade] + marca + texto[-metade:]
    return texto


def rotulo_status(s: "KeywordStatus") -> str:
    """Rotulo humano de um KeywordStatus — UNICO lugar (planilha e tela usam).

    `nao_consultada` tem status="error" (vocabulario fechado), mas NAO e
    "indisponivel": a palavra-chave simplesmente nao foi enviada. Rotula-la de
    indisponivel fazia o caminho feliz (10 keywords, max_results atingido)
    parecer uma fonte caida (rodada 2, R2-B6).
    """
    if s.status == "error" and s.motivo == "nao_consultada":
        return "Não consultada"
    return {"ok": "OK", "empty": "Sem resultado", "error": "Indisponível"}.get(s.status, s.status)
```

Em `NormativoResult`: docstring ganha (após `relevancia`):

```
        relevancia_origem: De onde veio ``relevancia``. Um de ORIGENS_RELEVANCIA.
              Default "padrao_fonte": os searchers atribuem uma constante e
              nenhuma avaliacao rodou ainda.
```

campo `relevancia_origem: str = "padrao_fonte"` após `relevancia: float = 0.0`; e no `__post_init__`, **antes** do hash:

```python
        if self.relevancia_origem not in ORIGENS_RELEVANCIA:
            raise ValueError(
                f"relevancia_origem={self.relevancia_origem!r} fora de "
                f"ORIGENS_RELEVANCIA {sorted(ORIGENS_RELEVANCIA)}"
            )
```

Em `KeywordStatus`: docstring ganha `motivo`, `detalhe`, `parcial` (texto da spec §3.1); a linha `status: str = "ok"  # "ok" | "empty" | "error"` vira `... | "error" (= fonte indisponivel; ver motivo)`; após `retried: bool = False`: A docstring de `retried` passa a dizer (R3): *a palavra-chave foi REENVIADA à fonte depois do passe principal (LexML/Google); tentativas HTTP internas (o TCU faz 3) NÃO contam — ficam no detalhe; retry pulado NÃO marca*. E a de `parcial`: *a coleta NÃO terminou — paginação interrompida (ok/empty) ou, no TCU, um endpoint caído com o outro vivo (error)*.

```python
    motivo: str = ""
    detalhe: str = ""
    parcial: bool = False

    def __post_init__(self) -> None:
        if self.motivo not in MOTIVOS:
            raise ValueError(f"motivo={self.motivo!r} fora de MOTIVOS {sorted(MOTIVOS)}")

    def __setattr__(self, nome: str, valor) -> None:
        # Tudo que vem de fora passa por redigir() em TODA atribuicao — o
        # construtor (dataclass usa setattr) e as mutacoes dos retries
        # (`st.error_message = f"Retry failed: {erro}"`). So no __post_init__
        # deixava a porta dos fundos aberta (rodada 2, R2-H1).
        if nome in ("detalhe", "error_message"):
            valor = redigir(valor or "")
        object.__setattr__(self, nome, valor)
```

Ao fim de `models.py`:

```python
def statuses_para_falha_total(source: str, keywords: list[str], exc: BaseException) -> list[KeywordStatus]:
    """Quando search() de uma fonte LEVANTA, a fonte nao pode sumir do relatorio.

    Antes, app.py engolia a excecao e nao gravava status nenhum: a fonte
    desaparecia da tela e da aba de diagnostico, e o Passo 4 dizia "nenhum
    normativo encontrado" (achado H2 da rodada adversarial de 22/09).
    """
    detalhe = f"{type(exc).__name__}: {exc}"
    alvo = keywords or ["(todas)"]
    return [
        KeywordStatus(keyword=k, source=source, result_count=0, status="error",
                      motivo="erro_interno", detalhe=detalhe, error_message=detalhe)
        for k in alvo
    ]
```

- [ ] **Step 4: `searchers/base.py`** — em `BaseSearcher`, logo após `RATE_LIMIT_JITTER: float = 0.5`:

```python
    # Identificador curto da fonte — o `source` de todo KeywordStatus e o que
    # app.py usa quando search() levanta. Cada subclasse define o seu (T2/T3/T5).
    # Antes, app.py mapeava por nome de exibicao com fallback "google", e uma
    # fonte nova que levantasse viraria "web aberta" (rodada 2).
    SOURCE_ID: str = ""
```

E ao fim do arquivo:

```python
class FonteIndisponivel(Exception):
    """A fonte NAO pode ser consultada — distinto de "consultei e nao achei".

    Nasce no searcher (bloqueio, 5xx, timeout, corpo ilegivel) e sobe ate o
    KeywordStatus como status="error" + motivo + detalhe. Antes, um HTML de
    desafio com HTTP 200 virava lista vazia e a UI dizia "0 erros" (22/09).

    Um motivo desconhecido aqui vira erro_interno com o valor original no
    detalhe — barulho, nunca crash da fonte inteira (a validacao dura e a do
    KeywordStatus). O detalhe passa por models.redigir() JA AQUI, porque os
    searchers logam `str(e)` antes de qualquer KeywordStatus existir: sem isso
    a URL com a chave do CSE ia inteira para o log (rodada 2).
    """

    _CONHECIDOS = {
        "bloqueio_waf", "http_5xx", "http_4xx", "rate_limit", "manutencao_503", "timeout",
        "conexao", "resposta_ilegivel", "endpoint_inexistente", "nao_consultada", "erro_interno",
    }

    def __init__(self, motivo: str, detalhe: str = "") -> None:
        if motivo not in self._CONHECIDOS:
            detalhe = f"motivo desconhecido {motivo!r}: {detalhe}"
            motivo = "erro_interno"
        from models import redigir  # models nao importa searchers: sem ciclo
        super().__init__(motivo)
        self.motivo = motivo
        self.detalhe = redigir(detalhe)

    def __str__(self) -> str:  # dinamico: quem edita .detalhe depois nao deixa str() velho
        return f"{self.motivo}: {self.detalhe}" if self.detalhe else self.motivo
```

Um teste em `test_phase4.py` (classe `TestVocabularioHonestidade`) para isso:

```python
    def test_fonte_indisponivel_motivo_desconhecido_vira_erro_interno_e_str_dinamico(self):
        from searchers.base import FonteIndisponivel
        e = FonteIndisponivel("http5xx", "GET x -> 500")
        assert (e.motivo, "http5xx" in e.detalhe) == ("erro_interno", True)
        e.detalhe = "novo"
        assert str(e) == "erro_interno: novo"
```

- [ ] **Step 5: Rodar e ver passar** — `python -m pytest test_phase4.py -q` → **`58 passed`** (41 + 17 novos: 10 em `TestVocabularioHonestidade`, 4 em `TestRedigir`, 1 em `TestRotuloStatus`, 2 em `TestStatusesParaFalhaTotal`). ⚠ Use o observado: se não for 58, contar os `def test_` antes de suspeitar do código.

- [ ] **Step 6: BASELINE, runner sem LLM, golden, spec** — `BASELINE["test_phase4.py"] = 58`. Em `tools/run_all_tests.py`, `_rodar` passa a chamar `subprocess.run(cmd, cwd=APP, env={**os.environ, "GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}, ...)` (+ `import os`), com o comentário `# 'roda sem LLM' so e garantido se o runner nao herdar a chave (rodada 2: test_comprehensive achou GEMINI_API_KEY no ambiente e levou 429 do Gemini)`. `python tools/golden_master.py comparar` → OK. Spec §3.1: trocar a lista de `motivo` pela de `MOTIVOS` acima e acrescentar `> ⚠ Emendado em 22/09 (plano v3, T1): endpoint_inexistente, erro_interno, http_4xx, rate_limit, nao_consultada; redigir() em toda atribuição de detalhe/error_message; rotulo_status() é o único rótulo humano; parcial pode acompanhar ok, empty e (TCU, um endpoint vivo) error.`

- [ ] **Step 7: Auditoria + commit**

```bash
git add levantamento-normativos/models.py levantamento-normativos/searchers/base.py levantamento-normativos/test_phase4.py tools/run_all_tests.py docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md
git commit -m "feat(frente2): vocabulario de honestidade, redigir() e FonteIndisponivel

MOTIVOS/ORIGENS_RELEVANCIA fechados; KeywordStatus ganha motivo/detalhe/
parcial e redige segredos/controle/formula em TODA atribuicao (a chave do
Google CSE ia para a planilha, inclusive pelo retry). rotulo_status() e
SOURCE_ID nascem aqui. Runner roda as suites com GEMINI_API_KEY vazia. statuses_para_falha_total() para a fonte
que levanta nao sumir do relatorio. FonteIndisponivel em searchers/base.
test_phase4: 41 -> 58."
git push origin master
```

---

### Task 2: LexML — sniff permissivo, falhas declaradas, cache de causa, parcial, `nao_consultada`

**Files** (linhas do HEAD `407b5a1`; conferidas na rodada 2):
- Modify: `levantamento-normativos/searchers/lexml_searcher.py` — `:20` (import de `searchers.base`), `:70-77` (classe/`__init__`), `:106-215` (`search()` inteiro, do `results_by_id` ao fim do retry), `:227-240` (`_search_keyword_safe`), `:242-304` (`_search_keyword`; o `while` está em `:271`), `:306-340` (`_fetch_sru`), `:342-378` (`_try_fetch`), `:393-397` (`_parse_sru_response`)
- Modify: `levantamento-normativos/test_comprehensive.py:362-367` **e `:377-384`** (R2-B2)
- Create: `levantamento-normativos/tests/test_fontes_indisponiveis.py`, `tests/fixtures/lexml_sru_valido.xml`
- Modify: `tools/run_all_tests.py`

**Interfaces — Produces:**
- `LexMLSearcher.SOURCE_ID = "lexml"`.
- `LexMLSearcher._search_keyword_safe(keyword, max_results) -> tuple[list[NormativoResult], Optional[FonteIndisponivel], Optional[FonteIndisponivel]]` = `(resultados, erro_fatal, erro_paginacao)`.
- `LexMLSearcher._urls_mortos: dict[str, FonteIndisponivel]` (limpo a cada `search()`); `_keyword_atual: str`.
- `LexMLSearcher._try_fetch(url, params) -> Optional[str]`: `None` **só** em 404; senão texto ou `FonteIndisponivel`.
- **Formato do `detalhe`** (R2-B1, fato primeiro, URL por último): `HTTP <status> <content-type>; título: <…>; corpo: '<120 chars>' | GET <url efetiva com query>`.
- Convenção de dublê (todas as tasks de searcher): `monkeypatch.setattr("searchers.<mod>.requests.get", fake)`; `time.sleep` dublado pela fixture `autouse`; **o dublê devolve `url + "?" + urlencode(params)` em `.url`**, como o `requests` faz — URL curta escondia o corte do detalhe (R2-B1).

- [ ] **Step 1: Fixture SRU** — `tests/fixtures/lexml_sru_valido.xml` (📝 escrito à mão; sem captura real porque a fonte está bloqueada — registrar em `LESSONS` na T10):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <srw:version>1.1</srw:version>
  <srw:numberOfRecords>1</srw:numberOfRecords>
  <srw:records>
    <srw:record>
      <srw:recordData>
        <dc:title>Lei nº 14.133, de 1º de Abril de 2021</dc:title>
        <dc:description>Lei de Licitações e Contratos Administrativos.</dc:description>
        <dc:date>2021-04-01</dc:date>
        <dc:creator>Presidência da República</dc:creator>
        <dc:type>Lei</dc:type>
        <dc:identifier>urn:lex:br:federal:lei:2021-04-01;14133</dc:identifier>
      </srw:recordData>
    </srw:record>
  </srw:records>
</srw:searchRetrieveResponse>
```

- [ ] **Step 2: Testes que falham** — criar `tests/test_fontes_indisponiveis.py` (16 testes):

```python
# -*- coding: utf-8 -*-
"""Frente 2 — fonte indisponivel != fonte sem resultado (spec 2026-09-22 §3.2/§3.3; plano v3).

Nenhum teste faz rede: requests.get e time.sleep sao dublados. As respostas
vem de fixtures — inclusive o HTML REAL do desafio do Senado e 2 acordaos
REAIS do TCU, capturados em 2026-09-22. O dublê devolve `.url` com a query,
como o requests faz: URL curta escondia o corte do detalhe (rodada 2).

Rodar de dentro de levantamento-normativos/:
    python -m pytest tests/test_fontes_indisponiveis.py -q
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode

import pytest
import requests
from requests.structures import CaseInsensitiveDict

FIXTURES = Path(__file__).parent / "fixtures"
DESAFIO_HTML = (FIXTURES / "lexml_desafio_senado.html").read_text(encoding="utf-8")
SRU_VALIDO = (FIXTURES / "lexml_sru_valido.xml").read_text(encoding="utf-8")


class RespostaFake:
    """O minimo de requests.Response que os searchers tocam."""

    def __init__(self, status: int, corpo: str = "", content_type: str = "application/xml",
                 json_data=None, url: str = "http://fake/?q=x"):
        self.status_code = status
        self.text = corpo
        self.headers = CaseInsensitiveDict({"content-type": content_type})
        self._json = json_data
        self.url = url

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error for url: {self.url}", response=self)

    def json(self):
        if self._json is None:
            raise requests.exceptions.JSONDecodeError("Expecting value", self.text, 0)
        return self._json


@pytest.fixture(autouse=True)
def sem_espera_e_sem_llm(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)


# ---------------------------------------------------------------------------
# LexML
# ---------------------------------------------------------------------------

def _lexml_com(monkeypatch, responder):
    """responder(url, params) -> RespostaFake (ou levanta). Devolve (searcher, chamadas)."""
    from searchers import lexml_searcher

    chamadas: list[str] = []

    def fake_get(url, params=None, timeout=None, **kw):
        chamadas.append(url)
        r = responder(url, params)
        r.url = url + "?" + urlencode(params or {})   # como o requests faz
        return r

    monkeypatch.setattr("searchers.lexml_searcher.requests.get", fake_get)
    return lexml_searcher.LexMLSearcher(), chamadas


def _cenario_real_22_09(url, params):
    """O que o curl mediu em 22/09: primario = 200 HTML de desafio; fallbacks = 404."""
    if url.endswith("/busca/SRU"):
        return RespostaFake(200, DESAFIO_HTML, "text/html; charset=UTF-8")
    return RespostaFake(404, "nao", "text/html")


def test_lexml_cenario_real_toda_keyword_e_bloqueio_waf_e_3_requisicoes(monkeypatch):
    """B2 + R2-B1/H2: 3 requisicoes, bloqueio_waf nas 3, detalhe inteiro sobrevive, retry NAO e inventado."""
    s, chamadas = _lexml_com(monkeypatch, _cenario_real_22_09)
    assert s.search(["protecao de dados", "b", "c"], max_results=5) == []
    assert len(chamadas) == 3 and len(set(chamadas)) == 3          # cada URL uma vez por busca
    sts = s.keyword_statuses
    assert [st.motivo for st in sts] == ["bloqueio_waf"] * 3
    assert all(st.source == "lexml" for st in sts)
    d0 = sts[0].detalhe
    assert "Verificação de segurança" in d0 and "text/html" in d0 and "HTTP 200" in d0
    assert "404" in d0 and "sru/SRU" in d0 and "srw/SRU" in d0     # cadeia agregada com status HTTP
    assert "operation=searchRetrieve" in d0                        # URL efetiva com query (M6)
    assert len(d0) < 2000
    assert all(st.retried is False for st in sts)                  # R2-H2: nada foi retentado
    assert all("retry pulado" in st.detalhe for st in sts)
    assert "cacheada" in sts[1].detalhe and 'palavra-chave "protecao de dados"' in sts[1].detalhe
    assert "query=" not in sts[1].detalhe                          # nao herda a query da keyword 1


def test_lexml_html_generico_e_resposta_ilegivel(monkeypatch):
    s, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(200, "<!DOCTYPE html><html><body>oi</body></html>", "text/html"))
    s.search(["x"], max_results=5)
    assert (s.keyword_statuses[0].status, s.keyword_statuses[0].motivo) == ("error", "resposta_ilegivel")


def test_lexml_xml_truncado_e_resposta_ilegivel(monkeypatch):
    s, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(200, SRU_VALIDO[:200], "application/xml"))
    s.search(["x"], max_results=5)
    assert s.keyword_statuses[0].motivo == "resposta_ilegivel"


def test_lexml_sru_valido_continua_ok_mesmo_com_bom_e_content_type_estranho(monkeypatch):
    """M10: o sniff nao pode reprovar SRU valido por BOM ou content-type."""
    s, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(200, "\ufeff" + SRU_VALIDO, "text/plain"))
    resultados = s.search(["x"], max_results=5)
    assert len(resultados) == 1 and resultados[0].numero == "14133"
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo, st.result_count, st.parcial, st.retried) == ("ok", "", 1, False, False)


def test_lexml_404_em_toda_a_cadeia_e_endpoint_inexistente(monkeypatch):
    s, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(404, "nao", "text/html"))
    s.search(["x"], max_results=5)
    st = s.keyword_statuses[0]
    assert st.motivo == "endpoint_inexistente" and "HTTP 404" in st.detalhe


def test_lexml_timeout_persistente_mapeia_motivo_e_nao_mata_o_url(monkeypatch):
    """B1 + R2-B3: timeout na 1a E na retentativa -> motivo timeout, retried=True; 'b' usou o primario."""
    from searchers import lexml_searcher

    def responder(u, p):
        if '"a"' in p["query"]:
            raise requests.exceptions.Timeout("lento")
        return RespostaFake(200, SRU_VALIDO)

    s, chamadas = _lexml_com(monkeypatch, responder)
    s.search(["a", "b"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.motivo, st.retried, st.status) == ("timeout", True, "error")
    assert "GET" in st.detalhe and "15" in st.detalhe               # REQUEST_TIMEOUT
    assert set(chamadas) == {lexml_searcher.PRIMARY_SRU_URL}      # nunca foi ao fallback
    assert len(chamadas) == 3                                      # a, b, retry de a
    assert s.keyword_statuses[1].status == "ok"


def test_lexml_conexao_e_5xx_mapeiam_motivo(monkeypatch):
    def cai(u, p):
        raise requests.exceptions.ConnectionError("sem rota")
    s, _ = _lexml_com(monkeypatch, cai)
    s.search(["x"], max_results=5)
    assert s.keyword_statuses[0].motivo == "conexao"

    s3, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(500, "boom", "text/html"))
    s3.search(["x"], max_results=5)
    assert s3.keyword_statuses[0].motivo == "http_5xx" and "HTTP 500" in s3.keyword_statuses[0].detalhe


def test_lexml_url_cacheado_que_passa_a_dar_404_nao_vira_erro_interno(monkeypatch):
    """H1: 200 na keyword 'a' cacheia o primario; 404 na 'b' tem de ser endpoint_inexistente, nao TypeError."""
    vez = {"n": 0}

    def responder(u, p):
        vez["n"] += 1
        return RespostaFake(200, SRU_VALIDO) if vez["n"] == 1 else RespostaFake(404, "", "text/html")

    s, _ = _lexml_com(monkeypatch, responder)
    s.search(["a", "b"], max_results=5)
    assert s.keyword_statuses[0].status == "ok"
    assert s.keyword_statuses[1].motivo == "endpoint_inexistente"
    assert "TypeError" not in s.keyword_statuses[1].detalhe


def test_lexml_retry_que_da_certo_diz_que_recuperou(monkeypatch):
    """M1 + R2 (adaptado): 500 na 1a, retry devolve SRU -> ok, motivo vazio, detalhe diz de que recuperou."""
    vez = {"n": 0}

    def responder(u, p):
        vez["n"] += 1
        return RespostaFake(500, "x", "text/html") if vez["n"] == 1 else RespostaFake(200, SRU_VALIDO)

    s, _ = _lexml_com(monkeypatch, responder)
    s.search(["a"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo, st.retried, st.result_count) == ("ok", "", True, 1)
    assert st.detalhe == "recuperado no retry após http_5xx"


def test_lexml_falha_na_segunda_pagina_e_ok_parcial_com_o_motivo_no_detalhe(monkeypatch):
    """H5 + R2-B4: pagina 1 diz 50 registros, pagina 2 devolve o desafio -> ok, parcial, detalhe diz pagina E motivo."""
    vez = {"n": 0}
    pagina1 = SRU_VALIDO.replace("<srw:numberOfRecords>1</srw:numberOfRecords>", "<srw:numberOfRecords>50</srw:numberOfRecords>")

    def responder(u, p):
        vez["n"] += 1
        return RespostaFake(200, pagina1) if vez["n"] == 1 else RespostaFake(200, DESAFIO_HTML, "text/html")

    s, _ = _lexml_com(monkeypatch, responder)
    resultados = s.search(["a"], max_results=50)
    assert len(resultados) == 1
    st = s.keyword_statuses[0]
    assert (st.status, st.parcial, st.motivo) == ("ok", True, "")
    assert st.detalhe.startswith("startRecord=21: bloqueio_waf: ")


def test_lexml_xml_ilegivel_na_segunda_pagina_tambem_e_parcial(monkeypatch):
    """R3-H3: XML truncado na pagina 2 nao pode virar erro fatal que descarta a pagina 1."""
    vez = {"n": 0}
    pagina1 = SRU_VALIDO.replace("<srw:numberOfRecords>1</srw:numberOfRecords>", "<srw:numberOfRecords>50</srw:numberOfRecords>")

    def responder(u, p):
        vez["n"] += 1
        return RespostaFake(200, pagina1) if vez["n"] == 1 else RespostaFake(200, SRU_VALIDO[:200], "application/xml")

    s, _ = _lexml_com(monkeypatch, responder)
    resultados = s.search(["a"], max_results=50)
    assert len(resultados) == 1
    st = s.keyword_statuses[0]
    assert (st.status, st.parcial, st.retried) == ("ok", True, False)
    assert st.detalhe.startswith("startRecord=21: resposta_ilegivel: ")


def test_lexml_keywords_nao_consultadas_por_cap_ganham_status(monkeypatch):
    """M4: max_results=1 atinge o cap na 1a keyword; 'b' e 'c' nao podem sumir do relatorio."""
    s, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(200, SRU_VALIDO))
    s.search(["a", "b", "c"], max_results=1)
    assert [st.status for st in s.keyword_statuses] == ["ok", "error", "error"]
    assert [st.motivo for st in s.keyword_statuses[1:]] == ["nao_consultada"] * 2
    assert "max_results=1" in s.keyword_statuses[1].detalhe and s.keyword_statuses[1].retried is False


def test_lexml_cache_de_falha_e_limpo_a_cada_busca(monkeypatch):
    """M11: mesma instancia, busca 1 com 404 em tudo, busca 2 com 200 -> ok."""
    vez = {"busca": 1}
    s, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(404, "", "text/html") if vez["busca"] == 1 else RespostaFake(200, SRU_VALIDO))
    s.search(["a"], max_results=5)
    assert s.keyword_statuses[0].motivo == "endpoint_inexistente"
    vez["busca"] = 2
    s.search(["a"], max_results=5)
    assert s.keyword_statuses[0].status == "ok"


def test_lexml_parse_error_levanta_fonte_indisponivel():
    """B3: o contrato antigo ([], 0) em XML malformado deixou de existir; test_comprehensive foi adaptado."""
    from searchers.base import FonteIndisponivel
    from searchers.lexml_searcher import LexMLSearcher
    with pytest.raises(FonteIndisponivel) as e:
        LexMLSearcher()._parse_sru_response("<not>valid<xml", "teste")
    assert e.value.motivo == "resposta_ilegivel"


def test_lexml_source_id_e_o_source_de_todo_status(monkeypatch):
    from searchers.lexml_searcher import LexMLSearcher
    assert LexMLSearcher.SOURCE_ID == "lexml"
    s, _ = _lexml_com(monkeypatch, _cenario_real_22_09)
    s.search(["a", "b"], max_results=5)
    assert {st.source for st in s.keyword_statuses} == {"lexml"}


def test_lexml_detalhe_de_erro_nao_carrega_segredo_nem_e_cortado_no_meio(monkeypatch):
    """R2-B1/H1 juntos: URL longa real + segredo hipotetico na query -> redigido e inteiro."""
    def responder(u, p):
        p["key"] = "AIzaSECRETO"   # simula uma fonte que exigisse chave na query
        return RespostaFake(500, "x" * 500, "text/html")
    s, _ = _lexml_com(monkeypatch, responder)
    s.search(["protecao de dados pessoais e privacidade na administracao publica federal"], max_results=5)
    d = s.keyword_statuses[0].detalhe
    assert "AIzaSECRETO" not in d and "key=***" in d
    assert d.startswith("HTTP 500") and "| GET " in d and "operation=searchRetrieve" in d
```

- [ ] **Step 3: Rodar e ver falhar** — `python -m pytest tests/test_fontes_indisponiveis.py -q` → 16 failed (assertions de status/motivo; nenhum `ImportError` — T1 já entregou os símbolos).

- [ ] **Step 4: `lexml_searcher.py` — imports, `SOURCE_ID`, `__init__`**

Import (`:20`): `from searchers.base import BaseSearcher, FonteIndisponivel, ProgressCallback`; acrescentar `from urllib.parse import urlencode`. Conferir `import re` no topo (existe: `URN_PATTERN` usa).

Na classe (`:70-77`), logo após `RATE_LIMIT_JITTER = 0.5`: `SOURCE_ID = "lexml"`. O `__init__` **já existe** em `:76-77` — acrescentar 3 linhas mantendo o comentário existente:

```python
    def __init__(self):
        self._sru_url: Optional[str] = None  # Resolved after first request
        # URLs que ja falharam NESTA busca -> a causa. Limpo em search().
        # Antes, cada palavra-chave tentava a cadeia inteira de novo (3 URLs x N
        # palavras-chave: parte dos ~390s do test_searchers.py em 22/09).
        self._urls_mortos: dict[str, FonteIndisponivel] = {}
        self._keyword_atual: str = ""   # para o detalhe dizer de qual keyword e a causa cacheada
```

- [ ] **Step 5: `_try_fetch` — reescrever inteiro** (`:342-378`):

```python
    def _try_fetch(self, url: str, params: dict) -> Optional[str]:
        """Attempt a single GET request to the given SRU URL.

        Retries once on connection error after a 3-second delay.

        Returns:
            Response body on success; None ONLY on HTTP 404 (URL inexistente —
            o chamador passa ao proximo da cadeia).

        Raises:
            FonteIndisponivel: para tudo que nao e sucesso nem 404 — timeout,
                conexao (apos o retry), 5xx/4xx, corpo que nao e SRU. Antes,
                esses casos devolviam None e viravam "URL morto" e depois
                "sem resultado" (bloqueadores B1/B2 da rodada de 22/09).
                Formato do detalhe: fato primeiro, URL (com query) por ultimo.
        """
        import time

        for attempt in range(2):  # Max 2 attempts (initial + 1 retry)
            try:
                response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            except requests.exceptions.Timeout as e:   # ANTES de ConnectionError: ConnectTimeout herda dos dois
                logger.warning(f"LexML timeout ({REQUEST_TIMEOUT}s) for {url}")
                raise FonteIndisponivel("timeout", f"sem resposta em {REQUEST_TIMEOUT}s | GET {url}?{urlencode(params)}") from e
            except requests.exceptions.ConnectionError as e:
                if attempt == 0:
                    logger.warning(f"LexML connection error: {e}. Retrying in 3s...")
                    time.sleep(3)
                    continue
                logger.error(f"LexML connection error after retry: {e}")
                raise FonteIndisponivel("conexao", f"conexao recusada/sem rota ({str(e)[:120]}) | GET {url}?{urlencode(params)}") from e
            except requests.exceptions.RequestException as e:
                logger.error(f"LexML request error: {e}")
                raise FonteIndisponivel("erro_interno", f"{type(e).__name__}: {str(e)[:120]} | GET {url}?{urlencode(params)}") from e

            efetiva = getattr(response, "url", None) or url
            sc = response.status_code
            if sc == 404:
                logger.warning(f"LexML: 404 from {url}")
                return None
            if sc == 429:
                raise FonteIndisponivel("rate_limit", f"HTTP 429 | GET {efetiva}")
            if sc >= 500:
                raise FonteIndisponivel("http_5xx", f"HTTP {sc}; corpo: {(response.text or '')[:120]!r} | GET {efetiva}")
            if sc >= 400:
                raise FonteIndisponivel("http_4xx", f"HTTP {sc} | GET {efetiva}")
            self._exigir_sru(response, efetiva)
            return response.text
        return None  # inalcancavel: o laco sempre devolve ou levanta

    def _exigir_sru(self, response, url: str) -> None:
        """HTTP 200 nao prova que veio SRU: em 22/09 o LexML devolvia 200
        text/html com a pagina "Verificacao de seguranca" do Senado.

        Sniff PERMISSIVO de proposito (M10): so HTML explicito e reprovado
        aqui; qualquer outra coisa vai para o ET, que levanta ParseError ->
        resposta_ilegivel em _parse_sru_response. SRU com BOM, sem <?xml ou
        com outro prefixo de namespace continua passando.
        """
        content_type = (response.headers.get("Content-Type") or "").lower()
        corpo = (response.text or "").lstrip("\ufeff \t\r\n")
        inicio = corpo[:15].lower()
        e_html = "text/html" in content_type or inicio.startswith(("<!doctype html", "<html"))
        if not e_html:
            return
        titulo = re.search(r"<title>([^<]*)</title>", corpo)
        fato = f"HTTP {response.status_code} {content_type or 'sem content-type'}"
        if titulo:
            fato += f"; título: {titulo.group(1).strip()}"
        detalhe = f"{fato}; corpo: {corpo[:120]!r} | GET {url}"
        texto = corpo.lower()
        if "verificação de segurança" in texto or "verificacao de seguranca" in texto or "challenge" in texto:
            raise FonteIndisponivel("bloqueio_waf", detalhe)
        raise FonteIndisponivel("resposta_ilegivel", detalhe)
```

- [ ] **Step 6: `_parse_sru_response`** (`:393-397`):

```python
        try:
            root = ET.fromstring(xml_text.lstrip("\ufeff \t\r\n"))
        except ET.ParseError as e:
            # Antes devolvia ([], 0) — a linha que transformava bloqueio em
            # "sem resultado". Agora e falha declarada.
            raise FonteIndisponivel(
                "resposta_ilegivel", f"XML SRU nao parseia: {e}; corpo: {xml_text[:120]!r}"
            ) from e
```

Docstring: `Returns ([], 0) on parse error.` → `Raises FonteIndisponivel("resposta_ilegivel") on parse error.`

- [ ] **Step 7: `_fetch_sru` — cache de causa por URL** (`:306-340`), corpo novo, mais dois métodos novos logo abaixo:

```python
        if self._sru_url:
            result = self._try_fetch(self._sru_url, params)
            if result is not None:
                return result
            # o URL que funcionava passou a dar 404 (H1): invalida e cai na cadeia
            self._urls_mortos[self._sru_url] = FonteIndisponivel(
                "endpoint_inexistente", f"HTTP 404 (URL que antes funcionava nesta busca) | GET {self._sru_url}")
            self._sru_url = None

        for url in (PRIMARY_SRU_URL, FALLBACK_SRU_URL, FALLBACK_SRU_URL_2):
            if url in self._urls_mortos:
                continue
            try:
                result = self._try_fetch(url, params)
            except FonteIndisponivel as e:
                if e.motivo in ("bloqueio_waf", "resposta_ilegivel"):
                    # falha do URL: guarda a causa e tenta o proximo da cadeia
                    self._urls_mortos[url] = e
                    logger.warning(f"LexML: {url} {e.motivo}; proximo da cadeia")
                    continue
                raise  # timeout/conexao/5xx/4xx: erro DESTA requisicao, nao do URL
            if result is not None:
                self._sru_url = url
                return result
            self._urls_mortos[url] = FonteIndisponivel("endpoint_inexistente", f"HTTP 404 | GET {url}")
            logger.warning(f"LexML: {url} 404; proximo da cadeia")

        raise self._causa_da_cadeia_morta()

    _PRIORIDADE = ("bloqueio_waf", "resposta_ilegivel", "endpoint_inexistente")

    @staticmethod
    def _status_http(causa: FonteIndisponivel) -> str:
        m = re.search(r"HTTP (\d{3})", causa.detalhe)
        return m.group(1) if m else "?"

    def _causa_da_cadeia_morta(self) -> FonteIndisponivel:
        """Nenhum URL restou: relevanta a causa MAIS ESPECIFICA (B2).

        'endpoint_inexistente' generico so quando tudo foi 404. O detalhe traz
        a causa principal inteira (fato primeiro) e a cadeia URL por URL COM o
        status HTTP (rodada 2: so o nome do motivo nao permitia reproduzir).
        Quando a causa foi medida numa keyword anterior, diz isso e tira a
        query da URL — senao a planilha mandaria reproduzir a busca errada.
        """
        causas = self._urls_mortos
        motivo = next((m for m in self._PRIORIDADE if any(c.motivo == m for c in causas.values())), "endpoint_inexistente")
        url_principal, principal = next((u, c) for u, c in causas.items() if c.motivo == motivo)
        cadeia = "; ".join(
            f"{u.split('gov.br/', 1)[-1]}: {c.motivo} (HTTP {self._status_http(c)})" for u, c in causas.items()
        )
        keyword_da_causa = getattr(principal, "keyword", "")
        fato, _, url_com_query = principal.detalhe.partition(" | GET ")
        if keyword_da_causa and keyword_da_causa != self._keyword_atual:
            detalhe = (f'causa cacheada da palavra-chave "{keyword_da_causa}" (esta palavra-chave não foi enviada): '
                       f"{fato} | cadeia: {cadeia} | GET {url_principal}")
        else:
            detalhe = f"{fato} | cadeia: {cadeia} | GET {url_com_query or url_principal}"   # URL por ULTIMO (R2-B1)
        e = FonteIndisponivel(motivo, detalhe)
        e.keyword = keyword_da_causa or self._keyword_atual
        return e
```

⚠ `e.keyword` é um atributo dinâmico na exceção (não está em `FonteIndisponivel.__init__`): `_search_keyword` o preenche ao cachear (Step 8). Docstring de `_fetch_sru`: substituir `Response body as string, or None on failure.` por `Response body as string. Raises FonteIndisponivel when no URL works; failed URLs are cached in self._urls_mortos for this search.`

- [ ] **Step 8: `_search_keyword`** (`:242-304`) — substituir de `all_results: list[NormativoResult] = []` (`:267`) até o `return all_results[:max_results]` (`:304`) por:

```python
        all_results: list[NormativoResult] = []
        start_record = 1
        first_page = True
        self._erro_paginacao: Optional[FonteIndisponivel] = None
        self._keyword_atual = keyword

        while len(all_results) < max_results:
            params = {
                "operation": "searchRetrieve",
                "version": "1.1",
                "query": cql_query,
                "startRecord": start_record,
                "maximumRecords": RECORDS_PER_PAGE,
            }

            try:
                xml_text = self._fetch_sru(params)
                # R3-H3: o parse fica DENTRO do try — XML ilegivel na pagina 2 e
                # falha de paginacao (parcial), nao erro fatal que joga fora a pagina 1
                records, total_count = self._parse_sru_response(xml_text, keyword)
            except FonteIndisponivel as e:
                if not getattr(e, "keyword", ""):
                    e.keyword = keyword          # de qual keyword e esta causa (cache)
                for causa in self._urls_mortos.values():
                    if not getattr(causa, "keyword", ""):
                        causa.keyword = keyword
                if first_page:
                    raise
                # H5 + R2-B4: pagina seguinte falhou — devolve o que veio, mas
                # DECLARA pagina E motivo (o TCU faz igual)
                e.detalhe = f"startRecord={start_record}: {e.motivo}: {e.detalhe}"
                self._erro_paginacao = e
                logger.warning(f"LexML: paginacao interrompida: {e}")
                break

            first_page = False
            all_results.extend(records)

            # Check if there are more pages
            next_start = start_record + RECORDS_PER_PAGE
            if next_start > total_count or len(records) == 0:
                break  # No more pages

            start_record = next_start

            # Rate limit between pagination requests
            self._rate_limit()

        return all_results[:max_results]
```

(As linhas `:245-266` — docstring, sanitização do CQL e `cql_query` — ficam como estão. O bloco `if xml_text is None: ... raise ConnectionError(...)` de `:281-288` desaparece com a substituição.) Docstring `Raises: ConnectionError...` → `Raises: FonteIndisponivel: se a primeira pagina falhar. Falha em pagina seguinte fica em self._erro_paginacao.`

- [ ] **Step 9: `_search_keyword_safe`** (`:227-240`):

```python
    def _search_keyword_safe(
        self, keyword: str, max_results: int = 50
    ) -> tuple[list[NormativoResult], Optional[FonteIndisponivel], Optional[FonteIndisponivel]]:
        """Search for a keyword, returning (results, erro_fatal, erro_paginacao).

        Returns:
            (results, None, None) em sucesso completo; (results, None, erro) quando
            a paginacao parou (parcial); ([], erro, None) quando a fonte nao pode
            ser consultada. Qualquer excecao imprevista vira erro_interno —
            nunca "sem resultado".
        """
        self._erro_paginacao = None
        try:
            results = self._search_keyword(keyword, max_results=max_results)
            return results, None, self._erro_paginacao
        except FonteIndisponivel as e:
            logger.warning(f"LexML: fonte indisponivel para '{keyword}': {e}")
            return [], e, None
        except Exception as e:
            logger.error(f"LexML: erro interno em '{keyword}': {e}")
            return [], FonteIndisponivel("erro_interno", f"{type(e).__name__}: {e}"[:200]), None
```

- [ ] **Step 10: `search()` — laço principal, cap e retry.** Substituir de `:106` (`results_by_id: dict...`) até **`:215`** (`if not api_still_down: self._rate_limit()` — o retry acaba aí, não em `:212`; R2) por:

```python
        results_by_id: dict[str, NormativoResult] = {}
        self.keyword_statuses: list[KeywordStatus] = []
        self._urls_mortos.clear()   # M11: cache de falha e POR BUSCA
        self._sru_url = None
        failed_keywords: list[str] = []
        total_keywords = len(keywords)
        URLS = (PRIMARY_SRU_URL, FALLBACK_SRU_URL, FALLBACK_SRU_URL_2)

        for idx, keyword in enumerate(keywords):
            if len(results_by_id) >= max_results:
                logger.info(f"LexML: reached max_results ({max_results}), stopping after {idx}/{total_keywords} keywords")
                # M4: palavra-chave nunca consultada nao pode virar "sem resultado"
                for restante in keywords[idx:]:
                    self.keyword_statuses.append(KeywordStatus(
                        keyword=restante, source=self.SOURCE_ID, result_count=0, status="error",
                        motivo="nao_consultada",
                        detalhe=f"busca parou em max_results={max_results} antes desta palavra-chave",
                    ))
                break

            if progress_callback:
                progress_callback(idx, total_keywords, f"LexML: buscando '{keyword}'")
            logger.info(f"LexML [{idx+1}/{total_keywords}]: buscando '{keyword}'")

            remaining = max_results - len(results_by_id)
            keyword_results, erro, erro_pag = self._search_keyword_safe(keyword, max_results=remaining)

            if erro is not None:
                self.keyword_statuses.append(KeywordStatus(
                    keyword=keyword, source=self.SOURCE_ID, result_count=0, status="error",
                    error_message=str(erro), motivo=erro.motivo, detalhe=erro.detalhe,
                ))
                failed_keywords.append(keyword)
            elif len(keyword_results) == 0:
                self.keyword_statuses.append(KeywordStatus(
                    keyword=keyword, source=self.SOURCE_ID, result_count=0, status="empty",
                    parcial=erro_pag is not None, detalhe=erro_pag.detalhe if erro_pag else "",
                ))
            else:
                count_before = len(results_by_id)
                for result in keyword_results:
                    if result.id in results_by_id:
                        existing = results_by_id[result.id]
                        if keyword not in existing.found_by:
                            existing.found_by += f", {keyword}"
                    else:
                        results_by_id[result.id] = result
                new_count = len(results_by_id) - count_before
                self.keyword_statuses.append(KeywordStatus(
                    keyword=keyword, source=self.SOURCE_ID, result_count=new_count, status="ok",
                    parcial=erro_pag is not None, detalhe=erro_pag.detalhe if erro_pag else "",
                ))

            if idx < total_keywords - 1:
                self._rate_limit()

        # --- Retry failed keywords (max 3 attempts, bail if API is down) ---
        MAX_RETRIES = 3
        cadeia_morta = all(u in self._urls_mortos for u in URLS)
        if failed_keywords and not cadeia_morta:
            retry_count = min(len(failed_keywords), MAX_RETRIES)
            logger.info(f"LexML: retrying {retry_count} of {len(failed_keywords)} failed keywords (max {MAX_RETRIES})")
            if progress_callback:
                progress_callback(total_keywords, total_keywords,
                                  f"LexML: retentando {retry_count} palavras-chave com erro...")

            import time
            time.sleep(3)

            # Only retry a few — if the first retry also fails, the API is
            # likely down and retrying more keywords would waste time.
            api_still_down = False
            for keyword in failed_keywords[:MAX_RETRIES]:
                if len(results_by_id) >= max_results:
                    break
                if api_still_down:
                    # Sem requisicao: NAO marca retried (R2-H2); so registra que pulou.
                    for st in self.keyword_statuses:
                        if st.keyword == keyword and st.source == self.SOURCE_ID and st.status == "error":
                            st.detalhe = f"{st.detalhe} | retry pulado: a retentativa anterior falhou"
                            break
                    continue

                remaining = max_results - len(results_by_id)
                keyword_results, erro, erro_pag = self._search_keyword_safe(keyword, max_results=remaining)

                for st in self.keyword_statuses:
                    if st.keyword == keyword and st.source == self.SOURCE_ID and st.status == "error":
                        st.retried = True
                        if erro is not None:
                            st.error_message = f"Retry failed: {erro}"
                            # B2: nunca rebaixar um motivo especifico para generico
                            if st.motivo in ("", "endpoint_inexistente") or erro.motivo != "endpoint_inexistente":
                                st.motivo, st.detalhe = erro.motivo, erro.detalhe
                            api_still_down = True  # Stop retrying
                        else:
                            # R2 (adaptado): o motivo anterior nao some — vira historia no detalhe
                            recuperado = f"recuperado no retry após {st.motivo}"
                            st.status = "ok" if keyword_results else "empty"
                            st.error_message, st.motivo = "", ""
                            st.parcial = erro_pag is not None
                            st.detalhe = f"{recuperado}; {erro_pag.detalhe}" if erro_pag else recuperado
                            for result in keyword_results:
                                if result.id in results_by_id:
                                    existing = results_by_id[result.id]
                                    if keyword not in existing.found_by:
                                        existing.found_by += f", {keyword}"
                                else:
                                    results_by_id[result.id] = result
                            st.result_count = len(keyword_results)
                        break

                if not api_still_down:
                    self._rate_limit()
        elif failed_keywords:
            # cadeia morta em cache: retentar nao faria requisicao nenhuma (B2).
            # R2-H2: NAO marca retried — "Retentado: Sim" sem requisicao seria mentira na planilha.
            logger.info("LexML: cadeia de URLs morta nesta busca; retry pulado")
            for st in self.keyword_statuses:
                if st.source == self.SOURCE_ID and st.status == "error" and st.motivo != "nao_consultada":
                    st.detalhe = f"{st.detalhe} | retry pulado: os 3 URLs já falharam nesta busca"
```

⚠ **O que o trecho preserva** do original: mensagens de log do laço, `progress_callback`, `MAX_RETRIES=3`, o comentário "Only retry a few…", a semântica de `api_still_down`. **O que é removido de propósito** (para o auditor do gate não reabrir): os logs `LexML: previous URL failed, trying fallback: {url}` e `LexML: all SRU endpoints failed` (`:331-339`, substituídos pelos `logger.warning` do Step 7) e o `error_message = "API indisponivel (retry skipped)"` (`:185`, substituído pelo motivo original + `retry pulado` no detalhe).

- [ ] **Step 11: Adaptar `test_comprehensive.py`** (B3 + R2-B2) — **três** call sites, contrato novo, testes mantidos:

(a) `:362-367`:
```python
def test_lexml_parse_sru_response_malformed_xml():
    """Malformed XML must be DECLARED as resposta_ilegivel, never silently ([], 0).

    Contrato mudou na frente 2 (2026-09-22): devolver ([], 0) era a linha que
    transformava o bloqueio do LexML em "sem resultado"."""
    from searchers.base import FonteIndisponivel
    searcher = LexMLSearcher()
    try:
        searcher._parse_sru_response("<not>valid<xml", "teste")
    except FonteIndisponivel as e:
        assert e.motivo == "resposta_ilegivel"
    else:
        raise AssertionError("esperava FonteIndisponivel")
```

(b) `:377-384` (`test_lexml_cql_injection_sanitization`): `results, error = searcher._search_keyword_safe(...)` → `results, erro, _pag = searcher._search_keyword_safe(...)`; manter `assert isinstance(results, list)`; docstring ganha `Contrato mudou na frente 2: (results, erro_fatal, erro_paginacao).` ⚠ Esse teste faz **rede real** (LexML); continua fazendo — fora do escopo desta frente dublá-lo; registrar em `_TODO.md` P3.

(c) Antes de fechar: `git grep -n "_search_keyword_safe" -- '*.py'` → **nenhum** call site além dos de `lexml_searcher.py` e deste teste.

- [ ] **Step 12: Rodar e ver passar**

`python -m pytest tests/test_fontes_indisponiveis.py -q` → `16 passed`.
`python test_comprehensive.py | tail -3` → `Total: 98 | Passed: 98 | Failed: 0`.
`python test_searchers.py | tail -2` → `13/13 passed` (anotar o tempo: era ~390s).
`python -m pytest test_phase4.py -q` → `58 passed`.

- [ ] **Step 13: Runner** — `SUITES_PYTEST = ["test_phase4.py", "tests/test_fontes_indisponiveis.py"]`, `BASELINE["tests/test_fontes_indisponiveis.py"] = 16`; atualizar o comentário sobre "nasce com UMA suite". Na raiz: `python tools/run_all_tests.py` → TUDO VERDE; `python tools/golden_master.py comparar` → OK.

- [ ] **Step 14: Auditoria (os 2 comandos) + commit**

```bash
git add levantamento-normativos/searchers/lexml_searcher.py levantamento-normativos/test_comprehensive.py levantamento-normativos/tests/ tools/run_all_tests.py
git commit -m "feat(frente2): LexML declara bloqueio, timeout, 5xx e paginacao parcial — nunca 'sem resultado'

_try_fetch reescrito: so 404 devolve None; o resto levanta com o motivo
certo e o detalhe traz o fato primeiro e a URL por ultimo (B1, R2-B1).
Cache de causa por URL, limpo por busca; cadeia morta relevanta a causa
mais especifica com a cadeia URL por URL e status HTTP; retry pulado nao
marca retried e diz que pulou (B2, R2-H2). Sniff permissivo. Falha em
pagina seguinte vira parcial com pagina e motivo no detalhe (H5, R2-B4).
Keyword pulada por max_results vira nao_consultada. Retry que da certo
diz de que recuperou. test_comprehensive: 3 call sites adaptados (98
mantidos). XML ilegivel em pagina seguinte e parcial, nao fatal. Suite nova: 16."
git push origin master
```

---

### Task 3: TCU — 5xx/4xx/503/HTML declarados, paginação parcial, classificação por endpoint

**Files:**
- Modify: `levantamento-normativos/searchers/tcu_searcher.py` — imports (`:1-20`); classe (`:33-40`, `SOURCE_ID`); `search()` (`:62-147`); `_fetch_all_pages_safe`/`_fetch_all_pages` (`:153-206`); `_request_with_retry` (`:208-253`)
- Modify: `levantamento-normativos/requirements.txt` (`tzdata`)
- Modify: `levantamento-normativos/test_comprehensive.py:473-477`
- Test: `tests/test_fontes_indisponiveis.py` (seção TCU, 10 testes)
- Modify: `tools/run_all_tests.py`

**Interfaces — Produces:**
- `TCUSearcher.SOURCE_ID = "tcu"`.
- `TCUSearcher._request_with_retry(url, params) -> dict | list` — levanta `FonteIndisponivel` (nunca `None`).
- `TCUSearcher._fetch_all_pages(url) -> tuple[list[dict], Optional[FonteIndisponivel], bool]` = `(itens, erro, parcial)`; idem `_fetch_all_pages_safe`.
- `TCUSearcher._texto_do_acordao(item) -> str` (nesta task lê só `ementa`; a T4 troca).
- Formato do `detalhe` por keyword — gravado **sempre** (R3-H5): `Acórdãos: <ok (N itens, M sem sumário — nesses só o título casa) | parcial (...) | <motivo> em <fato>>; Atos: <idem>`.

- [ ] **Step 1: Testes que falham** — acrescentar a `tests/test_fontes_indisponiveis.py`:

```python
# ---------------------------------------------------------------------------
# TCU — a fixture e o item REAL capturado em 22/09 (sem `ementa`, `numero`, `ano`)
# ---------------------------------------------------------------------------

ACORDAOS_REAIS = json.loads((FIXTURES / "tcu_acordaos_real.json").read_text(encoding="utf-8"))
ACORDAO = ACORDAOS_REAIS[0]   # sumario fala de "TURISMO"


def _tcu_com(monkeypatch, por_url):
    """por_url: {trecho_da_url: callable(params) -> RespostaFake | levanta}."""
    from searchers import tcu_searcher

    chamadas: list[str] = []

    def fake_get(url, params=None, timeout=None, **kw):
        chamadas.append(url)
        for trecho, responder in por_url.items():
            if trecho in url:
                r = responder(params)
                r.url = url + "?" + urlencode(params or {})
                return r
        raise AssertionError(f"URL inesperada: {url}")

    monkeypatch.setattr("searchers.tcu_searcher.requests.get", fake_get)
    return tcu_searcher.TCUSearcher(), chamadas


def _500_atos(p):
    return RespostaFake(500, '{"url":"Erro no serviço","erro":"HttpClientErrorException: 404 Not Found"}',
                        "application/json;charset=UTF-8")


def test_tcu_500_num_endpoint_e_error_parcial_mesmo_com_o_outro_ok(monkeypatch):
    s, chamadas = _tcu_com(monkeypatch, {
        "recupera-acordaos": lambda p: RespostaFake(200, json_data=ACORDAOS_REAIS),
        "recupera-atos-normativos": _500_atos,
    })
    resultados = s.search(["turismo"], max_results=5)
    assert len(resultados) == 0          # T4 troca para 1: ate la _texto_do_acordao le so `ementa`, que a API nao tem
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo, st.source) == ("error", "http_5xx", "tcu")
    assert st.parcial is True            # R2: um endpoint respondeu -> a coleta e parcial
    assert "recupera-atos-normativos" in st.detalhe and "404 Not Found" in st.detalhe
    assert "Acórdãos: ok (2 itens, 0 sem sumário" in st.detalhe
    assert sum(1 for u in chamadas if "atos" in u) == 3  # 3 retries no 5xx


def test_tcu_503_e_manutencao_com_hora_e_hipotese(monkeypatch):
    s, _ = _tcu_com(monkeypatch, {
        "recupera-acordaos": lambda p: RespostaFake(503, "", "text/html"),
        "recupera-atos-normativos": lambda p: RespostaFake(503, "", "text/html"),
    })
    s.search(["x"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo) == ("error", "manutencao_503")
    assert "HTTP 503 às " in st.detalhe and "20h" in st.detalhe and "hipótese" in st.detalhe


def test_tcu_404_e_endpoint_inexistente_sem_retry(monkeypatch):
    s, chamadas = _tcu_com(monkeypatch, {
        "recupera-acordaos": lambda p: RespostaFake(404, "", "text/html"),
        "recupera-atos-normativos": lambda p: RespostaFake(404, "", "text/html"),
    })
    s.search(["x"], max_results=5)
    assert s.keyword_statuses[0].motivo == "endpoint_inexistente"
    assert len(chamadas) == 2                          # sem retry em 4xx


def test_tcu_429_e_rate_limit_e_403_e_http_4xx(monkeypatch):
    s, _ = _tcu_com(monkeypatch, {
        "recupera-acordaos": lambda p: RespostaFake(429, "", "text/html"),
        "recupera-atos-normativos": lambda p: RespostaFake(403, "", "text/html"),
    })
    s.search(["x"], max_results=5)
    st = s.keyword_statuses[0]
    assert st.motivo == "rate_limit"                  # o primeiro endpoint que caiu manda o motivo
    assert "http_4xx" in st.detalhe and "HTTP 403" in st.detalhe


def test_tcu_200_html_e_bloqueio_ou_ilegivel_sem_retry(monkeypatch):
    s, chamadas = _tcu_com(monkeypatch, {
        "recupera-acordaos": lambda p: RespostaFake(200, DESAFIO_HTML, "text/html"),
        "recupera-atos-normativos": lambda p: RespostaFake(200, "<html>x</html>", "text/html"),
    })
    s.search(["x"], max_results=5)
    st = s.keyword_statuses[0]
    assert st.motivo == "bloqueio_waf" and "Verificação de segurança" in st.detalhe
    assert "resposta_ilegivel" in st.detalhe
    assert len(chamadas) == 2


def test_tcu_timeout_e_conexao_mapeiam_motivo(monkeypatch):
    def estoura(p):
        raise requests.exceptions.Timeout("lento")
    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": estoura, "recupera-atos-normativos": estoura})
    s.search(["x"], max_results=5)
    assert s.keyword_statuses[0].motivo == "timeout"

    def cai(p):
        raise requests.exceptions.ConnectionError("sem rota")
    s2, _ = _tcu_com(monkeypatch, {"recupera-acordaos": cai, "recupera-atos-normativos": cai})
    s2.search(["x"], max_results=5)
    assert s2.keyword_statuses[0].motivo == "conexao"


def test_tcu_falha_na_segunda_pagina_e_parcial_com_pagina_e_motivo(monkeypatch):
    from searchers import tcu_searcher
    pagina_cheia = [dict(ACORDAO, key=f"A-{i}", numeroAcordao=str(i)) for i in range(tcu_searcher.PAGE_SIZE)]

    def acordaos(p):
        if p["inicio"] == 0:
            return RespostaFake(200, json_data=pagina_cheia)
        return RespostaFake(500, "boom", "text/html")

    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": acordaos,
                                  "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[])})
    s.search(["turismo"], max_results=100)
    st = s.keyword_statuses[0]
    assert st.parcial is True
    assert "pagina 2 (inicio=20): http_5xx" in st.detalhe


def test_tcu_dois_endpoints_ok_sem_match_continua_empty(monkeypatch):
    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": lambda p: RespostaFake(200, json_data=ACORDAOS_REAIS),
                                  "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[])})
    s.search(["assunto-que-nao-existe"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo, st.parcial) == ("empty", "", False)
    assert st.detalhe.startswith("Acórdãos: ok (2 itens")       # R3-H5: o resumo vai SEMPRE


def test_tcu_acordaos_sem_sumario_sao_contados_e_nao_casam(monkeypatch):
    """R3-B1: o contador olha o CAMPO sumario; titulo esta sempre preenchido e nao conta."""
    sem = [dict(a, sumario=None) for a in ACORDAOS_REAIS]
    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": lambda p: RespostaFake(200, json_data=sem),
                                  "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[])})
    resultados = s.search(["turismo"], max_results=5)
    assert resultados == []
    st = s.keyword_statuses[0]
    assert st.status == "empty" and "2 sem sumário" in st.detalhe


@pytest.mark.xfail(reason="so na T4 _texto_do_acordao le sumario/titulo; ate la o item nem e mapeado", strict=True)
def test_tcu_item_que_quebra_o_mapeamento_vira_erro_interno_declarado(monkeypatch):
    """H2: um item malformado derrubava search() inteiro; agora e erro_interno por keyword, nao sumico."""
    quebrado = dict(ACORDAO, titulo=None, numeroAcordao=None, sumario=123)   # " ".join com int -> TypeError
    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": lambda p: RespostaFake(200, json_data=[quebrado]),
                                  "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[])})
    s.search(["turismo"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo) == ("error", "erro_interno")
    assert "TypeError" in st.detalhe
```

(10 testes; 9 passam nesta task, 1 `xfail strict` que a T4 destrava. Suíte: 16 + 10 = 26 coletados; `pytest -q` imprime **`25 passed, 1 xfailed`** e o runner lê **25**.)

- [ ] **Step 2: Ver falhar** — `python -m pytest tests/test_fontes_indisponiveis.py -q -k tcu` → falhas de status/motivo (o `xfail` aparece como `xfailed`).

- [ ] **Step 3: `tcu_searcher.py`**

**3a.** Imports: `from searchers.base import BaseSearcher, FonteIndisponivel, ProgressCallback`; conferir `import time`, `import re` (acrescentar se faltar) e acrescentar `from datetime import datetime`, `from zoneinfo import ZoneInfo` e `from urllib.parse import urlencode`. Em `requirements.txt`: `tzdata  # ZoneInfo no Windows nao tem base tz do sistema (rodada 3)`. Na classe, após `RATE_LIMIT_JITTER = 0.5`: `SOURCE_ID = "tcu"`.

**3b.** `_request_with_retry` — reescrever:

```python
    def _request_with_retry(self, url: str, params: dict) -> dict | list:
        """Send GET request with exponential backoff retry on 5xx/network.

        Returns:
            Parsed JSON (dict or list).

        Raises:
            FonteIndisponivel: com o motivo pela classe do erro (H6):
                503 -> manutencao_503 (sem retry; hora em BRT + hipotese da janela 20h-21h);
                404 -> endpoint_inexistente, 429 -> rate_limit, outro 4xx -> http_4xx (sem retry);
                5xx apos MAX_RETRIES -> http_5xx; timeout/conexao apos MAX_RETRIES;
                200 que nao e JSON -> bloqueio_waf (pagina de desafio) ou resposta_ilegivel.
            Antes devolvia None e o chamador tratava None como "fim das paginas":
            um 500 virava "sem resultado" (medido em 22/09). Detalhe: fato
            primeiro, URL (com query) por ultimo.
        """
        ultimo: Optional[Exception] = None
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            except requests.exceptions.Timeout as e:
                ultimo = e
            except requests.exceptions.ConnectionError as e:
                ultimo = e
            except requests.exceptions.RequestException as e:
                raise FonteIndisponivel("erro_interno", f"{type(e).__name__}: {str(e)[:120]} | GET {url}") from e
            else:
                efetiva = getattr(response, "url", None) or url
                sc = response.status_code
                if sc == 503:
                    agora = datetime.now(ZoneInfo("America/Sao_Paulo"))   # naive em servidor UTC erraria a janela (R2)
                    janela = "dentro" if 20 <= agora.hour < 21 else "fora"
                    raise FonteIndisponivel("manutencao_503",
                        f"HTTP 503 às {agora:%d/%m %H:%M} BRT ({janela} da janela de manutenção conhecida, 20h-21h); "
                        f"hipótese, não fato | GET {efetiva}")
                if sc == 404:
                    raise FonteIndisponivel("endpoint_inexistente", f"HTTP 404 | GET {efetiva}")
                if sc == 429:
                    raise FonteIndisponivel("rate_limit", f"HTTP 429 | GET {efetiva}")
                if 400 <= sc < 500:
                    raise FonteIndisponivel("http_4xx", f"HTTP {sc} | GET {efetiva}")
                if sc >= 500:
                    ultimo = requests.HTTPError(f"{sc}", response=response)
                else:
                    return self._exigir_json(response, efetiva)
            if attempt < MAX_RETRIES - 1:
                delay = 2 ** (attempt + 1)  # 2s, 4s, 8s
                logger.warning(f"TCU API error (attempt {attempt + 1}/{MAX_RETRIES}): {ultimo}. Retrying in {delay}s...")
                time.sleep(delay)
        logger.error(f"TCU API failed after {MAX_RETRIES} attempts: {ultimo}")
        if isinstance(ultimo, requests.exceptions.Timeout):   # ANTES de ConnectionError: ConnectTimeout herda dos dois
            raise FonteIndisponivel("timeout", f"sem resposta em {REQUEST_TIMEOUT}s x {MAX_RETRIES} | GET {url}?{urlencode(params)}")
        if isinstance(ultimo, requests.exceptions.ConnectionError):
            raise FonteIndisponivel("conexao", f"conexao recusada/sem rota ({str(ultimo)[:120]}) | GET {url}?{urlencode(params)}")
        resp = getattr(ultimo, "response", None)
        corpo = (getattr(resp, "text", "") or "")[:160]
        raise FonteIndisponivel("http_5xx",
            f"HTTP {getattr(resp, 'status_code', '?')} em {MAX_RETRIES} tentativas; corpo: {corpo!r} | GET {getattr(resp, 'url', url)}")

    def _exigir_json(self, response, url: str):
        """200 que nao e JSON e falha declarada, nao 'sem resultado' (H6)."""
        try:
            return response.json()
        except ValueError as e:   # requests.JSONDecodeError e ValueError
            corpo = (response.text or "").lstrip("\ufeff \t\r\n")
            ct = (response.headers.get("Content-Type") or "").lower()
            titulo = re.search(r"<title>([^<]*)</title>", corpo)
            fato = f"HTTP 200 {ct or 'sem content-type'} nao e JSON"
            if titulo:
                fato += f"; título: {titulo.group(1).strip()}"
            detalhe = f"{fato}; corpo: {corpo[:120]!r} | GET {url}"
            texto = corpo.lower()
            if "verificação de segurança" in texto or "verificacao de seguranca" in texto or "challenge" in texto:
                raise FonteIndisponivel("bloqueio_waf", detalhe) from e
            raise FonteIndisponivel("resposta_ilegivel", detalhe) from e
```

**3c.** `_fetch_all_pages` e `_fetch_all_pages_safe` → `(itens, erro, parcial)`:

```python
    def _fetch_all_pages(self, url: str) -> tuple[list[dict], Optional[FonteIndisponivel], bool]:
        """Fetch all pages from a paginated TCU API endpoint.

        Stops at MAX_PAGES * PAGE_SIZE records to avoid excessive requests.

        Returns:
            (itens, erro, parcial). Primeira pagina falhou -> ([], erro, False).
            Pagina seguinte falhou -> (o que veio, erro, True): "achei 40, a
            fonte caiu na pagina 3" e diferente de "achei 40". Antes, qualquer
            falha era `break` silencioso ("return what we have").
        """
        all_items: list[dict] = []
        offset = 0
        for page in range(MAX_PAGES):
            params = {"inicio": offset, "quantidade": PAGE_SIZE}
            try:
                data = self._request_with_retry(url, params)
            except FonteIndisponivel as e:
                if page == 0:
                    return [], e, False
                e.detalhe = f"pagina {page + 1} (inicio={offset}): {e.motivo}: {e.detalhe}"
                return all_items, e, True
            items = data if isinstance(data, list) else data.get("items", data.get("data", []))
            if not isinstance(items, list):
                erro = FonteIndisponivel("resposta_ilegivel", f"formato inesperado {type(data).__name__} | GET {url}?inicio={offset}")
                return all_items, erro, page > 0
            all_items.extend(items)
            if len(items) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
            self._rate_limit()
        return all_items, None, False

    def _fetch_all_pages_safe(self, url: str) -> tuple[list[dict], Optional[FonteIndisponivel], bool]:
        """Como _fetch_all_pages, mas nenhuma excecao escapa: bug nosso vira
        erro_interno declarado, nunca "sem resultado"."""
        try:
            return self._fetch_all_pages(url)
        except Exception as e:
            logger.error(f"TCU: erro interno em {url}: {e}")
            return [], FonteIndisponivel("erro_interno", f"{type(e).__name__}: {e}"[:200]), False
```

**3d.** `search()` — substituir **de** `acordao_items, acordao_error = self._fetch_all_pages_safe(` (**`:72`**, a linha que abre a chamada; a URL está em `:73` e o `)` em `:74`) **até a última linha do `for keyword in keywords:`** (`:137`, o `))` que fecha o `KeywordStatus(... status="ok")`), **inclusive os dois extremos, mantendo** o que vem depois (`# Final callback`, o `progress_callback` final e `return list(results_by_id.values())`):

```python
        acordao_items, acordao_erro, acordao_parcial = self._fetch_all_pages_safe(f"{API_BASE_URL}{ACORDAOS_PATH}")
        logger.info(f"TCU: {len(acordao_items)} acordaos fetched, filtering by keywords")

        if progress_callback:
            progress_callback(1, total_steps, "TCU: buscando atos normativos")
        logger.info("TCU: fetching atos normativos")
        atos_items, atos_erro, atos_parcial = self._fetch_all_pages_safe(f"{API_BASE_URL}{ATOS_PATH}")
        logger.info(f"TCU: {len(atos_items)} atos normativos fetched, filtering by keywords")

        def _sem_sumario(item) -> bool:
            # R3-B1: olha o CAMPO (titulo esta sempre preenchido e nao diz nada), e e
            # DEFENSIVO — roda fora do try por keyword; item malformado conta como
            # "sem sumario" aqui e vira erro_interno la dentro, nunca derruba search()
            try:
                return not str(item.get("sumario") or item.get("ementa") or "").strip()
            except Exception:
                return True
        sem_sumario = sum(1 for i in acordao_items if _sem_sumario(i))

        def _resumo(nome, itens, erro, parcial, extra=""):
            if erro is not None and not itens:
                return f"{nome}: {erro.motivo} em {erro.detalhe}"
            if parcial:
                return f"{nome}: parcial ({len(itens)} itens{extra}; {erro.detalhe})"
            return f"{nome}: ok ({len(itens)} itens{extra})"

        # R2-H5/R3: acordaos recentes chegam SEM sumario — nesses so o titulo casa;
        # "ok (500 itens)" sugeriria 500 avaliados por texto
        detalhe = "; ".join([
            _resumo("Acórdãos", acordao_items, acordao_erro, acordao_parcial,
                    f", {sem_sumario} sem sumário — nesses só o título casa" if acordao_items else ""),
            _resumo("Atos", atos_items, atos_erro, atos_parcial),
        ])
        # Um endpoint que caiu na PRIMEIRA pagina torna a busca "error" mesmo que
        # o outro tenha respondido: o usuario precisa saber que metade da fonte
        # nao foi vista. Resultados do endpoint vivo continuam entrando — e por
        # isso a coleta e PARCIAL (R2).
        erro_primario = next((e for e, itens in ((acordao_erro, acordao_items), (atos_erro, atos_items))
                              if e is not None and not itens), None)
        parcial = acordao_parcial or atos_parcial or (erro_primario is not None and bool(acordao_items or atos_items))

        for idx, keyword in enumerate(keywords):
            if len(results_by_id) >= max_results:
                for restante in keywords[idx:]:   # M4
                    self.keyword_statuses.append(KeywordStatus(
                        keyword=restante, source=self.SOURCE_ID, result_count=0, status="error", motivo="nao_consultada",
                        detalhe=f"busca parou em max_results={max_results} antes desta palavra-chave"))
                break
            kw_count = 0
            try:
                for item in acordao_items:
                    if len(results_by_id) >= max_results:
                        break
                    if self._matches_keyword(self._texto_do_acordao(item), keyword):
                        result = self._map_acordao(item, keyword)
                        if result.id not in results_by_id:
                            results_by_id[result.id] = result
                            kw_count += 1
                for item in atos_items:
                    if len(results_by_id) >= max_results:
                        break
                    if self._matches_keyword(item.get("ementa", ""), keyword):
                        result = self._map_ato_normativo(item, keyword)
                        if result.id not in results_by_id:
                            results_by_id[result.id] = result
                            kw_count += 1
            except Exception as e:   # H2: mapeamento que quebra nao derruba a fonte
                self.keyword_statuses.append(KeywordStatus(
                    keyword=keyword, source=self.SOURCE_ID, result_count=kw_count, status="error", motivo="erro_interno",
                    detalhe=f"{type(e).__name__}: {e}"[:200], error_message=f"{type(e).__name__}: {e}"[:200]))
                continue

            if erro_primario is not None:
                status, motivo = "error", erro_primario.motivo
            elif kw_count == 0:
                status, motivo = "empty", ""
            else:
                status, motivo = "ok", ""
            self.keyword_statuses.append(KeywordStatus(
                keyword=keyword, source=self.SOURCE_ID, result_count=kw_count, status=status, motivo=motivo,
                detalhe=detalhe,   # R3-H5: SEMPRE — "empty" com 500 acordaos sem sumario nao e "nao ha acordao"
                error_message=detalhe if status == "error" else "", parcial=parcial))
```

**3e.** Método novo — colar **depois** do `return list(results_by_id.values())` de `search()` e **antes** de `_matches_keyword` (R2-H4: na v2 este método ficava dentro do bloco anterior e engolia o rabo de `search()`):

```python
    def _texto_do_acordao(self, item: dict) -> str:
        """Texto onde a palavra-chave e procurada. Ate a T4: `ementa` (que a API
        real nao devolve — ver tests/fixtures/tcu_acordaos_real.json)."""
        return item.get("ementa", "") or ""
```

Docstring de `search()`: acrescentar `Um endpoint que falha na primeira pagina marca status="error" para toda palavra-chave (com result_count do endpoint que respondeu e parcial=True); paginacao interrompida marca parcial=True; palavra-chave pulada pelo cap marca nao_consultada.`

- [ ] **Step 4: Adaptar `test_comprehensive.py:473-477`** (B3): `s._fetch_all_pages = lambda url: []` → `s._fetch_all_pages = lambda url: ([], None, False)`, com a docstring do teste ganhando `Contrato de _fetch_all_pages mudou na frente 2 (2026-09-22): (itens, erro, parcial).` Conferir com `git grep -n "_fetch_all_pages\|_request_with_retry" -- '*.py'` que não há outro call site.

- [ ] **Step 5: Ver passar** — suíte nova `25 passed, 1 xfailed`; `python test_comprehensive.py` → 98/98; `python test_searchers.py` → 13/13.

- [ ] **Step 6: BASELINE** `tests/test_fontes_indisponiveis.py = 25`; runner TUDO VERDE; golden OK.

- [ ] **Step 7: Auditoria + commit**

```bash
git add levantamento-normativos/searchers/tcu_searcher.py levantamento-normativos/requirements.txt levantamento-normativos/test_comprehensive.py levantamento-normativos/tests/ tools/run_all_tests.py
git commit -m "feat(frente2): TCU classifica 5xx/4xx/503/HTML e declara paginacao parcial

_request_with_retry levanta FonteIndisponivel por classe de erro (4xx sem
retry; 503 com hora BRT e hipotese marcada; 200 nao-JSON e bloqueio ou
ilegivel); _fetch_all_pages devolve (itens, erro, parcial). Um endpoint
caido marca error E parcial mesmo com o outro ok; item que quebra o
mapeamento vira erro_interno por keyword; keyword pulada pelo cap vira
nao_consultada; o detalhe (gravado sempre) conta acordaos sem sumario.
Fixture: 2 acordaos REAIS de 22/09. test_comprehensive adaptado (98).
Suite: 16 -> 25 (+1 xfail para a T4)."
git push origin master
```

---

### Task 4: TCU — mapear o esquema REAL do acórdão (⚠ emenda à spec §3.7)

✅ **Fato medido em 22/09** (`tests/fixtures/tcu_acordaos_real.json`, `curl` em `recupera-acordaos?quantidade=2`): as chaves são `anoAcordao, colegiado, dataSessao, key, numeroAcordao, numeroAta, relator, situacao, sumario, tipo, titulo, urlAcordao, urlArquivo, urlArquivoPdf`. **Não existem `ementa`, `numero`, `ano`** — as três chaves que `_map_acordao` lê (`tcu_searcher.py:265-266,279`) e a que o filtro usa (`:104`). Consequência na v1.0: todo acórdão mapeia para `nome="Acordao / - TCU - Plenário"`, `numero="/"`, mesmo `id`, e **nunca casa palavra-chave** — a fonte diz "ok (500 itens)" e entrega zero. A spec §3.7 dizia "nenhum searcher muda o que mapeia"; **essa regra cai aqui**, porque manter o mapeamento é manter uma fonte estruturalmente cega. Decisão do Rodrigo em 22/09: "todos os consertos da v1 entram".

✅ **Limite medido pela rodada 2 (ao vivo):** `sumario` vem **nulo em 20/20** acórdãos das sessões mais recentes e em ~40% da janela de 500 registros; `titulo` é só "ACÓRDÃO N/AAAA ATA X/AAAA - PLENÁRIO". Ou seja: depois desta task, casam os acórdãos **que a API já preencheu** — a contagem "N sem texto" do detalhe (T3) é o que diz isso ao usuário. Não é "voltaram a casar"; é "deixaram de ser invisíveis".

📝 **Mapeamento** (literal, sem parafrasear): `nome ← titulo`; `numero ← f"{numeroAcordao}/{anoAcordao}"`; `data ← dataSessao` (⚠ R3: a precedência **inverte** — antes era `dataAta or dataSessao`; a API real só tem `dataSessao`; e o vazio continua `""`, **não** `None`, porque `data` entra no `id` e `None` mudaria o id de todo acórdão sem data); `orgao_emissor ← f"TCU - {colegiado}"`; `ementa ← sumario`; `link ← urlAcordao` (fallback `_build_acordao_link`); `situacao ← situacao` (a API traz `"OFICIALIZADO"` em 100% dos medidos — vai literal; a docstring de `NormativoResult.situacao` passa a admitir "o valor literal da fonte"). O filtro procura em `sumario` **e** `titulo`. Chaves antigas continuam aceitas como fallback.

**Files:** `tcu_searcher.py` (`_map_acordao`, `_texto_do_acordao`); `models.py` (docstring de `situacao`); `tests/test_fontes_indisponiveis.py`; `tools/run_all_tests.py`; spec §3.7.

- [ ] **Step 1: Testes** — (a) remover o decorator `@pytest.mark.xfail(...)` de `test_tcu_item_que_quebra_o_mapeamento_vira_erro_interno_declarado`; (b) em `test_tcu_500_num_endpoint_e_error_parcial_mesmo_com_o_outro_ok` trocar `assert len(resultados) == 0` por `assert len(resultados) == 1` (o acórdão real casa "turismo" no sumário); (c) acrescentar:

```python
def test_tcu_acordao_real_mapeia_titulo_numero_ano_sumario_link_situacao():
    from searchers.tcu_searcher import TCUSearcher
    r = TCUSearcher()._map_acordao(ACORDAO, "turismo")
    assert r.nome == ACORDAO["titulo"]
    assert r.numero == f'{ACORDAO["numeroAcordao"]}/{ACORDAO["anoAcordao"]}'
    assert r.data == ACORDAO["dataSessao"]
    assert r.ementa == ACORDAO["sumario"]          # literal, sem parafrase
    assert r.link == ACORDAO["urlAcordao"]
    assert r.orgao_emissor == f'TCU - {ACORDAO["colegiado"]}'
    assert r.situacao == ACORDAO["situacao"]


def test_tcu_acordaos_reais_tem_ids_distintos_e_casam_o_sumario(monkeypatch):
    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": lambda p: RespostaFake(200, json_data=ACORDAOS_REAIS),
                                  "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[])})
    resultados = s.search(["turismo"], max_results=10)
    ids = {s._map_acordao(a, "x").id for a in ACORDAOS_REAIS}
    assert len(ids) == len(ACORDAOS_REAIS)
    assert len(resultados) >= 1 and all("TURISMO" in (r.ementa + r.nome).upper() for r in resultados)


def test_tcu_pagina_cheia_com_numeros_distintos_da_page_size_resultados(monkeypatch):
    from searchers import tcu_searcher
    pagina = [dict(ACORDAO, key=f"A-{i}", numeroAcordao=str(i), titulo=f"ACÓRDÃO {i}/2026 - TURISMO") for i in range(tcu_searcher.PAGE_SIZE)]
    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": lambda p: RespostaFake(200, json_data=pagina if p["inicio"] == 0 else []),
                                  "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[])})
    resultados = s.search(["turismo"], max_results=100)
    assert len(resultados) == tcu_searcher.PAGE_SIZE
    assert len({r.id for r in resultados}) == tcu_searcher.PAGE_SIZE
```

- [ ] **Step 2: Ver falhar** — `-k "acordao_real or pagina_cheia or quebra_o_mapeamento or 500_num"` → 4 failed. E em `test_comprehensive.py`, no teste `test_tcu_map_acordao_missing_fields` (`:465-468`), acrescentar `assert r.data == ""` (R3: fixa que o vazio continua `""`).

- [ ] **Step 3: Implementar** — em `tcu_searcher.py`:

```python
    def _texto_do_acordao(self, item: dict) -> str:
        """Onde a palavra-chave e procurada: sumario + titulo (esquema real da
        API, medido em 22/09) — com fallback para `ementa` se a API tiver dois
        formatos. Antes lia so `ementa`, que a API nao devolve: zero match, sempre.
        Acordaos recentes vem SEM sumario (medido): so o titulo casa neles."""
        return " ".join(x for x in (item.get("sumario"), item.get("titulo"), item.get("ementa")) if x)

    def _map_acordao(self, item: dict, found_by: str) -> NormativoResult:
        """Map a raw acordao JSON item (esquema real de 22/09) to a NormativoResult.

        Campos literais da API, sem parafrase: titulo -> nome, sumario -> ementa,
        numeroAcordao/anoAcordao -> numero, dataSessao -> data, urlAcordao -> link,
        situacao -> situacao. Chaves antigas (numero/ano/ementa) aceitas como fallback.

        Returns:
            NormativoResult with tipo="Acordao TCU".
        """
        numero = str(item.get("numeroAcordao") or item.get("numero") or "")
        ano = str(item.get("anoAcordao") or item.get("ano") or "")
        colegiado = item.get("colegiado", "")
        date_raw = item.get("dataSessao") or item.get("dataAta") or ""   # precedencia invertida de proposito (API real)
        date_str = self._safe_date_format(str(date_raw)) if date_raw else ""  # "" e nao None: `data` entra no id
        return NormativoResult(
            nome=item.get("titulo") or f"Acordao {numero}/{ano} - TCU - {colegiado}",
            tipo="Acordao TCU",
            numero=f"{numero}/{ano}",
            data=date_str,
            orgao_emissor=f"TCU - {colegiado}",
            ementa=item.get("sumario") or item.get("ementa", "") or "",
            link=item.get("urlAcordao") or self._build_acordao_link(numero, ano),
            source="tcu",
            found_by=found_by,
            situacao=item.get("situacao") or "Nao identificado",
            relevancia=0.5,
            raw_data=item,
        )
```

Em `models.py`, docstring de `NormativoResult.situacao`: `"Vigente", "Revogado" ou "Nao identificado" (default)` → `"Vigente", "Revogado", "Nao identificado" (default) ou o valor literal da fonte (ex.: "OFICIALIZADO" do TCU).`

- [ ] **Step 4: Ver passar** — suíte `29 passed` (26 coletados na T3, o xfail vira passed, + 3 novos). `test_comprehensive` 98/98; `test_searchers` 13/13 (✅ rodada 2 verificou: nenhum teste antigo afirma o nome antigo; `test_comprehensive:424-441,461-468` passam pelo fallback). Golden OK (o corpus fixo não passa por `_map_acordao`).

- [ ] **Step 5: BASELINE 29; spec; commit**

Na spec §3.7: `> ⚠ Emendado em 22/09 (plano v3, T4): o mapeamento do acórdão do TCU MUDA — a API real não devolve as chaves que o código lia. Ver a fixture real. Limite medido: sumário vazio nos acórdãos recentes.`

```bash
git add levantamento-normativos/searchers/tcu_searcher.py levantamento-normativos/models.py levantamento-normativos/test_comprehensive.py levantamento-normativos/tests/ tools/run_all_tests.py docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md
git commit -m "fix(frente2): TCU le o esquema REAL do acordao (titulo/sumario/numeroAcordao/anoAcordao/urlAcordao/situacao)

Medido em 22/09: a API nao devolve ementa/numero/ano; _map_acordao lia so
essas chaves, entao todo acordao colapsava num id e nunca casava
palavra-chave. Emenda a spec 3.7. Textos literais, sem parafrase. Limite
medido (rodada 2): acordaos recentes chegam sem sumario — o detalhe conta
'N sem sumario'. Data vazia continua \"\" (id preservado). Suite: 25 -> 29."
git push origin master
```

---

### Task 5: Google/DDG — vocabulário mínimo (⚠ emenda à spec §5)

**Files:** `searchers/google_searcher.py` — imports (`:13-23`: **acrescentar `from typing import Optional`** — o módulo não tem `from __future__ import annotations`; sem isso o app inteiro não importa, R3-B2); classe (`SOURCE_ID`); `_search_urls` (`:127-143`); `_search_ddgs` (`:145-167`); `_search_cse_api` (`:169-205`); `_search_scraping` (`:207-215`); `search()` laço principal (`:252-271`) **e laço de retry inteiro (`:344-403`)**; callback final; `tests/test_fontes_indisponiveis.py`; `tools/run_all_tests.py`.

**Interfaces — Produces:** `GoogleSearcher.SOURCE_ID = "google"`; `_search_urls(keyword) -> tuple[list[dict], Optional[FonteIndisponivel]]` (era `(list, str)`); `DDGSException("No results found.")` → lista vazia **sem** erro.

- [ ] **Step 1: Testes** (8):

```python
# ---------------------------------------------------------------------------
# Google / DuckDuckGo (M5)
# ---------------------------------------------------------------------------

def _ddg_com(monkeypatch, text_impl):
    """text_impl(query) -> lista de dicts (ou levanta). Dubla ddgs.DDGS (import tardio dentro de _search_ddgs)."""
    from searchers import google_searcher
    monkeypatch.setattr(google_searcher, "_BACKEND", "ddgs")

    class DDGSFake:
        def text(self, query, max_results=10):
            return text_impl(query)

    import ddgs
    monkeypatch.setattr(ddgs, "DDGS", DDGSFake)
    return google_searcher.GoogleSearcher()


def _um_resultado(q):
    return [{"href": f"https://www.gov.br/{abs(hash(q)) % 10**6}", "title": f"Guia {q}", "body": "texto"}]


def test_ddg_no_results_e_empty_nao_error(monkeypatch):
    from ddgs.exceptions import DDGSException
    def sem(q): raise DDGSException("No results found.")
    s = _ddg_com(monkeypatch, sem)
    s.search(["x"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo, st.source) == ("empty", "", "google")


def test_ddg_timeout_e_ratelimit_mapeiam_motivo(monkeypatch):
    from ddgs.exceptions import TimeoutException, RatelimitException
    def lento(q): raise TimeoutException("t")
    s = _ddg_com(monkeypatch, lento); s.search(["x"], max_results=5)
    assert s.keyword_statuses[0].motivo == "timeout"
    def cota(q): raise RatelimitException("r")
    s2 = _ddg_com(monkeypatch, cota); s2.search(["x"], max_results=5)
    assert s2.keyword_statuses[0].motivo == "rate_limit"


def test_ddg_erro_generico_e_erro_interno(monkeypatch):
    def bug(q): raise KeyError("href")
    s = _ddg_com(monkeypatch, bug); s.search(["x"], max_results=5)
    assert s.keyword_statuses[0].motivo == "erro_interno"


def test_google_keywords_alem_de_5_ganham_nao_consultada(monkeypatch):
    s = _ddg_com(monkeypatch, lambda q: [])
    s.search([f"k{i}" for i in range(7)], max_results=50)
    nao = [st for st in s.keyword_statuses if st.motivo == "nao_consultada"]
    assert [st.keyword for st in nao] == ["k5", "k6"]
    assert "MAX_GOOGLE_KEYWORDS=5" in nao[0].detalhe
    assert len(s.keyword_statuses) == 7


def test_google_cap_de_max_results_dentro_das_5_tambem_e_nao_consultada(monkeypatch):
    """R3-H2: o break por max_results dentro das 5 ativas nao pode sumir com keywords."""
    s = _ddg_com(monkeypatch, _um_resultado)
    s.search([f"k{i}" for i in range(7)], max_results=2)
    assert len(s.keyword_statuses) == 7
    assert [st.status for st in s.keyword_statuses[:2]] == ["ok", "ok"]
    assert all(st.motivo == "nao_consultada" for st in s.keyword_statuses[2:])
    assert "max_results=2" in s.keyword_statuses[2].detalhe and "MAX_GOOGLE_KEYWORDS" in s.keyword_statuses[5].detalhe


def test_ddg_retry_que_da_certo_zera_motivo(monkeypatch):
    """R2-H3: o laco de retry tambem fala FonteIndisponivel, senao a aba diz 'Sem resultado · timeout'."""
    from ddgs.exceptions import TimeoutException
    vez = {"n": 0}
    def uma_vez(q):
        vez["n"] += 1
        if vez["n"] == 1:
            raise TimeoutException("t")
        return [{"href": "https://www.gov.br/x", "title": "Guia", "body": "texto"}]
    s = _ddg_com(monkeypatch, uma_vez)
    resultados = s.search(["x"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo, st.retried, st.result_count) == ("ok", "", True, 1)
    assert st.detalhe == "recuperado no retry após timeout"
    assert len(resultados) == 1


def test_ddg_retry_pulado_nao_marca_retried(monkeypatch):
    """R3-H1: so a 1a keyword e reenviada; as outras NAO podem sair 'Retentado: Sim'."""
    from ddgs.exceptions import TimeoutException
    def sempre(q): raise TimeoutException("t")
    s = _ddg_com(monkeypatch, sempre)
    s.search(["a", "b", "c"], max_results=5)
    assert [st.retried for st in s.keyword_statuses] == [True, False, False]
    assert all(st.motivo == "timeout" for st in s.keyword_statuses)
    assert all("retry pulado" in st.detalhe for st in s.keyword_statuses[1:])


def test_cse_200_nao_json_e_resposta_ilegivel(monkeypatch):
    """R2-H3 (CSE): 200 que nao e JSON caia num handler que assumia e.response."""
    from searchers import google_searcher
    monkeypatch.setattr(google_searcher, "_BACKEND", "cse")
    monkeypatch.setattr("searchers.google_searcher.requests.get",
                        lambda url, params=None, timeout=None, **kw: RespostaFake(200, "<html>oi</html>", "text/html", url=url + "?key=AIzaSECRET&cx=1"))
    s = google_searcher.GoogleSearcher()
    s.search(["x"], max_results=5)
    st = s.keyword_statuses[0]
    assert st.motivo == "resposta_ilegivel" and "AIzaSECRET" not in st.detalhe
```

- [ ] **Step 2: Ver falhar.**

- [ ] **Step 3: Implementar**

**3a.** Imports: `from typing import Optional` (**novo — R3-B2**) e `from searchers.base import BaseSearcher, FonteIndisponivel, ProgressCallback`. Na classe: `SOURCE_ID = "google"`.

**3b.** `_search_urls` (`:127-143`) — inteira:

```python
    def _search_urls(self, keyword: str) -> tuple[list[dict], Optional[FonteIndisponivel]]:
        """Search for results matching the keyword.

        Returns:
            (results, erro). Each result is a dict with keys: url, title, snippet.
            erro e None em sucesso (inclusive "sem resultado"); FonteIndisponivel
            quando a fonte nao pode ser consultada (frente 2).
        """
        if _BACKEND == "cse":
            return self._search_cse_api(keyword)
        elif _BACKEND == "ddgs":
            return self._search_ddgs(keyword)
        elif _BACKEND == "scraping":
            return self._search_scraping(keyword)
        else:
            return [], FonteIndisponivel("erro_interno", "Nenhum backend de busca disponivel. Instale 'ddgs': pip install ddgs")
```

**3c.** `_search_ddgs` — corpo do `try` inteiro:

```python
        try:
            raw_results = list(DDGS().text(query, max_results=RESULTS_PER_QUERY))
        except Exception as e:
            from ddgs.exceptions import DDGSException, RatelimitException, TimeoutException
            if isinstance(e, RatelimitException):          # subclasse de DDGSException: testar ANTES
                return [], FonteIndisponivel("rate_limit", f"DuckDuckGo: {e}")
            if isinstance(e, TimeoutException):
                return [], FonteIndisponivel("timeout", f"DuckDuckGo: {e}")
            if isinstance(e, DDGSException) and "no results" in str(e).lower():
                return [], None   # M5: "No results found." e resultado legitimo, nao falha (ddgs 9.12, ddgs.py:215)
            return [], FonteIndisponivel("erro_interno", f"DuckDuckGo: {type(e).__name__}: {e}")
        return [{"url": r.get("href", ""), "title": r.get("title", ""), "snippet": r.get("body", "")} for r in raw_results], None
```

Tipo de retorno na assinatura: `-> tuple[list[dict], Optional[FonteIndisponivel]]`.

**3d.** `_search_cse_api` — bloco `try` inteiro (assinatura idem):

```python
        try:
            response = requests.get(CSE_API_URL, params=params, timeout=CSE_TIMEOUT)
            efetiva = getattr(response, "url", CSE_API_URL)   # redigida pelo KeywordStatus/FonteIndisponivel
            sc = response.status_code
            if sc == 429:
                return [], FonteIndisponivel("rate_limit", f"HTTP 429 — cota diária excedida (100 queries/dia no plano gratuito) | GET {efetiva}")
            if sc == 403:
                return [], FonteIndisponivel("http_4xx", f"HTTP 403 — acesso negado (verifique GOOGLE_API_KEY e GOOGLE_CSE_ID) | GET {efetiva}")
            if sc == 404:
                return [], FonteIndisponivel("endpoint_inexistente", f"HTTP 404 | GET {efetiva}")
            if 400 <= sc < 500:
                return [], FonteIndisponivel("http_4xx", f"HTTP {sc} | GET {efetiva}")
            if sc >= 500:
                return [], FonteIndisponivel("http_5xx", f"HTTP {sc}; corpo: {(response.text or '')[:120]!r} | GET {efetiva}")
            try:
                data = response.json()
            except ValueError:   # R2-H3: 200 nao-JSON caia num handler que assumia e.response
                return [], FonteIndisponivel("resposta_ilegivel", f"HTTP 200 nao e JSON; corpo: {(response.text or '')[:120]!r} | GET {efetiva}")
            results = [{"url": i.get("link", ""), "title": i.get("title", ""), "snippet": i.get("snippet", "")}
                       for i in data.get("items", [])]
            return results, None
        except requests.exceptions.Timeout:
            return [], FonteIndisponivel("timeout", f"sem resposta em {CSE_TIMEOUT}s | GET {CSE_API_URL}")
        except requests.exceptions.ConnectionError as e:
            return [], FonteIndisponivel("conexao", f"conexao recusada/sem rota ({str(e)[:120]}) | GET {CSE_API_URL}")
        except Exception as e:
            return [], FonteIndisponivel("erro_interno", f"Google CSE: {type(e).__name__}: {e}")
```

**3e.** `_search_scraping` — inteira:

```python
    def _search_scraping(self, keyword: str) -> tuple[list[dict], Optional[FonteIndisponivel]]:
        """Search using googlesearch-python (scraping, no API key needed)."""
        from googlesearch import search as google_search

        query = f"{keyword} {SITE_RESTRICTION}"
        try:
            urls = list(google_search(query, num_results=RESULTS_PER_QUERY, lang="pt"))
            return [{"url": u, "title": "", "snippet": ""} for u in urls], None
        except Exception as e:
            return [], FonteIndisponivel("erro_interno", f"googlesearch: {type(e).__name__}: {e}")
```

**3f.** Laço principal — substituir de `if len(results) >= max_results:` / `break` (`:253-254`) até `continue` do bloco `if error_msg:` (`:271`):

```python
            if len(results) >= max_results:
                # R3-H2 (M4): keyword nunca enviada nao pode sumir do relatorio
                for restante in active_keywords[idx:]:
                    self.keyword_statuses.append(KeywordStatus(
                        keyword=restante, source=self.SOURCE_ID, result_count=0, status="error", motivo="nao_consultada",
                        detalhe=f"busca parou em max_results={max_results} antes desta palavra-chave"))
                break

            if progress_callback:
                progress_callback(idx, total_steps, f"Google: buscando '{keyword}'")

            logger.info(f"Google [{idx+1}/{total_steps}]: buscando '{keyword}'")

            search_results, erro = self._search_urls(keyword)

            if erro is not None:
                logger.warning(f"Google search failed for '{keyword}': {erro}")
                self.keyword_statuses.append(KeywordStatus(
                    keyword=keyword, source=self.SOURCE_ID, result_count=0,
                    status="error", error_message=str(erro), motivo=erro.motivo, detalhe=erro.detalhe,
                ))
                failed_keywords.append(keyword)
                continue
```

O bloco "Detect possible blocking (scraping mode only)" (`:275-292`) ganha `motivo="bloqueio_waf"` no `KeywordStatus`. Todos os `KeywordStatus(... source="google"` do arquivo → `source=self.SOURCE_ID`.

**3g.** Laço de retry — substituir **inteiro**, de `# --- Retry failed keywords (max 3, bail if API is down) ---` (`:344`) até `self._rate_limit()` (`:403`, o último do laço), **inclusive**, por:

```python
        # --- Retry failed keywords (max 3, bail if API is down) ---
        MAX_RETRIES = 3
        if failed_keywords:
            retry_count = min(len(failed_keywords), MAX_RETRIES)
            logger.info(f"Google: retrying {retry_count} of {len(failed_keywords)} failed keywords")
            import time
            time.sleep(5)

            api_still_down = False
            for keyword in failed_keywords[:MAX_RETRIES]:
                if len(results) >= max_results or api_still_down:
                    # R3-H1: sem requisicao NAO marca retried — so registra que pulou
                    for kws in self.keyword_statuses:
                        if kws.keyword == keyword and kws.source == self.SOURCE_ID and kws.status == "error":
                            motivo_pulo = "a retentativa anterior falhou" if api_still_down else "max_results atingido"
                            kws.detalhe = f"{kws.detalhe} | retry pulado: {motivo_pulo}"
                            break
                    continue

                search_results, erro = self._search_urls(keyword)
                for kws in self.keyword_statuses:
                    if kws.keyword == keyword and kws.source == self.SOURCE_ID and kws.status == "error":
                        kws.retried = True
                        if erro is not None:
                            kws.error_message = f"Retry failed: {erro}"
                            kws.motivo, kws.detalhe = erro.motivo, erro.detalhe
                            api_still_down = True
                        else:
                            recuperado = f"recuperado no retry após {kws.motivo}"   # ANTES de zerar o motivo
                            kw_count = 0
                            for sr in search_results:
                                if len(results) >= max_results:
                                    break
                                url = sr.get("url", "")
                                if not url:
                                    continue
                                normalized_url = self._normalize_url(url)
                                if normalized_url in seen_urls:
                                    continue
                                seen_urls.add(normalized_url)
                                title = sr.get("title", "")
                                description = sr.get("snippet", "")
                                if not title or not description:
                                    ft, fd = self._fetch_page_metadata(url)
                                    title = title or ft
                                    description = description or fd
                                org = self._extract_org(url)
                                results.append(NormativoResult(
                                    nome=title if title else url,
                                    tipo="Framework/Padrao", numero="", data=None,
                                    orgao_emissor=org, ementa=description, link=url,
                                    source="google", found_by=keyword, relevancia=0.3,
                                    raw_data={"url": url, "title": title, "description": description},
                                ))
                                kw_count += 1
                            kws.status = "ok" if kw_count > 0 else "empty"
                            kws.error_message, kws.motivo = "", ""
                            kws.detalhe = recuperado
                            kws.result_count = kw_count
                        break

                if not api_still_down:
                    self._rate_limit()

        # M4 (R2-H3): keyword alem de MAX_GOOGLE_KEYWORDS nunca foi enviada — nao pode sumir do relatorio.
        # Posicao pinada: DEPOIS do retry e ANTES do callback final (antes do laco ela era apagada
        # pela reinicializacao de keyword_statuses).
        for restante in keywords[MAX_GOOGLE_KEYWORDS:]:
            self.keyword_statuses.append(KeywordStatus(
                keyword=restante, source=self.SOURCE_ID, result_count=0, status="error", motivo="nao_consultada",
                detalhe=f"limite MAX_GOOGLE_KEYWORDS={MAX_GOOGLE_KEYWORDS} — palavra-chave não enviada à web aberta",
            ))
```

⚠ `git grep -n "_search_urls\|error_msg" -- levantamento-normativos/searchers/google_searcher.py levantamento-normativos/test_*.py` antes de fechar: nenhum resto de `error_msg`; se `test_searchers.py`/`test_comprehensive.py` afirmarem `_search_urls(...)[1] == ""` ou `error_message` literal do Google, adaptar no mesmo commit e registrar.

- [ ] **Step 4: Ver passar** — suíte `37 passed`; `test_searchers` 13/13; `test_comprehensive` 98/98; `python -c "from searchers import GoogleSearcher"` importa. BASELINE 37. Runner, golden. Commit `feat(frente2): Google/DDG entra no vocabulario — 'No results' e empty, nao error; retry honesto; cap declarado`. Push.

---

### Task 6: Origem da nota de relevância (`gemini_client.py`)

**Files:** `llm/gemini_client.py` (`:1-14` docstring de módulo; `:340-430`); `llm/__init__.py`; `test_llm_phase3.py` (seção 9, antes do `# Summary`); `tools/run_all_tests.py`.

**Interfaces — Produces:** `score_relevance_com_origem(topic, results, keywords=None) -> list[tuple[float, str]]`; `score_relevance` inalterada (wrapper); ambas exportadas por `llm/__init__.py`.

- [ ] **Step 1: Testes** — em `test_llm_phase3.py`, **antes** do bloco `# Summary` (10 `record`s):

```python
# ===========================================================================
# 9. Origem da nota (frente 2, spec 2026-09-22 §3.4)
# ===========================================================================
run_section("9. Origem da nota de relevancia")

try:
    from llm import score_relevance_com_origem
    from llm import gemini_client as _gc
    from models import ORIGENS_RELEVANCIA

    _docs = [{"nome": "Lei 13.709", "ementa": "Dispoe sobre protecao de dados pessoais e privacidade."},
             {"nome": "COBIT", "ementa": "Framework de governanca de TI."}]

    # sem chave (o topo do arquivo garante): heuristica
    pares = score_relevance_com_origem("tema", _docs, ["dados pessoais", "privacidade"])
    record("sem LLM devolve pares (nota, origem)", all(isinstance(p, tuple) and len(p) == 2 for p in pares))
    record("sem LLM a origem e 'heuristica'", all(o == "heuristica" for _, o in pares), str(pares))
    record("nota heuristica = fracao das keywords na ementa", abs(pares[0][0] - 1.0) < 1e-9 and pares[1][0] == 0.0, str(pares))
    record("toda origem esta em ORIGENS_RELEVANCIA", all(o in ORIGENS_RELEVANCIA for _, o in pares))

    # sem chave e sem keywords: nao ha o que calcular -> fallback_erro rotulado
    pares2 = score_relevance_com_origem("tema", _docs, None)
    record("sem LLM e sem keywords: 0.5 rotulado fallback_erro",
           all(p == (0.5, "fallback_erro") for p in pares2), str(pares2))

    # wrapper preserva o contrato antigo
    record("score_relevance == notas de score_relevance_com_origem",
           score_relevance("tema", _docs, ["dados pessoais", "privacidade"]) == [n for n, _ in pares])

    # com LLM "disponivel" mas lote vazio: fallback_erro (dublando is_available e _generate)
    _orig_avail, _orig_gen = _gc.is_available, _gc._generate
    try:
        _gc.is_available = lambda: True
        _gc._generate = lambda prompt, temperature=0.0, max_tokens=1024: ""
        pares3 = score_relevance_com_origem("tema", _docs, ["x"])
        record("lote vazio do modelo -> (0.5, fallback_erro)", all(p == (0.5, "fallback_erro") for p in pares3), str(pares3))

        _gc._generate = lambda prompt, temperature=0.0, max_tokens=1024: "[0.9, 0.1]"
        pares4 = score_relevance_com_origem("tema", _docs, ["x"])
        record("lote valido -> origem 'modelo'", pares4 == [(0.9, "modelo"), (0.1, "modelo")], str(pares4))

        _gc._generate = lambda prompt, temperature=0.0, max_tokens=1024: '[0.9, "abc"]'
        pares5 = score_relevance_com_origem("tema", _docs, ["x"])
        record("valor nao numerico -> so aquele item e fallback_erro",
               pares5 == [(0.9, "modelo"), (0.5, "fallback_erro")], str(pares5))

        _gc._generate = lambda prompt, temperature=0.0, max_tokens=1024: "[0.9]"
        pares6 = score_relevance_com_origem("tema", _docs, ["x"])
        record("tamanho errado -> lote inteiro fallback_erro", all(p == (0.5, "fallback_erro") for p in pares6), str(pares6))
    finally:
        _gc.is_available, _gc._generate = _orig_avail, _orig_gen
except Exception as e:
    record("secao 9 (origem da nota)", False, traceback.format_exc())
```

- [ ] **Step 2: Ver falhar** — `python test_llm_phase3.py | tail -5` → `Total: 54 | PASS: 53 | FAIL: 1` (a seção inteira cai no `except` com `ImportError`, um único `record` de falha).

- [ ] **Step 3: Implementar** — em `gemini_client.py`, **renomear** a atual `score_relevance` (`:340`) para `score_relevance_com_origem`, tipo de retorno `list[tuple[float, str]]`, e ajustar cada ponto que emite nota:

```python
    if not is_available():
        if keywords:
            logger.info("LLM indisponivel — heuristica por palavras-chave.")
            return [(_keyword_relevance(keywords, r.get("ementa", "")), "heuristica") for r in results]
        logger.info("LLM indisponivel e sem keywords — 0.5 rotulado como fallback_erro.")
        return [(0.5, "fallback_erro")] * len(results)
```

lote vazio (`:403-405`): `all_scores.extend([(0.5, "fallback_erro")] * len(batch))`; lote válido, dentro do `for val in parsed:`:

```python
                try:
                    score = max(0.0, min(1.0, float(val)))
                    batch_scores.append((score, "modelo"))
                except (TypeError, ValueError):
                    batch_scores.append((0.5, "fallback_erro"))
```

lote de tamanho errado (`:418-424`): `all_scores.extend([(0.5, "fallback_erro")] * len(batch))`.

Docstring da função nova — reescrever a atual acrescentando:

```
    Returns:
        Lista de (nota, origem), mesma ordem dos results. origem e um de
        models.ORIGENS_RELEVANCIA: "modelo" quando o LLM deu a nota;
        "heuristica" quando nao ha LLM e ha keywords; "fallback_erro" quando
        o LLM falhou (lote vazio, tamanho errado, valor nao numerico) ou nao
        ha nem LLM nem keywords. Antes, esses tres casos davam 0.5 sem marca.
```

Wrapper, logo abaixo:

```python
def score_relevance(
    topic: str,
    results: list[dict],
    keywords: Optional[list[str]] = None,
) -> list[float]:
    """Compat: so as notas. Ver score_relevance_com_origem para a procedencia."""
    return [nota for nota, _ in score_relevance_com_origem(topic, results, keywords)]
```

**M9 — docstring de módulo** (`gemini_client.py:11`): a linha `- score_relevance returns keyword-based heuristic scores or [0.5, ...]` vira `- score_relevance_com_origem returns (nota, origem): heuristica sem LLM (ou (0.5, "fallback_erro") sem keywords); score_relevance e o wrapper que descarta a origem`. Em `llm/__init__.py`: importar e exportar `score_relevance_com_origem` (no `from .gemini_client import (...)` e no `__all__`); a docstring do pacote, linha `Provides keyword expansion, relevance scoring, and auto-categorization`, ganha `(scores carry their origin: see score_relevance_com_origem)`. ⚠ **Não** tocar as frases sobre Gemini/API key (emenda B7, frente 5).

- [ ] **Step 4: Ver passar** — `Total: 63 | PASS: 63 | FAIL: 0`. `git grep -n 'score_relevance\b' -- '*.py'`: só o wrapper, `__init__.py`, `app.py:582` (que a T9 troca) e os testes.

- [ ] **Step 5: BASELINE 63; runner; golden OK; commit**

```bash
git add levantamento-normativos/llm/ levantamento-normativos/test_llm_phase3.py tools/run_all_tests.py
git commit -m "feat(frente2): a nota de relevancia passa a dizer de onde veio

score_relevance_com_origem devolve (nota, origem) com origem em
ORIGENS_RELEVANCIA; score_relevance vira wrapper com o mesmo contrato
(53 testes intactos). 0.5 de fallback deixa de ser indistinguivel de
nota do modelo. Docstrings de modulo e de pacote atualizadas.
test_llm_phase3: 53 -> 63."
git push origin master
```

---

### Task 7: `_merge` leva a origem da nota vencedora (invariante declarado)

**Files:** `deduplicator.py:98-113` (docstring), `:147` (`relevancia`); `test_phase4.py`; `tools/run_all_tests.py`.

- [ ] **Step 1: Testes** — ao fim de `test_phase4.py`:

```python
class TestMergeOrigem:
    """_merge guarda a maior nota E a origem dela (spec §3.4). Invariante: no app o
    dedup roda ANTES da pontuacao, entao hoje o efeito e nulo — ver docstring."""

    def test_incoming_maior_leva_sua_origem(self):
        a = _make_result(relevancia=0.4); a.relevancia_origem = "padrao_fonte"
        b = _make_result(source="google", relevancia=0.9); b.relevancia_origem = "modelo"
        _merge(a, b)
        assert (a.relevancia, a.relevancia_origem) == (0.9, "modelo")

    def test_existing_maior_mantem_sua_origem(self):
        a = _make_result(relevancia=0.9); a.relevancia_origem = "heuristica"
        b = _make_result(source="google", relevancia=0.2); b.relevancia_origem = "modelo"
        _merge(a, b)
        assert (a.relevancia, a.relevancia_origem) == (0.9, "heuristica")

    def test_empate_mantem_existing(self):
        a = _make_result(relevancia=0.5); a.relevancia_origem = "modelo"
        b = _make_result(source="google", relevancia=0.5); b.relevancia_origem = "fallback_erro"
        _merge(a, b)
        assert a.relevancia_origem == "modelo"
```

- [ ] **Step 2: Ver falhar** — `python -m pytest test_phase4.py -q -k MergeOrigem` → 1 failed.
- [ ] **Step 3: Implementar** — em `_merge`, trocar `existing.relevancia = max(existing.relevancia, incoming.relevancia)` por:

```python
    # Relevancia: keep higher score — e a ORIGEM da nota que venceu.
    # Invariante DECLARADO (M8 da rodada de 22/09): no app o dedup roda ANTES
    # da pontuacao, entao aqui todo item ainda e "padrao_fonte" e o efeito
    # pratico e nulo hoje. Existe para o dia em que a pontuacao vier antes
    # (ex.: nota por fonte), sem que a planilha diga "modelo" sobre uma nota
    # da heuristica.
    if incoming.relevancia > existing.relevancia:
        existing.relevancia = incoming.relevancia
        existing.relevancia_origem = incoming.relevancia_origem
```

Docstring: `- relevancia: keep the higher score` → `- relevancia: keep the higher score, and relevancia_origem of whichever won (tie keeps existing)`.

- [ ] **Step 4: Ver passar** — `61 passed`. **Golden: `dedup_esperado.json` inalterado — obrigatório.** BASELINE 61. Commit `feat(frente2): _merge leva a origem da nota que venceu (invariante)`. Push.

---

### Task 8: Planilha — coluna "Origem da nota", aba "Diagnostico da busca", golden nas duas abas

**Files:** `excel_export.py` (`:14-30` imports; `COLUMNS:75-87`; `_write_data_row:186-270`; `generate_excel:274-357`; função nova); `test_phase4.py` (`:421-447`; classes novas); `tools/golden_master.py` (`_sha_planilha:63-84`, docstring); `tests/golden/diagnostico_fixo.json` (novo), `planilha_sha256.txt`, `ambiente.txt`; `tools/run_all_tests.py`.

**Interfaces — Produces:** `COLUMNS` com 11 entradas (11ª = `("Origem da nota", 16, "relevancia_origem")`); `ORIGEM_LABEL`, `VAZIO = "—"`, `DIAGNOSTICO_SHEET`, `DIAGNOSTICO_COLUMNS`; `generate_excel(results, topic, diagnostico=None, quando=None) -> BytesIO`; aba `"Diagnostico da busca"` sempre presente; `wb.active` = `"Normativos"`; título da aba: `f"Diagnóstico da busca: {topic} — {quando or 'data/hora não informada'}"`.

- [ ] **Step 1: Testes** — em `test_phase4.py`:

(a) `TestExcelColumnCount` (`:421-447`): `test_has_10_columns` → `test_has_11_columns` com `== 11`; `range(1, 11)` → `range(1, 12)` e `== 10` → `== 11` nos outros dois; `expected` ganha `"Origem da nota"` no fim; docstring da classe `"""Verify all 11 expected columns are present."""`. ⚠ (M12) hoje só `test_has_10_columns` falha; os outros passam por omissão — atualizar os três mesmo assim.

(b) Classes novas ao fim (10 testes):

```python
from models import KeywordStatus as _KS, rotulo_status
from excel_export import ORIGEM_LABEL, VAZIO, DIAGNOSTICO_SHEET


class TestExcelHonestidade:
    def test_origem_em_portugues_na_coluna_11(self):
        r = _make_result(relevancia=0.85); r.relevancia_origem = "heuristica"
        ws = _load_workbook_from_buffer(generate_excel([r], "t")).active
        assert ws.cell(row=2, column=11).value == "Origem da nota"
        assert ws.cell(row=3, column=11).value == "Heurística (palavras-chave)"

    def test_default_padrao_fonte(self):
        ws = _load_workbook_from_buffer(generate_excel([_make_result()], "t")).active
        assert ws.cell(row=3, column=11).value == "Padrão da fonte"

    def test_aba_diagnostico_sempre_existe_e_normativos_continua_ativa(self):
        wb = _load_workbook_from_buffer(generate_excel([_make_result()], "t"))
        assert wb.sheetnames == ["Normativos", DIAGNOSTICO_SHEET]
        assert wb.active.title == "Normativos"
        assert wb[DIAGNOSTICO_SHEET].cell(row=3, column=1).value == "Nenhum diagnóstico registrado nesta exportação"

    def test_aba_diagnostico_lista_vazia_igual_a_none(self):
        a = _load_workbook_from_buffer(generate_excel([_make_result()], "t", diagnostico=None))[DIAGNOSTICO_SHEET]
        b = _load_workbook_from_buffer(generate_excel([_make_result()], "t", diagnostico=[]))[DIAGNOSTICO_SHEET]
        assert a.cell(row=3, column=1).value == b.cell(row=3, column=1).value

    def test_aba_diagnostico_uma_linha_por_status_com_traco_no_vazio(self):
        diag = [
            _KS(keyword="lgpd", source="lexml", status="error", motivo="bloqueio_waf",
                detalhe="HTTP 200 text/html; título: x | GET http://x", error_message="bloqueio"),
            _KS(keyword="lgpd", source="tcu", status="ok", result_count=4, parcial=True,
                detalhe="pagina 2 (inicio=20): http_5xx: HTTP 500 | GET http://y"),
            _KS(keyword="lgpd", source="google", status="empty"),
            _KS(keyword="outra", source="lexml", status="error", motivo="nao_consultada",
                detalhe="busca parou em max_results=50 antes desta palavra-chave"),
        ]
        wb = _load_workbook_from_buffer(generate_excel([_make_result()], "t", diagnostico=diag, quando="22/09/2026 10:00"))
        ws = wb[DIAGNOSTICO_SHEET]
        assert "22/09/2026 10:00" in ws.cell(row=1, column=1).value
        assert [ws.cell(row=2, column=c).value for c in range(1, 9)] == [
            "Fonte", "Palavra-chave", "Status", "Motivo", "Detalhe", "Resultados", "Parcial", "Retentado"]
        linhas = [[ws.cell(row=r, column=c).value for c in range(1, 9)] for r in range(3, 7)]
        assert linhas[0] == ["lexml", "lgpd", "Indisponível", "bloqueio_waf", "HTTP 200 text/html; título: x | GET http://x", 0, "Não", "Não"]
        assert linhas[1] == ["tcu", "lgpd", "OK", VAZIO, "pagina 2 (inicio=20): http_5xx: HTTP 500 | GET http://y", 4, "Sim", "Não"]
        assert linhas[2] == ["google", "lgpd", "Sem resultado", VAZIO, VAZIO, 0, "Não", "Não"]
        assert linhas[3][2:4] == ["Não consultada", "nao_consultada"]            # R2-B6
        assert ws.cell(row=7, column=1).value is None

    def test_rotulo_da_planilha_e_o_de_models(self):
        diag = [_KS(keyword="k", source="tcu", status="error", motivo="http_5xx")]
        ws = _load_workbook_from_buffer(generate_excel([], "t", diagnostico=diag))[DIAGNOSTICO_SHEET]
        assert ws.cell(row=3, column=3).value == rotulo_status(diag[0]) == "Indisponível"

    def test_sem_quando_o_titulo_diz_nao_informada(self):
        ws = _load_workbook_from_buffer(generate_excel([], "t"))[DIAGNOSTICO_SHEET]
        assert "data/hora não informada" in ws.cell(row=1, column=1).value      # R2-B5: informadA

    def test_detalhe_longo_cabe_na_celula_inteiro(self):
        longo = "HTTP 500; " + "x" * 1500 + " | GET http://z"
        diag = [_KS(keyword="k", source="lexml", status="error", motivo="http_5xx", detalhe=longo)]
        ws = _load_workbook_from_buffer(generate_excel([], "t", diagnostico=diag))[DIAGNOSTICO_SHEET]
        assert ws.cell(row=3, column=5).value == longo                          # R2-B1: nada cortado


class TestRotulosSincronizados:
    def test_origem_label_cobre_o_vocabulario(self):
        assert set(ORIGEM_LABEL) == ORIGENS_RELEVANCIA

    def test_status_label_vem_de_models(self):
        from excel_export import STATUS_LABEL
        assert STATUS_LABEL is rotulo_status   # unico lugar (R2-B6)
```

- [ ] **Step 2: Ver falhar** — na coleta: `ImportError: cannot import name 'ORIGEM_LABEL' from 'excel_export'` (nenhum teste roda — R3). Depois do Step 3c só, `1 + 10 failed` (M12: dos três testes de contagem só `test_has_10_columns` falha hoje).

- [ ] **Step 3: `excel_export.py`**

**3a.** Imports (`:14-30`): `from typing import Optional`; `from models import KeywordStatus, NormativoResult, redigir, rotulo_status`.

**3b.** `COLUMNS` ganha, após `("Relevancia", 12, "relevancia")`: `("Origem da nota", 16, "relevancia_origem"),` com o comentário `# ⚠ test_phase4.py fixa len(COLUMNS); mudar aqui = mudar la no mesmo commit`.

**3c.** Constantes, logo após `COLUMNS`:

```python
# Rotulos em portugues para a planilha (o vocabulario tecnico vive em models.py)
ORIGEM_LABEL = {
    "modelo": "Modelo (IA)",
    "heuristica": "Heurística (palavras-chave)",
    "fallback_erro": "Fallback (erro do modelo)",
    "padrao_fonte": "Padrão da fonte",
}
STATUS_LABEL = rotulo_status          # UNICO lugar: models.rotulo_status (R2-B6)
VAZIO = "—"                            # celula vazia le como None no round-trip do openpyxl; o traco diz
                                       # "campo considerado, sem valor" (B6)
DIAGNOSTICO_SHEET = "Diagnostico da busca"
DIAGNOSTICO_COLUMNS = [
    ("Fonte", 12), ("Palavra-chave", 28), ("Status", 14), ("Motivo", 20),
    ("Detalhe", 90), ("Resultados", 11), ("Parcial", 9), ("Retentado", 10),
]
```

**3d.** `_write_data_row`: antes do `elif field_name == "nome":`:

```python
        elif field_name == "relevancia_origem":
            cell.value = ORIGEM_LABEL.get(value, value)
            cell.font = DATA_FONT
            cell.alignment = RELEVANCIA_ALIGNMENT
```

Docstring de `_write_data_row`: acrescentar `- Origem da nota em portugues (ORIGEM_LABEL)` à lista.

**3e.** Função nova, antes de `generate_excel`:

```python
def _write_diagnostico_sheet(wb, topic: str, diagnostico: Optional[list[KeywordStatus]], quando: Optional[str]) -> None:
    """Aba 'Diagnostico da busca': uma linha por (fonte, palavra-chave).

    Existe SEMPRE, mesmo sem dados, para que quem abre a planilha saiba que o
    registro e previsto. E o que diz, seis meses depois, que o LexML nao
    respondeu naquele dia — a planilha e o artefato que sobrevive a sessao.
    `quando` vem formatado pelo chamador (o golden passa um valor fixo).
    """
    ws = wb.create_sheet(DIAGNOSTICO_SHEET)
    n = len(DIAGNOSTICO_COLUMNS)
    ws.merge_cells(f"A1:{get_column_letter(n)}1")
    t = ws.cell(row=1, column=1)
    t.value = f"Diagnóstico da busca: {topic} — {quando or 'data/hora não informada'}"
    t.font, t.alignment, t.fill = TITLE_FONT, TITLE_ALIGNMENT, TITLE_FILL
    ws.row_dimensions[1].height = 40
    for col, (nome, largura) in enumerate(DIAGNOSTICO_COLUMNS, start=1):
        c = ws.cell(row=2, column=col)
        c.value, c.font, c.fill, c.alignment, c.border = nome, HEADER_FONT, HEADER_FILL, HEADER_ALIGNMENT, THIN_BORDER
        ws.column_dimensions[get_column_letter(col)].width = largura
    if not diagnostico:
        c = ws.cell(row=3, column=1)
        c.value = "Nenhum diagnóstico registrado nesta exportação"
        c.font = DATA_FONT
        return
    sim_nao = lambda b: "Sim" if b else "Não"
    for row, s in enumerate(diagnostico, start=3):
        # keyword e source vem do usuario/LLM: '=1+1' viraria formula (R3); redigir neutraliza
        valores = [redigir(s.source), redigir(s.keyword), STATUS_LABEL(s), s.motivo or VAZIO,
                   (s.detalhe or s.error_message) or VAZIO, s.result_count, sim_nao(s.parcial), sim_nao(s.retried)]
        for col, v in enumerate(valores, start=1):
            c = ws.cell(row=row, column=col)
            c.value, c.font, c.border = v, DATA_FONT, THIN_BORDER
            c.alignment = EMENTA_ALIGNMENT if col == 5 else DATA_ALIGNMENT
    ws.freeze_panes = "A3"
    ws.auto_filter.ref = f"A2:{get_column_letter(n)}{len(diagnostico) + 2}"
```

**3f.** `generate_excel(results, topic, diagnostico: Optional[list[KeywordStatus]] = None, quando: Optional[str] = None)`: docstring — `The workbook contains a single sheet` vira `The workbook contains two sheets: 'Normativos' (active) and 'Diagnostico da busca'`; `Args` ganha `diagnostico: KeywordStatus list from the search; None or empty writes a placeholder row.` e `quando: search date/time already formatted (dd/mm/yyyy HH:MM); None writes 'não informada'.` Antes de `buffer = BytesIO()`: `_write_diagnostico_sheet(wb, topic, diagnostico, quando)` e em seguida `wb.active = 0` (garante `Normativos` ativa). `redigir` **não** é chamada aqui — o `KeywordStatus` já redigiu.

- [ ] **Step 4: `tools/golden_master.py`** (M7):

```python
def _carregar_diagnostico() -> list:
    from models import KeywordStatus
    dados = json.loads((GOLDEN / "diagnostico_fixo.json").read_text(encoding="utf-8"))
    return [KeywordStatus(**d) for d in dados]


def _sha_planilha(itens: list) -> str:
    """Hash dos VALORES das celulas, nao dos bytes do arquivo — de TODAS as abas.

    .xlsx e um ZIP: o date_time de cada membro e o docProps/core.xml carregam o
    relogio da geracao, entao o sha dos bytes crus muda a CADA execucao, com
    entrada identica (medido por tres revisores em 2026-09-16). Congelar bytes
    faria o comparador imprimir DIVERGIU sem nada ter mudado.

    Hasheia TODAS as abas (M7 da rodada de 22/09): a aba 'Diagnostico da busca'
    e o registro de que a fonte nao respondeu; sem ela no hash, uma regressao
    ali passaria com 'golden-master OK'. O diagnostico fixo cobre: error com
    motivo e detalhe; ok parcial; empty; nao_consultada; error retentado sem
    detalhe (so error_message). `quando` e fixo para o hash ser estavel.

    ⚠ O hash da aba de diagnostico depende de models.redigir e rotulo_status e
    de excel_export.ORIGEM_LABEL, VAZIO e do titulo com `quando` fixo (rodada 3):
    mudanca INTENCIONAL em qualquer um deles = recongelar com justificativa,
    nao regressao do dedup/export.

    A funcao publica e generate_excel(results, topic, diagnostico=None, quando=None)
    (excel_export.py) — e o que app.py e test_phase4.py usam.
    """
    from excel_export import generate_excel
    from openpyxl import load_workbook

    wb = load_workbook(generate_excel(itens, topic="golden-master",
                                      diagnostico=_carregar_diagnostico(), quando="22/09/2026 00:00"))
    linhas = []
    for ws in wb.worksheets:
        linhas.append(("__aba__", ws.title))
        linhas.extend(tuple(c.value for c in linha) for linha in ws.iter_rows())
    return hashlib.sha256(repr(linhas).encode("utf-8")).hexdigest()
```

`tests/golden/diagnostico_fixo.json` (5 linhas):

```json
[
  {"keyword": "protecao de dados", "source": "lexml", "result_count": 0, "status": "error",
   "error_message": "bloqueio_waf", "motivo": "bloqueio_waf",
   "detalhe": "HTTP 200 text/html; título: Verificação de segurança — Senado Federal; corpo: '<!DOCTYPE html>' | GET https://www.lexml.gov.br/busca/SRU?operation=searchRetrieve&query=x | cadeia: busca/SRU: bloqueio_waf (HTTP 200); sru/SRU: endpoint_inexistente (HTTP 404); srw/SRU: endpoint_inexistente (HTTP 404) | retry pulado: os 3 URLs já falharam nesta busca"},
  {"keyword": "protecao de dados", "source": "tcu", "result_count": 4, "status": "ok", "parcial": true,
   "detalhe": "pagina 2 (inicio=20): http_5xx: HTTP 500 em 3 tentativas; corpo: '' | GET https://dados-abertos.apps.tcu.gov.br/api/acordao/recupera-acordaos?inicio=20"},
  {"keyword": "LGPD", "source": "google", "result_count": 0, "status": "empty"},
  {"keyword": "governanca", "source": "lexml", "result_count": 0, "status": "error", "motivo": "nao_consultada",
   "detalhe": "busca parou em max_results=50 antes desta palavra-chave"},
  {"keyword": "LGPD", "source": "tcu", "result_count": 0, "status": "error", "motivo": "timeout",
   "retried": true, "error_message": "Retry failed: timeout: sem resposta em 15s x 3 | GET https://dados-abertos.apps.tcu.gov.br/api/acordao/recupera-acordaos?inicio=0"}
]
```

- [ ] **Step 5: Ver passar** — `python -m pytest test_phase4.py -q` → `71 passed`.

- [ ] **Step 6: Recongelar no mesmo commit** — na raiz: `python tools/golden_master.py comparar` → **esperado `DIVERGIU: planilha divergiu`, e NENHUMA linha `dedup divergiu`** (se houver, parar: regressão). `python tools/golden_master.py congelar`; `comparar` **2×** → OK e sha idêntico. `git diff --stat tests/golden/` → só `planilha_sha256.txt` (+ `ambiente.txt` se mudou) + `diagnostico_fixo.json` novo; `dedup_esperado.json` **ausente**.

- [ ] **Step 7: BASELINE 71; runner; auditoria; commit**

```bash
git add levantamento-normativos/excel_export.py levantamento-normativos/test_phase4.py tests/golden/ tools/golden_master.py tools/run_all_tests.py
git commit -m "feat(frente2): planilha ganha 'Origem da nota' e a aba 'Diagnostico da busca'; golden cobre as duas abas

COLUMNS 10 -> 11. Aba de diagnostico sempre presente, com data/hora da
busca, rotulo unico (models.rotulo_status: 'Nao consultada' nao e
'Indisponivel'), traco explicito no campo vazio, detalhe inteiro (ate
2000 chars). GOLDEN-MASTER RECONGELADO DE PROPOSITO (spec 3.5 + M7):
coluna nova e hash de todas as abas com diagnostico_fixo.json (5 linhas).
dedup_esperado.json inalterado — conferido pelo ramo do dedup antes de
recongelar. O hash da aba nova depende de redigir/rotulo_status/
ORIGEM_LABEL/VAZIO: mudanca intencional neles = recongelar.
test_phase4: 61 -> 71."
git push origin master
```

---

### Task 9: Tela — pontuar sempre, relatório honesto, avisos por fonte, card, preview, fonte que levanta

**Files:** `app.py` — imports (`:21-24`); `except` do laço de fontes (`:545-564`); pontuação (`:570-596`); `_render_search_diagnostics` (`:840-905`); `render_step4` (`:907-946`); card (`:1049-1065`); `generate_excel` (`:1195`); preview (`:1221-1232`). ⚠ **Linhas do HEAD:** os Steps 1-3 inserem ~20 linhas antes de `:840`; a partir daí, ancorar pelo **nome da função**, não pelo número. `tools/dirigir_app.py` (novo); `.gitignore`.

- [ ] **Step 1: Imports** — `from models import KeywordStatus, NormativoResult, ORIGENS_RELEVANCIA, statuses_para_falha_total` (⚠ **não** importar `rotulo_status`: a tela agrupa por motivo, só a planilha rotula — R3); `from datetime import datetime` (⚠ **não** `import datetime`); `from zoneinfo import ZoneInfo`; no topo, `ORIGEM_CURTA = {"modelo": "modelo", "heuristica": "heurística", "fallback_erro": "fallback", "padrao_fonte": "padrão da fonte"}`. O teste de sincronia `set(ORIGEM_CURTA) == ORIGENS_RELEVANCIA` **não** fica como `assert` no app (some com `-O`, R3): vai para `test_phase4.py::TestRotulosSincronizados` como `test_origem_curta_do_app_cobre_o_vocabulario` (`from app import ORIGEM_CURTA` — ⚠ importar `app` executa `st.set_page_config`; se isso levantar fora do Streamlit, mover `ORIGEM_CURTA` para `models.py` e importar de lá nos dois lugares). ⚠ Isso muda a contagem da T8/T9: +1 em `test_phase4` = **72** e total **283** — o executor atualiza a tabela e o BASELINE no commit da T9.

- [ ] **Step 2: Fonte que levanta não some (H2, R2)** — no `except Exception as e:` de `:556`, **antes** do `status_text.write`:

```python
                # H2: os statuses ja coletados antes da excecao ficam; o resto vira erro_interno por keyword
                ja = getattr(searcher, "keyword_statuses", []) or []
                all_keyword_statuses.extend(ja)
                cobertas = {s.keyword for s in ja}
                faltam = [k for k in keywords if k not in cobertas]
                if faltam or not keywords:   # R3: com tudo coberto, nao inventar uma linha "(todas)"
                    all_keyword_statuses.extend(statuses_para_falha_total(searcher.SOURCE_ID, faltam, e))
```

- [ ] **Step 3: Pontuação sempre** — `app.py:570-596`, trocar o bloco por:

```python
        # Relevancia SEMPRE roda (frente 2): com LLM e o modelo; sem LLM e a
        # heuristica por palavras-chave. Antes, sem chave, a nota ficava na
        # constante do searcher e a heuristica era codigo inalcancavel.
        if all_results:
            topic = st.session_state.get("topic", "")
            result_dicts = [{"nome": r.nome, "ementa": r.ementa} for r in all_results]
            status_text.write(
                "Avaliando relevancia com IA..." if llm_available()
                else "Avaliando relevancia por palavras-chave (sem LLM configurado)..."
            )
            pares = gemini_client.score_relevance_com_origem(topic, result_dicts, keywords)
            for i, (score, origem) in enumerate(pares):
                if i < len(all_results):
                    if origem not in ORIGENS_RELEVANCIA:   # M8/R3: validacao real, nao assert (some com -O)
                        logger.error("origem de relevancia desconhecida %r; gravando padrao_fonte", origem)
                        origem = "padrao_fonte"
                    all_results[i].relevancia = score
                    all_results[i].relevancia_origem = origem

            # Categorizacao continua condicionada ao LLM: nao ha heuristica
            # para ela, e "Nao categorizado" ja e honesto.
            if llm_available():
                status_text.write("Categorizando normativos...")
                categories = gemini_client.categorize_results(topic, result_dicts)
                for i, cat in enumerate(categories):
                    if i < len(all_results):
                        all_results[i].categoria = cat
```

- [ ] **Step 4: Relatório** — substituir `_render_search_diagnostics` inteira:

```python
def _render_search_diagnostics(kw_statuses: list[KeywordStatus]) -> None:
    """Relatorio da busca: indisponiveis, parciais, nao consultadas, sem resultado, OK.

    Classifica por MOTIVO, nao so por status (R2-B6): nao_consultada tem
    status="error" no vocabulario, mas nao e "fonte indisponivel" — e uma
    palavra-chave que nao foi enviada. Rotulos vem de models.rotulo_status.
    """
    if not kw_statuses:
        return

    indisponiveis = [s for s in kw_statuses if s.status == "error" and s.motivo != "nao_consultada"]
    nao_consultadas = [s for s in kw_statuses if s.motivo == "nao_consultada"]
    empty_statuses = [s for s in kw_statuses if s.status == "empty"]
    ok_statuses = [s for s in kw_statuses if s.status == "ok"]
    parciais = [s for s in kw_statuses if s.parcial and s.status != "error"]   # R3: disjunto de indisponiveis
    total = len(kw_statuses)

    label = (f"Relatório da busca — {len(ok_statuses)} OK · {len(indisponiveis)} indisponíveis · "
             f"{len(empty_statuses)} sem resultado · {len(nao_consultadas)} não consultadas ({total} buscas)")

    with st.expander(label, expanded=bool(indisponiveis or parciais)):
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total de buscas", total)
        c2.metric("OK", len(ok_statuses))
        c3.metric("Sem resultado", len(empty_statuses))
        c4.metric("Indisponíveis", len(indisponiveis))
        c5.metric("Não consultadas", len(nao_consultadas))

        if indisponiveis:
            st.markdown("**:red[Fontes indisponíveis (a fonte não pôde ser consultada):]**")
            for s in indisponiveis:
                retry_badge = " (retentado)" if s.retried else ""
                extra = f" — {s.result_count} resultado(s) do endpoint que respondeu" if s.result_count else ""
                badge_parcial = " (parcial)" if s.parcial else ""
                st.markdown(f"- :red[**{html_module.escape(s.keyword)}**] em *{html_module.escape(s.source)}*"
                            f"{retry_badge}{badge_parcial}: `{html_module.escape(s.motivo or 'erro')}`{extra}")
                st.code(s.detalhe or s.error_message or "(sem detalhe)", language=None)   # M13: nao passa pelo Markdown
            st.caption("A fonte não pôde ser consultada. Isso NÃO significa que não existem normativos — "
                       "significa que esta busca não os viu. Motivo e detalhe acima; a aba "
                       "'Diagnostico da busca' da planilha registra o mesmo.")

        if parciais:
            st.markdown("**:orange[Buscas parciais (a coleta não terminou):]**")
            for s in parciais:
                st.markdown(f"- :orange[**{html_module.escape(s.keyword)}**] em *{html_module.escape(s.source)}*: "
                            f"{s.result_count} resultado(s)")
                st.code(s.detalhe or "(sem detalhe)", language=None)

        if nao_consultadas:
            st.markdown("**:gray[Palavras-chave não consultadas (limite da busca atingido antes delas):]**")
            for s in nao_consultadas:
                st.markdown(f"- {html_module.escape(s.keyword)} em *{html_module.escape(s.source)}* — "
                            f"{html_module.escape(s.detalhe)}")

        if empty_statuses:
            st.markdown("**:orange[Palavras-chave sem resultados (nenhum normativo encontrado):]**")
            for s in empty_statuses:
                st.markdown(f"- :orange[**{html_module.escape(s.keyword)}**] em *{html_module.escape(s.source)}*")
                if s.detalhe:   # R3-H5: "500 acordaos sem sumario" nao e "nao ha acordao"
                    st.code(s.detalhe, language=None)
            st.caption("Essas palavras-chave foram buscadas com sucesso, mas nenhum normativo "
                       "correspondente foi encontrado na fonte. Quando há detalhe, ele diz o que a fonte entregou.")

        if ok_statuses:
            st.markdown("**:green[Palavras-chave com resultados:]**")
            for s in ok_statuses:
                st.markdown(f"- :green[**{html_module.escape(s.keyword)}**] em *{html_module.escape(s.source)}*: "
                            f"{s.result_count} resultado(s){' (parcial)' if s.parcial else ''}")
```

⚠ A assinatura mudou (só `kw_statuses`): as **duas** chamadas em `render_step4` (`:934` e `:946`) passam a `_render_search_diagnostics(kw_statuses)`, e as três listas `error_statuses/empty_statuses/ok_statuses` de `:914-916` saem — o `st.error` do ramo `if not results:` passa a usar `indisponiveis` calculado ali (Step 5).

- [ ] **Step 5: Avisos por fonte (H3, R2, R3-H4)** — em `render_step4`, o bloco abaixo entra **depois** do `st.header(...)` de cada um dos dois ramos (com e sem resultados — R3: antes do header ficava acima do título); as listas `catalogadas`/`indisponiveis`/`por_fonte` são calculadas uma vez, logo após `kw_statuses = ...`:

```python
    catalogadas = [s for s in kw_statuses if s.source in ("lexml", "tcu")]
    indisponiveis = [s for s in kw_statuses if s.status == "error" and s.motivo != "nao_consultada"]
    por_fonte = {}
    for s in catalogadas:
        f = por_fonte.setdefault(s.source, {"entregues": 0, "erros": 0, "total": 0, "motivos": set(), "parcial": False})
        f["total"] += 1
        f["entregues"] += s.result_count
        if s.status == "error" and s.motivo != "nao_consultada":
            f["erros"] += 1
            f["motivos"].add(s.motivo)
        f["parcial"] = f.get("parcial", False) or s.parcial
    # R3-H4: "morta" exige que NENHUM status da fonte seja parcial — TCU com acordaos 200
    # (0 match) e atos 500 respondeu pela metade, nao "esta indisponivel"
    mortas = [f for f, v in por_fonte.items() if v["total"] and v["erros"] == v["total"]
              and v["entregues"] == 0 and not v["parcial"]]
    parciais_fonte = [f for f, v in por_fonte.items() if v["erros"] and f not in mortas]
    nomes = ", ".join(sorted(por_fonte)) or "nenhuma selecionada"
    tem_web_aberta = any(s.source == "google" for s in kw_statuses)
    if mortas and not parciais_fonte:
        resto = " O que aparece abaixo vem só da web aberta." if tem_web_aberta else " Nenhuma outra fonte foi consultada."
        st.warning(f"Nenhuma fonte catalogada ({nomes}) entregou resultado nesta busca: "
                   + "; ".join(f"{f} indisponível ({', '.join(sorted(por_fonte[f]['motivos']))})" for f in mortas)
                   + "." + resto + " Veja o relatório da busca.")
    elif mortas or parciais_fonte:
        partes = [f"{f} indisponível ({', '.join(sorted(por_fonte[f]['motivos']))})" for f in mortas]
        partes += [f"{f} respondeu parcialmente ({por_fonte[f]['entregues']} resultado(s); "
                   f"{', '.join(sorted(por_fonte[f]['motivos']))})" for f in parciais_fonte]
        st.warning("Cobertura incompleta nas fontes catalogadas: " + "; ".join(partes)
                   + ". O restante pode estar faltando. Veja o relatório da busca.")
    if results and all(r.relevancia_origem == "heuristica" for r in results):
        st.caption("Sem LLM configurado, a relevância é a fração das palavras-chave presentes na ementa: "
                   "0% significa 'nenhuma palavra-chave na ementa', não 'irrelevante'.")   # M14
```

E no ramo `if not results:`, o `st.error` passa a ser: `if indisponiveis: st.error(f"Nenhum normativo encontrado. {len(indisponiveis)} busca(s) não puderam consultar a fonte (indisponível). Isso não significa que o normativo não existe — veja o relatório.")`.

- [ ] **Step 6: Card, preview, exportação** — card (`Relevancia:` na `:1065`): `f"<b>Relevancia:</b> {relevancia_pct}% <i>({ORIGEM_CURTA.get(item.relevancia_origem, item.relevancia_origem)})</i> &middot; "` (`.get`: lookup duro vira traceback na página — R3); preview (`:1221-1232`): depois de `"Relevancia": ...,` acrescentar `"Origem": ORIGEM_CURTA.get(item.relevancia_origem, item.relevancia_origem),`; exportação (`:1195`): `generate_excel(selected, topic, diagnostico=st.session_state.get("keyword_statuses", []), quando=datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M"))` (BRT como o 503 do TCU — R3).

- [ ] **Step 7: Gate visual V11** — `tools/dirigir_app.py`:

```python
# -*- coding: utf-8 -*-
"""Gate visual da frente 2: dirige o app pelo navegador e AFIRMA o que a UI diz.

Pre-requisito: o app no ar em http://localhost:8501
    (em levantamento-normativos/: python -m streamlit run app.py --server.headless true)
Uso (na raiz):  PYTHONIOENCODING=utf-8 python tools/dirigir_app.py
Usa o Chrome instalado (channel="chrome"): os navegadores do Playwright nao
estao baixados nesta maquina (ENVIRONMENT.md, 2026-09-22).
Assume o cenario de 22/09 (LexML bloqueado). Se o LexML voltar, o gate
avisa e o humano decide — nao ha como ser verde e vermelho ao mesmo tempo.
"""
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "tests" / "evidencia" / "v11_passo4.png"   # evidencia de sessao, NAO versionada
SAIDA.parent.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    pg = b.new_page(viewport={"width": 1440, "height": 1600})
    pg.goto("http://localhost:8501", wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(3000)
    pg.get_by_text("Inserir palavras-chave manualmente").click()
    pg.wait_for_timeout(2000)
    ta = pg.locator("textarea").first
    ta.click(); ta.fill("LGPD\nprotecao de dados pessoais")
    pg.keyboard.press("Control+Enter"); pg.wait_for_timeout(2500)
    pg.get_by_role("button", name="Proximo >>").click(); pg.wait_for_timeout(3000)
    pg.get_by_role("button", name="Iniciar Busca").click()
    for _ in range(60):
        pg.wait_for_timeout(5000)
        if "Passo 4 - " in pg.inner_text("body"):
            break
    pg.wait_for_timeout(3000)
    pg.screenshot(path=str(SAIDA), full_page=True)
    texto = pg.inner_text("body")
    print(texto[:4000])
    b.close()

print("\n=== GATE V11 ===")
m = re.search(r"Revisar Resultados \((\d+) normativos\)", texto)
n_cab = int(m.group(1)) if m else 0
n_cards = texto.count("Ver detalhes")
checks = {
    "relatório mostra ≥1 indisponível": bool(re.search(r"·\s*[1-9]\d*\s*indisponíveis", texto)),
    "bloqueio_waf visível na tela": "bloqueio_waf" in texto,
    "aviso por fonte presente": ("indisponível (" in texto),
    "TCU declarado parcial (acórdãos 200, atos 500 — cenário de 22/09)": ("tcu respondeu parcialmente" in texto),
    "origem no card": any(o in texto for o in ("(heurística)", "(modelo)", "(fallback)")),
    "nenhum card sumiu (cards == N do cabeçalho)": n_cab > 0 and n_cards == n_cab,
    "'0 erros' não aparece": "0 erros" not in texto,   # mantido por historia; nao e o gate
}
for k, v in checks.items():
    print(f"  {'OK ' if v else 'FALHOU'} {k}")
if not checks["relatório mostra ≥1 indisponível"]:
    print("  ⚠ Se o LexML voltou a responder, este gate nao se aplica hoje — confirmar no relatório.")
assert all(v for k, v in checks.items() if k not in ("'0 erros' não aparece",)), "gate V11 reprovou"
print("GATE V11 OK — abrir e OLHAR:", SAIDA)
```

`.gitignore` ganha `tests/evidencia/`. Rodar com o app no ar; **abrir o PNG e olhar**.

- [ ] **Step 8: Runner, golden, auditoria; commit** `feat(frente2): a tela classifica por motivo, avisa por fonte e mostra a origem da nota`. Push.

---

### Task 10: Fechar a frente

- [ ] Critérios de pronto da spec §7 (com os comandos e saídas no commit): 9 commits das tasks; runner TUDO VERDE sem `[AVISO] cresceu`; `golden_master.py comparar` OK e `git diff d054d5b -- tests/golden/dedup_esperado.json` vazio; V11 rodado de novo; auditoria dos 2 comandos sobre `dc99d73..HEAD`.
- [ ] Duráveis: `_TODO.md` (frente 2 ✅; F9 perde os achados que viraram código; P3 ganha: "sanitizar ementa/nome contra fórmula na aba Normativos", "dublar `test_lexml_cql_injection_sanitization` — faz rede", "tela: agrupar o detalhe do TCU por fonte (é idêntico por keyword)", "runner sem LLM de verdade: `st.secrets` vence a variável vazia — frente 5"); `log.md`; `SESSION-ONBOARD` §2/§6 (próxima: frente 5); `BLOCKED-ON-RODRIGO.md` B-04 (`✅ a UI e a planilha distinguem indisponível de sem resultado; acórdãos do TCU deixaram de ser invisíveis — mas os recentes chegam sem sumário (medido), a lacuna continua`); `LESSONS.md`: (1) fixture escrita à mão sobre esquema não capturado é falsa testemunha — a real derrubou o teste e revelou um bug de produção (B5); (2) correção que tapa um bug abre outro: `redigir(300)` × cadeia agregada (R2-B1) e `sem_texto` fora do try × `_texto_do_acordao` não-total (R3-B1) — em duas rodadas seguidas, o pior achado foi um **cruzamento de duas correções da rodada anterior**; só rodada seguinte pega, e o plano só ficou executável na 4ª versão; (3) falta captura real de SRU do LexML — capturar quando a fonte responder.
- [ ] Commit `docs: fecha a frente 2`; push; `/checkpoint`.

---

## Self-review (v4)

**Cobertura da spec + emendas:** §3.1 → T1 · §3.2 → T2 · §3.3 → T3 · §3.4 → T6+T7+T9 · §3.5 → T8 · §3.6 → T9 · §3.7 → gates de golden (exceção declarada em T4) · §4 V1–V11 → T1..T9 · §5 → estrutura (+ google, tcu mapping) · §7 → T10. Emendas à spec: §3.1 (motivos; redigir em toda atribuição; rotulo_status na planilha; parcial com empty/error), §3.7 (T4; data vazia continua `""`), §5 (T5), §3.5 (`quando`, `—`, golden nas 2 abas, detalhe até 2000 com corte marcado).
**Contagens (recomputadas dos blocos, v4):** T1 41+17=58 · T2 16 · T3 +10 = 26 coletados (25 passed + 1 xfail) · T4 xfail→passed +3 = 29 · T5 +8 = 37 · T6 63 · T7 61 · T8 71 · T9 +1 (`test_origem_curta_do_app…`) = 72 · **final 13 + 63 + 98 + 72 + 37 = 283**. ⚠ A tabela do topo mostra 282/71 na T8/T9 porque o teste da T9 nasce na T9; o executor corrige a tabela e o BASELINE no commit da T9.
**Delegações à v1:** nenhuma. **Placeholders:** nenhum `TBD`/`TODO`/`# inalterado`/`...`.
**Nomes:** `FonteIndisponivel(motivo, detalhe)` · `SOURCE_ID` · `_search_keyword_safe -> (list, erro_fatal, erro_paginacao)` · `_fetch_all_pages -> (itens, erro, parcial)` · `_search_urls -> (list, erro)` · `_texto_do_acordao` (não-total, sempre dentro de `try`) · `_sem_sumario` (total) · `score_relevance_com_origem -> list[tuple[float, str]]` · `generate_excel(results, topic, diagnostico=None, quando=None)` · `redigir(texto, limite=2000)` (corte no meio, marcado) · `rotulo_status(s)` (só planilha) · `statuses_para_falha_total(source, keywords, exc)` · `_render_search_diagnostics(kw_statuses)`.

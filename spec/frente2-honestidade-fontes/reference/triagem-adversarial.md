> Trilha de auditoria das 3 rodadas adversariais, extraída **verbatim** do plano (`docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md`,
> linhas 15-182). **Não é instrução de build**: tudo o que foi aceito já está dobrado no
> corpo das tasks. Serve para saber POR QUE um trecho é como é (ids R2-*, R3-*, B*, H*, M*).

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

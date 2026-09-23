# T2 · LexML declara bloqueio, timeout, 5xx, paginação parcial e `nao_consultada` — registro de implementação

> Task: `../tasks/02-lexml-falhas-declaradas.md` (plano v4, linhas 583-1334 — o plano é a fonte de verdade; a cópia
> da task foi conferida contra o plano por `diff`: idêntica).
> Trilha A, worktree `bn-trilha-a`, branch `frente2/trilha-a`, 23/09/2026.
> Commits: **`8f5ccfc`** `feat(frente2): LexML declara bloqueio, timeout, 5xx e paginacao parcial — nunca 'sem resultado'`
> · **`407e341`** `fix(frente2): review da T2 — URL no detalhe de corpo ilegivel; comentarios de fallback`.
> Teste independente: **APROVADO**. Revisão de código: **APROVADO com 1 importante + 2 menores** (I1 e M1 aplicados em
> `407e341`; M2 adiado). Vereditos completos: `../execucao/revisoes/T2.md`.

## 1. O que foi feito

| Arquivo | Símbolos |
|---|---|
| `levantamento-normativos/searchers/lexml_searcher.py` | import `FonteIndisponivel`, `urlencode`, `redigir` (este no fix); `LexMLSearcher.SOURCE_ID = "lexml"`; `__init__` ganha `_urls_mortos`, `_keyword_atual` e (fix I1) `_ultima_url`; `search()` com o laço, o cap `nao_consultada`, o retry que não rebaixa motivo e o `retry pulado`; `_search_keyword_safe` → `(resultados, erro_fatal, erro_paginacao)`; `_search_keyword` com o parse dentro do `try` (página seguinte = parcial) e (fix I1) o parse embrulhado para anexar `\| GET <url>`; `_fetch_sru` com cache de causa por URL; novos `_PRIORIDADE`, `_status_http`, `_causa_da_cadeia_morta`, `_exigir_sru`; `_try_fetch` reescrito (só 404 → `None`); `_parse_sru_response` levanta `resposta_ilegivel` |
| `levantamento-normativos/tests/test_fontes_indisponiveis.py` | **novo**: 16 testes do plano + 1 da review (I1) = 17 |
| `levantamento-normativos/tests/fixtures/lexml_sru_valido.xml` | **novo**: SRU mínimo, 📝 escrito à mão (não há captura real porque a fonte está bloqueada; o `LESSONS` é da T10) |
| `levantamento-normativos/test_comprehensive.py` | `test_lexml_parse_sru_response_malformed_xml` (contrato novo) e `test_lexml_cql_injection_sanitization` (tupla de 3) |
| `tools/run_all_tests.py` | `SUITES_PYTEST` ganha a suíte nova; `BASELINE[...] = 16` → **17** no fix; comentário "Nasce com UMA suite" reescrito; docstring "Uma e pytest" corrigida |

Os blocos de código do plano foram colados como estão. Extraí-os por script do arquivo da task, sem redigitar.

## 2. Desvios do plano e por quê

Os desvios 1 a 4 foram aceitos pelo revisor ("Desvios declarados 1-3: aceitos"; o 4 é a instrução de não fazer push).

1. **Args do `_try_fetch` mantido.** O bloco do Step 5 não trazia a seção `Args: url/params` do docstring antigo. Mantive a seção (acréscimo; regra "documentação move junto").
2. **Comentário `# Merge into results_by_id, deduplicating by ID` mantido.** O bloco do Step 10 o omitia.
3. **Docstrings e comentários que ficaram falsos foram corrigidos** (regra verify-stale-docs), sem mudar código:
   - comentário do módulo nas constantes `*_SRU_URL` e docstring de `_fetch_sru`: diziam "fallback em 404 ou erro de conexão";
   - `Returns` de `_search_keyword`: dizia "may be empty on error";
   - `search()`: ganhou um parágrafo sobre falha declarada, retry pulado, `nao_consultada` e `parcial`;
   - docstring do runner: dizia "Uma e pytest".
4. **Sem `git push`, sem `_TODO.md`.** O push fica com o orquestrador. A nota P3 do Step 11(b) foi registrada por ele.
5. **Teste além do plano (review I1).** Com ele a suíte vai de 16 para 17, e o `BASELINE` foi para 17 no mesmo commit (`407e341`).
   ⚠ **As contagens do plano para esta suíte ficam +1 a partir daqui:**

   | Após | Plano | Real |
   |---|---|---|
   | T3 | 25 (26 coletados, 1 xfail) | **26** (27 coletados, 1 xfail) |
   | T4 | 29 | **30** |
   | T5 | 37 | **38** |

   O total do runner também fica +1 em cada linha da tabela de BASELINE.

## 3. Gates e saídas

### Ver falhar (Step 3): 15 failed + 1 passed, não 16 failed

```
FAILED ...::test_lexml_cenario_real_toda_keyword_e_bloqueio_waf_e_3_requisicoes   (1 URL distinta, esperava 3)
FAILED ...::test_lexml_html_generico_e_resposta_ilegivel                           (('empty','') != ('error','resposta_ilegivel'))
...                                                                                 (+12 do mesmo tipo)
FAILED ...::test_lexml_parse_error_levanta_fonte_indisponivel                     (DID NOT RAISE FonteIndisponivel)
PASSED ...::test_lexml_sru_valido_continua_ok_mesmo_com_bom_e_content_type_estranho
15 failed, 1 passed in 1.01s
```

Todas as falhas são de assertion; nenhuma é `ImportError` (a T1 entregou os símbolos). A suíte tem **16** `def test_` (`grep -c`), então a diferença está na previsão, não num teste faltando.

O teste que passa é o **guarda M10**: SRU válido com BOM e `text/plain` continua `ok`. O código antigo já aceitava esse caso (o `ET.fromstring` de `str` com BOM parseia). Um guarda de não-regressão passar antes da mudança é o comportamento correto. O tester confirmou isso contra o `lexml_searcher.py` de `8f5ccfc~1`.

O teste do fix I1 também foi visto falhar antes da correção (código de `8f5ccfc` com o teste novo):

```
E  assert ('| GET ' in 'XML SRU nao parseia: not well-formed (invalid token): line 1, column 0; corpo: \'{"erro": "nao e SRU"}\'')
1 failed, 16 passed
```

### Ver passar (implementador)

| Suíte | `8f5ccfc` | `407e341` |
|---|---|---|
| `tests/test_fontes_indisponiveis.py` | `16 passed in 0.71s` | `17 passed in 0.64s` |
| `test_comprehensive.py` | `Total: 98 \| Passed: 98 \| Failed: 0` | 98 (runner) |
| `test_phase4.py` | `58 passed` | `58 passed` |

Runner (`python tools/run_all_tests.py`, raiz), TUDO VERDE, exit 0:

```
                                      8f5ccfc     407e341
test_searchers.py                  13  402.8s   13  404.9s
test_llm_phase3.py                 53    2.7s   53    2.7s
test_comprehensive.py              98  139.1s   98  136.6s
test_phase4.py                     58    2.6s   58    2.4s
tests/test_fontes_indisponiveis.py 16    1.8s   17    1.7s
total                             238          239
```

- `python tools/golden_master.py comparar` → `golden-master OK`, nos dois commits.
- `git grep -n "_search_keyword_safe" -- '*.py'` → só `lexml_searcher.py` (`:147`, `:207`, definição) e `test_comprehensive.py` (`:389`, `:391`). Há também `tools/split_frente2.py:62`, mas ali é texto do critério de aceite, não call site.
- Nenhum outro arquivo chama `_try_fetch`, `_fetch_sru` ou `_sru_url`.

### Tempo do `test_searchers`: não caiu, e por quê

Medido: 411s na T1, 402.8s e 404.9s na T2. O plano previa queda com o cache de falha. Ela não veio porque o `test_searchers` faz **uma** busca LexML com **uma** keyword (`search(["LGPD"])`). O cache economiza entre keywords e entre retries, e ali quase não há o que economizar.

Medição ao vivo (rede real, 23/09) da mesma chamada com o código novo: **1,7 s**, `status=error`, `motivo=bloqueio_waf`, `retried=False`. O detalhe traz:

```
... | cadeia: busca/SRU: bloqueio_waf (HTTP 200); sru/SRU: endpoint_inexistente (HTTP 404); srw/SRU: endpoint_inexistente (HTTP 404) | GET https://www.lexml.gov.br/busca/SRU?operation=searchRetrieve&...
```

O tester mediu 2,9 s. Os ~400 s restantes são do TCU: 500 com 3 tentativas, conforme o tester. O ganho de tempo depende da T3 e de buscas com mais keywords.

O tester também viu uma vez `test_searchers 35280s` no runner. Isso é impossível; provavelmente um salto de relógio ou suspensão do Windows. Não se repetiu.

### Auditoria de documentação (os 2 comandos, lidos inteiros)

**`8f5ccfc`** — `git diff -U0 HEAD~1 -- '*.py' | grep '^-' | grep -v '^---'` → 105 linhas removidas.

| Removido | Destino |
|---|---|
| logs `previous URL failed, trying fallback` e `all SRU endpoints failed` | removidos de propósito (Step 10); substituídos pelos `logger.warning(... proximo da cadeia)` do Step 7 |
| `error_message = "API indisponivel (retry skipped)"` e o comentário `Mark remaining as retried-but-failed` | removidos de propósito (Step 10); agora ficam o motivo original + `retry pulado` no detalhe, e o comentário "Sem requisicao: NAO marca retried (R2-H2)" |
| `# First page failed — API is unreachable, raise so caller can distinguish from "found 0 results"` | `Raises:` do docstring de `_search_keyword` + `if first_page: raise` |
| `break  # Subsequent page failed; return what we have` | comentário "H5 + R2-B4: pagina seguinte falhou — devolve o que veio, mas DECLARA…" |
| `# Try primary URL first`, `# Primary failed -- try fallback URLs in order` | docstring reescrito de `_fetch_sru` (ordem da cadeia e cache) |
| `# If we already know which URL works, use it directly` | **restaurado em `407e341`** (review M1) |
| log `LexML XML parse error` | vira `raise`; o `_search_keyword_safe` loga a exceção |
| log `error searching keyword` | `fonte indisponivel para` / `erro interno em` |
| logs de timeout e de conexão | mantidos no `_try_fetch` novo (só mudaram de posição) |
| `logger.info(...)` em várias linhas | mesma mensagem, numa linha (bloco do plano) |
| docstrings `([], 0)`, `(results, error_message)`, `ConnectionError`, `None on failure` | contratos novos nos mesmos docstrings |
| comentário "Nasce com UMA suite" do runner | reescrito ("Nasceu com UMA… cada suite entra no commit que a CRIA") |

**`407e341`** — 8 linhas removidas: o import (ganhou `redigir`), 3 linhas do comentário do módulo e do docstring de `_fetch_sru` (reescritas com "corpo HTML"), a chamada do parse (agora embrulhada) e o `BASELINE` 16 (agora 17).

**Comando 2** (`git grep -n -E 'score_relevance|…|rotulo_status' -- '*.py'`): dos símbolos da lista, a T2 muda só `_search_keyword_safe` (assinatura) e `_parse_sru_response` (contrato de erro). Todo call site foi conferido:
- `_parse_sru_response`: `test_comprehensive:336/357` (SRU válido e vazio, sem mudança) e `:370` (adaptado).
- `_search_keyword_safe`: ver o grep acima.

## 4. Evidência e2e (tester)

- Playwright, porta 8511, `channel="chrome"`: a busca chegou ao **Passo 4 em 145 s**, sem exceção.
- O relatório da v1.0 agora diz **"2 OK, 2 erros, 2 sem resultados"**; na T1 dizia "0 erros". Os erros são o LexML com `bloqueio_waf`.
- O Excel exportado tem 18 linhas.
- Screenshots em `bn-trilha-a/tests/evidencia/t2_passo4.png` e `t2_passo5.png` (**não versionados**).
- Ao vivo: 2 keywords `bloqueio_waf`, `retried=False`, e a 2ª com "causa cacheada".

## 5. Achados de teste e revisão, e para onde foram

| # | Achado | Destino |
|---|---|---|
| I1 | Um 200 que não é HTML nem XML (ex. `application/json`) virava `resposta_ilegivel` **sem `\| GET <url>`**, contra a regra "motivo e detalhe bastam para reproduzir com curl". Os comentários de fallback diziam "unreadable body". Tester obs. 1 = reviewer I1. | **Corrigido em `407e341`.** `_try_fetch` guarda `self._ultima_url`; `_search_keyword` envolve só o parse, anexa `\| GET <url>` com `redigir()` (a `FonteIndisponivel` só redige no `__init__`) e re-levanta para o `except` de fora. Assim a página seguinte continua parcial com `startRecord=21: resposta_ilegivel: …` (teste R3-H3 verde). **Sem** fallback novo. Comentários corrigidos. Teste novo `test_lexml_corpo_200_nao_html_nao_xml_e_ilegivel_com_url_no_detalhe`. |
| M1 | Comentário `# If we already know which URL works, use it directly` removido sem constar das remoções deliberadas. | **Restaurado em `407e341`.** |
| M2 | WAF ou HTML num URL já cacheado (`_sru_url`) sobe direto, sem entrar em `_urls_mortos` nem tentar fallback: o motivo sai certo, mas há requisições a mais e `cadeia_morta` nunca fica true. | Adiado → `_TODO.md` P3 (registrado pelo orquestrador). |
| obs. 2 | Keyword que a sanitização deixa vazia nunca é enviada, mas sai `empty` (comportamento antigo). | Adiado → P3; o conserto certo é em `search()`, fora do plano. |
| obs. 3 | Keywords além de `MAX_RETRIES`, ou cortadas por `max_results` no retry, ficam sem nota no detalhe. `retried=False` é verdade; falta a explicação. | Adiado → P3. |
| obs. 4 | UI v1.0: escape HTML duplo na mensagem e linha que estoura a largura. | É da **T9** (tela). |
| obs. 5 | O logger imprime a exceção crua (não redigida). Irrelevante para a URL fixa do LexML. | Fica na T2; é **item explícito da review da T5** (Google: a chave do CSE vai na query → logar `redigir(str(e))`). |
| Step 11(b) | `test_lexml_cql_injection_sanitization` continua fazendo rede real. | P3 no `_TODO.md` (orquestrador). |

## 6. Regras respeitadas

- Nenhum `secrets.toml` criado.
- Nenhum teste novo faz rede ou chama LLM (`requests.get` e `time.sleep` dublados).
- Arquivos em CRLF.
- A raiz `tests/` não foi adicionada (lá ficam os screenshots).
- Branch `deploy`, `execucao/*` e `_TODO.md` intocados.
- Push fica com o orquestrador.

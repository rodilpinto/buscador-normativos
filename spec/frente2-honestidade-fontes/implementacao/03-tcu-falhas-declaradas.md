# T3 · TCU classifica 5xx/4xx/503/HTML, declara paginação parcial e classifica por endpoint — registro de implementação

> Task: `../tasks/03-tcu-falhas-declaradas.md` (plano v4, linhas 1338-1764 — o plano é a fonte de verdade; a cópia
> da task foi conferida contra o plano por `diff`: idêntica).
> Trilha A, worktree `bn-trilha-a`, branch `frente2/trilha-a`, 23/09/2026.
> Commits: **`f044a3c`** `feat(frente2): TCU classifica 5xx/4xx/503/HTML e declara paginacao parcial`
> · **`e8d59a4`** `fix(frente2): review da T3 — formato inesperado e resposta_ilegivel/parcial; contagem por key; log`.
> Teste independente: **APROVADO**. Revisão de código: **APROVADO com 2 importantes + 1 menor** (todos aplicados em
> `e8d59a4`). Vereditos completos: `../execucao/revisoes/T3.md`.

## 1. O que foi feito

| Arquivo | Símbolos |
|---|---|
| `levantamento-normativos/searchers/tcu_searcher.py` | imports `re`, `datetime`, `urlencode`, `ZoneInfo`, `FonteIndisponivel`; `TCUSearcher.SOURCE_ID = "tcu"`; `search()` (3d: classificação por endpoint, `erro_primario`, `parcial`, detalhe gravado **sempre** com `N sem sumário`, `nao_consultada` no cap, `erro_interno` por keyword); `_texto_do_acordao` (3e, depois do `return` de `search()`; lê só `ementa` até a T4); `_fetch_all_pages`/`_fetch_all_pages_safe` → `(itens, erro, parcial)`; `_request_with_retry` levanta por classe (503 com hora BRT e hipótese; 404/429/4xx sem retry; 5xx/timeout/conexão após 3 tentativas); `_exigir_json` (200 não-JSON → `bloqueio_waf` ou `resposta_ilegivel`). **Fix:** formato inesperado → `resposta_ilegivel` com página, tipo, chaves e URL (I1); dedupe por `key` (I2); `logger.warning` da falha (menor 1) |
| `levantamento-normativos/requirements.txt` | `tzdata  # ZoneInfo no Windows nao tem base tz do sistema (rodada 3)` |
| `levantamento-normativos/test_comprehensive.py` | `test_tcu_search_empty_keywords`: mock `lambda url: ([], None, False)` + nota do contrato |
| `levantamento-normativos/tests/test_fontes_indisponiveis.py` | seção TCU: 10 testes do plano (9 + 1 `xfail strict` que a T4 destrava) + **3 da review** (I1 ×2, I2) e a classe `RespostaJsonNulo` |
| `tools/run_all_tests.py` | `BASELINE["tests/test_fontes_indisponiveis.py"]` 17 → 26 (`f044a3c`) → **29** (`e8d59a4`) |

Os blocos de código do plano foram colados como estão. Extraí-os por script do arquivo da task, sem redigitar. O 3d ficou exatamente entre as âncoras, com `# Final callback`, o `progress_callback` final e o `return` intactos. O 3e ficou depois do `return` e antes de `_matches_keyword` (R2-H4).

`tzdata` 2025.3 já estava instalado nesta máquina (`pip show tzdata`) e `ZoneInfo("America/Sao_Paulo")` resolve. Nada foi instalado.

## 2. Desvios do plano e por quê

1. **Documentação preservada** (acréscimo, sem mudar código):
   - seções `Args:` de `_request_with_retry` e de `_fetch_all_pages`, que os blocos do plano não traziam;
   - comentários originais que caíam dentro dos trechos substituídos: "The response may be a list directly or wrapped in an object. Handle both cases.", "If we got fewer items than PAGE_SIZE, no more pages", `# --- Step 2: Atos Normativos ---`, `# Track per-keyword statuses`, `# Filter acordaos/atos for this keyword`;
   - a frase que o 3d acrescenta ao docstring de `search()` foi quebrada em 4 linhas.
2. **Mensagem de commit.** Diz "Suite: 17 -> 26" em vez de "16 -> 25": o +1 é o teste da review da T2.
3. **Sem `git push`** (fica com o orquestrador); `_TODO.md` e `execucao/*` intocados.
4. **3 testes além do plano (review da T3):**
   - `test_tcu_200_json_sem_items_e_resposta_ilegivel`;
   - `test_tcu_json_nulo_na_segunda_pagina_e_parcial` — usa a classe nova `RespostaJsonNulo`, cujo `.json()` devolve `None`. O `RespostaFake` levanta quando `_json is None`, e assim o teste passaria pelo caminho "não é JSON" em vez do caminho "JSON `null`";
   - `test_tcu_itens_repetidos_entre_paginas_contam_uma_vez_por_key`.

   A suíte vai de 26 para 29 (+1 xfail), com o `BASELINE` atualizado no mesmo commit.
   ⚠ **Contagens desta suíte a partir daqui:** a T2 somou +1 e a T3 +3, então o plano fica +4:

   | Após | Plano | Real |
   |---|---|---|
   | T4 | 29 | **33** |
   | T5 | 37 | **41** |

   O total do runner também fica +4 em cada linha seguinte da tabela de BASELINE.
5. **Guarda extra no dedupe (I2).** Só `key` do tipo `str` ou `int` entra no conjunto de vistas; item sem `key`, ou com `key` não escalar, entra sempre. Uma `key` lista ou dict daria `TypeError`, e o `_fetch_all_pages_safe` transformaria o endpoint inteiro em `erro_interno`.
6. **Docstring de `search()`.** Ainda diz que o casamento é "in the ementa field". Isso é verdade na T3 (o `_texto_do_acordao` lê `ementa`); a T4 troca o campo e corrige o docstring.

## 3. Gates e saídas

### Ver falhar

Plano, Step 2 (`pytest tests/test_fontes_indisponiveis.py -q -k tcu`), antes do Step 3:

```
FAILED ...::test_tcu_500_num_endpoint_e_error_parcial_mesmo_com_o_outro_ok   (('empty','','tcu') != ('error','http_5xx','tcu'))
FAILED ...::test_tcu_503_e_manutencao_com_hora_e_hipotese                    (('empty','') != ('error','manutencao_503'))
FAILED ...::test_tcu_404_e_endpoint_inexistente_sem_retry                    ('' == 'endpoint_inexistente')
...                                                                           (+6: rate_limit, bloqueio_waf, timeout, parcial, detalhe vazio)
9 failed, 17 deselected, 1 xfailed in 0.83s
```

Todas as falhas são de assertion, nenhuma é `ImportError`. O `xfail strict` aparece como `xfailed`. A suíte tem 27 `def test_` (17 + 10).

Review, antes do fix:

```
test_tcu_200_json_sem_items_e_resposta_ilegivel         ('empty','') != ('error','resposta_ilegivel')
test_tcu_json_nulo_na_segunda_pagina_e_parcial          parcial False; detalhe "Acórdãos: erro_interno em AttributeError: 'NoneType' object has no attribute 'get'"
test_tcu_itens_repetidos_entre_paginas_contam_uma_vez_por_key   'Acórdãos: ok (60 itens' em vez de 50
3 failed, 27 deselected
```

### Ver passar

| Suíte | `f044a3c` (implementador) | `e8d59a4` (implementador) | Tester (`f044a3c`) |
|---|---|---|---|
| `tests/test_fontes_indisponiveis.py` | `26 passed, 1 xfailed` | `29 passed, 1 xfailed` | 26 + 1 xfailed |
| `test_comprehensive.py` | 98 | `Total: 98 \| Passed: 98 \| Failed: 0` | 98 |
| `test_phase4.py` | 58 | 58 | 58 |
| `test_searchers.py` | 13 | 13 | 13 (395 s) |

Runner (`timeout 900 python -u tools/run_all_tests.py`, foreground, raiz), TUDO VERDE, exit 0:

```
                                      f044a3c     e8d59a4
test_searchers.py                  13  390.5s   13  391.9s
test_llm_phase3.py                 53    2.5s   53    2.8s
test_comprehensive.py              98  137.9s   98  136.0s
test_phase4.py                     58    2.5s   58    2.4s
tests/test_fontes_indisponiveis.py 26    2.0s   29    2.0s
total                             248          251
```

- `python tools/golden_master.py comparar` → `golden-master OK`, nos dois commits.
- `git grep -n "_fetch_all_pages\|_request_with_retry" -- '*.py'` → só `tcu_searcher.py` (definições e chamadas internas) e `test_comprehensive.py:483-486` (o mock adaptado). Há também `tools/split_frente2.py:73`, mas ali é texto de critério de aceite, não call site. Os nomes antigos `acordao_error`/`atos_error` não existem mais em lugar nenhum.

⚠ `pytest tests/...` rodado da **raiz** do repo dá "29 failed" por import (`models`, `searchers`). O diretório certo é `levantamento-normativos/`, como dizem as Global Constraints; o runner já usa `cwd=APP`.

### Tempo do `test_searchers`: é paginação, não retry

Medido: 404.9s (fim da T2), 390.5s (`f044a3c`), 391.9s (`e8d59a4`). A T3 não moveu o tempo, e não deveria mover.

Uma chamada ao vivo de `TCUSearcher().search(["governança de TI"])` levou **127,9 s**:
- **~114 s** baixando o endpoint de acórdãos: ~26 páginas a ~4,4 s cada (1,5–2 s de `_rate_limit` + ~2,5 s de resposta).
- **~13 s** nas 3 tentativas do HTTP 500 do endpoint de atos (backoff 2 s + 4 s + as requisições).

A T3 mantém o retry em 5xx de propósito. Ela só tira o retry de 4xx, 503 e 200 não-JSON, e nenhum desses acontece ao vivo hoje.

O `test_searchers` faz **2** buscas TCU ao vivo: o teste 8, e o teste 11, que chama `search(["test"], max_results=0)` e baixa tudo mesmo sem poder devolver nada. São ~256 s dos ~390 s.

📝 Sugestões minhas, não validadas: `return` cedo quando `max_results <= 0`, ou cache das páginas por processo. Qualquer uma cortaria ~metade do tempo. A primeira foi adiada para o P3 pelo orquestrador.

**520 a 580 itens com teto de 500 (MAX_PAGES × PAGE_SIZE).** O tester mediu que a API às vezes devolve **40 itens** numa página pedida com `quantidade=20`: 580 itens, 500 keys únicas. O `extend` somava as repetições, então o "ok (N itens, M sem sumário)" que o usuário vê mostrava um N inflado e variável (520 no meu teste, 540 e 580 nos do tester). Os resultados em si nunca duplicaram, porque `results_by_id` deduplica. **Corrigido em `e8d59a4`** (dedupe por `key`, I2).

Resultado ao vivo com `f044a3c`: `error http_5xx parcial=True`, e o detalhe traz:

```
Acórdãos: ok (520 itens, 327 sem sumário — nesses só o título casa); Atos: http_5xx em HTTP 500 em 3 tentativas; corpo: '{"url":"Erro no serviço, contate o administrador","erro":"…HttpClientErrorException: 404 Not Found…' | GET …recupera-atos-normativos?inicio=0&quantidade=20
```

### Auditoria de documentação (os 2 comandos, lidos inteiros)

**`f044a3c`** — linhas removidas e destino:

| Removido | Destino |
|---|---|
| laço antigo de `search()` (inclusive `# Both endpoints failed — keyword status is error`) | bloco 3d; o comentário vira o do `erro_primario` ("Um endpoint que caiu na PRIMEIRA pagina torna a busca error…") |
| `_fetch_all_pages_safe` antigo (`(items, error_message)`, log `error fetching`) | contrato novo; o log vira `TCU: erro interno em {url}` |
| `break  # API error; return what we have` | docstring de `_fetch_all_pages` ("Antes, qualquer falha era `break` silencioso") |
| log `TCU: unexpected response format` | `FonteIndisponivel("resposta_ilegivel", "formato inesperado …")` |
| docstring "Handles the TCU maintenance window (503 between 20:00-21:00 BRT) with a user-friendly log message" e o `logger.warning` do 503 ("A API do TCU fica indisponivel diariamente das 20h as 21h…") | o fato vai para o `Raises:` de `_request_with_retry` e para o detalhe que o usuário vê ("HTTP 503 às dd/mm HH:MM BRT (dentro/fora da janela de manutenção conhecida, 20h-21h); hipótese, não fato"). O rastro no console foi **restaurado em `e8d59a4`** (menor 1) |
| logs de retry e de falha após retry | mantidos no código novo, com o mesmo texto |
| `Returns: … or None on failure` | contratos novos (`Raises:`) |

**`e8d59a4`** — removidos só `all_items.extend(items)` (virou o laço com dedupe, com comentário) e o `BASELINE` 26 (agora 29).

**Comando 2:** mudaram de assinatura `_fetch_all_pages`, `_fetch_all_pages_safe` e `_request_with_retry`; todo call site foi conferido (grep acima). `_map_acordao` não muda nesta task. `_texto_do_acordao` é novo e só aparece em `tcu_searcher` e nos testes.

## 4. Evidência e2e (tester)

- Playwright, porta 8511: Passo 4 "(16 normativos)", sem exceção.
- O relatório da v1.0 agora diz **"2 OK, 4 erros, 0 sem resultados"**: o TCU aparece como **erro** e não mais como "sem resultados". Na T2 era "2 OK, 2 erros, 2 sem resultados".
- Excel com 18 linhas, 0 do TCU. Isso é esperado até a T4, porque a API não devolve `ementa`.
- Screenshots `bn-trilha-a/tests/evidencia/t3_passo4.png` e `t3_passo5.png` (**não versionados**).
- Ao vivo (`search(["turismo"])`): 131,5 s, `error/http_5xx/parcial`, "Acórdãos: ok (540 itens, 347 sem sumário…); Atos: http_5xx…".
- Sondas do tester: 40/40.

## 5. Achados de teste e revisão, e para onde foram

| # | Achado | Destino |
|---|---|---|
| I1 = (a)+(b) | `_fetch_all_pages`: um dict sem `items`/`data` passava em silêncio (`{"outra":1}` → `empty` "ok (0 itens)"; um 200 com o corpo de erro do TCU seria lido como "sem resultado"). JSON string, número ou `null` → `AttributeError` → `erro_interno` sem URL; na página 2 isso descartava a página 1 com `parcial=False`. | **Corrigido em `e8d59a4`.** Antes do `items = …`: se não é list nem dict, ou é dict sem `items`/`data` → `resposta_ilegivel` `"pagina N (inicio=…): formato inesperado <tipo> [chaves=…] \| GET …"`, devolvido como `all_items, erro, page > 0`. 2 testes. |
| I2 = (c) | O contador incluía duplicatas: a API devolve 40 itens para `quantidade=20` (580 itens / 500 keys), e o detalhe ficava inflado e variável. | **Corrigido em `e8d59a4`.** Dedupe por `key` ao acumular; a parada continua pelo tamanho cru da página. 1 teste. |
| Menor 1 | 503, 4xx, não-JSON e formato inesperado não logavam mais no console. | **Corrigido em `e8d59a4`.** `logger.warning(f"TCU: {e}")` no `except FonteIndisponivel` e no formato inesperado; o detalhe já vem redigido. |
| — | `ChunkedEncodingError`/`ContentDecodingError` viram `erro_interno` sem retry. | Adiado → `_TODO.md` P3. |
| — | `nao_consultada` e `erro_interno` por keyword não carregam `parcial` nem o resumo dos endpoints. | Adiado → P3. |
| (d) | O regex de `redigir` come o separador seguinte ao segredo (`token=abc;` → `token=***`). | Adiado → P3 (item da T1: `[^&\s;,)'"]+` + teste). |
| — | `max_results=0` baixa tudo mesmo assim (~128 s por chamada; metade do `test_searchers`). | Adiado → P3. |
| UI | Escape HTML duplo em `app.py:876` (pré-existente). | **T9**. |

## 6. Regras respeitadas

- Nenhum `secrets.toml` criado.
- Nenhum teste novo faz rede ou chama LLM (`requests.get` e `time.sleep` dublados).
- Arquivos em CRLF.
- A raiz `tests/` não foi adicionada.
- Branch `deploy`, `execucao/*` e `_TODO.md` intocados.
- Push fica com o orquestrador.

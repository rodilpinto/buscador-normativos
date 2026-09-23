# T5 · Google/DuckDuckGo entra no vocabulário mínimo — registro de implementação

> Task: `../tasks/05-google-vocabulario.md` (plano v4 — o plano é a fonte de verdade; a cópia da task foi conferida
> contra o plano por `diff`: idêntica). ⚠ Emenda à spec §5.
> Trilha A, worktree `bn-trilha-a`, branch `frente2/trilha-a`, 23/09/2026. Última task da trilha A.
>
> Commits:
> - **`5dad3c7`** `feat(frente2): Google/DDG entra no vocabulario — 'No results' e empty, nao error; retry honesto; cap declarado`
> - **`e70d9f6`** `fix(frente2): review da T5 — teste do log que falha de verdade; detalhe do bloqueio; spec 5 emendada`
>
> Teste independente: **APROVADO**, sem defeito de código. Revisão: **APROVADO com 1 importante** (no teste), aplicado
> em `e70d9f6`. Vereditos completos: `../execucao/revisoes/T5.md`.

## 1. O que foi feito

| Arquivo | Símbolos |
|---|---|
| `levantamento-normativos/searchers/google_searcher.py` | ver o detalhamento abaixo |
| `levantamento-normativos/tests/test_fontes_indisponiveis.py` | 8 testes do plano (seção Google/DDG; `_ddg_com`, `_um_resultado`) + **1 além do plano**: `test_cse_falha_nao_vaza_a_chave_no_log`, reescrito em `e70d9f6` |
| `tools/run_all_tests.py` | `BASELINE[...]` 36 → **45** |
| `docs/superpowers/specs/…-design.md` §5 | linha de `google_searcher.py` + nota `⚠ Emendado em 23/09 (plano v4, T5; …)` (`e70d9f6`) |

Mudanças em `google_searcher.py`:
- **Imports:** `from typing import Optional` (R3-B2: sem ele o app inteiro não importa), `FonteIndisponivel`, `redigir`.
- **`SOURCE_ID = "google"`.**
- **Backends:** `_search_urls`, `_search_ddgs`, `_search_cse_api` e `_search_scraping` devolvem `(resultados, FonteIndisponivel | None)`.
  - DDG `"No results found."` → `empty`, sem erro.
  - `RatelimitException` é testada antes de `DDGSException`.
  - CSE: 429/403/404/4xx/5xx mapeados; 200 não-JSON → `resposta_ilegivel`; `Timeout` antes de `ConnectionError`.
- **Laço principal (3f):** `nao_consultada` no corte por `max_results`.
- **Bloqueio do scraping:** `motivo="bloqueio_waf"` e, em `e70d9f6`, o fato no detalhe.
- **Laço de retry (3g):** colado **inteiro**.
  - Um retry que dá certo diz de que recuperou.
  - Um retry pulado **não** marca `retried`.
  - As keywords além de `MAX_GOOGLE_KEYWORDS` ganham `nao_consultada`, depois do retry e antes do callback final.
- **`source=self.SOURCE_ID`** em todo `KeywordStatus`. O `NormativoResult(source="google")` fica literal, como o plano diz.
- **Logs** com URL ou exceção passam por `redigir()` (item carregado; ver §2).

Os blocos de código do plano foram colados como estão. Extraí-os por script do arquivo da task, e cada trecho foi substituído entre as âncoras citadas.

## 2. Desvios do plano e por quê

1. **Item carregado da review da T2 (além do plano): a chave do CSE não pode ir para o log.** A chave vai na query string, e a mensagem crua do `requests` traz a URL inteira.
   - O `logger.warning` do laço loga a `FonteIndisponivel`, cujo detalhe já é redigido no `__init__` (comentado no código).
   - Os logs de `_is_safe_url` (SSRF) e de `_fetch_page_metadata` ("Skipping unsafe URL" e o debug com URL + exceção) passaram a usar `redigir(...)`.
   - Teste `test_cse_falha_nao_vaza_a_chave_no_log`, com `caplog` em DEBUG.
   - Antes do código novo, o log mostrava `…/customsearch/v1?key=AIzaSECRETO123&cx=&q=x…`.
2. **O teste do log agora falha de verdade** (review da T5, importante). A 1ª versão não podia falhar: o ramo `conexao` corta `str(e)` em 120 chars e o segredo longo nunca chegava ao detalhe. O reviewer provou com um mutante (`redigir` → identidade): o teste passava.
   - Conserto: segredo **curto** (`"AIzaK1"`) no **começo** da mensagem da exceção, e `assert "key=***" in st.detalhe`.
   - **Prova com mutante** (script descartável fora do repo, **não commitado**: um plugin do pytest troca `models.redigir` e `searchers.google_searcher.redigir` pela identidade):
     ```
     == mutante (redigir = identidade) ==
     E  assert 'key=***' in "conexao recusada/sem rota (/customsearch/v1?key=AIzaK1&cx=&q=x&num=10&lr=lang_pt Max retries exceeded …) | GET https://www.googleapis.com/customsearch/v1"
     WARNING searchers.google_searcher:google_searcher.py:276 Google search failed for 'x': conexao: … key=AIzaK1 …
     1 failed, 44 deselected
     == codigo real ==
     1 passed, 44 deselected
     ```
   - A contagem ficou em 45.
3. **Detalhe do bloqueio do scraping** (review, menor): `"0 resultados em N palavras-chave seguidas (scraping) — provável bloqueio de IP, hipótese, não fato"`, com comentário. Nenhum teste afirmava `detalhe == ""` para esse status.
4. **Docstring de `search()`:** 2 linhas sobre `nao_consultada` (keywords além de `MAX_GOOGLE_KEYWORDS` ou cortadas por `max_results`).
5. **Spec §5**, devida pela T5 e omitida nos steps do plano: linha nova na tabela "Arquivos tocados" e nota datada. Nada apagado.
6. **Contagens:** suíte 36 → 45 (plano: 29 → 37). O +8 sobre o plano é: +7 das reviews e do tester de T2–T4, e +1 daqui. O commit diz isso. Sem `git push`.

## 3. Gates e saídas

**Ver falhar**, antes do código novo, com os 9 testes novos:

```
('error','','google') != ('empty','','google')     # DDG "No results found."
'' == 'timeout' · '' == 'erro_interno'
[] == ['k5','k6']                                   # nao_consultada ausente
2 == 7                                              # corte por max_results
'' == 'recuperado no retry após timeout'
[True, True, True] == [True, False, False]          # retry pulado marcava retried
'' == 'resposta_ilegivel' · '' == 'conexao'
WARNING … Google CSE: erro de rede: HTTPSConnectionPool(…) … /customsearch/v1?key=AIzaSECRETO123&cx=&q=x…
```

(Um re-run com `-p no:logging` deu "8 failed, 1 error". O erro é artefato do comando: essa flag desliga o `caplog`.)

**Ver passar:**
- Suíte: `45 passed`.
- `python -c "from searchers import GoogleSearcher"` importa (`SOURCE_ID` google).
- `test_phase4`: 58.
- `git grep -n "_search_urls\|error_msg" -- …google_searcher.py 'levantamento-normativos/test_*.py'` → só a definição (`:130`) e as 2 chamadas (`search_results, erro = …`); nenhum `error_msg`. Nenhum teste chamava `_search_urls` nem afirmava `error_message` do Google, então `test_searchers` e `test_comprehensive` não mudaram.

Runner (`timeout 900 python -u tools/run_all_tests.py`, foreground), TUDO VERDE, exit 0:

```
                                      5dad3c7     e70d9f6
test_searchers.py                  13  200.3s   13  222.4s
test_llm_phase3.py                 53    2.6s   53    2.7s
test_comprehensive.py              98   73.1s   98   77.8s
test_phase4.py                     58    2.4s   58    2.4s
tests/test_fontes_indisponiveis.py 45    1.7s   45    1.7s
total                             267          267
```

- `python tools/golden_master.py comparar` → `golden-master OK`, nos dois commits.

**Tester (sobre `5dad3c7`):**
- Suíte 45, import OK, runner 267 em foreground (4m40s), golden OK, grep limpo, auditoria sem perda, CRLF.
- **Sondas 26/26:**
  - exceções do ddgs na ordem certa;
  - CSE 429/403/404/400/500/200 não-JSON/200 sem `items`/timeout/conexão → motivos certos;
  - **nenhum `AIza…`** em status, `repr`, `str(erro)`, `erro.args` nem no caplog DEBUG dos `searchers.*`;
  - 7 keywords com `max_results=2` → 7 status (2 ok + 5 `nao_consultada` com os dois textos certos);
  - `retried` verdadeiro; `seen_urls` respeitado no retry; `bloqueio_waf` no scraping.

**Auditoria de documentação (os 2 comandos):**
- `5dad3c7`: removidos os retornos `(list, str)`, o `error_msg` e a marcação antiga do retry pulado (`retried = True` + `"API indisponivel (retry skipped)"`, que vira `retry pulado: …` no detalhe, como no LexML).
- As mensagens de usuário do CSE sobrevivem nos detalhes novos: "cota diária excedida (100 queries/dia no plano gratuito)", "acesso negado (verifique GOOGLE_API_KEY e GOOGLE_CSE_ID)". "timeout na requisicao" vira "sem resposta em 15s | GET …".
- Os 3 logs com URL/exceção foram embrulhados em `redigir`.
- Nenhum comentário nem docstring perdido.
- `e70d9f6`: removidas só as linhas da 1ª versão do teste do log (docstring estendido, segredo, mensagem e asserts reescritos).
- Símbolos com assinatura mudada: `_search_urls` e os 3 backends. Todo call site está dentro de `google_searcher.py`.

## 4. Evidência e2e (tester)

- Playwright, porta 8511: Passo 4 "(17 normativos)", Google ok. O Excel abre.
- Com 7 keywords, a `nao_consultada` do Google aparece no relatório v1.0 como erro com mensagem vazia. É da **T9** (tela), já carregado.
- Screenshots `bn-trilha-a/tests/evidencia/t5_*_passo{4,5}.png` (**não versionados**).

## 5. Achados de teste e revisão, e para onde foram

| # | Achado | Destino |
|---|---|---|
| Importante (reviewer) | O teste do log não podia falhar (corte de 120 chars; mutante passava). | **Corrigido em `e70d9f6`** + prova com mutante (§2.2). |
| Menor (reviewer) | `bloqueio_waf` do scraping sem `detalhe`. | **Corrigido em `e70d9f6`**. |
| Dívida de doc (tester item 5 / reviewer 1) | Spec §5 sem linha para `google_searcher.py` nem nota "⚠ Emendado". | **Corrigido em `e70d9f6`**. |
| Resíduo (tester / reviewer 2) | Com o urllib3 em DEBUG e resposta 500, o próprio urllib3 loga a linha da requisição com `key=AIza…`. O padrão é WARNING (`app.py:38` fixa WARNING). | Adiado → `_TODO.md`, **frente 5**. |
| reviewer 3 | Keyword além de `MAX_RETRIES` fica sem nota no detalhe. | Adiado → `_TODO.md` P3 (mesma entrada da obs. 3 do LexML). |
| 📝 tester | O ddgs devolveu lista vazia depois de respostas HTTP 202 do DDG ("COBIT", "ISO 27001" → "sem resultado"): possível mascaramento do lado do ddgs, não investigado. | Adiado → `_TODO.md` P3. |
| tester | `nao_consultada` aparece como erro com mensagem vazia na tela v1.0. | **T9** (já carregado). |

## 6. Regras respeitadas

- Nenhum `secrets.toml` criado.
- Nenhum teste novo faz rede ou chama LLM (`ddgs.DDGS` e `requests.get` dublados).
- O mutante rodou fora do repo e não foi commitado.
- Arquivos em CRLF.
- A raiz `tests/` não foi adicionada.
- Branch `deploy`, `execucao/*`, `_TODO.md`, o plano e `tasks/*` intocados.
- Push fica com o orquestrador.

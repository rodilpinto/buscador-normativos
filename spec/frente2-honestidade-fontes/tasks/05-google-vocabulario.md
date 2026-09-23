---
task: 5
fase: "Fase 2 — Fontes honestas"
plan: docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md (linhas 1886-2203)
reference: spec/frente2-honestidade-fontes/reference/global-constraints.md
depends_on: [T1, T2]
---

> Extraído **verbatim** do plano v4 (linhas 1886-2203). **O plano segue fonte de verdade**:
> divergência entre o plano e esta cópia → o plano ganha. Status em `../execucao/TODOS.md` — **não marque
> os checkboxes aqui**. Antes de começar, ler `../reference/global-constraints.md` (Global
> Constraints, Estrutura de arquivos, BASELINE por task). Ordem e dependências: `../00-overview.md`.

# T5 · Google/DuckDuckGo entra no vocabulário mínimo (⚠ emenda à spec §5)

**Fase 2 — Fontes honestas.**

## Depende de

- **T1** — `FonteIndisponivel`, `KeywordStatus` novos
- **T2** — `RespostaFake` e a suíte nova (usada pelo teste do CSE)

**Arquivos compartilhados com outras tasks:** `tests/test_fontes_indisponiveis.py` · runner. **Não** consome código da T3/T4, mas soma na mesma suíte e no mesmo `BASELINE` — por isso vem depois delas.

## Critérios de aceite

> Derivados do próprio plano (os "Ver passar", "Expected" e gates da task e das Global
> Constraints) — **nenhum critério novo**. Números são previsões do plano: se o observado
> divergir, contar os `def test_` do bloco da task antes de suspeitar do código.

- Suíte nova → **`37 passed`** (29 + 8) — Step 4.
- `python -c "from searchers import GoogleSearcher"` importa (R3-B2: sem `from typing import Optional` o app inteiro não sobe).
- `DDGSException("No results found.")` → `empty` sem motivo; timeout/ratelimit mapeados; keywords além de 5 e as cortadas por `max_results` ganham `nao_consultada`; retry pulado **não** marca `retried`.
- `git grep` sem resto de `error_msg` em `google_searcher.py`; `test_searchers` 13/13; `test_comprehensive` 98/98.
- `BASELINE` 37; runner TUDO VERDE (total **259**); golden OK; auditoria; commit + push.

---

## Conteúdo da task (verbatim do plano)

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

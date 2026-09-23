---
task: 3
fase: "Fase 2 — Fontes honestas"
plan: docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md (linhas 1338-1764)
reference: spec/frente2-honestidade-fontes/reference/global-constraints.md
depends_on: [T1, T2]
---

> Extraído **verbatim** do plano v4 (linhas 1338-1764). **O plano segue fonte de verdade**:
> divergência entre o plano e esta cópia → o plano ganha. Status só no `_TODO.md` — **não marque
> os checkboxes aqui**. Antes de começar, ler `../reference/global-constraints.md` (Global
> Constraints, Estrutura de arquivos, BASELINE por task). Ordem e dependências: `../00-overview.md`.

# T3 · TCU classifica 5xx/4xx/503/HTML, declara paginação parcial e classifica por endpoint

**Fase 2 — Fontes honestas.**

## Depende de

- **T1** — `FonteIndisponivel`, `KeywordStatus` novos
- **T2** — a suíte `tests/test_fontes_indisponiveis.py` (`RespostaFake`, `DESAFIO_HTML`, fixture `autouse`) e o registro dela no runner

**Arquivos compartilhados com outras tasks:** `tests/test_fontes_indisponiveis.py` · `test_comprehensive.py` · `requirements.txt` · runner

## Critérios de aceite

> Derivados do próprio plano (os "Ver passar", "Expected" e gates da task e das Global
> Constraints) — **nenhum critério novo**. Números são previsões do plano: se o observado
> divergir, contar os `def test_` do bloco da task antes de suspeitar do código.

- Suíte nova → **`25 passed, 1 xfailed`** (26 coletados; o `xfail strict` é destravado na T4) — Step 5.
- `test_comprehensive.py` → 98/98; `test_searchers.py` → 13/13.
- `tzdata` no `requirements.txt`; `git grep -n "_fetch_all_pages\|_request_with_retry" -- '*.py'` sem call site além dos previstos (Step 4).
- O `detalhe` do TCU é gravado **sempre**, inclusive em `empty`, e conta `N sem sumário` (R3-H5, R3-B1).
- `BASELINE` da suíte = 25; runner TUDO VERDE (total **247**); golden OK; auditoria; commit + push.

---

## Conteúdo da task (verbatim do plano)

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

---
task: 2
fase: "Fase 2 — Fontes honestas"
plan: docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md (linhas 583-1334)
reference: spec/frente2-honestidade-fontes/reference/global-constraints.md
depends_on: [T1]
---

> Extraído **verbatim** do plano v4 (linhas 583-1334). **O plano segue fonte de verdade**:
> divergência entre o plano e esta cópia → o plano ganha. Status em `../execucao/TODOS.md` — **não marque
> os checkboxes aqui**. Antes de começar, ler `../reference/global-constraints.md` (Global
> Constraints, Estrutura de arquivos, BASELINE por task). Ordem e dependências: `../00-overview.md`.

# T2 · LexML declara bloqueio, timeout, 5xx, paginação parcial e `nao_consultada`

**Fase 2 — Fontes honestas.**

## Depende de

- **T1** — `FonteIndisponivel`, campos `motivo`/`detalhe`/`parcial` de `KeywordStatus`, `redigir`, `SOURCE_ID` na base

**Arquivos compartilhados com outras tasks:** `tests/test_fontes_indisponiveis.py` (**criado aqui**; T3, T4, T5 acrescentam) · `test_comprehensive.py` (T3, T4) · runner

## Critérios de aceite

> Derivados do próprio plano (os "Ver passar", "Expected" e gates da task e das Global
> Constraints) — **nenhum critério novo**. Números são previsões do plano: se o observado
> divergir, contar os `def test_` do bloco da task antes de suspeitar do código.

- `python -m pytest tests/test_fontes_indisponiveis.py -q` → **`16 passed`** (Step 12).
- `python test_comprehensive.py | tail -3` → `Total: 98 | Passed: 98 | Failed: 0`; `python test_searchers.py | tail -2` → `13/13 passed` (**anotar o tempo**, era ~390s); `test_phase4.py` → `58 passed`.
- Cenário real de 22/09 (primário = desafio HTML, fallbacks = 404): as 3 keywords saem `bloqueio_waf`, com 3 requisições no total, `retried=False` e `retry pulado` no detalhe (teste `test_lexml_cenario_real_…`).
- `git grep -n "_search_keyword_safe" -- '*.py'` → só `lexml_searcher.py` e os testes (Step 11c).
- Runner: `SUITES_PYTEST` inclui a suíte nova; `BASELINE["tests/test_fontes_indisponiveis.py"] = 16`; TUDO VERDE (total **238**); golden OK; auditoria; commit + push.

---

## Conteúdo da task (verbatim do plano)

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

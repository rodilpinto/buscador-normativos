# Frente 2 — Honestidade das fontes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer o app dizer a verdade quando uma fonte não pôde ser consultada e de onde veio cada nota de relevância — na tela e na planilha — sem mudar o que ele busca nem como deduplica.

**Architecture:** Uma exceção tipada (`FonteIndisponivel`, com `motivo` e `detalhe`) nasce nos searchers e sobe até `KeywordStatus`, que ganha os mesmos campos mais `parcial`. A nota de relevância ganha um campo irmão `relevancia_origem` preenchido por uma função nova ao lado da existente. A planilha ganha uma coluna e uma aba; a tela, rótulos honestos. Cada mudança é provada por teste sem rede (fixtures, dublês de `requests.get`) e pelo golden-master.

**Tech Stack:** Python 3.13.7 · Streamlit 1.55 · requests · openpyxl 3.1.5 · pytest 9 · Playwright (Python, `channel="chrome"`) só para o gate visual.

**Spec:** `docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md` — seções citadas como §3.x.

## Global Constraints

- **Texto normativo NUNCA é parafraseado.** Nada aqui toca `nome`/`ementa`.
- **O sistema roda inteiro sem LLM.** Todo teste novo roda com `GEMINI_API_KEY` vazia; nenhum teste novo faz rede.
- **Rastreabilidade é essência:** `motivo` e `detalhe` têm de bastar para reproduzir o problema com `curl`.
- **Separar fato de sugestão:** marcar `📝` o que for proposta não validada.
- **UTF-8 explícito em todo `open()` / `read_text` / `write_text`.**
- **Rodar Python via Bash, não PowerShell.** Prefixar `PYTHONIOENCODING=utf-8` em comando que imprime acento.
- **Acima de 260 caracteres o Python falha em silêncio no Windows.**
- **Documentação move junto com o código.** Toda docstring alterada é reescrita, não apagada. Gate no fim de cada task: `git diff -U0 HEAD~1 -- '*.py' | grep '^-' | grep -v '^---'` lido **inteiro**, sem `head`.
- **Golden-master:** `python tools/golden_master.py comparar` tem de dar OK ao fim de **toda** task, exceto a Task 6, que recongela **no mesmo commit** e diz por quê. `dedup_esperado.json` **nunca** muda nesta frente.
- **Runner:** `python tools/run_all_tests.py` TUDO VERDE ao fim de toda task (≈9 min; as suítes LIVE são lentas por causa das fontes quebradas — é esperado). Task que acrescenta teste atualiza `BASELINE` **no mesmo commit** (o runner avisa `cresceu` se esquecer).
- **Push a cada task fechada** (D-C7). `git push origin master`.
- **Vocabulário fechado.** `MOTIVOS` e `ORIGENS_RELEVANCIA` vivem em `models.py`; nenhum outro arquivo inventa valor.
- **Diretório de trabalho dos comandos:** a raiz do repo (`~/Documents/solucoes/buscador-normativos/`) para `tools/`; `levantamento-normativos/` para `pytest` e os scripts de teste. Cada step diz qual.
- ⚠ **Emenda à spec §3.1 (feita neste plano):** `MOTIVOS` ganha dois valores que a spec não listou e a implementação exige: `endpoint_inexistente` (404 em todos os URLs — não é `conexao`) e `erro_interno` (exceção não prevista — não é `resposta_ilegivel`). Registrado na spec na Task 1, Step 6.

---

## Estrutura de arquivos

| Arquivo | Responsabilidade nesta frente |
|---|---|
| `levantamento-normativos/models.py` | vocabulário (`MOTIVOS`, `ORIGENS_RELEVANCIA`), campos novos em `KeywordStatus` e `NormativoResult` |
| `levantamento-normativos/searchers/base.py` | `FonteIndisponivel` |
| `levantamento-normativos/searchers/lexml_searcher.py` | sniff de conteúdo, `ParseError` levanta, cache de falha, mapeamento para `motivo` |
| `levantamento-normativos/searchers/tcu_searcher.py` | `_request_with_retry` levanta; `_fetch_all_pages` → `(itens, erro, parcial)`; classificação por endpoint |
| `levantamento-normativos/llm/gemini_client.py` | `score_relevance_com_origem`; `score_relevance` vira wrapper |
| `levantamento-normativos/llm/__init__.py` | exporta a função nova |
| `levantamento-normativos/deduplicator.py` | `_merge` leva `relevancia_origem` |
| `levantamento-normativos/excel_export.py` | coluna "Origem da nota"; aba "Diagnostico da busca"; `diagnostico=` |
| `levantamento-normativos/app.py` | pontuação sempre; relatório; aviso; card; preview; `diagnostico=` |
| `levantamento-normativos/tests/test_fontes_indisponiveis.py` | **novo** — pytest, sem rede |
| `levantamento-normativos/tests/fixtures/lexml_desafio_senado.html` | ✅ **já capturado em 22/09** (9.049 bytes, o HTML real do desafio) |
| `levantamento-normativos/tests/fixtures/lexml_sru_valido.xml` | **novo** — SRU mínimo com 1 registro |
| `levantamento-normativos/test_phase4.py` | asserts 10 → 11; testes de vocabulário, `_merge` e planilha |
| `levantamento-normativos/test_llm_phase3.py` | seção 9: origem da nota |
| `tools/run_all_tests.py` | suíte nova em `SUITES_PYTEST`; `BASELINE` por task |
| `tools/dirigir_app.py` | **novo** — gate visual V11 (Playwright) |
| `tests/golden/planilha_sha256.txt` · `ambiente.txt` | recongelados na Task 6 |

---

### Task 1: Vocabulário e campos novos (`models.py`)

**Files:**
- Modify: `levantamento-normativos/models.py:59-63` (defaults de `NormativoResult`) e `:95-100` (`KeywordStatus`)
- Test: `levantamento-normativos/test_phase4.py` (classe nova no fim)
- Modify: `tools/run_all_tests.py:47-52` (`BASELINE["test_phase4.py"]`)
- Modify: `docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md` §3.1 (emenda dos 2 motivos)

**Interfaces:**
- Produces:
  - `MOTIVOS: frozenset[str]` = `{"", "bloqueio_waf", "http_5xx", "manutencao_503", "timeout", "conexao", "resposta_ilegivel", "endpoint_inexistente", "erro_interno"}`
  - `ORIGENS_RELEVANCIA: frozenset[str]` = `{"modelo", "heuristica", "fallback_erro", "padrao_fonte"}`
  - `KeywordStatus(..., motivo: str = "", detalhe: str = "", parcial: bool = False)`; `__post_init__` levanta `ValueError` se `motivo not in MOTIVOS`
  - `NormativoResult(..., relevancia_origem: str = "padrao_fonte")`; `__post_init__` levanta `ValueError` se fora de `ORIGENS_RELEVANCIA`

- [ ] **Step 1: Escrever os testes que falham** — acrescentar ao **fim** de `levantamento-normativos/test_phase4.py`:

```python
# ===========================================================================
#  FRENTE 2 — VOCABULARIO DE HONESTIDADE (spec 2026-09-22 §3.1)
# ===========================================================================

from models import KeywordStatus, MOTIVOS, ORIGENS_RELEVANCIA


class TestVocabularioHonestidade:
    """KeywordStatus e NormativoResult carregam motivo/detalhe/parcial e origem da nota."""

    def test_motivos_fechados(self):
        assert MOTIVOS == frozenset({
            "", "bloqueio_waf", "http_5xx", "manutencao_503", "timeout", "conexao",
            "resposta_ilegivel", "endpoint_inexistente", "erro_interno",
        })

    def test_origens_fechadas(self):
        assert ORIGENS_RELEVANCIA == frozenset(
            {"modelo", "heuristica", "fallback_erro", "padrao_fonte"}
        )

    def test_keyword_status_construtor_antigo_continua_valido(self):
        s = KeywordStatus(keyword="lgpd", source="lexml", result_count=0, status="empty")
        assert (s.motivo, s.detalhe, s.parcial) == ("", "", False)

    def test_keyword_status_aceita_motivo_valido(self):
        s = KeywordStatus(keyword="lgpd", source="lexml", status="error",
                          motivo="bloqueio_waf", detalhe="HTTP 200 text/html", parcial=False)
        assert s.motivo == "bloqueio_waf"

    def test_keyword_status_rejeita_motivo_inventado(self):
        with pytest.raises(ValueError, match="motivo"):
            KeywordStatus(keyword="lgpd", source="lexml", status="error", motivo="waf")

    def test_normativo_origem_default_e_padrao_fonte(self):
        assert _make_result().relevancia_origem == "padrao_fonte"

    def test_normativo_aceita_origem_valida(self):
        r = NormativoResult(nome="x", tipo="Lei", numero="1", data=None, orgao_emissor="",
                            ementa="", link="", source="lexml", found_by="k",
                            relevancia_origem="heuristica")
        assert r.relevancia_origem == "heuristica"

    def test_normativo_rejeita_origem_inventada(self):
        with pytest.raises(ValueError, match="relevancia_origem"):
            NormativoResult(nome="x", tipo="Lei", numero="1", data=None, orgao_emissor="",
                            ementa="", link="", source="lexml", found_by="k",
                            relevancia_origem="ia")
```

- [ ] **Step 2: Rodar e ver falhar**

Run (em `levantamento-normativos/`): `python -m pytest test_phase4.py -q -k Vocabulario`
Expected: `ImportError: cannot import name 'MOTIVOS'` (a coleta falha antes de rodar) — é a falha esperada.

- [ ] **Step 3: Implementar em `models.py`**

Logo após `from dataclasses import dataclass, field`:

```python
# ---------------------------------------------------------------------------
# Vocabulario fechado de honestidade (spec 2026-09-22 §3.1)
# ---------------------------------------------------------------------------

# Por que uma fonte NAO pode ser consultada. String (nao Enum) para caber na
# planilha e no JSON sem conversao. "" = nao se aplica (status ok/empty).
MOTIVOS: frozenset[str] = frozenset({
    "",
    "bloqueio_waf",          # HTTP 200 com pagina de desafio (Senado/LexML, medido em 22/09)
    "http_5xx",              # 5xx depois dos retries
    "manutencao_503",        # janela diaria do TCU (20h-21h BRT)
    "timeout",               # requests.Timeout
    "conexao",               # requests.ConnectionError
    "resposta_ilegivel",     # HTTP 200, mas o corpo nao e o formato esperado
    "endpoint_inexistente",  # 404 em todos os URLs da cadeia
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
```

Em `NormativoResult`, na docstring, depois da linha de `relevancia`:

```
        relevancia_origem: De onde veio ``relevancia``. Um de ORIGENS_RELEVANCIA.
              Default "padrao_fonte": os searchers atribuem uma constante e
              nenhuma avaliacao rodou ainda.
```

Depois de `relevancia: float = 0.0`:

```python
    relevancia_origem: str = "padrao_fonte"
```

No `__post_init__` de `NormativoResult`, **antes** do cálculo do `id`:

```python
        if self.relevancia_origem not in ORIGENS_RELEVANCIA:
            raise ValueError(
                f"relevancia_origem={self.relevancia_origem!r} fora de "
                f"ORIGENS_RELEVANCIA {sorted(ORIGENS_RELEVANCIA)}"
            )
```

Em `KeywordStatus`, docstring ganha:

```
        motivo: Por que a fonte nao pode ser consultada (um de MOTIVOS).
              "" quando status != "error". Ex: "bloqueio_waf".
        detalhe: O que um humano precisa para reproduzir com curl: URL, HTTP
              status, content-type, primeiros chars do corpo.
        parcial: True quando status == "ok" mas a paginacao parou por erro
              ("achei 40, a fonte caiu na pagina 3").
```

E depois de `retried: bool = False`:

```python
    motivo: str = ""
    detalhe: str = ""
    parcial: bool = False

    def __post_init__(self) -> None:
        if self.motivo not in MOTIVOS:
            raise ValueError(
                f"motivo={self.motivo!r} fora de MOTIVOS {sorted(MOTIVOS)}"
            )
```

Atualizar a linha `status: str = "ok"  # "ok" | "empty" | "error"` para:
`status: str = "ok"  # "ok" | "empty" | "error" (= fonte indisponivel; ver motivo)`.

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m pytest test_phase4.py -q`
Expected: `49 passed` (41 + 8).

- [ ] **Step 5: Atualizar o BASELINE e o golden-master**

Em `tools/run_all_tests.py`: `"test_phase4.py": 41,` → `"test_phase4.py": 49,`.
Run (na raiz): `python tools/golden_master.py comparar` → `golden-master OK` (campo novo com default não muda célula nem id).

- [ ] **Step 6: Emendar a spec** — em §3.1, na linha do `motivo`, trocar a lista por
`"" | bloqueio_waf | http_5xx | manutencao_503 | timeout | conexao | resposta_ilegivel | endpoint_inexistente | erro_interno`
e acrescentar abaixo do bloco:
`> ⚠ **Emendado em 2026-09-22, Task 1 do plano:** `endpoint_inexistente` (404 em toda a cadeia não é `conexao`) e `erro_interno` (exceção imprevista não é `resposta_ilegivel`).`

- [ ] **Step 7: Auditoria de documentação + commit**

Run: `git diff -U0 -- '*.py' | grep '^-' | grep -v '^---'` — ler tudo; a única linha removida deve ser o comentário de `status` (substituído).

```bash
git add levantamento-normativos/models.py levantamento-normativos/test_phase4.py tools/run_all_tests.py docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md
git commit -m "feat(frente2): vocabulario de honestidade — motivo/detalhe/parcial e origem da nota

MOTIVOS e ORIGENS_RELEVANCIA fechados em models.py, validados no
__post_init__. Emenda a spec 3.1: endpoint_inexistente e erro_interno.
test_phase4: 41 -> 49; BASELINE atualizado no mesmo commit."
git push origin master
```

---

### Task 2: LexML — sniff de conteúdo, `ParseError` levanta, cache de falha

**Files:**
- Create: `levantamento-normativos/searchers/base.py` (classe nova ao fim do arquivo)
- Modify: `levantamento-normativos/searchers/lexml_searcher.py:104-137` (laço de `search`), `:180-203` (laço de retry), `:228-241` (`_search_keyword_safe`), `:279-286` (primeira página `None`), `:314-343` (`_fetch_sru`), `:345-382` (`_try_fetch`), `:393-397` (`_parse_sru_response`)
- Create: `levantamento-normativos/tests/test_fontes_indisponiveis.py`
- Create: `levantamento-normativos/tests/fixtures/lexml_sru_valido.xml`
- Modify: `tools/run_all_tests.py` (`SUITES_PYTEST` + `BASELINE`)

**Interfaces:**
- Consumes: `KeywordStatus(motivo=, detalhe=)` da Task 1.
- Produces:
  - `searchers.base.FonteIndisponivel(Exception)` com `motivo: str`, `detalhe: str`; `str(e)` = `f"{motivo}: {detalhe}"`.
  - `LexMLSearcher._search_keyword_safe(keyword, max_results) -> tuple[list[NormativoResult], FonteIndisponivel | None]` (era `tuple[list, str]`).
  - `LexMLSearcher._urls_mortos: set[str]` (por instância).
  - Convenção de dublê usada por todas as tasks de searcher: `monkeypatch.setattr("searchers.lexml_searcher.requests.get", fake)` e `monkeypatch.setattr("time.sleep", lambda s: None)`.

- [ ] **Step 1: Fixture SRU válido** — criar `levantamento-normativos/tests/fixtures/lexml_sru_valido.xml`:

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

- [ ] **Step 2: Escrever os testes que falham** — criar `levantamento-normativos/tests/test_fontes_indisponiveis.py`:

```python
# -*- coding: utf-8 -*-
"""Frente 2 — fonte indisponivel != fonte sem resultado (spec 2026-09-22 §3.2/§3.3).

Nenhum teste aqui faz rede: requests.get e time.sleep sao dublados. As
respostas vem de fixtures — inclusive o HTML REAL do desafio do Senado,
capturado em 2026-09-22.

Rodar de dentro de levantamento-normativos/:
    python -m pytest tests/test_fontes_indisponiveis.py -q
"""
from __future__ import annotations

from pathlib import Path

import pytest
import requests

FIXTURES = Path(__file__).parent / "fixtures"
DESAFIO_HTML = (FIXTURES / "lexml_desafio_senado.html").read_text(encoding="utf-8")
SRU_VALIDO = (FIXTURES / "lexml_sru_valido.xml").read_text(encoding="utf-8")


class RespostaFake:
    """O minimo de requests.Response que os searchers tocam."""

    def __init__(self, status: int, corpo: str = "", content_type: str = "application/xml",
                 json_data=None, url: str = "http://fake"):
        self.status_code = status
        self.text = corpo
        self.headers = {"Content-Type": content_type}
        self._json = json_data
        self.url = url

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Server Error", response=self)

    def json(self):
        return self._json


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)


# ---------------------------------------------------------------------------
# LexML
# ---------------------------------------------------------------------------

def _lexml_com(monkeypatch, responder):
    """Instala `responder(url, params) -> RespostaFake` como requests.get do LexML."""
    from searchers import lexml_searcher

    chamadas: list[str] = []

    def fake_get(url, params=None, timeout=None, **kw):
        chamadas.append(url)
        return responder(url, params)

    monkeypatch.setattr("searchers.lexml_searcher.requests.get", fake_get)
    return lexml_searcher.LexMLSearcher(), chamadas


def test_lexml_desafio_do_senado_e_bloqueio_waf(monkeypatch):
    s, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(200, DESAFIO_HTML, "text/html; charset=UTF-8"))
    resultados = s.search(["licitacao"], max_results=5)
    assert resultados == []
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo) == ("error", "bloqueio_waf")
    assert "Verificação de segurança" in st.detalhe
    assert "text/html" in st.detalhe


def test_lexml_html_generico_e_resposta_ilegivel(monkeypatch):
    s, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(200, "<html><body>oi</body></html>", "text/html"))
    s.search(["licitacao"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo) == ("error", "resposta_ilegivel")


def test_lexml_xml_truncado_e_resposta_ilegivel(monkeypatch):
    s, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(200, SRU_VALIDO[:200], "application/xml"))
    s.search(["licitacao"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo) == ("error", "resposta_ilegivel")


def test_lexml_sru_valido_continua_ok(monkeypatch):
    s, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(200, SRU_VALIDO, "application/xml"))
    resultados = s.search(["licitacao"], max_results=5)
    assert len(resultados) == 1
    assert resultados[0].numero == "14133"
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo, st.result_count) == ("ok", "", 1)


def test_lexml_404_em_toda_a_cadeia_e_endpoint_inexistente(monkeypatch):
    s, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(404, "nao", "text/html"))
    s.search(["licitacao"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo) == ("error", "endpoint_inexistente")


def test_lexml_url_morto_e_tentado_uma_vez_por_busca(monkeypatch):
    """Cache de falha (§3.2): 3 palavras-chave x 3 URLs 404 = 3 requisicoes, nao 9."""
    s, chamadas = _lexml_com(monkeypatch, lambda u, p: RespostaFake(404, "nao", "text/html"))
    s.search(["a", "b", "c"], max_results=5)
    assert len(chamadas) == 3, chamadas
    assert len({*chamadas}) == 3
    assert all(st.status == "error" for st in s.keyword_statuses)


def test_lexml_timeout_e_conexao_mapeiam_motivo(monkeypatch):
    def estoura(u, p):
        raise requests.exceptions.Timeout("lento")
    s, _ = _lexml_com(monkeypatch, estoura)
    s.search(["x"], max_results=5)
    assert s.keyword_statuses[0].motivo == "timeout"

    def cai(u, p):
        raise requests.exceptions.ConnectionError("sem rota")
    s2, _ = _lexml_com(monkeypatch, cai)
    s2.search(["x"], max_results=5)
    assert s2.keyword_statuses[0].motivo == "conexao"
```

- [ ] **Step 3: Rodar e ver falhar**

Run (em `levantamento-normativos/`): `python -m pytest tests/test_fontes_indisponiveis.py -q`
Expected: os 7 testes falham (`AttributeError: 'KeywordStatus' object has no attribute 'motivo'` **não** — a Task 1 já resolveu isso; a falha esperada é `assert ('empty', '') == ('error', 'bloqueio_waf')` e afins).

- [ ] **Step 4: `FonteIndisponivel` em `searchers/base.py`** — ao fim do arquivo:

```python
class FonteIndisponivel(Exception):
    """A fonte NAO pode ser consultada — distinto de "consultei e nao achei".

    Nasce no searcher (bloqueio, 5xx, timeout, corpo ilegivel) e sobe ate o
    KeywordStatus como status="error" + motivo + detalhe. Antes desta classe,
    um HTML de desafio com HTTP 200 virava lista vazia e a UI dizia "0 erros"
    (medido em 2026-09-22).

    Args:
        motivo: um de models.MOTIVOS (validado no KeywordStatus, nao aqui).
        detalhe: o que um humano precisa para reproduzir com curl.
    """

    def __init__(self, motivo: str, detalhe: str = "") -> None:
        super().__init__(f"{motivo}: {detalhe}" if detalhe else motivo)
        self.motivo = motivo
        self.detalhe = detalhe
```

- [ ] **Step 5: `lexml_searcher.py` — importar e instrumentar**

Import: `from searchers.base import BaseSearcher, FonteIndisponivel, ProgressCallback`.

**5a.** `_try_fetch` (`:345-382`): trocar o corpo do `try` por:

```python
                response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
                if response.status_code == 404:
                    logger.warning(f"LexML: 404 from {url}")
                    return None
                response.raise_for_status()
                self._exigir_sru(response, url)
                return response.text
```

e acrescentar o método (logo antes de `_parse_sru_response`):

```python
    def _exigir_sru(self, response, url: str) -> None:
        """HTTP 200 nao prova que veio SRU. Medido em 2026-09-22: o LexML
        devolve 200 text/html com a pagina "Verificacao de seguranca" do
        Senado. Sem esta checagem o ParseError virava lista vazia e a UI
        dizia "sem resultado" — o pior erro possivel numa ferramenta de
        pesquisa.

        Raises:
            FonteIndisponivel: bloqueio_waf se for pagina de desafio;
                resposta_ilegivel para qualquer outro nao-XML.
        """
        content_type = (response.headers.get("Content-Type") or "").lower()
        corpo = (response.text or "").lstrip()
        parece_sru = corpo.startswith(("<?xml", "<srw:", "<searchRetrieveResponse"))
        if "xml" in content_type and parece_sru:
            return
        detalhe = (
            f"GET {url} -> HTTP {response.status_code} {content_type or 'sem content-type'}; "
            f"corpo: {corpo[:120]!r}"
        )
        texto = corpo.lower()
        if "verificação de segurança" in texto or "verificacao de seguranca" in texto or "challenge" in texto:
            titulo = re.search(r"<title>([^<]*)</title>", corpo)
            if titulo:
                detalhe = f"{titulo.group(1).strip()} — {detalhe}"
            raise FonteIndisponivel("bloqueio_waf", detalhe)
        raise FonteIndisponivel("resposta_ilegivel", detalhe)
```

**5b.** `_parse_sru_response` (`:393-397`): substituir o `except`:

```python
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            # Antes devolvia ([], 0) — era a linha que transformava bloqueio
            # em "sem resultado". Agora e falha declarada.
            raise FonteIndisponivel(
                "resposta_ilegivel", f"XML SRU nao parseia: {e}; corpo: {xml_text[:120]!r}"
            ) from e
```

E na docstring dele, trocar `Returns ([], 0) on parse error.` por `Raises FonteIndisponivel("resposta_ilegivel") on parse error.`

**5c.** `_fetch_sru` (`:314-343`) — cache de falha. No `__init__` da classe (criar se não existir; `BaseSearcher` não define `__init__`):

```python
    def __init__(self) -> None:
        self._sru_url: Optional[str] = None
        # URLs que ja falharam NESTA busca (404 ou bloqueio). Antes, cada
        # palavra-chave tentava a cadeia inteira de novo: 3 URLs x N
        # palavras-chave, e era parte dos ~390s do test_searchers.py.
        self._urls_mortos: set[str] = set()
        self.keyword_statuses: list[KeywordStatus] = []
```

⚠ Conferir se já existe `__init__` definindo `self._sru_url` (grep `_sru_url = None`); se existir, só acrescentar as duas linhas.

Corpo novo de `_fetch_sru`:

```python
        if self._sru_url:
            return self._try_fetch(self._sru_url, params)

        candidatos = [u for u in (PRIMARY_SRU_URL, FALLBACK_SRU_URL, FALLBACK_SRU_URL_2)
                      if u not in self._urls_mortos]
        if not candidatos:
            raise FonteIndisponivel(
                "endpoint_inexistente",
                f"todos os URLs SRU ja falharam nesta busca: {sorted(self._urls_mortos)}",
            )
        for url in candidatos:
            try:
                result = self._try_fetch(url, params)
            except FonteIndisponivel:
                self._urls_mortos.add(url)
                raise
            if result is not None:
                self._sru_url = url
                return result
            self._urls_mortos.add(url)
            logger.warning(f"LexML: {url} falhou; proximo da cadeia")
        logger.error("LexML: all SRU endpoints failed")
        raise FonteIndisponivel(
            "endpoint_inexistente",
            f"404/falha em todos os URLs SRU: {sorted(self._urls_mortos)}",
        )
```

Docstring de `_fetch_sru`: acrescentar `URLs que falharam ficam em self._urls_mortos e nao sao tentados de novo nesta busca.` e trocar `Response body as string, or None on failure.` por `Response body as string. Raises FonteIndisponivel when no URL works.`

**5d.** `_search_keyword` (`:279-286`): o bloco `if xml_text is None:` fica só com o `break` das páginas seguintes, porque `_fetch_sru` agora levanta na primeira:

```python
            try:
                xml_text = self._fetch_sru(params)
            except FonteIndisponivel:
                if first_page:
                    raise
                logger.warning("LexML: pagina seguinte falhou; devolvendo o que veio")
                break
```

(remover o `raise ConnectionError(...)` e o comentário acima dele; a docstring `Raises: ConnectionError` vira `Raises: FonteIndisponivel: se a primeira pagina falhar.`)

**5e.** `_search_keyword_safe` (`:228-241`):

```python
    def _search_keyword_safe(
        self, keyword: str, max_results: int = 50
    ) -> tuple[list[NormativoResult], Optional[FonteIndisponivel]]:
        """Search for a keyword, returning (results, erro).

        Returns:
            (results, None) em sucesso; ([], FonteIndisponivel) quando a fonte
            nao pode ser consultada. Excecoes de rede do requests sao mapeadas
            para motivo timeout/conexao; qualquer outra vira erro_interno —
            nunca "sem resultado".
        """
        try:
            return self._search_keyword(keyword, max_results=max_results), None
        except FonteIndisponivel as e:
            logger.warning(f"LexML: fonte indisponivel para '{keyword}': {e}")
            return [], e
        except requests.exceptions.Timeout as e:
            return [], FonteIndisponivel("timeout", f"{REQUEST_TIMEOUT}s: {e}")
        except requests.exceptions.ConnectionError as e:
            return [], FonteIndisponivel("conexao", str(e)[:200])
        except Exception as e:
            logger.error(f"LexML: erro interno em '{keyword}': {e}")
            return [], FonteIndisponivel("erro_interno", f"{type(e).__name__}: {e}"[:200])
```

**5f.** Laço de `search` (`:124-137`): `keyword_results, error_msg = ...` vira `keyword_results, erro = ...`; o `if error_msg:` vira:

```python
            if erro is not None:
                self.keyword_statuses.append(KeywordStatus(
                    keyword=keyword, source="lexml", result_count=0,
                    status="error", error_message=str(erro),
                    motivo=erro.motivo, detalhe=erro.detalhe,
                ))
                failed_keywords.append(keyword)
```

**5g.** Laço de retry (`:180-203`): `keyword_results, error_msg = ...` vira `keyword_results, erro = ...`; `if error_msg:` vira `if erro is not None:` e dentro dele acrescentar `st.motivo = erro.motivo` e `st.detalhe = erro.detalhe` antes de `api_still_down = True`; nos ramos `empty`/`ok`, acrescentar `st.motivo = ""` e `st.detalhe = ""`. ⚠ `time.sleep(3)` do retry: com `_urls_mortos`, as retentativas de uma cadeia morta levantam sem rede — o `sleep` continua (3s), aceitável.

- [ ] **Step 6: Rodar e ver passar**

Run: `python -m pytest tests/test_fontes_indisponiveis.py -q` → `7 passed`.
Run: `python test_searchers.py` → `Results: 13/13 passed` (os LIVE degradam como antes; ⚠ demora ~6 min hoje — pode ficar mais rápido com o cache de falha; anotar o tempo).
Run: `python -m pytest test_phase4.py -q` → `49 passed`.

- [ ] **Step 7: Registrar a suíte no runner**

`tools/run_all_tests.py`: `SUITES_PYTEST = ["test_phase4.py", "tests/test_fontes_indisponiveis.py"]` e `BASELINE["tests/test_fontes_indisponiveis.py"] = 7`. Atualizar o comentário acima de `SUITES_PYTEST` (que diz "nasce com UMA suite") para dizer que a segunda entrou na frente 2.

Run (na raiz): `python tools/run_all_tests.py` → TUDO VERDE, 5 linhas.
Run: `python tools/golden_master.py comparar` → OK.

- [ ] **Step 8: Auditoria de documentação + commit**

`git diff -U0 -- '*.py' | grep '^-' | grep -v '^---'` — toda docstring removida tem substituta (5b, 5c, 5d, 5e).

```bash
git add levantamento-normativos/searchers/base.py levantamento-normativos/searchers/lexml_searcher.py levantamento-normativos/tests/ tools/run_all_tests.py
git commit -m "feat(frente2): LexML declara bloqueio e resposta ilegivel em vez de 'sem resultado'

HTTP 200 text/html com a pagina de desafio do Senado vira
status=error motivo=bloqueio_waf (fixture com o HTML real de 22/09).
ParseError levanta FonteIndisponivel(resposta_ilegivel). 404 na cadeia
inteira e endpoint_inexistente. URLs mortos ficam em cache por busca:
3 palavras-chave x 3 URLs 404 = 3 requisicoes, nao 9.
Suite nova tests/test_fontes_indisponiveis.py (7) registrada no runner."
git push origin master
```

---

### Task 3: TCU — 500/503 viram erro declarado, paginação parcial é declarada

**Files:**
- Modify: `levantamento-normativos/searchers/tcu_searcher.py:62-137` (`search`), `:153-206` (`_fetch_all_pages_safe`, `_fetch_all_pages`), `:208-256` (`_request_with_retry`)
- Test: `levantamento-normativos/tests/test_fontes_indisponiveis.py` (seção TCU)
- Modify: `tools/run_all_tests.py` (`BASELINE`)

**Interfaces:**
- Consumes: `FonteIndisponivel` (Task 2), `KeywordStatus(motivo=, detalhe=, parcial=)` (Task 1).
- Produces:
  - `TCUSearcher._request_with_retry(url, params) -> dict | list` — **levanta** `FonteIndisponivel` em vez de devolver `None`.
  - `TCUSearcher._fetch_all_pages(url) -> tuple[list[dict], Optional[FonteIndisponivel], bool]` = `(itens, erro, parcial)`.
  - `TCUSearcher._fetch_all_pages_safe(url) -> tuple[list[dict], Optional[FonteIndisponivel], bool]`.

- [ ] **Step 1: Testes que falham** — acrescentar a `tests/test_fontes_indisponiveis.py`:

```python
# ---------------------------------------------------------------------------
# TCU
# ---------------------------------------------------------------------------

ACORDAO = {"key": "ACORDAO-1", "tipo": "ACÓRDÃO", "anoAcordao": "2026",
           "titulo": "ACÓRDÃO 1/2026 - PLENÁRIO", "numeroAcordao": "1", "colegiado": "Plenário",
           "ementa": "Auditoria de governanca de TI na administracao publica federal.",
           "dataSessao": "01/01/2026", "urlAcordao": "https://pesquisa.apps.tcu.gov.br/x"}


def _tcu_com(monkeypatch, por_url):
    """por_url: dict {trecho_da_url: callable(params) -> RespostaFake}."""
    from searchers import tcu_searcher

    chamadas: list[str] = []

    def fake_get(url, params=None, timeout=None, **kw):
        chamadas.append(url)
        for trecho, responder in por_url.items():
            if trecho in url:
                return responder(params)
        raise AssertionError(f"URL inesperada: {url}")

    monkeypatch.setattr("searchers.tcu_searcher.requests.get", fake_get)
    return tcu_searcher.TCUSearcher(), chamadas


def test_tcu_500_num_endpoint_e_error_mesmo_com_o_outro_ok(monkeypatch):
    s, chamadas = _tcu_com(monkeypatch, {
        "recupera-acordaos": lambda p: RespostaFake(200, json_data=[ACORDAO]),
        "recupera-atos-normativos": lambda p: RespostaFake(500, "Internal Server Error", "text/html"),
    })
    resultados = s.search(["governanca"], max_results=5)
    assert len(resultados) == 1                      # o acordao entrou
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo, st.result_count) == ("error", "http_5xx", 1)
    assert "recupera-atos-normativos" in st.detalhe
    assert "Acórdãos: ok" in st.detalhe
    assert chamadas.count(next(u for u in chamadas if "atos" in u)) == 3  # 3 retries


def test_tcu_503_e_manutencao(monkeypatch):
    s, _ = _tcu_com(monkeypatch, {
        "recupera-acordaos": lambda p: RespostaFake(503, "", "text/html"),
        "recupera-atos-normativos": lambda p: RespostaFake(503, "", "text/html"),
    })
    s.search(["x"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo) == ("error", "manutencao_503")
    assert "20h" in st.detalhe


def test_tcu_falha_na_segunda_pagina_e_ok_parcial(monkeypatch):
    from searchers import tcu_searcher
    pagina_cheia = [dict(ACORDAO, key=f"A-{i}", numeroAcordao=str(i)) for i in range(tcu_searcher.PAGE_SIZE)]

    def acordaos(p):
        if p["inicio"] == 0:
            return RespostaFake(200, json_data=pagina_cheia)
        return RespostaFake(500, "boom", "text/html")

    s, _ = _tcu_com(monkeypatch, {
        "recupera-acordaos": acordaos,
        "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[]),
    })
    resultados = s.search(["governanca"], max_results=100)
    assert len(resultados) == tcu_searcher.PAGE_SIZE
    st = s.keyword_statuses[0]
    assert (st.status, st.parcial) == ("ok", True)
    assert "pagina 2" in st.detalhe or "inicio=20" in st.detalhe


def test_tcu_dois_endpoints_ok_sem_match_continua_empty(monkeypatch):
    s, _ = _tcu_com(monkeypatch, {
        "recupera-acordaos": lambda p: RespostaFake(200, json_data=[ACORDAO]),
        "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[]),
    })
    s.search(["assunto-que-nao-existe"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo, st.parcial) == ("empty", "", False)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_fontes_indisponiveis.py -q -k tcu` → 4 failed (`('empty', '') == ('error', 'http_5xx')` etc.).

- [ ] **Step 3: Implementar em `tcu_searcher.py`**

Import: `from searchers.base import BaseSearcher, FonteIndisponivel, ProgressCallback`.

**3a.** `_request_with_retry` → levanta em vez de `None`:

```python
    def _request_with_retry(self, url: str, params: dict) -> dict | list:
        """Send GET request with exponential backoff retry.

        Handles the TCU maintenance window (503 between 20:00-21:00 BRT)
        with a user-friendly message.

        Returns:
            Parsed JSON (dict or list).

        Raises:
            FonteIndisponivel: manutencao_503 no 503; http_5xx apos MAX_RETRIES
                em outro 5xx; timeout/conexao para falhas de rede. Antes
                devolvia None, e o chamador tratava None como "fim das
                paginas" — um 500 virava "sem resultado" (medido em 22/09).
        """
        ultimo: Optional[Exception] = None
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
                if response.status_code == 503:
                    raise FonteIndisponivel(
                        "manutencao_503",
                        f"GET {url} -> 503. A API do TCU fica indisponivel diariamente "
                        f"das 20h as 21h (horario de Brasilia). Tente mais tarde.",
                    )
                response.raise_for_status()
                return response.json()
            except FonteIndisponivel:
                raise
            except requests.exceptions.RequestException as e:
                ultimo = e
                if attempt < MAX_RETRIES - 1:
                    delay = 2 ** (attempt + 1)  # 2s, 4s, 8s
                    logger.warning(
                        f"TCU API error (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
        logger.error(f"TCU API failed after {MAX_RETRIES} attempts: {ultimo}")
        if isinstance(ultimo, requests.exceptions.Timeout):
            raise FonteIndisponivel("timeout", f"GET {url}: {REQUEST_TIMEOUT}s x {MAX_RETRIES}")
        if isinstance(ultimo, requests.exceptions.ConnectionError):
            raise FonteIndisponivel("conexao", f"GET {url}: {str(ultimo)[:160]}")
        status = getattr(getattr(ultimo, "response", None), "status_code", "?")
        raise FonteIndisponivel(
            "http_5xx", f"GET {url} -> HTTP {status} em {MAX_RETRIES} tentativas: {str(ultimo)[:160]}"
        )
```

⚠ Conferir que `import time` existe no topo do módulo (o código atual usa `time.sleep(delay)`).

**3b.** `_fetch_all_pages` → `(itens, erro, parcial)`:

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
                e.detalhe = f"pagina {page + 1} (inicio={offset}): {e.detalhe}"
                return all_items, e, True

            items = data if isinstance(data, list) else data.get("items", data.get("data", []))
            if not isinstance(items, list):
                return all_items, FonteIndisponivel(
                    "resposta_ilegivel", f"GET {url} inicio={offset}: formato inesperado {type(data).__name__}"
                ), page > 0

            all_items.extend(items)
            if len(items) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
            self._rate_limit()

        return all_items, None, False
```

**3c.** `_fetch_all_pages_safe`:

```python
    def _fetch_all_pages_safe(self, url: str) -> tuple[list[dict], Optional[FonteIndisponivel], bool]:
        """Como _fetch_all_pages, mas nenhuma excecao escapa: bug nosso vira
        erro_interno declarado, nunca "sem resultado"."""
        try:
            return self._fetch_all_pages(url)
        except Exception as e:  # FonteIndisponivel ja foi tratada dentro
            logger.error(f"TCU: erro interno em {url}: {e}")
            return [], FonteIndisponivel("erro_interno", f"{type(e).__name__}: {e}"[:200]), False
```

**3d.** `search()` (`:70-137`): as duas chamadas viram
`acordao_items, acordao_erro, acordao_parcial = self._fetch_all_pages_safe(...)` e
`atos_items, atos_erro, atos_parcial = ...`. Substituir o bloco `for keyword in keywords:` inteiro por:

```python
        def _resumo(nome: str, itens: list, erro: Optional[FonteIndisponivel], parcial: bool) -> str:
            if erro is not None and not itens:
                return f"{nome}: {erro.motivo} em {erro.detalhe}"
            if parcial:
                return f"{nome}: parcial ({len(itens)} itens; {erro.detalhe})"
            return f"{nome}: ok ({len(itens)} itens)"

        detalhe = "; ".join([
            _resumo("Acórdãos", acordao_items, acordao_erro, acordao_parcial),
            _resumo("Atos", atos_items, atos_erro, atos_parcial),
        ])
        # Um endpoint que caiu na PRIMEIRA pagina torna a busca "error" mesmo
        # que o outro tenha respondido: o usuario precisa saber que metade da
        # fonte nao foi vista. Resultados do endpoint vivo continuam entrando.
        erro_primario = next(
            (e for e, itens in ((acordao_erro, acordao_items), (atos_erro, atos_items))
             if e is not None and not itens), None,
        )
        parcial = acordao_parcial or atos_parcial

        for keyword in keywords:
            kw_count = 0
            for item in acordao_items:
                if len(results_by_id) >= max_results:
                    break
                if self._matches_keyword(item.get("ementa", ""), keyword):
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

            if erro_primario is not None:
                status, motivo = "error", erro_primario.motivo
            elif kw_count == 0:
                status, motivo = "empty", ""
            else:
                status, motivo = "ok", ""
            self.keyword_statuses.append(KeywordStatus(
                keyword=keyword, source="tcu", result_count=kw_count,
                status=status, motivo=motivo,
                detalhe=detalhe if (status == "error" or parcial) else "",
                error_message=detalhe if status == "error" else "",
                parcial=parcial,
            ))
```

Docstring de `search()`: acrescentar `Um endpoint que falha na primeira pagina marca status="error" para toda palavra-chave, com result_count do endpoint que respondeu; paginacao interrompida marca parcial=True.`

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m pytest tests/test_fontes_indisponiveis.py -q` → `11 passed`.
Run: `python test_searchers.py` → `13/13 passed`. ⚠ Se algum teste de `test_searchers.py` ou `test_comprehensive.py` **afirmar** que `_fetch_all_pages` devolve lista ou que `_request_with_retry` devolve `None`, ele quebra aqui: abrir o teste, entender o que ele protegia, e **adaptar a asserção ao contrato novo no mesmo commit** — nunca apagar o teste. Registrar no commit qual asserção mudou e por quê.

- [ ] **Step 5: BASELINE + runner + golden**

`BASELINE["tests/test_fontes_indisponiveis.py"] = 11`. Run (raiz): `python tools/run_all_tests.py` → TUDO VERDE; `python tools/golden_master.py comparar` → OK.

- [ ] **Step 6: Auditoria de documentação + commit**

```bash
git add levantamento-normativos/searchers/tcu_searcher.py levantamento-normativos/tests/test_fontes_indisponiveis.py tools/run_all_tests.py
git commit -m "feat(frente2): TCU declara 5xx/503 e paginacao parcial em vez de engolir

_request_with_retry levanta FonteIndisponivel (http_5xx, manutencao_503,
timeout, conexao) em vez de devolver None; _fetch_all_pages devolve
(itens, erro, parcial) e nao trata None como fim das paginas. Um
endpoint caido marca error para a palavra-chave mesmo com o outro ok,
e o detalhe nomeia qual. Suite: 7 -> 11."
git push origin master
```

---

### Task 4: Origem da nota de relevância (`gemini_client.py`)

**Files:**
- Modify: `levantamento-normativos/llm/gemini_client.py:340-430` (`score_relevance`)
- Modify: `levantamento-normativos/llm/__init__.py`
- Test: `levantamento-normativos/test_llm_phase3.py` (seção 9, antes do `Summary`)
- Modify: `tools/run_all_tests.py` (`BASELINE["test_llm_phase3.py"]`)

**Interfaces:**
- Produces:
  - `score_relevance_com_origem(topic: str, results: list[dict], keywords: Optional[list[str]] = None) -> list[tuple[float, str]]` — o `str` é um de `ORIGENS_RELEVANCIA`.
  - `score_relevance(...) -> list[float]` inalterada em assinatura e valores (wrapper).
  - Exportadas por `llm/__init__.py`.

- [ ] **Step 1: Testes que falham** — em `test_llm_phase3.py`, **antes** do bloco `# Summary`:

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

- [ ] **Step 2: Rodar e ver falhar**

Run: `python test_llm_phase3.py | tail -5` → `Total: 54 | PASS: 53 | FAIL: 1` (a seção inteira cai no `except` com `ImportError`, um único `record` de falha).

- [ ] **Step 3: Implementar**

Em `gemini_client.py`, **renomear** a atual `score_relevance` para `score_relevance_com_origem`, mudar a assinatura de retorno para `list[tuple[float, str]]`, e ajustar cada ponto que emite nota:

```python
    if not is_available():
        if keywords:
            logger.info("LLM indisponivel — heuristica por palavras-chave.")
            return [(_keyword_relevance(keywords, r.get("ementa", "")), "heuristica") for r in results]
        logger.info("LLM indisponivel e sem keywords — 0.5 rotulado como fallback_erro.")
        return [(0.5, "fallback_erro")] * len(results)
```

no lote vazio: `all_scores.extend([(0.5, "fallback_erro")] * len(batch))`;
no lote válido, dentro do `for val in parsed:`:

```python
                try:
                    score = max(0.0, min(1.0, float(val)))
                    batch_scores.append((score, "modelo"))
                except (TypeError, ValueError):
                    batch_scores.append((0.5, "fallback_erro"))
```

no lote de tamanho errado: `all_scores.extend([(0.5, "fallback_erro")] * len(batch))`.

Docstring da função nova — reescrever a atual acrescentando:

```
    Returns:
        Lista de (nota, origem), mesma ordem dos results. origem e um de
        models.ORIGENS_RELEVANCIA: "modelo" quando o LLM deu a nota;
        "heuristica" quando nao ha LLM e ha keywords; "fallback_erro" quando
        o LLM falhou (lote vazio, tamanho errado, valor nao numerico) ou nao
        ha nem LLM nem keywords. Antes, esses tres casos davam 0.5 sem marca.
```

E acrescentar o wrapper, logo abaixo:

```python
def score_relevance(
    topic: str,
    results: list[dict],
    keywords: Optional[list[str]] = None,
) -> list[float]:
    """Compat: so as notas. Ver score_relevance_com_origem para a procedencia."""
    return [nota for nota, _ in score_relevance_com_origem(topic, results, keywords)]
```

Em `llm/__init__.py`: importar e exportar `score_relevance_com_origem` (em `from .gemini_client import (...)` e em `__all__`). Na docstring do pacote, a linha `Provides keyword expansion, relevance scoring, and auto-categorization` ganha `(scores carry their origin: see score_relevance_com_origem)`. ⚠ **Não** tocar nas frases sobre Gemini/API key — são a emenda B7, frente 5.

- [ ] **Step 4: Rodar e ver passar**

Run: `python test_llm_phase3.py | tail -3` → `Total: 63 | PASS: 63 | FAIL: 0`.

- [ ] **Step 5: BASELINE + runner + golden**

`BASELINE["test_llm_phase3.py"] = 63`. Runner TUDO VERDE; golden OK (nada de planilha mudou).

- [ ] **Step 6: Auditoria + commit**

```bash
git add levantamento-normativos/llm/ levantamento-normativos/test_llm_phase3.py tools/run_all_tests.py
git commit -m "feat(frente2): a nota de relevancia passa a dizer de onde veio

score_relevance_com_origem devolve (nota, origem) com origem em
ORIGENS_RELEVANCIA; score_relevance vira wrapper com o mesmo contrato
(53 testes intactos). 0.5 de fallback deixa de ser indistinguivel de
nota do modelo. test_llm_phase3: 53 -> 63."
git push origin master
```

---

### Task 5: `_merge` leva a origem da nota vencedora

**Files:**
- Modify: `levantamento-normativos/deduplicator.py:98-113` (docstring) e `:147` (`relevancia`)
- Test: `levantamento-normativos/test_phase4.py` (classe `TestVocabularioHonestidade` ganha 3 testes, ou classe nova `TestMergeOrigem`)
- Modify: `tools/run_all_tests.py`

- [ ] **Step 1: Testes que falham** — ao fim de `test_phase4.py`:

```python
class TestMergeOrigem:
    """_merge guarda a maior nota E a origem dela (spec §3.4)."""

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

- [ ] **Step 2: Ver falhar** — `python -m pytest test_phase4.py -q -k MergeOrigem` → 1 failed (`'padrao_fonte' == 'modelo'`).

- [ ] **Step 3: Implementar** — em `_merge`, trocar `existing.relevancia = max(existing.relevancia, incoming.relevancia)` por:

```python
    # Relevancia: keep higher score — e a ORIGEM da nota que venceu, senao a
    # planilha diria "modelo" sobre um numero que veio da heuristica.
    if incoming.relevancia > existing.relevancia:
        existing.relevancia = incoming.relevancia
        existing.relevancia_origem = incoming.relevancia_origem
```

Na docstring, a linha `- relevancia: keep the higher score` vira `- relevancia: keep the higher score, and relevancia_origem of whichever won (tie keeps existing)`.

- [ ] **Step 4: Ver passar** — `python -m pytest test_phase4.py -q` → `52 passed`.

- [ ] **Step 5: BASELINE + golden** — `BASELINE["test_phase4.py"] = 52`. `python tools/golden_master.py comparar` → **OK obrigatório**: `dedup_esperado.json` não pode mudar (id/nome/link intactos). Runner TUDO VERDE.

- [ ] **Step 6: Commit**

```bash
git add levantamento-normativos/deduplicator.py levantamento-normativos/test_phase4.py tools/run_all_tests.py
git commit -m "feat(frente2): _merge leva a origem da nota que venceu

Docstring de _merge atualizada campo a campo. dedup_esperado.json
inalterado (golden-master OK). test_phase4: 49 -> 52."
git push origin master
```

---

### Task 6: Planilha — coluna "Origem da nota" e aba "Diagnostico da busca"

**Files:**
- Modify: `levantamento-normativos/excel_export.py:75-87` (`COLUMNS`), `:186-270` (`_write_data_row`), `:274-357` (`generate_excel`), + função nova `_write_diagnostico_sheet`
- Modify: `levantamento-normativos/test_phase4.py:409` (coluna do link não muda), `:421-447` (10 → 11), `:537-544` (coluna 10 continua `Relevancia`), + testes novos
- Modify: `tests/golden/planilha_sha256.txt`, `tests/golden/ambiente.txt` (recongelados)
- Modify: `tools/run_all_tests.py`

**Interfaces:**
- Consumes: `NormativoResult.relevancia_origem`, `KeywordStatus(motivo, detalhe, parcial)`.
- Produces:
  - `COLUMNS` com 11 entradas; a 11ª = `("Origem da nota", 16, "relevancia_origem")`.
  - `ORIGEM_LABEL: dict[str, str]` e `STATUS_LABEL: dict[str, str]` em `excel_export.py`.
  - `generate_excel(results, topic, diagnostico: Optional[list[KeywordStatus]] = None) -> BytesIO`.
  - Aba `"Diagnostico da busca"` sempre presente, `wb.active` continua `"Normativos"`.

- [ ] **Step 1: Testes que falham** — em `test_phase4.py`:

(a) `TestExcelColumnCount`: `10` → `11` em `test_has_10_columns` (renomear para `test_has_11_columns`), `range(1, 11)` → `range(1, 12)` e `== 10` → `== 11` em `test_header_row_has_11_columns`; em `test_expected_header_names`, `expected` ganha `"Origem da nota"` no fim e `range(1, 11)` → `range(1, 12)`. A docstring da classe: `"""Verify all 11 expected columns are present."""`.

(b) Classe nova ao fim:

```python
from models import KeywordStatus as _KS


class TestExcelHonestidade:
    """Coluna 'Origem da nota' e aba 'Diagnostico da busca' (spec §3.5)."""

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
        assert wb.sheetnames == ["Normativos", "Diagnostico da busca"]
        assert wb.active.title == "Normativos"
        ws = wb["Diagnostico da busca"]
        assert ws.cell(row=3, column=1).value == "Nenhum diagnóstico registrado nesta exportação"

    def test_aba_diagnostico_uma_linha_por_status(self):
        diag = [
            _KS(keyword="lgpd", source="lexml", status="error", motivo="bloqueio_waf",
                detalhe="GET x -> 200 text/html", error_message="bloqueio"),
            _KS(keyword="lgpd", source="tcu", status="ok", result_count=4, parcial=True,
                detalhe="pagina 2 (inicio=20): http_5xx"),
            _KS(keyword="lgpd", source="google", status="empty"),
        ]
        wb = _load_workbook_from_buffer(generate_excel([_make_result()], "t", diagnostico=diag))
        ws = wb["Diagnostico da busca"]
        cab = [ws.cell(row=2, column=c).value for c in range(1, 9)]
        assert cab == ["Fonte", "Palavra-chave", "Status", "Motivo", "Detalhe",
                       "Resultados", "Parcial", "Retentado"]
        linhas = [[ws.cell(row=r, column=c).value for c in range(1, 9)] for r in range(3, 6)]
        assert linhas[0] == ["lexml", "lgpd", "Indisponível", "bloqueio_waf", "GET x -> 200 text/html", 0, "Não", "Não"]
        assert linhas[1][2:7] == ["OK", "", "pagina 2 (inicio=20): http_5xx", 4, "Sim"]
        assert linhas[2][2] == "Sem resultado"
        assert ws.cell(row=6, column=1).value is None
```

- [ ] **Step 2: Ver falhar** — `python -m pytest test_phase4.py -q` → 7 failed (3 da contagem + 4 novos).

- [ ] **Step 3: Implementar em `excel_export.py`**

**3a.** Import: `from models import KeywordStatus, NormativoResult` e `from typing import Optional`.

**3b.** `COLUMNS` ganha, após `("Relevancia", 12, "relevancia")`: `("Origem da nota", 16, "relevancia_origem"),`. Comentário acima: `# ⚠ test_phase4.py fixa len(COLUMNS); mudar aqui = mudar la no mesmo commit`.

**3c.** Constantes, logo após `COLUMNS`:

```python
# Rotulos em portugues para a planilha (o vocabulario tecnico vive em models.py)
ORIGEM_LABEL = {
    "modelo": "Modelo (IA)",
    "heuristica": "Heurística (palavras-chave)",
    "fallback_erro": "Fallback (erro do modelo)",
    "padrao_fonte": "Padrão da fonte",
}
STATUS_LABEL = {"ok": "OK", "empty": "Sem resultado", "error": "Indisponível"}
DIAGNOSTICO_SHEET = "Diagnostico da busca"
DIAGNOSTICO_COLUMNS = [
    ("Fonte", 12), ("Palavra-chave", 28), ("Status", 14), ("Motivo", 20),
    ("Detalhe", 70), ("Resultados", 11), ("Parcial", 9), ("Retentado", 10),
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
def _write_diagnostico_sheet(wb, topic: str, diagnostico: Optional[list[KeywordStatus]]) -> None:
    """Aba 'Diagnostico da busca': uma linha por (fonte, palavra-chave).

    Existe SEMPRE, mesmo sem dados, para que quem abre a planilha saiba que o
    registro e previsto. E o que diz, seis meses depois, que o LexML nao
    respondeu naquele dia — a planilha e o artefato que sobrevive a sessao.
    """
    ws = wb.create_sheet(DIAGNOSTICO_SHEET)
    n = len(DIAGNOSTICO_COLUMNS)
    ws.merge_cells(f"A1:{get_column_letter(n)}1")
    t = ws.cell(row=1, column=1)
    t.value = f"Diagnóstico da busca: {topic}"
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
        valores = [s.source, s.keyword, STATUS_LABEL.get(s.status, s.status), s.motivo,
                   s.detalhe or s.error_message, s.result_count, sim_nao(s.parcial), sim_nao(s.retried)]
        for col, v in enumerate(valores, start=1):
            c = ws.cell(row=row, column=col)
            c.value, c.font, c.border = v, DATA_FONT, THIN_BORDER
            c.alignment = EMENTA_ALIGNMENT if col == 5 else DATA_ALIGNMENT
    ws.freeze_panes = "A3"
    ws.auto_filter.ref = f"A2:{get_column_letter(n)}{len(diagnostico) + 2}"
```

**3f.** `generate_excel(results, topic, diagnostico: Optional[list[KeywordStatus]] = None)`: docstring — `The workbook contains a single sheet` vira `The workbook contains two sheets: 'Normativos' (active) and 'Diagnostico da busca'`; `Args` ganha `diagnostico: KeywordStatus list from the search; None or empty writes a placeholder row.` Antes de `buffer = BytesIO()`: `_write_diagnostico_sheet(wb, topic, diagnostico)`. Depois dele: `wb.active = 0` (garante `Normativos` ativa).

- [ ] **Step 4: Ver passar** — `python -m pytest test_phase4.py -q` → `56 passed`.

- [ ] **Step 5: Recongelar o golden-master — no mesmo commit**

Run (raiz): `python tools/golden_master.py comparar` → **esperado: `DIVERGIU: planilha divergiu`** (coluna nova) e **nenhuma** linha `dedup divergiu`. Se `dedup divergiu` aparecer, **parar**: é regressão, não a mudança planejada.
Run: `python tools/golden_master.py congelar` → grava sha novo + `ambiente.txt`.
Run: `python tools/golden_master.py comparar` → OK. Rodar `comparar` **duas vezes** e conferir que o sha é estável (regra do LESSONS de 16/09).
Run: `git diff --stat tests/golden/` → só `planilha_sha256.txt` (e `ambiente.txt` se a versão mudou); `dedup_esperado.json` **ausente** do diff.

- [ ] **Step 6: BASELINE + runner** — `BASELINE["test_phase4.py"] = 56`. Runner TUDO VERDE.

- [ ] **Step 7: Auditoria + commit**

```bash
git add levantamento-normativos/excel_export.py levantamento-normativos/test_phase4.py tests/golden/ tools/run_all_tests.py
git commit -m "feat(frente2): planilha ganha 'Origem da nota' e a aba 'Diagnostico da busca'

COLUMNS 10 -> 11 (test_phase4 atualizado no mesmo commit). Aba de
diagnostico sempre presente: fonte x palavra-chave x status x motivo x
detalhe x resultados x parcial x retentado. 'Normativos' continua ativa.

GOLDEN-MASTER RECONGELADO DE PROPOSITO (spec 2026-09-22 §3.5): a coluna
nova muda os valores das celulas. dedup_esperado.json inalterado —
conferido pelo ramo do dedup antes de recongelar. Sha estavel em 2 runs.
test_phase4: 52 -> 56."
git push origin master
```

---

### Task 7: Tela — pontuar sempre, relatório honesto, aviso, card, preview, exportar diagnóstico

**Files:**
- Modify: `levantamento-normativos/app.py:24-26` (imports), `:570-596` (pontuação), `:840-905` (`_render_search_diagnostics`), `:907-946` (`render_step4`), `:1049-1065` (card), `:1221-1232` (preview), `:1195` (`generate_excel`)
- Create: `tools/dirigir_app.py` (gate visual V11)

**Interfaces:**
- Consumes: `score_relevance_com_origem`, `generate_excel(..., diagnostico=)`, `KeywordStatus.motivo/detalhe/parcial`, `NormativoResult.relevancia_origem`.
- Produces: nada consumido por outra task. Gate: V11.

⚠ Streamlit não tem teste unitário neste repo; o gate desta task é o roteiro dirigido pelo navegador (Step 6) **mais** o runner e o golden. Cada edição abaixo é pequena e nomeada — fazer uma de cada vez e recarregar o app entre elas.

- [ ] **Step 1: Pontuação sempre** — `app.py:570-596`. Trocar o bloco por:

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

Conferir em `app.py:24-26` que `gemini_client` é importado como módulo (`from llm import gemini_client` ou equivalente) — se `score_relevance` era importada por nome, importar `score_relevance_com_origem` do mesmo lugar e chamar sem o prefixo.

- [ ] **Step 2: Relatório honesto** — em `_render_search_diagnostics`:

```python
    label = (f"Relatório da busca — {n_ok} OK · {n_err} indisponíveis · "
             f"{n_empty} sem resultado ({total} buscas)")
    parciais = [s for s in kw_statuses if s.parcial]

    with st.expander(label, expanded=bool(error_statuses or parciais)):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de buscas", total)
        with col2:
            st.metric("OK", n_ok)
        with col3:
            st.metric("Sem resultado", n_empty)
        with col4:
            st.metric("Indisponíveis", n_err)

        if error_statuses:
            st.markdown("**:red[Fontes indisponíveis (a fonte não pôde ser consultada):]**")
            for s in error_statuses:
                retry_badge = " (retentado)" if s.retried else ""
                extra = f" — {s.result_count} resultado(s) do endpoint que respondeu" if s.result_count else ""
                st.markdown(
                    f"- :red[**{html_module.escape(s.keyword)}**] em *{html_module.escape(s.source)}*"
                    f"{retry_badge}: `{html_module.escape(s.motivo or 'erro')}`{extra}  \n"
                    f"  <small>{html_module.escape(s.detalhe or s.error_message)}</small>",
                    unsafe_allow_html=True,
                )
            st.caption(
                "A fonte não pôde ser consultada. Isso NÃO significa que não existem "
                "normativos — significa que esta busca não os viu. Motivo e detalhe acima; "
                "a aba 'Diagnostico da busca' da planilha registra o mesmo."
            )

        if parciais:
            st.markdown("**:orange[Buscas parciais (a fonte parou de responder no meio da paginação):]**")
            for s in parciais:
                st.markdown(f"- :orange[**{html_module.escape(s.keyword)}**] em *{html_module.escape(s.source)}*: "
                            f"{s.result_count} resultado(s) — <small>{html_module.escape(s.detalhe)}</small>",
                            unsafe_allow_html=True)
```

Os blocos de `empty_statuses` e `ok_statuses` ficam como estão, com `(parcial)` acrescentado ao lado do `result_count` quando `s.parcial`.

- [ ] **Step 3: Aviso "nenhuma catalogada respondeu"** — em `render_step4`, logo após calcular `ok_statuses` e **antes** do `if not results:`:

```python
    catalogadas = {s.source for s in kw_statuses if s.source in ("lexml", "tcu")}
    catalogadas_ok = {s.source for s in kw_statuses if s.source in ("lexml", "tcu") and s.status != "error"}
    if catalogadas and not catalogadas_ok:
        st.warning(
            "Nenhuma fonte catalogada (LexML, TCU) respondeu nesta busca. "
            "Os resultados abaixo vêm só da web aberta. Veja o relatório da busca."
        )
```

E na mensagem `st.error` do ramo `if not results:` trocar `falharam por erro de API. A fonte pode estar indisponivel` por `não puderam consultar a fonte (indisponível). Isso não significa que o normativo não existe`.

- [ ] **Step 4: Card e preview**

Card (`:1065`): `f"<b>Relevancia:</b> {relevancia_pct}% &middot; "` vira
`f"<b>Relevancia:</b> {relevancia_pct}% <i>({html_module.escape(ORIGEM_CURTA.get(item.relevancia_origem, item.relevancia_origem))})</i> &middot; "`,
com, no topo do `app.py` (após os imports): `ORIGEM_CURTA = {"modelo": "modelo", "heuristica": "heurística", "fallback_erro": "fallback", "padrao_fonte": "padrão da fonte"}`.

Preview (`:1221-1232`): depois de `"Relevancia": ...,` acrescentar `"Origem": ORIGEM_CURTA.get(item.relevancia_origem, item.relevancia_origem),`.

- [ ] **Step 5: Exportar o diagnóstico** — `:1195`: `buffer = generate_excel(selected, topic)` vira
`buffer = generate_excel(selected, topic, diagnostico=st.session_state.get("keyword_statuses", []))`.

- [ ] **Step 6: Gate visual V11** — criar `tools/dirigir_app.py`:

```python
# -*- coding: utf-8 -*-
"""Gate visual da frente 2: dirige o app pelo navegador e imprime o que a UI diz.

Pre-requisito: o app no ar em http://localhost:8501
    (em levantamento-normativos/: python -m streamlit run app.py --server.headless true)
Uso (na raiz):  PYTHONIOENCODING=utf-8 python tools/dirigir_app.py
Usa o Chrome instalado (channel="chrome"): os navegadores do Playwright nao
estao baixados nesta maquina (ENVIRONMENT.md, 2026-09-22).
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

SAIDA = Path(__file__).resolve().parent.parent / "tests" / "golden" / "v11_passo4.png"

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
    print("\n=== GATE V11 ===")
    print("indisponíveis no relatório:", "indisponíveis" in texto)
    print("aviso 'Nenhuma fonte catalogada':", "Nenhuma fonte catalogada" in texto)
    print("origem no card:", any(o in texto for o in ("(heurística)", "(modelo)", "(fallback)")))
    print("'0 erros' NAO aparece:", "0 erros" not in texto)
    b.close()
```

Run: subir o app; `PYTHONIOENCODING=utf-8 python tools/dirigir_app.py`.
Expected: as quatro linhas do `GATE V11` em `True`; **abrir o PNG e olhar** (`tests/golden/v11_passo4.png` — ⚠ acrescentar `tests/golden/*.png` ao `.gitignore`: é evidência de sessão, não referência).

- [ ] **Step 7: Runner + golden + auditoria**

Runner TUDO VERDE (nenhum teste novo nesta task; BASELINE não muda). `golden_master.py comparar` → OK. `git diff -U0 -- '*.py' | grep '^-' | grep -v '^---'`: os comentários removidos em `:570` ("LLM enrichment (relevance scoring + categorization)") foram substituídos pelos novos.

- [ ] **Step 8: Commit**

```bash
git add levantamento-normativos/app.py tools/dirigir_app.py .gitignore
git commit -m "feat(frente2): a tela diz 'indisponivel', avisa quando nenhuma catalogada respondeu e mostra a origem da nota

Pontuacao roda sempre (heuristica sem LLM). Relatorio: 'N OK · N
indisponiveis · N sem resultado', com motivo e detalhe por fonte e badge
de busca parcial. Card e preview mostram a origem. Exportacao passa o
diagnostico para a aba da planilha. Gate V11 em tools/dirigir_app.py:
com LexML e TCU quebrados como estao hoje, e impossivel ver '0 erros'."
git push origin master
```

---

### Task 8: Fechar a frente — duráveis, lições, auditoria final

**Files:**
- Modify: `_TODO.md` (frente 2 feita; F9 perde os dois achados, que viraram código), `log.md` (entrada), `SESSION-ONBOARD-buscador.md` (§2, §6), `LESSONS.md` (se algo custou tempo), `BLOCKED-ON-RODRIGO.md` (B-04 ganha "a UI agora distingue")

- [ ] **Step 1: Critérios de pronto da spec §7, um a um, com comando e saída colados no commit**

1. V1–V11: `git log --oneline dc99d73..HEAD` mostra os 7 commits das tasks.
2. `python tools/run_all_tests.py` → TUDO VERDE; nenhum `[AVISO] cresceu`.
3. `python tools/golden_master.py comparar` → OK; `git diff d054d5b -- tests/golden/dedup_esperado.json` → vazio.
4. V11 rodado nesta task de novo (o app pode ter mudado): 4 `True`.
5. Auditoria de documentação: `git diff -U0 dc99d73..HEAD -- '*.py' | grep '^-' | grep -v '^---'` lido inteiro; cada linha removida tem substituta ou é código.

- [ ] **Step 2: Duráveis**

`_TODO.md`: seção nova `## v1.x — frente 2 ✅ (2026-MM-DD)` com os 7 commits; em **F9**, remover os dois parágrafos de "achado" (viraram código nas Tasks 4 e 7) e deixar só o pedido da aba. `log.md`: entrada `## [data] frente 2 | fonte indisponível ≠ sem resultado`. `SESSION-ONBOARD` §2/§6: próxima = **frente 5** (LM local), com o ponteiro para a pesquisa do wiki-chat no `log.md` de 22/09. `BLOCKED-ON-RODRIGO.md` B-04: acrescentar `✅ (frente 2) a UI e a planilha agora distinguem indisponível de sem resultado; a medição da lacuna continua pendente`.

- [ ] **Step 3: Commit e push**

```bash
git add -A
git commit -m "docs: fecha a frente 2 — criterios de pronto verificados"
git push origin master
```

Depois: `/checkpoint` (o Rodrigo pediu checkpoint ao fim de cada frente antes de seguir).

---

## Self-review (feito ao escrever)

**Cobertura da spec:** §3.1 → T1 · §3.2 → T2 · §3.3 → T3 · §3.4 → T4+T5+T7(Step 1) · §3.5 → T6 · §3.6 → T7 · §3.7 → gates de golden em toda task · §4 V1–V11 → T1..T7 (V10 = T6 Step 5, V11 = T7 Step 6) · §5 → Estrutura de arquivos · §7 → T8.
**Lacuna encontrada e fechada:** a spec não dizia o que o LexML faz quando a **primeira** página levanta `FonteIndisponivel` dentro de `_search_keyword` (T2 Step 5d) nem o mapeamento de `Timeout`/`ConnectionError` no TCU (T3 Step 3a) — ambos especificados aqui.
**Placeholders:** nenhum `TBD`/`TODO`/"similar à Task N"; todo step de código tem código.
**Consistência de nomes:** `FonteIndisponivel(motivo, detalhe)` · `_search_keyword_safe -> (list, FonteIndisponivel|None)` · `_fetch_all_pages -> (itens, erro, parcial)` · `score_relevance_com_origem -> list[tuple[float, str]]` · `generate_excel(results, topic, diagnostico=None)` · `ORIGEM_LABEL`/`STATUS_LABEL` (excel) vs `ORIGEM_CURTA` (app) — nomes distintos de propósito, escopos distintos.
**BASELINE ao fim:** `test_searchers 13 · test_llm_phase3 63 · test_comprehensive 98 · test_phase4 56 · tests/test_fontes_indisponiveis.py 11` = **241**.

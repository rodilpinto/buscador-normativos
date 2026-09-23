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


def test_lexml_corpo_200_nao_html_nao_xml_e_ilegivel_com_url_no_detalhe(monkeypatch):
    """Review da T2 (I1), ALEM do plano: 200 application/json nao e HTML (passa o
    sniff) nem XML (falha no parse). O detalhe tem de levar a URL efetiva com a
    query, senao nao da para reproduzir com curl (Global Constraints)."""
    s, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(200, '{"erro": "nao e SRU"}', "application/json"))
    s.search(["x"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo) == ("error", "resposta_ilegivel")
    assert "| GET " in st.detalhe and "operation=searchRetrieve" in st.detalhe


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

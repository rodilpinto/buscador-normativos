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
    assert len(resultados) == 1          # T4: o acordao real casa "turismo" no sumario
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



# --- Review da T3 (ALEM do plano): I1 formato inesperado, I2 contagem por key ---

class RespostaJsonNulo(RespostaFake):
    """200 cujo corpo e o JSON `null`: .json() devolve None (o RespostaFake levanta)."""

    def json(self):
        return None


def test_tcu_200_json_sem_items_e_resposta_ilegivel(monkeypatch):
    """I1: um 200 com o corpo de erro do proprio TCU nao pode ser lido como "sem resultado"."""
    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": lambda p: RespostaFake(200, json_data={"erro": "x"}),
                                  "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[])})
    s.search(["turismo"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo) == ("error", "resposta_ilegivel")
    assert "formato inesperado dict" in st.detalhe and "chaves=['erro']" in st.detalhe
    assert "| GET " in st.detalhe and "recupera-acordaos" in st.detalhe


def test_tcu_json_nulo_na_segunda_pagina_e_parcial(monkeypatch):
    """I1: JSON null na pagina 2 nao pode descartar a pagina 1 como erro_interno."""
    from searchers import tcu_searcher
    pagina_cheia = [dict(ACORDAO, key=f"A-{i}", numeroAcordao=str(i)) for i in range(tcu_searcher.PAGE_SIZE)]

    def acordaos(p):
        if p["inicio"] == 0:
            return RespostaFake(200, json_data=pagina_cheia)
        return RespostaJsonNulo(200, "null", "application/json")

    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": acordaos,
                                  "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[])})
    s.search(["turismo"], max_results=100)
    st = s.keyword_statuses[0]
    assert st.parcial is True and st.motivo != "erro_interno"
    assert "pagina 2 (inicio=20)" in st.detalhe and "formato inesperado NoneType" in st.detalhe
    assert f"Acórdãos: parcial ({tcu_searcher.PAGE_SIZE} itens" in st.detalhe   # a pagina 1 ficou


def test_tcu_itens_repetidos_entre_paginas_contam_uma_vez_por_key(monkeypatch):
    """I2: a API as vezes devolve 40 itens para quantidade=20 (medido: 580 itens, 500 keys unicas)."""
    def acordaos(p):
        if p["inicio"] == 0:
            return RespostaFake(200, json_data=[dict(ACORDAO, key=f"A-{i}") for i in range(0, 20)])
        if p["inicio"] == 20:
            return RespostaFake(200, json_data=[dict(ACORDAO, key=f"A-{i}") for i in range(10, 50)])
        return RespostaFake(200, json_data=[])

    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": acordaos,
                                  "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[])})
    s.search(["turismo"], max_results=100)
    assert "Acórdãos: ok (50 itens" in s.keyword_statuses[0].detalhe

def test_tcu_item_que_quebra_o_mapeamento_vira_erro_interno_declarado(monkeypatch):
    """H2: um item malformado derrubava search() inteiro; agora e erro_interno por keyword, nao sumico."""
    quebrado = dict(ACORDAO, titulo=None, numeroAcordao=None, sumario=123)   # " ".join com int -> TypeError
    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": lambda p: RespostaFake(200, json_data=[quebrado]),
                                  "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[])})
    s.search(["turismo"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo) == ("error", "erro_interno")
    assert "TypeError" in st.detalhe


def test_tcu_acordao_real_mapeia_titulo_numero_ano_sumario_link_situacao():
    from searchers.tcu_searcher import TCUSearcher
    r = TCUSearcher()._map_acordao(ACORDAO, "turismo")
    assert r.nome == ACORDAO["titulo"]
    # T4 (tester): o colegiado entra no numero — as Camaras numeram em series proprias
    assert r.numero == f'{ACORDAO["numeroAcordao"]}/{ACORDAO["anoAcordao"]}-TCU-{ACORDAO["colegiado"]}'
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


# --- T4, defeito do tester (ALEM do plano): colegiados numeram em series proprias ---
# Dois acordaos REAIS capturados ao vivo em 23/09 (tester da T4): mesmo numero, ano e
# dataSessao, 1a x 2a Camara. Com numero = "N/AAAA" colidiam no id e o 2o SUMIA em
# search(); o dedup (tipo_numero) os fundiria mesmo com ids distintos.
COLEGIADOS_REAIS = json.loads((FIXTURES / "tcu_acordaos_colegiados_real.json").read_text(encoding="utf-8"))


def test_tcu_acordaos_de_colegiados_diferentes_com_mesmo_numero_sobrevivem_ao_search(monkeypatch):
    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": lambda p: RespostaFake(200, json_data=COLEGIADOS_REAIS),
                                  "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[])})
    resultados = s.search(["acórdão de relação"], max_results=50)
    assert sorted(r.nome for r in resultados) == sorted(a["titulo"] for a in COLEGIADOS_REAIS)
    assert len({r.id for r in resultados}) == 2


def test_tcu_acordaos_de_colegiados_diferentes_sobrevivem_ao_dedup_e_a_mesma_copia_funde():
    from deduplicator import deduplicate
    from searchers.tcu_searcher import TCUSearcher
    s = TCUSearcher()
    a, b = (s._map_acordao(x, "k") for x in COLEGIADOS_REAIS)
    copia_de_a = s._map_acordao(dict(COLEGIADOS_REAIS[0]), "outra")
    saida = deduplicate([a, b, copia_de_a])
    assert sorted(r.nome for r in saida) == sorted(x["titulo"] for x in COLEGIADOS_REAIS)
    assert next(r for r in saida if r.nome == a.nome).found_by == "k, outra"   # a copia fundiu


def test_tcu_acordao_com_colegiado_nulo_nao_escreve_none():
    """Review da T4 (M5, pre-existente): a API pode mandar `colegiado: null` — nada de "TCU - None"."""
    from searchers.tcu_searcher import TCUSearcher
    r = TCUSearcher()._map_acordao(dict(ACORDAO, colegiado=None), "turismo")
    assert r.orgao_emissor == "TCU"
    assert r.numero == f'{ACORDAO["numeroAcordao"]}/{ACORDAO["anoAcordao"]}'   # sem colegiado: "N/AAAA"
    assert "None" not in r.orgao_emissor + r.numero + r.nome


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


def test_cse_falha_nao_vaza_a_chave_no_log(monkeypatch, caplog):
    """Item carregado da review da T2 (ALEM do plano): a chave do CSE vai na query
    string e a mensagem crua do requests traz a URL inteira — nenhum log de
    google_searcher pode imprimi-la (nem o detalhe/error_message do status).

    Review da T5: o segredo e CURTO e vem no COMECO da mensagem, para sobreviver ao
    corte de 120 chars do ramo `conexao` — senao o teste passava ate com redigir()
    trocado por identidade (mutante do reviewer). Provado: com o mutante, falha."""
    import logging
    from searchers import google_searcher
    segredo = "AIzaK1"
    monkeypatch.setattr(google_searcher, "_BACKEND", "cse")
    monkeypatch.setattr(google_searcher, "_google_api_key", segredo)

    def cai(url, params=None, timeout=None, **kw):
        raise requests.exceptions.ConnectionError(
            f"/customsearch/v1?{urlencode(params or {})} Max retries exceeded "
            "(Caused by NewConnectionError('sem rota'))")

    monkeypatch.setattr("searchers.google_searcher.requests.get", cai)
    caplog.set_level(logging.DEBUG)
    s = google_searcher.GoogleSearcher()
    s.search(["x", "y"], max_results=5)
    st = s.keyword_statuses[0]
    assert st.motivo == "conexao"
    assert "key=***" in st.detalhe                                   # a chave estava la e foi redigida
    assert segredo not in caplog.text
    assert all(segredo not in k.detalhe + k.error_message for k in s.keyword_statuses)

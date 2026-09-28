# -*- coding: utf-8 -*-
"""Cadeia de provedores do LLM (llm/cadeia.py): ordem, rodizio de modelos, esperas,
chave do usuario por sessao. 23/09 (cadeia A > B > C); 25/09 (modelos, presets, usuario).

Nenhum teste faz rede: os transportes de cada tipo sao dublados.

Rodar de dentro de levantamento-normativos/:
    python -m pytest tests/test_cadeia_llm.py -q
"""
from __future__ import annotations

import contextvars
import time

import pytest

from llm import cadeia, gemini_client as gc


def _prov(nome, tipo="gemini", modelos=("m1", "m2")):
    return cadeia._novo_provedor(nome, tipo, "segredo-" + nome, list(modelos), "http://x/v1")


@pytest.fixture
def provs(monkeypatch):
    lista = [_prov("A", "openai"), _prov("B"), _prov("C")]
    monkeypatch.setattr(cadeia, "_provedores", lista)
    cadeia.usar_contexto(cadeia.novo_contexto())
    yield lista
    cadeia.usar_contexto(None)


def _dublar(monkeypatch, comportamento):
    """comportamento: "prov/modelo" -> texto devolvido ou Exception levantada (padrao "ok-<chave>")."""
    chamados = []

    def gerar(p, modelo, prompt, temperature, max_tokens):
        k = f"{p['nome']}/{modelo}"
        chamados.append(k)
        r = comportamento.get(k, f"ok-{k}")
        if isinstance(r, Exception):
            raise r
        return r

    monkeypatch.setattr(cadeia, "_gerar_openai", gerar)
    monkeypatch.setattr(cadeia, "_gerar_gemini", gerar)
    return chamados


def test_usa_o_primeiro_que_responde(provs, monkeypatch):
    chamados = _dublar(monkeypatch, {})
    assert cadeia.gerar("p") == ("ok-A/m1", "A (m1)")
    assert chamados == ["A/m1"]
    assert cadeia.ultimo_usado() == "A (m1)"


def test_cota_do_modelo_roda_para_o_proximo_modelo_do_mesmo_provedor(provs, monkeypatch):
    chamados = _dublar(monkeypatch, {"A/m1": RuntimeError("429 RESOURCE_EXHAUSTED PerMinute")})
    assert cadeia.gerar("p")[0] == "ok-A/m2"
    assert chamados == ["A/m1", "A/m2"]
    assert gc._generate("p") == "ok-A/m2"          # m1 em espera: nem tenta
    assert chamados == ["A/m1", "A/m2", "A/m2"]


def test_cota_diaria_espera_ate_a_meia_noite_do_pacifico(provs, monkeypatch):
    _dublar(monkeypatch, {"B/m1": RuntimeError(
        "429 RESOURCE_EXHAUSTED quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier")})
    provs[0]["bloqueado_ate"] = time.time() + 999
    cadeia.gerar("p")
    espera = provs[1]["modelo_bloqueado_ate"]["m1"] - time.time()
    assert 60 < espera <= 24 * 3600 + 5


def test_rede_e_chave_invalida_param_o_provedor_inteiro(provs, monkeypatch):
    chamados = _dublar(monkeypatch, {
        "A/m1": ConnectionError("10.10.111.125 inalcancavel"),
        "B/m1": RuntimeError("400 API_KEY_INVALID"),
    })
    assert cadeia.gerar("p")[0] == "ok-C/m1"
    assert chamados == ["A/m1", "B/m1", "C/m1"]   # nem A/m2 nem B/m2
    assert provs[0]["bloqueado_ate"] > time.time()
    assert provs[1]["bloqueado_ate"] > provs[0]["bloqueado_ate"]   # chave ruim espera mais que rede
    assert [l.endswith("em espera") for l in cadeia.descrever()] == [True, True, False]


def test_sobrecarga_503_para_so_o_modelo_por_um_minuto(provs, monkeypatch):
    _dublar(monkeypatch, {"A/m1": RuntimeError("503 UNAVAILABLE high demand")})
    assert cadeia.gerar("p")[0] == "ok-A/m2"
    assert provs[0]["bloqueado_ate"] == 0.0
    assert provs[0]["modelo_bloqueado_ate"]["m1"] - time.time() <= 61


def test_todos_falham_devolve_none(provs, monkeypatch):
    _dublar(monkeypatch, {k: OSError("x") for k in ("A/m1", "A/m2", "B/m1", "B/m2", "C/m1", "C/m2")})
    assert cadeia.gerar("p") == (None, None)
    assert gc._generate("p") is None


def test_resposta_vazia_nao_troca_de_modelo(provs, monkeypatch):
    chamados = _dublar(monkeypatch, {"A/m1": None})
    assert gc._generate("p") is None
    assert chamados == ["A/m1"]


def test_espera_expira(provs, monkeypatch):
    chamados = _dublar(monkeypatch, {})
    provs[0]["bloqueado_ate"] = 1.0
    provs[0]["modelo_bloqueado_ate"]["m1"] = 1.0
    assert cadeia.gerar("p")[0] == "ok-A/m1"
    assert chamados == ["A/m1"]


def test_sem_provedor_nao_ha_llm(monkeypatch):
    monkeypatch.setattr(cadeia, "_provedores", [])
    cadeia.usar_contexto(None)
    assert gc.is_available() is False
    assert gc._generate("p") is None


def test_chave_do_usuario_vai_na_frente_so_na_sessao_dela(provs, monkeypatch):
    chamados = _dublar(monkeypatch, {})
    usuario = cadeia.provedor_do_usuario("groq", "chave-do-usuario")
    assert usuario["base_url"] == "https://api.groq.com/openai/v1"
    ctx = cadeia.novo_contexto()
    ctx["usuario"] = usuario
    cadeia.usar_contexto(ctx)
    assert cadeia.gerar("p")[1] == f"usuario ({usuario['modelos'][0]})"
    assert ctx["ultimo"].startswith("usuario")
    # outra sessao (outra thread/contexto) nao ve a chave nem a ultima resposta
    outra = contextvars.Context()
    assert outra.run(lambda: cadeia._contexto.get()["usuario"]) is None
    assert outra.run(lambda: cadeia.descrever())[0].startswith("A")
    assert not any("chave-do-usuario" in l for l in cadeia.descrever())


def test_provedor_do_usuario_incompleto_e_none():
    assert cadeia.provedor_do_usuario("groq", "") is None
    assert cadeia.provedor_do_usuario("openai", "k", modelo="m") is None          # sem URL
    assert cadeia.provedor_do_usuario("openai", "", modelo="m", base_url="http://h/v1") is not None  # local sem chave
    assert cadeia.provedor_do_usuario("xyz", "k") is None
    assert cadeia.provedor_do_usuario("gemini", "k", modelo="a, b")["modelos"] == ["a", "b"]


def test_montar_le_os_segredos_na_ordem(monkeypatch):
    if cadeia._sdk == "none":
        pytest.skip("sem SDK Gemini instalado")
    valores = {"LLM_BASE_URL": "http://10.10.111.125:1234/v1/", "LLM_MODEL": "gemma, qwen",
               "GEMINI_API_KEY": "k1", "GEMINI_API_KEY_2": "k2", "OPENROUTER_API_KEY": "k3",
               "GROQ_API_KEY": "k4", "GROQ_MODELS": "x"}
    monkeypatch.setattr(cadeia, "_segredo", lambda n: valores.get(n, ""))
    ps = cadeia._montar_provedores()
    assert [p["nome"] for p in ps] == ["local", "gemini", "gemini-2", "groq", "openrouter"]
    assert ps[0]["base_url"] == "http://10.10.111.125:1234/v1"
    assert ps[0]["modelos"] == ["gemma", "qwen"]
    assert ps[1]["modelos"] == cadeia.GEMINI_MODELOS_PADRAO
    assert ps[3]["modelos"] == ["x"]
    valores["LLM_ORDEM"] = "openrouter,gemini"
    assert [p["nome"] for p in cadeia._montar_provedores()] == \
        ["openrouter", "gemini", "local", "gemini-2", "groq"]


def test_log_nunca_leva_a_chave(provs, monkeypatch, caplog):
    _dublar(monkeypatch, {"A/m1": RuntimeError("401 bad key segredo-A")})
    cadeia.gerar("p")
    assert "segredo-A" not in caplog.text


def test_pensamento_de_modelo_de_raciocinio_e_removido(monkeypatch):
    class R:
        status_code = 200
        def json(self):
            return {"choices": [{"message": {"content": "<think>[1,2]</think>\n[0.9, 0.1]"}}]}
    import requests
    monkeypatch.setattr(requests, "post", lambda *a, **k: R())
    p = _prov("A", "openai")
    assert cadeia._gerar_openai(p, "m", "p", 0.0, 10) == "[0.9, 0.1]"

# -*- coding: utf-8 -*-
"""Testes do llm_cadeia: ordem, rodizio de modelos, esperas, chave do usuario por sessao,
sistema/json, segunda chave. Viajam com a pasta: nao importam nada do app.

Nenhum teste faz rede: os transportes sao dublados.

Rodar da pasta que CONTEM llm_cadeia/:
    python -m pytest llm_cadeia/test_llm_cadeia.py -q
"""
from __future__ import annotations

import contextvars
import time

import pytest

from llm_cadeia import nucleo as cadeia


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

    def gerar(p, modelo, prompt, sistema, json_, temperature, max_tokens):
        k = f"{p['nome']}/{modelo}"
        chamados.append(k)
        r = comportamento.get(k, f"ok-{k}")
        if isinstance(r, Exception):
            raise r
        return r

    monkeypatch.setattr(cadeia, "_gerar_openai", gerar)
    monkeypatch.setattr(cadeia, "_gerar_gemini", gerar)
    return chamados


# --- ordem e rodizio -------------------------------------------------------

def test_usa_o_primeiro_que_responde(provs, monkeypatch):
    chamados = _dublar(monkeypatch, {})
    r = cadeia.gerar("p")
    assert (r.texto, r.origem, r.tentativas) == ("ok-A/m1", "A (m1)", [])
    assert chamados == ["A/m1"]
    assert cadeia.ultimo_usado() == "A (m1)"


def test_cota_do_modelo_roda_para_o_proximo_modelo_do_mesmo_provedor(provs, monkeypatch):
    chamados = _dublar(monkeypatch, {"A/m1": RuntimeError("429 RESOURCE_EXHAUSTED PerMinute")})
    assert cadeia.gerar("p").texto == "ok-A/m2"
    assert chamados == ["A/m1", "A/m2"]
    r = cadeia.gerar("p")                            # m1 em espera: nem tenta
    assert r.texto == "ok-A/m2" and r.tentativas == ["A/m1: em espera"]
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
    assert cadeia.gerar("p").texto == "ok-C/m1"
    assert chamados == ["A/m1", "B/m1", "C/m1"]   # nem A/m2 nem B/m2
    assert provs[0]["bloqueado_ate"] > time.time()
    assert provs[1]["bloqueado_ate"] > provs[0]["bloqueado_ate"]   # chave ruim espera mais que rede
    assert [l.endswith("em espera") for l in cadeia.descrever()] == [True, True, False]


def test_sobrecarga_503_para_so_o_modelo_por_um_minuto(provs, monkeypatch):
    _dublar(monkeypatch, {"A/m1": RuntimeError("503 UNAVAILABLE high demand")})
    assert cadeia.gerar("p").texto == "ok-A/m2"
    assert provs[0]["bloqueado_ate"] == 0.0
    assert provs[0]["modelo_bloqueado_ate"]["m1"] - time.time() <= 61


def test_todos_falham_devolve_none_e_explica(provs, monkeypatch):
    _dublar(monkeypatch, {k: OSError("x") for k in ("A/m1", "A/m2", "B/m1", "B/m2", "C/m1", "C/m2")})
    r = cadeia.gerar("p")
    assert (r.texto, r.origem) == (None, None)
    assert [t.split(":")[0] for t in r.tentativas] == ["A/m1", "A/m2", "B/m1", "B/m2", "C/m1", "C/m2"]


def test_gerar_nunca_levanta(provs, monkeypatch):
    monkeypatch.setattr(cadeia, "_cadeia_efetiva", lambda: 1 / 0)
    r = cadeia.gerar("p")
    assert r.texto is None and r.tentativas == ["erro interno: ZeroDivisionError"]


def test_resposta_vazia_nao_troca_de_modelo(provs, monkeypatch):
    chamados = _dublar(monkeypatch, {"A/m1": None})
    r = cadeia.gerar("p")
    assert (r.texto, r.origem) == (None, "A (m1)")
    assert chamados == ["A/m1"]


def test_espera_expira(provs, monkeypatch):
    chamados = _dublar(monkeypatch, {})
    provs[0]["bloqueado_ate"] = 1.0
    provs[0]["modelo_bloqueado_ate"]["m1"] = 1.0
    assert cadeia.gerar("p").texto == "ok-A/m1"
    assert chamados == ["A/m1"]


def test_sem_provedor_nao_ha_llm(monkeypatch):
    monkeypatch.setattr(cadeia, "_provedores", [])
    cadeia.usar_contexto(None)
    assert cadeia.disponivel() is False
    assert cadeia.gerar("p").texto is None


# --- chave do usuario ------------------------------------------------------

def test_chave_do_usuario_vai_na_frente_so_na_sessao_dela(provs, monkeypatch):
    _dublar(monkeypatch, {})
    usuario = cadeia.provedor_do_usuario("groq", "chave-do-usuario")
    assert usuario["base_url"] == "https://api.groq.com/openai/v1"
    ctx = cadeia.novo_contexto()
    ctx["usuario"] = usuario
    cadeia.usar_contexto(ctx)
    assert cadeia.gerar("p").origem == f"usuario ({usuario['modelos'][0]})"
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
    if cadeia._sdk != "none":
        assert cadeia.provedor_do_usuario("gemini", "k", modelo="a, b")["modelos"] == ["a", "b"]


# --- configuracao ----------------------------------------------------------

def test_montar_le_os_segredos_na_ordem(monkeypatch):
    if cadeia._sdk == "none":
        pytest.skip("sem SDK Gemini instalado")
    valores = {"LLM_BASE_URL": "http://10.10.111.125:1234/v1/", "LLM_MODEL": "gemma, qwen",
               "GEMINI_API_KEY": "k1", "GEMINI_API_KEY_2": "k2", "OPENROUTER_API_KEY": "k3",
               "GROQ_API_KEY": "k4", "GROQ_API_KEY_2": "k5", "GROQ_MODELS": "x"}
    monkeypatch.setattr(cadeia, "_segredo", lambda n: valores.get(n, ""))
    ps = cadeia._montar_provedores()
    assert [p["nome"] for p in ps] == ["local", "gemini", "gemini-2", "groq", "groq-2", "openrouter"]
    assert ps[0]["base_url"] == "http://10.10.111.125:1234/v1"
    assert ps[0]["modelos"] == ["gemma", "qwen"]
    assert ps[1]["modelos"] == cadeia.GEMINI_MODELOS_PADRAO
    assert ps[3]["modelos"] == ps[4]["modelos"] == ["x"]
    assert ps[4]["chave"] == "k5"
    valores["LLM_ORDEM"] = "openrouter,groq-2,gemini"
    assert [p["nome"] for p in cadeia._montar_provedores()] == \
        ["openrouter", "groq-2", "gemini", "local", "gemini-2", "groq"]


def test_log_e_tentativas_nunca_levam_a_chave(provs, monkeypatch, caplog):
    _dublar(monkeypatch, {"A/m1": RuntimeError("401 bad key segredo-A")})
    r = cadeia.gerar("p")
    assert "segredo-A" not in caplog.text
    assert not any("segredo-A" in t for t in r.tentativas)


# --- transportes -----------------------------------------------------------

class _RespostaFake:
    status_code = 200

    def __init__(self, conteudo):
        self.conteudo = conteudo

    def json(self):
        return {"choices": [{"message": {"content": self.conteudo}}]}


def test_pensamento_de_modelo_de_raciocinio_e_removido(monkeypatch):
    import requests
    monkeypatch.setattr(requests, "post", lambda *a, **k: _RespostaFake("<think>[1,2]</think>\n[0.9, 0.1]"))
    assert cadeia._gerar_openai(_prov("A", "openai"), "m", "p", None, False, 0.0, 10) == "[0.9, 0.1]"


def test_sistema_vira_mensagem_system_e_json_tira_a_cerca(monkeypatch):
    import requests
    enviado = {}

    def post(url, headers, json, timeout):
        enviado.update(json)
        return _RespostaFake('```json\n{"a": 1}\n```')

    monkeypatch.setattr(requests, "post", post)
    texto = cadeia._gerar_openai(_prov("A", "openai"), "m", "p", "voce e um auditor", True, 0.0, 10)
    assert texto == '{"a": 1}'
    assert enviado["messages"] == [{"role": "system", "content": "voce e um auditor"},
                                   {"role": "user", "content": "p"}]
    assert "response_format" not in enviado


def test_sem_json_a_cerca_fica():
    assert cadeia._limpar("```json\n[1]\n```", False) == "```json\n[1]\n```"
    assert cadeia._limpar("```\n[1]\n```", True) == "[1]"


def test_gemini_recebe_sistema_e_mime_json(monkeypatch):
    if cadeia._sdk != "genai":
        pytest.skip("sem google-genai")
    capturado = {}

    class Modelos:
        def generate_content(self, model, contents, config):
            capturado["config"] = config
            return type("R", (), {"text": '{"ok": true}'})()

    p = _prov("B")
    p["cliente"] = type("C", (), {"models": Modelos()})()
    assert cadeia._gerar_gemini(p, "m", "p", "sys", True, 0.0, 10) == '{"ok": true}'
    assert capturado["config"].system_instruction == "sys"
    assert capturado["config"].response_mime_type == "application/json"
    assert capturado["config"].max_output_tokens == 4096   # piso: modelos que pensam


# --- diagnostico -------------------------------------------------------------

def test_diagnostico_lista_cada_modelo_e_ignora_esperas(provs, monkeypatch):
    from llm_cadeia import diagnostico
    _dublar(monkeypatch, {"A/m2": RuntimeError("404 NOT_FOUND segredo-A"), "B/m1": None})
    provs[2]["bloqueado_ate"] = time.time() + 999   # em espera, mas o diagnostico testa mesmo assim
    linhas = diagnostico.diagnosticar()
    assert [(p, m) for p, m, _ in linhas] == [("A", "m1"), ("A", "m2"), ("B", "m1"), ("B", "m2"),
                                               ("C", "m1"), ("C", "m2")]
    assert linhas[0][2] == "ok" and linhas[2][2] == "resposta vazia"
    assert "404" in linhas[1][2] and "segredo-A" not in linhas[1][2]

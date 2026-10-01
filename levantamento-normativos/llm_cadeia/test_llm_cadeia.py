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
        "A/m1": ConnectionError("servidor-local inalcancavel"),
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
    valores = {"LLM_BASE_URL": "http://servidor-local:1234/v1/", "LLM_MODEL": "gemma, qwen",
               "GEMINI_API_KEY": "k1", "GEMINI_API_KEY_2": "k2", "OPENROUTER_API_KEY": "k3",
               "GROQ_API_KEY": "k4", "GROQ_API_KEY_2": "k5", "GROQ_MODELS": "x"}
    monkeypatch.setattr(cadeia, "_segredo", lambda n: valores.get(n, ""))
    ps = cadeia._montar_provedores()
    assert [p["nome"] for p in ps] == ["local", "gemini", "gemini-2", "groq", "groq-2", "openrouter"]
    assert ps[0]["base_url"] == "http://servidor-local:1234/v1"
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


def test_ao_responder_avisa_quem_respondeu_e_nunca_quebra_o_gerar(provs, monkeypatch):
    _dublar(monkeypatch, {"A/m1": None})
    avisos = []
    ctx = cadeia.novo_contexto()
    ctx["ao_responder"] = avisos.append
    cadeia.usar_contexto(ctx)
    cadeia.gerar("p")                                 # resposta vazia: nao avisa
    assert avisos == []
    provs[0]["modelos"] = ["m2"]
    assert cadeia.gerar("p").texto == "ok-A/m2"
    assert avisos == ["A (m2)"]
    ctx["ao_responder"] = lambda origem: 1 / 0        # gancho quebrado nao derruba a resposta
    assert cadeia.gerar("p").texto == "ok-A/m2"


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


class _Resposta400:
    status_code = 400

    def __init__(self, texto):
        self.text = texto


@pytest.mark.parametrize("erro", [
    "Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.",
    "Unsupported value: 'temperature' does not support 0.0 with this model. Only the default (1) value is supported.",
])
def test_modelo_de_raciocinio_da_openai_repete_com_max_completion_tokens(monkeypatch, erro):
    import requests
    corpos = []

    def post(url, headers, json, timeout):
        corpos.append(dict(json))
        return _Resposta400(erro) if len(corpos) == 1 else _RespostaFake("ok")

    monkeypatch.setattr(requests, "post", post)
    assert cadeia._gerar_openai(_prov("A", "openai"), "gpt-5-mini", "p", None, False, 0.0, 10) == "ok"
    assert len(corpos) == 2
    assert corpos[0]["max_tokens"] == 4096 and corpos[0]["temperature"] == 0.0
    assert corpos[1]["max_completion_tokens"] == 4096
    assert "max_tokens" not in corpos[1] and "temperature" not in corpos[1]


def test_outro_400_nao_repete(monkeypatch):
    import requests
    chamadas = []

    def post(url, headers, json, timeout):
        chamadas.append(1)
        return _Resposta400("400 model not found")

    monkeypatch.setattr(requests, "post", post)
    with pytest.raises(RuntimeError, match="400"):
        cadeia._gerar_openai(_prov("A", "openai"), "m", "p", None, False, 0.0, 10)
    assert chamadas == [1]


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


# --- 1.1.0: pedidos do checklist (a-e) ----------------------------------------

def _montar_com(monkeypatch, valores):
    monkeypatch.setattr(cadeia, "_segredo", lambda n: valores.get(n, ""))
    return {p["nome"]: p for p in cadeia._montar_provedores()}


class _Post:
    """Dublê de requests.post: devolve as respostas na ordem e guarda cada corpo/timeout."""

    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.corpos, self.timeouts = [], []

    def __call__(self, url, headers, json, timeout):
        self.corpos.append(dict(json))
        self.timeouts.append(timeout)
        return self.respostas.pop(0)


def test_a_local_espera_300s_por_padrao_e_LLM_TIMEOUT_S_troca(monkeypatch):
    base = {"LLM_BASE_URL": "http://servidor-local:1234/v1", "LLM_MODEL": "g", "GROQ_API_KEY": "k"}
    ps = _montar_com(monkeypatch, base)
    assert ps["local"]["timeout"] == 300.0
    assert ps["groq"]["timeout"] == cadeia._TIMEOUT_NUVEM_S == 120.0
    assert _montar_com(monkeypatch, {**base, "LLM_TIMEOUT_S": "600"})["local"]["timeout"] == 600.0
    assert _montar_com(monkeypatch, {**base, "LLM_TIMEOUT_S": "abc"})["local"]["timeout"] == 300.0
    assert _montar_com(monkeypatch, {**base, "LLM_TIMEOUT_S": "-1"})["local"]["timeout"] == 300.0

    import requests
    post = _Post(_RespostaFake("ok"))
    monkeypatch.setattr(requests, "post", post)
    p = _montar_com(monkeypatch, {**base, "LLM_TIMEOUT_S": "600"})["local"]
    assert cadeia._gerar_openai(p, "g", "p", None, False, 0.0, 10) == "ok"
    assert post.timeouts == [(5.0, 600.0)]


def test_b_desligar_raciocinio_so_no_local(monkeypatch):
    base = {"LLM_BASE_URL": "http://servidor-local:1234/v1", "LLM_MODEL": "g", "GROQ_API_KEY": "k"}
    assert _montar_com(monkeypatch, base)["local"]["sem_raciocinio"] is False
    ps = _montar_com(monkeypatch, {**base, "LLM_DISABLE_THINKING": "1"})
    assert ps["local"]["sem_raciocinio"] is True
    assert ps["groq"]["sem_raciocinio"] is False

    import requests
    post = _Post(_RespostaFake("ok"), _RespostaFake("ok"))
    monkeypatch.setattr(requests, "post", post)
    cadeia._gerar_openai(ps["local"], "g", "p", None, False, 0.0, 10)
    cadeia._gerar_openai(ps["groq"], "m", "p", None, False, 0.0, 10)
    assert post.corpos[0]["chat_template_kwargs"] == {"enable_thinking": False}
    assert "chat_template_kwargs" not in post.corpos[1]


def test_b_servidor_que_recusa_o_campo_recebe_a_chamada_de_novo_sem_ele(monkeypatch):
    import requests
    p = _prov("local", "openai")
    p["sem_raciocinio"] = True
    post = _Post(_Resposta400("Unrecognized request argument supplied: chat_template_kwargs"), _RespostaFake("ok"))
    monkeypatch.setattr(requests, "post", post)
    assert cadeia._gerar_openai(p, "g", "p", None, False, 0.0, 10) == "ok"
    assert "chat_template_kwargs" in post.corpos[0]
    assert "chat_template_kwargs" not in post.corpos[1]


def test_d_LLM_SOMENTE_usa_so_os_listados_nessa_ordem(monkeypatch):
    if cadeia._sdk == "none":
        pytest.skip("sem SDK Gemini instalado")
    base = {"LLM_BASE_URL": "http://servidor-local:1234/v1", "LLM_MODEL": "g", "GEMINI_API_KEY": "k1",
            "GROQ_API_KEY": "k2", "GROQ_API_KEY_2": "k3", "LLM_ORDEM": "gemini"}
    valores = {**base, "LLM_SOMENTE": "groq-2, gemini, nao-existe"}
    monkeypatch.setattr(cadeia, "_segredo", lambda n: valores.get(n, ""))
    assert [p["nome"] for p in cadeia._montar_provedores()] == ["groq-2", "gemini"]
    valores["LLM_SOMENTE"] = ""   # sem LLM_SOMENTE, LLM_ORDEM volta a pôr os omitidos no fim
    assert [p["nome"] for p in cadeia._montar_provedores()] == ["gemini", "local", "groq", "groq-2"]


def test_d_recarregar_remonta_a_cadeia(monkeypatch):
    monkeypatch.setattr(cadeia, "_provedores", cadeia._provedores)   # devolvido no fim do teste
    valores = {"GROQ_API_KEY": "k", "CEREBRAS_API_KEY": "k", "LLM_SOMENTE": "cerebras"}
    monkeypatch.setattr(cadeia, "_segredo", lambda n: valores.get(n, ""))
    cadeia.usar_contexto(None)
    import llm_cadeia
    llm_cadeia.recarregar()
    assert [c.split(" ")[0] for c in cadeia.descrever()] == ["cerebras"]


def test_e_gemini_tem_tempo_limite(monkeypatch):
    if cadeia._sdk != "genai":
        pytest.skip("sem google-genai")
    criado = {}

    class Cliente:
        def __init__(self, api_key, http_options=None):
            criado["http_options"] = http_options
            self.models = self

        def generate_content(self, model, contents, config):
            return type("R", (), {"text": "ok"})()

    monkeypatch.setattr(cadeia._genai_new, "Client", Cliente)
    p = _prov("B")
    assert p["timeout"] == cadeia._TIMEOUT_NUVEM_S
    assert cadeia._gerar_gemini(p, "m", "p", None, False, 0.0, 10) == "ok"
    assert criado["http_options"].timeout == int(cadeia._TIMEOUT_NUVEM_S * 1000)   # a SDK usa milissegundos


def test_e_timeout_do_gemini_para_o_provedor_como_falha_de_rede(provs, monkeypatch):
    class ReadTimeout(Exception):   # o nome do tipo é o que o httpx levanta
        pass

    _dublar(monkeypatch, {"B/m1": ReadTimeout("The read operation timed out")})
    provs[0]["bloqueado_ate"] = time.time() + 999
    assert cadeia.gerar("p").texto == "ok-C/m1"
    assert 0 < provs[1]["bloqueado_ate"] - time.time() <= cadeia._ESPERA_REDE_S + 1


def test_c_pasta_sem_dado_interno():
    """A pasta tem de poder ir para um repo público sem exceção na trava de publicação.

    Os padrões são montados em partes para este arquivo não conter o que procura.
    """
    import re
    from pathlib import Path

    padroes = {
        "IP de rede privada": re.compile(
            r"\b(?:10|192\.168|172\.(?:1[6-9]|2\d|3[01]))(?:\.\d{1,3}){2,3}\b(?!\.)"),
        "login institucional": re.compile("nuati" + r"[.@]" + "secin", re.IGNORECASE),
        "servidor git interno": re.compile("git" + r"\." + "camara", re.IGNORECASE),
    }
    pasta = Path(__file__).parent
    achados = []
    for arquivo in sorted(pasta.rglob("*")):
        if not arquivo.is_file() or "__pycache__" in arquivo.parts:
            continue
        texto = arquivo.read_text(encoding="utf-8", errors="ignore")
        for nome, padrao in padroes.items():
            for m in padrao.finditer(texto):
                achados.append(f"{arquivo.name}: {nome}: {m.group(0)}")
    assert achados == []

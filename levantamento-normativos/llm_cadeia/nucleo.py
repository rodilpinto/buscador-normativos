"""Cadeia de provedores de LLM — nucleo do pacote GENERICO ``llm_cadeia``.

Nao importa nada do projeto: so stdlib, ``requests`` e (opcional) ``google-genai``.
Para levar a outro app, copie a PASTA ``llm_cadeia/`` inteira (ver README.md dela) e
chame ``gerar(prompt)``. Nasceu em ``llm/cadeia.py`` do buscador-normativos (23-25/09);
virou pacote em 28/09; a origem passou para o nuati-framework em 29/09.

Ordem padrao de tentativa:

    usuario       chave que o proprio usuario digitou na tela (so na sessao dele)
    local         LLM_BASE_URL + LLM_MODEL (+ LLM_API_KEY) — servidor OpenAI-compativel
                  da rede interna (intranet: a nuvem NAO alcanca)
    gemini        GEMINI_API_KEY     (conta institucional)
    gemini-2      GEMINI_API_KEY_2   (segunda conta; so soma cota se for OUTRO projeto Google)
    groq, groq-2              GROQ_API_KEY, GROQ_API_KEY_2
    cerebras, cerebras-2      CEREBRAS_API_KEY, CEREBRAS_API_KEY_2
    openrouter, openrouter-2  OPENROUTER_API_KEY, OPENROUTER_API_KEY_2

``LLM_ORDEM`` (ex.: "local,gemini,groq") troca a ordem (omitidos vao para o fim);
``LLM_SOMENTE`` (ex.: "groq") usa so os listados. "usuario" vem sempre primeiro.
Cada provedor tem uma LISTA de modelos (``<NOME>_MODELS``, separados por virgula, troca o
padrao sem deploy). Dentro de um provedor, os modelos sao tentados em ordem.

Tempo limite de resposta: ``local`` = ``LLM_TIMEOUT_S`` (padrao 300 s); nuvem = 120 s.
``LLM_DISABLE_THINKING=1`` desliga o raciocinio do ``local`` (chat_template_kwargs).

Por que rodar entre modelos: a cota do Gemini e "per project" e por modelo — os quotaId
do 429 sao ``GenerateRequestsPerDayPerProjectPerModel`` / ``...PerMinutePerProjectPerModel``
(docs ai.google.dev/gemini-api/docs/rate-limits, conferido em 25/09/2026). Esgotou o
flash-lite, o flash do MESMO projeto ainda tem cota propria. Groq tambem limita por modelo
e por organizacao; OpenRouter limita os ``:free`` por conta (20/min, 50/dia sem creditos).

Espera apos falha (nunca some item: so decide quem responde):
    429 por dia        -> modelo parado ate a meia-noite do Pacifico (reset do Gemini)
    429 por minuto     -> modelo parado 60 s
    503/500/sobrecarga -> modelo parado 60 s
    404 (modelo nao existe para esta chave) -> modelo parado 6 h
    401/403 (chave invalida/sem permissao)  -> provedor inteiro parado 6 h
    rede/timeout       -> provedor inteiro parado 5 min
    outro erro         -> modelo parado 5 min

Nenhuma funcao publica levanta excecao; sem nenhum provedor, ``gerar`` devolve
``Resposta(texto=None, origem=None, ...)`` e o app roda sem LLM. Chaves nunca aparecem em
log nem em ``descrever()``.
"""

from __future__ import annotations

import contextvars
import logging
import os
import re
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SDK Gemini — google-genai (new) with fallback to google-generativeai (deprecated)
# ---------------------------------------------------------------------------

_sdk: str = "none"  # "genai" | "legacy" | "none"

try:
    from google import genai as _genai_new
    from google.genai import types as _genai_types
    _sdk = "genai"
except ImportError:
    _genai_new = None
    _genai_types = None
    try:
        import google.generativeai as _genai_legacy
        _sdk = "legacy"
        logger.info("Using deprecated google-generativeai SDK. Consider upgrading to google-genai.")
    except ImportError:
        _genai_legacy = None
        logger.info("No Gemini SDK installed — Gemini providers disabled.")

# ---------------------------------------------------------------------------
# Catalogo (📝 escolhas de 25/09/2026 — modelos conferidos nas docs de cada provedor)
# ---------------------------------------------------------------------------

# Gemini: ordem = maior vazao gratuita primeiro, qualidade depois, Gemma por ultimo (cota grande).
# gemini-3.5-flash-lite: since 2026-09-22. The API answered 404 "gemini-2.5-flash-lite is no longer
#   available to new users" for a key created that day (institutional project) and suggested this
#   model; verified with a real call. Free-tier limits NOT re-verified.
# History (limits measured when chosen, Mar/2026 — may be stale):
#   gemini-2.5-flash-lite: best free-tier throughput (15 RPM, 1000/day) — retired for new users
#     (kept in the list: older keys still get it; a 404 just parks it for 6 h)
#   gemini-2.5-flash: better quality but lower free-tier limits (10 RPM, 250/day)
# 25/09: 3.5-flash-lite, 3.5-flash, 3.6-flash, 3-flash-preview, 2.5-flash, 2.5-flash-lite e
#   gemma-4-31b-it responderam "ok" a uma chamada real; 3.1-flash-lite e 3.8-flash deram 503
#   (sobrecarga momentanea, nao ausencia).
GEMINI_MODELOS_PADRAO = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3-flash-preview",
    "gemma-4-31b-it",
]

# Servicos OpenAI-compativeis com camada gratuita. Limites nas docs em 25/09/2026:
#   groq:       gpt-oss-120b / qwen3.8-27b — 30 req/min, 1.000 req/dia, 8K tokens/min cada
#   cerebras:   gpt-oss-120b / qwen-3.8-27b — 5 req/min, 1M tokens/dia
#   openrouter: modelos ":free" — 20 req/min, 50 req/dia (1.000/dia com US$10 de creditos);
#               "openrouter/free" escolhe sozinho um modelo gratuito disponivel
# Verificados com chave real em 28/09/2026 (python -m llm_cadeia): groq, cerebras e openrouter respondem.
PRESETS: dict[str, dict] = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "segredo": "GROQ_API_KEY",
        "modelos": ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"],
    },
    "cerebras": {
        "base_url": "https://api.cerebras.ai/v1",
        "segredo": "CEREBRAS_API_KEY",
        "modelos": ["gpt-oss-120b", "qwen-3.8-27b"],
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "segredo": "OPENROUTER_API_KEY",
        "modelos": ["qwen/qwen3.8-27b:free", "google/gemma-4-31b-it:free", "openrouter/free"],
    },
}

# Cada servico aceita uma segunda chave (sufixo _2 no segredo, "-2" no nome), p.ex. outro login.
ORDEM_PADRAO = ["local", "gemini", "gemini-2", "groq", "groq-2", "cerebras", "cerebras-2",
                "openrouter", "openrouter-2"]

_ESPERA_MINUTO_S = 60.0
_ESPERA_404_S = 6 * 3600.0
_ESPERA_AUTH_S = 6 * 3600.0
_ESPERA_REDE_S = 5 * 60.0
_ESPERA_OUTRO_S = 5 * 60.0

# Tempo limite de cada chamada. Conexao curta: servidor inalcancavel (ex.: o local visto da
# nuvem) falha em 5 s. Resposta: o local e lento — medido 28/09 no checklist, 5.000 caracteres
# de normativo: 154 s com raciocinio, 54 s sem; o app antigo usava 300 s.
_TIMEOUT_CONEXAO_S = 5.0
_TIMEOUT_NUVEM_S = 120.0
_TIMEOUT_LOCAL_PADRAO_S = 300.0

# ---------------------------------------------------------------------------
# Leitura de configuracao
# ---------------------------------------------------------------------------


def _segredo(nome: str) -> str:
    """Read one setting: st.secrets > env var > "" (never raises)."""
    try:
        import streamlit as st
        return str(st.secrets.get(nome, os.environ.get(nome, "")) or "").strip()
    except Exception:
        return os.environ.get(nome, "").strip()


def _lista(valor: str) -> list[str]:
    return [v.strip() for v in valor.split(",") if v.strip()]


def _novo_provedor(nome: str, tipo: str, chave: str, modelos: list[str], base_url: str = "",
                   timeout: float = _TIMEOUT_NUVEM_S, sem_raciocinio: bool = False) -> dict:
    return {
        "nome": nome, "tipo": tipo, "chave": chave, "modelos": list(modelos),
        "base_url": base_url.rstrip("/"), "bloqueado_ate": 0.0, "modelo_bloqueado_ate": {},
        "cliente": None, "timeout": timeout, "sem_raciocinio": sem_raciocinio,
    }


def _timeout_local() -> float:
    """LLM_TIMEOUT_S (seconds, > 0) or the 300 s default."""
    try:
        valor = float(_segredo("LLM_TIMEOUT_S"))
    except ValueError:
        return _TIMEOUT_LOCAL_PADRAO_S
    return valor if valor > 0 else _TIMEOUT_LOCAL_PADRAO_S


def _ligado(nome: str) -> bool:
    return _segredo(nome).lower() in ("1", "true", "sim", "yes", "on")


def _montar_provedores() -> list[dict]:
    """Build the chain from secrets/env: LLM_SOMENTE (only those), else LLM_ORDEM (or default) order."""
    disponiveis: dict[str, dict] = {}

    base_url, modelos = _segredo("LLM_BASE_URL"), _lista(_segredo("LLM_MODEL"))
    if base_url and modelos:
        disponiveis["local"] = _novo_provedor(
            "local", "openai", _segredo("LLM_API_KEY"), modelos, base_url,
            timeout=_timeout_local(), sem_raciocinio=_ligado("LLM_DISABLE_THINKING"))

    if _sdk != "none":
        modelos_gemini = _lista(_segredo("GEMINI_MODELS")) or GEMINI_MODELOS_PADRAO
        for nome, segredo in (("gemini", "GEMINI_API_KEY"), ("gemini-2", "GEMINI_API_KEY_2")):
            chave = _segredo(segredo)
            if chave:
                disponiveis[nome] = _novo_provedor(nome, "gemini", chave, modelos_gemini)

    for nome, preset in PRESETS.items():
        modelos = _lista(_segredo(f"{nome.upper()}_MODELS")) or preset["modelos"]
        for sufixo_nome, sufixo_segredo in (("", ""), ("-2", "_2")):
            chave = _segredo(preset["segredo"] + sufixo_segredo)
            if chave:
                disponiveis[nome + sufixo_nome] = _novo_provedor(
                    nome + sufixo_nome, "openai", chave, modelos, preset["base_url"])

    somente = _lista(_segredo("LLM_SOMENTE"))
    if somente:   # para teste/comparacao de modelos: nenhum outro entra
        return [disponiveis[n] for n in somente if n in disponiveis]
    ordem = _lista(_segredo("LLM_ORDEM")) or list(ORDEM_PADRAO)
    ordem += [n for n in ORDEM_PADRAO if n not in ordem]   # nome esquecido na LLM_ORDEM ainda entra, no fim
    return [disponiveis[n] for n in ordem if n in disponiveis]


_provedores: list[dict] = _montar_provedores()


def recarregar() -> None:
    """Rebuild the chain from secrets/env (it is built at import). Also clears the waits."""
    global _provedores
    _provedores = _montar_provedores()

# ---------------------------------------------------------------------------
# Chave do usuario — por SESSAO, nunca global
#
# Streamlit serve varios usuarios no MESMO processo: uma chave digitada por um
# nao pode ir para _provedores (os outros usariam a cota dele). O app guarda o
# contexto no st.session_state e o instala a cada execucao do script com
# usar_contexto(); o ContextVar vale so para a thread daquela execucao.
# ---------------------------------------------------------------------------

_contexto_padrao: dict = {"usuario": None, "ultimo": None, "ao_responder": None}
_contexto: contextvars.ContextVar[dict] = contextvars.ContextVar("cadeia_llm", default=_contexto_padrao)


def provedor_do_usuario(tipo: str, chave: str, modelo: str = "", base_url: str = "") -> Optional[dict]:
    """Build the user's own provider. tipo: "gemini" | um preset | "openai" (exige base_url).

    Returns None when the input is incomplete. modelo vazio = modelos padrao do tipo.
    """
    chave = (chave or "").strip()
    modelos = _lista(modelo or "")
    if tipo == "gemini":
        if not chave or _sdk == "none":
            return None
        return _novo_provedor("usuario", "gemini", chave, modelos or GEMINI_MODELOS_PADRAO)
    if tipo in PRESETS:
        if not chave:
            return None
        return _novo_provedor("usuario", "openai", chave, modelos or PRESETS[tipo]["modelos"],
                              PRESETS[tipo]["base_url"])
    if tipo == "openai":   # "Outro": em geral um servidor proprio, lento como o local
        if not base_url.strip() or not modelos:
            return None
        return _novo_provedor("usuario", "openai", chave, modelos, base_url.strip(), timeout=_timeout_local())
    return None


def usar_contexto(contexto: Optional[dict]) -> None:
    """Install this session's context.

    {"usuario": provedor|None, "ultimo": str|None, "ao_responder": callable(origem)|None}.
    ao_responder is called after each successful answer (painel_llm uses it to refresh
    "Última resposta" in the same script run); its errors are swallowed.
    """
    _contexto.set(contexto if contexto is not None else _contexto_padrao)


def novo_contexto() -> dict:
    return {"usuario": None, "ultimo": None, "ao_responder": None}


def _cadeia_efetiva() -> list[dict]:
    usuario = _contexto.get().get("usuario")
    return ([usuario] if usuario else []) + _provedores


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


def disponivel() -> bool:
    """True if at least one provider is configured (says nothing about quota)."""
    return bool(_cadeia_efetiva())


def ultimo_usado() -> Optional[str]:
    """"provedor (modelo)" of this session's last successful answer."""
    return _contexto.get().get("ultimo")


def descrever() -> list[str]:
    """Chain status for the UI, in try order. Never includes keys."""
    agora = time.time()
    linhas = []
    for p in _cadeia_efetiva():
        if p["bloqueado_ate"] > agora:
            linhas.append(f"{p['nome']} — em espera")
            continue
        livres = [m for m in p["modelos"] if p["modelo_bloqueado_ate"].get(m, 0.0) <= agora]
        parados = len(p["modelos"]) - len(livres)
        sufixo = f" (+{parados} em espera)" if parados else ""
        linhas.append(f"{p['nome']} — {livres[0] if livres else 'todos em espera'}{sufixo}")
    return linhas


# ---------------------------------------------------------------------------
# Classificacao de erro -> quanto tempo esperar, e se para o modelo ou o provedor
# ---------------------------------------------------------------------------


def _meia_noite_pacifico(agora: float) -> float:
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("America/Los_Angeles")
        d = datetime.fromtimestamp(agora, tz)
        amanha = (d + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return amanha.timestamp()
    except Exception:
        return agora + 6 * 3600.0


def _classificar(e: Exception, agora: float) -> tuple[str, float]:
    """Return (escopo, bloqueado_ate); escopo = "modelo" | "provedor"."""
    texto = str(e).upper()
    nome_tipo = type(e).__name__.upper()
    if "429" in texto or "RESOURCE_EXHAUSTED" in texto or "RATE LIMIT" in texto or "QUOTA" in texto:
        if re.search(r"PER ?DAY|PER-DAY|\bRPD\b|DAILY|PER_DAY", texto):
            return "modelo", _meia_noite_pacifico(agora)
        return "modelo", agora + _ESPERA_MINUTO_S
    if any(m in texto for m in ("401", "403", "API_KEY_INVALID", "PERMISSION_DENIED", "UNAUTHENTICATED",
                                "INVALID API KEY", "API KEY NOT VALID")):
        return "provedor", agora + _ESPERA_AUTH_S
    if "404" in texto or "NOT_FOUND" in texto:
        return "modelo", agora + _ESPERA_404_S
    if any(m in texto for m in ("503", "500", "502", "UNAVAILABLE", "OVERLOADED", "HIGH DEMAND")):
        return "modelo", agora + _ESPERA_MINUTO_S
    if "CONNECTION" in nome_tipo or "TIMEOUT" in nome_tipo or "CONNECTION" in texto or "TIMED OUT" in texto:
        return "provedor", agora + _ESPERA_REDE_S
    return "modelo", agora + _ESPERA_OUTRO_S


def _sem_chave(texto: str, p: dict) -> str:
    """Belt and braces: never let a key reach a log line."""
    return texto.replace(p["chave"], "***") if p.get("chave") else texto


# ---------------------------------------------------------------------------
# Transportes
# ---------------------------------------------------------------------------

_PENSAMENTO = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_CERCA = re.compile(r"^\s*```[a-zA-Z]*\s*\n?(.*?)\n?```\s*$", re.DOTALL)


def _limpar(texto: str, json_: bool) -> Optional[str]:
    """Drop reasoning blocks; with json_, drop a ```json fence around the whole answer."""
    texto = _PENSAMENTO.sub("", texto or "").strip()
    if json_:
        m = _CERCA.match(texto)
        if m:
            texto = m.group(1).strip()
    return texto or None


def _pede_parametros_de_raciocinio(texto: str) -> bool:
    """True for the OpenAI 400s of reasoning models: "Use 'max_completion_tokens' instead" /
    "'temperature' does not support 0.0 with this model"."""
    texto = (texto or "").lower()
    return "max_completion_tokens" in texto or ("temperature" in texto and "unsupported" in texto)


def _gerar_openai(p: dict, modelo: str, prompt: str, sistema: Optional[str], json_: bool,
                  temperature: float, max_tokens: int) -> Optional[str]:
    """One call to an OpenAI-compatible /chat/completions. Raises on failure.

    json_ does NOT send response_format: support varies by server (📝 suspected, not
    verified: LM Studio rejects {"type": "json_object"}). The prompt must ask for JSON;
    _limpar strips the fence. Verified 28/09/2026 with google/gemma-4 on the Nuati LM Studio:
    sistema= + JSON asked in the prompt -> json.loads OK.

    OpenAI reasoning models (gpt-5*, o-series) answer 400 to "max_tokens" (they want
    "max_completion_tokens") and to temperature != 1. On that 400 the call is repeated ONCE
    with max_completion_tokens and without temperature. ⚠ Built from the OpenAI error texts;
    covered by a mocked test, NOT verified live (no OpenAI key available on 28/09).

    p["sem_raciocinio"] (LLM_DISABLE_THINKING, local only) sends
    chat_template_kwargs={"enable_thinking": false} (Gemma/Qwen chat templates). A server that
    answers 400 naming that field gets the call again ONCE without it (mocked test only).
    Verified live 29/09 with google/gemma-4 on the local server: field accepted, same prompt
    27.1 s -> 3.8 s.
    """
    import requests
    headers = {"Content-Type": "application/json"}
    if p["chave"]:
        headers["Authorization"] = f"Bearer {p['chave']}"
    mensagens = ([{"role": "system", "content": sistema}] if sistema else []) + \
        [{"role": "user", "content": prompt}]
    corpo = {
        "model": modelo,
        "messages": mensagens,
        "temperature": temperature,
        # modelos de raciocinio (gpt-oss, qwen) gastam tokens pensando antes da resposta
        "max_tokens": max(max_tokens, 4096),
    }
    if p.get("sem_raciocinio"):
        corpo["chat_template_kwargs"] = {"enable_thinking": False}

    def enviar():
        return requests.post(
            f"{p['base_url']}/chat/completions",
            headers=headers,
            json=corpo,
            # connect fast-fails an unreachable server; the read timeout is per provider
            timeout=(_TIMEOUT_CONEXAO_S, p.get("timeout", _TIMEOUT_NUVEM_S)),
        )

    resp = enviar()
    if resp.status_code == 400 and "chat_template_kwargs" in (resp.text or ""):
        corpo.pop("chat_template_kwargs", None)
        resp = enviar()
    if resp.status_code == 400 and _pede_parametros_de_raciocinio(resp.text):
        corpo["max_completion_tokens"] = corpo.pop("max_tokens")
        corpo.pop("temperature")
        resp = enviar()
    if resp.status_code >= 400:
        raise RuntimeError(f"{resp.status_code} {resp.text[:300]}")
    return _limpar(resp.json()["choices"][0]["message"].get("content") or "", json_)


def _gerar_gemini(p: dict, modelo: str, prompt: str, sistema: Optional[str], json_: bool,
                  temperature: float, max_tokens: int) -> Optional[str]:
    """One Gemini call with this provider's key. Raises on failure.

    max_output_tokens has a 4096 floor, like the OpenAI path: thinking models
    (gemini-2.5-flash, gemma-4) spend the budget thinking and return EMPTY text when
    it is small — measured 28/09: 16 tokens -> None, 512 -> "ok" (gemma-4-31b-it).

    Timeout p["timeout"] (120 s): without it, a call hung ~7.5 min in the checklist v2 (28/09).
    The genai SDK takes milliseconds; a timeout raises a *Timeout* error, which parks the
    provider 5 min like any network failure.
    """
    max_tokens = max(max_tokens, 4096)
    timeout_s = p.get("timeout", _TIMEOUT_NUVEM_S)
    extras = {}
    if sistema:
        extras["system_instruction"] = sistema
    if json_:
        extras["response_mime_type"] = "application/json"
    if _sdk == "genai":
        if p["cliente"] is None:
            p["cliente"] = _genai_new.Client(
                api_key=p["chave"], http_options=_genai_types.HttpOptions(timeout=int(timeout_s * 1000)))
        response = p["cliente"].models.generate_content(
            model=modelo,
            contents=prompt,
            config=_genai_types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                **extras,
            ),
        )
        return _limpar(response.text or "", json_)
    # Legacy SDK: configure() is global, so re-apply this provider's key per call
    _genai_legacy.configure(api_key=p["chave"])
    response = _genai_legacy.GenerativeModel(
        modelo, system_instruction=extras.get("system_instruction"),
    ).generate_content(
        prompt,
        generation_config=_genai_legacy.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            **({"response_mime_type": "application/json"} if json_ else {}),
        ),
        request_options={"timeout": timeout_s},
    )
    return _limpar(response.text or "", json_)


# ---------------------------------------------------------------------------
# Entrada principal
# ---------------------------------------------------------------------------


def _avisar(ctx: dict, origem: str) -> None:
    """Call the session's ao_responder hook, if any. Never raises (gerar's promise)."""
    gancho = ctx.get("ao_responder")
    if gancho is None:
        return
    try:
        gancho(origem)
    except Exception as e:
        logger.warning("llm_cadeia: ao_responder falhou: %s", str(e)[:200])


@dataclass
class Resposta:
    """Result of gerar(). Never contains a key.

    texto:      the answer, or None (all failed / none configured / empty answer)
    origem:     "provedor (modelo)" that answered, or None
    tentativas: "provedor/modelo: motivo" for each one skipped or failed in THIS call,
                in order — use it to build the app's error message
    """
    texto: Optional[str]
    origem: Optional[str]
    tentativas: list[str] = field(default_factory=list)


def gerar(prompt: str, sistema: Optional[str] = None, json: bool = False,
          temperatura: float = 0.0, max_tokens: int = 1024) -> Resposta:
    """Ask the first provider/model of the chain that answers. Never raises.

    An EMPTY answer returns Resposta(None, origem) without trying the next one: an
    empty answer is not an outage, and falling through would silently mix models.
    """
    ctx = _contexto.get()
    tentativas: list[str] = []
    try:
        for p in _cadeia_efetiva():
            agora = time.time()
            if p["bloqueado_ate"] > agora:
                tentativas.append(f"{p['nome']}: em espera")
                continue
            for modelo in p["modelos"]:
                if p["modelo_bloqueado_ate"].get(modelo, 0.0) > agora:
                    tentativas.append(f"{p['nome']}/{modelo}: em espera")
                    continue
                transporte = _gerar_openai if p["tipo"] == "openai" else _gerar_gemini
                try:
                    texto = transporte(p, modelo, prompt, sistema, json, temperatura, max_tokens)
                except Exception as e:
                    agora = time.time()
                    escopo, ate = _classificar(e, agora)
                    motivo = _sem_chave(str(e)[:200], p)
                    tentativas.append(f"{p['nome']}/{modelo}: {motivo[:120]}")
                    logger.warning("LLM %s/%s falhou (%s); %s em espera %ds.", p["nome"], modelo,
                                   motivo, escopo, int(ate - agora))
                    if escopo == "provedor":
                        p["bloqueado_ate"] = ate
                        break
                    p["modelo_bloqueado_ate"][modelo] = ate
                    continue
                origem = f"{p['nome']} ({modelo})"
                if texto:
                    ctx["ultimo"] = origem
                    _avisar(ctx, origem)
                return Resposta(texto, origem, tentativas)
    except Exception as e:   # promessa: gerar nunca levanta
        logger.error("llm_cadeia: erro inesperado: %s", str(e)[:200])
        tentativas.append(f"erro interno: {type(e).__name__}")
    return Resposta(None, None, tentativas)

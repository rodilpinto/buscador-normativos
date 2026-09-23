"""
Modelos de dados para o Levantamento de Normativos.

Define as dataclasses centrais usadas em todo o pipeline:
- NormativoResult: um normativo encontrado por qualquer fonte de busca.
- SearchConfig: parametros de configuracao de uma sessao de busca.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
import re


# ---------------------------------------------------------------------------
# Vocabulario fechado de honestidade (spec 2026-09-22 §3.1; plano v2 T1)
# ---------------------------------------------------------------------------

# Por que uma fonte NAO pode ser consultada. String (nao Enum) para caber na
# planilha e no JSON sem conversao. "" = nao se aplica (status ok/empty).
MOTIVOS: frozenset[str] = frozenset({
    "",
    "bloqueio_waf",          # HTTP 200 com pagina de desafio (Senado/LexML, medido em 22/09)
    "http_5xx",              # 5xx depois dos retries
    "http_4xx",              # 4xx que nao e 404 nem 429 (401, 403...) — sem retry
    "rate_limit",            # 429 / RatelimitException — esperar, nao "fonte caiu"
    "manutencao_503",        # 503 (o TCU tem janela diaria 20h-21h BRT; hipotese, ver detalhe)
    "timeout",               # requests.Timeout
    "conexao",               # requests.ConnectionError
    "resposta_ilegivel",     # HTTP 200, mas o corpo nao e o formato esperado
    "endpoint_inexistente",  # 404 em todos os URLs da cadeia
    "nao_consultada",        # a busca parou antes desta palavra-chave (limite de resultados/keywords)
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

_RE_SEGREDO = re.compile(r"(?i)(?<![A-Za-z0-9])(key|cx|api[_-]?key|token|access_token|secret|client_secret|password|sig(?:nature)?)=([^&\s]+)")
_RE_BEARER = re.compile(r"(?i)\bBearer\s+\S+")
_RE_CONTROLE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def redigir(texto: str, limite: int = 2000) -> str:
    """Torna um texto vindo de fora seguro para tela, log e planilha.

    Redige segredos em query string e Bearer (a mensagem do requests inclui a
    URL inteira: `?key=AIza...` ia para a aba de diagnostico), remove chars de
    controle (openpyxl levanta IllegalCharacterError), neutraliza formula
    (so '=': e o unico prefixo que o openpyxl trata como formula) e corta em
    `limite`. O limite e o TETO DE CELULA (2000), nao um tamanho de tela:
    com 300, a URL real do LexML (~230 chars) engolia o titulo do desafio e a
    cadeia de URLs — o fato central da frente nunca chegava a planilha
    (rodada 2, R2-B1). Quem precisa de texto curto corta na renderizacao.
    """
    texto = _RE_SEGREDO.sub(lambda m: f"{m.group(1)}=***", texto or "")
    texto = _RE_BEARER.sub("Bearer ***", texto)
    texto = _RE_CONTROLE.sub("", texto)
    if texto[:1] == "=":
        texto = "'" + texto
    if len(texto) > limite:
        # corta no MEIO, com marca: o comeco (fato) e o fim (URL, 'retry pulado')
        # sao o que importa; cortar o sufixo em silencio apagava exatamente os
        # appends que a T2/T5 fazem no detalhe (rodada 3)
        marca = f" […cortado {len(texto) - limite} chars…] "
        metade = (limite - len(marca)) // 2
        texto = texto[:metade] + marca + texto[-metade:]
    return texto


def rotulo_status(s: "KeywordStatus") -> str:
    """Rotulo humano de um KeywordStatus — UNICO lugar (planilha e tela usam).

    `nao_consultada` tem status="error" (vocabulario fechado), mas NAO e
    "indisponivel": a palavra-chave simplesmente nao foi enviada. Rotula-la de
    indisponivel fazia o caminho feliz (10 keywords, max_results atingido)
    parecer uma fonte caida (rodada 2, R2-B6).
    """
    if s.status == "error" and s.motivo == "nao_consultada":
        return "Não consultada"
    return {"ok": "OK", "empty": "Sem resultado", "error": "Indisponível"}.get(s.status, s.status)


@dataclass
class NormativoResult:
    """Representa um normativo ou ato encontrado durante a busca.

    O campo ``id`` e gerado automaticamente em ``__post_init__`` como o
    hash SHA-256 da concatenacao ``tipo|numero|data``.  Esse hash e usado
    para deduplicacao de resultados vindos de fontes diferentes.

    Attributes:
        id: SHA-256 hex digest de ``f"{tipo}|{numero}|{data}"``.
             Gerado automaticamente -- nao passar no construtor.
        nome: Nome completo do normativo.
              Ex: "Lei n. 13.709, de 14 de agosto de 2018 (LGPD)".
        tipo: Categoria do ato.  Valores esperados:
              "Lei", "Decreto", "Instrucao Normativa", "Portaria",
              "Acordao TCU", "Resolucao", "Framework/Padrao", "Outro".
        numero: Numero do ato (ex: "13.709").  String vazia se nao aplicavel.
        data: Data no formato DD/MM/AAAA, ou ``None`` se desconhecida.
        orgao_emissor: Orgao emissor.
              Ex: "Presidencia da Republica", "TCU", "ISACA".
        ementa: Resumo ou descricao do conteudo.
        link: URL para o documento original.
        categoria: Tema ou categoria atribuida. Default "Nao categorizado".
        situacao: Vigencia do normativo.
              "Vigente", "Revogado", "Nao identificado" (default) ou o valor
              literal da fonte (ex.: "OFICIALIZADO" do TCU).
        relevancia: Score de relevancia entre 0.0 e 1.0. Default 0.0.
        relevancia_origem: De onde veio ``relevancia``. Um de ORIGENS_RELEVANCIA.
              Default "padrao_fonte": os searchers atribuem uma constante e
              nenhuma avaliacao rodou ainda.
        source: Identificador da fonte de busca.
              "lexml", "tcu" ou "google".
        found_by: Palavra-chave que originou o resultado.
        raw_data: Resposta bruta da API de origem. Default ``{}``.
    """

    # Campos obrigatorios (sem default) --------------------------------
    nome: str
    tipo: str
    numero: str
    data: str | None
    orgao_emissor: str
    ementa: str
    link: str
    source: str
    found_by: str

    # Campos com default ------------------------------------------------
    id: str = field(default="", init=False)
    categoria: str = "Nao categorizado"
    situacao: str = "Nao identificado"
    relevancia: float = 0.0
    relevancia_origem: str = "padrao_fonte"
    raw_data: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Gera o ``id`` a partir de tipo, numero e data.

        Quando ``numero`` esta vazio (ex: resultados do Google para
        frameworks/padroes), inclui ``link`` no hash para evitar
        colisao de IDs entre resultados distintos.
        """
        if self.relevancia_origem not in ORIGENS_RELEVANCIA:
            raise ValueError(
                f"relevancia_origem={self.relevancia_origem!r} fora de "
                f"ORIGENS_RELEVANCIA {sorted(ORIGENS_RELEVANCIA)}"
            )
        if self.numero:
            raw = f"{self.tipo}|{self.numero}|{self.data}"
        else:
            raw = f"{self.tipo}|{self.link}|{self.data}"
        self.id = hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class KeywordStatus:
    """Status of a keyword search across a specific source.

    Tracks whether a keyword returned results, returned zero results
    (legitimately not found), or failed due to an API/network error.

    Attributes:
        keyword: The search term.
        source: Which searcher produced this status ("lexml", "tcu", "google").
        result_count: Number of results found (0 if not found or error).
        status: One of "ok", "empty", "error". "error" significa "a fonte
              NAO pode ser consultada" (bloqueio, 5xx, timeout, resposta
              ilegivel...); o rotulo humano vem de rotulo_status().
        error_message: Error description if status == "error", else empty.
              Passa por redigir() em toda atribuicao.
        retried: a palavra-chave foi REENVIADA a fonte depois do passe
              principal (LexML/Google); tentativas HTTP internas (o TCU faz
              3) NAO contam — ficam no detalhe; retry pulado NAO marca.
        motivo: Por que a fonte nao pode ser consultada. Um de MOTIVOS
              (string com valores fechados, nao Enum, para caber na planilha
              e no JSON sem conversao). "" = nao se aplica (ok/empty).
        detalhe: URL, HTTP status, content-type, primeiros 120 chars do
              corpo — o que um humano precisa para reproduzir com curl.
              Passa por redigir() em toda atribuicao (segredos redigidos).
        parcial: a coleta NAO terminou — paginacao interrompida (ok/empty)
              ou, no TCU, um endpoint caido com o outro vivo (error): "achei
              40, a fonte caiu na pagina 3" e diferente de "achei 40".
    """

    keyword: str
    source: str
    result_count: int = 0
    status: str = "ok"  # "ok" | "empty" | "error" (= fonte indisponivel; ver motivo)
    error_message: str = ""
    retried: bool = False
    motivo: str = ""
    detalhe: str = ""
    parcial: bool = False

    def __post_init__(self) -> None:
        if self.motivo not in MOTIVOS:
            raise ValueError(f"motivo={self.motivo!r} fora de MOTIVOS {sorted(MOTIVOS)}")

    def __setattr__(self, nome: str, valor) -> None:
        # Tudo que vem de fora passa por redigir() em TODA atribuicao — o
        # construtor (dataclass usa setattr) e as mutacoes dos retries
        # (`st.error_message = f"Retry failed: {erro}"`). So no __post_init__
        # deixava a porta dos fundos aberta (rodada 2, R2-H1).
        if nome in ("detalhe", "error_message"):
            valor = redigir(valor or "")
        object.__setattr__(self, nome, valor)


@dataclass
class SearchConfig:
    """Configuracao de uma sessao de busca.

    Attributes:
        topic: Descricao em linguagem natural do tema de pesquisa.
        keywords: Lista final de palavras-chave para busca.
        sources: Fontes selecionadas.  Default ``["lexml", "tcu", "google"]``.
        max_results_per_source: Limite de resultados por fonte. Default 50.
    """

    topic: str = ""
    keywords: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=lambda: ["lexml", "tcu", "google"])
    max_results_per_source: int = 50


def statuses_para_falha_total(source: str, keywords: list[str], exc: BaseException) -> list[KeywordStatus]:
    """Quando search() de uma fonte LEVANTA, a fonte nao pode sumir do relatorio.

    Antes, app.py engolia a excecao e nao gravava status nenhum: a fonte
    desaparecia da tela e da aba de diagnostico, e o Passo 4 dizia "nenhum
    normativo encontrado" (achado H2 da rodada adversarial de 22/09).
    """
    detalhe = f"{type(exc).__name__}: {exc}"
    alvo = keywords or ["(todas)"]
    return [
        KeywordStatus(keyword=k, source=source, result_count=0, status="error",
                      motivo="erro_interno", detalhe=detalhe, error_message=detalhe)
        for k in alvo
    ]

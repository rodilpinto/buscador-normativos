"""
LexML Brasil searcher using the SRU (Search/Retrieve via URL) API.

LexML is a federated portal of Brazilian legislation maintained by the
Federal Senate. It aggregates laws, decrees, normative instructions,
and other legal acts from all levels of government.

API documentation: https://www.lexml.gov.br/
SRU protocol: http://www.loc.gov/standards/sru/
"""

import logging
import re
import xml.etree.ElementTree as ET
from typing import Optional
from urllib.parse import urlencode

import requests

from models import KeywordStatus, NormativoResult, redigir
from searchers.base import BaseSearcher, FonteIndisponivel, ProgressCallback

logger = logging.getLogger(__name__)

# SRU endpoint URLs. The primary URL is tried first; if it answers 404, a WAF
# challenge or an HTML body, the fallbacks are used in order (see
# LexMLSearcher._fetch_sru; frente 2, 2026-09-23 — connection errors no longer
# fall back, they are declared as motivo="conexao"). A non-HTML body that does
# not parse as SRU fails in _parse_sru_response (resposta_ilegivel), WITHOUT
# fallback.
PRIMARY_SRU_URL = "https://www.lexml.gov.br/busca/SRU"
FALLBACK_SRU_URL = "https://www.lexml.gov.br/sru/SRU"
FALLBACK_SRU_URL_2 = "https://www.lexml.gov.br/srw/SRU"

# XML namespaces used in SRU responses
NAMESPACES = {
    "srw": "http://www.loc.gov/zing/srw/",
    "dc": "http://purl.org/dc/elements/1.1/",
}

# Regex to extract tipo, date, and number from LexML URN identifiers.
# URN format: urn:lex:br:ESFERA:TIPO:DATA;NUMERO
# The (?:[^:]*:)+ group matches the variable-length path segments
# between "br" and the tipo (e.g., "br:federal:", "br;sao.paulo:").
URN_PATTERN = re.compile(
    r"urn:lex:br(?:[^:]*:)+([^:]+):(\d{4}(?:-\d{2}-\d{2})?);?(\d*)"
)

# Map from URN tipo slug to display name
URN_TIPO_MAP = {
    "lei": "Lei",
    "lei.complementar": "Lei Complementar",
    "lei.ordinaria": "Lei Ordinária",
    "decreto": "Decreto",
    "decreto.lei": "Decreto-Lei",
    "instrucao.normativa": "Instrução Normativa",
    "portaria": "Portaria",
    "resolucao": "Resolução",
    "medida.provisoria": "Medida Provisória",
    "emenda.constitucional": "Emenda Constitucional",
    "portaria.normativa": "Portaria Normativa",
    "deliberacao": "Deliberação",
    "parecer": "Parecer",
    "sumula": "Súmula",
    "ato": "Ato",
}

# Records per SRU page request
RECORDS_PER_PAGE = 20

# HTTP timeout for SRU requests (seconds)
REQUEST_TIMEOUT = 15


class LexMLSearcher(BaseSearcher):
    """Search Brazilian legislation via the LexML SRU API."""

    RATE_LIMIT_DELAY = 1.0
    RATE_LIMIT_JITTER = 0.5
    SOURCE_ID = "lexml"

    def __init__(self):
        self._sru_url: Optional[str] = None  # Resolved after first request
        # URLs que ja falharam NESTA busca -> a causa. Limpo em search().
        # Antes, cada palavra-chave tentava a cadeia inteira de novo (3 URLs x N
        # palavras-chave: parte dos ~390s do test_searchers.py em 22/09).
        self._urls_mortos: dict[str, FonteIndisponivel] = {}
        self._keyword_atual: str = ""   # para o detalhe dizer de qual keyword e a causa cacheada
        # URL efetiva (com query) do ultimo corpo devolvido por _try_fetch: se o
        # parse falhar, o detalhe precisa dela para ser reproduzivel com curl
        # (review da T2, I1: 200 application/json virava resposta_ilegivel sem URL).
        self._ultima_url: str = ""

    def source_name(self) -> str:
        return "LexML Brasil"

    def search(
        self,
        keywords: list[str],
        max_results: int = 50,
        progress_callback: ProgressCallback = None,
    ) -> list[NormativoResult]:
        """Search LexML for each keyword independently and merge results.

        Each keyword generates a separate SRU query. Results are deduplicated
        by ID (hash of tipo|numero|data). If the same normativo is found by
        multiple keywords, the found_by field accumulates all matching keywords.

        Keywords that fail due to API errors are retried once after all other
        keywords have been processed. The keyword_statuses attribute is
        populated with per-keyword diagnostic information.

        Frente 2 (2026-09-23): a failure is DECLARED (status="error" + motivo +
        detalhe), never "sem resultado". When all 3 SRU URLs already failed in
        this search the retry is skipped (no request is made, so retried stays
        False and the detalhe says "retry pulado"). Keywords never sent because
        max_results was reached get motivo="nao_consultada". A later page that
        fails makes the status parcial=True, with page and motivo in detalhe.

        Args:
            keywords: Search terms to query against LexML.
            max_results: Maximum total results to return.
            progress_callback: Optional callback(current, total, message).

        Returns:
            Deduplicated list of NormativoResult objects.
        """
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
                # Merge into results_by_id, deduplicating by ID
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

        # Final progress callback
        if progress_callback:
            progress_callback(
                total_keywords, total_keywords,
                f"LexML: {len(results_by_id)} resultados encontrados"
            )

        logger.info(f"LexML: total {len(results_by_id)} resultados unicos")
        return list(results_by_id.values())

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

    def _search_keyword(
        self, keyword: str, max_results: int = 50
    ) -> list[NormativoResult]:
        """Search LexML for a single keyword with pagination.

        Args:
            keyword: Single search term.
            max_results: Maximum results for this keyword.

        Returns:
            List of NormativoResult objects (empty = the source answered and
            found nothing, or the keyword was empty after sanitization; errors
            raise FonteIndisponivel, never an empty list).

        Raises:
            FonteIndisponivel: se a primeira pagina falhar. Falha em pagina seguinte fica em self._erro_paginacao.
        """
        # Sanitize keyword to prevent CQL injection
        safe_kw = keyword.replace('"', '').replace('\\', '').strip()
        if not safe_kw:
            return []
        cql_query = (
            f'dc.description any "{safe_kw}" '
            f'OR dc.subject any "{safe_kw}" '
            f'OR dc.title any "{safe_kw}"'
        )

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
                try:
                    records, total_count = self._parse_sru_response(xml_text, keyword)
                except FonteIndisponivel as e:
                    # I1 (review da T2): o parse nao conhece a URL — anexa-a por ultimo
                    # (R2-B1) e segue para o except de fora (pagina 2 continua parcial).
                    # redigir() aqui porque FonteIndisponivel so redige no __init__.
                    e.detalhe = redigir(f"{e.detalhe} | GET {self._ultima_url}")
                    raise
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

    def _fetch_sru(self, params: dict) -> Optional[str]:
        """Send an SRU GET request, with fallback URL logic.

        On the first call, tries PRIMARY_SRU_URL. If it gets a 404, a WAF
        challenge or an HTML body, tries FALLBACK_SRU_URL, then
        FALLBACK_SRU_URL_2. A non-HTML body that does not parse as SRU is NOT
        a fallback case: it is returned and fails in _parse_sru_response.
        The working URL is cached in self._sru_url for subsequent calls. Timeout/connection/5xx/4xx are errors of THIS
        request, not of the URL: they propagate and do not skip to the next
        URL (frente 2, 2026-09-23 — before, a connection error also fell back).

        Args:
            params: SRU query parameters dict.

        Returns:
            Response body as string. Raises FonteIndisponivel when no URL works; failed URLs are cached in self._urls_mortos for this search.
        """
        # If we already know which URL works, use it directly
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

    def _try_fetch(self, url: str, params: dict) -> Optional[str]:
        """Attempt a single GET request to the given SRU URL.

        Retries once on connection error after a 3-second delay.

        Args:
            url: SRU endpoint URL.
            params: Query parameters.

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
            self._ultima_url = efetiva   # I1: para o detalhe de um parse que falhe
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

    def _parse_sru_response(
        self, xml_text: str, keyword: str
    ) -> tuple[list[NormativoResult], int]:
        """Parse an SRU XML response into NormativoResult objects.

        Args:
            xml_text: Raw XML response body.
            keyword: The keyword that produced this response (for found_by).

        Returns:
            Tuple of (list of NormativoResult, total number of records reported
            by the server). Raises FonteIndisponivel("resposta_ilegivel") on parse error.
        """
        try:
            root = ET.fromstring(xml_text.lstrip("\ufeff \t\r\n"))
        except ET.ParseError as e:
            # Antes devolvia ([], 0) — a linha que transformava bloqueio em
            # "sem resultado". Agora e falha declarada.
            raise FonteIndisponivel(
                "resposta_ilegivel", f"XML SRU nao parseia: {e}; corpo: {xml_text[:120]!r}"
            ) from e

        # Total records reported by the server
        total_el = root.find("srw:numberOfRecords", NAMESPACES)
        total_count = int(total_el.text) if total_el is not None and total_el.text else 0

        results: list[NormativoResult] = []
        records = root.findall("srw:records/srw:record", NAMESPACES)

        for record in records:
            record_data = record.find("srw:recordData", NAMESPACES)
            if record_data is None:
                continue

            result = self._parse_record(record_data, keyword)
            if result is not None:
                results.append(result)

        return results, total_count

    def _parse_record(
        self, record_data: ET.Element, keyword: str
    ) -> Optional[NormativoResult]:
        """Parse a single SRU record into a NormativoResult.

        Args:
            record_data: The <srw:recordData> XML element.
            keyword: The keyword that found this record.

        Returns:
            NormativoResult or None if the record cannot be parsed.
        """
        # Helper to extract text from a Dublin Core element.
        # Some records nest DC elements inside an additional wrapper;
        # search recursively to handle both cases.
        def dc_text(tag: str) -> str:
            # Try direct child first
            el = record_data.find(f"dc:{tag}", NAMESPACES)
            if el is None:
                # Try recursive search (for nested record formats)
                el = record_data.find(f".//dc:{tag}", NAMESPACES)
            return el.text.strip() if el is not None and el.text else ""

        title = dc_text("title")
        description = dc_text("description")
        date_raw = dc_text("date")
        creator = dc_text("creator")
        dc_type = dc_text("type")
        identifier = dc_text("identifier")

        # Parse URN to extract tipo, date, and number
        tipo = ""
        numero = ""
        urn_date = ""
        link = ""

        if identifier and identifier.startswith("urn:lex:"):
            link = f"https://www.lexml.gov.br/urn/{identifier}"

            match = URN_PATTERN.search(identifier)
            if match:
                tipo_slug = match.group(1)
                urn_date = match.group(2)
                numero = match.group(3)

                # Map tipo slug to display name
                tipo = URN_TIPO_MAP.get(
                    tipo_slug,
                    tipo_slug.replace(".", " ").title()
                )

        # Determine the best date: prefer URN date, then dc:date
        date_str: Optional[str] = None
        if urn_date:
            date_str = self._safe_date_format(urn_date)
        elif date_raw:
            date_str = self._safe_date_format(date_raw)

        # Build the nome (display name)
        nome = title if title else f"{tipo} n. {numero}" if tipo and numero else identifier

        try:
            return NormativoResult(
                nome=nome,
                tipo=tipo,
                numero=numero,
                data=date_str,
                orgao_emissor=creator,
                ementa=description,
                link=link,
                source="lexml",
                found_by=keyword,
                relevancia=0.5,
                raw_data={
                    "dc_title": title,
                    "dc_description": description,
                    "dc_date": date_raw,
                    "dc_creator": creator,
                    "dc_type": dc_type,
                    "dc_identifier": identifier,
                },
            )
        except Exception as e:
            logger.warning(f"LexML: failed to create NormativoResult: {e}")
            return None

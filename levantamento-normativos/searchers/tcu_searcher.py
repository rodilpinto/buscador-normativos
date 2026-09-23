"""
TCU (Tribunal de Contas da Uniao) searcher using the Open Data API.

Searches two endpoints:
1. Acordaos -- court decisions with binding/recommendatory effect
2. Atos normativos -- normative acts (instructions, resolutions, etc.)

API documentation: https://dados-abertos.apps.tcu.gov.br/
"""

import logging
import re
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import requests

from models import KeywordStatus, NormativoResult
from searchers.base import BaseSearcher, FonteIndisponivel, ProgressCallback

logger = logging.getLogger(__name__)

API_BASE_URL = "https://dados-abertos.apps.tcu.gov.br/api"
ACORDAOS_PATH = "/acordao/recupera-acordaos"
ATOS_PATH = "/atonormativo/recupera-atos-normativos"

# Pagination settings
PAGE_SIZE = 20
MAX_PAGES = 25  # Max 500 records per endpoint
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3


class TCUSearcher(BaseSearcher):
    """Search TCU acordaos and atos normativos."""

    RATE_LIMIT_DELAY = 1.5   # TCU API is more sensitive
    RATE_LIMIT_JITTER = 0.5
    SOURCE_ID = "tcu"

    def source_name(self) -> str:
        return "TCU Dados Abertos"

    def search(
        self,
        keywords: list[str],
        max_results: int = 50,
        progress_callback: ProgressCallback = None,
    ) -> list[NormativoResult]:
        """Search TCU for acordaos and atos normativos matching keywords.

        Fetches records from both endpoints, then filters client-side
        for keyword matches in the ementa field.  Tracks per-keyword
        diagnostics in ``self.keyword_statuses``.

        Um endpoint que falha na primeira pagina marca status="error" para toda
        palavra-chave (com result_count do endpoint que respondeu e parcial=True);
        paginacao interrompida marca parcial=True; palavra-chave pulada pelo cap
        marca nao_consultada.

        Args:
            keywords: Search terms.
            max_results: Maximum total results.
            progress_callback: Optional callback(current, total, message).

        Returns:
            Deduplicated list of NormativoResult objects.
        """
        # Total steps: 2 (one per endpoint)
        total_steps = 2
        results_by_id: dict[str, NormativoResult] = {}
        self.keyword_statuses: list[KeywordStatus] = []

        # --- Step 1: Acordaos ---
        if progress_callback:
            progress_callback(0, total_steps, "TCU: buscando acordaos")

        logger.info("TCU: fetching acordaos")
        acordao_items, acordao_erro, acordao_parcial = self._fetch_all_pages_safe(f"{API_BASE_URL}{ACORDAOS_PATH}")
        logger.info(f"TCU: {len(acordao_items)} acordaos fetched, filtering by keywords")

        # --- Step 2: Atos Normativos ---
        if progress_callback:
            progress_callback(1, total_steps, "TCU: buscando atos normativos")
        logger.info("TCU: fetching atos normativos")
        atos_items, atos_erro, atos_parcial = self._fetch_all_pages_safe(f"{API_BASE_URL}{ATOS_PATH}")
        logger.info(f"TCU: {len(atos_items)} atos normativos fetched, filtering by keywords")

        def _sem_sumario(item) -> bool:
            # R3-B1: olha o CAMPO (titulo esta sempre preenchido e nao diz nada), e e
            # DEFENSIVO — roda fora do try por keyword; item malformado conta como
            # "sem sumario" aqui e vira erro_interno la dentro, nunca derruba search()
            try:
                return not str(item.get("sumario") or item.get("ementa") or "").strip()
            except Exception:
                return True
        sem_sumario = sum(1 for i in acordao_items if _sem_sumario(i))

        def _resumo(nome, itens, erro, parcial, extra=""):
            if erro is not None and not itens:
                return f"{nome}: {erro.motivo} em {erro.detalhe}"
            if parcial:
                return f"{nome}: parcial ({len(itens)} itens{extra}; {erro.detalhe})"
            return f"{nome}: ok ({len(itens)} itens{extra})"

        # R2-H5/R3: acordaos recentes chegam SEM sumario — nesses so o titulo casa;
        # "ok (500 itens)" sugeriria 500 avaliados por texto
        detalhe = "; ".join([
            _resumo("Acórdãos", acordao_items, acordao_erro, acordao_parcial,
                    f", {sem_sumario} sem sumário — nesses só o título casa" if acordao_items else ""),
            _resumo("Atos", atos_items, atos_erro, atos_parcial),
        ])
        # Um endpoint que caiu na PRIMEIRA pagina torna a busca "error" mesmo que
        # o outro tenha respondido: o usuario precisa saber que metade da fonte
        # nao foi vista. Resultados do endpoint vivo continuam entrando — e por
        # isso a coleta e PARCIAL (R2).
        erro_primario = next((e for e, itens in ((acordao_erro, acordao_items), (atos_erro, atos_items))
                              if e is not None and not itens), None)
        parcial = acordao_parcial or atos_parcial or (erro_primario is not None and bool(acordao_items or atos_items))

        # Track per-keyword statuses
        for idx, keyword in enumerate(keywords):
            if len(results_by_id) >= max_results:
                for restante in keywords[idx:]:   # M4
                    self.keyword_statuses.append(KeywordStatus(
                        keyword=restante, source=self.SOURCE_ID, result_count=0, status="error", motivo="nao_consultada",
                        detalhe=f"busca parou em max_results={max_results} antes desta palavra-chave"))
                break
            kw_count = 0
            try:
                # Filter acordaos for this keyword
                for item in acordao_items:
                    if len(results_by_id) >= max_results:
                        break
                    if self._matches_keyword(self._texto_do_acordao(item), keyword):
                        result = self._map_acordao(item, keyword)
                        if result.id not in results_by_id:
                            results_by_id[result.id] = result
                            kw_count += 1
                # Filter atos for this keyword
                for item in atos_items:
                    if len(results_by_id) >= max_results:
                        break
                    if self._matches_keyword(item.get("ementa", ""), keyword):
                        result = self._map_ato_normativo(item, keyword)
                        if result.id not in results_by_id:
                            results_by_id[result.id] = result
                            kw_count += 1
            except Exception as e:   # H2: mapeamento que quebra nao derruba a fonte
                self.keyword_statuses.append(KeywordStatus(
                    keyword=keyword, source=self.SOURCE_ID, result_count=kw_count, status="error", motivo="erro_interno",
                    detalhe=f"{type(e).__name__}: {e}"[:200], error_message=f"{type(e).__name__}: {e}"[:200]))
                continue

            if erro_primario is not None:
                status, motivo = "error", erro_primario.motivo
            elif kw_count == 0:
                status, motivo = "empty", ""
            else:
                status, motivo = "ok", ""
            self.keyword_statuses.append(KeywordStatus(
                keyword=keyword, source=self.SOURCE_ID, result_count=kw_count, status=status, motivo=motivo,
                detalhe=detalhe,   # R3-H5: SEMPRE — "empty" com 500 acordaos sem sumario nao e "nao ha acordao"
                error_message=detalhe if status == "error" else "", parcial=parcial))

        # Final callback
        if progress_callback:
            progress_callback(
                total_steps, total_steps,
                f"TCU: {len(results_by_id)} resultados encontrados"
            )

        logger.info(f"TCU: total {len(results_by_id)} resultados unicos")
        return list(results_by_id.values())

    def _texto_do_acordao(self, item: dict) -> str:
        """Texto onde a palavra-chave e procurada. Ate a T4: `ementa` (que a API
        real nao devolve — ver tests/fixtures/tcu_acordaos_real.json)."""
        return item.get("ementa", "") or ""

    def _matches_keyword(self, text: str, keyword: str) -> bool:
        """Check if keyword appears in text, accent/case insensitive."""
        return self._normalize_text(keyword) in self._normalize_text(text)

    def _fetch_all_pages(self, url: str) -> tuple[list[dict], Optional[FonteIndisponivel], bool]:
        """Fetch all pages from a paginated TCU API endpoint.

        Stops at MAX_PAGES * PAGE_SIZE records to avoid excessive requests.

        Args:
            url: Full endpoint URL.

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
                e.detalhe = f"pagina {page + 1} (inicio={offset}): {e.motivo}: {e.detalhe}"
                return all_items, e, True
            # The response may be a list directly or wrapped in an object.
            # Handle both cases.
            items = data if isinstance(data, list) else data.get("items", data.get("data", []))
            if not isinstance(items, list):
                erro = FonteIndisponivel("resposta_ilegivel", f"formato inesperado {type(data).__name__} | GET {url}?inicio={offset}")
                return all_items, erro, page > 0
            all_items.extend(items)
            # If we got fewer items than PAGE_SIZE, no more pages
            if len(items) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
            self._rate_limit()
        return all_items, None, False

    def _fetch_all_pages_safe(self, url: str) -> tuple[list[dict], Optional[FonteIndisponivel], bool]:
        """Como _fetch_all_pages, mas nenhuma excecao escapa: bug nosso vira
        erro_interno declarado, nunca "sem resultado"."""
        try:
            return self._fetch_all_pages(url)
        except Exception as e:
            logger.error(f"TCU: erro interno em {url}: {e}")
            return [], FonteIndisponivel("erro_interno", f"{type(e).__name__}: {e}"[:200]), False

    def _request_with_retry(self, url: str, params: dict) -> dict | list:
        """Send GET request with exponential backoff retry on 5xx/network.

        Args:
            url: Request URL.
            params: Query parameters.

        Returns:
            Parsed JSON (dict or list).

        Raises:
            FonteIndisponivel: com o motivo pela classe do erro (H6):
                503 -> manutencao_503 (sem retry; hora em BRT + hipotese da janela 20h-21h);
                404 -> endpoint_inexistente, 429 -> rate_limit, outro 4xx -> http_4xx (sem retry);
                5xx apos MAX_RETRIES -> http_5xx; timeout/conexao apos MAX_RETRIES;
                200 que nao e JSON -> bloqueio_waf (pagina de desafio) ou resposta_ilegivel.
            Antes devolvia None e o chamador tratava None como "fim das paginas":
            um 500 virava "sem resultado" (medido em 22/09). Detalhe: fato
            primeiro, URL (com query) por ultimo.
        """
        ultimo: Optional[Exception] = None
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            except requests.exceptions.Timeout as e:
                ultimo = e
            except requests.exceptions.ConnectionError as e:
                ultimo = e
            except requests.exceptions.RequestException as e:
                raise FonteIndisponivel("erro_interno", f"{type(e).__name__}: {str(e)[:120]} | GET {url}") from e
            else:
                efetiva = getattr(response, "url", None) or url
                sc = response.status_code
                if sc == 503:
                    agora = datetime.now(ZoneInfo("America/Sao_Paulo"))   # naive em servidor UTC erraria a janela (R2)
                    janela = "dentro" if 20 <= agora.hour < 21 else "fora"
                    raise FonteIndisponivel("manutencao_503",
                        f"HTTP 503 às {agora:%d/%m %H:%M} BRT ({janela} da janela de manutenção conhecida, 20h-21h); "
                        f"hipótese, não fato | GET {efetiva}")
                if sc == 404:
                    raise FonteIndisponivel("endpoint_inexistente", f"HTTP 404 | GET {efetiva}")
                if sc == 429:
                    raise FonteIndisponivel("rate_limit", f"HTTP 429 | GET {efetiva}")
                if 400 <= sc < 500:
                    raise FonteIndisponivel("http_4xx", f"HTTP {sc} | GET {efetiva}")
                if sc >= 500:
                    ultimo = requests.HTTPError(f"{sc}", response=response)
                else:
                    return self._exigir_json(response, efetiva)
            if attempt < MAX_RETRIES - 1:
                delay = 2 ** (attempt + 1)  # 2s, 4s, 8s
                logger.warning(f"TCU API error (attempt {attempt + 1}/{MAX_RETRIES}): {ultimo}. Retrying in {delay}s...")
                time.sleep(delay)
        logger.error(f"TCU API failed after {MAX_RETRIES} attempts: {ultimo}")
        if isinstance(ultimo, requests.exceptions.Timeout):   # ANTES de ConnectionError: ConnectTimeout herda dos dois
            raise FonteIndisponivel("timeout", f"sem resposta em {REQUEST_TIMEOUT}s x {MAX_RETRIES} | GET {url}?{urlencode(params)}")
        if isinstance(ultimo, requests.exceptions.ConnectionError):
            raise FonteIndisponivel("conexao", f"conexao recusada/sem rota ({str(ultimo)[:120]}) | GET {url}?{urlencode(params)}")
        resp = getattr(ultimo, "response", None)
        corpo = (getattr(resp, "text", "") or "")[:160]
        raise FonteIndisponivel("http_5xx",
            f"HTTP {getattr(resp, 'status_code', '?')} em {MAX_RETRIES} tentativas; corpo: {corpo!r} | GET {getattr(resp, 'url', url)}")

    def _exigir_json(self, response, url: str):
        """200 que nao e JSON e falha declarada, nao 'sem resultado' (H6)."""
        try:
            return response.json()
        except ValueError as e:   # requests.JSONDecodeError e ValueError
            corpo = (response.text or "").lstrip("\ufeff \t\r\n")
            ct = (response.headers.get("Content-Type") or "").lower()
            titulo = re.search(r"<title>([^<]*)</title>", corpo)
            fato = f"HTTP 200 {ct or 'sem content-type'} nao e JSON"
            if titulo:
                fato += f"; título: {titulo.group(1).strip()}"
            detalhe = f"{fato}; corpo: {corpo[:120]!r} | GET {url}"
            texto = corpo.lower()
            if "verificação de segurança" in texto or "verificacao de seguranca" in texto or "challenge" in texto:
                raise FonteIndisponivel("bloqueio_waf", detalhe) from e
            raise FonteIndisponivel("resposta_ilegivel", detalhe) from e

    def _map_acordao(self, item: dict, found_by: str) -> NormativoResult:
        """Map a raw acordao JSON item to a NormativoResult.

        Args:
            item: Raw API response item.
            found_by: Comma-separated keywords that matched.

        Returns:
            NormativoResult with tipo="Acordao TCU".
        """
        numero = str(item.get("numero", ""))
        ano = str(item.get("ano", ""))
        colegiado = item.get("colegiado", "")

        # Parse date from dataAta or dataSessao
        date_raw = item.get("dataAta") or item.get("dataSessao", "")
        date_str = self._safe_date_format(date_raw)

        return NormativoResult(
            nome=f"Acordao {numero}/{ano} - TCU - {colegiado}",
            tipo="Acordao TCU",
            numero=f"{numero}/{ano}",
            data=date_str,
            orgao_emissor=f"TCU - {colegiado}",
            ementa=item.get("ementa", ""),
            link=self._build_acordao_link(numero, ano),
            source="tcu",
            found_by=found_by,
            relevancia=0.5,
            raw_data=item,
        )

    def _map_ato_normativo(self, item: dict, found_by: str) -> NormativoResult:
        """Map a raw ato normativo JSON item to a NormativoResult.

        Args:
            item: Raw API response item.
            found_by: Comma-separated keywords that matched.

        Returns:
            NormativoResult with the tipo from the API response.
        """
        tipo = item.get("tipo", "Ato Normativo")
        numero = str(item.get("numero", ""))

        # Parse date
        date_raw = item.get("dataPublicacao") or item.get("data", "")
        date_str = self._safe_date_format(date_raw)

        # Link: use provided link/url, or empty
        link = item.get("link") or item.get("url", "")

        return NormativoResult(
            nome=f"{tipo} TCU n. {numero}",
            tipo=tipo,
            numero=numero,
            data=date_str,
            orgao_emissor="TCU",
            ementa=item.get("ementa", ""),
            link=link,
            source="tcu",
            found_by=found_by,
            relevancia=0.5,
            raw_data=item,
        )

    @staticmethod
    def _build_acordao_link(numero: str, ano: str) -> str:
        """Build the TCU search URL for a specific acordao.

        Args:
            numero: Acordao number.
            ano: Acordao year.

        Returns:
            URL to the TCU acordao search page.
        """
        return (
            f"https://pesquisa.apps.tcu.gov.br/documento/acordao-completo/"
            f"*/NUMACORDAO%253A{numero}%2520ANOACORDAO%253A{ano}"
        )

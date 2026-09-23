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
        for keyword matches: acordaos in sumario + titulo (_texto_do_acordao;
        esquema real da API, frente 2 T4), atos in ementa.  Tracks per-keyword
        diagnostics in ``self.keyword_statuses``.

        Um endpoint que falha na primeira pagina marca status="error" para toda
        palavra-chave (com result_count do endpoint que respondeu e parcial=True);
        paginacao interrompida marca parcial=True; palavra-chave pulada pelo cap
        marca nao_consultada.

        Revisao final (23/09): a keyword que so casa itens ja trazidos por outra
        sai ok (result_count = novos) e entra no found_by deles (F-N4); a keyword
        em curso cortada por max_results sai parcial=True (F-N5); o detalhe diz a
        janela de datas dos acordaos trazidos (F-UX3).

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
                    f", {sem_sumario} sem sumário — nesses só o título casa{self._janela_de_cobertura(acordao_items)}"
                    if acordao_items else ""),
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
            # F-N4 (revisao final, 23/09): casamentos e ids NOVOS sao contados em
            # separado. Antes so os novos contavam: a keyword 2 que casava um
            # acordao ja trazido pela 1 saia "empty" ("consultei e nao achei" —
            # falso) e o found_by nunca a acumulava. Agora e como o LexML:
            # status pelo casamento, result_count = novos, found_by acumula.
            kw_novos = 0      # ids que esta keyword acrescentou
            kw_repetidos = 0  # casaram, mas ja tinham vindo por keyword anterior
            cortado = False   # F-N5: parou em max_results com casamento novo sobrando
            ids_desta_kw: set[str] = set()
            try:
                # Filter acordaos (sumario + titulo) and then atos (ementa) for this
                # keyword — one list, same order as before, so the cap cuts in the same place
                candidatos = [(item, self._texto_do_acordao, self._map_acordao) for item in acordao_items]
                candidatos += [(item, lambda i: i.get("ementa", ""), self._map_ato_normativo) for item in atos_items]
                for item, texto_de, mapear in candidatos:
                    if not self._matches_keyword(texto_de(item), keyword):
                        continue
                    result = mapear(item, keyword)
                    if result.id in ids_desta_kw:
                        continue   # mesmo id duas vezes NESTA keyword: nao e "de palavra-chave anterior"
                    existente = results_by_id.get(result.id)
                    if existente is not None:
                        kw_repetidos += 1
                        self._acumular_found_by(existente, keyword)   # mesma regra do LexML (keyword inteira)
                        continue
                    if len(results_by_id) >= max_results:
                        # Antes: `break` silencioso e "ok N". Repetido nao ocupa
                        # vaga (acima), so um casamento NOVO sem lugar corta.
                        # Limite conhecido (review da FIX-FONTES, menor 5): depois
                        # deste break os itens seguintes nao sao olhados, entao um
                        # casamento REPETIDO que viesse depois nao acumula esta
                        # keyword no found_by — o status ja sai parcial e diz o corte.
                        cortado = True
                        break
                    results_by_id[result.id] = result
                    ids_desta_kw.add(result.id)
                    kw_novos += 1
            except Exception as e:   # H2: mapeamento que quebra nao derruba a fonte
                self.keyword_statuses.append(KeywordStatus(
                    keyword=keyword, source=self.SOURCE_ID, result_count=kw_novos, status="error", motivo="erro_interno",
                    detalhe=f"{type(e).__name__}: {e}"[:200], error_message=f"{type(e).__name__}: {e}"[:200]))
                continue

            if erro_primario is not None:
                status, motivo = "error", erro_primario.motivo
            elif kw_novos + kw_repetidos == 0:
                status, motivo = "empty", ""
            else:
                status, motivo = "ok", ""
            detalhe_kw = detalhe   # R3-H5: SEMPRE — "empty" com 500 acordaos sem sumario nao e "nao ha acordao"
            if kw_repetidos:
                detalhe_kw += (f"; {kw_repetidos} já trazido por palavra-chave anterior" if kw_repetidos == 1
                               else f"; {kw_repetidos} já trazidos por palavra-chave anterior")
            if cortado:
                detalhe_kw += f"; cortado em max_results={max_results}: havia mais itens que casam esta palavra-chave"
            self.keyword_statuses.append(KeywordStatus(
                keyword=keyword, source=self.SOURCE_ID, result_count=kw_novos, status=status, motivo=motivo,
                detalhe=detalhe_kw,
                error_message=detalhe_kw if status == "error" else "", parcial=parcial or cortado))

        # Final callback
        if progress_callback:
            progress_callback(
                total_steps, total_steps,
                f"TCU: {len(results_by_id)} resultados encontrados"
            )

        logger.info(f"TCU: total {len(results_by_id)} resultados unicos")
        return list(results_by_id.values())

    def _janela_de_cobertura(self, itens: list) -> str:
        """"; os N acórdãos mais recentes, de dd/mm/aaaa a dd/mm/aaaa" (com 1 item:
        "; o único acórdão trazido, de dd/mm/aaaa").

        Revisao final (ux 3, 23/09): a API nao filtra por palavra-chave, so
        pagina; com MAX_PAGES os 500 acordaos trazidos cobriam ~1 semana (todos
        de 16/09/2026) e "500 itens" nao dizia isso. As datas sao o min/max do
        `dataSessao` dos itens trazidos, como a API os escreve (so o formato e
        normalizado por _safe_date_format); item sem data legivel e contado a
        parte, nunca vira data inventada. "mais recentes" e a ordem em que a API
        devolve (medido em 22-23/09), nao um filtro nosso.
        """
        datas = []
        for item in itens:
            try:
                bruto = item.get("dataSessao") or item.get("dataAta") or ""
                datas.append(datetime.strptime(self._safe_date_format(str(bruto)), "%d/%m/%Y"))
            except Exception:   # defensivo como _sem_sumario: roda fora do try por keyword
                continue
        # Review da FIX-FONTES (menor 4): nada de "os 1 acórdãos mais recentes"
        if len(itens) == 1:
            return (f"; o único acórdão trazido, de {datas[0]:%d/%m/%Y}" if datas
                    else "; o único acórdão trazido não tem dataSessao legível")
        if not datas:
            return f"; nenhum dos {len(itens)} acórdãos tem dataSessao legível"
        sem_data = len(itens) - len(datas)
        janela = f"; os {len(itens)} acórdãos mais recentes, de {min(datas):%d/%m/%Y} a {max(datas):%d/%m/%Y}"
        return janela + (f" ({sem_data} sem dataSessao legível)" if sem_data else "")

    def _texto_do_acordao(self, item: dict) -> str:
        """Onde a palavra-chave e procurada: sumario + titulo (esquema real da
        API, medido em 22/09) — com fallback para `ementa` se a API tiver dois
        formatos. Antes lia so `ementa`, que a API nao devolve: zero match, sempre.
        Acordaos recentes vem SEM sumario (medido): so o titulo casa neles.
        Esquema real: tests/fixtures/tcu_acordaos_real.json e
        tests/fixtures/tcu_acordaos_colegiados_real.json."""
        return " ".join(x for x in (item.get("sumario"), item.get("titulo"), item.get("ementa")) if x)

    def _matches_keyword(self, text: str, keyword: str) -> bool:
        """Check if keyword appears in text, accent/case insensitive."""
        return self._normalize_text(keyword) in self._normalize_text(text)

    def _fetch_all_pages(self, url: str) -> tuple[list[dict], Optional[FonteIndisponivel], bool]:
        """Fetch all pages from a paginated TCU API endpoint.

        Stops after MAX_PAGES pages to avoid excessive requests. The API can
        send more than `quantidade` items per page (measured: 40 for 20), so
        the total may pass MAX_PAGES * PAGE_SIZE before dedup; items are
        deduplicated by `key` since frente 2 T3 (review I2).

        Args:
            url: Full endpoint URL.

        Returns:
            (itens, erro, parcial). Primeira pagina falhou -> ([], erro, False).
            Pagina seguinte falhou -> (o que veio, erro, True): "achei 40, a
            fonte caiu na pagina 3" e diferente de "achei 40". Antes, qualquer
            falha era `break` silencioso ("return what we have").
        """
        all_items: list[dict] = []
        vistas: set = set()   # keys ja acumuladas (I2 da review da T3)
        offset = 0
        for page in range(MAX_PAGES):
            params = {"inicio": offset, "quantidade": PAGE_SIZE}
            try:
                data = self._request_with_retry(url, params)
            except FonteIndisponivel as e:
                # Menor 1 (review da T3): devolve ao console o rastro que o 503/4xx
                # tinham antes; o detalhe ja vem redigido pela FonteIndisponivel
                logger.warning(f"TCU: {e}")
                if page == 0:
                    return [], e, False
                e.detalhe = f"pagina {page + 1} (inicio={offset}): {e.motivo}: {e.detalhe}"
                return all_items, e, True
            # The response may be a list directly or wrapped in an object.
            # Handle both cases.
            # I1 (review da T3): qualquer outra forma e falha declarada, nunca
            # "sem resultado" — um 200 com o corpo de erro do proprio TCU
            # ({"url": "Erro no servico", "erro": ...}) passava como lista vazia, e
            # um JSON null/str/numero dava AttributeError -> erro_interno que, na
            # pagina 2, jogava fora a pagina 1. Pagina >= 2 fica parcial.
            if not isinstance(data, (list, dict)) or (
                isinstance(data, dict) and "items" not in data and "data" not in data
            ):
                chaves = f" chaves={str(sorted(data))[:80]}" if isinstance(data, dict) else ""
                erro = FonteIndisponivel(
                    "resposta_ilegivel",
                    f"pagina {page + 1} (inicio={offset}): formato inesperado {type(data).__name__}{chaves}"
                    f" | GET {url}?inicio={offset}")
                logger.warning(f"TCU: {erro}")
                return all_items, erro, page > 0
            items = data if isinstance(data, list) else data.get("items", data.get("data", []))
            if not isinstance(items, list):
                erro = FonteIndisponivel("resposta_ilegivel", f"formato inesperado {type(data).__name__} | GET {url}?inicio={offset}")
                return all_items, erro, page > 0
            # I2 (review da T3): a API as vezes devolve 40 itens para quantidade=20,
            # repetindo os da pagina anterior (medido: 580 itens, 500 keys unicas) —
            # sem isto o "ok (N itens, M sem sumario)" do detalhe mostrava um N
            # inflado e variavel. Item sem `key` (ou com key nao escalar) entra sempre.
            for item in items:
                key = item.get("key") if isinstance(item, dict) else None
                if isinstance(key, (str, int)):   # key nao-hashable nao pode virar TypeError
                    if key in vistas:
                        continue
                    vistas.add(key)
                all_items.append(item)
            # If we got fewer items than PAGE_SIZE, no more pages
            # (conta a pagina CRUA: duplicata nao encurta a pagina)
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
                    dentro = 20 <= agora.hour < 21
                    # Revisao final (manut., perda parcial): o log antigo dizia "Tente
                    # novamente mais tarde." — o conselho volta, so quando cabe
                    conselho = "; tente de novo após 21h BRT" if dentro else ""
                    raise FonteIndisponivel("manutencao_503",
                        f"HTTP 503 às {agora:%d/%m %H:%M} BRT ({'dentro' if dentro else 'fora'} da janela de manutenção "
                        f"conhecida, 20h-21h); hipótese, não fato{conselho} | GET {efetiva}")
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
        """Map a raw acordao JSON item (esquema real de 22/09) to a NormativoResult.

        Campos literais da API, sem parafrase: titulo -> nome, sumario -> ementa,
        numeroAcordao/anoAcordao/colegiado -> numero, dataSessao -> data,
        urlAcordao -> link, situacao -> situacao. Chaves antigas
        (numero/ano/ementa) aceitas como fallback.

        numero = "N/AAAA-TCU-<colegiado literal>" quando ha colegiado (forma da
        citacao do TCU, "Acordao 1.765/2023-TCU-Plenario", com o colegiado como a
        API o escreve). Motivo (tester da T4, 23/09): Plenario, 1a e 2a Camara
        numeram em series PROPRIAS e se reunem no mesmo dia — com "N/AAAA" o id
        (tipo|numero|data) colidia (3.200 keys ao vivo -> 2.988 ids) e search()
        descartava o 2o em silencio; o dedup (tipo, numero) fundiria ate os de
        datas diferentes (so 2.025 pares numero/ano distintos). Medido nas 3.200:
        (numero, ano, colegiado) e unico por key. Sem colegiado: "N/AAAA" e
        orgao_emissor "TCU".

        Esquema real capturado: tests/fixtures/tcu_acordaos_real.json (22/09) e
        tests/fixtures/tcu_acordaos_colegiados_real.json (o par 4318/2026 1a x 2a
        Camara, 23/09).

        Args:
            item: Raw API response item.
            found_by: Comma-separated keywords that matched.

        Returns:
            NormativoResult with tipo="Acordao TCU".
        """
        numero = str(item.get("numeroAcordao") or item.get("numero") or "")
        ano = str(item.get("anoAcordao") or item.get("ano") or "")
        # `or ""`: a API pode mandar colegiado null (review da T4, M5) — sem isto
        # o orgao_emissor saia "TCU - None"
        colegiado = item.get("colegiado") or ""
        date_raw = item.get("dataSessao") or item.get("dataAta") or ""   # precedencia invertida de proposito (API real)
        date_str = self._safe_date_format(str(date_raw)) if date_raw else ""  # "" e nao None: `data` entra no id
        return NormativoResult(
            nome=item.get("titulo") or f"Acordao {numero}/{ano} - TCU - {colegiado}",
            tipo="Acordao TCU",
            numero=f"{numero}/{ano}-TCU-{colegiado}" if colegiado else f"{numero}/{ano}",
            data=date_str,
            orgao_emissor=f"TCU - {colegiado}" if colegiado else "TCU",
            ementa=item.get("sumario") or item.get("ementa", "") or "",
            link=item.get("urlAcordao") or self._build_acordao_link(numero, ano),
            source="tcu",
            found_by=found_by,
            situacao=item.get("situacao") or "Nao identificado",
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

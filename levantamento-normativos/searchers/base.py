"""
Abstract base class for all normativo searchers.

Every search backend (LexML, TCU, Google) inherits from BaseSearcher
and implements search() and source_name(). Shared logic for rate
limiting and text normalization lives here.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging
import re
import time
import unicodedata
from random import random
from typing import Callable, Optional

# Type alias for the progress callback used across all searchers.
# Signature: callback(current_step: int, total_steps: int, message: str)
ProgressCallback = Optional[Callable[[int, int, str], None]]

logger = logging.getLogger(__name__)


class BaseSearcher(ABC):
    """Abstract base class for normativo search backends."""

    # Seconds to wait between consecutive API requests.
    # Subclasses may override for APIs with stricter limits.
    RATE_LIMIT_DELAY: float = 1.0

    # Maximum random jitter (seconds) added to the base delay.
    RATE_LIMIT_JITTER: float = 0.5

    # Identificador curto da fonte — o `source` de todo KeywordStatus e o que
    # app.py usa quando search() levanta. Cada subclasse define o seu (T2/T3/T5).
    # Antes, app.py mapeava por nome de exibicao com fallback "google", e uma
    # fonte nova que levantasse viraria "web aberta" (rodada 2).
    SOURCE_ID: str = ""

    @abstractmethod
    def search(
        self,
        keywords: list[str],
        max_results: int = 50,
        progress_callback: ProgressCallback = None,
    ) -> list:
        """Search for normativos matching the given keywords.

        Args:
            keywords: List of search terms (e.g. ["governanca de TI", "COBIT"]).
                      Each keyword is searched independently and results are merged.
            max_results: Maximum total results to return across all keywords.
            progress_callback: Optional callback invoked after each keyword is
                               processed. Signature: callback(current, total, message).
                               - current: 0-based step index
                               - total: total number of steps
                               - message: human-readable status string

        Returns:
            List of NormativoResult objects, deduplicated by id.

        Raises:
            No exceptions should propagate. All API/network errors are caught
            internally, logged, and the searcher returns partial results.
        """
        ...

    @abstractmethod
    def source_name(self) -> str:
        """Return a human-readable name for this search source.

        Used in UI labels (e.g. "LexML Brasil", "TCU Dados Abertos", "Google").
        """
        ...

    def _rate_limit(self) -> None:
        """Sleep to respect API rate limits.

        Adds random jitter to the base delay to avoid thundering-herd
        patterns when multiple searchers run concurrently.
        """
        delay = self.RATE_LIMIT_DELAY + random() * self.RATE_LIMIT_JITTER
        logger.debug(f"Rate limit: sleeping {delay:.2f}s")
        time.sleep(delay)

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for comparison.

        Applies: strip, lowercase, remove diacritics (accents),
        collapse multiple whitespace into single space.

        Used for deduplication and keyword matching where accent-insensitive
        comparison is needed.

        Args:
            text: Raw text string.

        Returns:
            Normalized string suitable for comparison.
        """
        if not text:
            return ""
        text = text.strip().lower()
        # Decompose Unicode characters, then remove combining marks (accents)
        nfd = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def _safe_date_format(date_str: str) -> str:
        """Attempt to parse a date string and return DD/MM/YYYY format.

        Tries common formats: YYYY-MM-DD, YYYY, DD/MM/YYYY, DD-MM-YYYY.
        Returns the original string if no format matches.

        Args:
            date_str: Date string from an API response.

        Returns:
            Date in DD/MM/YYYY format, or the original string if unparseable.
        """
        if not date_str:
            return ""

        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip()[:19], fmt)
                return dt.strftime("%d/%m/%Y")
            except ValueError:
                continue

        # If only a year was provided
        if re.match(r"^\d{4}$", date_str.strip()):
            return f"01/01/{date_str.strip()}"

        return date_str


class FonteIndisponivel(Exception):
    """A fonte NAO pode ser consultada — distinto de "consultei e nao achei".

    Nasce no searcher (bloqueio, 5xx, timeout, corpo ilegivel) e sobe ate o
    KeywordStatus como status="error" + motivo + detalhe. Antes, um HTML de
    desafio com HTTP 200 virava lista vazia e a UI dizia "0 erros" (22/09).

    Um motivo desconhecido aqui vira erro_interno com o valor original no
    detalhe — barulho, nunca crash da fonte inteira (a validacao dura e a do
    KeywordStatus). O detalhe passa por models.redigir() JA AQUI, porque os
    searchers logam `str(e)` antes de qualquer KeywordStatus existir: sem isso
    a URL com a chave do CSE ia inteira para o log (rodada 2).
    """

    _CONHECIDOS = {
        "bloqueio_waf", "http_5xx", "http_4xx", "rate_limit", "manutencao_503", "timeout",
        "conexao", "resposta_ilegivel", "endpoint_inexistente", "nao_consultada", "erro_interno",
    }

    def __init__(self, motivo: str, detalhe: str = "") -> None:
        if motivo not in self._CONHECIDOS:
            detalhe = f"motivo desconhecido {motivo!r}: {detalhe}"
            motivo = "erro_interno"
        from models import redigir  # models nao importa searchers: sem ciclo
        super().__init__(motivo)
        self.motivo = motivo
        self.detalhe = redigir(detalhe)

    def __str__(self) -> str:  # dinamico: quem edita .detalhe depois nao deixa str() velho
        return f"{self.motivo}: {self.detalhe}" if self.detalhe else self.motivo

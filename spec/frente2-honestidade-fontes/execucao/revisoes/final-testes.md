# Revisão final · testes e gates, com mutação (qa-test-engineer, `d4cab80`, 23/09)

Gates rodados: runner **TUDO VERDE 296** (13/64/98/76/45 = `BASELINE`); golden OK.

## Mutação (cópia `git archive d4cab80`, uma mutação por vez) — **15/15 mortas pelo gate documentado**
redigir→identidade · troca "Não consultada"/"Indisponível" · `_exigir_sru` nunca acusa HTML · TCU engole erro da 1ª pág. ·
dedup por `key` removido · motivo `nao_consultada` trocado · `retried=True` no retry pulado (Google) · `parcial` sempre False
(TCU) · fallback rotulado "modelo" (morto pelo runner, que lê o `PASS/FAIL` impresso — o `test_llm_phase3.py` sozinho sai 0
mesmo falhando) · `_merge` sem a origem · `ORIGEM_LABEL` trocado · coluna `retried` fora da aba · `_md_html` = só
`html.escape` · regra R3-H4 invertida · `except` que coleta status desligado.

## Lacunas
- **Alto:** o golden (`entrada_fixa.json`, 14 `NormativoResult` à mão) **não passa pelos searchers** — não pega regressão do
  `numero` do TCU, do parse do Google/DDG nem de honestidade de searcher (as mutações 3-8 e 15 só morreram pelas suítes
  unitárias). → golden de resposta congelada: payload real capturado de TCU/LexML passando pelo parse real, com hash dos
  `KeywordStatus`/`NormativoResult`.
- **Alto:** `test_searchers.py` (13) e `test_comprehensive.py::test_lexml_cql_injection_sanitization` batem na rede real
  (já em P3): podem ficar vermelhos por fonte fora do ar, ou verdes sem testar o caso. → ao menos o CQL-injection dublado.
- Médio: V11 depende da fonte viva e dos textos literais; conta depois do dedup (D-C17) — é smoke visual, não gate de lógica.
- Baixo: a janela 20h-21h do 503 é afirmada por substrings estáveis — sem flakiness.

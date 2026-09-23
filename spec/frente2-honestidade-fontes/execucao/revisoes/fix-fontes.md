# FIX-FONTES — vereditos (worktree `../bn-fix-fontes`, branch `frente2/fix-fontes`, commits `66b7145` + `9fb4aeb`)

## Implementação (coder A) — 23/09
11 itens da triagem, cada um com teste visto falhando: F-N2, F-M2, F-N4, F-N5 (3 searchers), F-UX3, F-MT503, F-MT1 (fim de
`_CONHECIDOS`), F-MT3, F-SSRF (`allow_redirects=False` + revalidação por salto, ≤3 saltos, corpo ≤512 KiB), F-T1 (teste do
CQL dublado; provado por mutante), F-UX2 (`_keyword_relevance` com a mesma normalização do filtro). llm 65, fontes 60,
runner 312, golden OK. Desvios 📝: F-N2 só levanta se o diagnóstico vier SEM registros; F-N4 `result_count` = ids novos (0
possível, o detalhe explica) e `found_by` com o mesmo teste de substring do LexML; laços do Google unificados em `_coletar`;
"mais recentes" depende da ordem da API; resíduo de DNS-rebinding documentado.

## Testador (coder B) — ✅ APROVADO, sem bloqueador (23/09)
- Runner 312 TUDO VERDE; golden OK; CRLF; +704/−140 sem reescrita inteira; docs preservadas.
- Sondas: todas as alegações confirmadas; **SSRF sem bypass** (127.0.0.1, `[::1]`, 0.0.0.0, 2130706433, 0177.0.0.1, 0x7f.1,
  127.1, localhost, `LOCALHOST.`, IPv6-mapeado, 169.254.169.254, fe80::1, `//127.0.0.1`, `file://`; 4 saltos e laço param;
  corpo infinito cortado em 524.377 bytes); `_coletar` idêntico ao código antigo em 12 cenários.
- Ao vivo: TCU "os 500 acórdãos mais recentes, de 08/09/2026 a 22/09/2026", `found_by` = "turismo, monitoramento"; LexML
  `bloqueio_waf` com a cadeia e `retried=False`.
- E2E (8541): ⚠ 1ª execução chamou o Gemini de verdade (chaves no ambiente) — descartada; refeita com `env -u …`: 0 chamadas,
  30 resultados, janela do TCU no relatório, "LICITAÇÃO" → 50% (heurística). `fix-fontes-e2e-semllm2.png`.

**Menores:** (1) `google_searcher.py:300` keyword só com duplicatas conta como "0 resultados" na sequência do scraping
(pré-existente); (2) `lexml_searcher.py:390` marca corte mesmo quando o que sobrou são duplicatas (o texto segue verdadeiro);
(3) SSRF pré-existente não declarado: 100.64.0.0/10 e multicast passam como seguros; só o 1º endereço do `getaddrinfo` é
checado; (4) "os 1 acórdãos mais recentes" no singular.

## Reviewer — ✅ APROVADO, sem bloqueador (23/09)
Conferido: 60 passed em 0,75s com `env -u` (sem rede possível); `import llm` não carrega `searchers`; os 11 itens com teste
que fica vermelho sem o conserto; docs preservadas; BASELINE fecha. Desvios todos aceitos (`_coletar`, import tardio, MOTIVOS
lido na hora, F-N2 só sem registros, F-N4 ids novos).
- **Importante 1 — SSRF:** checar **todos** os endereços do `getaddrinfo` e bloquear `not is_global or is_multicast`
  (`100.64.0.1` não é global; `224.0.0.1` é "global" — por isso o `is_multicast`). Testes: [8.8.8.8, 127.0.0.1] bloqueado;
  100.64.0.1 bloqueado.
- **Importante 2 — `found_by` por substring** (`tcu:162`, `lexml:198,260`): "licita" nunca entra depois de "licitacao" →
  helper `BaseSearcher._acumular_found_by` comparando com `split(", ")`, nos 3 lugares; teste nos dois searchers.
- **Importante 3 — Google só duplicatas:** status `empty` e conta na sequência que dispara `bloqueio_waf` → `ok` quando houve
  repetidos; sequência conta `len(search_results) == 0`; teste no scraping.
- Menor 4 singular ("o único acórdão trazido, de dd/mm/aaaa") — corrigir. Menor 5 TCU depois do corte não acumula `found_by`
  — documentar. Menor 6 LexML:390 — aceito sem mudança.
- 📝 P3: mover `_normalize_text` para um módulo de texto leve (hoje `llm` depende de `searchers`).

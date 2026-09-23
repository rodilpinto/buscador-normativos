# FIX-FONTES · searchers, base e heurística dizem a verdade nos cantos que a revisão final achou — registro de implementação

> Origem: `../execucao/revisoes/final-triagem.md`, tabela **Trilha FIX-FONTES**. Os vereditos citados são
> `final-spec.md`, `final-seguranca.md`, `final-ux.md`, `final-manutencao.md` e `final-testes.md`.
> Worktree `bn-fix-fontes`, branch `frente2/fix-fontes` (criada de master `e024ec3`), 23/09/2026.
> Commits:
> - **`66b7145`** `fix(frente2): relevancia heuristica sem acento (revisao final, F-UX2)`
> - **`9fb4aeb`** `fix(frente2): searchers dizem a verdade nos cantos que a revisao final achou (FIX-FONTES)`
> - **`cb9e0b5`** `fix(frente2): review da FIX-FONTES — SSRF todos os enderecos, found_by exato, duplicatas do Google`
>
> Teste independente: **APROVADO**. Revisão de código: **APROVADO**, com 3 importantes e 2 menores, todos aplicados no
> terceiro commit (o menor 6 foi aceito sem mudança). Vereditos: `../execucao/revisoes/fix-fontes.md`.
> A trilha irmã FIX-SAÍDA (`app.py`/`excel_export.py`/`models.py`) não foi tocada. `models.MOTIVOS` não precisou mudar.

## 1. O que foi feito (item → arquivo/símbolo)

| id | arquivo · símbolo | o quê |
|---|---|---|
| F-N2 | `searchers/lexml_searcher.py` · `_parse_sru_response`, `_nome_local` (novo) | XML bem-formado cuja raiz não é `searchRetrieveResponse` → `resposta_ilegivel` ("raiz `<error>`; corpo: …"). `<srw:diagnostics>` **sem registro** → `resposta_ilegivel` com `uri=/message=/details=` literais da fonte. O `\| GET <url>` entra depois, em `_search_keyword` (I1 da T2). Comparação pelo nome local da tag (permissivo com prefixo/namespace, M10). SRU válido com 0 registros continua `empty` |
| F-M2 | `lexml_searcher.py` · `_fetch_sru`, `_matar_url` (novo), `_MOTIVOS_DO_URL` | WAF/HTML no `_sru_url` cacheado mata o URL (`_urls_mortos`) e tenta a cadeia. Antes o erro subia direto. `_matar_url` marca a causa com a keyword que a mediu no momento da morte: se o fallback responde, o `except` de `_search_keyword` não roda, e a causa ficava sem keyword |
| F-N4 | `searchers/tcu_searcher.py` · laço por keyword de `search` | Casamentos e ids novos contados em separado. Uma keyword que só casa acórdão já trazido sai `ok` com `result_count` = novos (convenção do LexML), entra no `found_by` e o detalhe diz "N já trazido(s) por palavra-chave anterior". O mesmo id duas vezes na mesma keyword não conta como "anterior" |
| F-N5 | LexML `_search_keyword` (`self._cortado`) + `_parcial_e_detalhe` (novo); TCU (`cortado`); Google `_coletar` (novo) | A keyword **em curso** que para em `max_results` com item novo sobrando → `parcial=True` e "cortado em max_results=N: …" (também no retry recuperado). As keywords seguintes seguem `nao_consultada`. Repetido não ocupa vaga nem corta |
| F-UX3 | `tcu_searcher.py` · `_janela_de_cobertura` (novo) | Detalhe dos acórdãos: "…; os N acórdãos mais recentes, de dd/mm/aaaa a dd/mm/aaaa" (min/max do `dataSessao` trazido). Item sem data legível é contado à parte; com 1 item, "o único acórdão trazido, de dd/mm/aaaa" (review) |
| F-UX2 | `llm/gemini_client.py` · `_keyword_relevance` | Sem acento e sem caixa, com `BaseSearcher._normalize_text` **importado** (o mesmo de `TCUSearcher._matches_keyword`). Import tardio: `import llm` não carrega `searchers` |
| F-SSRF | `searchers/google_searcher.py` · `_fetch_page_metadata`, `_ler_limitado` (novo), `MAX_PAGE_REDIRECTS=3`, `MAX_PAGE_BYTES=512 KiB`, `PAGE_READ_CHUNK`, `_REDIRECT_STATUS`; `_is_safe_url` (review) | Detalhado no item 1a abaixo |
| F-MT1 | `searchers/base.py` · `FonteIndisponivel.__init__` | Valida contra `models.MOTIVOS - {""}`, lido a cada construção. O `_CONHECIDOS` duplicado foi removido |
| F-MT3 | `google_searcher.py` · `search` (`zeros_seguidos`) | O `bloqueio_waf` inferido do scraping conta só **respostas** com `len(search_results) == 0` imediatamente seguidas. Erro, keyword longe na lista e keyword só com duplicatas interrompem ou não contam (a última é da review) |
| F-MT503 | `tcu_searcher.py` · `_request_with_retry` | 503 dentro da janela 20h-21h: o detalhe ganha "; tente de novo após 21h BRT", o conselho que o log antigo dava |
| F-T1 | `test_comprehensive.py` · `test_lexml_cql_injection_sanitization` | Sem rede: `requests.get` dublado; afirma a CQL **enviada** (sem aspas nem barra invertida) |
| review 2 | `base.py` · `BaseSearcher._acumular_found_by` (novo); usado em LexML (passada e retry), TCU e Google | `found_by` compara a keyword **inteira** (`split(",")` + `strip`), não substring: "licita" entrava nunca depois de "licitacao" |
| review 3 | `google_searcher.py` · `_coletar` → `(novos, cortado, repetidos)`, `_detalhe_coleta` (substitui `_detalhe_corte`) | Uma keyword cujos resultados já tinham vindo sai `ok`, acumula `found_by` na URL anterior e o detalhe diz quantos (como o TCU). Não alimenta mais a sequência de "zeros" do scraping |

### 1a. F-SSRF em detalhe

`_fetch_page_metadata`:
- Chama `requests.get(..., allow_redirects=False, stream=True)`.
- Cada `Location` é resolvido com `urljoin` contra a URL atual e revalidado por `_is_safe_url` antes de ser pedido, até 3 saltos.
- O corpo é lido em pedaços, cortado em 512 KiB, e a resposta é fechada.

`_is_safe_url` (review, importante 1):
- Checa **todos** os endereços do `getaddrinfo`.
- Bloqueia se `not is_global or is_multicast`. O IPv4 mapeado em IPv6 é julgado pelo IPv4.
- Endereço que não parseia é bloqueado.
- A lista antiga (private/loopback/link-local) deixava passar 100.64.0.0/10 e multicast. `224.0.0.1` é `is_global=True` no Python 3.13, por isso o `is_multicast`.

📝 Risco residual documentado no docstring: DNS rebinding entre o `getaddrinfo` da validação e o do `requests`. O conserto de verdade é um adapter que valide o IP conectado.

`BASELINE`:
- `test_llm_phase3.py`: 64 → **65** (`66b7145`).
- `tests/test_fontes_indisponiveis.py`: 45 → **60** (`9fb4aeb`) → **66** (review).
- Cada mudança tem um comentário com a conta por item.

## 2. Desvios e escolhas (📝 decisões minhas; o reviewer aceitou todas)

1. **F-N2:** o diagnóstico SRU só levanta quando vem **sem registros**. Com registros, eles ficam e o searcher loga um aviso. No SRU o diagnóstico pode ser não-fatal, e descartar resultados reais seria a mentira oposta.
2. **F-N4:** `result_count` = ids novos, então "ok 0" é possível; o detalhe explica. Na 1ª entrega o `found_by` usava a mesma substring do LexML; a review (importante 2) trocou pelo helper exato.
3. **Google:** as duas cópias do laço de coleta (passada e retry) viraram um `_coletar`, com os comentários levados junto. Não foi pedido; tira a deriva apontada em manut. 4. O testador comparou com o código antigo em 12 cenários: idêntico.
4. **F-UX3:** "mais recentes" é a ordem em que a API devolve (medido em 22-23/09), não um filtro nosso; o docstring diz isso. As datas só têm o formato normalizado.
5. **F-UX2:** o import de `BaseSearcher` fica dentro da função, para `import llm` não puxar ddgs/bs4/streamlit. 📝 P3 do reviewer: mover `_normalize_text` para um módulo de texto leve.
6. **F-N5 no TCU e no Google (review, menor 5):** depois do corte os itens seguintes não são olhados. Um casamento **repetido** posterior não acumula a keyword no `found_by`. Documentado em comentário; o status já sai parcial.
7. **Review 3:** a URL repetida acumula a keyword no `found_by` do resultado anterior. O reviewer pediu só o status/detalhe; acrescentei o `found_by` para o "ok" não afirmar um casamento que a planilha não mostra.
8. **Gate do runner:** o runner leva ~9,5 min e a ferramenta limita comando em primeiro plano a 10 min. Rodei o mesmo comando (`timeout 900 python -u tools/run_all_tests.py`) como job rastreado, esperando o exit code.

## 3. Evidência por item (teste visto falhando → passando)

Testes em `levantamento-normativos/tests/test_fontes_indisponiveis.py`, salvo indicação.

| id | teste | falha antes do conserto | depois |
|---|---|---|---|
| F-N2 | `test_lexml_xml_que_nao_e_searchRetrieveResponse_e_resposta_ilegivel` · `test_lexml_sru_com_diagnostics_e_resposta_ilegivel_com_a_mensagem` | `('empty', '') == ('error', 'resposta_ilegivel')` nos dois | passed |
| F-N2 (guarda) | `test_lexml_sru_valido_com_zero_registros_continua_empty` | passava antes, de propósito | passed |
| F-M2 | `test_lexml_waf_no_url_cacheado_mata_o_url_e_tenta_a_cadeia` | `['ok', 'error', 'error'] == ['ok', 'ok', 'ok']` | passed |
| F-N4 | `test_tcu_keyword_que_casa_acordao_ja_trazido_e_ok_e_acumula_found_by` | `'turismo' == 'turismo, monitoramento'` | passed |
| F-N5 | `test_{lexml,tcu,google}_keyword_cortada_por_max_results_e_parcial` | `('ok', False) == ('ok', True)` (Google: `('ok', 2, False)`) | passed |
| F-UX3 | `test_tcu_detalhe_diz_a_janela_de_cobertura_dos_acordaos` | texto da janela ausente | passed |
| F-MT503 | `test_tcu_503_dentro_da_janela_aconselha_tentar_depois_das_21h` (relógio dublado 20:30 / 15:30) | conselho ausente | passed |
| F-MT1 | `test_fonte_indisponivel_aceita_todo_motivo_de_models_motivos` | `'erro_interno' == 'motivo_novo'` | passed |
| F-MT3 | `test_google_scraping_bloqueio_conta_zeros_realmente_seguidos` | "c" marcado `bloqueio_waf` contando o erro de "b" | passed |
| F-SSRF | `test_fetch_metadata_nao_segue_redirect_para_metadados_nem_para_ip_privado` | a URL de metadados foi pedida | passed |
| F-SSRF | `test_fetch_metadata_segue_redirect_seguro_salto_a_salto_e_com_limite` | `('', '') == ('Guia', 'desc')` | passed |
| F-SSRF | `test_fetch_metadata_corta_corpo_grande` | `('', '') == ('Guia', 'desc')` | passed |
| F-T1 | `test_comprehensive.py::test_lexml_cql_injection_sanitization` | conserto de **teste**, provado por mutação (abaixo) | PASS |
| F-UX2 | `test_llm_phase3.py` record "Accent insensitive matching (both directions)" | `Total: 65 \| PASS: 64 \| FAIL: 1` | `Total: 65 \| PASS: 65` |
| review 1 | `test_is_safe_url_bloqueia_se_qualquer_endereco_resolvido_for_interno` | `assert True is False` ([8.8.8.8, 127.0.0.1] passava) | passed |
| review 1 | `test_is_safe_url_bloqueia_faixas_nao_globais_e_multicast` (100.64.0.1, 224.0.0.1, ::ffff:127.0.0.1, 0.0.0.0, fc00::1) | `AssertionError: 100.64.0.1` | passed |
| review 2 | `test_tcu_found_by_acumula_keyword_que_e_substring_de_outra` · `test_lexml_found_by_acumula_keyword_que_e_substring_de_outra` | `'licitacao' == 'licitacao, licita'` nos dois | passed |
| review 3 | `test_google_keyword_so_com_duplicatas_e_ok_e_nao_dispara_bloqueio` | b, c `empty` e d `bloqueio_waf` | passed |
| menor 4 | `test_tcu_janela_de_cobertura_no_singular` | "os 1 acórdãos mais recentes, de 16/09/2026 a 16/09/2026" | passed |

**F-T1 por mutação.** Script descartável no scratchpad roda só esse teste, com o `requests.get` real trocado por um que levanta "REDE REAL!":
- código atual: **PASS**;
- mutante sem a sanitização das aspas: **FAIL** (`dc.description any ""; DROP TABLE laws --" …`).

O teste antigo só afirmava `isinstance(results, list)` e passaria com esse mutante.

Os dublês de `requests.get` do F-SSRF imitam o `requests`: sem `allow_redirects=False`, o dublê segue o `Location` sozinho. Sem isso, o código antigo passaria no teste. O `getaddrinfo` também é dublado: nenhum teste faz rede.

## 4. Gates

**Coder A:**

| momento | runner (`timeout 900 python -u tools/run_all_tests.py`) | golden `comparar` | auditoria |
|---|---|---|---|
| `9fb4aeb` | **TUDO VERDE 312** = 13/65/98/76/60 | OK | removido lido inteiro; toda explicação com casa nova. O "Filter acordaos/atos" do TCU foi restaurado na lista única; os comentários do Google foram para `_coletar` |
| review `cb9e0b5` | **TUDO VERDE 318** = 13/65/98/76/66 | OK | o comentário manut. 3 foi fundido no novo; os docstrings mantêm a 1ª linha. Nenhuma assinatura auditada mudou (`_search_keyword_safe` segue com 3 posições; o corte vai em `self._cortado`) |
| merge com `origin/master` | feito DEPOIS deste commit de docs; runner e golden do merge vão no relatório ao orquestrador (e no `execucao/revisoes/fix-fontes.md`) | | |

Na 1ª rodada o runner deu verde com aviso "cresceu 45 → 60": o comentário do `BASELINE` tinha sido escrito sem trocar o número. Corrigido antes do commit; a rodada em `9fb4aeb` saiu sem aviso.

`dedup_esperado.json` e `tests/golden/*` **não mudaram**. CRLF conferido byte a byte em todo arquivo tocado.

**Testador (coder B), APROVADO:**
- Runner 312 TUDO VERDE, golden OK, CRLF, +704/−140 sem reescrita inteira, docs preservadas.
- SSRF sem bypass em 16 formas: 127.0.0.1, `[::1]`, 0.0.0.0, 2130706433, 0177.0.0.1, 0x7f.1, 127.1, localhost, `LOCALHOST.`, IPv6-mapeado, 169.254.169.254, fe80::1, `//127.0.0.1`, `file://`, 4 saltos e laço (param). Corpo infinito cortado em 524.377 bytes.
- `_coletar` idêntico ao código antigo em 12 cenários.

**Reviewer, APROVADO:** 60 passed em 0,75 s com `env -u` (sem rede possível); `import llm` não carrega `searchers`.

## 5. E2E (testador, porta 8541)

**Ao vivo:**
- TCU: "os 500 acórdãos mais recentes, de 08/09/2026 a 22/09/2026".
- `found_by` = "turismo, monitoramento".
- LexML: `bloqueio_waf` com a cadeia e `retried=False`.

⚠ **A 1ª execução do e2e foi DESCARTADA:** chamou o Gemini de verdade, porque as chaves estavam no ambiente do processo. Isso viola "nenhum LLM de verdade". Foi refeita com `env -u GEMINI_API_KEY -u GOOGLE_API_KEY`: 0 chamadas, 30 resultados, a janela do TCU no relatório, e "LICITAÇÃO" → 50% pela heurística (o F-UX2 visto na tela).

Print: `tests/evidencia/fix-fontes-e2e-semllm2.png` (não versionado). O e2e depois da review não foi refeito por mim. Os 3 importantes são cobertos por testes sem rede; a tela não mudou de forma.

## 6. Achados de teste/review e destino

| achado | origem | destino |
|---|---|---|
| SSRF: só o 1º endereço do `getaddrinfo`; 100.64/10 e multicast passavam | testador menor 3 + reviewer imp. 1 | **aplicado** (review) |
| `found_by` por substring (TCU e LexML) | reviewer imp. 2 (e desvio 2 da 1ª entrega) | **aplicado**: `BaseSearcher._acumular_found_by` nos 3 lugares + Google |
| Google: keyword só com duplicatas saía `empty` e contava na sequência do `bloqueio_waf` | testador menor 1 + reviewer imp. 3 | **aplicado** |
| "os 1 acórdãos mais recentes" | testador menor 4 + reviewer menor 4 | **aplicado** |
| TCU depois do corte não acumula `found_by` de repetido posterior | reviewer menor 5 | **documentado** em comentário (desvio 6) |
| LexML marca corte mesmo quando o que sobrou são duplicatas (texto segue verdadeiro: "a fonte tinha mais registros") | testador menor 2 / reviewer menor 6 | **aceito sem mudança** |
| `_normalize_text` num módulo de texto leve (hoje `llm` depende de `searchers`) | reviewer 📝 | **P3** |
| DNS rebinding | seg. + docstring | **P3** (risco residual documentado) |
| janela do TCU no cabeçalho e na planilha (ux 3 pede também lá) | ux 3 | **trilha FIX-SAÍDA / frente 4**: arquivos de outra trilha; o texto já está no `detalhe` do TCU |
| e2e com chaves no ambiente chamou o Gemini | testador | o e2e deve rodar com `env -u GEMINI_API_KEY -u GOOGLE_API_KEY` (o runner já zera; o `streamlit run` manual não) |

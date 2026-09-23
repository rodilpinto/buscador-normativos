> Material transversal extraído **verbatim** do plano (`docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md`, linhas 1-11 e
> 186-242). Citado pelo header de cada task. O plano segue fonte de verdade.

# Frente 2 — Honestidade das fontes — Implementation Plan (v4, pós 3 rodadas adversariais)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer o app dizer a verdade quando uma fonte não pôde ser consultada e de onde veio cada nota de relevância — na tela e na planilha — sem mudar como ele deduplica.

**Architecture:** Uma exceção tipada (`FonteIndisponivel`, com `motivo` e `detalhe`) nasce nos searchers e sobe até `KeywordStatus`, que ganha os mesmos campos mais `parcial`. A nota de relevância ganha um campo irmão `relevancia_origem`. A planilha ganha uma coluna e uma aba; a tela, rótulos honestos. Cada mudança é provada por teste sem rede (fixtures reais capturadas em 22/09, dublês de `requests.get`) e pelo golden-master, que passa a cobrir as duas abas.

**Tech Stack:** Python 3.13.7 · Streamlit 1.55 · requests 2.32 · openpyxl 3.1.5 · pytest 9 · ddgs 9.12 · Playwright (Python, `channel="chrome"`) só para o gate visual.

**Spec:** `docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md` (§3.x). **Esta v4 emenda a spec em 4 pontos**, listados na triagem abaixo e marcados `⚠ emenda à spec` no corpo.

---

## Global Constraints

- **Texto normativo NUNCA é parafraseado.** `nome`/`ementa` só recebem campos literais da API (T4 troca *qual* campo, não o texto).
- **O sistema roda inteiro sem LLM.** Todo teste novo roda com `GEMINI_API_KEY` vazia; nenhum teste novo faz rede.
- **Rastreabilidade:** `motivo` e `detalhe` bastam para reproduzir com `curl` (URL efetiva com query, status, content-type, hora quando relevante) — **com segredos redigidos**.
- **Separar fato de sugestão:** `📝` no que for proposta não validada.
- **UTF-8 explícito em todo `open()` / `read_text` / `write_text`.** `PYTHONIOENCODING=utf-8` em comando que imprime acento.
- **Rodar Python via Bash, não PowerShell.** Acima de 260 caracteres o Python falha em silêncio no Windows.
- **Documentação move junto com o código.** Gate ao fim de **cada** task, os dois comandos, lidos inteiros: `git diff -U0 HEAD~1 -- '*.py' | grep '^-' | grep -v '^---'` e `git grep -n -E 'score_relevance|_fetch_all_pages|_search_keyword_safe|_request_with_retry|_parse_sru_response|_search_urls|_render_search_diagnostics|generate_excel|_texto_do_acordao|_map_acordao|rotulo_status' -- '*.py'` (**sem `\b`** — ele não casa `score_relevance_com_origem`; inclui `tools/` porque `golden_master.py` documenta `generate_excel`; todo call site e docstring de símbolo cuja assinatura mudou, **antes** de escrever o step de adaptação; R2-B2, R3).
- **Golden-master:** `python tools/golden_master.py comparar` → OK ao fim de **toda** task, exceto a T8, que recongela **no mesmo commit** e diz por quê. `dedup_esperado.json` **nunca** muda nesta frente.
- **Runner:** `python tools/run_all_tests.py` TUDO VERDE ao fim de toda task (≈9 min hoje; deve cair com o cache de falha da T2 — anotar). Task que acrescenta teste atualiza `BASELINE` **no mesmo commit**. ⚠ **Os números "Expected" abaixo são previsões**: se o observado divergir, **parar e reconciliar** (um teste a mais/menos é sinal de step aplicado errado), nunca "ajustar o BASELINE ao que deu".
- **Sem LLM de verdade:** `tools/run_all_tests.py` roda as suítes com `env={**os.environ, "GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}` (T1 Step 6); a suíte nova tem `monkeypatch.delenv` autouse. ⚠ `st.secrets` **vence** a variável: se existir `levantamento-normativos/.streamlit/secrets.toml` (hoje só há o `.example`), o runner acha que roda sem LLM e não roda — dito no comentário do runner e no `LESSONS`; o conserto de código é da frente 5.
- **Push a cada task fechada** (D-C7).
- **Vocabulário fechado** em `models.py`: `MOTIVOS` e `ORIGENS_RELEVANCIA`. Nenhum outro arquivo inventa valor.
- **Diretório:** raiz do repo para `tools/`; `levantamento-normativos/` para `pytest` e os scripts de teste. Cada step diz qual.
- **Âncoras:** onde um step diz "de `:N` até `:M`", o **texto** citado é a âncora e o número é dica (linhas mudam); substituir sempre do começo da linha que contém o texto-âncora inicial até o fim da linha do texto-âncora final, **inclusive**.

---

## Estrutura de arquivos

| Arquivo | Responsabilidade nesta frente |
|---|---|
| `levantamento-normativos/models.py` | `MOTIVOS`, `ORIGENS_RELEVANCIA`, `redigir()`, `statuses_para_falha_total()`; campos novos em `KeywordStatus` e `NormativoResult` |
| `levantamento-normativos/searchers/base.py` | `FonteIndisponivel` |
| `levantamento-normativos/searchers/lexml_searcher.py` | sniff permissivo; `_try_fetch` levanta; cache de causa por URL; parcial; `nao_consultada`; retry que não rebaixa motivo |
| `levantamento-normativos/searchers/tcu_searcher.py` | `_request_with_retry` classifica por status e levanta; `_fetch_all_pages` → `(itens, erro, parcial)`; classificação por endpoint; **mapeamento do esquema real do acórdão** |
| `levantamento-normativos/searchers/google_searcher.py` | mapeamento mínimo ddgs/CSE → motivo; `nao_consultada` para keywords além de 5 |
| `levantamento-normativos/llm/gemini_client.py` · `llm/__init__.py` | `score_relevance_com_origem`; wrapper; docstrings |
| `levantamento-normativos/deduplicator.py` | `_merge` leva `relevancia_origem` (invariante) |
| `levantamento-normativos/excel_export.py` | coluna "Origem da nota"; aba "Diagnostico da busca"; `diagnostico=`, `quando=` |
| `levantamento-normativos/app.py` | pontuação sempre; relatório; avisos; card; preview; `statuses_para_falha_total`; `diagnostico=`/`quando=` |
| `levantamento-normativos/tests/test_fontes_indisponiveis.py` | **novo** — pytest, sem rede |
| `levantamento-normativos/tests/fixtures/lexml_desafio_senado.html` | ✅ capturado 22/09 (9.049 bytes, HTML real do desafio) |
| `levantamento-normativos/tests/fixtures/tcu_acordaos_real.json` | ✅ capturado 22/09 (2 acórdãos reais; chaves `numeroAcordao`, `anoAcordao`, `sumario`, `titulo`, `dataSessao`, `urlAcordao`…) |
| `levantamento-normativos/tests/fixtures/lexml_sru_valido.xml` | **novo** — SRU mínimo, 📝 escrito à mão (não há captura real: a fonte está bloqueada) |
| `levantamento-normativos/test_phase4.py` · `test_llm_phase3.py` · `test_comprehensive.py` | asserts adaptados; testes novos |
| `tools/run_all_tests.py` | suíte nova em `SUITES_PYTEST`; `BASELINE` por task |
| `tools/golden_master.py` | hash de **todas** as abas; `diagnostico_fixo.json` |
| `tests/golden/diagnostico_fixo.json` · `planilha_sha256.txt` · `ambiente.txt` | novo · recongelados na T8 |
| `tools/dirigir_app.py` · `tests/evidencia/` | gate visual V11 (PNG **não** versionado) |

**BASELINE previsto por task** (o runner avisa `cresceu`; o commit da task o atualiza):

| Após | `test_searchers` | `test_llm_phase3` | `test_comprehensive` | `test_phase4` | `tests/test_fontes_indisponiveis.py` | total |
|---|---|---|---|---|---|---|
| T1 | 13 | 53 | 98 | **58** | — | 222 |
| T2 | 13 | 53 | 98 | 58 | **16** | 238 |
| T3 | 13 | 53 | 98 | 58 | **25** (26 coletados, 1 xfail) | 247 |
| T4 | 13 | 53 | 98 | 58 | **29** | 251 |
| T5 | 13 | 53 | 98 | 58 | **37** | 259 |
| T6 | 13 | **63** | 98 | 58 | 37 | 269 |
| T7 | 13 | 63 | 98 | **61** | 37 | 272 |
| T8 | 13 | 63 | 98 | **71** | 37 | 282 |
| T9 | 13 | 63 | 98 | **72** (+1: `test_origem_curta_do_app…`) | 37 | 283 |

⚠ Contagens **recomputadas na v4** (a v3 contou um teste duas vezes na T4). **O observado manda**; se divergir, contar os testes do bloco da task **antes** de suspeitar do código — `grep -c '^def test_'` nas suítes pytest (`test_phase4.py`, `tests/…`); nas suítes-script (`test_llm_phase3.py` usa `record()`, sem `def test_`) o número esperado é o `Total:` que o step da task declara — e a regra "parar e reconciliar" vale para a diferença entre o bloco e o observado, não entre a tabela e o observado.

# Frente 2 — Honestidade das fontes — Implementation Plan (v2, pós-rodada adversarial)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer o app dizer a verdade quando uma fonte não pôde ser consultada e de onde veio cada nota de relevância — na tela e na planilha — sem mudar como ele deduplica.

**Architecture:** Uma exceção tipada (`FonteIndisponivel`, com `motivo` e `detalhe`) nasce nos searchers e sobe até `KeywordStatus`, que ganha os mesmos campos mais `parcial`. A nota de relevância ganha um campo irmão `relevancia_origem`. A planilha ganha uma coluna e uma aba; a tela, rótulos honestos. Cada mudança é provada por teste sem rede (fixtures reais capturadas em 22/09, dublês de `requests.get`) e pelo golden-master, que passa a cobrir as duas abas.

**Tech Stack:** Python 3.13.7 · Streamlit 1.55 · requests 2.32 · openpyxl 3.1.5 · pytest 9 · ddgs 9.12 · Playwright (Python, `channel="chrome"`) só para o gate visual.

**Spec:** `docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md` (§3.x). **Esta v2 emenda a spec em 4 pontos**, listados na triagem abaixo e marcados `⚠ emenda à spec` no corpo.

---

## Rodada 1 adversarial — triagem (2026-09-22)

5 lentes independentes (regressão · dados/API · risco · arquitetura · testes), **55 achados brutos, todos os 5 vereditos "não executável como está"**, a maioria provada aplicando a v1 do plano num clone e rodando os testes do próprio plano. **Esta v2 dobra as emendas aceitas no corpo** (não há seção separada de emendas a consultar). O registro abaixo é a trilha de auditoria: o que entrou, o que foi adaptado e o que foi rejeitado, com a razão.

### Bloqueadores convergentes (≥2 lentes, provados por execução) — todos ACEITOS

| # | Achado | Lentes | O que muda no plano |
|---|---|---|---|
| B1 | `_try_fetch` mantinha os `except ... return None`: timeout/conexão/5xx do LexML viravam `endpoint_inexistente`; o teste do próprio plano falhava | 1, 3, 4, 5 | T2: `_try_fetch` reescrito inteiro; só 404 devolve `None`; o resto **levanta** com o motivo certo. `_fetch_sru` só mata URL em 404 / bloqueio / ilegível — timeout e 5xx sobem sem matar o URL |
| B2 | Cache de falha + laço de retry **sobrescreviam `bloqueio_waf` por `endpoint_inexistente`** no cenário real de 22/09 (primário WAF, fallbacks 404) — o fato central da frente nunca chegava à tela | 2, 3, 4 | T2: cache guarda a **causa** por URL; esgotada a cadeia, relevanta a causa mais específica com detalhe agregado; retry **pula** cadeia morta (sem sleep) e nunca rebaixa motivo. Teste V2 vira o cenário misto |
| B3 | `test_comprehensive.py` perde 2 testes (LexML parse malformado; TCU mock de `_fetch_all_pages`) já na T2; o plano dizia "98 intactos" | 1, 3, 5 | T2 e T3 ganham step de **adaptação nomeada** das duas asserções, no mesmo commit; `test_comprehensive` entra nas listas de "rodar" |
| B4 | Step 5g deixava `error_msg` na linha 196 → `NameError` no retry; 6 de 7 testes crashavam | 2 | T2: o laço de retry é colado **inteiro**, literal |
| B5 | Fixture do TCU usava `numeroAcordao`/`anoAcordao`, chaves que `_map_acordao` não lê → 20 itens colapsam em 1. **E a lente 2 mediu por `curl` que o esquema REAL da API é esse** — não há `ementa`/`numero`/`ano`: **todo acórdão real colapsa e nunca casa palavra-chave** | 1, 2, 3, 4, 5 | ✅ confirmado por mim em 22/09 (`tests/fixtures/tcu_acordaos_real.json`). **T4 nova: mapear o esquema real** (`⚠ emenda à spec §3.7`). O teste de paginação usa a fixture real |
| B6 | openpyxl devolve `None` para célula `""` no round-trip; teste da aba falhava | 1, 2, 4, 5 | T8: célula vazia grava `"—"` de propósito (leitor sabe que o campo foi considerado); teste espera `"—"` |

### Altos — ACEITOS

| # | Achado | Lente | O que muda |
|---|---|---|---|
| H1 | Ramo `if self._sru_url` de `_fetch_sru` devolvia `None` num 404 tardio → `TypeError` → `erro_interno` com traceback no detalhe | 5 | T2: `None` no URL cacheado invalida o cache e cai na cadeia; teste `200 → 404` |
| H2 | `app.py` engole exceção do `search()` e a fonte **some** do relatório e da aba — a mentira que a frente quer matar | 3 | T1: `statuses_para_falha_total()` em `models.py` (testável sem Streamlit); T9 usa no `except`; T3 envolve o mapeamento de item |
| H3 | Aviso "nenhuma catalogada respondeu" disparava com acórdãos do TCU na tela (T3 marca `error` com `result_count>0`); o gate V11 **premiava** o bug | 3, 5 | T9: critério = soma de `result_count` das catalogadas; frase distinta para "respondeu parcialmente"; V11 checa a frase certa ao cenário |
| H4 | `error_message` do Google CSE carrega a URL com `key=`/`cx=` → chave na tela e, com a aba nova, na planilha | 3 | T1: `redigir()` em `models.py`, aplicada no `__post_init__` de `KeywordStatus` (segredos, chars de controle, prefixo `=` de fórmula, 300 chars) |
| H5 | `parcial` só existia no TCU; LexML com falha na página ≥2 seguia `ok` sem declarar | 3 | T2: `_search_keyword` registra o erro de paginação; `search()` grava `parcial=True` + detalhe; teste de 2 páginas |
| H6 | 4xx do TCU retentado 3× e rotulado `http_5xx`; 200 HTML → `JSONDecodeError` → `http_5xx`; 503 com causa afirmada como fato | 2, 3, 4 | T3: classificação por status (404 → `endpoint_inexistente`, 429 → `rate_limit`, outro 4xx → `http_4xx`, sem retry); JSON ilegível → sniff HTML → `bloqueio_waf`/`resposta_ilegivel`; 503 com hora e hipótese marcada (`⚠ emenda à spec §3.1`: `rate_limit`, `http_4xx`) |

### Médios/baixos — ACEITOS ou ADAPTADOS

| # | Achado | Verdict | O que muda |
|---|---|---|---|
| M1 | Retry-depois-sucesso sem teste; TCU timeout/conexão sem teste | aceito | T2/T3: testes acrescentados |
| M2 | `MOTIVOS` validado só no `KeywordStatus`: typo num searcher derruba a fonte inteira; `e.detalhe = ...` não atualiza `str(e)` | adaptado | T1: `FonteIndisponivel.__init__` mapeia motivo desconhecido → `erro_interno` (com o original no detalhe) em vez de levantar; `__str__` dinâmico; `KeywordStatus` continua validando (cinto) |
| M3 | `__init__` do LexML **já existe** em `:76-77`; a v1 tinha dois textos concorrentes | aceito | T2: "acrescentar 2 linhas mantendo o comentário" |
| M4 | Palavras-chave nunca consultadas (cap de `max_results`, `MAX_GOOGLE_KEYWORDS=5`) não geram status → lidas como "não existe" | adaptado | `⚠ emenda à spec §3.1`: motivo `nao_consultada` com `status="error"`; T2/T3/T5 gravam para cada keyword pulada |
| M5 | `google_searcher.py` fora do vocabulário: `DDGSException('No results')` vira `error`; nada tem `motivo` | adaptado | `⚠ emenda à spec §5`: **T5 nova, mínima** — mapear ddgs/CSE para `empty`/`timeout`/`rate_limit`/`http_4xx`/`erro_interno`; 4 testes com dublê |
| M6 | Aba de diagnóstico sem data/hora; detalhe sem query string | aceito | T8: `generate_excel(..., quando: str \| None)`; T2/T3: detalhe usa `response.url` (já redigido) |
| M7 | Golden-master lia só a aba ativa: a aba nova ficava sem proteção | aceito | T8: `_sha_planilha` hasheia **todas** as abas; `diagnostico_fixo.json` (3 statuses) ao lado de `entrada_fixa.json`; recongelar no mesmo commit |
| M8 | `_merge` com origem nunca é exercitado pelo app (dedup roda antes da pontuação); origem atribuída depois não passa pelo `__post_init__` | adaptado | T7 fica como **invariante declarado** na docstring; T9 valida a origem no ponto de atribuição. Inverter a ordem dedup/pontuação **rejeitado**: muda o dedup, exige task própria com golden |
| M9 | Docstring de módulo de `gemini_client.py:11` fica falsa; o gate de auditoria só vê linhas removidas | aceito | T6 edita a linha; gate de cada task ganha `git grep` dos símbolos renomeados |
| M10 | Sniff SRU estrito demais (BOM U+FEFF; prefixo `zs:`) — declararia "indisponível" um LexML que voltasse noutro formato | aceito | T2: sniff permissivo — só HTML explícito é bloqueio/ilegível; o resto o `ET` decide. `LESSONS`: falta captura real de SRU |
| M11 | `_urls_mortos` por instância nunca limpo; comentário prometia "nesta busca" | aceito | T2: `clear()` no início de `search()`; teste de reuso |
| M12 | T6 (agora T8) Step 2 previa "7 failed"; só 1 falha (os outros iteram `range(1, 11)` e passam por omissão) | aceito | corrigido |
| M13 | PNG do V11 em `tests/golden/`; docstring de `golden_master.py` cita assinatura velha; dicts de rótulo sem teste de sincronia; `RespostaFake.headers` dict simples; `detalhe` renderizado via Markdown | aceito | `tests/evidencia/` + `.gitignore`; T8 atualiza a docstring; asserts `set(ORIGEM_LABEL) == ORIGENS_RELEVANCIA` etc.; `CaseInsensitiveDict` no dublê; `st.code` para o detalhe |
| M14 | Sem LLM, ementa vazia → 0% onde antes 50%; ordem dos cards muda | aceito | T9: linha explicando "0% = nenhuma palavra-chave na ementa"; V11 confere que nenhum card sumiu |
| M15 | `diagnostico=[]` não testado separado de `None` | aceito | T8 |

### Rejeitados — com a razão

| Achado | Por quê |
|---|---|
| Pontuar antes de deduplicar para `_merge` valer de verdade (lente 5, opção b) | Muda o dedup e o golden; é task própria, fora desta frente. A origem está protegida pela atribuição pós-dedup (M8). |
| Retentar 503 uma vez (lente 3) | 503 é manutenção declarada; retentar só atrasa. Fica sem retry, com hora no detalhe. |
| Novo motivo `acesso_negado` para 401/403 (lente 3) | Coberto por `http_4xx` + detalhe com o status; vocabulário menor envelhece melhor. |
| Sanitizar `ementa`/`nome` na aba `Normativos` contra fórmula (lente 3) | Pré-existente, fora do escopo desta frente; registrado em `_TODO.md` P3. |

✅ **Verificado pela lente 4 e registrado para o executor não gastar tempo:** `python -m pytest tests/...` de dentro de `levantamento-normativos/` importa `searchers` sem `conftest`/`__init__` (cwd entra no `sys.path` via `-m`); `monkeypatch.setattr("searchers.lexml_searcher.requests.get")` patcha o módulo `requests` compartilhado (vale para TCU e Google); `"time.sleep"` global cobre o `import time` local de `_try_fetch`; `app.py:23` importa `gemini_client` como módulo; `searchers.base` não importa `models` (sem ciclo — `FonteIndisponivel` fica sem validar contra `MOTIVOS` por import; ver T1); searchers são instanciados por busca (`app.py:490-494`).

---

## Global Constraints

- **Texto normativo NUNCA é parafraseado.** `nome`/`ementa` só recebem campos literais da API (T4 troca *qual* campo, não o texto).
- **O sistema roda inteiro sem LLM.** Todo teste novo roda com `GEMINI_API_KEY` vazia; nenhum teste novo faz rede.
- **Rastreabilidade:** `motivo` e `detalhe` bastam para reproduzir com `curl` (URL efetiva com query, status, content-type, hora quando relevante) — **com segredos redigidos**.
- **Separar fato de sugestão:** `📝` no que for proposta não validada.
- **UTF-8 explícito em todo `open()` / `read_text` / `write_text`.** `PYTHONIOENCODING=utf-8` em comando que imprime acento.
- **Rodar Python via Bash, não PowerShell.** Acima de 260 caracteres o Python falha em silêncio no Windows.
- **Documentação move junto com o código.** Gate ao fim de **cada** task, os dois comandos, lidos inteiros: `git diff -U0 HEAD~1 -- '*.py' | grep '^-' | grep -v '^---'` e `git grep -n -E 'score_relevance\b|_fetch_all_pages\b|_search_keyword_safe\b|_request_with_retry\b|_parse_sru_response\b' -- '*.py'` (linhas de docstring que citam símbolo cuja assinatura mudou).
- **Golden-master:** `python tools/golden_master.py comparar` → OK ao fim de **toda** task, exceto a T8, que recongela **no mesmo commit** e diz por quê. `dedup_esperado.json` **nunca** muda nesta frente.
- **Runner:** `python tools/run_all_tests.py` TUDO VERDE ao fim de toda task (≈9 min hoje; deve cair com o cache de falha da T2 — anotar). Task que acrescenta teste atualiza `BASELINE` **no mesmo commit**. ⚠ **Os números "Expected" abaixo são previsões**: se o observado divergir, **parar e reconciliar** (um teste a mais/menos é sinal de step aplicado errado), nunca "ajustar o BASELINE ao que deu".
- **Push a cada task fechada** (D-C7).
- **Vocabulário fechado** em `models.py`: `MOTIVOS` e `ORIGENS_RELEVANCIA`. Nenhum outro arquivo inventa valor.
- **Diretório:** raiz do repo para `tools/`; `levantamento-normativos/` para `pytest` e os scripts de teste. Cada step diz qual.

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
| T1 | 13 | 53 | 98 | **56** | — | 220 |
| T2 | 13 | 53 | 98 | 56 | **13** | 233 |
| T3 | 13 | 53 | 98 | 56 | **20** (+1 xfail) | 240 |
| T4 | 13 | 53 | 98 | 56 | **24** | 244 |
| T5 | 13 | 53 | 98 | 56 | **28** | 248 |
| T6 | 13 | **63** | 98 | 56 | 28 | 258 |
| T7 | 13 | 63 | 98 | **59** | 28 | 261 |
| T8 | 13 | 63 | 98 | **67** | 28 | 269 |
| T9 | 13 | 63 | 98 | 67 | 28 | 269 |

---

### Task 1: Vocabulário, `redigir()`, `statuses_para_falha_total()`, `FonteIndisponivel`

**Files:**
- Modify: `levantamento-normativos/models.py` (topo; `NormativoResult:59-63` e `__post_init__:65-76`; `KeywordStatus:95-100`)
- Modify: `levantamento-normativos/searchers/base.py` (fim do arquivo)
- Test: `levantamento-normativos/test_phase4.py` (classes novas no fim)
- Modify: `tools/run_all_tests.py` (`BASELINE["test_phase4.py"]`)
- Modify: spec §3.1 (emenda dos motivos novos)

**Interfaces — Produces:**
- `MOTIVOS: frozenset[str]` = `{"", "bloqueio_waf", "http_5xx", "http_4xx", "rate_limit", "manutencao_503", "timeout", "conexao", "resposta_ilegivel", "endpoint_inexistente", "nao_consultada", "erro_interno"}`
- `ORIGENS_RELEVANCIA: frozenset[str]` = `{"modelo", "heuristica", "fallback_erro", "padrao_fonte"}`
- `redigir(texto: str, limite: int = 300) -> str` — redige `key=`/`cx=`/`api_key=`/`token=`/`apikey=` (valor → `***`), remove chars de controle (exceto `\n`, `\t`), prefixa `'` se começar com `=`, `+`, `-`, `@`, corta em `limite`.
- `KeywordStatus(..., motivo: str = "", detalhe: str = "", parcial: bool = False)`; `__post_init__`: `ValueError` se `motivo ∉ MOTIVOS`; **aplica `redigir` a `detalhe` e `error_message`**.
- `NormativoResult(..., relevancia_origem: str = "padrao_fonte")`; `__post_init__`: `ValueError` se fora de `ORIGENS_RELEVANCIA`.
- `statuses_para_falha_total(source: str, keywords: list[str], exc: BaseException) -> list[KeywordStatus]` — um `error`/`erro_interno` por keyword.
- `searchers.base.FonteIndisponivel(motivo, detalhe="")` — **não** valida contra `MOTIVOS` (evita ciclo de import); `str(e)` lê `self.motivo`/`self.detalhe` dinamicamente.

- [ ] **Step 1: Testes que falham** — ao fim de `levantamento-normativos/test_phase4.py`:

```python
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

    def test_normativo_origem_default_e_padrao_fonte(self):
        assert _make_result().relevancia_origem == "padrao_fonte"

    def test_normativo_rejeita_origem_inventada(self):
        with pytest.raises(ValueError, match="relevancia_origem"):
            NormativoResult(nome="x", tipo="Lei", numero="1", data=None, orgao_emissor="",
                            ementa="", link="", source="lexml", found_by="k",
                            relevancia_origem="ia")


class TestRedigir:
    def test_redige_segredos_em_query(self):
        assert redigir("u?key=ABC&cx=DEF&api_key=GHI&token=JKL&q=x") == "u?key=***&cx=***&api_key=***&token=***&q=x"

    def test_remove_controle_e_corta(self):
        assert redigir("a\x00b\x07c\n") == "abc\n"
        assert len(redigir("x" * 1000)) == 300

    def test_neutraliza_formula(self):
        assert redigir('=HYPERLINK("http://evil","clique")').startswith("'=")
        assert redigir("+1").startswith("'+") and redigir("-1").startswith("'-") and redigir("@x").startswith("'@")

    def test_texto_normal_intacto(self):
        assert redigir("GET https://x/y?q=lgpd -> 200 text/html") == "GET https://x/y?q=lgpd -> 200 text/html"


class TestStatusesParaFalhaTotal:
    def test_um_status_por_keyword(self):
        sts = statuses_para_falha_total("tcu", ["a", "b"], AttributeError("'int' object has no attribute 'strip'"))
        assert [s.keyword for s in sts] == ["a", "b"]
        assert all((s.source, s.status, s.motivo) == ("tcu", "error", "erro_interno") for s in sts)
        assert "AttributeError" in sts[0].detalhe and "strip" in sts[0].detalhe

    def test_lista_vazia_de_keywords_da_um_status_generico(self):
        sts = statuses_para_falha_total("lexml", [], RuntimeError("x"))
        assert len(sts) == 1 and sts[0].keyword == "(todas)"
```

- [ ] **Step 2: Rodar e ver falhar** — em `levantamento-normativos/`: `python -m pytest test_phase4.py -q` → `ImportError: cannot import name 'MOTIVOS'` na coleta.

- [ ] **Step 3: `models.py`** — logo após `from dataclasses import dataclass, field`, acrescentar `import re` e:

```python
# ---------------------------------------------------------------------------
# Vocabulario fechado de honestidade (spec 2026-09-22 §3.1; plano v2 T1)
# ---------------------------------------------------------------------------

# Por que uma fonte NAO pode ser consultada. String (nao Enum) para caber na
# planilha e no JSON sem conversao. "" = nao se aplica (status ok/empty).
MOTIVOS: frozenset[str] = frozenset({
    "",
    "bloqueio_waf",          # HTTP 200 com pagina de desafio (Senado/LexML, medido em 22/09)
    "http_5xx",              # 5xx depois dos retries
    "http_4xx",              # 4xx que nao e 404 nem 429 (401, 403...) — sem retry
    "rate_limit",            # 429 / RatelimitException — esperar, nao "fonte caiu"
    "manutencao_503",        # 503 (o TCU tem janela diaria 20h-21h BRT; hipotese, ver detalhe)
    "timeout",               # requests.Timeout
    "conexao",               # requests.ConnectionError
    "resposta_ilegivel",     # HTTP 200, mas o corpo nao e o formato esperado
    "endpoint_inexistente",  # 404 em todos os URLs da cadeia
    "nao_consultada",        # a busca parou antes desta palavra-chave (limite de resultados/keywords)
    "erro_interno",          # excecao nao prevista — bug nosso, nao da fonte
})

# De onde veio a nota de relevancia. Tres procedencias colapsavam no mesmo
# numero (0.5 podia ser modelo, fallback de erro ou default da fonte).
ORIGENS_RELEVANCIA: frozenset[str] = frozenset({
    "modelo",         # nota dada pelo LLM
    "heuristica",     # fracao das palavras-chave presentes na ementa (deterministica)
    "fallback_erro",  # o LLM falhou nesse lote; 0.5 rotulado como tal
    "padrao_fonte",   # constante que o searcher atribui; nenhuma avaliacao rodou
})

_RE_SEGREDO = re.compile(r"(?i)\b(key|cx|api_key|apikey|token)=([^&\s]+)")
_RE_CONTROLE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def redigir(texto: str, limite: int = 300) -> str:
    """Torna um texto vindo de fora seguro para tela e planilha.

    Redige segredos em query string (a mensagem do requests inclui a URL
    inteira: `?key=AIza...` ia para a aba de diagnostico), remove chars de
    controle (openpyxl levanta IllegalCharacterError), neutraliza formula
    (celula que comeca com '=' vira formula no Excel) e corta em `limite`.
    """
    texto = _RE_SEGREDO.sub(lambda m: f"{m.group(1)}=***", texto or "")
    texto = _RE_CONTROLE.sub("", texto)
    if texto[:1] in ("=", "+", "-", "@"):
        texto = "'" + texto
    return texto[:limite]
```

Em `NormativoResult`: docstring ganha (após `relevancia`):

```
        relevancia_origem: De onde veio ``relevancia``. Um de ORIGENS_RELEVANCIA.
              Default "padrao_fonte": os searchers atribuem uma constante e
              nenhuma avaliacao rodou ainda.
```

campo `relevancia_origem: str = "padrao_fonte"` após `relevancia: float = 0.0`; e no `__post_init__`, **antes** do hash:

```python
        if self.relevancia_origem not in ORIGENS_RELEVANCIA:
            raise ValueError(
                f"relevancia_origem={self.relevancia_origem!r} fora de "
                f"ORIGENS_RELEVANCIA {sorted(ORIGENS_RELEVANCIA)}"
            )
```

Em `KeywordStatus`: docstring ganha `motivo`, `detalhe`, `parcial` (texto da spec §3.1); a linha `status: str = "ok"  # "ok" | "empty" | "error"` vira `... | "error" (= fonte indisponivel; ver motivo)`; após `retried: bool = False`:

```python
    motivo: str = ""
    detalhe: str = ""
    parcial: bool = False

    def __post_init__(self) -> None:
        if self.motivo not in MOTIVOS:
            raise ValueError(f"motivo={self.motivo!r} fora de MOTIVOS {sorted(MOTIVOS)}")
        # Tudo que vem de fora passa por redigir(): e AQUI, no unico construtor,
        # que a tela e a planilha ficam protegidas de uma vez.
        self.detalhe = redigir(self.detalhe)
        self.error_message = redigir(self.error_message)
```

Ao fim de `models.py`:

```python
def statuses_para_falha_total(source: str, keywords: list[str], exc: BaseException) -> list[KeywordStatus]:
    """Quando search() de uma fonte LEVANTA, a fonte nao pode sumir do relatorio.

    Antes, app.py engolia a excecao e nao gravava status nenhum: a fonte
    desaparecia da tela e da aba de diagnostico, e o Passo 4 dizia "nenhum
    normativo encontrado" (achado H2 da rodada adversarial de 22/09).
    """
    detalhe = f"{type(exc).__name__}: {exc}"
    alvo = keywords or ["(todas)"]
    return [
        KeywordStatus(keyword=k, source=source, result_count=0, status="error",
                      motivo="erro_interno", detalhe=detalhe, error_message=detalhe)
        for k in alvo
    ]
```

- [ ] **Step 4: `searchers/base.py`** — ao fim:

```python
class FonteIndisponivel(Exception):
    """A fonte NAO pode ser consultada — distinto de "consultei e nao achei".

    Nasce no searcher (bloqueio, 5xx, timeout, corpo ilegivel) e sobe ate o
    KeywordStatus como status="error" + motivo + detalhe. Antes, um HTML de
    desafio com HTTP 200 virava lista vazia e a UI dizia "0 erros" (22/09).

    Nao valida `motivo` contra models.MOTIVOS (seria import circular); quem
    valida e o KeywordStatus. Um motivo desconhecido aqui vira erro_interno
    com o valor original no detalhe — barulho, nunca crash da fonte inteira.
    """

    _CONHECIDOS = {
        "bloqueio_waf", "http_5xx", "http_4xx", "rate_limit", "manutencao_503", "timeout",
        "conexao", "resposta_ilegivel", "endpoint_inexistente", "nao_consultada", "erro_interno",
    }

    def __init__(self, motivo: str, detalhe: str = "") -> None:
        if motivo not in self._CONHECIDOS:
            detalhe = f"motivo desconhecido {motivo!r}: {detalhe}"
            motivo = "erro_interno"
        super().__init__(motivo)
        self.motivo = motivo
        self.detalhe = detalhe

    def __str__(self) -> str:  # dinamico: quem edita .detalhe depois nao deixa str() velho
        return f"{self.motivo}: {self.detalhe}" if self.detalhe else self.motivo
```

Um teste em `test_phase4.py` (classe `TestVocabularioHonestidade`) para isso:

```python
    def test_fonte_indisponivel_motivo_desconhecido_vira_erro_interno_e_str_dinamico(self):
        from searchers.base import FonteIndisponivel
        e = FonteIndisponivel("http5xx", "GET x -> 500")
        assert (e.motivo, "http5xx" in e.detalhe) == ("erro_interno", True)
        e.detalhe = "novo"
        assert str(e) == "erro_interno: novo"
```

- [ ] **Step 5: Rodar e ver passar** — `python -m pytest test_phase4.py -q` → **`56 passed`** (41 + 15 novos: 9 em `TestVocabularioHonestidade`, 4 em `TestRedigir`, 2 em `TestStatusesParaFalhaTotal`). ⚠ Use o observado: se não for 56, algum step foi aplicado errado.

- [ ] **Step 6: BASELINE, golden, spec** — `BASELINE["test_phase4.py"] = 56`. `python tools/golden_master.py comparar` → OK. Spec §3.1: trocar a lista de `motivo` pela de `MOTIVOS` acima e acrescentar `> ⚠ Emendado em 22/09 (plano v2, T1): endpoint_inexistente, erro_interno, http_4xx, rate_limit, nao_consultada; redigir() aplicada no __post_init__.`

- [ ] **Step 7: Auditoria + commit**

```bash
git add levantamento-normativos/models.py levantamento-normativos/searchers/base.py levantamento-normativos/test_phase4.py tools/run_all_tests.py docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md
git commit -m "feat(frente2): vocabulario de honestidade, redigir() e FonteIndisponivel

MOTIVOS/ORIGENS_RELEVANCIA fechados; KeywordStatus ganha motivo/detalhe/
parcial e redige segredos/controle/formula no __post_init__ (a chave do
Google CSE ia para a planilha). statuses_para_falha_total() para a fonte
que levanta nao sumir do relatorio. FonteIndisponivel em searchers/base.
test_phase4: 41 -> 56."
git push origin master
```

---

### Task 2: LexML — sniff permissivo, falhas declaradas, cache de causa, parcial, `nao_consultada`

**Files:**
- Modify: `levantamento-normativos/searchers/lexml_searcher.py` — `:15-19` (imports), `:76-77` (`__init__`), `:106-118` (início de `search`, cap), `:124-137` (laço), `:157-212` (retry), `:228-241` (`_search_keyword_safe`), `:271-304` (`_search_keyword`), `:314-343` (`_fetch_sru`), `:345-382` (`_try_fetch`), `:393-397` (`_parse_sru_response`)
- Modify: `levantamento-normativos/test_comprehensive.py:362-367`
- Create: `levantamento-normativos/tests/test_fontes_indisponiveis.py`, `tests/fixtures/lexml_sru_valido.xml`
- Modify: `tools/run_all_tests.py`

**Interfaces — Produces:**
- `LexMLSearcher._search_keyword_safe(keyword, max_results) -> tuple[list[NormativoResult], Optional[FonteIndisponivel], Optional[FonteIndisponivel]]` = `(resultados, erro_fatal, erro_paginacao)`.
- `LexMLSearcher._urls_mortos: dict[str, FonteIndisponivel]` (limpo a cada `search()`).
- `LexMLSearcher._try_fetch(url, params) -> Optional[str]`: `None` **só** em 404; senão texto ou `FonteIndisponivel`.
- Convenção de dublê (todas as tasks de searcher): `monkeypatch.setattr("searchers.<mod>.requests.get", fake)`; `time.sleep` dublado pela fixture `autouse`.

- [ ] **Step 1: Fixture SRU** — `tests/fixtures/lexml_sru_valido.xml` (📝 escrito à mão; sem captura real porque a fonte está bloqueada):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <srw:version>1.1</srw:version>
  <srw:numberOfRecords>1</srw:numberOfRecords>
  <srw:records>
    <srw:record>
      <srw:recordData>
        <dc:title>Lei nº 14.133, de 1º de Abril de 2021</dc:title>
        <dc:description>Lei de Licitações e Contratos Administrativos.</dc:description>
        <dc:date>2021-04-01</dc:date>
        <dc:creator>Presidência da República</dc:creator>
        <dc:type>Lei</dc:type>
        <dc:identifier>urn:lex:br:federal:lei:2021-04-01;14133</dc:identifier>
      </srw:recordData>
    </srw:record>
  </srw:records>
</srw:searchRetrieveResponse>
```

- [ ] **Step 2: Testes que falham** — criar `tests/test_fontes_indisponiveis.py`:

```python
# -*- coding: utf-8 -*-
"""Frente 2 — fonte indisponivel != fonte sem resultado (spec 2026-09-22 §3.2/§3.3; plano v2).

Nenhum teste faz rede: requests.get e time.sleep sao dublados. As respostas
vem de fixtures — inclusive o HTML REAL do desafio do Senado e 2 acordaos
REAIS do TCU, capturados em 2026-09-22.

Rodar de dentro de levantamento-normativos/:
    python -m pytest tests/test_fontes_indisponiveis.py -q
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import requests
from requests.structures import CaseInsensitiveDict

FIXTURES = Path(__file__).parent / "fixtures"
DESAFIO_HTML = (FIXTURES / "lexml_desafio_senado.html").read_text(encoding="utf-8")
SRU_VALIDO = (FIXTURES / "lexml_sru_valido.xml").read_text(encoding="utf-8")


class RespostaFake:
    """O minimo de requests.Response que os searchers tocam."""

    def __init__(self, status: int, corpo: str = "", content_type: str = "application/xml",
                 json_data=None, url: str = "http://fake/?q=x"):
        self.status_code = status
        self.text = corpo
        self.headers = CaseInsensitiveDict({"content-type": content_type})
        self._json = json_data
        self.url = url

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error for url: {self.url}", response=self)

    def json(self):
        if self._json is None:
            raise requests.exceptions.JSONDecodeError("Expecting value", self.text, 0)
        return self._json


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)


# ---------------------------------------------------------------------------
# LexML
# ---------------------------------------------------------------------------

def _lexml_com(monkeypatch, responder):
    """responder(url, params) -> RespostaFake (ou levanta). Devolve (searcher, chamadas)."""
    from searchers import lexml_searcher

    chamadas: list[str] = []

    def fake_get(url, params=None, timeout=None, **kw):
        chamadas.append(url)
        return responder(url, params)

    monkeypatch.setattr("searchers.lexml_searcher.requests.get", fake_get)
    return lexml_searcher.LexMLSearcher(), chamadas


def _cenario_real_22_09(url, params):
    """O que o curl mediu em 22/09: primario = 200 HTML de desafio; fallbacks = 404."""
    if url.endswith("/busca/SRU"):
        return RespostaFake(200, DESAFIO_HTML, "text/html; charset=UTF-8", url=url + "?operation=searchRetrieve")
    return RespostaFake(404, "nao", "text/html", url=url)


def test_lexml_cenario_real_toda_keyword_e_bloqueio_waf_e_3_requisicoes(monkeypatch):
    """B2 da rodada adversarial: o retry e o cache NAO podem rebaixar bloqueio_waf."""
    s, chamadas = _lexml_com(monkeypatch, _cenario_real_22_09)
    assert s.search(["a", "b", "c"], max_results=5) == []
    assert len(chamadas) == 3 and len(set(chamadas)) == 3          # cada URL uma vez por busca
    assert [st.motivo for st in s.keyword_statuses] == ["bloqueio_waf"] * 3
    assert all("Verificação de segurança" in st.detalhe for st in s.keyword_statuses)
    assert all("text/html" in st.detalhe for st in s.keyword_statuses)
    assert all("404" in st.detalhe for st in s.keyword_statuses)   # detalhe agregado por URL
    assert s.keyword_statuses[0].retried is True                   # retentado sem rede, motivo mantido


def test_lexml_html_generico_e_resposta_ilegivel(monkeypatch):
    s, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(200, "<!DOCTYPE html><html><body>oi</body></html>", "text/html"))
    s.search(["x"], max_results=5)
    assert (s.keyword_statuses[0].status, s.keyword_statuses[0].motivo) == ("error", "resposta_ilegivel")


def test_lexml_xml_truncado_e_resposta_ilegivel(monkeypatch):
    s, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(200, SRU_VALIDO[:200], "application/xml"))
    s.search(["x"], max_results=5)
    assert s.keyword_statuses[0].motivo == "resposta_ilegivel"


def test_lexml_sru_valido_continua_ok_mesmo_com_bom_e_content_type_estranho(monkeypatch):
    """M10: o sniff nao pode reprovar SRU valido por BOM ou content-type."""
    s, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(200, "﻿" + SRU_VALIDO, "text/plain"))
    resultados = s.search(["x"], max_results=5)
    assert len(resultados) == 1 and resultados[0].numero == "14133"
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo, st.result_count, st.parcial) == ("ok", "", 1, False)


def test_lexml_404_em_toda_a_cadeia_e_endpoint_inexistente(monkeypatch):
    s, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(404, "nao", "text/html"))
    s.search(["x"], max_results=5)
    assert s.keyword_statuses[0].motivo == "endpoint_inexistente"


def test_lexml_timeout_conexao_e_5xx_mapeiam_motivo_e_nao_matam_o_url(monkeypatch):
    """B1: timeout/conexao/5xx sobem com o motivo certo; a keyword seguinte tenta o primario de novo."""
    from searchers import lexml_searcher
    vez = {"n": 0}

    def responder(u, p):
        vez["n"] += 1
        if vez["n"] == 1:
            raise requests.exceptions.Timeout("lento")
        return RespostaFake(200, SRU_VALIDO)

    s, chamadas = _lexml_com(monkeypatch, responder)
    s.search(["a", "b"], max_results=5)
    assert s.keyword_statuses[0].motivo == "timeout"
    assert "GET" in s.keyword_statuses[0].detalhe and "15" in s.keyword_statuses[0].detalhe  # REQUEST_TIMEOUT
    assert chamadas[0] == chamadas[-1] == lexml_searcher.PRIMARY_SRU_URL                  # nao foi para o fallback

    def cai(u, p):
        raise requests.exceptions.ConnectionError("sem rota")
    s2, _ = _lexml_com(monkeypatch, cai)
    s2.search(["x"], max_results=5)
    assert s2.keyword_statuses[0].motivo == "conexao"

    s3, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(500, "boom", "text/html"))
    s3.search(["x"], max_results=5)
    assert s3.keyword_statuses[0].motivo == "http_5xx" and "500" in s3.keyword_statuses[0].detalhe


def test_lexml_url_cacheado_que_passa_a_dar_404_nao_vira_erro_interno(monkeypatch):
    """H1: 200 na keyword 'a' cacheia o primario; 404 na 'b' tem de ser endpoint_inexistente, nao TypeError."""
    vez = {"n": 0}

    def responder(u, p):
        vez["n"] += 1
        return RespostaFake(200, SRU_VALIDO) if vez["n"] == 1 else RespostaFake(404, "", "text/html")

    s, _ = _lexml_com(monkeypatch, responder)
    s.search(["a", "b"], max_results=5)
    assert s.keyword_statuses[0].status == "ok"
    assert s.keyword_statuses[1].motivo == "endpoint_inexistente"
    assert "TypeError" not in s.keyword_statuses[1].detalhe


def test_lexml_retry_que_da_certo_zera_motivo_e_detalhe(monkeypatch):
    """M1: primeira tentativa 500, retry devolve SRU valido -> ok limpo."""
    vez = {"n": 0}

    def responder(u, p):
        vez["n"] += 1
        return RespostaFake(500, "x", "text/html") if vez["n"] == 1 else RespostaFake(200, SRU_VALIDO)

    s, _ = _lexml_com(monkeypatch, responder)
    s.search(["a"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo, st.detalhe, st.retried, st.result_count) == ("ok", "", "", True, 1)


def test_lexml_falha_na_segunda_pagina_e_ok_parcial(monkeypatch):
    """H5: pagina 1 diz 50 registros, pagina 2 devolve o desafio -> ok, parcial=True, detalhe diz a pagina."""
    vez = {"n": 0}
    pagina1 = SRU_VALIDO.replace("<srw:numberOfRecords>1</srw:numberOfRecords>", "<srw:numberOfRecords>50</srw:numberOfRecords>")

    def responder(u, p):
        vez["n"] += 1
        return RespostaFake(200, pagina1) if vez["n"] == 1 else RespostaFake(200, DESAFIO_HTML, "text/html")

    s, _ = _lexml_com(monkeypatch, responder)
    resultados = s.search(["a"], max_results=50)
    assert len(resultados) == 1
    st = s.keyword_statuses[0]
    assert (st.status, st.parcial) == ("ok", True)
    assert "startRecord" in st.detalhe and "bloqueio_waf" in st.detalhe


def test_lexml_keywords_nao_consultadas_por_cap_ganham_status(monkeypatch):
    """M4: max_results=1 atinge o cap na 1a keyword; 'b' e 'c' nao podem sumir do relatorio."""
    s, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(200, SRU_VALIDO))
    s.search(["a", "b", "c"], max_results=1)
    assert [st.status for st in s.keyword_statuses] == ["ok", "error", "error"]
    assert [st.motivo for st in s.keyword_statuses[1:]] == ["nao_consultada"] * 2
    assert "max_results=1" in s.keyword_statuses[1].detalhe


def test_lexml_cache_de_falha_e_limpo_a_cada_busca(monkeypatch):
    """M11: mesma instancia, busca 1 com 404 em tudo, busca 2 com 200 -> ok."""
    vez = {"busca": 1}
    s, _ = _lexml_com(monkeypatch, lambda u, p: RespostaFake(404, "", "text/html") if vez["busca"] == 1 else RespostaFake(200, SRU_VALIDO))
    s.search(["a"], max_results=5)
    assert s.keyword_statuses[0].motivo == "endpoint_inexistente"
    vez["busca"] = 2
    s.search(["a"], max_results=5)
    assert s.keyword_statuses[0].status == "ok"


def test_lexml_detalhe_usa_url_efetiva_com_query(monkeypatch):
    """M6: o detalhe precisa reproduzir com curl — URL com a query, nao so a base."""
    s, _ = _lexml_com(monkeypatch, _cenario_real_22_09)
    s.search(["a"], max_results=5)
    assert "operation=searchRetrieve" in s.keyword_statuses[0].detalhe


def test_lexml_parse_error_levanta_fonte_indisponivel():
    """B3: o contrato antigo ([], 0) em XML malformado deixou de existir; test_comprehensive foi adaptado."""
    from searchers.base import FonteIndisponivel
    from searchers.lexml_searcher import LexMLSearcher
    with pytest.raises(FonteIndisponivel) as e:
        LexMLSearcher()._parse_sru_response("<not>valid<xml", "teste")
    assert e.value.motivo == "resposta_ilegivel"
```

(13 testes.)

- [ ] **Step 3: Rodar e ver falhar** — `python -m pytest tests/test_fontes_indisponiveis.py -q` → 13 failed (assertions de status/motivo; nenhum `ImportError` — T1 já entregou os símbolos).

- [ ] **Step 4: `lexml_searcher.py` — imports e `__init__`**

Import (`:19`): `from searchers.base import BaseSearcher, FonteIndisponivel, ProgressCallback`.

`__init__` (`:76-77`) **já existe** — acrescentar 2 linhas mantendo o comentário existente:

```python
    def __init__(self):
        self._sru_url: Optional[str] = None  # Resolved after first request
        # URLs que ja falharam NESTA busca -> a causa. Limpo em search().
        # Antes, cada palavra-chave tentava a cadeia inteira de novo (3 URLs x N
        # palavras-chave: parte dos ~390s do test_searchers.py em 22/09).
        self._urls_mortos: dict[str, FonteIndisponivel] = {}
```

- [ ] **Step 5: `_try_fetch` — reescrever inteiro** (`:345-382`):

```python
    def _try_fetch(self, url: str, params: dict) -> Optional[str]:
        """Attempt a single GET request to the given SRU URL.

        Retries once on connection error after a 3-second delay.

        Returns:
            Response body on success; None ONLY on HTTP 404 (URL inexistente —
            o chamador passa ao proximo da cadeia).

        Raises:
            FonteIndisponivel: para tudo que nao e sucesso nem 404 — timeout,
                conexao (apos o retry), 5xx/4xx, corpo que nao e SRU. Antes,
                esses casos devolviam None e viravam "URL morto" e depois
                "sem resultado" (bloqueadores B1/B2 da rodada de 22/09).
        """
        import time

        for attempt in range(2):  # Max 2 attempts (initial + 1 retry)
            try:
                response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            except requests.exceptions.ConnectionError as e:
                if attempt == 0:
                    logger.warning(f"LexML connection error: {e}. Retrying in 3s...")
                    time.sleep(3)
                    continue
                logger.error(f"LexML connection error after retry: {e}")
                raise FonteIndisponivel("conexao", f"GET {url}: {str(e)[:160]}") from e
            except requests.exceptions.Timeout as e:
                logger.warning(f"LexML timeout ({REQUEST_TIMEOUT}s) for {url}")
                raise FonteIndisponivel("timeout", f"GET {url}: sem resposta em {REQUEST_TIMEOUT}s") from e
            except requests.exceptions.RequestException as e:
                logger.error(f"LexML request error: {e}")
                raise FonteIndisponivel("erro_interno", f"GET {url}: {type(e).__name__}: {str(e)[:160]}") from e

            efetiva = getattr(response, "url", None) or url
            if response.status_code == 404:
                logger.warning(f"LexML: 404 from {url}")
                return None
            if response.status_code == 429:
                raise FonteIndisponivel("rate_limit", f"GET {efetiva} -> 429")
            if response.status_code >= 500:
                raise FonteIndisponivel("http_5xx", f"GET {efetiva} -> HTTP {response.status_code}; corpo: {(response.text or '')[:120]!r}")
            if response.status_code >= 400:
                raise FonteIndisponivel("http_4xx", f"GET {efetiva} -> HTTP {response.status_code}")
            self._exigir_sru(response, efetiva)
            return response.text
        return None  # inalcancavel: o laco sempre devolve ou levanta

    def _exigir_sru(self, response, url: str) -> None:
        """HTTP 200 nao prova que veio SRU: em 22/09 o LexML devolvia 200
        text/html com a pagina "Verificacao de seguranca" do Senado.

        Sniff PERMISSIVO de proposito (M10): so HTML explicito e reprovado
        aqui; qualquer outra coisa vai para o ET, que levanta ParseError ->
        resposta_ilegivel em _parse_sru_response. Um SRU com BOM, sem
        declaracao <?xml ou com prefixo de namespace diferente continua
        passando — o parser usa namespace por URI.
        """
        content_type = (response.headers.get("Content-Type") or "").lower()
        corpo = (response.text or "").lstrip("﻿ \t\r\n")
        inicio = corpo[:15].lower()
        e_html = "text/html" in content_type or inicio.startswith(("<!doctype html", "<html"))
        if not e_html:
            return
        detalhe = f"GET {url} -> HTTP {response.status_code} {content_type or 'sem content-type'}; corpo: {corpo[:120]!r}"
        texto = corpo.lower()
        if "verificação de segurança" in texto or "verificacao de seguranca" in texto or "challenge" in texto:
            titulo = re.search(r"<title>([^<]*)</title>", corpo)
            if titulo:
                detalhe = f"{detalhe} — título: {titulo.group(1).strip()}"
            raise FonteIndisponivel("bloqueio_waf", detalhe)
        raise FonteIndisponivel("resposta_ilegivel", detalhe)
```

- [ ] **Step 6: `_parse_sru_response`** (`:393-397`):

```python
        try:
            root = ET.fromstring(xml_text.lstrip("﻿ \t\r\n"))
        except ET.ParseError as e:
            # Antes devolvia ([], 0) — a linha que transformava bloqueio em
            # "sem resultado". Agora e falha declarada.
            raise FonteIndisponivel(
                "resposta_ilegivel", f"XML SRU nao parseia: {e}; corpo: {xml_text[:120]!r}"
            ) from e
```

Docstring: `Returns ([], 0) on parse error.` → `Raises FonteIndisponivel("resposta_ilegivel") on parse error.`

- [ ] **Step 7: `_fetch_sru` — cache de causa** (`:314-343`), corpo novo:

```python
        if self._sru_url:
            result = self._try_fetch(self._sru_url, params)
            if result is not None:
                return result
            # o URL que funcionava passou a dar 404 (H1): invalida e cai na cadeia
            self._urls_mortos[self._sru_url] = FonteIndisponivel(
                "endpoint_inexistente", f"GET {self._sru_url} -> 404 (URL que antes funcionava nesta busca)")
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
            self._urls_mortos[url] = FonteIndisponivel("endpoint_inexistente", f"GET {url} -> 404")
            logger.warning(f"LexML: {url} 404; proximo da cadeia")

        raise self._causa_da_cadeia_morta()

    _PRIORIDADE = ("bloqueio_waf", "resposta_ilegivel", "endpoint_inexistente")

    def _causa_da_cadeia_morta(self) -> FonteIndisponivel:
        """Nenhum URL restou: relevanta a causa MAIS ESPECIFICA (B2).

        'endpoint_inexistente' generico so quando tudo foi 404. O detalhe
        agrega URL por URL, para a tela e a planilha dizerem o que o curl diz.
        """
        causas = self._urls_mortos
        motivo = next((m for m in self._PRIORIDADE if any(c.motivo == m for c in causas.values())), "endpoint_inexistente")
        principal = next(c for c in causas.values() if c.motivo == motivo)
        resumo = "; ".join(f"{u.rsplit('/', 2)[-2]}/{u.rsplit('/', 1)[-1]}: {c.motivo}" for u, c in causas.items())
        return FonteIndisponivel(motivo, f"{principal.detalhe} | cadeia: {resumo} (cacheado nesta busca)")
```

Docstring de `_fetch_sru`: substituir `Response body as string, or None on failure.` por `Response body as string. Raises FonteIndisponivel when no URL works; failed URLs are cached in self._urls_mortos for this search.`

- [ ] **Step 8: `_search_keyword`** (`:271-304`) — paginação declarada:

```python
        all_results: list[NormativoResult] = []
        start_record = 1
        first_page = True
        self._erro_paginacao: Optional[FonteIndisponivel] = None

        while len(all_results) < max_results:
            params = {...}  # inalterado
            try:
                xml_text = self._fetch_sru(params)
            except FonteIndisponivel as e:
                if first_page:
                    raise
                # H5: pagina seguinte falhou — devolve o que veio, mas DECLARA
                e.detalhe = f"startRecord={start_record}: {e.detalhe}"
                self._erro_paginacao = e
                logger.warning(f"LexML: paginacao interrompida: {e}")
                break
            first_page = False
            records, total_count = self._parse_sru_response(xml_text, keyword)
            ...  # restante inalterado
```

Remover o bloco `if xml_text is None: ... raise ConnectionError(...)` (`:279-286`) e o comentário acima dele. Docstring `Raises: ConnectionError...` → `Raises: FonteIndisponivel: se a primeira pagina falhar. Falha em pagina seguinte fica em self._erro_paginacao.`

- [ ] **Step 9: `_search_keyword_safe`** (`:228-241`):

```python
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
```

- [ ] **Step 10: `search()` — laço principal, cap e retry.** Substituir o trecho de `:106` (`results_by_id: dict...`) até `:212` (fim do retry) por:

```python
        results_by_id: dict[str, NormativoResult] = {}
        self.keyword_statuses: list[KeywordStatus] = []
        self._urls_mortos.clear()   # M11: cache de falha e POR BUSCA
        self._sru_url = None
        failed_keywords: list[str] = []
        total_keywords = len(keywords)

        for idx, keyword in enumerate(keywords):
            if len(results_by_id) >= max_results:
                logger.info(f"LexML: reached max_results ({max_results}), stopping after {idx}/{total_keywords} keywords")
                # M4: palavra-chave nunca consultada nao pode virar "sem resultado"
                for restante in keywords[idx:]:
                    self.keyword_statuses.append(KeywordStatus(
                        keyword=restante, source="lexml", result_count=0, status="error",
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
                    keyword=keyword, source="lexml", result_count=0, status="error",
                    error_message=str(erro), motivo=erro.motivo, detalhe=erro.detalhe,
                ))
                failed_keywords.append(keyword)
            elif len(keyword_results) == 0:
                self.keyword_statuses.append(KeywordStatus(
                    keyword=keyword, source="lexml", result_count=0, status="empty",
                    parcial=erro_pag is not None, detalhe=erro_pag.detalhe if erro_pag else "",
                ))
            else:
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
                    keyword=keyword, source="lexml", result_count=new_count, status="ok",
                    parcial=erro_pag is not None, detalhe=erro_pag.detalhe if erro_pag else "",
                ))

            if idx < total_keywords - 1:
                self._rate_limit()

        # --- Retry failed keywords (max 3 attempts, bail if API is down) ---
        MAX_RETRIES = 3
        cadeia_morta = all(u in self._urls_mortos for u in (PRIMARY_SRU_URL, FALLBACK_SRU_URL, FALLBACK_SRU_URL_2))
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
                    # Mark remaining as retried-but-failed without calling API.
                    # B2: motivo/detalhe originais FICAM — so o retried muda.
                    for st in self.keyword_statuses:
                        if st.keyword == keyword and st.source == "lexml" and st.status == "error":
                            st.retried = True
                            break
                    continue

                remaining = max_results - len(results_by_id)
                keyword_results, erro, erro_pag = self._search_keyword_safe(keyword, max_results=remaining)

                for st in self.keyword_statuses:
                    if st.keyword == keyword and st.source == "lexml" and st.status == "error":
                        st.retried = True
                        if erro is not None:
                            st.error_message = f"Retry failed: {erro}"
                            # B2: nunca rebaixar um motivo especifico para generico
                            if st.motivo in ("", "endpoint_inexistente") or erro.motivo not in ("endpoint_inexistente",):
                                st.motivo, st.detalhe = erro.motivo, erro.detalhe
                            api_still_down = True  # Stop retrying
                        elif len(keyword_results) == 0:
                            st.status, st.error_message, st.motivo, st.detalhe = "empty", "", "", ""
                            st.parcial = erro_pag is not None
                        else:
                            st.status, st.error_message, st.motivo, st.detalhe = "ok", "", "", ""
                            st.parcial = erro_pag is not None
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
            # cadeia morta em cache: retentar nao faria requisicao nenhuma (B2)
            logger.info("LexML: cadeia de URLs morta nesta busca; retry pulado")
            for st in self.keyword_statuses:
                if st.source == "lexml" and st.status == "error" and st.motivo != "nao_consultada":
                    st.retried = True
```

⚠ O que o trecho acima **preserva** do original: mensagens de log, `progress_callback`, `MAX_RETRIES=3`, o comentário "Only retry a few…", a semântica de `api_still_down`. O que muda está comentado com o código do achado.

- [ ] **Step 11: Adaptar `test_comprehensive.py:362-367`** (B3) — o contrato mudou; o teste passa a afirmar o contrato novo, **mantido, não apagado**:

```python
def test_lexml_parse_sru_response_malformed_xml():
    """Malformed XML must be DECLARED as resposta_ilegivel, never silently ([], 0).

    Contrato mudou na frente 2 (2026-09-22): devolver ([], 0) era a linha que
    transformava o bloqueio do LexML em "sem resultado"."""
    from searchers.base import FonteIndisponivel
    searcher = LexMLSearcher()
    try:
        searcher._parse_sru_response("<not>valid<xml", "teste")
    except FonteIndisponivel as e:
        assert e.motivo == "resposta_ilegivel"
    else:
        raise AssertionError("esperava FonteIndisponivel")
```

- [ ] **Step 12: Rodar e ver passar**

`python -m pytest tests/test_fontes_indisponiveis.py -q` → `13 passed`.
`python test_comprehensive.py | tail -3` → `Total: 98 | Passed: 98 | Failed: 0`.
`python test_searchers.py | tail -2` → `13/13 passed` (anotar o tempo: era ~390s).
`python -m pytest test_phase4.py -q` → `56 passed`.

- [ ] **Step 13: Runner** — `SUITES_PYTEST = ["test_phase4.py", "tests/test_fontes_indisponiveis.py"]`, `BASELINE["tests/test_fontes_indisponiveis.py"] = 13`; atualizar o comentário sobre "nasce com UMA suite". Na raiz: `python tools/run_all_tests.py` → TUDO VERDE; `python tools/golden_master.py comparar` → OK.

- [ ] **Step 14: Auditoria (os 2 comandos) + commit**

```bash
git add levantamento-normativos/searchers/lexml_searcher.py levantamento-normativos/test_comprehensive.py levantamento-normativos/tests/ tools/run_all_tests.py
git commit -m "feat(frente2): LexML declara bloqueio, timeout, 5xx e paginacao parcial — nunca 'sem resultado'

_try_fetch reescrito: so 404 devolve None; o resto levanta com o motivo
certo (B1). Cache de causa por URL, limpo por busca; cadeia morta relevanta
a causa mais especifica e o retry nao rebaixa motivo (B2): no cenario real
de 22/09 as 3 palavras-chave saem bloqueio_waf com o titulo do desafio.
Sniff permissivo (BOM/prefixo nao reprovam SRU). Falha em pagina seguinte
vira parcial=True. Keyword pulada por max_results vira nao_consultada.
test_comprehensive adaptado ao contrato novo de _parse_sru_response (98
mantidos). Suite nova: 13."
git push origin master
```

---

### Task 3: TCU — 5xx/4xx/503/HTML declarados, paginação parcial, classificação por endpoint

**Files:**
- Modify: `levantamento-normativos/searchers/tcu_searcher.py` — imports; `search()` (`:62-147`); `_fetch_all_pages_safe`/`_fetch_all_pages` (`:153-206`); `_request_with_retry` (`:208-256`)
- Modify: `levantamento-normativos/test_comprehensive.py:473-477`
- Test: `tests/test_fontes_indisponiveis.py` (seção TCU)
- Modify: `tools/run_all_tests.py`

**Interfaces — Produces:**
- `TCUSearcher._request_with_retry(url, params) -> dict | list` — levanta `FonteIndisponivel` (nunca `None`).
- `TCUSearcher._fetch_all_pages(url) -> tuple[list[dict], Optional[FonteIndisponivel], bool]` = `(itens, erro, parcial)`; idem `_fetch_all_pages_safe`.

- [ ] **Step 1: Testes que falham** — acrescentar a `tests/test_fontes_indisponiveis.py`:

```python
# ---------------------------------------------------------------------------
# TCU — a fixture e o item REAL capturado em 22/09 (sem `ementa`, `numero`, `ano`)
# ---------------------------------------------------------------------------

ACORDAOS_REAIS = json.loads((FIXTURES / "tcu_acordaos_real.json").read_text(encoding="utf-8"))
ACORDAO = ACORDAOS_REAIS[0]   # sumario fala de "TURISMO"


def _tcu_com(monkeypatch, por_url):
    """por_url: {trecho_da_url: callable(params) -> RespostaFake | levanta}."""
    from searchers import tcu_searcher

    chamadas: list[str] = []

    def fake_get(url, params=None, timeout=None, **kw):
        chamadas.append(url)
        for trecho, responder in por_url.items():
            if trecho in url:
                return responder(params)
        raise AssertionError(f"URL inesperada: {url}")

    monkeypatch.setattr("searchers.tcu_searcher.requests.get", fake_get)
    return tcu_searcher.TCUSearcher(), chamadas


def _500_atos(p):
    return RespostaFake(500, '{"url":"Erro no serviço","erro":"HttpClientErrorException: 404 Not Found"}',
                        "application/json;charset=UTF-8", url="https://tcu/api/atonormativo/recupera-atos-normativos?inicio=0")


def test_tcu_500_num_endpoint_e_error_mesmo_com_o_outro_ok(monkeypatch):
    s, chamadas = _tcu_com(monkeypatch, {
        "recupera-acordaos": lambda p: RespostaFake(200, json_data=ACORDAOS_REAIS),
        "recupera-atos-normativos": _500_atos,
    })
    resultados = s.search(["turismo"], max_results=5)
    assert len(resultados) == 1                      # o acordao real entrou (T4 e quem casa o sumario;
    st = s.keyword_statuses[0]                       #  ate la, este assert e ajustado na T4 — ver nota)
    assert (st.status, st.motivo) == ("error", "http_5xx")
    assert "recupera-atos-normativos" in st.detalhe and "404 Not Found" in st.detalhe
    assert "Acórdãos: ok" in st.detalhe
    assert sum(1 for u in chamadas if "atos" in u) == 3  # 3 retries no 5xx
```

⚠ **Nota sobre `len(resultados) == 1`:** até a T4, `_map_acordao` não lê `sumario`, então o acórdão real **não casa** "turismo" — o assert correto **nesta task** é `len(resultados) == 0` e `st.result_count == 0`. Escrever assim na T3; a **T4 troca para 1** no mesmo commit em que corrige o mapeamento. (Registrado para o executor não "consertar" o searcher aqui.)

```python
def test_tcu_503_e_manutencao_com_hora_e_hipotese(monkeypatch):
    s, _ = _tcu_com(monkeypatch, {
        "recupera-acordaos": lambda p: RespostaFake(503, "", "text/html"),
        "recupera-atos-normativos": lambda p: RespostaFake(503, "", "text/html"),
    })
    s.search(["x"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo) == ("error", "manutencao_503")
    assert "503" in st.detalhe and "às " in st.detalhe and "20h" in st.detalhe   # hora + hipotese marcada


def test_tcu_404_e_endpoint_inexistente_sem_retry(monkeypatch):
    s, chamadas = _tcu_com(monkeypatch, {
        "recupera-acordaos": lambda p: RespostaFake(404, "", "text/html"),
        "recupera-atos-normativos": lambda p: RespostaFake(404, "", "text/html"),
    })
    s.search(["x"], max_results=5)
    assert s.keyword_statuses[0].motivo == "endpoint_inexistente"
    assert len(chamadas) == 2                          # sem retry em 4xx


def test_tcu_429_e_rate_limit_e_403_e_http_4xx(monkeypatch):
    s, _ = _tcu_com(monkeypatch, {
        "recupera-acordaos": lambda p: RespostaFake(429, "", "text/html"),
        "recupera-atos-normativos": lambda p: RespostaFake(403, "", "text/html"),
    })
    s.search(["x"], max_results=5)
    st = s.keyword_statuses[0]
    assert st.motivo == "rate_limit"                  # o primeiro endpoint que caiu manda o motivo
    assert "http_4xx" in st.detalhe and "403" in st.detalhe


def test_tcu_200_html_e_bloqueio_ou_ilegivel_sem_retry(monkeypatch):
    s, chamadas = _tcu_com(monkeypatch, {
        "recupera-acordaos": lambda p: RespostaFake(200, DESAFIO_HTML, "text/html"),
        "recupera-atos-normativos": lambda p: RespostaFake(200, "<html>x</html>", "text/html"),
    })
    s.search(["x"], max_results=5)
    st = s.keyword_statuses[0]
    assert st.motivo == "bloqueio_waf"
    assert "resposta_ilegivel" in st.detalhe
    assert len(chamadas) == 2


def test_tcu_timeout_e_conexao_mapeiam_motivo(monkeypatch):
    def estoura(p):
        raise requests.exceptions.Timeout("lento")
    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": estoura, "recupera-atos-normativos": estoura})
    s.search(["x"], max_results=5)
    assert s.keyword_statuses[0].motivo == "timeout"

    def cai(p):
        raise requests.exceptions.ConnectionError("sem rota")
    s2, _ = _tcu_com(monkeypatch, {"recupera-acordaos": cai, "recupera-atos-normativos": cai})
    s2.search(["x"], max_results=5)
    assert s2.keyword_statuses[0].motivo == "conexao"


def test_tcu_falha_na_segunda_pagina_e_ok_parcial(monkeypatch):
    """B5: itens REAIS variando numeroAcordao; ids distintos so depois da T4 — aqui provamos o parcial."""
    from searchers import tcu_searcher
    pagina_cheia = [dict(ACORDAO, key=f"A-{i}", numeroAcordao=str(i), titulo=f"ACÓRDÃO {i}/2026") for i in range(tcu_searcher.PAGE_SIZE)]

    def acordaos(p):
        if p["inicio"] == 0:
            return RespostaFake(200, json_data=pagina_cheia)
        return RespostaFake(500, "boom", "text/html", url="https://tcu/api/acordao/recupera-acordaos?inicio=20")

    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": acordaos,
                                  "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[])})
    s.search(["turismo"], max_results=100)
    st = s.keyword_statuses[0]
    assert st.parcial is True
    assert "inicio=20" in st.detalhe and "http_5xx" in st.detalhe


def test_tcu_dois_endpoints_ok_sem_match_continua_empty(monkeypatch):
    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": lambda p: RespostaFake(200, json_data=ACORDAOS_REAIS),
                                  "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[])})
    s.search(["assunto-que-nao-existe"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo, st.parcial) == ("empty", "", False)


def test_tcu_item_que_quebra_o_mapeamento_vira_erro_interno_declarado(monkeypatch):
    """H2: dataSessao inteiro derrubava search() inteiro; agora e erro_interno por keyword, nao sumico."""
    quebrado = dict(ACORDAO, dataSessao=20260916)
    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": lambda p: RespostaFake(200, json_data=[quebrado]),
                                  "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[])})
    s.search(["turismo"], max_results=5)
    st = s.keyword_statuses[0]
    assert (st.status, st.motivo) == ("error", "erro_interno")
    assert "AttributeError" in st.detalhe or "strip" in st.detalhe
```

(8 testes → suíte 13 + 8 = 21.) ⚠ O último teste só faz sentido **depois da T4** (hoje `sumario` não é lido, então "turismo" não casa e o mapeamento nem roda): **escrever na T3 com a keyword que casa o campo lido hoje** — nenhuma casa; então na T3 este teste é escrito **já com o assert final** e marcado `@pytest.mark.xfail(reason="mapeamento real so na T4", strict=True)`; a T4 remove o `xfail`. Assim a contagem da suíte já é 21 na T3 e continua 21 na T4 (o `xfail` conta como passed no `-q`? **Não** — pytest reporta `xfailed` separado e `PADRAO_PYTEST` do runner só lê `N passed`; então na T3 o runner vê **20** e o BASELINE da T3 é **20**; a T4 sobe para **21 + 3 novos = 24**). A tabela do topo reflete isso (T3 = 20, total 240).

- [ ] **Step 2: Ver falhar** — `python -m pytest tests/test_fontes_indisponiveis.py -q -k tcu` → falhas de status/motivo.

- [ ] **Step 3: `tcu_searcher.py`**

**3a.** Import: `from searchers.base import BaseSearcher, FonteIndisponivel, ProgressCallback`; conferir `import time` e `import re` no topo (acrescentar `re` se faltar) e `from datetime import datetime`.

**3b.** `_request_with_retry` — reescrever:

```python
    def _request_with_retry(self, url: str, params: dict) -> dict | list:
        """Send GET request with exponential backoff retry on 5xx/network.

        Returns:
            Parsed JSON (dict or list).

        Raises:
            FonteIndisponivel: com o motivo pela classe do erro (H6):
                503 -> manutencao_503 (sem retry; hora + hipotese da janela 20h-21h);
                404 -> endpoint_inexistente, 429 -> rate_limit, outro 4xx -> http_4xx (sem retry);
                5xx apos MAX_RETRIES -> http_5xx; timeout/conexao apos MAX_RETRIES;
                200 que nao e JSON -> bloqueio_waf (pagina de desafio) ou resposta_ilegivel.
            Antes devolvia None e o chamador tratava None como "fim das paginas":
            um 500 virava "sem resultado" (medido em 22/09).
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
                raise FonteIndisponivel("erro_interno", f"GET {url}: {type(e).__name__}: {str(e)[:160]}") from e
            else:
                efetiva = getattr(response, "url", None) or url
                sc = response.status_code
                if sc == 503:
                    agora = datetime.now()
                    janela = "dentro da janela de manutenção conhecida (20h-21h BRT)" if 20 <= agora.hour < 21 \
                        else "fora da janela de manutenção conhecida (20h-21h BRT)"
                    raise FonteIndisponivel("manutencao_503", f"GET {efetiva} -> 503 às {agora:%d/%m %H:%M}; {janela}. Hipótese, não fato.")
                if sc == 404:
                    raise FonteIndisponivel("endpoint_inexistente", f"GET {efetiva} -> 404")
                if sc == 429:
                    raise FonteIndisponivel("rate_limit", f"GET {efetiva} -> 429")
                if 400 <= sc < 500:
                    raise FonteIndisponivel("http_4xx", f"GET {efetiva} -> HTTP {sc}")
                if sc >= 500:
                    ultimo = requests.HTTPError(f"{sc}", response=response)
                else:
                    return self._exigir_json(response, efetiva)
            if attempt < MAX_RETRIES - 1:
                delay = 2 ** (attempt + 1)  # 2s, 4s, 8s
                logger.warning(f"TCU API error (attempt {attempt + 1}/{MAX_RETRIES}): {ultimo}. Retrying in {delay}s...")
                time.sleep(delay)
        logger.error(f"TCU API failed after {MAX_RETRIES} attempts: {ultimo}")
        if isinstance(ultimo, requests.exceptions.Timeout):
            raise FonteIndisponivel("timeout", f"GET {url}: {REQUEST_TIMEOUT}s x {MAX_RETRIES}")
        if isinstance(ultimo, requests.exceptions.ConnectionError):
            raise FonteIndisponivel("conexao", f"GET {url}: {str(ultimo)[:160]}")
        resp = getattr(ultimo, "response", None)
        corpo = (getattr(resp, "text", "") or "")[:160]
        raise FonteIndisponivel("http_5xx", f"GET {getattr(resp, 'url', url)} -> HTTP {getattr(resp, 'status_code', '?')} em {MAX_RETRIES} tentativas; corpo: {corpo!r}")

    def _exigir_json(self, response, url: str):
        """200 que nao e JSON e falha declarada, nao 'sem resultado' (H6)."""
        try:
            return response.json()
        except ValueError as e:
            corpo = (response.text or "").lstrip("﻿ \t\r\n")
            ct = (response.headers.get("Content-Type") or "").lower()
            detalhe = f"GET {url} -> 200 {ct or 'sem content-type'} nao e JSON; corpo: {corpo[:120]!r}"
            texto = corpo.lower()
            if "verificação de segurança" in texto or "verificacao de seguranca" in texto or "challenge" in texto:
                raise FonteIndisponivel("bloqueio_waf", detalhe) from e
            raise FonteIndisponivel("resposta_ilegivel", detalhe) from e
```

**3c.** `_fetch_all_pages` → `(itens, erro, parcial)`:

```python
    def _fetch_all_pages(self, url: str) -> tuple[list[dict], Optional[FonteIndisponivel], bool]:
        """Fetch all pages from a paginated TCU API endpoint.

        Stops at MAX_PAGES * PAGE_SIZE records to avoid excessive requests.

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
            items = data if isinstance(data, list) else data.get("items", data.get("data", []))
            if not isinstance(items, list):
                erro = FonteIndisponivel("resposta_ilegivel", f"GET {url}?inicio={offset}: formato inesperado {type(data).__name__}")
                return all_items, erro, page > 0
            all_items.extend(items)
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
```

**3d.** `search()` — substituir de `acordao_items, acordao_error = ...` até o fim do `for keyword in keywords:` por:

```python
        acordao_items, acordao_erro, acordao_parcial = self._fetch_all_pages_safe(f"{API_BASE_URL}{ACORDAOS_PATH}")
        logger.info(f"TCU: {len(acordao_items)} acordaos fetched, filtering by keywords")

        if progress_callback:
            progress_callback(1, total_steps, "TCU: buscando atos normativos")
        logger.info("TCU: fetching atos normativos")
        atos_items, atos_erro, atos_parcial = self._fetch_all_pages_safe(f"{API_BASE_URL}{ATOS_PATH}")
        logger.info(f"TCU: {len(atos_items)} atos normativos fetched, filtering by keywords")

        def _resumo(nome, itens, erro, parcial):
            if erro is not None and not itens:
                return f"{nome}: {erro.motivo} em {erro.detalhe}"
            if parcial:
                return f"{nome}: parcial ({len(itens)} itens; {erro.detalhe})"
            return f"{nome}: ok ({len(itens)} itens)"

        detalhe = "; ".join([_resumo("Acórdãos", acordao_items, acordao_erro, acordao_parcial),
                             _resumo("Atos", atos_items, atos_erro, atos_parcial)])
        # Um endpoint que caiu na PRIMEIRA pagina torna a busca "error" mesmo que
        # o outro tenha respondido: o usuario precisa saber que metade da fonte
        # nao foi vista. Resultados do endpoint vivo continuam entrando.
        erro_primario = next((e for e, itens in ((acordao_erro, acordao_items), (atos_erro, atos_items))
                              if e is not None and not itens), None)
        parcial = acordao_parcial or atos_parcial

        for idx, keyword in enumerate(keywords):
            if len(results_by_id) >= max_results:
                for restante in keywords[idx:]:   # M4
                    self.keyword_statuses.append(KeywordStatus(
                        keyword=restante, source="tcu", result_count=0, status="error", motivo="nao_consultada",
                        detalhe=f"busca parou em max_results={max_results} antes desta palavra-chave"))
                break
            kw_count = 0
            try:
                for item in acordao_items:
                    if len(results_by_id) >= max_results:
                        break
                    if self._matches_keyword(self._texto_do_acordao(item), keyword):
                        result = self._map_acordao(item, keyword)
                        if result.id not in results_by_id:
                            results_by_id[result.id] = result
                            kw_count += 1
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
                    keyword=keyword, source="tcu", result_count=kw_count, status="error", motivo="erro_interno",
                    detalhe=f"{type(e).__name__}: {e}"[:200], error_message=f"{type(e).__name__}: {e}"[:200]))
                continue

            if erro_primario is not None:
                status, motivo = "error", erro_primario.motivo
            elif kw_count == 0:
                status, motivo = "empty", ""
            else:
                status, motivo = "ok", ""
            self.keyword_statuses.append(KeywordStatus(
                keyword=keyword, source="tcu", result_count=kw_count, status=status, motivo=motivo,
                detalhe=detalhe if (status == "error" or parcial) else "",
                error_message=detalhe if status == "error" else "", parcial=parcial))

    def _texto_do_acordao(self, item: dict) -> str:
        """Texto onde a palavra-chave e procurada. Ate a T4: `ementa` (que a API
        real nao devolve — ver tests/fixtures/tcu_acordaos_real.json)."""
        return item.get("ementa", "")
```

Docstring de `search()`: acrescentar `Um endpoint que falha na primeira pagina marca status="error" para toda palavra-chave, com result_count do endpoint que respondeu; paginacao interrompida marca parcial=True; palavra-chave pulada pelo cap marca nao_consultada.`

- [ ] **Step 4: Adaptar `test_comprehensive.py:473-477`** (B3): `s._fetch_all_pages = lambda url: []` → `s._fetch_all_pages = lambda url: ([], None, False)`, com a docstring do teste ganhando `Contrato de _fetch_all_pages mudou na frente 2 (2026-09-22): (itens, erro, parcial).`

- [ ] **Step 5: Ver passar** — suíte nova `20 passed, 1 xfailed`; `python test_comprehensive.py` → 98/98; `python test_searchers.py` → 13/13.

- [ ] **Step 6: BASELINE** `tests/test_fontes_indisponiveis.py = 20`; runner TUDO VERDE; golden OK.

- [ ] **Step 7: Auditoria + commit**

```bash
git add levantamento-normativos/searchers/tcu_searcher.py levantamento-normativos/test_comprehensive.py levantamento-normativos/tests/ tools/run_all_tests.py
git commit -m "feat(frente2): TCU classifica 5xx/4xx/503/HTML e declara paginacao parcial

_request_with_retry levanta FonteIndisponivel por classe de erro (4xx sem
retry; 503 com hora e hipotese marcada; 200 nao-JSON e bloqueio ou
ilegivel); _fetch_all_pages devolve (itens, erro, parcial). Um endpoint
caido marca error mesmo com o outro ok; item que quebra o mapeamento vira
erro_interno por keyword; keyword pulada pelo cap vira nao_consultada.
Fixture: 2 acordaos REAIS de 22/09. test_comprehensive adaptado (98).
Suite: 13 -> 20 (+1 xfail para a T4)."
git push origin master
```

---

### Task 4: TCU — mapear o esquema REAL do acórdão (⚠ emenda à spec §3.7)

✅ **Fato medido em 22/09** (`tests/fixtures/tcu_acordaos_real.json`, `curl` em `recupera-acordaos?quantidade=2`): as chaves são `anoAcordao, colegiado, dataSessao, key, numeroAcordao, numeroAta, relator, situacao, sumario, tipo, titulo, urlAcordao, urlArquivo, urlArquivoPdf`. **Não existem `ementa`, `numero`, `ano`** — as três chaves que `_map_acordao` lê (`tcu_searcher.py:265-266,279`) e a que o filtro usa (`:104`). Consequência na v1.0: todo acórdão mapeia para `nome="Acordao / - TCU - Plenário"`, `numero="/"`, mesmo `id`, e **nunca casa palavra-chave** — a fonte diz "ok (500 itens)" e entrega zero. A spec §3.7 dizia "nenhum searcher muda o que mapeia"; **essa regra cai aqui**, porque manter o mapeamento é manter uma fonte estruturalmente cega. Decisão do Rodrigo em 22/09: "todos os consertos da v1 entram".

📝 **Mapeamento proposto** (literal, sem parafrasear): `nome ← titulo`; `numero ← f"{numeroAcordao}/{anoAcordao}"`; `data ← dataSessao`; `orgao_emissor ← f"TCU - {colegiado}"`; `ementa ← sumario` (é o texto do acórdão; o TCU chama de sumário); `link ← urlAcordao` (o link real da API; `_build_acordao_link` continua como fallback quando `urlAcordao` vier vazio); `situacao ← situacao` se presente. O filtro passa a procurar a palavra-chave em `sumario` **e** `titulo`. Chaves antigas continuam aceitas como fallback (`item.get("numeroAcordao") or item.get("numero")`), para não regredir se a API tiver dois formatos.

**Files:** `tcu_searcher.py` (`_map_acordao`, `_texto_do_acordao`); `tests/test_fontes_indisponiveis.py`; `tools/run_all_tests.py`.

- [ ] **Step 1: Testes** — remover o `xfail` de `test_tcu_item_que_quebra_o_mapeamento_vira_erro_interno_declarado`; em `test_tcu_500_num_endpoint...` trocar `len(resultados) == 0`/`result_count == 0` por `== 1`; acrescentar:

```python
def test_tcu_acordao_real_mapeia_titulo_numero_ano_sumario_link():
    from searchers.tcu_searcher import TCUSearcher
    r = TCUSearcher()._map_acordao(ACORDAO, "turismo")
    assert r.nome == ACORDAO["titulo"]
    assert r.numero == f'{ACORDAO["numeroAcordao"]}/{ACORDAO["anoAcordao"]}'
    assert r.data == ACORDAO["dataSessao"]
    assert r.ementa == ACORDAO["sumario"]          # literal, sem parafrase
    assert r.link == ACORDAO["urlAcordao"]
    assert r.orgao_emissor == f'TCU - {ACORDAO["colegiado"]}'


def test_tcu_acordaos_reais_tem_ids_distintos_e_casam_o_sumario(monkeypatch):
    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": lambda p: RespostaFake(200, json_data=ACORDAOS_REAIS),
                                  "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[])})
    resultados = s.search(["turismo"], max_results=10)
    ids = {s._map_acordao(a, "x").id for a in ACORDAOS_REAIS}
    assert len(ids) == len(ACORDAOS_REAIS)
    assert len(resultados) >= 1 and all("TURISMO" in r.ementa.upper() or "TURISMO" in r.nome.upper() for r in resultados)


def test_tcu_pagina_cheia_com_numeros_distintos_da_page_size_resultados(monkeypatch):
    from searchers import tcu_searcher
    pagina = [dict(ACORDAO, key=f"A-{i}", numeroAcordao=str(i), titulo=f"ACÓRDÃO {i}/2026 - TURISMO") for i in range(tcu_searcher.PAGE_SIZE)]
    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": lambda p: RespostaFake(200, json_data=pagina if p["inicio"] == 0 else []),
                                  "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[])})
    resultados = s.search(["turismo"], max_results=100)
    assert len(resultados) == tcu_searcher.PAGE_SIZE
    assert len({r.id for r in resultados}) == tcu_searcher.PAGE_SIZE
```

- [ ] **Step 2: Ver falhar** — `-k "acordao_real or pagina_cheia or quebra_o_mapeamento"` → 3 failed + o ex-xfail agora falha "normalmente".

- [ ] **Step 3: Implementar**

```python
    def _texto_do_acordao(self, item: dict) -> str:
        """Onde a palavra-chave e procurada: sumario + titulo (esquema real da
        API, medido em 22/09) — com fallback para `ementa` se a API tiver dois
        formatos. Antes lia so `ementa`, que a API nao devolve: zero match, sempre."""
        return " ".join(x for x in (item.get("sumario"), item.get("titulo"), item.get("ementa")) if x)

    def _map_acordao(self, item: dict, found_by: str) -> NormativoResult:
        """Map a raw acordao JSON item (esquema real de 22/09) to a NormativoResult.

        Campos literais da API, sem parafrase: titulo -> nome, sumario -> ementa,
        numeroAcordao/anoAcordao -> numero, dataSessao -> data, urlAcordao -> link.
        Chaves antigas (numero/ano/ementa) aceitas como fallback.

        Returns:
            NormativoResult with tipo="Acordao TCU".
        """
        numero = str(item.get("numeroAcordao") or item.get("numero") or "")
        ano = str(item.get("anoAcordao") or item.get("ano") or "")
        colegiado = item.get("colegiado", "")
        date_raw = item.get("dataSessao") or item.get("dataAta") or ""
        date_str = self._safe_date_format(str(date_raw)) if date_raw else None
        return NormativoResult(
            nome=item.get("titulo") or f"Acordao {numero}/{ano} - TCU - {colegiado}",
            tipo="Acordao TCU",
            numero=f"{numero}/{ano}",
            data=date_str,
            orgao_emissor=f"TCU - {colegiado}",
            ementa=item.get("sumario") or item.get("ementa", ""),
            link=item.get("urlAcordao") or self._build_acordao_link(numero, ano),
            source="tcu",
            found_by=found_by,
            relevancia=0.5,
            raw_data=item,
        )
```

⚠ `date_str` para `dataSessao` inteiro (teste H2): `str(20260916)` passa por `_safe_date_format` sem levantar — o teste de `erro_interno` precisa então de outro item quebrado: usar `dict(ACORDAO, titulo=None, numeroAcordao=None, sumario=123)` (o `" ".join` de `_texto_do_acordao` levanta `TypeError` com `123`). Ajustar o teste H2 para esse item e para `"TypeError" in st.detalhe`.

- [ ] **Step 4: Ver passar** — suíte `24 passed`. `test_comprehensive` 98/98; `test_searchers` 13/13 (⚠ se algum afirmar o `nome` antigo `Acordao N/A - TCU`, adaptar no mesmo commit e registrar). Golden OK (o corpus fixo não passa por `_map_acordao`).

- [ ] **Step 5: BASELINE 24; commit**

```bash
git add levantamento-normativos/searchers/tcu_searcher.py levantamento-normativos/tests/ tools/run_all_tests.py docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md
git commit -m "fix(frente2): TCU le o esquema REAL do acordao (titulo/sumario/numeroAcordao/anoAcordao/urlAcordao)

Medido em 22/09: a API nao devolve ementa/numero/ano; _map_acordao lia so
essas chaves, entao todo acordao colapsava num id e nunca casava
palavra-chave — a fonte dizia ok e entregava zero. Emenda a spec 3.7,
registrada nela. Textos literais, sem parafrase. Suite: 20 -> 24."
git push origin master
```

E na spec §3.7, acrescentar: `> ⚠ Emendado em 22/09 (plano v2, T4): o mapeamento do acórdão do TCU MUDA — a API real não devolve as chaves que o código lia. Ver a fixture real.`

---

### Task 5: Google/DDG — vocabulário mínimo (⚠ emenda à spec §5)

**Files:** `searchers/google_searcher.py` (`:145-167` ddgs; `:169-205` CSE; `:246-271` laço); `tests/test_fontes_indisponiveis.py`; `tools/run_all_tests.py`.

**Interfaces — Produces:** `GoogleSearcher._search_urls(keyword) -> tuple[list[dict], Optional[FonteIndisponivel]]` (era `(list, str)`); `DDGSException("No results found.")` → lista vazia **sem** erro.

- [ ] **Step 1: Testes** (4):

```python
# ---------------------------------------------------------------------------
# Google / DuckDuckGo (M5)
# ---------------------------------------------------------------------------

def _ddg_com(monkeypatch, text_impl):
    from searchers import google_searcher
    monkeypatch.setattr(google_searcher, "_BACKEND", "ddgs")

    class DDGSFake:
        def text(self, query, max_results=10):
            return text_impl(query)

    import ddgs
    monkeypatch.setattr(ddgs, "DDGS", DDGSFake)
    return google_searcher.GoogleSearcher()


def test_ddg_no_results_e_empty_nao_error(monkeypatch):
    from ddgs.exceptions import DDGSException
    def sem(q): raise DDGSException("No results found.")
    s = _ddg_com(monkeypatch, sem)
    s.search(["x"], max_results=5)
    assert (s.keyword_statuses[0].status, s.keyword_statuses[0].motivo) == ("empty", "")


def test_ddg_timeout_e_ratelimit_mapeiam_motivo(monkeypatch):
    from ddgs.exceptions import TimeoutException, RatelimitException
    def lento(q): raise TimeoutException("t")
    s = _ddg_com(monkeypatch, lento); s.search(["x"], max_results=5)
    assert s.keyword_statuses[0].motivo == "timeout"
    def cota(q): raise RatelimitException("r")
    s2 = _ddg_com(monkeypatch, cota); s2.search(["x"], max_results=5)
    assert s2.keyword_statuses[0].motivo == "rate_limit"


def test_ddg_erro_generico_e_erro_interno(monkeypatch):
    def bug(q): raise KeyError("href")
    s = _ddg_com(monkeypatch, bug); s.search(["x"], max_results=5)
    assert s.keyword_statuses[0].motivo == "erro_interno"


def test_google_keywords_alem_de_5_ganham_nao_consultada(monkeypatch):
    s = _ddg_com(monkeypatch, lambda q: [])
    s.search([f"k{i}" for i in range(7)], max_results=50)
    assert [st.motivo for st in s.keyword_statuses[5:]] == ["nao_consultada"] * 2
    assert "MAX_GOOGLE_KEYWORDS=5" in s.keyword_statuses[5].detalhe
```

- [ ] **Step 2: Ver falhar.**

- [ ] **Step 3: Implementar** — `from searchers.base import BaseSearcher, FonteIndisponivel, ProgressCallback`.

`_search_ddgs`:

```python
        try:
            raw_results = list(DDGS().text(query, max_results=RESULTS_PER_QUERY))
        except Exception as e:
            from ddgs.exceptions import DDGSException, RatelimitException, TimeoutException
            if isinstance(e, RatelimitException):
                return [], FonteIndisponivel("rate_limit", f"DuckDuckGo: {e}")
            if isinstance(e, TimeoutException):
                return [], FonteIndisponivel("timeout", f"DuckDuckGo: {e}")
            if isinstance(e, DDGSException) and "no results" in str(e).lower():
                return [], None   # M5: "No results found." e resultado legitimo, nao falha
            return [], FonteIndisponivel("erro_interno", f"DuckDuckGo: {type(e).__name__}: {e}")
        return [{"url": r.get("href", ""), "title": r.get("title", ""), "snippet": r.get("body", "")} for r in raw_results], None
```

`_search_cse_api`: os `return [], "..."` viram `FonteIndisponivel`: 429 → `rate_limit`; 403 → `http_4xx`; `Timeout` → `timeout`; `RequestException` → `conexao` se `ConnectionError` senão `http_5xx`/`http_4xx` pelo `status_code` de `e.response` (404 → `endpoint_inexistente`); `Exception` → `erro_interno`. `_search_scraping`: `except Exception` → `erro_interno`. `_search_urls`: o "Nenhum backend" → `FonteIndisponivel("erro_interno", ...)`. Tipo de retorno das quatro: `tuple[list[dict], Optional[FonteIndisponivel]]`; docstrings ajustadas.

Laço de `search()`: `search_results, error_msg = ...` → `search_results, erro = ...`; `if error_msg:` → `if erro is not None:` gravando `motivo=erro.motivo, detalhe=erro.detalhe, error_message=str(erro)`. Após o corte `active_keywords = keywords[:MAX_GOOGLE_KEYWORDS]`, gravar `nao_consultada` para `keywords[MAX_GOOGLE_KEYWORDS:]` com detalhe `f"limite MAX_GOOGLE_KEYWORDS={MAX_GOOGLE_KEYWORDS} — palavra-chave não enviada à web aberta"`. O bloco de "possible blocking (scraping)" ganha `motivo="bloqueio_waf"`. ⚠ Conferir em `test_searchers.py`/`test_comprehensive.py` se algum teste afirma `_search_urls(...)[1] == ""` ou `error_message` literal do Google — adaptar no mesmo commit.

- [ ] **Step 4: Ver passar** — suíte `28`; `test_searchers` 13/13; `test_comprehensive` 98/98. BASELINE 28. Runner, golden. Commit `feat(frente2): Google/DDG entra no vocabulario — 'No results' e empty, nao error`. Push.

---

### Task 6: Origem da nota de relevância (`gemini_client.py`)

**Files:** `llm/gemini_client.py` (`:1-14` docstring de módulo; `:340-430`); `llm/__init__.py`; `test_llm_phase3.py`; `tools/run_all_tests.py`.

**Interfaces — Produces:** `score_relevance_com_origem(topic, results, keywords=None) -> list[tuple[float, str]]`; `score_relevance` inalterada (wrapper); ambas exportadas.

- [ ] **Step 1: Testes** — em `test_llm_phase3.py`, antes do `# Summary`, a seção 9 **exatamente como na v1 do plano** (10 `record`s: pares/heurística/fração/origens/sem-keywords/wrapper/lote vazio/lote válido/não numérico/tamanho errado). *(Texto integral na v1, commit `b1a6d3c`, Task 4 Step 1 — copiar dali; não muda.)*

- [ ] **Step 2: Ver falhar** — `Total: 54 | PASS: 53 | FAIL: 1`.

- [ ] **Step 3: Implementar** — renomear `score_relevance` → `score_relevance_com_origem` devolvendo `(nota, origem)` em cada ponto (heurística → `"heuristica"`; sem LLM e sem keywords → `(0.5, "fallback_erro")`; lote vazio / tamanho errado → `(0.5, "fallback_erro")` por item; valor não numérico → `(0.5, "fallback_erro")` só naquele item; numérico clampado → `"modelo"`); acrescentar o wrapper `score_relevance(...) -> list[float]`. Docstring da função nova com a tabela de origens. **M9:** docstring de módulo `:11` — `- score_relevance returns keyword-based heuristic scores or [0.5, ...]` vira `- score_relevance_com_origem returns (nota, origem): heuristica sem LLM (ou (0.5, "fallback_erro") sem keywords); score_relevance e o wrapper que descarta a origem`. `llm/__init__.py`: importar/exportar `score_relevance_com_origem`; docstring do pacote ganha a menção. ⚠ Não tocar as frases sobre Gemini/API key (B7, frente 5).

- [ ] **Step 4: Ver passar** — `Total: 63 | PASS: 63`. BASELINE 63. Runner, golden. Commit `feat(frente2): a nota de relevancia passa a dizer de onde veio`. Push.

---

### Task 7: `_merge` leva a origem da nota vencedora (invariante declarado)

**Files:** `deduplicator.py:98-113,147`; `test_phase4.py`; `tools/run_all_tests.py`.

- [ ] **Step 1: Testes** — os 3 de `TestMergeOrigem` da v1 (incoming maior leva origem; existing maior mantém; empate mantém existing).
- [ ] **Step 2: Ver falhar** (1 failed).
- [ ] **Step 3: Implementar**:

```python
    # Relevancia: keep higher score — e a ORIGEM da nota que venceu.
    # Invariante DECLARADO (M8 da rodada de 22/09): no app o dedup roda ANTES
    # da pontuacao, entao aqui todo item ainda e "padrao_fonte" e o efeito
    # pratico e nulo hoje. Existe para o dia em que a pontuacao vier antes
    # (ex.: nota por fonte), sem que a planilha diga "modelo" sobre uma nota
    # da heuristica.
    if incoming.relevancia > existing.relevancia:
        existing.relevancia = incoming.relevancia
        existing.relevancia_origem = incoming.relevancia_origem
```

Docstring: `- relevancia: keep the higher score, and relevancia_origem of whichever won (tie keeps existing)`.

- [ ] **Step 4: Ver passar** — `59 passed`. **Golden: `dedup_esperado.json` inalterado — obrigatório.** BASELINE 59. Commit `feat(frente2): _merge leva a origem da nota que venceu (invariante)`. Push.

---

### Task 8: Planilha — coluna "Origem da nota", aba "Diagnostico da busca", golden nas duas abas

**Files:** `excel_export.py` (`COLUMNS:75-87`; `_write_data_row:186-270`; `generate_excel:274-357`; função nova); `test_phase4.py` (`:421-447`; classes novas); `tools/golden_master.py`; `tests/golden/diagnostico_fixo.json` (novo), `planilha_sha256.txt`, `ambiente.txt`; `tools/run_all_tests.py`.

**Interfaces — Produces:** `COLUMNS` com 11 entradas (11ª = `("Origem da nota", 16, "relevancia_origem")`); `ORIGEM_LABEL`, `STATUS_LABEL`, `VAZIO = "—"`; `generate_excel(results, topic, diagnostico=None, quando=None) -> BytesIO`; aba `"Diagnostico da busca"` sempre presente; `wb.active` = `"Normativos"`.

- [ ] **Step 1: Testes** — em `test_phase4.py`:

(a) `TestExcelColumnCount`: `test_has_10_columns` → `test_has_11_columns` com `== 11`; `range(1, 11)` → `range(1, 12)` e `== 10` → `== 11` nos outros dois; `expected` ganha `"Origem da nota"`; docstring da classe `"""Verify all 11 expected columns are present."""`. ⚠ (M12) hoje só `test_has_10_columns` falha; os outros passam por omissão — atualizar os três mesmo assim.

(b) Classes novas:

```python
from models import KeywordStatus as _KS
from excel_export import ORIGEM_LABEL, STATUS_LABEL, VAZIO


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
        assert wb.sheetnames == ["Normativos", "Diagnostico da busca"]
        assert wb.active.title == "Normativos"
        assert wb["Diagnostico da busca"].cell(row=3, column=1).value == "Nenhum diagnóstico registrado nesta exportação"

    def test_aba_diagnostico_lista_vazia_igual_a_none(self):
        a = _load_workbook_from_buffer(generate_excel([_make_result()], "t", diagnostico=None))["Diagnostico da busca"]
        b = _load_workbook_from_buffer(generate_excel([_make_result()], "t", diagnostico=[]))["Diagnostico da busca"]
        assert a.cell(row=3, column=1).value == b.cell(row=3, column=1).value

    def test_aba_diagnostico_uma_linha_por_status_com_traco_no_vazio(self):
        diag = [
            _KS(keyword="lgpd", source="lexml", status="error", motivo="bloqueio_waf",
                detalhe="GET x -> 200 text/html", error_message="bloqueio"),
            _KS(keyword="lgpd", source="tcu", status="ok", result_count=4, parcial=True,
                detalhe="pagina 2 (inicio=20): http_5xx"),
            _KS(keyword="lgpd", source="google", status="empty"),
        ]
        wb = _load_workbook_from_buffer(generate_excel([_make_result()], "t", diagnostico=diag, quando="22/09/2026 10:00"))
        ws = wb["Diagnostico da busca"]
        assert "22/09/2026 10:00" in ws.cell(row=1, column=1).value
        assert [ws.cell(row=2, column=c).value for c in range(1, 9)] == [
            "Fonte", "Palavra-chave", "Status", "Motivo", "Detalhe", "Resultados", "Parcial", "Retentado"]
        linhas = [[ws.cell(row=r, column=c).value for c in range(1, 9)] for r in range(3, 6)]
        assert linhas[0] == ["lexml", "lgpd", "Indisponível", "bloqueio_waf", "GET x -> 200 text/html", 0, "Não", "Não"]
        assert linhas[1] == ["tcu", "lgpd", "OK", VAZIO, "pagina 2 (inicio=20): http_5xx", 4, "Sim", "Não"]
        assert linhas[2] == ["google", "lgpd", "Sem resultado", VAZIO, VAZIO, 0, "Não", "Não"]
        assert ws.cell(row=6, column=1).value is None

    def test_sem_quando_o_titulo_diz_nao_informado(self):
        ws = _load_workbook_from_buffer(generate_excel([], "t"))["Diagnostico da busca"]
        assert "não informado" in ws.cell(row=1, column=1).value


class TestRotulosSincronizados:
    def test_origem_label_cobre_o_vocabulario(self):
        assert set(ORIGEM_LABEL) == ORIGENS_RELEVANCIA

    def test_status_label_cobre_os_tres_status(self):
        assert set(STATUS_LABEL) == {"ok", "empty", "error"}
```

(8 novos; com o rename, `test_phase4` 59 → 67.)

- [ ] **Step 2: Ver falhar** — `1 + 8 failed` (M12).

- [ ] **Step 3: `excel_export.py`** — como na v1 (`COLUMNS` +1; `ORIGEM_LABEL`, `STATUS_LABEL`, `DIAGNOSTICO_SHEET`, `DIAGNOSTICO_COLUMNS`; ramo `relevancia_origem` em `_write_data_row`; `_write_diagnostico_sheet`; `generate_excel(..., diagnostico=None, quando=None)`; `wb.active = 0`), com estas diferenças:
  - `VAZIO = "—"` (B6): em `_write_diagnostico_sheet`, `s.motivo or VAZIO` e `(s.detalhe or s.error_message) or VAZIO`;
  - título: `f"Diagnóstico da busca: {topic} — {quando or 'data/hora não informada'}"`;
  - `redigir` **não** é chamada aqui — o `KeywordStatus` já redigiu no construtor (T1);
  - docstring de `generate_excel`: duas abas; `Args` com `diagnostico` e `quando` (`str` já formatado pelo chamador: a função é determinística para o golden).

- [ ] **Step 4: `tools/golden_master.py`** (M7):

```python
def _carregar_diagnostico() -> list:
    from models import KeywordStatus
    dados = json.loads((GOLDEN / "diagnostico_fixo.json").read_text(encoding="utf-8"))
    return [KeywordStatus(**d) for d in dados]


def _sha_planilha(itens: list) -> str:
    """... (docstring existente) ...

    Hasheia TODAS as abas (M7 da rodada de 22/09): a aba 'Diagnostico da busca'
    e o registro de que a fonte nao respondeu; sem ela no hash, uma regressao
    ali passaria com 'golden-master OK'. `quando` e fixo para o hash ser estavel.
    A funcao publica e generate_excel(results, topic, diagnostico=None, quando=None).
    """
    from excel_export import generate_excel
    from openpyxl import load_workbook

    wb = load_workbook(generate_excel(itens, topic="golden-master",
                                      diagnostico=_carregar_diagnostico(), quando="22/09/2026 00:00"))
    linhas = []
    for ws in wb.worksheets:
        linhas.append(("__aba__", ws.title))
        linhas.extend(tuple(c.value for c in linha) for linha in ws.iter_rows())
    return hashlib.sha256(repr(linhas).encode("utf-8")).hexdigest()
```

`tests/golden/diagnostico_fixo.json`:

```json
[
  {"keyword": "protecao de dados", "source": "lexml", "result_count": 0, "status": "error",
   "error_message": "bloqueio_waf", "motivo": "bloqueio_waf",
   "detalhe": "GET https://www.lexml.gov.br/busca/SRU?operation=searchRetrieve -> HTTP 200 text/html; título: Verificação de segurança — Senado Federal"},
  {"keyword": "protecao de dados", "source": "tcu", "result_count": 4, "status": "ok", "parcial": true,
   "detalhe": "pagina 2 (inicio=20): http_5xx: GET https://dados-abertos.apps.tcu.gov.br/api/acordao/recupera-acordaos?inicio=20 -> HTTP 500"},
  {"keyword": "LGPD", "source": "google", "result_count": 0, "status": "empty"}
]
```

- [ ] **Step 5: Ver passar** — `python -m pytest test_phase4.py -q` → `67 passed`.

- [ ] **Step 6: Recongelar no mesmo commit** — na raiz: `python tools/golden_master.py comparar` → **esperado `DIVERGIU: planilha divergiu`, e NENHUMA linha `dedup divergiu`** (se houver, parar: regressão). `python tools/golden_master.py congelar`; `comparar` **2×** → OK e sha idêntico. `git diff --stat tests/golden/` → só `planilha_sha256.txt` (+ `ambiente.txt` se mudou) + `diagnostico_fixo.json` novo; `dedup_esperado.json` **ausente**.

- [ ] **Step 7: BASELINE 67; runner; auditoria (golden_master docstring atualizada); commit**

```bash
git add levantamento-normativos/excel_export.py levantamento-normativos/test_phase4.py tests/golden/ tools/golden_master.py tools/run_all_tests.py
git commit -m "feat(frente2): planilha ganha 'Origem da nota' e a aba 'Diagnostico da busca'; golden cobre as duas abas

COLUMNS 10 -> 11. Aba de diagnostico sempre presente, com data/hora da
busca e traco explicito no campo vazio (openpyxl le '' como None).
GOLDEN-MASTER RECONGELADO DE PROPOSITO (spec §3.5 + M7): coluna nova e
hash de todas as abas com diagnostico_fixo.json. dedup_esperado.json
inalterado — conferido pelo ramo do dedup antes de recongelar.
test_phase4: 59 -> 67."
git push origin master
```

---

### Task 9: Tela — pontuar sempre, relatório honesto, avisos, card, preview, fonte que levanta

**Files:** `app.py` (`:24-26`; `:545-564` except; `:570-596` pontuação; `:840-905` relatório; `:907-946` step4; `:1049-1065` card; `:1195` export; `:1221-1232` preview); `tools/dirigir_app.py`; `.gitignore`.

- [ ] **Step 1: Imports** — `from models import KeywordStatus, NormativoResult, ORIGENS_RELEVANCIA, statuses_para_falha_total`; no topo, `ORIGEM_CURTA = {"modelo": "modelo", "heuristica": "heurística", "fallback_erro": "fallback", "padrao_fonte": "padrão da fonte"}` seguido de `assert set(ORIGEM_CURTA) == ORIGENS_RELEVANCIA` (M13).

- [ ] **Step 2: Fonte que levanta não some (H2)** — no `except Exception as e:` de `:556`, antes do `status_text.write`:

```python
                slug = {"LexML Brasil": "lexml", "TCU Dados Abertos": "tcu"}.get(source_name, "google")
                all_keyword_statuses.extend(statuses_para_falha_total(slug, keywords, e))
```

- [ ] **Step 3: Pontuação sempre** — como na v1 (Task 7 Step 1), **mais** a validação no ponto de atribuição (M8): `assert origem in ORIGENS_RELEVANCIA, origem` antes de `all_results[i].relevancia_origem = origem`.

- [ ] **Step 4: Relatório** — como na v1 (Task 7 Step 2), com `detalhe` renderizado por `st.code(s.detalhe or s.error_message, language=None)` em vez de `<small>` (M13); `parcial` com badge.

- [ ] **Step 5: Avisos (H3)** — em `render_step4`, antes do `if not results:`:

```python
    catalogadas = [s for s in kw_statuses if s.source in ("lexml", "tcu")]
    entregues = sum(s.result_count for s in catalogadas)
    indisponiveis = {s.source for s in catalogadas if s.status == "error" and s.motivo != "nao_consultada"}
    if catalogadas and entregues == 0 and indisponiveis:
        st.warning("Nenhuma fonte catalogada (LexML, TCU) entregou resultado nesta busca: "
                   f"{', '.join(sorted(indisponiveis))} indisponível(is). O que aparece abaixo vem só da web aberta. "
                   "Veja o relatório da busca.")
    elif indisponiveis:
        st.warning(f"Fonte(s) catalogada(s) parcialmente indisponível(is): {', '.join(sorted(indisponiveis))}. "
                   f"{entregues} resultado(s) vieram do que respondeu; o restante pode estar faltando. Veja o relatório.")
    if results and all(r.relevancia_origem == "heuristica" for r in results):
        st.caption("Sem LLM configurado, a relevância é a fração das palavras-chave presentes na ementa: "
                   "0% significa 'nenhuma palavra-chave na ementa', não 'irrelevante'.")   # M14
```

E a mensagem `st.error` do ramo `if not results:` como na v1.

- [ ] **Step 6: Card, preview, exportação** — card: `f"<b>Relevancia:</b> {relevancia_pct}% <i>({ORIGEM_CURTA[item.relevancia_origem]})</i> &middot; "`; preview: coluna `"Origem"`; exportação: `generate_excel(selected, topic, diagnostico=st.session_state.get("keyword_statuses", []), quando=datetime.now().strftime("%d/%m/%Y %H:%M"))` (import `datetime`).

- [ ] **Step 7: Gate visual V11** — `tools/dirigir_app.py` como na v1, com: `SAIDA = RAIZ / "tests" / "evidencia" / "v11_passo4.png"` (criar a pasta; `.gitignore` ganha `tests/evidencia/`); e os checks:

```python
    n_cards = texto.count("Ver detalhes")
    print("indisponíveis no relatório:", "indisponíveis" in texto)
    print("bloqueio_waf visível:", "bloqueio_waf" in texto)
    print("aviso coerente com o cenário:", ("entregou resultado" in texto) != ("parcialmente indisponível" in texto))
    print("origem no card:", any(o in texto for o in ("(heurística)", "(modelo)", "(fallback)")))
    print("'0 erros' NÃO aparece:", "0 erros" not in texto)
    print("cards == resultados (nada sumiu):", n_cards, "— conferir com o cabeçalho 'Passo 4 - Revisar Resultados (N normativos)'")
```

Rodar com o app no ar; **abrir o PNG**; os 5 booleanos `True`; a contagem de cards bate com o `N` do cabeçalho.

- [ ] **Step 8: Runner, golden, auditoria; commit** `feat(frente2): a tela diz 'indisponivel', avisa com precisao e mostra a origem da nota`. Push.

---

### Task 10: Fechar a frente

- [ ] Critérios de pronto da spec §7 (com os comandos e saídas no commit): 10 commits das tasks; runner TUDO VERDE sem `[AVISO] cresceu`; `golden_master.py comparar` OK e `git diff d054d5b -- tests/golden/dedup_esperado.json` vazio; V11 rodado de novo; auditoria dos 2 comandos sobre `dc99d73..HEAD`.
- [ ] Duráveis: `_TODO.md` (frente 2 ✅; F9 perde os achados que viraram código; P3 ganha "sanitizar ementa/nome contra fórmula na aba Normativos"); `log.md`; `SESSION-ONBOARD` §2/§6 (próxima: frente 5); `BLOCKED-ON-RODRIGO.md` B-04 (`✅ a UI e a planilha distinguem; TCU acórdãos voltaram a casar`); `LESSONS.md`: (1) fixture escrita à mão sobre esquema não capturado = falsa testemunha (B5); (2) falta captura real de SRU do LexML — capturar quando a fonte responder (M10).
- [ ] Commit `docs: fecha a frente 2`; push; `/checkpoint`.

---

## Self-review (v2)

**Cobertura da spec + emendas:** §3.1 → T1 · §3.2 → T2 · §3.3 → T3 · §3.4 → T6+T7+T9 · §3.5 → T8 · §3.6 → T9 · §3.7 → gates de golden (com a exceção declarada em T4) · §4 V1–V11 → T1..T9 · §5 → estrutura (+ google, tcu mapping) · §7 → T10. Emendas à spec: §3.1 (motivos; redigir), §3.7 (T4), §5 (T5), §3.5 (`quando`, `—`, golden nas 2 abas).
**Contagens:** T1 56 · T2 +13 · T3 20 (+1 xfail) · T4 24 · T5 28 · T6 63 · T7 59 · T8 67 · total final **13 + 63 + 98 + 67 + 28 = 269**. A tabela "BASELINE previsto" do topo bate com esta contagem.
**Placeholders:** nenhum; a T6 Step 1 remete ao texto literal da v1 (commit `b1a6d3c`) em vez de repetir 60 linhas — é referência a texto versionado, não "similar à Task N".
**Nomes:** `FonteIndisponivel(motivo, detalhe)` · `_search_keyword_safe -> (list, erro_fatal, erro_paginacao)` · `_fetch_all_pages -> (itens, erro, parcial)` · `_search_urls -> (list, erro)` · `score_relevance_com_origem -> list[tuple[float, str]]` · `generate_excel(results, topic, diagnostico=None, quando=None)` · `redigir(texto, limite=300)` · `statuses_para_falha_total(source, keywords, exc)`.

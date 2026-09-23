# T6 · Origem da nota de relevância — registro de implementação

> Task: `../tasks/06-origem-da-nota.md` (plano v4, linhas 2198-2326; o plano é a fonte de verdade).
> Trilha B (worktree `bn-trilha-b`, branch `frente2/trilha-b`), 23/09/2026.
> Commits: **`7d8f1ce`** `feat(frente2): a nota de relevancia passa a dizer de onde veio` ·
> **`6594cd8`** `fix(frente2): review da T6 — bool/NaN/Infinity do modelo viram fallback_erro`.
> Teste independente: **APROVADO**. Revisão de código: **APROVADO, sem bloqueador** (um achado importante
> corrigido na T6, outro adiado para a frente 5). Vereditos completos: `../execucao/revisoes/T6.md`.

## 1. O que foi feito

| Arquivo | Símbolos |
|---|---|
| `levantamento-normativos/llm/gemini_client.py` | `score_relevance` renomeada para **`score_relevance_com_origem(topic, results, keywords=None) -> list[tuple[float, str]]`**. Os 4 pontos que emitem nota agora rotulam a origem: sem LLM e com keywords → `"heuristica"`; sem LLM e sem keywords → `(0.5, "fallback_erro")`; lote vazio → `fallback_erro`; valor válido → `"modelo"`; valor não numérico → só aquele item vira `fallback_erro`; lote de tamanho errado → o lote inteiro vira `fallback_erro`. Docstring `Returns` reescrita com o texto do plano. Novo wrapper **`score_relevance`** (contrato antigo, `list[float]`), logo abaixo. Docstring de módulo (M9, linha 11) atualizada. Depois do review: `import math`, e `bool`/não-finitos rejeitados antes do clamp |
| `levantamento-normativos/llm/__init__.py` | importa e exporta `score_relevance_com_origem` (no `from .gemini_client import (...)` e no `__all__`). A docstring do pacote ganhou `(scores carry their origin: see score_relevance_com_origem)`. As frases sobre Gemini/API key não foram tocadas (emenda B7, frente 5) |
| `levantamento-normativos/test_llm_phase3.py` | seção 9 "Origem da nota de relevancia", verbatim do plano: 10 `record`s, antes do banner `# Summary`. Depois do review: +1 `record` (`'[NaN, true]'`) |
| `tools/run_all_tests.py` | só `BASELINE["test_llm_phase3.py"]`: 53 → 63 (`7d8f1ce`), depois 63 → 64 (`6594cd8`) |

O código dos blocos do plano foi colado como está. As mensagens de `logger.info` do ramo sem LLM viraram as do plano, em português. Os `logger.warning` em inglês dos lotes (`:411`, `:425`) foram mantidos: são pré-existentes, e o reviewer disse para deixá-los.

## 2. Desvios do plano e por quê

1. **Uma linha extra na docstring `Returns`.** O plano manda "reescrever a atual acrescentando" o bloco novo. O texto antigo (`List of float scores in [0.0, 1.0], same length and order as results.`) dizia o intervalo e o tamanho, e o bloco do plano não dizia. Para não perder essa informação, acrescentei `Notas em [0.0, 1.0]; mesmo tamanho que results.` **Aceito pelo reviewer.**
2. **Além do plano: `bool`, `NaN` e `Infinity` viram `fallback_erro`** (`6594cd8`). Achado do testador, que o reviewer classificou como importante e o orquestrador mandou corrigir na T6. `json.loads` aceita `true`/`false`, `NaN` e `Infinity`. Antes, `NaN` saía como `(1.0, "modelo")`, porque `min(1.0, nan)` dá 1.0: a nota máxima, rotulada como nota do modelo. `true` também saía como `(1.0, "modelo")`, porque `float(True)` dá 1.0. O defeito é pré-existente, mas a T6 passou a dizer que a nota era "do modelo". Correção: dentro do `try` do `for val in parsed:`, `isinstance(val, bool)` levanta `TypeError` e `not math.isfinite(score)` levanta `ValueError`, os dois antes do clamp. O `except (TypeError, ValueError)` que já existia faz o resto. **Efeito nas contagens:** `test_llm_phase3` fica em **64**, não nos 63 do plano, e todos os totais do plano a partir da T6 ficam +1 (T6 270, T7 273, T8 283, T9 284, somando as duas trilhas).
3. **Total do runner nesta trilha.** O plano prevê 269 após a T6, mas conta as duas trilhas (T2-T5 acrescentam `tests/test_fontes_indisponiveis.py`, da trilha A). Nesta worktree os searchers não mudaram, então o total aqui é 13+63+98+58 = **232** e, depois do review, **233**. O que tinha de bater com o plano era a suíte que a task mexe, e bateu: 54/53/1 → 63/63.
4. Sem push (o orquestrador faz).

## 3. Gates e saídas

### Implementador

- **Step 2, ver falhar** (em `levantamento-normativos/`, `python test_llm_phase3.py`):
  ```
  [FAIL] secao 9 (origem da nota) — Traceback (most recent call last):
    File "...\test_llm_phase3.py", line 283, in <module>
      from llm import score_relevance_com_origem
  ImportError: cannot import name 'score_relevance_com_origem' from 'llm'
    Total: 54  |  PASS: 53  |  FAIL: 1
  ```
- **Step 4, ver passar:** `Total: 63  |  PASS: 63  |  FAIL: 0`.
- **Runner `7d8f1ce`** (`python tools/run_all_tests.py`, raiz), exit 0:
  ```
  test_searchers.py     |     13 |      0 |       13 |  421.1s
  test_llm_phase3.py    |     63 |      0 |       63 |    2.7s
  test_comprehensive.py |     98 |      0 |       98 |  140.1s
  test_phase4.py        |     58 |      0 |       58 |    2.7s
  TUDO VERDE
  ```
- **Fix do review, TDD:** com a seção 9 já com o `record` novo e o `gemini_client.py` de `7d8f1ce`:
  ```
  [FAIL] NaN e bool do modelo -> fallback_erro — [(1.0, 'modelo'), (1.0, 'modelo')]
  Total: 64  |  PASS: 63  |  FAIL: 1
  ```
  Com o fix: `Total: 64  |  PASS: 64  |  FAIL: 0`. Sonda descartável: `[Infinity, -Infinity]` → dois `(0.5, 'fallback_erro')`; `[false, 0.3]` → `(0.5, 'fallback_erro'), (0.3, 'modelo')`; `[1.5, -2]` → `(1.0, 'modelo'), (0.0, 'modelo')`. O clamp continua valendo para números finitos.
- **Runner `6594cd8`** (`timeout 900 python -u tools/run_all_tests.py`, foreground), exit 0:
  ```
  test_searchers.py     |     13 |      0 |       13 |  400.8s
  test_llm_phase3.py    |     64 |      0 |       64 |    2.6s
  test_comprehensive.py |     98 |      0 |       98 |  137.9s
  test_phase4.py        |     58 |      0 |       58 |    2.6s
  TUDO VERDE
  ```
- `python tools/golden_master.py comparar` → `golden-master OK`, nos dois commits.
- **`git grep -n 'score_relevance\b' -- '*.py'`:**
  - Os hits previstos: o wrapper (`gemini_client.py:438`), `__init__.py:8/19/26`, `app.py:582` (a T9 troca) e os testes (`test_comprehensive.py:926/1032/1033/1042`, `test_llm_phase3.py`).
  - Dois hits a mais, os dois só texto: `gemini_client.py:11`, a linha da docstring de módulo que o próprio M9 pede; e `tools/split_frente2.py:107`, uma string que cita o critério de aceite.

### Auditoria de documentação (os 2 comandos das Global Constraints, lidos inteiros)

`git diff -U0 HEAD~1 -- '*.py' | grep '^-' | grep -v '^---'`:

- **Em `7d8f1ce`, 21 linhas.** Todas têm destino:

| Linha removida | Destino |
|---|---|
| `Provides keyword expansion, relevance scoring, and auto-categorization` (pacote) | a mesma frase, com `(scores carry their origin: see score_relevance_com_origem)` |
| `- score_relevance returns keyword-based heuristic scores or [0.5, ...]` (módulo) | a linha M9 do plano |
| `def score_relevance(` / `) -> list[float]:` | `score_relevance_com_origem` / `list[tuple[float, str]]`; o nome e o tipo antigos vivem no wrapper |
| `List of float scores in [0.0, 1.0], same length and order as results.` | o bloco `Returns` do plano + `Notas em [0.0, 1.0]; mesmo tamanho que results.` (desvio 1) |
| os 2 `logger.info("Gemini unavailable …")` | as mensagens do plano, em português |
| as demais (list comprehension, `[0.5] * len(...)`, `score = float(val)`/clamp/`score = 0.5`/`append`, `all_scores: list[float]`) | o código do plano que rotula a origem |
| `"test_llm_phase3.py": 53,` | 63 |

- **Em `6594cd8`, 2 linhas:** `score = max(0.0, min(1.0, float(val)))`, que virou as validações de bool/não-finito + o mesmo clamp; e `"test_llm_phase3.py": 63,`, que virou 64. Nenhum comentário nem docstring foi removido. O fix acrescentou um comentário dizendo por que valida.

`git grep -n -E 'score_relevance|…|rotulo_status' -- '*.py'`: a única assinatura que mudou é a da função renomeada. Os call sites do nome antigo são `app.py:582` e `test_comprehensive.py:926/1033/1042`, e todos usam o wrapper, que tem o contrato antigo. Nenhum precisa de adaptação nesta task.

### Tester independente (coder B)

- **Suíte:** antes (`7d8f1ce~1` via `git archive` + teste novo) `54/53/1`, e a falha é a seção 9 com `ImportError`. Depois, `63/63`.
- **Gates:** runner 232 TUDO VERDE, golden OK, `git grep` só nos pontos previstos. M9 e a docstring do pacote OK; B7 intacto; line endings OK.
- **Sondas, todas OK:** resultados vazios; keywords `[]`/`None`; ementa ausente; cercas markdown; clamp [0,1]; listas aninhadas; `null` por item. Também 3 lotes, um vazio e um de tamanho errado: só o lote afetado vira `fallback_erro`. Toda origem está em `ORIGENS_RELEVANCIA`, e o wrapper devolve só as notas.
- **Travamento:** o 1º runner do tester, em background, saiu com log vazio (causa desconhecida; talvez concorrência com o e2e). Refeito em foreground com `timeout 590`, passou.

### Evidência e2e (tester)

- Playwright, porta 8521, `channel="chrome"`. O app chegou em **"Passo 4 - Revisar Resultados (15 normativos)"** sem exceção. Os cards mostram "Relevancia: 30%": sem LLM o app ainda não pontua pela função nova, e isso é da T9. O Excel exportou 17 linhas.
- Screenshots `tests/evidencia/t6_passo4.png` e `tests/evidencia/t6_passo5.png`, **não versionados**.
- A T6 não muda nada visível. `app.py` ainda chama o wrapper e a coluna "Origem da nota" é da T8. O e2e prova que nada quebrou.

## 4. Achados de teste e revisão, e para onde foram

| # | Achado | Origem | Destino |
|---|---|---|---|
| 1 | `[true, false]` vira `(1.0, modelo), (0.0, modelo)`, porque `float(bool)` funciona | tester (pré-existente) | **Corrigido na T6** (`6594cd8`, desvio 2) |
| 2 | `[NaN]` vira `(1.0, modelo)`, porque `min(1.0, nan)` = 1.0; `Infinity` também escapa | tester (pré-existente) + reviewer | **Corrigido na T6** (`6594cd8`) + `record` `'[NaN, true]'` |
| 3 | `ementa: None` levanta `TypeError` em `gemini_client.py:384` (`r.get('ementa','')[:200]`) e em `categorize_results` (`:476`), só com LLM ligado. Isso contradiz a docstring "never raises". `ementa` pode chegar `None`: TCU com `null`, `snippet` do Google | tester + reviewer (pré-existente) | **Adiado para a frente 5** (o orquestrador registra em `_TODO.md`). Conserto indicado pelo reviewer: `(r.get('ementa') or '')[:200]` e `r.get('nome') or ''` + teste com `_generate` dublado |
| 4 | Logs em inglês "Gemini returned empty response…" / "Using 0.5 fallback" em `:411/:425` | reviewer (menor, pré-existente) | Deixados como estão, por decisão do reviewer |
| 5 | Linha extra na docstring `Returns` (desvio 1) | implementador | Aceito pelo reviewer |
| 6 | `score_relevance\b` casa em `tools/split_frente2.py:107` | tester | Inofensivo (string); sem ação |

## 5. Armadilha de ambiente: `sed -i` troca CRLF por LF

Os arquivos são CRLF no working tree (`core.autocrlf=true`). Um `sed -i 's/…\r$/…\r/'` no Git Bash **regravou `gemini_client.py` inteiro em LF** e **não aplicou** a substituição. `file` passou a dizer só "UTF-8 text", sem "with CRLF line terminators", e o git avisou `LF will be replaced by CRLF`. Conserto: refiz a edição em Python, lendo e gravando com `open(..., encoding="utf-8", newline="")`, e confirmei com `file` depois de cada edição.

**Regra daqui em diante:** nesta árvore, editar por Python com `newline=""`, ou pela ferramenta Edit, nunca por `sed -i`. Conferir com `file` após editar.

## 6. Regras respeitadas

Não criei `secrets.toml` (só existe o `.example`). Nenhum teste novo faz rede ou chama LLM: a seção 9 dubla `is_available`/`_generate` e restaura os dois no `finally`. A branch `deploy`, `execucao/*` e `_TODO.md` ficaram intocados. `tests/` da raiz não foi versionado. O push fica com o orquestrador.

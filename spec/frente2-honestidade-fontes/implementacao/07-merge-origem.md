# T7 · `_merge` leva a origem da nota vencedora — registro de implementação

> Task: `../tasks/07-merge-origem.md` (plano v4, linhas 2330-2377; o plano é a fonte de verdade).
> Trilha B (worktree `bn-trilha-b`, branch `frente2/trilha-b`), 23/09/2026.
> Commit de código: **`7d5e69b`** `feat(frente2): _merge leva a origem da nota que venceu (invariante)`.
> Teste independente: **APROVADO, sem defeito**. Revisão de código: **APROVADO, "nada a corrigir"**.
> Vereditos completos: `../execucao/revisoes/T7.md`.

## 1. O que foi feito

| Arquivo | Símbolos |
|---|---|
| `levantamento-normativos/deduplicator.py` | docstring de `_merge` (`:105`): `- relevancia: keep the higher score` → `- relevancia: keep the higher score, and relevancia_origem of whichever won (tie keeps existing)`. Corpo (`:146-154`): `existing.relevancia = max(existing.relevancia, incoming.relevancia)` trocado pelo bloco do plano, `if incoming.relevancia > existing.relevancia:` leva nota **e** `relevancia_origem`, com o comentário de 6 linhas do invariante, literal |
| `levantamento-normativos/test_phase4.py` | `TestMergeOrigem` (3 testes, verbatim): o incoming maior leva sua origem; o existing maior mantém a sua; no empate fica o existing |
| `tools/run_all_tests.py` | só `BASELINE["test_phase4.py"]`: 58 → 61 |

## 2. O invariante, e por que o efeito é nulo hoje

No app, `app.py:568` **deduplica antes** de `app.py:582` **pontuar**. Quando `_merge` roda, todo item ainda tem a nota da fonte e `relevancia_origem = "padrao_fonte"`. Levar "a origem da nota que venceu" não muda nada na prática. O invariante existe para o dia em que a pontuação vier antes do dedup (ex.: nota por fonte). Nesse dia, a planilha não pode dizer "modelo" sobre uma nota que veio da heurística. O comentário no código diz exatamente isso (M8 da rodada de 22/09).

A nota em si continua igual ao `max()` antigo. Em empate fica o existing, e o valor é o mesmo. O reviewer conferiu que vale inclusive com NaN.

## 3. Desvios do plano e por quê (aceitos pelo reviewer)

1. **Onde ficaram os testes.** O plano diz "ao fim de `test_phase4.py`". A classe entrou **antes** do banner final `# Run via pytest or direct execution` / `if __name__ == "__main__"`, a mesma posição aceita na T1. Conteúdo idêntico.
2. **`deduplicator.py` deixou de ser ASCII puro e virou UTF-8.** O comentário do plano tem um travessão (`—`), e mantive o texto literal. O tester confirmou que o módulo importa até com `-X utf8=0`.
3. **Total do runner.** O header da task cita 272, a soma das duas trilhas. Nesta trilha o total é 13+64+98+61 = **236**. O `test_llm_phase3` está em 64 por causa do `record` extra do review da T6. A suíte da task (`test_phase4`) bateu com o plano: 61.
4. Sem push (o orquestrador faz).

## 4. Gates e saídas

### Implementador

- **Step 2, ver falhar** (em `levantamento-normativos/`, `python -m pytest test_phase4.py -q -k MergeOrigem`):
  ```
  >       assert (a.relevancia, a.relevancia_origem) == (0.9, "modelo")
  E       AssertionError: assert (0.9, 'padrao_fonte') == (0.9, 'modelo')
  FAILED test_phase4.py::TestMergeOrigem::test_incoming_maior_leva_sua_origem
  1 failed, 2 passed, 58 deselected in 0.61s
  ```
  É o "1 failed" do plano. Os outros dois passam já no código antigo, porque manter o existing era o comportamento de antes.
- **Step 4, ver passar:** `61 passed in 1.29s`.
- **Runner** (`timeout 900 python -u tools/run_all_tests.py`, foreground), exit 0:
  ```
  test_searchers.py     |     13 |      0 |       13 |  401.9s
  test_llm_phase3.py    |     64 |      0 |       64 |    2.8s
  test_comprehensive.py |     98 |      0 |       98 |  137.9s
  test_phase4.py        |     61 |      0 |       61 |    2.4s
  TUDO VERDE
  ```
- **Golden:** `python tools/golden_master.py comparar` → `golden-master OK`. `git diff --stat -- tests/golden/` vazio: **`dedup_esperado.json` inalterado**, como é obrigatório.

### Auditoria de documentação (os 2 comandos das Global Constraints, lidos inteiros)

`git diff -U0 HEAD~1 -- '*.py' | grep '^-' | grep -v '^---'` → 4 linhas removidas, todas com destino:

| Linha removida | Destino |
|---|---|
| `- relevancia: keep the higher score` (docstring) | a mesma frase, estendida com a regra da origem e do empate |
| `# Relevancia: keep higher score` | `# Relevancia: keep higher score — e a ORIGEM da nota que venceu.` + o comentário do invariante |
| `existing.relevancia = max(existing.relevancia, incoming.relevancia)` | o bloco `if` (a nota fica igual ao `max`) |
| `"test_phase4.py": 58,` | 61 |

- **`git grep` dos símbolos das Global Constraints:** a T7 não muda a assinatura de nenhum deles.
- **`git grep -E '_merge\b|relevancia_origem'`:** a assinatura de `_merge` não mudou. Os call sites em `deduplicate` (`:239/:253/:282`) e as referências em `tools/golden_master.py` (`:40/:107/:132`) ficam como estão.

### Tester independente (coder B)

- `test_phase4` 61. Antes (`7d5e69b~1`, numa cópia): `-k MergeOrigem` → 1 failed (`test_incoming_maior_leva_sua_origem`) + 2 passed.
- Runner em foreground 236 TUDO VERDE (13/64/98/61); golden OK; `tests/golden/` intocado.
- **Sondas:** 23/23 nas 3 estratégias do dedup (2 e 3 vias). Depois, um teste **exaustivo** de 3 estratégias × 4³ notas × 4³ origens, **12.288 combinações**. Em todas:
  - sai sempre 1 item;
  - a origem está no vocabulário;
  - a origem é a do **primeiro** máximo (empate mantém o existing);
  - todos os outros campos ficam idênticos aos do `deduplicate` pré-T7.
- **Entrada do golden:** saída idêntica à de antes da T7, tudo `padrao_fonte`. É o efeito nulo, medido.

### Evidência e2e (tester)

- Playwright, porta 8521, `channel="chrome"`. O app chegou em **"Passo 4 - Revisar Resultados (16 normativos)"**, com 16 cards, e o Excel saiu com 16 linhas, sem exceção.
- Screenshots `tests/evidencia/t7_passo4.png` e `tests/evidencia/t7_passo5.png`, **não versionados**.
- A T7 não muda nada visível (efeito nulo hoje). O e2e prova que nada quebrou.

## 5. Achados de teste e revisão, e para onde foram

| # | Achado | Origem | Destino |
|---|---|---|---|
| 1 | O comentário "o efeito pratico e nulo hoje" poderia dizer "sobre a origem" | reviewer (menor) | **Não aplicado**, por decisão do orquestrador: o plano manda o texto literal |
| 2 | O header da task cita total 272 (duas trilhas); na trilha B vale 236 | tester (obs.) | Registrado aqui (desvio 3); sem ação |
| 3 | `deduplicator.py` agora é UTF-8 | tester/reviewer | Aceito (desvio 2); importa com `-X utf8=0` |

Nenhum defeito.

## 6. Regras respeitadas

Edições por Python com `newline=""`: CRLF preservado, conferido com `file`. Nenhum teste novo faz rede ou chama LLM. `dedup_esperado.json` intocado. A branch `deploy`, `execucao/*` e `_TODO.md` ficaram intocados. `tests/` da raiz não foi versionado. O push fica com o orquestrador.

# T8 · Planilha: coluna "Origem da nota", aba "Diagnostico da busca", golden nas duas abas — registro de implementação

> Task: `../tasks/08-planilha-diagnostico.md` (plano v4, linhas 2381-2628; o plano é a fonte de verdade).
> Trilha B (worktree `bn-trilha-b`, branch `frente2/trilha-b`), 23/09/2026.
> Commits: **`6178f9d`** `feat(frente2): planilha ganha 'Origem da nota' e a aba 'Diagnostico da busca'; golden cobre as duas abas`
> (**recongela o golden, de propósito, no mesmo commit**) ·
> **`04b2947`** `fix(frente2): review da T8 — docstrings do golden e comentario do redigir` (só comentários, sem recongelar).
> Teste independente: **APROVADO, sem defeito**. Revisão de código: **APROVADO**, com 3 menores só de comentário, aplicados.
> Vereditos completos: `../execucao/revisoes/T8.md`.

## 1. O que foi feito

| Arquivo | Símbolos |
|---|---|
| `levantamento-normativos/excel_export.py` | **3a:** `from typing import Optional`; `from models import KeywordStatus, NormativoResult, redigir, rotulo_status`. **3b:** `COLUMNS` 10 → 11, `("Origem da nota", 16, "relevancia_origem")` com o comentário `⚠` sobre `len(COLUMNS)`. **3c:** `ORIGEM_LABEL`, `STATUS_LABEL = rotulo_status` (único lugar, R2-B6), `VAZIO = "—"`, `DIAGNOSTICO_SHEET`, `DIAGNOSTICO_COLUMNS`. **3d:** ramo `relevancia_origem` em `_write_data_row` + item na docstring. **3e:** `_write_diagnostico_sheet(wb, topic, diagnostico, quando)` verbatim, sob um banner `# Helper: Diagnostico sheet`. **3f:** `generate_excel(results, topic, diagnostico=None, quando=None)`, com docstring de duas abas + `Args`; chama `_write_diagnostico_sheet` e depois `wb.active = 0` antes de salvar |
| `levantamento-normativos/test_phase4.py` | (a) `TestExcelColumnCount` para 11 (docstring, `test_has_11_columns`, `range(1, 12)`, `== 11`, `"Origem da nota"` no `expected`). (b) `TestExcelHonestidade` (8) + `TestRotulosSincronizados` (2), verbatim |
| `tools/golden_master.py` | `_carregar_diagnostico()`; `_sha_planilha` hasheia **todas** as abas (marcador `("__aba__", título)`), com `diagnostico_fixo.json` e `quando="22/09/2026 00:00"` fixos; docstring nova (M7) |
| `tests/golden/diagnostico_fixo.json` | **novo**, 5 linhas verbatim: error com motivo+detalhe; ok parcial; empty; `nao_consultada`; error retentado só com `error_message` |
| `tests/golden/planilha_sha256.txt` | recongelado: `2003b1cc7fd1…` → `c7a5dd5796db…` |
| `tools/run_all_tests.py` | só `BASELINE["test_phase4.py"]`: 61 → 71 |

`dedup_esperado.json` e `ambiente.txt` **não mudaram**.

## 2. Desvios do plano e por quê (todos aceitos pelo reviewer)

1. **Docstring de `_sha_planilha`: explicações restauradas.** O texto do plano, que substitui o antigo, perdia quatro explicações. No `6178f9d` restaurei duas: "o risco pior nao e o falso vermelho, e o executor apagar a prova para destravar a task" e "load_workbook e a mesma tecnica que test_phase4.py ja usa". No `04b2947` (review M1) restaurei as outras duas: "tres revisores **independentes**" e "DIVERGIU **na sequencia imediata**".
2. **Docstrings de módulo atualizadas além da lista do plano.** Só acréscimos:
   - `golden_master.py`, item 2: agora diz que o hash cobre todas as abas e cita `diagnostico_fixo.json`.
   - `excel_export.py`: ganhou um item para a segunda aba. Sem isso, a docstring do módulo descreveria uma planilha de uma aba só.
3. **Comentário `# Sheet 2` antes de `_write_diagnostico_sheet(...)`.** Transforma em comentário a nota em prosa do plano ("`redigir` não é chamada aqui"). O review M3 corrigiu a frase, porque a função redige `source`/`keyword`. Agora diz: "redigir NAO e reaplicada a detalhe/error_message: o KeywordStatus ja redigiu (source/keyword sao redigidos dentro da funcao)".
4. **Posições.** O comentário `⚠` da 3b ficou inline na entrada nova de `COLUMNS`. As classes novas entraram antes do banner final `__main__` (mesma posição da T1/T7). `test_header_row_has_10_columns` **mantém o nome**: o plano só troca o `range` e a contagem. O rename opcional do reviewer não foi aplicado, por decisão do orquestrador.
5. **`diagnostico_fixo.json` em CRLF**, como os outros JSON do golden (`entrada_fixa.json`, `dedup_esperado.json`). O conteúdo é o do plano, verbatim. O tester confirmou que o CRLF não mexe no sha.
6. **Total do runner nesta trilha:** 13+64+98+71 = **246**. O plano diz 282 porque soma as duas trilhas. O `test_llm_phase3` está em 64 por causa do record extra do review da T6. A suíte da task bateu com o plano: 71.
7. **Revisão M2 (imprecisão vinda do plano).** O parágrafo `⚠` dizia que `ORIGEM_LABEL` entrava no hash "da aba de diagnostico". Na verdade, `ORIGEM_LABEL` alimenta a aba **Normativos**. Texto novo: "O hash da planilha depende de models.redigir e rotulo_status (aba de diagnostico), de excel_export.ORIGEM_LABEL (aba Normativos), de VAZIO e do titulo com `quando` fixo…".

## 3. Gates e saídas

### Implementador

- **Step 2, ver falhar** (em `levantamento-normativos/`, `python -m pytest test_phase4.py -q`). A falha é na coleta, e nenhum teste roda:
  ```
  test_phase4.py:706: in <module>
      from excel_export import ORIGEM_LABEL, VAZIO, DIAGNOSTICO_SHEET
  E   ImportError: cannot import name 'ORIGEM_LABEL' from 'excel_export'
  !!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
  1 error in 0.68s
  ```
- **Checagem intermediária (M12), com só 3a e 3c aplicados:** `11 failed, 60 passed`. O total bate com o "1 + 10" do plano, mas a composição é outra:
  - Os **3** testes de contagem falham: depois do Step 1(a), os três esperam 11 colunas, e ainda há 10.
  - **8** dos testes novos falham.
  - Os 2 de `TestRotulosSincronizados` já passam só com as constantes da 3c.

  A nota M12 ("hoje só `test_has_10_columns` falha") descreve os testes **antes** do Step 1(a). O arquivo tem 71 funções de teste, como o plano prevê.
- **Step 5, ver passar:** `71 passed in 1.81s`. Depois do fix do review: `71 passed in 1.71s`.
- **Step 6, recongelar** (na raiz), sequência completa:
  ```
  (planilha_sha256.txt antes: 2003b1cc7fd1d7a9f99225a893c02baf3b7eb3411dde04209d866423917eceb0)
  --- comparar (antes)
  DIVERGIU: planilha divergiu: 2003b1cc7fd1 -> c7a5dd5796db
  Ambiente do congelamento: python=3.13.7 openpyxl=3.1.5 | Agora: python=3.13.7 | openpyxl=3.1.5
  1 divergencia(s)                                  exit=1
  --- congelar
  congelado em C:\Users\Rodrigo\Documents\solucoes\bn-trilha-b\tests\golden   exit=0
  --- comparar 1
  golden-master OK                                  exit=0
  --- comparar 2
  golden-master OK                                  exit=0
  --- sha: c7a5dd5796db6c1d7fc886cb2b3934225d3aa7790769402ef4e0e40a959e0919
      (_sha_planilha calculado direto 2x: o mesmo sha nas duas)
  --- git diff --stat -- tests/golden/
   tests/golden/diagnostico_fixo.json | 12 ++++++++++++
   tests/golden/planilha_sha256.txt   |  2 +-
  ```
  - **Nenhuma linha `dedup divergiu`.**
  - `dedup_esperado.json` e `ambiente.txt` **ausentes** do diff. O `congelar` regravou o `dedup_esperado.json` com conteúdo idêntico.
- **Conferência da planilha do golden** (dump via openpyxl):
  - abas `['Normativos', 'Diagnostico da busca']`, e a ativa é `Normativos`;
  - K2 = "Origem da nota", K3 = "Padrão da fonte";
  - título "Diagnóstico da busca: golden-master — 22/09/2026 00:00";
  - as 5 linhas dizem Indisponível / OK + Parcial Sim / Sem resultado com `—` / Não consultada / Indisponível + Retentado Sim.
- **Runner `6178f9d`** (`timeout 900 python -u tools/run_all_tests.py`, foreground), exit 0:
  ```
  test_searchers.py     |     13 |      0 |       13 |  397.4s
  test_llm_phase3.py    |     64 |      0 |       64 |    3.1s
  test_comprehensive.py |     98 |      0 |       98 |  139.4s
  test_phase4.py        |     71 |      0 |       71 |    2.9s
  TUDO VERDE
  ```
- **Fix do review (`04b2947`), só comentários:**
  - `comparar` → `golden-master OK`.
  - `_sha_planilha` calculado direto dá `c7a5dd5796db…`, igual ao congelado. Isso prova que comentário não move o sha.
  - `test_phase4` 71. O runner não foi re-rodado: não houve mudança de código.

### Auditoria de documentação (os 2 comandos das Global Constraints, lidos inteiros)

**Em `6178f9d`:** `git diff -U0 HEAD~1 -- '*.py' | grep '^-' | grep -v '^---'`, 21 linhas, todas com destino:

| Linha removida | Destino |
|---|---|
| `from models import NormativoResult` | import estendido (3a) |
| `def generate_excel(results: list[NormativoResult], topic: str) -> BytesIO:` | assinatura multilinha com `diagnostico=None, quando=None` |
| `The workbook contains a single sheet named 'Normativos' with:` | "two sheets: 'Normativos' (active) and 'Diagnostico da busca'", e a lista antiga continua sob "'Normativos' has:" |
| as 6 linhas de `TestExcelColumnCount` (docstring, nome, `== 10`, `range(1, 11)` ×2) | as mesmas, para 11 (Step 1a) |
| item 2 da docstring de módulo do `golden_master.py` | estendido (desvio 2) |
| docstring antiga de `_sha_planilha` (7 linhas) | o texto do plano + as 4 explicações restauradas (desvio 1) + o ponteiro para a assinatura nova |
| as 2 linhas que hasheavam uma aba só | o laço sobre `wb.worksheets` |
| `"test_phase4.py": 61,` | 71 |

**Em `04b2947`:** 8 linhas removidas, todas substituídas pelo texto corrigido (M1/M2/M3, acima). Nada se perdeu.

`git grep` dos símbolos (Global Constraints). `generate_excel` mudou de assinatura, mas os parâmetros novos são opcionais:
- os call sites `app.py:1196` (2 argumentos; a T9 passa `diagnostico=`/`quando=`), `test_comprehensive.py` e `test_phase4.py` continuam valendo;
- `golden_master.py` foi atualizado, na docstring e na chamada;
- `rotulo_status` só entra via `STATUS_LABEL` (`excel_export.py:100`).

### Tester independente (coder B)

- `test_phase4` 71; runner foreground 246 TUDO VERDE; `comparar` 2× OK, com o sha `c7a5dd57…` igual ao congelado; `ambiente.txt` igual.
- **Re-derivação independente do recongelamento** (árvore pré-T8 via `git archive`):
  - `dedup_esperado.json` byte-idêntico.
  - A lógica **nova** do dedup contra o arquivo congelado **antigo** → OK, 11/11.
  - Só `planilha_sha256.txt` e `diagnostico_fixo.json` mudaram.
- **Prova mais forte:** tirando a coluna 11, a aba `Normativos` nova é igual à antiga linha a linha. O hash dela, calculado do jeito antigo, reproduz exatamente o sha pré-T8 (`2003b1cc7fd1`). A única mudança na aba é a coluna nova ("Padrão da fonte").
- Mutar 1 célula em cada aba muda o sha, então o hash cobre as duas abas. O CRLF do `diagnostico_fixo.json` não mexe no sha.
- **Sondas 32/32:**
  - placeholder igual com `None` e com `[]`;
  - fórmula neutralizada (nenhuma célula do tipo `f`);
  - caracteres de controle removidos;
  - detalhe de 2000 chars inteiro;
  - Sim/Não e rótulos;
  - freeze `A3`, filtro `A2:H6`;
  - `Normativos` ativa;
  - a planilha reabre sem aviso, e `testzip()` OK.

### Evidência e2e (tester)

- Playwright, porta 8521, `channel="chrome"`. O app chegou em **"Passo 4 - Revisar Resultados (14 normativos)"** sem exceção.
- O Excel exportado tem as 2 abas. K2 = "Origem da nota", e as 14 linhas dizem "Padrão da fonte". A aba de diagnóstico mostra o placeholder, e o título diz "— data/hora não informada". Isso é o esperado: o app só passa `diagnostico=`/`quando=` na T9.
- Screenshots `tests/evidencia/t8_passo4.png` e `tests/evidencia/t8_passo5.png`, mais `t8_export.xlsx` e `t8_probe.xlsx`. Nada disso é versionado.

## 4. Achados de teste e revisão, e para onde foram

| # | Achado | Origem | Destino |
|---|---|---|---|
| 1 | A docstring de `_sha_planilha` perdeu "independentes" e "na sequencia imediata" | tester (1) + reviewer M1 | **Corrigido** em `04b2947` |
| 2 | O parágrafo `⚠` atribuía `ORIGEM_LABEL` à aba de diagnóstico | reviewer M2 (imprecisão do plano) | **Corrigido** em `04b2947` |
| 3 | O comentário `# Sheet 2` dizia "redigir NAO e chamada aqui", mas a função redige `source`/`keyword` | reviewer M3 | **Corrigido** em `04b2947` |
| 4 | `test_header_row_has_10_columns` afirma 11 | reviewer (opcional) | **Não aplicado**, por decisão do orquestrador: o plano não renomeia |
| 5 | Sem diagnóstico, a aba não ganha freeze/filtro | tester (2) | Nada a fazer: é o que o plano manda, e é irrelevante com uma linha só |
| 6 | `motivo` é escrito sem `redigir` | tester (3) | Nada a fazer: é seguro, porque `motivo` vem do vocabulário fechado `MOTIVOS`, validado no construtor |

Nenhum defeito. Nenhum achado muda o conteúdo do xlsx, então não houve recongelamento extra.

## 5. Regras respeitadas

Edições por Python com `newline=""`: CRLF preservado, conferido com `file`. Nenhum teste novo faz rede ou chama LLM. `dedup_esperado.json` inalterado. De `tests/` na raiz, só `tests/golden/` foi versionado; `tests/evidencia/` não. A branch `deploy`, `execucao/*` e `_TODO.md` ficaram intocados. O push fica com o orquestrador.

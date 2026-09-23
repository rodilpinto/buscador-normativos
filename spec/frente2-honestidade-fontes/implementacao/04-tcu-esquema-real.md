# T4 · TCU lê o esquema REAL do acórdão — registro de implementação

> Task: `../tasks/04-tcu-esquema-real.md` (plano v4, linhas 1768-1873 — o plano é a fonte de verdade; a cópia da task
> foi conferida contra o plano por `diff`: idêntica). ⚠ Emenda à spec §3.7.
> Trilha A, worktree `bn-trilha-a`, branch `frente2/trilha-a`, 23/09/2026.
>
> Commits:
> - **`e960497`** `fix(frente2): TCU le o esquema REAL do acordao (…)` — o plano.
> - **`bdd89a1`** `fix(frente2): T4 — acordaos de colegiados diferentes nao colidem (id e dedup)` — conserto do defeito
>   que **reprovou** a T4 no teste.
> - **`38a110d`** `fix(frente2): review da T4 — docstrings, spec 3.7 anotada, orgao_emissor sem colegiado`.
>
> Teste: **REPROVADO** em `e960497` (1 defeito); **APROVADO** no re-teste de `bdd89a1`. Revisão: **APROVADO**, sem
> bloqueador. Vereditos completos: `../execucao/revisoes/T4.md`.

## 1. O que foi feito

| Arquivo | Símbolos |
|---|---|
| `levantamento-normativos/searchers/tcu_searcher.py` | `_texto_do_acordao` (sumario + titulo, fallback `ementa`); `_map_acordao` com o esquema real, todo campo literal da API: `nome ← titulo`, `ementa ← sumario`, `data ← dataSessao` (precedência invertida; vazio `""`), `link ← urlAcordao` (fallback `_build_acordao_link`), `situacao` literal, chaves antigas como fallback. `numero ← "numeroAcordao/anoAcordao-TCU-<colegiado>"` (`bdd89a1`). `colegiado` nulo vira `""`, e `orgao_emissor` fica "TCU" (`38a110d`). Docstrings de `search()`, `_fetch_all_pages`, `_texto_do_acordao` e `_map_acordao` atualizados |
| `levantamento-normativos/models.py` | docstring de `situacao` (admite o valor literal da fonte, ex. "OFICIALIZADO"); docstring de `numero` (exemplo do TCU; o `id` é montado de `numero`) |
| `levantamento-normativos/tests/test_fontes_indisponiveis.py` | xfail removido (vira passed); `== 0` → `== 1` no teste do 500; 3 testes do plano; **3 além do plano**: 2 de colegiados (`bdd89a1`) e 1 de `colegiado` nulo (`38a110d`) |
| `levantamento-normativos/tests/fixtures/tcu_acordaos_colegiados_real.json` | **novo**: os 2 acórdãos REAIS "ACÓRDÃO DE RELAÇÃO 4318/2026 ATA 25/2026" (1ª × 2ª Câmara, 04/08/2026). É captura ao vivo do tester, 23/09, verbatim de `live_all.json` |
| `levantamento-normativos/test_comprehensive.py` | `assert result.data == ""` em `test_tcu_map_acordao_missing_fields` (plano). `test_tcu_map_acordao`: numero com colegiado (desvio declarado) |
| `tools/run_all_tests.py` | `BASELINE[...]` 29 → 33 → 35 → **36** |
| `docs/superpowers/specs/…-design.md` §3.7 | nota do plano (T4); complemento de 23/09 (filtro, `numero` com colegiado, `requirements.txt` mudou na T3); 1º bullet e bullet do `requirements.txt` anotados `⚠ 23/09 … superado`, nada apagado |

Os blocos de código do plano foram colados como estão (extraídos por script). Texto normativo não foi parafraseado:
- `nome` e `ementa` são os campos `titulo` e `sumario` da API, literais;
- `numero` é composição de campos literais (`numeroAcordao`, `anoAcordao`, `colegiado`) com o separador `-TCU-`, na forma de citação do TCU.

## 2. Desvios do plano e por quê

1. **Args do `_map_acordao` preservado.** O bloco do Step 3 não o trazia.
2. **`numero` do acórdão leva o colegiado** (`bdd89a1`): `"4318/2026-TCU-Primeira Câmara"`; sem colegiado continua `"N/AAAA"`.
   - É a forma de citação do TCU ("Acórdão 1.765/2023-TCU-Plenário"), com o colegiado **como a API o escreve** ("Plenário", "Primeira Câmara", "Segunda Câmara").
   - 📝 A forma oficial curta "1ª Câmara" exigiria uma tabela de tradução: deixaria de ser literal, e um colegiado novo a quebraria. Não adotada.
   - O porquê está na §3.
3. **Dois asserts alterados**, com o mínimo necessário e comentados:
   - teste do plano `test_tcu_acordao_real_mapeia_…`: `r.numero == f'{numeroAcordao}/{anoAcordao}'` → `f'…/{anoAcordao}-TCU-{colegiado}'`;
   - legado `test_comprehensive.test_tcu_map_acordao`: `"1234/2023"` → `"1234/2023-TCU-Plenário"` (o item tem colegiado "Plenário"; a regra é uma só para todo item).

   `test_tcu_map_acordao_missing_fields` não tem colegiado e continua `"999/2024"`. Ids de itens sem colegiado não mudam.
4. **`colegiado` nulo** (`38a110d`, M5, pré-existente): `item.get("colegiado") or ""`, e `orgao_emissor` = `"TCU"` quando vazio.
   - Itens **com** colegiado: saída idêntica.
   - Item legado sem colegiado: `orgao_emissor` passa de `"TCU - "` para `"TCU"`. Nenhum teste afirmava isso, e `orgao_emissor` não entra no `id` nem no dedup.
5. **Testes além do plano: +3** (2 de colegiados, 1 de `colegiado` nulo). ⚠ Contagens desta suíte: T2 +1, T3 +3, T4 +3 = **+7 sobre o plano**:

   | Após | Plano | Real |
   |---|---|---|
   | T4 | 29 | **36** |
   | T5 | 37 | **44** |

   Os totais do runner também ficam +7.
6. **Mensagens de commit** com os números reais e o porquê. Sem `git push`. O plano e `tasks/*` não foram editados: a anotação do corpo do plano (review I1) é do orquestrador, no master.

## 3. A reprovação e o conserto (defeito de colisão)

**Defeito (tester, sobre `e960497`).** Plenário, 1ª e 2ª Câmara numeram em séries **próprias** e se reúnem no mesmo dia.
- Com `numero = "N/AAAA"`, o `id` (`tipo|numero|data`, `models.py`) colidia. Exemplo: 4318/2026, 1ª × 2ª Câmara, 04/08/2026.
- `search()` descartava o 2º em silêncio (`if result.id not in results_by_id`). É perda silenciosa de fonte normativa, exatamente o que a frente proíbe.
- O dedup `tipo_numero` (que ignora `data`) fundiria os dois mesmo com ids distintos.

**Medições sobre as 3.200 keys que o tester capturou ao vivo:**

| | ids distintos | após `deduplicate` |
|---|---|---|
| `e960497` | 2.988 (212 colisões) | 2.025 (**1.175 perdidos**) |
| `bdd89a1` | **3.200** | **3.200** |

Os pares `(numero, ano)` distintos são só 2.025; `(numero, ano, colegiado)` é **único** por key.

**Opções avaliadas:**
- **(a) colegiado em `numero` — escolhida.** `numero` é lido só em três lugares:
  - `models.py` (id);
  - `deduplicator.py:237` (tipo_numero);
  - exibição (`app.py:1085`, `excel_export.py:79`).

  Nada o parseia (conferido pelo tester). Consertam-se os dois caminhos (id e dedup) sem mudar a fórmula do `id` nem a estratégia do dedup.
- **(b) colegiado em `tipo` — rejeitada.** `tipo` alimenta o filtro de tipo do app (`app.py:771`, opções `:952`), a ordenação (`:803`), a cor (`:1048`), as contagens (`:1168`), a coluna "Tipo" da planilha (`:1225`) e o dedup. Partiria "Acordao TCU" em três grupos e quebraria o `assert result.tipo == "Acordao TCU"` legado.
- **(c) mudar a fórmula do `id` — rejeitada.** Afetaria LexML e Google e arriscaria o `dedup_esperado`. Um ramo só para o TCU no modelo ainda deixaria a fusão `tipo_numero`, e o dedup não pode mudar nesta frente.

**Golden:** o corpus fixo tem 1 item `source: tcu` (tipo "Acórdão") montado à mão; `golden_master.py` não chama `_map_acordao` nem `tcu_searcher`. `golden_master.py comparar` → OK.

**TDD do conserto.** Dois testes com os 2 itens reais:
- `test_tcu_acordaos_de_colegiados_diferentes_com_mesmo_numero_sobrevivem_ao_search`;
- `test_tcu_acordaos_de_colegiados_diferentes_sobrevivem_ao_dedup_e_a_mesma_copia_funde`: `deduplicate([a, b, copia_de_a])` mantém os 2 e funde a cópia (`found_by == "k, outra"`).

Antes do conserto, os dois e o assert do plano falhavam:
- os dois: `Right contains one more item: '…SEGUNDA CÂMARA'`;
- o do plano: `'2561/2026' == '2561/2026-TCU-Plenário'`.

**Verificação:**
- `collide.py` do tester: `same id: False`, 2 resultados (PRIMEIRA e SEGUNDA CÂMARA).
- `_fetch_all_pages` ao vivo com `MAX_PAGES=10` (só leitura): 200 itens, 200 keys, **200 ids**, 200 após dedup (fuzzy ativo, n ≤ 1000).

## 4. Gates e saídas

**Ver falhar (Step 2)** — `-k "acordao_real or pagina_cheia or quebra_o_mapeamento or 500_num"` → `4 failed, 29 deselected`, como o plano prevê:
- `assert 0 == 1` (500_num);
- `('empty','') != ('error','erro_interno')` (quebra_o_mapeamento);
- `'Acordao / - TCU - Plenário' != 'ACÓRDÃO 2561/2026 ATA 36/2026 - PLENÁRIO'` (acordao_real);
- `0 == 20` (pagina_cheia).

M5 antes do conserto: `'TCU - None' == 'TCU'`.

**Ver passar:**

| | `e960497` | `bdd89a1` | `38a110d` |
|---|---|---|---|
| `tests/test_fontes_indisponiveis.py` | 33 passed | 35 passed | 36 passed |
| `test_comprehensive.py` | 98/98 | 98/98 | 98/98 |
| `test_phase4.py` | 58 | 58 | 58 |
| golden `comparar` | OK | OK | OK |

Runner (`timeout 900 python -u tools/run_all_tests.py`, foreground), TUDO VERDE, exit 0 nos três:

```
                                     e960497     bdd89a1     38a110d
test_searchers.py                  13 399.8s   13 255.9s   13 203.8s
test_llm_phase3.py                 53   3.0s   53   3.0s   53   2.7s
test_comprehensive.py              98 140.8s   98  78.9s   98  72.4s
test_phase4.py                     58   2.8s   58   2.4s   58   2.4s
tests/test_fontes_indisponiveis.py 33   1.8s   35   1.8s   36   1.7s
total                             255         257         258
```

A queda de tempo entre `e960497` e os commits seguintes **não** vem de código no caminho de rede; o mais provável é a API ao vivo estar mais rápida nesse horário. Não medi.

**Tester:** runner 255 → 257, suíte 33 → 35, golden OK, CRLF, auditoria. **Mapeamento literal conferido em 500 itens ao vivo**, com 0 divergências:
- `sumario` nulo em 327/500;
- `situacao` OFICIALIZADO 499 + INVALIDADO 1;
- nenhuma chave nova ou faltando em relação à fixture.

**Ao vivo, `TCUSearcher().search(["turismo"], max_results=5)`** (implementador, `e960497`): **1** resultado (antes da T4: 0).
- `nome` = `'ACÓRDÃO 2561/2026 ATA 36/2026 - PLENÁRIO'`, `data` = `16/09/2026`, `situacao` = `OFICIALIZADO`, `link` = `contas.tcu.gov.br/pesquisaJurisprudencia/#/detalhamento/…`, `ementa` = o `sumario` literal.
- Detalhe: "Acórdãos: ok (500 itens, 327 sem sumário …)". O dedup por key da T3 funcionando ao vivo.

**Auditoria de documentação (os 2 comandos):**
- Removidos em `e960497`: os corpos e docstrings antigos de `_texto_do_acordao` e `_map_acordao` (substituídos pelos do Step 3, Args preservado); `# Parse date from dataAta or dataSessao` (vira os comentários inline "precedencia invertida de proposito" e `"" e nao None`); a linha "ementa field" do docstring de `search()` (reescrita); o decorator xfail e `== 0` (Step 1); `BASELINE`.
- Removidos em `bdd89a1`: a linha antiga `numero=`, os 2 asserts declarados, linhas reescritas de docstring e `BASELINE`.
- Removidos em `38a110d`: `colegiado = item.get("colegiado", "")`, a linha `orgao_emissor=`, 2 linhas de docstring estendidas e `BASELINE`.
- `_map_acordao` e `_texto_do_acordao` só são chamados em `tcu_searcher`, `test_comprehensive` (itens legados, via fallback) e nos testes novos. Nenhuma assinatura mudou.

## 5. Evidência e2e (tester)

- "turismo" → **4 cards de acórdão** conferidos contra a API byte a byte (`t4_lgpd_passo{4,5}.png`, `t4_turismo_passo{4,5}.png`).
- No re-teste, o card e o Excel mostram `2561/2026-TCU-Plenário` (`t4b_turismo_detalhes.png`).
- Screenshots em `bn-trilha-a/tests/evidencia/`, **não versionados**.

## 6. Achados de teste e revisão, e para onde foram

| # | Achado | Destino |
|---|---|---|
| Defeito (tester) | Acórdãos de colegiados diferentes colidem no `id` e somem em `search()`; o dedup `tipo_numero` os fundiria. | **Corrigido em `bdd89a1`** (§3). Re-teste APROVADO: 3.200 / 3.200 / 3.200. |
| tester | Spec §3.7 ainda listava `requirements.txt` em "O que NÃO muda", e a nota nova só cobria o mapeamento (a T4 também muda o filtro). | **Corrigido em `bdd89a1`**: complemento datado + bullet anotado. |
| tester | Docstring de `_fetch_all_pages` "Stops at MAX_PAGES * PAGE_SIZE records" é falsa ao vivo (a API manda mais por página). | **Corrigido em `bdd89a1`**. |
| tester | `_sem_sumario` não conta `sumario=123`. | Correção ao brief, não defeito; sem ação. |
| tester | Escape HTML duplo na tela. | **T9** (já carregado). |
| I1 (reviewer) | O corpo do plano (`:1774`, `:1841`) e a task 04 ainda mostram `numero ← f"{numeroAcordao}/{anoAcordao}"`. | **Orquestrador**, no master (nota datada, sem reescrever). |
| M2 | Docstring de `numero` sem o exemplo do TCU. | **Corrigido em `38a110d`**. |
| M3 | Docstrings de `_texto_do_acordao`/`_map_acordao` perderam o ponteiro para a fixture real. | **Corrigido em `38a110d`** (as duas fixtures). |
| M4 | Spec §3.7, 1º bullet, sem a anotação de "superado". | **Corrigido em `38a110d`** (nada apagado). |
| M5 | `colegiado: null` → `orgao_emissor` "TCU - None" (pré-existente). | **Corrigido em `38a110d`** + teste. |
| D-C17 | Efeito colateral: com ids distintos, o dedup **fuzzy** (sumário ≥ 0,85) agora funde acórdãos **distintos** de sumários parecidos: 26 de 900 numa amostra real. Não é defeito da T4; a spec proíbe mudar o dedup nesta frente. | **Decisão humana D-C17** em `_DECISOES-PENDENTES.md`. O reviewer propõe a opção `a'`, porque a `a` mudaria o golden. **Sem código.** |

## 7. Regras respeitadas

- Nenhum `secrets.toml` criado.
- Nenhum teste novo faz rede (as chamadas ao vivo acima foram só leitura e fora da suíte).
- Arquivos em CRLF.
- A raiz `tests/` não foi adicionada.
- Branch `deploy`, `execucao/*`, `_TODO.md`, o plano e `tasks/*` intocados.
- Push fica com o orquestrador.

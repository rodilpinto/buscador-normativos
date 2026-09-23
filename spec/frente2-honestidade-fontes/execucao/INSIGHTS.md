---
title: Frente 2 — insights da execução (atualizado depois de cada task)
related: [CONTEXTO.md, TODOS.md, ../../../LESSONS.md]
---

# Insights — frente 2

> Um bloco por task, escrito ao fechar a task: o que o plano previu × o que aconteceu, o que os agentes
> acharam, o que custou tempo. Na T10, o que for transversal sobe para o `LESSONS.md` (e o que for de
> máquina, para `~/.claude/ENVIRONMENT.md`); aqui fica o registro completo.

## Preparação (2026-09-22)

- `spec/implementation` (citado no pedido) não existe; a pasta é `spec/frente2-honestidade-fontes/`.
- Não há "Playwright skill" nesta sessão; e2e usa o **Playwright Python** instalado, com
  `channel="chrome"` (os navegadores do Playwright não estão baixados — `ENVIRONMENT.md`).
- Paralelismo: trilhas A (T2–T5) e B (T6–T8) depois da T1, em worktrees; portas distintas para o e2e.

## T1 · vocabulário (fechada 23/09)

- Impl: previsão do plano bateu exatamente (fail = `ImportError MOTIVOS` na coleta; 41 + 17 = 58; total 222).
- Runner: 9m21s, **411s só no `test_searchers`** (fontes LIVE quebradas) — o gargalo que a T2 deve reduzir.
- Efeito colateral declarado pelo coder: `KeywordStatus.__setattr__` converte `detalhe`/`error_message = None` em `""`.
- Repo em `core.autocrlf=true`: arquivos CRLF na árvore, LF no índice — agentes devem manter CRLF.
- Teste: e2e real mostrou a UI v1.0 dizendo **"2 OK, 0 erros, 4 sem resultados"** com LexML bloqueado — a mentira
  que a frente mata, agora com screenshot (`tests/evidencia/t1_passo4.png`, não versionado).
- Sondas do testador acharam 2 bordas no código **literal do plano** em `redigir`: o marcador de corte conta
  `len - limite`, não o que foi cortado; `limite` < tamanho do marcador faz o texto crescer. Levados ao reviewer.
- ⚠ `tests/evidencia/` só entra no `.gitignore` na T9: até lá, nenhum agente pode fazer `git add tests/` na raiz.
- Review: "nada a corrigir". Os 4 menores do testador ficam **fora da T1** — o código é o literal do plano, e mudar a
  saída de `redigir` emendaria o plano e poderia mexer no hash do golden da T8. 📝 **Candidatos a hardening (não
  validados)** para uma task própria com teste: (1) marcador conta `len(texto) - 2*metade`; (2) guarda para
  `limite < len(marca)`; (3) validar `motivo` também em `__setattr__`; (4) redigir `key%3D…` e `"key": "…"` (frente 5).
  Ir para `_TODO.md` P3 na T10.

## T6 · origem da nota (trilha B, fechada 23/09)

- Impl: contagens do plano exatas (Step 2 `54/53/1` com `ImportError`; Step 4 `63/63`). Runner da trilha = **232**
  (13+63+98+58), não os 269 do plano — esperado com trilhas paralelas.
- Armadilha de ambiente: **`sed -i` do Git Bash converteu `gemini_client.py` para LF e não aplicou a edição**; o coder
  restaurou CRLF e passou a editar com Python `newline=""`. Candidato a `ENVIRONMENT.md` na T10 (é da máquina).
- O coder manteve a informação da linha `Returns` antiga ("[0.0, 1.0]; mesmo tamanho") com uma linha a mais —
  documentação preservada, desvio declarado.

## T2 · LexML (trilha A, fechada 23/09)

- **Previsão do plano errou por 1 no "ver falhar":** 15 failed + 1 passed, não 16 failed. O que passou é um teste-guarda
  (M10: SRU válido com BOM não pode ser reprovado) que o código antigo já satisfazia. `def test_` = 16, como previsto.
  Lição: teste que protege comportamento EXISTENTE passa no "ver falhar" — o plano deveria prevê-lo como passed.
- **O cache de falha NÃO derrubou o tempo do `test_searchers`** (402,8s vs ~411s): a suíte faz uma busca LexML de 1
  keyword só. Ao vivo, o LexML novo leva **1,7s** (antes: cadeia + sleep + retry). O resto dos ~400s é outra fonte
  (TCU com retries, presumido — medir na T3). A expectativa do plano ("deve cair com o cache da T2") estava errada.
- Coder corrigiu 4 docstrings/comentários que a mudança tornava falsos (regra verify-stale-docs) e manteve 2 textos
  que o bloco do plano derrubava. Pendência: nota de P3 do Step 11(b) (`test_lexml_cql_injection_sanitization` faz rede)
  — o `_TODO.md` é do orquestrador: entra na T10.

- (T6/T2, 23/09) **Agentes de teste com runner em background travam**: o testador da T6 ficou 600s sem progresso
  (runner em background com log vazio, provável concorrência com o e2e); retomado via SendMessage, refez em foreground
  com `timeout 590`. A duração relatada de dois agentes (~9,8 h) e um tempo de suíte de 35.280s indicam **suspensão da
  máquina** durante a noite — `time.monotonic` no Windows avança na suspensão. Regra: brief de teste pede runner em
  foreground com `timeout`, e duração de suíte absurda = conferir relógio antes de suspeitar do código.

- (T2 fechada) Review pegou uma **lacuna do plano**: corpo 200 não-HTML e não-XML saía sem `| GET <url>` — violava a
  própria Global Constraint de reprodutibilidade. Conserto + 1 teste além do plano → a suíte nova fica **+1 em todas as
  previsões seguintes** (T3 26+1xfail, T4 30, T5 38). Registrado no doc da T2; o brief das próximas tasks diz isso.

- (T6 fechada) Review pegou **rótulo desonesto herdado**: `NaN`/`Infinity`/`true` vindos do modelo saíam como nota do
  modelo (NaN → 1,0, a nota máxima) — o defeito só virou visível porque a T6 passou a ROTULAR a origem. +1 teste além do
  plano (`test_llm_phase3` 64). Padrão: **dar nome à procedência revela lixo que antes era só um número.**

## T3 · TCU falhas (trilha A, em andamento)

- Impl: ver-falhar 9 failed + 1 xfailed (como previsto, com o +1 da T2 a suíte coleta 27); depois 26 + 1 xfail.
- **Ao vivo o TCU agora é honesto:** `error http_5xx parcial=True`, detalhe "Acórdãos: ok (520 itens, **327 sem sumário**
  — nesses só o título casa); Atos: http_5xx …" — o fato medido na rodada 2 (sumário nulo) virou texto na tela.
- **O gargalo do `test_searchers` NÃO é retry, é PAGINAÇÃO:** 1 busca TCU ao vivo = 128s, ~114s baixando 26 páginas de
  acórdãos (rate-limit 1,5–2s + ~2,5s/requisição); os 3 retries do 500 custam ~13s. A suíte faz 2 buscas TCU (uma com
  `max_results=0`, que baixa tudo mesmo assim). 📝 Ideias do coder, não validadas: sair cedo com `max_results<=0`;
  cache de páginas por processo. Possível P3. Estranheza: 520 itens contra teto 500 (MAX_PAGES×PAGE_SIZE) → testador.
- Perda declarada (código do plano): 503 deixou de ter linha de log própria; o fato vive no docstring e no detalhe.

## T7 · `_merge` (trilha B, fechada 23/09)

- Ciclo limpo: testador sem defeito (sondagem exaustiva de 12.288 combinações), reviewer "nada a corrigir". Invariante
  declarado: o dedup roda antes da pontuação no app, então a origem mesclada é sempre `padrao_fonte` hoje.

## T8 · planilha (trilha B, em andamento)

- Recongelamento como o plano manda: `comparar` → só "planilha divergiu" (nenhum "dedup divergiu") → `congelar` →
  `comparar` 2× OK, mesmo sha; `dedup_esperado.json` fora do diff.
- **Previsão M12 do plano estava desatualizada:** com só 3a+3c aplicados deram `11 failed` com composição diferente da
  prevista ("1 + 10") — os 3 testes de contagem já tinham sido atualizados para 11 colunas e falham juntos. Total igual,
  explicação diferente.
- Coder restaurou 2 frases do docstring de `_sha_planilha` que o bloco do plano derrubava (o porquê de hashear
  células, e que `load_workbook` é a mesma técnica dos testes) — regra docs-move-with-code em ação.

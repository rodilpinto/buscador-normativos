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

## T1 · vocabulário (em andamento)

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

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

---
task: 10
fase: "Fase 5 — Fechamento"
plan: docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md (linhas 2877-2881)
reference: spec/frente2-honestidade-fontes/reference/global-constraints.md
depends_on: [T9]
---

> Extraído **verbatim** do plano v4 (linhas 2877-2881). **O plano segue fonte de verdade**:
> divergência entre o plano e esta cópia → o plano ganha. Status em `../execucao/TODOS.md` — **não marque
> os checkboxes aqui**. Antes de começar, ler `../reference/global-constraints.md` (Global
> Constraints, Estrutura de arquivos, BASELINE por task). Ordem e dependências: `../00-overview.md`.

# T10 · fechar a frente 2: critérios de pronto da spec §7, duráveis, lições

**Fase 5 — Fechamento.**

## Depende de

- **T9** — todas as anteriores fechadas (9 commits de task)

**Arquivos compartilhados com outras tasks:** ledgers e docs do repo

## Critérios de aceite

> Derivados do próprio plano (os "Ver passar", "Expected" e gates da task e das Global
> Constraints) — **nenhum critério novo**. Números são previsões do plano: se o observado
> divergir, contar os `def test_` do bloco da task antes de suspeitar do código.

- Critérios de pronto da spec §7 com comandos e saídas no commit: runner TUDO VERDE **sem** `[AVISO] cresceu`; `golden_master.py comparar` OK e `git diff d054d5b -- tests/golden/dedup_esperado.json` vazio; V11 rodado de novo; auditoria dos 2 comandos sobre `dc99d73..HEAD`.
- Duráveis atualizados como a task lista (`_TODO.md`, `log.md`, `SESSION-ONBOARD` §2/§6 → próxima: frente 5, `BLOCKED-ON-RODRIGO.md` B-04, `LESSONS.md` com as 3 lições).
- Commit `docs: fecha a frente 2`; push; `/checkpoint`.

---

## Conteúdo da task (verbatim do plano)

### Task 10: Fechar a frente

- [ ] Critérios de pronto da spec §7 (com os comandos e saídas no commit): 9 commits das tasks; runner TUDO VERDE sem `[AVISO] cresceu`; `golden_master.py comparar` OK e `git diff d054d5b -- tests/golden/dedup_esperado.json` vazio; V11 rodado de novo; auditoria dos 2 comandos sobre `dc99d73..HEAD`.
- [ ] Duráveis: `_TODO.md` (frente 2 ✅; F9 perde os achados que viraram código; P3 ganha: "sanitizar ementa/nome contra fórmula na aba Normativos", "dublar `test_lexml_cql_injection_sanitization` — faz rede", "tela: agrupar o detalhe do TCU por fonte (é idêntico por keyword)", "runner sem LLM de verdade: `st.secrets` vence a variável vazia — frente 5"); `log.md`; `SESSION-ONBOARD` §2/§6 (próxima: frente 5); `BLOCKED-ON-RODRIGO.md` B-04 (`✅ a UI e a planilha distinguem indisponível de sem resultado; acórdãos do TCU deixaram de ser invisíveis — mas os recentes chegam sem sumário (medido), a lacuna continua`); `LESSONS.md`: (1) fixture escrita à mão sobre esquema não capturado é falsa testemunha — a real derrubou o teste e revelou um bug de produção (B5); (2) correção que tapa um bug abre outro: `redigir(300)` × cadeia agregada (R2-B1) e `sem_texto` fora do try × `_texto_do_acordao` não-total (R3-B1) — em duas rodadas seguidas, o pior achado foi um **cruzamento de duas correções da rodada anterior**; só rodada seguinte pega, e o plano só ficou executável na 4ª versão; (3) falta captura real de SRU do LexML — capturar quando a fonte responder.
- [ ] Commit `docs: fecha a frente 2`; push; `/checkpoint`.

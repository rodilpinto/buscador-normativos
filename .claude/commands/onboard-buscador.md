# Onboard — Buscador de Base Normativa

**Uso**: `/onboard-buscador`

Carrega o contexto do projeto (estado atual, decisões, trabalho pendente) para começar uma
sessão nova pronta para trabalhar.

---

## O que fazer

Leia os arquivos na ordem, depois resuma o estado ao usuário. **Se a mensagem do usuário já
trouxe uma tarefa junto com o onboard, siga com ela após o resumo; senão, NÃO comece nada
até ele dar uma.**

### Passo 1 — Estado (ponto de entrada, ≤ 1 página)
`SESSION-ONBOARD-buscador.md` — ler inteiro. §2 (estado) e §5 (próximo) mandam.
⚠ A §3 tem os achados críticos que custam caro se forem redescobertos — não pule.

### Passo 2 — Ledgers
`_TODO.md` (P0/P1) e `_DECISOES-PENDENTES.md` (🔴/🟡 e o que cada uma trava).

### Passo 3 — Spec e plano (a fonte real do trabalho)
- `docs/superpowers/specs/2026-09-08-buscador-normativos-design.md` — **por que** cada coisa
  é como é. Ler §2 (princípio), §4 (decisões B1-B5 e as tensões aceitas) e §7 (riscos).
- `docs/superpowers/plans/2026-09-08-buscador-normativos.md` — as 16 tasks. **Não leia as 16
  de uma vez**: leia "Global Constraints", a "File Structure" e só a task da vez.

### Passo 4 — Log recente (skim)
`grep -n "^## \[" log.md | head -5`, ler a entrada do topo.

### Passo 5 — Estado do git
```bash
git log --oneline -5
git status --short
```

---

## Depois de ler

Responda com um resumo curto (≤ 8 linhas):
1. Fase do projeto e último commit.
2. Qual task do plano é a próxima.
3. Decisões abertas e o que cada uma trava.
4. As ressalvas da §3 do state file que afetam a task da vez.

Depois: se o usuário já deu uma tarefa, siga; senão pergunte **"Qual a tarefa de hoje?"** e
**pare**.

---

## Regras deste projeto

- **Uma task do plano = um chunk.** Rodar a suíte, atualizar duráveis, commitar, e só então
  a próxima. Fechar com `/checkpoint`.
- **TDD é do plano, não é sugestão:** teste que falha → ver falhar → implementar → ver passar
  → commit. Os passos estão escritos.
- **Não "simplificar" as travas anti-ancoragem** da Task 10 nem o dedup sha256 da Task 12:
  são mitigações de tensões que o Rodrigo aceitou conscientemente (spec §7 e §4).
- **Fixtures sintéticas não provam nada sobre os sites reais.** Antes de confiar em qualquer
  adaptador, baixar a página real e trocar a fixture.
- **Windows:** rodar Python via **Bash** (PowerShell quebra com acento); acima de 260 chars o
  Python falha em silêncio.
- Separar fato de sugestão: marcar `📝` o que for proposta não validada.

Até existir uma tarefa, NÃO: editar arquivos · começar a implementar · commitar · explorar
além dos documentos acima.

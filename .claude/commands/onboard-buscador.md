# Onboard — Buscador de Base Normativa

**Uso**: `/onboard-buscador`

Carrega o contexto do projeto (estado, decisões, pendências) para começar uma sessão nova pronta
para trabalhar.

---

## O que fazer

Leia na ordem, depois resuma ao usuário. **Se a mensagem do usuário já trouxe uma tarefa junto
com o onboard, siga com ela após o resumo; senão, NÃO comece nada até ele dar uma.**

### Passo 1 — Estado (ponto de entrada, ≤ 1 página)
`SESSION-ONBOARD-buscador.md` — ler inteiro. §2 (estado) e §6 (próximo movimento) mandam.
⚠ A §3 tem os achados críticos que custam caro se forem redescobertos — **não pule**.
⚠ A §4 tem o ponto de restauração, com a mensagem literal da tag e o comando de checkout.

### Passo 2 — Ledgers
- `_TODO.md` — status por task. **Só aqui.**
- `_DECISOES-PENDENTES.md` — decisões abertas. Procure **🔴, 🟡 e ⛔** (a legenda está no topo do
  arquivo); ⛔ são permissões pendentes, não escolhas.
- `BLOCKED-ON-RODRIGO.md` — o que espera uma ação do humano.
- `LESSONS.md` — lições transversais. Skim; o índice do fim aponta as de máquina.

### Passo 3 — Spec e plano vigentes
- `docs/superpowers/specs/2026-09-16-consolidacao-buscador-design.md` — **por que** cada coisa é
  como é. A spec de 08/09 continua valendo no que esta não contrariar, e esta declara onde prevalece.
- `docs/superpowers/plans/2026-09-16-consolidacao-fase1.md` — o plano vigente.
  ⛔ **Leia as seções de EMENDAS antes do corpo.** Precedência declarada no topo de cada uma.
  Cada seção do corpo que foi derrubada carrega um marcador `⛔` nomeando a emenda que a derruba.
  **Não leia o plano inteiro de uma vez:** leia as emendas, as "Global Constraints" e só a task da vez.
  ⚠ **A ordem de execução NÃO é a numeração das tasks** — o `_TODO.md` traz a ordem real.

⛔ **Superados, histórico apenas — não execute:** `docs/superpowers/plans/2026-09-08-*`,
`docs/superpowers/specs/2026-09-08-*` na parte contrariada, e `spec/buscador/tasks/`.

### Passo 4 — Log recente (skim)
`grep -n "^## \[" log.md | head -5`, ler a entrada do topo.

### Passo 5 — Estado do git
```bash
git log --oneline -5
git status --short
```
⚠ O SHA mais novo citado no state file está sempre um passo atrás do commit que o gravou. A
cadeia real é a do `git log`.

---

## Depois de ler

Resumo curto (≤ 8 linhas):
1. Fase do projeto e último commit.
2. Qual task é a próxima (ordem real, não numérica).
3. Decisões abertas e o que cada uma trava.
4. As ressalvas da §3 do state file que afetam a task da vez.

Depois: se o usuário já deu uma tarefa, siga; senão pergunte **"Qual a tarefa de hoje?"** e **pare**.

---

## Regras deste projeto

- **Uma task = um chunk.** Rodar a suíte + o golden-master, atualizar duráveis, commitar **e
  pushar**, e só então a próxima. Fechar com `/checkpoint`.
- **TDD é do plano, não é sugestão:** teste que falha → ver falhar → implementar → ver passar →
  commit. Os passos estão escritos.
- **O agrupamento semântico é ADITIVO** — nunca remove, oculta nem filtra item da visão do
  usuário. Requisito vinculante do Rodrigo, com teste próprio. Não "simplificar".
- **Não "simplificar" as travas anti-ancoragem** nem o dedup sha256: são mitigações de tensões
  que o Rodrigo aceitou conscientemente (spec de 08/09 §4 e §7).
- **Cobertura é requisito, não preferência.** Ferramenta de pesquisa que não pega o máximo não é
  confiável — medir a lacuna antes de fechar o MVP.
- **Nada de código pode exigir LLM.** Backend nulo é o padrão; a suíte passa com as variáveis de
  ambiente todas vazias.
- **Windows:** rodar Python via **Bash** (PowerShell quebra com acento); acima de 260 chars o
  Python falha em silêncio.
- **Auto-memória exige autorização explícita** do Rodrigo antes de qualquer escrita.
- Separar fato de sugestão: marcar `📝` o que for proposta não validada.

Até existir uma tarefa, NÃO: editar arquivos · começar a implementar · commitar · explorar além
dos documentos acima.

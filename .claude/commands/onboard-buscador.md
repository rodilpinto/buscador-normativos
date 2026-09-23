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

### Passo 3 — Spec e plano da frente da vez
A §6 do state file diz qual frente está ativa. Para cada frente há uma spec e um plano em
`docs/superpowers/{specs,plans}/` com a data em que nasceram; o state file §7 aponta os vigentes.

- **Spec da frente** — o *porquê*. A spec de consolidação de 16/09 continua valendo para a arquitetura.
- **Plano da frente** — leia "Global Constraints", "Estrutura de arquivos" e **só a task da vez**.
  ⚠ Planos têm dois formatos: (a) **emendas dobradas no corpo** (a triagem de cada rodada adversarial fica
  no topo como registro; o corpo já está corrigido; ordem = numeração) — é o caso do plano da frente 2;
  (b) **seções de emendas no topo** que prevalecem sobre o corpo (precedência declarada em cada seção; cada
  seção do corpo derrubada tem marcador `⛔`; a ordem real está no `_TODO.md`) — é o caso do plano de 16/09.
  O topo do plano diz qual formato ele usa; não leia o corpo antes disso.
- **Split da frente, quando existir** — `spec/<frente>/00-overview.md` (fases, dependências, protocolo) e
  `spec/<frente>/tasks/NN-*.md` (cópia verbatim de cada task + critérios de aceite). É o que o subagente lê.
  O plano continua fonte de verdade. A frente 2 tem: `spec/frente2-honestidade-fontes/`.

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
2. Qual frente e qual task são as próximas (a ordem real está no `_TODO.md`; no plano da frente 2 é a numeração).
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

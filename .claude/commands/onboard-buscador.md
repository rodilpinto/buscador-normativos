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

**Se a §2/§6 disser que uma frente está EM EXECUÇÃO:** ler em seguida `spec/<frente>/execucao/CONTEXTO.md`
(objetivo, regras de papel, trilhas) e `execucao/TODOS.md` (status por task — SSOT da execução; o `_TODO.md`
aponta para ele). Conferir o trabalho em voo com `git worktree list` e `git -C <worktree> log --oneline homologacao..`.

### Passo 2 — Ledgers
- `_TODO.md` — status por task (**exceto** frente em execução: aí o SSOT é `spec/<frente>/execucao/TODOS.md`).
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
  pushar**, e só então a próxima. Fechar com `/checkpoint`. ⚠ **Antes de empurrar, leia a §6 do state file:**
  se ela declarar congelamento, commite e **não** empurre até o ok explícito do Rodrigo.
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
- **`levantamento-normativos/{llm_cadeia,branding,tempo_economizado}/` e `servidor_nuati/` são cópias e NÃO se editam
  aqui**: a origem é o repo `rodilpinto/nuati-framework` (D-C23). Defeito ou falta vira pedido ao framework; o buscador recebe
  por recópia.
- **Ambientes (D-C22):** `main` = produção (padrão no GitHub), `homologacao` = trabalho. Fatos de infraestrutura (apps,
  servidor do Nuati, espelho `camara`): state file §8.
- **Push em `homologacao` redeploya o app de homologação; push em `main` muda a produção**, e este só com ok do Rodrigo e tag.
  Dois remotos: `origin` (GitHub, origem) e `camara` (Gitea, espelho que o servidor do Nuati usa); push para o `camara` só da
  sessão principal, nunca de subagente.
- **Chaves de LLM nunca passam pelo chat nem pelo repo.** Para teste local, carregar o arquivo de chaves da máquina dentro do
  processo Python, sem imprimir (PC do trabalho: `%USERPROFILE%\.streamlit\secrets.toml`, receita no README do framework §1;
  outra máquina: `~/.llm-chaves.toml`, receita em `~/.claude/ENVIRONMENT.md`).

Até existir uma tarefa, NÃO: editar arquivos · começar a implementar · commitar · explorar além
dos documentos acima.

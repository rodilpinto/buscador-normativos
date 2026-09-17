---
title: Buscador de Base Normativa — state snapshot
maintained_by: sessões do Claude Code; humanos podem editar
last_updated: 2026-09-16
related: [_TODO.md, _DECISOES-PENDENTES.md, log.md, LESSONS.md, BLOCKED-ON-RODRIGO.md, decisions/DECISIONS-LOG.md, docs/superpowers/specs/2026-09-16-consolidacao-buscador-design.md, docs/superpowers/plans/2026-09-16-consolidacao-fase1.md]
---

# Buscador de Base Normativa — onboarding de sessão

Ponto de entrada único. ≤ 1 página. Histórico em `log.md`; backlog em `_TODO.md`; decisões em
`_DECISOES-PENDENTES.md`; lições em `LESSONS.md`.

## 1. O que é (30s)

App web local que **constrói** o acervo de critério de uma ação de controle: tema →
palavras-chave → busca → **triagem em poucas decisões** → download → organização → planilha.

⚠ **Não confundir com o `wiki-chat`** (`projetos-nuati/wiki-chat/`): aquele **consome** acervo
pronto; este **constrói**. Projetos distintos, declarado pelo Rodrigo em 08/09 e reconfirmado no
board de 16/09 (decisão D-C2).

## 2. Estado na última pausa (2026-09-16)

🟡 **Planejamento fechado e revisado. ZERO linha de código de produção.** O que existe é spec,
plano e ledgers. Nada foi merjado ainda.

**Cadeia desta sessão:** `7e42f51` → `8bdb0e3` → `e70f533` → `c93e6de` → `1c7fa04` → `8b5cf6a`
→ commit deste checkpoint.
⚠ **O SHA mais novo listado aqui está SEMPRE um passo atrás do commit que gravou este arquivo** —
é propriedade estrutural do checkpoint, não erro. A cadeia real termina em `git log --oneline -3`.

**Working tree:** limpo na pausa; `master` rastreando `origin/master`, tudo pushed.

## 3. Achados críticos (não perder)

1. **O projeto NÃO é greenfield.** O app `levantamento-normativos` existe desde março/2026 em
   `~/Documents/projeto-nuati-normativos-levantamento/`: **205 testes verdes** medidos em 16/09 (13+53+98+41),
   busca por API (LexML SRU/CQL, TCU Dados Abertos, Google CSE/DuckDuckGo). A spec de 08/09 dizia
   o contrário — a varredura dela não cobriu essa pasta. Detalhe em `LESSONS.md`.
2. **A decisão B2 foi REVERTIDA:** a base é o **Streamlit já escrito**, não um FastAPI novo.
3. **Precedência das emendas: C > B > A > corpo.** O plano da Fase 1 tem 3 rodadas de revisão
   adversarial; cada seção do corpo derrubada carrega um marcador `⛔` apontando a emenda.
4. **A ordem das tasks não é a numeração:** T3 → T1 → T2 → T4 → T5 → T6 → T7 → T8 → T9 (emenda A1).
5. **O agrupamento semântico é ADITIVO** — nunca remove, oculta ou filtra item da visão do
   usuário (requisito vinculante do Rodrigo, D-C1). Tem teste próprio; não "simplificar".
6. **Cobertura é requisito, não preferência:** medir a lacuna das fontes catalogadas contra um
   tema real **antes** de fechar o MVP.
7. **LLM local inalcançável desta máquina** (`10.10.111.125:1234`, timeout). Detalhe e a regra do
   `timeout` em tupla: `~/.claude/ENVIRONMENT.md`.

## 4. Ponto de restauração (rollback)

Tag anotada no repo A, **mensagem literal**: *"Estado pre-consolidacao: app Streamlit completo e
revisado (mar/2026)."* — ou seja, o estado **ANTES** da consolidação.
✅ Empurrada para o remoto em 16/09 (`git ls-remote --tags origin` confirma).

```bash
cd ~/Documents/projeto-nuati-normativos-levantamento && git checkout levantamento-v1-streamlit
```

## 5. Disciplina de trabalho

Um chunk = uma task do plano. Fechar cada chunk: rodar a suíte → golden-master → atualizar
duráveis → commitar **e pushar** (decisão D-C7). Retomar com `/onboard-buscador`.

## 6. Próximo movimento (recomendação, não decidido)

O Rodrigo tem uma escolha aberta do fim da sessão de 16/09, **não respondida**:

1. **Dobrar as emendas (`A1`-`A21`, `B1`-`B12`, `C1`-`C5`) no corpo do plano** antes de construir (plano linear, ~1 passada), ou
2. **Construir já**, lendo as três seções de emendas junto com cada task.

Em qualquer dos dois, a primeira task é a **T3 (merge)**. Pergunte antes de escolher por ele.

## 7. Ponteiros

| Doc | Papel |
|---|---|
| `docs/superpowers/specs/2026-09-16-consolidacao-buscador-design.md` | **spec vigente** |
| `docs/superpowers/plans/2026-09-16-consolidacao-fase1.md` | **plano vigente** (emendas no topo) |
| `_TODO.md` · `_DECISOES-PENDENTES.md` · `log.md` | status · decisões · timeline |
| `LESSONS.md` · `BLOCKED-ON-RODRIGO.md` | lições transversais · o que espera o humano |
| `decisions/DECISIONS-LOG.md` + o board `.html` | as rodadas de decisão, com os comentários |
| ⛔ `docs/.../2026-09-08-*` e `spec/buscador/tasks/` | **SUPERADOS**, histórico apenas |

## 8. Fatos que não estão escritos em nenhum outro lugar

| | |
|---|---|
| **Repo B** (este) | `github.com/rodilpinto/buscador-normativos`, privado, branch **`master`** |
| **Repo A** (a consolidar) | `github.com/rodilpinto/levantamento-normativos`, privado, branch **`main`** |
| Caminho de A | `~/Documents/projeto-nuati-normativos-levantamento/` — ⚠ o código fica em `levantamento-normativos/` **dentro** dele, não na raiz |
| Cliente de LLM | `llm/gemini_client.py` (dentro de `llm/`, não na raiz) |
| Rodar o app | `python -m streamlit run app.py`, a partir da pasta do código |
| Acervo de consulta | `~/Documents/projetos-nuati/referencias/` |

⚠ **Assimetria de branch:** A usa `main`, B usa `master`. No merge (T3) isso aparece como
`git fetch levantamento` + `levantamento/main`, enquanto o push daqui é `origin master`.

⚠ **`.claude/` é rastreado neste repo** (`.claude/commands/onboard-buscador.md`). Por isso **não**
entra no `.gitignore` unido da T3, embora estivesse no de A.

⚠ **Namespace `R1-*` tem dois significados:** no plano de 08/09 são as emendas de 2026-09-11; na
revisão de 16/09 os achados brutos foram numerados à parte. Diga sempre de qual documento.

⚠ **A mensagem da tag de rollback é imutável e cita `6.533 linhas`** — medição antiga, que omitia
`llm/__init__.py`. O valor correto é **6.561** (`git ls-files '*.py' | xargs wc -l`).

**Fechar a D-C9** quando respondida: mover para 🟢 em `_DECISOES-PENDENTES.md` com a data, abrir
seção em `decisions/DECISIONS-LOG.md`, fechar `B-02` no `BLOCKED-ON-RODRIGO.md` e atualizar a §6.

## 9. Como atualizar este arquivo

Ao mudar de estado: atualize §2/§6, bump `last_updated`, acrescente entrada no `log.md`, atualize
os ledgers. Mantenha ≤ 1 página.
